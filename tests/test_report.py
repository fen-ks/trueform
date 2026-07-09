from trueform.pipeline.report import (
    MANUAL_CHECKLIST,
    CSV_COLUMNS,
    build_test_cases_csv,
    format_csv,
    format_report,
    overall_label,
    overall_summary,
)
from trueform.pipeline.scoring import score_text


def test_format_csv_has_header_and_scores():
    text = "Tech moves fast. Honestly? Most of it barely matters."
    csv_text = format_csv(text)
    lines = csv_text.strip().splitlines()
    assert lines[0] == ",".join(CSV_COLUMNS)
    assert "Tech moves fast" in lines[1]
    assert overall_label(score_text(text).overall) in lines[1]


def test_build_test_cases_csv_has_two_samples():
    csv_text = build_test_cases_csv()
    lines = csv_text.strip().splitlines()
    assert len(lines) == 3  # header + 2 samples
    assert "AI-style" in csv_text
    assert "Human-style" in csv_text


def test_overall_label_buckets():
    assert overall_label(85) == "Sounds very human"
    assert overall_label(65) == "Mostly natural - a few stiff spots"
    assert overall_label(45) == "Mixed - noticeable AI-style patterns"
    assert overall_label(20) == "Likely AI-written or very formal"


def test_overall_summary_is_plain_english():
    text = overall_summary(85)
    assert "perplexity" not in text.lower()
    assert "burstiness" not in text.lower()
    assert len(text) > 20


def test_format_report_includes_verdict_and_checklist():
    ai = (
        "In today's fast-paced world, it is important to note that we utilize "
        "technology. Furthermore, it is a powerful tool that can be leveraged."
    )
    report = format_report(ai)
    assert "WRITING QUALITY REPORT" in report
    assert "Overall score:" in report
    assert "Verdict:" in report
    assert "Sentence rhythm:" in report
    assert "MANUAL CHECKLIST" in report
    assert len(MANUAL_CHECKLIST) >= 5
    for title, _ in MANUAL_CHECKLIST:
        assert title in report


def test_human_text_report_scores_higher_in_verdict():
    ai = (
        "In today's fast-paced world, it is important to note that we utilize "
        "technology. Furthermore, it is a powerful tool that can be leveraged. "
        "Moreover, it plays a crucial role. In conclusion, we must leverage it."
    )
    human = (
        "Tech moves fast. Honestly? Most of it barely matters. But a few tools "
        "genuinely changed how I work, and I can't imagine going back now."
    )
    ai_score = score_text(ai).overall
    human_score = score_text(human).overall
    assert human_score > ai_score
    assert "AI-style phrases found:" in format_report(ai)
    assert format_report(human, score=score_text(human))
