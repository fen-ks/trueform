from trueform.config import HumanizeConfig, Strength, Tone
from trueform.pipeline.prompts import (
    build_refine_system_prompt,
    build_refine_user_prompt,
    _weak_signal_fixes,
)
from trueform.pipeline.scoring import HumanScore


def test_weak_signal_fixes_lists_low_burstiness():
    score = HumanScore(
        overall=40.0,
        burstiness=30.0,
        vocabulary=80.0,
        phrasing=80.0,
        contractions=80.0,
    )
    fixes = _weak_signal_fixes(score)
    assert any("sentence length" in f.lower() for f in fixes)
    assert not any("contractions" in f.lower() for f in fixes)


def test_refine_prompt_includes_score_and_fixes():
    score = HumanScore(
        overall=45.0,
        burstiness=20.0,
        vocabulary=90.0,
        phrasing=10.0,
        contractions=50.0,
        ai_tell_hits=5,
    )
    config = HumanizeConfig(target_score=70.0)
    system = build_refine_system_prompt(config, score)
    user = build_refine_user_prompt("Draft text here.", score)

    assert "45.0/100" in system
    assert "70.0" in system
    assert "sentence length" in system.lower() or "ai phrases" in system.lower()
    assert "Draft text here." in user
    assert "Refine" in user
