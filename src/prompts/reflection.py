"""Self-Reflection prompts: learn from errors before fixing."""

from src.models.problem import Problem
from src.prompts.writer import _lang_tag


REFLECTION_SYSTEM = (
    "You are an expert programmer who learns from mistakes. "
    "When given a failed submission, first reflect on what went wrong and why, "
    "then produce a corrected solution."
)


def reflection_prompt(
    problem: Problem,
    code: str,
    error_type: str,
    error_msg: str,
    past_reflections: list[str],
) -> str:
    """Ask the writer to reflect on the error and produce a fix."""
    tag = _lang_tag(problem.lang)
    history = ""
    if past_reflections:
        numbered = "\n".join(f"{i+1}. {r}" for i, r in enumerate(past_reflections))
        history = f"## Lessons from previous attempts\n{numbered}\n\n"

    return (
        f"Your solution failed with {error_type}.\n\n"
        f"## Problem\n{problem.title}\n\n"
        f"{problem.description}\n\n"
        f"## Your solution\n```{tag}\n{code}\n```\n\n"
        f"## Error\n{error_msg}\n\n"
        f"{history}"
        f"First, write a short REFLECTION (1-3 sentences) on what went wrong.\n"
        f"Then return the corrected code in a ```{tag}``` block."
    )
