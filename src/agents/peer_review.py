"""Pipeline where multiple reviewers vote on the code each round."""

import logging
import time
from typing import Optional

from src.agents.pipeline import PipelineResult
from src.clients.ollama_client import OllamaClient
from src.clients.leetcode_submitter import LeetCodeSubmitter
from src.models.config import SolveConfig
from src.models.problem import Problem
from src.models.result import AgentStep
from src.prompts import (
    writer_system, writer_prompt, writer_revision_prompt,
    REVIEWER_SYSTEM, reviewer_prompt,
)
from src.utils.parsers import extract_code, parse_review

log = logging.getLogger(__name__)


class PeerReview:
    """3 reviewers vote each round, majority decides accept/revise."""

    name = "peer-review"

    def __init__(
        self,
        ollama: OllamaClient,
        config: SolveConfig,
        reviewer_models: list[str],
        submitter: Optional[LeetCodeSubmitter] = None,
        temperatures: tuple[float, ...] = (0.2, 0.5, 0.8),
    ) -> None:
        self.ollama = ollama
        self.config = config
        self.reviewer_models = reviewer_models
        self.submitter = submitter
        self.temperatures = temperatures
        self._same_model = len(set(reviewer_models)) == 1

    def _collect_votes(
        self, problem: Problem, code: str, round_number: int, steps: list[AgentStep],
    ) -> tuple[int, list[str]]:
        """Run all reviewers and return (accept_count, list of REVISE feedbacks)."""
        accept_count = 0
        revise_feedbacks: list[str] = []

        for i, model in enumerate(self.reviewer_models):
            temp = self.temperatures[i % len(self.temperatures)] if self._same_model else 0.2

            t0 = time.time()
            raw = self.ollama.generate(
                model=model,
                prompt=reviewer_prompt(problem, code),
                system=REVIEWER_SYSTEM,
                temperature=temp,
            )
            accepted, feedback = parse_review(raw)

            steps.append(AgentStep(
                role="reviewer", model=model, round_number=round_number,
                action="accept" if accepted else "revise",
                content=feedback, index=i,
                duration_seconds=round(time.time() - t0, 1),
                metadata={"temperature": temp},
            ))

            if accepted:
                accept_count += 1
                log.info("Reviewer %d (%s): ACCEPT", i, model)
            else:
                revise_feedbacks.append(feedback)
                log.info("Reviewer %d (%s): REVISE", i, model)

        return accept_count, revise_feedbacks

    def run(self, problem: Problem) -> PipelineResult:
        sys_prompt = writer_system(problem.lang)
        steps: list[AgentStep] = []
        majority = len(self.reviewer_models) // 2 + 1

        # Initial generation
        t0 = time.time()
        raw = self.ollama.generate(
            model=self.config.writer_model, prompt=writer_prompt(problem), system=sys_prompt,
        )
        code = extract_code(raw)
        steps.append(AgentStep(
            role="writer", model=self.config.writer_model, round_number=0,
            action="generate", content=raw,
            duration_seconds=round(time.time() - t0, 1),
        ))
        if not code:
            return PipelineResult(code=None, steps=steps)

        # Review loop
        for i in range(self.config.max_iterations):
            accept_count, revise_feedbacks = self._collect_votes(problem, code, i + 1, steps)

            if accept_count >= majority:
                log.info("Round %d: majority ACCEPT (%d/%d)", i + 1, accept_count, len(self.reviewer_models))
                submission = None
                if self.submitter:
                    submission = self.submitter.submit(problem.slug, problem.id, code, lang=problem.lang)
                return PipelineResult(code=code, steps=steps, submission=submission)

            # Majority REVISE — combine feedbacks and revise
            log.info("Round %d: majority REVISE (%d/%d)", i + 1, accept_count, len(self.reviewer_models))
            combined_feedback = "\n\n---\n\n".join(revise_feedbacks)

            t0 = time.time()
            raw = self.ollama.generate(
                model=self.config.writer_model,
                prompt=writer_revision_prompt(problem, code, combined_feedback),
                system=sys_prompt,
            )
            new_code = extract_code(raw)
            steps.append(AgentStep(
                role="writer", model=self.config.writer_model, round_number=i + 1,
                action="revise", content=raw,
                duration_seconds=round(time.time() - t0, 1),
            ))

            if not new_code:
                log.warning("No code block in revision round %d", i + 1)
                break
            code = new_code

        # Loop exhausted — submit what we have
        submission = None
        if code and self.submitter:
            submission = self.submitter.submit(problem.slug, problem.id, code, lang=problem.lang)
        return PipelineResult(code=code, steps=steps, submission=submission)
