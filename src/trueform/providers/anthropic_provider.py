"""Anthropic (Claude) provider using the raw Messages REST API via httpx.

We hit the REST endpoint directly rather than depend on the SDK so the whole
project stays light and every provider looks the same.
"""

from __future__ import annotations

import httpx

from trueform.providers.base import Provider, ProviderError

DEFAULT_MODEL = "claude-3-5-sonnet-latest"
API_URL = "https://api.anthropic.com/v1/messages"
API_VERSION = "2023-06-01"


class AnthropicProvider(Provider):
    name = "anthropic"

    def __init__(self, api_key: str, model: str | None = None, base_url: str | None = None):
        if not api_key:
            raise ProviderError(
                "No Anthropic API key. Set ANTHROPIC_API_KEY or pass --api-key."
            )
        self.api_key = api_key
        self.model = model or DEFAULT_MODEL
        self.url = base_url or API_URL

    def complete(
        self, system_prompt: str, user_prompt: str, *, temperature: float, max_tokens: int
    ) -> str:
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": API_VERSION,
            "content-type": "application/json",
        }
        payload = {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_prompt}],
        }
        try:
            resp = httpx.post(self.url, headers=headers, json=payload, timeout=120)
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise ProviderError(f"Anthropic API error {e.response.status_code}: {e.response.text}")
        except httpx.HTTPError as e:
            raise ProviderError(f"Anthropic request failed: {e}") from e

        data = resp.json()
        try:
            return "".join(block["text"] for block in data["content"] if block["type"] == "text")
        except (KeyError, TypeError) as e:
            raise ProviderError(f"Unexpected Anthropic response shape: {data}") from e
