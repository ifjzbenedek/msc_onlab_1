import math
import random
from typing import Optional

from src.agents.pipeline import AgentPipeline, PipelineResult
from src.models.problem import Problem


class Exp3:
    """Exponential-weight exploration-exploitation bandit."""

    def __init__(
        self,
        pipelines: list[AgentPipeline],
        gamma: float = 0.1,
        seed: Optional[int] = None,
    ) -> None:
        if not pipelines:
            raise ValueError("pipelines must be non-empty")
        if not 0.0 < gamma <= 1.0:
            raise ValueError(f"gamma must be in (0, 1], got {gamma}")
        self.pipelines = pipelines
        self.gamma = gamma
        self.weights: list[float] = [1.0] * len(pipelines)
        self._rng = random.Random(seed)
        inner = ",".join(p.name for p in pipelines)
        self.name = f"exp3([{inner}], gamma={gamma})"

    def run(self, problem: Problem) -> PipelineResult:
        weights_before = list(self.weights)
        probs = self._distribution()
        idx = self._rng.choices(range(len(self.pipelines)), weights=probs, k=1)[0]

        result = self.pipelines[idx].run(problem)
        reward = 1.0 if (result.submission and result.submission.accepted) else 0.0

        # importance-weighted update, only the sampled arm
        estimated_reward = reward / probs[idx]
        k = len(self.pipelines)
        self.weights[idx] *= math.exp(self.gamma * estimated_reward / k)

        result.voting_stats = {
            "pipeline_names": [p.name for p in self.pipelines],
            "weights_before": weights_before,
            "weights_after": list(self.weights),
            "probs": probs,
            "sampled_pipeline": self.pipelines[idx].name,
            "reward": reward,
            "any_accepted": bool(reward),
        }
        return result

    def _distribution(self) -> list[float]:
        """Mix the current weight distribution with uniform exploration."""
        total = sum(self.weights)
        k = len(self.pipelines)
        if total <= 0:
            return [1.0 / k] * k
        return [
            (1.0 - self.gamma) * (w / total) + self.gamma / k
            for w in self.weights
        ]