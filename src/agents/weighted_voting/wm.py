from typing import Optional

from src.agents.pipeline import AgentPipeline, PipelineResult
from src.agents.weighted_voting.base import WeightedVotingBase


class WeightedMajority(WeightedVotingBase):

    def __init__(
        self,
        pipelines: list[AgentPipeline],
        beta: float = 0.5,
        seed: Optional[int] = None,
    ) -> None:
        super().__init__(pipelines, beta=beta, seed=seed)

    def _build_name(self) -> str:
        inner = ",".join(p.name for p in self.pipelines)
        return f"wm([{inner}], beta={self.beta})"

    def _pick_master_output(self, results: list[PipelineResult]) -> PipelineResult:
        max_weight = max(self.weights)
        idx = self.weights.index(max_weight)
        return results[idx]
