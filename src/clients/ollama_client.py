import logging
from typing import Optional
from ollama import Client

log = logging.getLogger(__name__)

class OllamaClient:

    def __init__(
        self,
        host: str,
        timeout: int = 300,
        default_temperature: float = 0.2,
        default_top_p: Optional[float] = None,
        default_top_k: Optional[int] = None,
        default_repeat_penalty: Optional[float] = None,
    ) -> None:
        self._client = Client(host=host, timeout=timeout)
        self._default_temperature = default_temperature
        self._default_top_p = default_top_p
        self._default_top_k = default_top_k
        self._default_repeat_penalty = default_repeat_penalty

    def generate(
        self,
        model: str,
        prompt: str,
        system: str = "",
        temperature: Optional[float] = None,
    ) -> str:
        if temperature is None:
            temperature = self._default_temperature

        options: dict = {"temperature": temperature}
        if self._default_top_p is not None:
            options["top_p"] = self._default_top_p
        if self._default_top_k is not None:
            options["top_k"] = self._default_top_k
        if self._default_repeat_penalty is not None:
            options["repeat_penalty"] = self._default_repeat_penalty

        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        log.info("Calling model=%s (prompt length=%d chars)", model, len(prompt))
        response = self._client.chat(
            model=model,
            messages=messages,
            options=options,
            keep_alive="30m",
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