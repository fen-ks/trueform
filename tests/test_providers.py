import pytest

from trueform.config import HumanizeConfig
from trueform.providers import ProviderError, build_provider


def test_auto_detect_prefers_anthropic(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "x")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    assert build_provider(HumanizeConfig()).name == "anthropic"


def test_auto_detect_falls_back_to_ollama(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    assert build_provider(HumanizeConfig()).name == "ollama"


def test_explicit_mock():
    assert build_provider(HumanizeConfig(provider="mock")).name == "mock"


def test_unknown_provider_raises():
    with pytest.raises(ProviderError):
        build_provider(HumanizeConfig(provider="does-not-exist"))


def test_anthropic_without_key_raises(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(ProviderError):
        build_provider(HumanizeConfig(provider="anthropic"))
