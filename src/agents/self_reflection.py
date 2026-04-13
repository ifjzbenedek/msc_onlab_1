import logging
import time

from src.agents.pipeline import PipelineResult
from src.clients.ollama_client import OllamaClient
from src.clients.leetcode_submitter import LeetCodeSubmitter
from src.models.problem import Problem
from src.models.result import AgentStep
from src.prompts import writer_system, writer_prompt
from src.prompts.reflection import REFLECTION_SYSTEM, reflection_prompt
from src.utils.parsers import extract_code

log = logging.getLogger(__name__)


def _extract_reflection(response: str) -> str:
    """Extract the reflection text (everything before the code block)."""
    code_start = response.find("```")
    if code_start == -1:
        return response.strip()
    return response[:code_start].strip()


class SelfReflection:
    """Submit, reflect on errors, accumulate lessons, retry."""

    name = "self-reflection"

    def __init__(
        self,
        ollama: OllamaClient,
        model: str,
        submitter: LeetCodeSubmitter,
        max_fixes: int = 3,
    ) -> None:
        self.ollama = ollama
        self.model = model
        self.submitter = submitter
        self.max_fixes = max_fixes

    def run(self, problem: Problem) -> PipelineResult:
        sys_prompt = writer_system(problem.lang)
        steps: list[AgentStep] = []

        t0 = time.time()
        raw = self.ollama.generate(
            model=self.model, prompt=writer_prompt(problem), system=sys_prompt,
        )
        code = extract_code(raw)
        steps.append(AgentStep(
            role="writer", model=self.model, round_number=0,
            action="generate", content=raw, duration_seconds=round(time.time() - t0, 1),
        ))
        if not code:
            return PipelineResult(code=None, steps=steps)

        reflections: list[str] = []
        last_sub = None

        for i in range(self.max_fixes):
            try:
                last_sub = self.submitter.submit(
                    problem.slug, problem.id, code, lang=problem.lang,
                )
            except Exception as e:
                log.error("Submit failed: %s", e)
                return PipelineResult(code=code, steps=steps, submission=last_sub)

            if last_sub.status not in ("Runtime Error", "Compile Error"):
                return PipelineResult(code=code, steps=steps, submission=last_sub)

            error_msg = last_sub.compile_error or last_sub.runtime_error or ""
            log.info("Reflection attempt #%d: %s", i + 1, last_sub.status)

            t0 = time.time()
            raw = self.ollama.generate(
                model=self.model,
                prompt=reflection_prompt(
                    problem, code, last_sub.status, error_msg, reflections,
                ),
                system=REFLECTION_SYSTEM,
            )

            reflection_text = _extract_reflection(raw)
            if reflection_text:
                reflections.append(reflection_text)
                log.info("Reflection: %s", reflection_text[:100])

            steps.append(AgentStep(
                role="writer", model=self.model, round_number=i + 1,
                action="reflect", content=raw,
                duration_seconds=round(time.time() - t0, 1),
                metadata={"reflection": reflection_text},
            ))

            new_code = extract_code(raw)
            if not new_code:
                log.warning("No code block after reflection #%d", i + 1)
                return PipelineResult(code=code, steps=steps, submission=last_sub)
            code = new_code

        return PipelineResult(code=code, steps=steps, submission=last_sub)
