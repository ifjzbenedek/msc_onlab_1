from dataclasses import dataclass


@dataclass
class SolveConfig:
    writer_model: str
    reviewer_model: str
    max_iterations: int = 3