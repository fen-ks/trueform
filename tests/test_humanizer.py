import pytest

from trueform import HumanizeConfig, Humanizer, humanize
from trueform.config import Tone
from trueform.pipeline.scoring import score_text
from trueform.providers.base import Provider


def _mock_config(**kw):
    return HumanizeConfig(provider="mock", **kw)


def test_humanize_runs_with_mock_provider():
    out = humanize("It is important. We utilize this. Furthermore, it is good.", _mock_config())
    # Mock provider applies simple substitutions.
    assert "it's" in out
    assert "use" in out
    assert "Also," in out
    assert "Furthermore," not in out


def test_result_metadata():
    result = Humanizer(_mock_config(tone=Tone.CASUAL)).run("do not worry")
    assert result.provider == "mock"
    assert result.original == "do not worry"
    assert "don't" in result.text
    assert isinstance(result.scores, dict)
    assert "before" in result.scores
    assert "after" in result.scores


def test_empty_input_raises():
    with pytest.raises(ValueError):
        Humanizer(_mock_config()).run("   ")


def test_code_is_protected_through_pipeline():
    text = "We utilize `keep_me()` here."
    out = humanize(text, _mock_config())
    assert "`keep_me()`" in out
    assert "use" in out  # prose around it was still humanized


def test_single_pass_skips_refinement_loop():
    text = (
        "In today's fast-paced world, it is important to note that we utilize "
        "technology. Furthermore, it is a powerful tool."
    )
    result = Humanizer(_mock_config(max_passes=1)).run(text)
    assert result.scores["pass_count"] == 1
    assert len(result.scores["passes"]) == 1


def test_multi_pass_improves_score_on_stiff_text():
    text = (
        "In today's fast-paced world, it is important to note that we utilize "
        "technology. Furthermore, it is a powerful tool that can be leveraged. "
        "Moreover, it plays a crucial role. In conclusion, we must leverage it."
    )
    before = score_text(text).overall
    result = Humanizer(_mock_config(max_passes=3, target_score=70.0, min_improvement=0.5)).run(text)
    after = result.scores["after"]["overall"]
    assert after > before
    assert result.scores["pass_count"] >= 2


def test_multi_pass_stops_when_target_met():
    text = "It is important. We utilize this. Furthermore, it is good."
    result = Humanizer(_mock_config(max_passes=5, target_score=50.0)).run(text)
    assert result.scores["target_met"] is True
    assert result.scores["pass_count"] <= 5


class _FlatProvider(Provider):
    """Returns the same text every pass — used to test early-stop on no improvement."""

    name = "flat"

    def complete(self, system_prompt, user_prompt, *, temperature, max_tokens):
        marker = "TEXT:\n"
        return user_prompt.split(marker, 1)[1].strip() if marker in user_prompt else user_prompt


def test_multi_pass_stops_when_improvement_stalls():
    text = "Furthermore, we utilize it."
    result = Humanizer(
        HumanizeConfig(provider="mock", max_passes=5, target_score=99.0, min_improvement=5.0),
        provider=_FlatProvider(),
    ).run(text)
    assert result.scores["pass_count"] <= 2
