"""Provider abstraction.

A provider is anything that can turn a (system_prompt, user_prompt) pair into a
completion string. Keeping this interface tiny means adding a new backend (a new
API, a local model, a mock for tests) is a ~30-line file.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class ProviderError(RuntimeError):
    """Raised when a provider cannot fulfill a request (auth, network, etc.)."""


class Provider(ABC):
    """Minimal LLM backend interface."""

    name: str = "base"

    @abstractmethod
    def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        temperature: float,
        max_tokens: int,
    ) -> str:
        """Return the model's text completion for the given prompts."""
        raise NotImplementedError
