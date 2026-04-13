import logging

from src.clients.ollama_client import OllamaClient
from src.models.problem import Problem
from src.prompts.orchestrator import ORCHESTRATOR_SYSTEM, orchestrator_prompt

log = logging.getLogger(__name__)


class LLMRouter:
    """LLM analyzes the problem and picks a pipeline."""

    def __init__(self, ollama: OllamaClient, model: str) -> None:
        self.ollama = ollama
        self.model = model

    def choose(self, problem: Problem, options: list[str]) -> str:
        raw = self.ollama.generate(
            model=self.model,
            prompt=orchestrator_prompt(problem, options),
            system=ORCHESTRATOR_SYSTEM,
        )
        choice = raw.strip().split("\n")[0].strip()

        # Find the option that best matches the response (with fuzzy matching)
        for opt in options:
            if opt.lower() in choice.lower() or choice.lower() in opt.lower():
                log.info("LLMRouter chose: %s", opt)
                return opt

        log.warning("LLMRouter response '%s' not recognized, using first option", choice)
        return options[0]