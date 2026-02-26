import re

_CODE_BLOCK = re.compile(r"```(?:python)?\s*\n(.+?)```", re.DOTALL)


def extract_code(response: str) -> str | None:
    """Pull the first ```python``` block from the model response, or None if missing"""
    match = _CODE_BLOCK.search(response)
    return match.group(1).strip() if match else None
