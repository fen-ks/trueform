"""Prompt construction for the humanization pass.

The system prompt encodes the *why* text reads as machine-generated (low
perplexity, low burstiness) and the concrete rewrite rules that counter it.
This is deliberately explicit so behavior is auditable and easy to tune.
"""

from __future__ import annotations

from trueform.config import HumanizeConfig, Strength, Tone

_TONE_GUIDANCE = {
    Tone.NATURAL: "a relaxed, natural voice — how a thoughtful person actually writes",
    Tone.CASUAL: "a casual, conversational voice with contractions and everyday word choices",
    Tone.PROFESSIONAL: "a clear, professional voice — polished but never stiff or robotic",
    Tone.ACADEMIC: "a careful academic voice that is still readable and human, not bloated",
    Tone.PERSONAL: "a warm, personal, first-person voice with genuine feeling",
}

_STRENGTH_GUIDANCE = {
    Strength.LIGHT: (
        "Make light edits only. Preserve the original wording where possible; "
        "fix the most robotic phrasing and vary a few sentence lengths."
    ),
    Strength.MEDIUM: (
        "Rewrite freely at the sentence level. Reshape phrasing and rhythm, "
        "but keep every fact, claim, and the overall structure intact."
    ),
    Strength.HEAVY: (
        "Rewrite aggressively. Restructure sentences and paragraph flow as needed "
        "to sound fully human, while preserving all meaning and information."
    ),
}

_CORE_RULES = """\
AI-generated text is flagged because it is statistically *too smooth*: every word
is highly predictable (low perplexity) and every sentence is about the same length
and shape (low burstiness). Your job is to reintroduce natural human irregularity
WITHOUT changing meaning.

Rewrite rules:
- Vary sentence length a lot. Mix short, punchy sentences with longer flowing ones.
- Break the uniform rhythm. Avoid every paragraph having the same cadence.
- Replace predictable, over-used connectors ("Furthermore", "Moreover", "In today's
  world", "It is important to note") with natural alternatives or cut them.
- Prefer concrete, specific wording over generic filler.
- Use contractions where they fit the tone.
- Allow small natural touches: a brief aside, a rhetorical question, mild informality.
- Do NOT invent facts, add fluff, or pad length. Keep the same information.
- Do NOT use em-dash pile-ups, listy "not only... but also" scaffolding, or the same
  three-item list pattern repeatedly — these are AI tells.

Output ONLY the rewritten text. No preamble, no explanation, no quotes around it.
"""


def build_system_prompt(config: HumanizeConfig) -> str:
    parts = [
        "You are trueform, an expert human editor. You take AI-assisted or stiff writing "
        "and make it read like a specific, real person wrote it.",
        f"Target voice: {_TONE_GUIDANCE[config.tone]}.",
        _STRENGTH_GUIDANCE[config.strength],
        _CORE_RULES,
    ]
    if config.style_profile:
        parts.append(_render_style_profile(config.style_profile))
    if config.extra_instructions:
        parts.append(f"Additional instructions from the user:\n{config.extra_instructions}")
    return "\n\n".join(parts)


def build_user_prompt(text: str) -> str:
    return f"Rewrite the following text according to your instructions.\n\nTEXT:\n{text}"


def _render_style_profile(profile: dict) -> str:
    # Placeholder for Phase 3 (style learning). Rendered defensively so passing a
    # profile early does no harm.
    lines = ["Match this writer's style profile as closely as possible:"]
    for k, v in profile.items():
        lines.append(f"- {k}: {v}")
    return "\n".join(lines)
