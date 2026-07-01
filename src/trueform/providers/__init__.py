"""Provider factory: turn a HumanizeConfig into a ready-to-use Provider.

Resolution order when `config.provider` is None (auto-detect):
    1. ANTHROPIC_API_KEY set  -> anthropic
    2. OPENAI_API_KEY set     -> openai
    3. otherwise              -> ollama (local, no key)
"""

from __future__ import annotations

import os

from trueform.config import HumanizeConfig
from trueform.providers.anthropic_provider import AnthropicProvider
from trueform.providers.base import Provider, ProviderError
from trueform.providers.mock_provider import MockProvider
from trueform.providers.ollama_provider import OllamaProvider
from trueform.providers.openai_provider import OpenAIProvider

__all__ = ["Provider", "ProviderError", "build_provider"]


def _auto_detect() -> str:
    if os.getenv("ANTHROPIC_API_KEY"):
        return "anthropic"
    if os.getenv("OPENAI_API_KEY"):
        return "openai"
    return "ollama"


def build_provider(config: HumanizeConfig) -> Provider:
    """Construct the appropriate provider from config + environment."""
    provider = (config.provider or _auto_detect()).lower()

    if provider == "mock":
        return MockProvider()

    if provider == "anthropic":
        key = config.api_key or os.getenv("ANTHROPIC_API_KEY", "")
        return AnthropicProvider(api_key=key, model=config.model, base_url=config.base_url)

    if provider == "openai":
        key = config.api_key or os.getenv("OPENAI_API_KEY", "")
        return OpenAIProvider(api_key=key, model=config.model, base_url=config.base_url)

    if provider == "ollama":
        return OllamaProvider(model=config.model, base_url=config.base_url)

    raise ProviderError(
        f"Unknown provider '{provider}'. Choose from: anthropic, openai, ollama, mock."
    )
