"""Pipeline wrapper that runs an inner pipeline N times and picks the best result."""

from src.agents.pipeline import AgentPipeline, PipelineResult
from src.models.problem import Problem


class BestOfN:

    def __init__(self, inner: AgentPipeline, runs: int = 3) -> None:
        self.inner = inner
        self.runs = runs
        self.name = f"best_of_n({inner.name}, n={runs})"

    def run(self, problem: Problem) -> PipelineResult:
        results: list[PipelineResult] = []
        for _ in range(self.runs):
            results.append(self.inner.run(problem))

        best = _pick_best(results)
        best.voting_stats = _build_stats(results)
        return best


def _pick_best(results: list[PipelineResult]) -> PipelineResult:
    if not results:
        return PipelineResult(code=None)

    accepted = [r for r in results if r.submission and r.submission.accepted]
    if accepted:
        return accepted[0]

    with_submission = [r for r in results if r.submission]
    if with_submission:
        return min(with_submission, key=lambda r: _status_rank(r.submission.status))

    with_code = [r for r in results if r.code]
    if with_code:
        return with_code[0]

    return results[0]


_STATUS_PRIORITY = {
    "Accepted": 0,
    "Wrong Answer": 1,
    "Time Limit Exceeded": 2,
    "Memory Limit Exceeded": 3,
    "Runtime Error": 4,
    "Compile Error": 5,
}


def _status_rank(status: str) -> int:
    return _STATUS_PRIORITY.get(status, 99)


def _build_stats(results: list[PipelineResult]) -> dict:
    statuses: list[str] = []
    for r in results:
        if r.submission:
            statuses.append(r.submission.status)
        elif r.code:
            statuses.append("no submission")
        else:
            statuses.append("no code")

    return {
        "total_runs": len(results),
        "accepted": sum(1 for s in statuses if s == "Accepted"),
        "statuses": statuses,
    }
