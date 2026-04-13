from src.models.problem import Problem
from src.prompts.writer import _lang_name, _lang_tag


DEBATE_JUDGE_SYSTEM = (
    "You are an expert judge evaluating two code solutions. "
    "Compare them and pick the better one, or combine the best parts of both."
)


def debate_critique_prompt(problem: Problem, own_code: str, opponent_code: str) -> str:
    """Ask a writer to critique the opponent's code and improve their own."""
    tag = _lang_tag(problem.lang)
    return (
        f"You are solving a LeetCode problem. Another programmer proposed a different solution.\n\n"
        f"## Problem\n{problem.title}\n\n"
        f"{problem.description}\n\n"
        f"## Your solution\n```{tag}\n{own_code}\n```\n\n"
        f"## Opponent's solution\n```{tag}\n{opponent_code}\n```\n\n"
        f"Critique the opponent's solution, then return your improved solution "
        f"in a ```{tag}``` block."
    )


def debate_judge_prompt(problem: Problem, code_a: str, code_b: str) -> str:
    """Ask the judge to pick the better solution or merge them."""
    tag = _lang_tag(problem.lang)
    return (
        f"Two programmers proposed solutions for the following problem.\n\n"
        f"## Problem\n{problem.title}\n\n"
        f"{problem.description}\n\n"
        f"## Solution A\n```{tag}\n{code_a}\n```\n\n"
        f"## Solution B\n```{tag}\n{code_b}\n```\n\n"
        f"Pick the better solution or combine the best parts of both.\n"
        f"Return ONLY the final code in a ```{tag}``` block."
    )
