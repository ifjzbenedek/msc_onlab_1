import logging
import time

from src.agents.pipeline import AgentPipeline, PipelineResult
from src.agents.routers import Router
from src.models.problem import Problem
from src.models.result import AgentStep

log = logging.getLogger(__name__)


class Orchestrator:
    """Picks the best pipeline for each problem using a Router."""

    def __init__(
        self,
        pipelines: dict[str, AgentPipeline],
        router: Router,
        name: str = "orchestrator",
    ) -> None:
        self.pipelines = pipelines
        self.router = router
        self.name = name

    def run(self, problem: Problem) -> PipelineResult:
        options = list(self.pipelines.keys())

        t0 = time.time()
        chosen = self.router.choose(problem, options)
        route_time = round(time.time() - t0, 1)

        log.info("Orchestrator routed '%s' to: %s", problem.title, chosen)

        # Record the routing decision
        route_step = AgentStep(
            role="orchestrator",
            model=getattr(self.router, "model", "rule-based"),
            round_number=0,
            action="route",
            content=chosen,
            duration_seconds=route_time,
            metadata={"chosen_pipeline": chosen},
        )

        # Run the chosen pipeline
        result = self.pipelines[chosen].run(problem)

        result.steps.insert(0, route_step)

        return result
