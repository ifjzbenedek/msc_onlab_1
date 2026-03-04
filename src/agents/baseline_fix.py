import logging

from src.agents.pipeline import PipelineResult
from src.clients.ollama_client import OllamaClient
from src.clients.leetcode_submitter import LeetCodeSubmitter
from src.models.problem import Problem
from src.prompts import WRITER_SYSTEM, writer_prompt, writer_error_prompt
from src.utils.parsers import extract_code

log = logging.getLogger(__name__)


class BaselineFix:
    name = "baseline+fix"

    def __init__(self, ollama: OllamaClient, model: str, submitter: LeetCodeSubmitter, max_fixes: int = 3) -> None:
        self.ollama = ollama
        self.model = model
        self.submitter = submitter
        self.max_fixes = max_fixes

    def run(self, problem: Problem) -> PipelineResult:
        raw = self.ollama.generate(
            model=self.model, prompt=writer_prompt(problem), system=WRITER_SYSTEM,
        )
        code = extract_code(raw)
        if not code:
            return PipelineResult(code=None)

        last_sub = None
        for _ in range(self.max_fixes):
            try:
                last_sub = self.submitter.submit(problem.slug, problem.id, code)
            except Exception as e:
                log.error("Submit failed: %s", e)
                return PipelineResult(code=code, submission=last_sub)

            if last_sub.status not in ("Runtime Error", "Compile Error"):
                return PipelineResult(code=code, submission=last_sub)

            error_msg = last_sub.compile_error or last_sub.runtime_error or ""
            log.info("Submit error: %s — retrying", last_sub.status)

            raw = self.ollama.generate(
                model=self.model,
                prompt=writer_error_prompt(problem, code, last_sub.status, error_msg),
                system=WRITER_SYSTEM,
            )
            new_code = extract_code(raw)
            if not new_code:
                log.warning("No code block after error fix attempt")
                return PipelineResult(code=code, submission=last_sub)
            code = new_code

        return PipelineResult(code=code, submission=last_sub)