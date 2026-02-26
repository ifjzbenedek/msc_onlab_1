from src.models.problem import Problem

WRITER_SYSTEM = "You are an expert Python programmer. Return only code in a ```python``` block."

def writer_prompt(problem: Problem) -> str:
    return (
        f"Solve this LeetCode problem in Python. Return ONLY the code, no explanation.\n\n"
        f"{problem.title}\n\n"
        f"{problem.description}\n\n"
        f"Starting code:\n{problem.code_stub}"
    )
