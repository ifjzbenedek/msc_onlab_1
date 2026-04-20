"""Base class for weighted-voting ensembles over AgentPipelines.

Faithful to Littlestone & Warmuth (1994), p. 215: on each problem every
pipeline runs and its code is submitted. Every pipeline whose submission
was not Accepted is a "mistake" — its weight is multiplied by beta.
The ensemble's output (master prediction) is produced by a subclass rule
applied to the per-pipeline results.
"""

from abc import ABC, abstractmethod
from typing import Optional

from src.agents.pipeline import AgentPipeline, PipelineResult
from src.models.problem import Problem


class WeightedVotingBase(ABC):

    def __init__(
        self,
        pipelines: list[AgentPipeline],
        beta: float = 0.5,
        seed: Optional[int] = None,
    ) -> None:
        if not pipelines:
            raise ValueError("pipelines must be non-empty")
        if not 0.0 <= beta < 1.0:
            raise ValueError(f"beta must be in [0, 1), got {beta}")
        self.pipelines = pipelines
        self.beta = beta
        self.seed = seed
        self.weights: list[float] = [1.0] * len(pipelines)
        self.name: str = self._build_name()

    @abstractmethod
    def _pick_master_output(self, results: list[PipelineResult]) -> PipelineResult:
        """Given all per-pipeline results, choose the ensemble's output."""

    def _build_name(self) -> str:
        inner = ",".join(p.name for p in self.pipelines)
        return f"weighted_voting([{inner}], beta={self.beta})"

    def run(self, problem: Problem) -> PipelineResult:
        weights_before = list(self.weights)
        results = [p.run(problem) for p in self.pipelines]
        self._update_weights(results)
        output = self._pick_master_output(results)
        output.voting_stats = {
            "pipeline_names": [p.name for p in self.pipelines],
            "weights_before": weights_before,
            "weights_after": list(self.weights),
            "per_pipeline_accepted": [self._is_correct(r) for r in results],
            "any_accepted": any(self._is_correct(r) for r in results),
        }
        return output

    def _update_weights(self, results: list[PipelineResult]) -> None:
        for i, result in enumerate(results):
            if not self._is_correct(result):
                self.weights[i] *= self.beta

    @staticmethod
    def _is_correct(result: PipelineResult) -> bool:
        return bool(result.submission and result.submission.accepted)
