import logging

from src.models.problem import Problem

log = logging.getLogger(__name__)


class RuleRouter:
    """Routes based on problem difficulty field."""

    def __init__(self, mapping: dict[str, str]) -> None:
        self.mapping = mapping

    def choose(self, problem: Problem, options: list[str]) -> str:
        choice = self.mapping.get(problem.difficulty, options[0])
        if choice not in options:
            log.warning("RuleRouter mapped to '%s' but not in options, using first", choice)
            return options[0]
        log.info("RuleRouter chose: %s (difficulty=%s)", choice, problem.difficulty)
        return choice