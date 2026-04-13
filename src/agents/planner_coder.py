"""Pipeline that separates planning from coding into two agent roles."""

import logging
import time
from typing import Optional

from src.agents.pipeline import PipelineResult
from src.clients.ollama_client import OllamaClient
from src.clients.leetcode_submitter import LeetCodeSubmitter
from src.models.problem import Problem
from src.models.result import AgentStep
from src.prompts import writer_system
from src.prompts.planner import PLANNER_SYSTEM, planner_prompt, writer_from_plan_prompt
from src.utils.parsers import extract_code

log = logging.getLogger(__name__)


class PlannerCoder:
    """Planner designs algorithm, Coder implements it."""

    name = "planner-coder"

    def __init__(
        self,
        ollama: OllamaClient,
        planner_model: str,
        coder_model: str,
        submitter: Optional[LeetCodeSubmitter] = None,
    ) -> None:
        self.ollama = ollama
        self.planner_model = planner_model
        self.coder_model = coder_model
        self.submitter = submitter

    def run(self, problem: Problem) -> PipelineResult:
        steps: list[AgentStep] = []

        # Step 1: Planner designs algorithm
        t0 = time.time()
        plan = self.ollama.generate(
            model=self.planner_model,
            prompt=planner_prompt(problem),
            system=PLANNER_SYSTEM,
        )
        steps.append(AgentStep(
            role="planner", model=self.planner_model, round_number=0,
            action="plan", content=plan, index=0,
            duration_seconds=round(time.time() - t0, 1),
        ))
        log.info("Plan generated (%d chars)", len(plan))

        # Step 2: Coder implements from plan
        t0 = time.time()
        raw = self.ollama.generate(
            model=self.coder_model,
            prompt=writer_from_plan_prompt(problem, plan),
            system=writer_system(problem.lang),
        )
        code = extract_code(raw)
        steps.append(AgentStep(
            role="writer", model=self.coder_model, round_number=1,
            action="generate", content=raw, index=0,
            duration_seconds=round(time.time() - t0, 1),
        ))

        if not code:
            return PipelineResult(code=None, steps=steps)

        # Step 3: Submit
        submission = None
        if self.submitter:
            submission = self.submitter.submit(problem.slug, problem.id, code, lang=problem.lang)

        return PipelineResult(code=code, steps=steps, submission=submission)
