"""Deterministic in-memory provider for tests and offline demos.

It performs a tiny rule-based "humanization" (expands a couple of stiff phrases
and adds a contraction) so the pipeline can be exercised end-to-end without any
network access or API key.
"""

from __future__ import annotations

from trueform.providers.base import Provider

_REPLACEMENTS = {
    "Furthermore,": "Also,",
    "Moreover,": "On top of that,",
    "In conclusion,": "So, to wrap up,",
    "utilize": "use",
    "it is": "it's",
    "do not": "don't",
    "cannot": "can't",
}


class MockProvider(Provider):
    name = "mock"

    def __init__(self, *args, **kwargs):
        pass

    def complete(
        self, system_prompt: str, user_prompt: str, *, temperature: float, max_tokens: int
    ) -> str:
        # The pipeline passes the source text as the last line of the user prompt
        # after a TEXT: marker; fall back to the whole prompt if not present.
        text = user_prompt
        marker = "TEXT:\n"
        if marker in user_prompt:
            text = user_prompt.split(marker, 1)[1]
        for src, dst in _REPLACEMENTS.items():
            text = text.replace(src, dst)
        return text.strip()
