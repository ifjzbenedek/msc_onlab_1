import random
from typing import Optional

from src.agents.pipeline import AgentPipeline, PipelineResult
from src.models.problem import Problem


class RandomizedWeightedMajorityWithRetry:
    """WMR variant that retries only on failure, sampling without replacement."""

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
        self.weights: list[float] = [1.0] * len(pipelines)
        self._rng = random.Random(seed)
        inner = ",".join(p.name for p in pipelines)
        self.name = f"wmr-retry([{inner}], beta={beta})"

    def run(self, problem: Problem) -> PipelineResult:
        weights_before = list(self.weights)
        remaining = list(range(len(self.pipelines)))
        attempts: list[tuple[int, PipelineResult]] = []

        while remaining:
            idx = self._sample_from(remaining)
            result = self.pipelines[idx].run(problem)
            attempts.append((idx, result))

            if self._is_correct(result):
                break

            self.weights[idx] *= self.beta
            remaining.remove(idx)

        final_idx, final_result = attempts[-1]
        final_result.voting_stats = {
            "pipeline_names": [p.name for p in self.pipelines],
            "weights_before": weights_before,
            "weights_after": list(self.weights),
            "attempts": [
                {"pipeline": self.pipelines[i].name, "accepted": self._is_correct(r)}
                for i, r in attempts
            ],
            "final_pipeline": self.pipelines[final_idx].name,
            "any_accepted": self._is_correct(final_result),
        }
        return final_result

    def _sample_from(self, indices: list[int]) -> int:
        sub_weights = [self.weights[i] for i in indices]
        total = sum(sub_weights)
        if total <= 0:
            return self._rng.choice(indices)
        return self._rng.choices(indices, weights=sub_weights, k=1)[0]

    @staticmethod
    def _is_correct(result: PipelineResult) -> bool:
        return bool(result.submission and result.submission.accepted)