from src.models.problem import Problem

# Mapping from LeetCode langSlug to display name and code fence tag
_LANG_DISPLAY = {
    "python3": ("Python", "python"),
    "java": ("Java", "java"),
    "cpp": ("C++", "cpp"),
}


def _lang_name(lang: str) -> str:
    """Human-readable language name."""
    return _LANG_DISPLAY.get(lang, (lang, lang))[0]


def _lang_tag(lang: str) -> str:
    """Code fence tag for the language."""
    return _LANG_DISPLAY.get(lang, (lang, lang))[1]


def writer_system(lang: str) -> str:
    """System prompt for the writer agent."""
    tag = _lang_tag(lang)
    return f"You are an expert {_lang_name(lang)} programmer. Return only code in a ```{tag}``` block."


def writer_prompt(problem: Problem) -> str:
    """Initial code generation prompt."""
    return (
        f"Solve this LeetCode problem in {_lang_name(problem.lang)}. Return ONLY the code, no explanation.\n\n"
        f"{problem.title}\n\n"
        f"{problem.description}\n\n"
        f"Starting code:\n{problem.code_stub}"
    )


def writer_revision_prompt(problem: Problem, code: str, feedback: str) -> str:
    """Prompt for revising code based on reviewer feedback."""
    tag = _lang_tag(problem.lang)
    return (
        f"Your previous solution was reviewed and needs revision.\n\n"
        f"## Problem\n{problem.title}\n\n"
        f"{problem.description}\n\n"
        f"## Your previous solution\n```{tag}\n{code}\n```\n\n"
        f"## Reviewer feedback\n{feedback}\n\n"
        f"Fix the issues and return ONLY the corrected code in a ```{tag}``` block."
    )


def writer_error_prompt(problem: Problem, code: str, error_type: str, error_msg: str) -> str:
    """Prompt for fixing code based on submission error."""
    tag = _lang_tag(problem.lang)
    return (
        f"Your solution has a {error_type}.\n\n"
        f"## Problem\n{problem.title}\n\n"
        f"{problem.description}\n\n"
        f"## Your solution\n```{tag}\n{code}\n```\n\n"
        f"## Error message\n{error_msg}\n\n"
        f"Fix the error and return ONLY the corrected code in a ```{tag}``` block."
    )