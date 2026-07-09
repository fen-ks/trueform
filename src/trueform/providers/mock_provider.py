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

# Applied on refine passes (when the prompt mentions human-likeness score).
_REFINE_REPLACEMENTS = {
    "In today's fast-paced world,": "These days,",
    "In today's fast-paced world": "These days",
    "it is important to note that": "",
    "important to note that": "",
    "leverage": "use",
    "increasingly prevalent": "common now",
    "plays a crucial role": "matters",
    "not only": "",
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

        if "human-likeness" in user_prompt.lower() or "refine the following" in user_prompt.lower():
            for src, dst in _REFINE_REPLACEMENTS.items():
                text = text.replace(src, dst)
            # Add burstiness: prepend a short sentence if the draft is still stiff.
            if not text.startswith("Honestly"):
                text = "Honestly? " + text[0].lower() + text[1:] if len(text) > 1 else text

        return text.strip()
