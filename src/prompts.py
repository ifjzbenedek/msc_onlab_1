from src.models.problem import Problem

WRITER_SYSTEM = "You are an expert Python programmer. Return only code in a ```python``` block."

def writer_prompt(problem: Problem) -> str:
    return (
        f"Solve this LeetCode problem in Python. Return ONLY the code, no explanation.\n\n"
        f"{problem.title}\n\n"
        f"{problem.description}\n\n"
        f"Starting code:\n{problem.code_stub}"
    )


REVIEWER_SYSTEM = (
    "You are an expert code reviewer. "
    "Review the given solution and respond with ACCEPT or REVISE on the first line. "
    "If REVISE, explain what needs to be fixed."
)

def reviewer_prompt(problem: Problem, code: str) -> str:
    return (
        f"Review this Python solution for the following LeetCode problem.\n\n"
        f"## Problem\n{problem.title}\n\n"
        f"{problem.description}\n\n"
        f"## Submitted solution\n```python\n{code}\n```\n\n"
        f"First line: ACCEPT if correct, REVISE if not.\n"
        f"Then explain your reasoning."
    )


def writer_revision_prompt(problem: Problem, code: str, feedback: str) -> str:
    return (
        f"Your previous solution was reviewed and needs revision.\n\n"
        f"## Problem\n{problem.title}\n\n"
        f"{problem.description}\n\n"
        f"## Your previous solution\n```python\n{code}\n```\n\n"
        f"## Reviewer feedback\n{feedback}\n\n"
        f"Fix the issues and return ONLY the corrected code in a ```python``` block."
    )


def writer_error_prompt(problem: Problem, code: str, error_type: str, error_msg: str) -> str:
    return (
        f"Your solution has a {error_type}.\n\n"
        f"## Problem\n{problem.title}\n\n"
        f"{problem.description}\n\n"
        f"## Your solution\n```python\n{code}\n```\n\n"
        f"## Error message\n{error_msg}\n\n"
        f"Fix the error and return ONLY the corrected code in a ```python``` block."
    )
