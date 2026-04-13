from typing import Protocol

from src.models.problem import Problem


class Router(Protocol):
    
    def choose(self, problem: Problem, options: list[str]) -> str: ...