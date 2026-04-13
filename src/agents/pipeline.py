from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Protocol

from src.models.problem import Problem
from src.models.result import AgentStep, ReviewerFeedback, SubmissionResult


@dataclass
class PipelineResult:
    code: Optional[str]
    reviews: list[ReviewerFeedback] = field(default_factory=list)
    steps: list[AgentStep] = field(default_factory=list)
    submission: Optional[SubmissionResult] = None
    voting_stats: Optional[dict] = None


class AgentPipeline(Protocol):
    name: str

    def run(self, problem: Problem) -> PipelineResult: ...