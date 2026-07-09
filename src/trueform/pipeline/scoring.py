"""Local, dependency-free "human-likeness" scoring.

Detectors flag AI text mainly because it is statistically *too smooth*:

* low **perplexity**  -> word choices are too predictable
* low **burstiness**  -> sentence lengths are too uniform

Measuring true perplexity needs a language model (e.g. GPT-2). To keep trueform
free and installable anywhere, this module approximates the same signals with
plain-Python heuristics: sentence-length variation, vocabulary variety, the
density of well-known "AI-tell" phrases, and contraction usage. Each sub-score is
0-100, and they are combined into one overall score where **higher = more human**.

The neural, higher-accuracy scorer is a future drop-in: anything that returns a
`HumanScore` can be swapped in without touching the pipeline.
"""

from __future__ import annotations

import re
import statistics
from dataclasses import asdict, dataclass

# Phrases that show up far more often in AI writing than in natural human prose.
# Kept lowercase; matched case-insensitively as whole words/phrases.
_AI_TELL_PHRASES = (
    "furthermore",
    "moreover",
    "in conclusion",
    "it is important to note",
    "it is worth noting",
    "in today's fast-paced world",
    "in the realm of",
    "navigating the",
    "delve into",
    "tapestry",
    "leverage",
    "utilize",
    "utilizing",
    "seamless",
    "robust",
    "not only",  # part of the "not only... but also" scaffold
    "plays a crucial role",
    "plays a vital role",
    "a testament to",
)

_SENTENCE_SPLIT = re.compile(r"[.!?]+")
_WORD = re.compile(r"[A-Za-z']+")
_CONTRACTION = re.compile(r"\b[A-Za-z]+'[A-Za-z]+\b")


@dataclass
class HumanScore:
    """A breakdown of how human a piece of text reads.

    All fields are 0-100. `overall` is the weighted blend the pipeline uses to
    decide whether a rewrite is good enough to stop.
    """

    overall: float
    burstiness: float
    vocabulary: float
    phrasing: float
    contractions: float

    # Raw measurements kept for the explainability report (Phase: v1.0).
    sentence_count: int = 0
    avg_sentence_len: float = 0.0
    ai_tell_hits: int = 0

    def to_dict(self) -> dict:
        return asdict(self)


def _split_sentences(text: str) -> list[str]:
    return [s.strip() for s in _SENTENCE_SPLIT.split(text) if s.strip()]


def _words(text: str) -> list[str]:
    return _WORD.findall(text.lower())


def _score_burstiness(sentences: list[str]) -> tuple[float, float]:
    """Reward variation in sentence length (in words).

    Returns (score_0_100, avg_sentence_len). Uniform lengths -> low score.
    """
    lengths = [len(_words(s)) for s in sentences if _words(s)]
    if len(lengths) < 2:
        # Not enough sentences to judge rhythm; treat as neutral.
        return 50.0, float(lengths[0]) if lengths else 0.0

    mean_len = statistics.mean(lengths)
    if mean_len == 0:
        return 50.0, 0.0

    # Coefficient of variation: stdev relative to mean. Human prose typically
    # lands around 0.5-0.8; very uniform AI text sits nearer 0.2-0.35.
    cv = statistics.pstdev(lengths) / mean_len
    score = _clamp(cv / 0.7 * 100)  # cv of ~0.7 maps to a full 100
    return score, mean_len


def _score_vocabulary(words: list[str]) -> float:
    """Type-token ratio: unique words / total words. More variety -> higher."""
    if not words:
        return 50.0
    ttr = len(set(words)) / len(words)
    # TTR falls naturally as text gets longer, so a ratio of ~0.6 is already
    # quite varied. Scale so 0.6+ approaches 100.
    return _clamp(ttr / 0.6 * 100)


def _score_phrasing(text: str, word_count: int) -> tuple[float, int]:
    """Penalize density of AI-tell phrases. Returns (score_0_100, hit_count)."""
    lowered = text.lower()
    hits = sum(lowered.count(phrase) for phrase in _AI_TELL_PHRASES)
    if word_count == 0:
        return 100.0, 0
    # Density per 100 words; each ~1% cliché density knocks off a big chunk.
    density = hits / word_count * 100
    score = _clamp(100 - density * 25)
    return score, hits


def _score_contractions(text: str, sentence_count: int) -> float:
    """Humans use contractions; their total absence is a mild AI signal."""
    if sentence_count == 0:
        return 50.0
    contractions = len(_CONTRACTION.findall(text))
    ratio = contractions / sentence_count
    # Roughly one contraction every two sentences already reads very natural.
    return _clamp(ratio / 0.5 * 100)


def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def score_text(text: str) -> HumanScore:
    """Compute a 0-100 human-likeness breakdown for `text`."""
    sentences = _split_sentences(text)
    words = _words(text)

    burstiness, avg_len = _score_burstiness(sentences)
    vocabulary = _score_vocabulary(words)
    phrasing, hits = _score_phrasing(text, len(words))
    contractions = _score_contractions(text, len(sentences))

    # Weights reflect how strongly each signal separates human from AI text.
    # Burstiness and phrasing are the most telling, so they carry the most weight.
    overall = (
        burstiness * 0.35
        + phrasing * 0.30
        + vocabulary * 0.20
        + contractions * 0.15
    )

    return HumanScore(
        overall=round(overall, 1),
        burstiness=round(burstiness, 1),
        vocabulary=round(vocabulary, 1),
        phrasing=round(phrasing, 1),
        contractions=round(contractions, 1),
        sentence_count=len(sentences),
        avg_sentence_len=round(avg_len, 1),
        ai_tell_hits=hits,
    )
