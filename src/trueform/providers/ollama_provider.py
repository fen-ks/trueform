"""Ollama provider — fully local, free, private. No API key required.

Requires a running Ollama instance (https://ollama.com). Pull a model first,
e.g. `ollama pull llama3.1`, then trueform can use it with `--provider ollama`.
"""

from __future__ import annotations

import httpx

from trueform.providers.base import Provider, ProviderError

DEFAULT_MODEL = "llama3.1"
DEFAULT_URL = "http://localhost:11434/api/chat"


class OllamaProvider(Provider):
    name = "ollama"

    def __init__(self, model: str | None = None, base_url: str | None = None, api_key: str | None = None):
        # api_key is accepted and ignored so the factory can call every provider
        # with the same signature.
        self.model = model or DEFAULT_MODEL
        self.url = base_url or DEFAULT_URL

    def complete(
        self, system_prompt: str, user_prompt: str, *, temperature: float, max_tokens: int
    ) -> str:
        payload = {
            "model": self.model,
            "stream": False,
            "options": {"temperature": temperature, "num_predict": max_tokens},
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        try:
            resp = httpx.post(self.url, json=payload, timeout=300)
            resp.raise_for_status()
        except httpx.ConnectError as e:
            raise ProviderError(
                "Could not reach Ollama at "
                f"{self.url}. Is it running? Start it and `ollama pull {self.model}`."
            ) from e
        except httpx.HTTPError as e:
            raise ProviderError(f"Ollama request failed: {e}") from e

        data = resp.json()
        try:
            return data["message"]["content"]
        except (KeyError, TypeError) as e:
            raise ProviderError(f"Unexpected Ollama response shape: {data}") from e
