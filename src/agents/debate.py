import logging
import time
from typing import Optional

from src.agents.pipeline import PipelineResult
from src.clients.ollama_client import OllamaClient
from src.clients.leetcode_submitter import LeetCodeSubmitter
from src.models.problem import Problem
from src.models.result import AgentStep
from src.prompts import writer_system, writer_prompt
from src.prompts.debate import DEBATE_JUDGE_SYSTEM, debate_critique_prompt, debate_judge_prompt
from src.utils.parsers import extract_code

log = logging.getLogger(__name__)


class Debate:
    """Two writers argue over solutions, a judge picks the winner."""

    name = "debate"

    def __init__(
        self,
        ollama: OllamaClient,
        writer_model_a: str,
        writer_model_b: str,
        judge_model: str,
        submitter: Optional[LeetCodeSubmitter] = None,
        rounds: int = 2,
        temperatures: tuple[float, float] = (0.2, 0.8),
    ) -> None:
        self.ollama = ollama
        self.writer_model_a = writer_model_a
        self.writer_model_b = writer_model_b
        self.judge_model = judge_model
        self.submitter = submitter
        self.rounds = rounds
        self.temperatures = temperatures
        self._same_model = writer_model_a == writer_model_b

    def _generate(self, model: str, prompt: str, system: str, index: int) -> str:
        """Generate with appropriate temperature for same-model setups."""
        temp = self.temperatures[index] if self._same_model else 0.2
        return self.ollama.generate(model=model, prompt=prompt, system=system, temperature=temp)

    def run(self, problem: Problem) -> PipelineResult:
        sys_prompt = writer_system(problem.lang)
        steps: list[AgentStep] = []

        # Round 0, both writers generate independently
        t0 = time.time()
        raw_a = self._generate(self.writer_model_a, writer_prompt(problem), sys_prompt, 0)
        code_a = extract_code(raw_a)
        steps.append(AgentStep(
            role="writer", model=self.writer_model_a, round_number=0,
            action="generate", content=raw_a, index=0,
            duration_seconds=round(time.time() - t0, 1),
        ))

        t0 = time.time()
        raw_b = self._generate(self.writer_model_b, writer_prompt(problem), sys_prompt, 1)
        code_b = extract_code(raw_b)
        steps.append(AgentStep(
            role="writer", model=self.writer_model_b, round_number=0,
            action="generate", content=raw_b, index=1,
            duration_seconds=round(time.time() - t0, 1),
        ))

        if not code_a and not code_b:
            return PipelineResult(code=None, steps=steps)

        # If one failed, use the other
        if not code_a:
            code_a = code_b
        if not code_b:
            code_b = code_a

        # Debate rounds, each writer critiques the other's code
        for r in range(self.rounds):
            t0 = time.time()
            raw_a = self._generate(
                self.writer_model_a,
                debate_critique_prompt(problem, code_a, code_b),
                sys_prompt, 0,
            )
            new_a = extract_code(raw_a)
            steps.append(AgentStep(
                role="writer", model=self.writer_model_a, round_number=r + 1,
                action="critique", content=raw_a, index=0,
                duration_seconds=round(time.time() - t0, 1),
            ))

            t0 = time.time()
            raw_b = self._generate(
                self.writer_model_b,
                debate_critique_prompt(problem, code_b, code_a),
                sys_prompt, 1,
            )
            new_b = extract_code(raw_b)
            steps.append(AgentStep(
                role="writer", model=self.writer_model_b, round_number=r + 1,
                action="critique", content=raw_b, index=1,
                duration_seconds=round(time.time() - t0, 1),
            ))

            if new_a:
                code_a = new_a
            if new_b:
                code_b = new_b

            log.info("Debate round %d complete", r + 1)

        # Judge picks the best solution
        t0 = time.time()
        raw_judge = self.ollama.generate(
            model=self.judge_model,
            prompt=debate_judge_prompt(problem, code_a, code_b),
            system=DEBATE_JUDGE_SYSTEM,
        )
        final_code = extract_code(raw_judge)
        steps.append(AgentStep(
            role="judge", model=self.judge_model, round_number=self.rounds + 1,
            action="judge", content=raw_judge, index=0,
            duration_seconds=round(time.time() - t0, 1),
        ))

        # Fallback if judge didn't produce code
        if not final_code:
            log.warning("Judge produced no code, falling back to writer A")
            final_code = code_a

        submission = None
        if final_code and self.submitter:
            submission = self.submitter.submit(problem.slug, problem.id, final_code, lang=problem.lang)

        return PipelineResult(code=final_code, steps=steps, submission=submission)