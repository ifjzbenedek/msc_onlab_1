from typing import Optional

from src.agents.pipeline import PipelineResult
from src.clients.ollama_client import OllamaClient
from src.clients.leetcode_submitter import LeetCodeSubmitter
from src.models.problem import Problem
from src.prompts import WRITER_SYSTEM, writer_prompt
from src.utils.parsers import extract_code


class Baseline:
    name = "baseline"

    def __init__(self, ollama: OllamaClient, model: str, submitter: Optional[LeetCodeSubmitter] = None) -> None:
        self.ollama = ollama
        self.model = model
        self.submitter = submitter

    def run(self, problem: Problem) -> PipelineResult:
        raw = self.ollama.generate(
            model=self.model, prompt=writer_prompt(problem), system=WRITER_SYSTEM,
        )
        code = extract_code(raw)

        submission = None
        if code and self.submitter:
            submission = self.submitter.submit(problem.slug, problem.id, code)

        return PipelineResult(code=code, submission=submission)