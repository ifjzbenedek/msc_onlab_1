"""Reviewer agent prompts: code review and critique."""

from src.models.problem import Problem
from src.prompts.writer import _lang_name, _lang_tag


REVIEWER_SYSTEM = (
    "You are an expert code reviewer. "
    "Review the given solution and respond with ACCEPT or REVISE on the first line. "
    "If REVISE, explain what needs to be fixed."
)


def reviewer_prompt(problem: Problem, code: str) -> str:
    """Standard code review prompt."""
    tag = _lang_tag(problem.lang)
    return (
        f"Review this {_lang_name(problem.lang)} solution for the following LeetCode problem.\n\n"
        f"## Problem\n{problem.title}\n\n"
        f"{problem.description}\n\n"
        f"## Submitted solution\n```{tag}\n{code}\n```\n\n"
        f"First line: ACCEPT if correct, REVISE if not.\n"
        f"Then explain your reasoning."
    )
