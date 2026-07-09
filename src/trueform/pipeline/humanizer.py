"""The humanization engine.

v0.5 runs a multi-pass loop: rewrite -> score -> refine until the human-likeness
target is met or max_passes is reached. A single pass is still available via
max_passes=1.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from trueform.config import HumanizeConfig
from trueform.pipeline.prompts import (
    build_refine_system_prompt,
    build_refine_user_prompt,
    build_system_prompt,
    build_user_prompt,
)
from trueform.pipeline.protect import Protector
from trueform.pipeline.scoring import HumanScore, score_text
from trueform.providers import Provider, build_provider


@dataclass
class HumanizeResult:
    """Outcome of a humanization run."""

    text: str
    original: str
    provider: str
    model: str | None = None
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

        before = score_text(text)
        best_text = text
        best_score = before
        pass_history: list[dict] = []
        notes: list[str] = []
        current = text
        previous_best = before.overall

        for pass_num in range(1, max(1, self.config.max_passes) + 1):
            if pass_num == 1:
                draft_score = before
            else:
                draft_score = score_text(current)
                if draft_score.overall >= self.config.target_score:
                    notes.append(
                        f"Target {self.config.target_score} already met before pass {pass_num}; "
                        "stopping."
                    )
                    break

            rewritten = self._rewrite_pass(
                current,
                protector,
                refine_score=draft_score if pass_num > 1 else None,
            )
            after = score_text(rewritten)

            pass_history.append(
                {
                    "pass": pass_num,
                    "score": after.to_dict(),
                    "improved": after.overall > best_score.overall,
                }
            )

            if after.overall > best_score.overall:
                best_text = rewritten
                best_score = after

            if best_score.overall >= self.config.target_score:
                notes.append(
                    f"Target score {self.config.target_score} reached on pass {pass_num}."
                )
                break

            if pass_num > 1:
                gain = best_score.overall - previous_best
                if gain < self.config.min_improvement:
                    notes.append(
                        f"Stopped after pass {pass_num}: improvement ({gain:.1f}) below "
                        f"min_improvement ({self.config.min_improvement})."
                    )
                    break
                previous_best = best_score.overall

            if pass_num >= self.config.max_passes:
                if best_score.overall < self.config.target_score:
                    notes.append(
                        f"Stopped after {self.config.max_passes} passes "
                        f"(target {self.config.target_score} not reached)."
                    )
                break

            current = best_text

        return HumanizeResult(
            text=best_text,
            original=text,
            provider=self.provider.name,
            model=self.config.model,
            scores={
                "before": before.to_dict(),
                "after": best_score.to_dict(),
                "passes": pass_history,
                "pass_count": len(pass_history),
                "target_score": self.config.target_score,
                "target_met": best_score.overall >= self.config.target_score,
            },
            notes=notes,
        )

    def _rewrite_pass(
        self,
        text: str,
        protector: Protector,
        *,
        refine_score: HumanScore | None,
    ) -> str:
        masked = protector.mask(text)

        if refine_score is None:
            system_prompt = build_system_prompt(self.config)
            user_prompt = build_user_prompt(masked)
        else:
            system_prompt = build_refine_system_prompt(self.config, refine_score)
            user_prompt = build_refine_user_prompt(masked, refine_score)

        rewritten = self.provider.complete(
            system_prompt,
            user_prompt,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
        )
        return protector.restore(rewritten.strip())


def humanize(text: str, config: HumanizeConfig | None = None) -> str:
    """Convenience one-liner: humanize text and return the string."""
    return Humanizer(config).run(text).text
