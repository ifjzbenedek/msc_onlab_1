"""Client for the remote Ollama API (accessed via SSH tunnel)."""

import logging

from ollama import Client

log = logging.getLogger(__name__)


class OllamaClient:

    def __init__(self, host: str, timeout: int = 300) -> None:
        self._client = Client(host=host, timeout=timeout)

    def generate(
        self,
        model: str,
        prompt: str,
        system: str = "",
        temperature: float = 0.2,
    ) -> str:
        
        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        log.info("Calling model=%s (prompt length=%d chars)", model, len(prompt))
        response = self._client.chat(
            model=model,
            messages=messages,
            options={"temperature": temperature},
        )
        text = response.message.content
        log.info("Response: %d chars", len(text))
        return text

    def list_models(self) -> list[str]:
        response = self._client.list()
        return [m.model for m in response.models]

    def ping(self, model: str = "tinyllama") -> bool:
        try:
            reply = self.generate(model=model, prompt="Say OK.", temperature=0.0)
            return len(reply) > 0
        except Exception as exc:
            log.error("Ping failed: %s", exc)
            return False