"""The humanization engine.

v0.1 runs a single, well-engineered rewrite pass with content protection. The
class is structured so later phases (analyze -> rewrite -> verify -> refine,
local perplexity scoring, style profiles) slot in without changing the public
`humanize()` signature.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from trueform.config import HumanizeConfig
from trueform.pipeline.prompts import build_system_prompt, build_user_prompt
from trueform.pipeline.protect import Protector
from trueform.providers import Provider, build_provider


@dataclass
class HumanizeResult:
    """Outcome of a humanization run."""

    text: str
    original: str
    provider: str
    model: str | None = None
    # Populated by later phases (scoring, explainability). Present now so callers
    # can rely on a stable shape.
    scores: dict = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)


class Humanizer:
    """Orchestrates a humanization run for a given config."""

    def __init__(self, config: HumanizeConfig | None = None, provider: Provider | None = None):
        self.config = config or HumanizeConfig()
        self.provider = provider or build_provider(self.config)

    def run(self, text: str) -> HumanizeResult:
        if not text or not text.strip():
            raise ValueError("Nothing to humanize: input text is empty.")

        protector = Protector(
            protect_code=self.config.protect_code,
            protect_urls=self.config.protect_urls,
        )
        masked = protector.mask(text)

        system_prompt = build_system_prompt(self.config)
        user_prompt = build_user_prompt(masked)

        rewritten = self.provider.complete(
            system_prompt,
            user_prompt,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
        )

        restored = protector.restore(rewritten.strip())

        return HumanizeResult(
            text=restored,
            original=text,
            provider=self.provider.name,
            model=self.config.model,
        )


def humanize(text: str, config: HumanizeConfig | None = None) -> str:
    """Convenience one-liner: humanize text and return the string."""
    return Humanizer(config).run(text).text
