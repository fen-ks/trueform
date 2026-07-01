"""Configuration objects for a humanization run.

These are intentionally plain dataclasses so they are trivial to construct from
the CLI, a web request body, or a Python import without pulling in extra deps.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Tone(str, Enum):
    """Target register for the rewrite."""

    NATURAL = "natural"
    CASUAL = "casual"
    PROFESSIONAL = "professional"
    ACADEMIC = "academic"
    PERSONAL = "personal"


# How hard the humanizer is allowed to rewrite. Low = light touch-up that stays
# very close to the source; high = free to restructure sentences aggressively.
class Strength(str, Enum):
    LIGHT = "light"
    MEDIUM = "medium"
    HEAVY = "heavy"


@dataclass
class HumanizeConfig:
    """Everything the pipeline needs to know for one run.

    Provider/model/api_key are resolved lazily by the provider factory so that a
    caller can rely on environment variables (BYO key) instead of passing secrets
    around explicitly.
    """

    tone: Tone = Tone.NATURAL
    strength: Strength = Strength.MEDIUM

    # Provider selection. `None` means "auto-detect from environment".
    provider: str | None = None
    model: str | None = None
    api_key: str | None = None
    base_url: str | None = None

    temperature: float = 0.9
    max_tokens: int = 4096

    # Protect content that must survive verbatim (code, citations, URLs...).
    protect_code: bool = True
    protect_urls: bool = True

    # Free-form extra guidance appended to the system prompt.
    extra_instructions: str | None = None

    # Reserved for later phases (multi-pass, style profiles); kept here so the
    # public config shape is stable across versions.
    style_profile: dict | None = field(default=None, repr=False)
