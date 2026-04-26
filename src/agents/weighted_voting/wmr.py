import random
from typing import Optional

from src.agents.pipeline import AgentPipeline, PipelineResult
from src.agents.weighted_voting.base import WeightedVotingBase


class RandomizedWeightedMajority(WeightedVotingBase):
    """Master output is sampled with probability proportional to weights."""

    def __init__(
        self,
        pipelines: list[AgentPipeline],
        beta: float = 0.5,
        seed: Optional[int] = None,
    ) -> None:
        super().__init__(pipelines, beta=beta, seed=seed)
        self._rng = random.Random(seed)

    def _build_name(self) -> str:
        inner = ",".join(p.name for p in self.pipelines)
        return f"wmr([{inner}], beta={self.beta})"

    def _pick_master_output(self, results: list[PipelineResult]) -> PipelineResult:
        total = sum(self.weights)
        if total <= 0:
            # All weights collapsed, fallback to uniform random
            return self._rng.choice(results)
        idx = self._rng.choices(range(len(results)), weights=self.weights, k=1)[0]
        return results[idx]