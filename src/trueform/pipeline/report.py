"""Plain-English reports for human-likeness scores.

Designed for non-technical readers: editors, QA testers, and content reviewers
who need to understand *why* a piece of writing scored the way it did.
"""

from __future__ import annotations

import csv
import io

from trueform.pipeline.scoring import HumanScore, score_text

# Friendly labels and short explanations for each measured signal.
_SIGNALS: tuple[tuple[str, str, str], ...] = (
    (
        "burstiness",
        "Sentence rhythm",
        "Do your sentences vary in length? Human writing mixes short punchy lines "
        "with longer ones. Robot-like text often uses sentences that are all about "
        "the same size.",
    ),
    (
        "vocabulary",
        "Word variety",
        "Do you repeat the same words over and over? Natural writing reuses fewer "
        "words than stiff, template-style text.",
    ),
    (
        "phrasing",
        "Natural phrasing",
        'Does the text avoid stock AI phrases like "Furthermore," "In conclusion," '
        'or "It is important to note"? These show up far more often in AI drafts.',
    ),
    (
        "contractions",
        "Conversational tone",
        'Do you use contractions like "don\'t" and "can\'t"? Their absence is not '
        "always wrong, but fully formal phrasing everywhere can feel machine-made.",
    ),
)

# Manual checklist items a non-technical tester can tick off.
MANUAL_CHECKLIST: tuple[tuple[str, str], ...] = (
    (
        "Rhythm",
        "Read it aloud. Does it sound like a person talking, or like a brochure?",
    ),
    (
        "Opener",
        'Does it avoid starting with "In today\'s fast-paced world" or similar filler?',
    ),
    (
        "Connectors",
        'Are words like "Furthermore," "Moreover," and "In conclusion" absent or rare?',
    ),
    (
        "Buzzwords",
        'Are buzzwords like "leverage," "utilize," "robust," and "seamless" gone or '
        "replaced with plain words?",
    ),
    (
        "Meaning",
        "After any rewrite, does the text still say the same thing?",
    ),
    (
        "Your voice",
        "Would you actually write this, or does it still feel like a generic template?",
    ),
)


def overall_label(overall: float) -> str:
    """One-line verdict for the combined score."""
    if overall >= 80:
        return "Sounds very human"
    if overall >= 60:
        return "Mostly natural - a few stiff spots"
    if overall >= 40:
        return "Mixed - noticeable AI-style patterns"
    return "Likely AI-written or very formal"


def overall_summary(overall: float) -> str:
    """A short paragraph explaining what the overall number means."""
    label = overall_label(overall)
    if overall >= 80:
        detail = (
            "The writing has varied rhythm, plain phrasing, and few obvious "
            "AI tells. It should read naturally to most people."
        )
    elif overall >= 60:
        detail = (
            "The writing is close, but you may still spot uniform sentences or "
            "a formal tone in places. A light edit could help."
        )
    elif overall >= 40:
        detail = (
            "Several patterns commonly seen in AI text are still present - "
            "similar sentence lengths, filler phrases, or corporate wording."
        )
    else:
        detail = (
            "The text shows strong signs of AI-style writing: repeated filler "
            "phrases, very even sentence rhythm, and stiff word choices."
        )
    return f"{label}. {detail}"


def _signal_label(value: float) -> str:
    if value >= 75:
        return "Good"
    if value >= 50:
        return "Okay"
    if value >= 25:
        return "Needs work"
    return "Poor"


def _signal_note(key: str, value: float, score: HumanScore) -> str:
    if key == "burstiness":
        if value >= 75:
            return "Sentence lengths vary nicely - good natural rhythm."
        if value >= 50:
            return "Some variation, but sentences are still a bit same-y."
        return (
            f"Sentences are very uniform (average length: {score.avg_sentence_len} words). "
            "Try mixing one short sentence with a longer one."
        )

    if key == "vocabulary":
        if value >= 75:
            return "Good word variety for the length of the text."
        if value >= 50:
            return "Acceptable variety; watch for repeated filler words."
        return "Lots of repeated wording - try swapping in plainer synonyms."

    if key == "phrasing":
        hits = score.ai_tell_hits
        if hits == 0:
            return "No common AI phrases detected."
        if hits == 1:
            return "One common AI phrase detected - consider rewording it."
        return f"{hits} common AI phrases detected - reword or cut them."

    if key == "contractions":
        if value >= 75:
            return "Contractions give the text a conversational feel."
        if value >= 50:
            return "Some conversational tone; could add a contraction or two if it fits."
        return "Very formal throughout - fine for legal text, stiff for blogs or email."

    return ""


def format_report(text: str, *, score: HumanScore | None = None) -> str:
    """Return a plain-English report for `text` (scores it if `score` is omitted)."""
    result = score if score is not None else score_text(text)
    lines: list[str] = []

    lines.append("WRITING QUALITY REPORT")
    lines.append("=" * 50)
    lines.append("")
    lines.append(f"Overall score: {result.overall} / 100")
    lines.append(f"Verdict: {overall_label(result.overall)}")
    lines.append("")
    lines.append(overall_summary(result.overall))
    lines.append("")
    lines.append("WHAT WE CHECKED")
    lines.append("-" * 50)

    for key, title, description in _SIGNALS:
        value = getattr(result, key)
        lines.append("")
        lines.append(f"{title}: {value:.0f} / 100 ({_signal_label(value)})")
        lines.append(description)
        lines.append(f"-> {_signal_note(key, value, result)}")

    lines.append("")
    lines.append("QUICK FACTS")
    lines.append("-" * 50)
    lines.append(f"- Sentences: {result.sentence_count}")
    lines.append(f"- Average sentence length: {result.avg_sentence_len} words")
    lines.append(f"- AI-style phrases found: {result.ai_tell_hits}")
    lines.append("")
    lines.append("MANUAL CHECKLIST (for testers)")
    lines.append("-" * 50)
    lines.append("Tick each item after you read the text:")
    lines.append("")

    for title, question in MANUAL_CHECKLIST:
        lines.append(f"[ ] {title} - {question}")

    lines.append("")
    lines.append("SCORE GUIDE")
    lines.append("-" * 50)
    lines.append("80-100  Sounds very human")
    lines.append("60-79   Mostly natural")
    lines.append("40-59   Mixed / some AI patterns")
    lines.append("0-39    Likely AI-written or very stiff")

    return "\n".join(lines)


CSV_COLUMNS = (
    "text",
    "overall_score",
    "verdict",
    "sentence_rhythm",
    "word_variety",
    "natural_phrasing",
    "conversational_tone",
    "sentence_count",
    "avg_sentence_length",
    "ai_phrases_found",
)


def format_csv(text: str, *, score: HumanScore | None = None) -> str:
    """Return a one-row CSV score sheet for `text`."""
    result = score if score is not None else score_text(text)
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(CSV_COLUMNS)
    writer.writerow(
        [
            text,
            result.overall,
            overall_label(result.overall),
            result.burstiness,
            result.vocabulary,
            result.phrasing,
            result.contractions,
            result.sentence_count,
            result.avg_sentence_len,
            result.ai_tell_hits,
        ]
    )
    return buffer.getvalue()


TEST_CASE_COLUMNS = (
    "test_id",
    "sample_type",
    "text",
    "overall_score",
    "verdict",
    "sentence_rhythm",
    "word_variety",
    "natural_phrasing",
    "conversational_tone",
    "ai_phrases_found",
    "expected_result",
    "rhythm_pass",
    "opener_pass",
    "connectors_pass",
    "buzzwords_pass",
    "meaning_pass",
    "voice_pass",
    "tester_notes",
)


def build_test_cases_csv() -> str:
    """Build a ready-to-use CSV with sample paragraphs for manual testing."""
    samples = (
        (
            "1",
            "AI-style (should fail)",
            (
                "In today's fast-paced world, it is important to note that we utilize "
                "technology. Furthermore, it is a powerful tool that can be leveraged. "
                "Moreover, it plays a crucial role. In conclusion, we must leverage it."
            ),
            "Fail - score should be below 60",
        ),
        (
            "2",
            "Human-style (should pass)",
            (
                "Tech moves fast. Honestly? Most of it barely matters. But a few tools "
                "genuinely changed how I work, and I can't imagine going back now."
            ),
            "Pass - score should be 75 or higher",
        ),
    )

    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(TEST_CASE_COLUMNS)

    for test_id, sample_type, text, expected in samples:
        result = score_text(text)
        writer.writerow(
            [
                test_id,
                sample_type,
                text,
                result.overall,
                overall_label(result.overall),
                result.burstiness,
                result.vocabulary,
                result.phrasing,
                result.contractions,
                result.ai_tell_hits,
                expected,
                "",
                "",
                "",
                "",
                "",
                "",
                "",
            ]
        )

    return buffer.getvalue()
