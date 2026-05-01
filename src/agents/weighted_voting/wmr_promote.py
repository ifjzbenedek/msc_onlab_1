import random
from typing import Optional

from src.agents.pipeline import AgentPipeline, PipelineResult
from src.agents.weighted_voting.base import WeightedVotingBase


class RandomizedWeightedMajorityPromote(WeightedVotingBase):

    def __init__(
        self,
        pipelines: list[AgentPipeline],
        alpha: float = 0.5,
        beta: float = 0.5,
        seed: Optional[int] = None,
    ) -> None:
        if alpha < 0.0:
            raise ValueError(f"alpha must be >= 0, got {alpha}")
        self.alpha = alpha
        super().__init__(pipelines, beta=beta, seed=seed)
        self._rng = random.Random(seed)

    def _build_name(self) -> str:
        inner = ",".join(p.name for p in self.pipelines)
        return f"wmr-promote([{inner}], alpha={self.alpha}, beta={self.beta})"

    def _pick_master_output(self, results: list[PipelineResult]) -> PipelineResult:
        total = sum(self.weights)
        if total <= 0:
            return self._rng.choice(results)
        idx = self._rng.choices(range(len(results)), weights=self.weights, k=1)[0]
        return results[idx]

    def _update_weights(self, results: list[PipelineResult]) -> None:
        for i, result in enumerate(results):
            if self._is_correct(result):
                self.weights[i] *= (1.0 + self.alpha)
            else:
                self.weights[i] *= self.beta
