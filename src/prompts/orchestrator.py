from src.models.problem import Problem


ORCHESTRATOR_SYSTEM = (
    "You are a task router. Given a programming problem, decide which solving "
    "strategy is best. Respond with ONLY one of the given options, nothing else."
)


def orchestrator_prompt(problem: Problem, options: list[str]) -> str:
    options_str = "\n".join(f"- {opt}" for opt in options)
    return (
        f"Which strategy should be used to solve this problem?\n\n"
        f"## {problem.title} ({problem.difficulty})\n\n"
        f"{problem.description}\n\n"
        f"Options:\n{options_str}\n\n"
        f"Respond with ONLY the strategy name."
    )
