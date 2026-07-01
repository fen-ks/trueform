import pytest

from trueform import HumanizeConfig, Humanizer, humanize
from trueform.config import Tone


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


def test_empty_input_raises():
    with pytest.raises(ValueError):
        Humanizer(_mock_config()).run("   ")


def test_code_is_protected_through_pipeline():
    text = "We utilize `keep_me()` here."
    out = humanize(text, _mock_config())
    assert "`keep_me()`" in out
    assert "use" in out  # prose around it was still humanized
