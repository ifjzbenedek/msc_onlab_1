"""Pipeline where two writers independently generate, then a merger combines."""

import logging
import time
from typing import Optional

from src.agents.pipeline import PipelineResult
from src.clients.ollama_client import OllamaClient
from src.clients.leetcode_submitter import LeetCodeSubmitter
from src.models.problem import Problem
from src.models.result import AgentStep
from src.prompts import writer_system, writer_prompt
from src.prompts.merge import MERGER_SYSTEM, merger_prompt
from src.utils.parsers import extract_code

log = logging.getLogger(__name__)


class CoopetitionMerge:
    """Two writers generate independently, a merger combines the best parts."""

    name = "coopetition-merge"

    def __init__(
        self,
        ollama: OllamaClient,
        writer_model_a: str,
        writer_model_b: str,
        merger_model: str,
        submitter: Optional[LeetCodeSubmitter] = None,
        temperatures: tuple[float, float] = (0.2, 0.8),
    ) -> None:
        self.ollama = ollama
        self.writer_model_a = writer_model_a
        self.writer_model_b = writer_model_b
        self.merger_model = merger_model
        self.submitter = submitter
        self.temperatures = temperatures
        self._same_model = writer_model_a == writer_model_b

    def run(self, problem: Problem) -> PipelineResult:
        sys_prompt = writer_system(problem.lang)
        steps: list[AgentStep] = []

        # Writer A generates
        temp_a = self.temperatures[0] if self._same_model else 0.2
        t0 = time.time()
        raw_a = self.ollama.generate(
            model=self.writer_model_a, prompt=writer_prompt(problem),
            system=sys_prompt, temperature=temp_a,
        )
        code_a = extract_code(raw_a)
        steps.append(AgentStep(
            role="writer", model=self.writer_model_a, round_number=0,
            action="generate", content=raw_a, index=0,
            duration_seconds=round(time.time() - t0, 1),
            metadata={"temperature": temp_a},
        ))

        # Writer B generates independently
        temp_b = self.temperatures[1] if self._same_model else 0.2
        t0 = time.time()
        raw_b = self.ollama.generate(
            model=self.writer_model_b, prompt=writer_prompt(problem),
            system=sys_prompt, temperature=temp_b,
        )
        code_b = extract_code(raw_b)
        steps.append(AgentStep(
            role="writer", model=self.writer_model_b, round_number=0,
            action="generate", content=raw_b, index=1,
            duration_seconds=round(time.time() - t0, 1),
            metadata={"temperature": temp_b},
        ))

        # If both failed, give up
        if not code_a and not code_b:
            return PipelineResult(code=None, steps=steps)

        # If only one produced code, use that directly
        if not code_a or not code_b:
            final_code = code_a or code_b
            log.info("Only one writer produced code, skipping merge")
            submission = None
            if self.submitter:
                submission = self.submitter.submit(problem.slug, problem.id, final_code, lang=problem.lang)
            return PipelineResult(code=final_code, steps=steps, submission=submission)

        # Merger combines both solutions
        t0 = time.time()
        raw_merge = self.ollama.generate(
            model=self.merger_model,
            prompt=merger_prompt(problem, code_a, code_b),
            system=MERGER_SYSTEM,
        )
        final_code = extract_code(raw_merge)
        steps.append(AgentStep(
            role="merger", model=self.merger_model, round_number=1,
            action="merge", content=raw_merge, index=0,
            duration_seconds=round(time.time() - t0, 1),
        ))

        # Fallback if merger produced no code
        if not final_code:
            log.warning("Merger produced no code, falling back to writer A")
            final_code = code_a

        submission = None
        if self.submitter:
            submission = self.submitter.submit(problem.slug, problem.id, final_code, lang=problem.lang)

        return PipelineResult(code=final_code, steps=steps, submission=submission)
