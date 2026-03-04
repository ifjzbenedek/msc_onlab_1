import re

_CODE_BLOCK = re.compile(r"```(?:python)?\s*\n(.+?)```", re.DOTALL)


def extract_code(response: str) -> str | None:
    match = _CODE_BLOCK.search(response)
    return match.group(1).strip() if match else None


def parse_review(response: str) -> tuple[bool, str]:
    first_line = response.strip().split("\n", 1)[0].upper()
    accepted = "ACCEPT" in first_line
    feedback = response.strip()
    return accepted, feedback