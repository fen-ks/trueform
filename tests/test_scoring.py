from trueform.pipeline.scoring import HumanScore, score_text


def test_human_text_scores_higher_than_ai_text():
    ai = (
        "In today's fast-paced world, it is important to note that we utilize "
        "technology. Furthermore, it is a powerful tool that can be leveraged. "
        "Moreover, it plays a crucial role. In conclusion, we must leverage it."
    )
    human = (
        "Tech moves fast. Honestly? Most of it barely matters. But a few tools "
        "genuinely changed how I work, and I can't imagine going back now."
    )
    assert score_text(human).overall > score_text(ai).overall


def test_ai_tell_phrases_are_counted():
    score = score_text("Furthermore, we utilize it. Moreover, it is important to note this.")
    assert score.ai_tell_hits >= 3
    assert score.phrasing < 60


def test_contractions_are_detected():
    score = score_text("I can't do it. You won't either. It's just how it is.")
    assert score.contractions > 0


def test_uniform_sentences_have_low_burstiness():
    uniform = "I went to the store today. I bought some food there. I came back home after."
    varied = "I went to the store. Then, after wandering the aisles for far too long "
    varied += "trying to decide, I finally grabbed food and left. Home again."
    assert score_text(varied).burstiness > score_text(uniform).burstiness


def test_score_shape_is_stable():
    score = score_text("A simple sentence.")
    assert isinstance(score, HumanScore)
    for field in ("overall", "burstiness", "vocabulary", "phrasing", "contractions"):
        value = getattr(score, field)
        assert 0.0 <= value <= 100.0
