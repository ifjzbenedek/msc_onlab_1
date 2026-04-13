from src.models.problem import Problem
from src.prompts.writer import _lang_name, _lang_tag


PLANNER_SYSTEM = (
    "You are an expert algorithm designer. Given a problem, produce a clear, "
    "step-by-step plan (pseudocode or bullet points). Do NOT write actual code."
)


def planner_prompt(problem: Problem) -> str:
    """Ask the planner to design an algorithm"""
    return (
        f"Design an algorithm for this LeetCode problem. "
        f"Return a step-by-step plan, NOT code.\n\n"
        f"## {problem.title}\n\n"
        f"{problem.description}\n\n"
        f"Think about edge cases and time complexity."
    )


def writer_from_plan_prompt(problem: Problem, plan: str) -> str:
    """Ask the writer to implement code from a plan"""
    tag = _lang_tag(problem.lang)
    return (
        f"Implement the following algorithm plan in {_lang_name(problem.lang)}.\n\n"
        f"## Problem\n{problem.title}\n\n"
        f"{problem.description}\n\n"
        f"## Algorithm plan\n{plan}\n\n"
        f"Starting code:\n{problem.code_stub}\n\n"
        f"Return ONLY the code in a ```{tag}``` block."
    )