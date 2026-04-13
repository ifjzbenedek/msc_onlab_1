"""Coopetition Merge prompts: combine two independent solutions."""

from src.models.problem import Problem
from src.prompts.writer import _lang_name, _lang_tag


MERGER_SYSTEM = (
    "You are an expert programmer. Given two solutions to the same problem, "
    "analyze both and produce the best possible solution by combining their strengths."
)


def merger_prompt(problem: Problem, code_a: str, code_b: str) -> str:
    """Ask the merger to combine two solutions."""
    tag = _lang_tag(problem.lang)
    return (
        f"Two models produced different solutions for this problem.\n\n"
        f"## Problem\n{problem.title}\n\n"
        f"{problem.description}\n\n"
        f"## Solution A\n```{tag}\n{code_a}\n```\n\n"
        f"## Solution B\n```{tag}\n{code_b}\n```\n\n"
        f"Analyze both. Pick the better one, or merge the best parts into one solution.\n"
        f"Return ONLY the final code in a ```{tag}``` block."
    )
