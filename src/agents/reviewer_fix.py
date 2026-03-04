from src.agents.pipeline import PipelineResult
from src.agents.solve_loop import solve_with_review
from src.clients.ollama_client import OllamaClient
from src.clients.leetcode_submitter import LeetCodeSubmitter
from src.models.config import SolveConfig
from src.models.problem import Problem


class ReviewerFix:
    name = "reviewer+fix"

    def __init__(self, ollama: OllamaClient, config: SolveConfig, submitter: LeetCodeSubmitter) -> None:
        self.ollama = ollama
        self.config = config
        self.submitter = submitter

    def run(self, problem: Problem) -> PipelineResult:
        code, reviews, submission = solve_with_review(
            problem=problem, ollama=self.ollama, config=self.config, submitter=self.submitter,
        )
        return PipelineResult(code=code, reviews=reviews, submission=submission)