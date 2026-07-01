"""OpenAI provider using the Chat Completions REST API via httpx.

Also works with any OpenAI-compatible endpoint (set base_url), e.g. local
servers, OpenRouter, Groq, etc.
"""

from __future__ import annotations

import httpx

from trueform.providers.base import Provider, ProviderError

DEFAULT_MODEL = "gpt-4o-mini"
DEFAULT_URL = "https://api.openai.com/v1/chat/completions"


class OpenAIProvider(Provider):
    name = "openai"

    def __init__(self, api_key: str, model: str | None = None, base_url: str | None = None):
        if not api_key:
            raise ProviderError("No OpenAI API key. Set OPENAI_API_KEY or pass --api-key.")
        self.api_key = api_key
        self.model = model or DEFAULT_MODEL
        self.url = base_url or DEFAULT_URL

    def complete(
        self, system_prompt: str, user_prompt: str, *, temperature: float, max_tokens: int
    ) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        try:
            resp = httpx.post(self.url, headers=headers, json=payload, timeout=120)
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise ProviderError(f"OpenAI API error {e.response.status_code}: {e.response.text}")
        except httpx.HTTPError as e:
            raise ProviderError(f"OpenAI request failed: {e}") from e

        data = resp.json()
        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as e:
            raise ProviderError(f"Unexpected OpenAI response shape: {data}") from e
