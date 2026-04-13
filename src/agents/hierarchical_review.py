"""Pipeline with two-layer review: quick filter then deep review."""

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
    REVIEWER_SYSTEM, QUICK_REVIEWER_SYSTEM, reviewer_prompt,
)
from src.utils.parsers import extract_code, parse_review

log = logging.getLogger(__name__)


class HierarchicalReview:
    """Quick reviewer filters obvious bugs, deep reviewer checks algorithm."""

    name = "hierarchical-review"

    def __init__(
        self,
        ollama: OllamaClient,
        config: SolveConfig,
        quick_model: str,
        deep_model: str,
        submitter: Optional[LeetCodeSubmitter] = None,
    ) -> None:
        self.ollama = ollama
        self.config = config
        self.quick_model = quick_model
        self.deep_model = deep_model
        self.submitter = submitter

    def run(self, problem: Problem) -> PipelineResult:

        sys_prompt = writer_system(problem.lang)
        steps: list[AgentStep] = []

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
            # Layer 1: quick review
            t0 = time.time()
            raw = self.ollama.generate(
                model=self.quick_model,
                prompt=reviewer_prompt(problem, code),
                system=QUICK_REVIEWER_SYSTEM,
            )
            accepted, feedback = parse_review(raw)
            steps.append(AgentStep(
                role="reviewer", model=self.quick_model, round_number=i + 1,
                action="accept" if accepted else "revise",
                content=feedback, index=0,
                duration_seconds=round(time.time() - t0, 1),
                metadata={"layer": "quick"},
            ))

            if not accepted:
                log.info("Round %d: quick reviewer REVISE — skipping deep review", i + 1)
                t0 = time.time()
                raw = self.ollama.generate(
                    model=self.config.writer_model,
                    prompt=writer_revision_prompt(problem, code, feedback),
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
                continue

            # Layer 2, deep review (only if quick accepted)
            t0 = time.time()
            raw = self.ollama.generate(
                model=self.deep_model,
                prompt=reviewer_prompt(problem, code),
                system=REVIEWER_SYSTEM,
            )
            accepted, feedback = parse_review(raw)
            steps.append(AgentStep(
                role="reviewer", model=self.deep_model, round_number=i + 1,
                action="accept" if accepted else "revise",
                content=feedback, index=1,
                duration_seconds=round(time.time() - t0, 1),
                metadata={"layer": "deep"},
            ))

            if accepted:
                log.info("Round %d: both layers ACCEPT", i + 1)
                submission = None
                if self.submitter:
                    submission = self.submitter.submit(problem.slug, problem.id, code, lang=problem.lang)
                return PipelineResult(code=code, steps=steps, submission=submission)

            # Deep reviewer rejected
            log.info("Round %d: deep reviewer REVISE", i + 1)
            t0 = time.time()
            raw = self.ollama.generate(
                model=self.config.writer_model,
                prompt=writer_revision_prompt(problem, code, feedback),
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

        # Loop exhausted, return last code
        submission = None
        if code and self.submitter:
            submission = self.submitter.submit(problem.slug, problem.id, code, lang=problem.lang)
        return PipelineResult(code=code, steps=steps, submission=submission)
