"""Strictly bind measured recognizer words to exact source-character spans.

This module does not estimate timing.  A caller must supply measured word
boundaries from an audio recognizer/alignment backend; any textual or temporal
ambiguity makes the whole unit unusable for word highlighting.
"""
from dataclasses import dataclass
import math
import numbers
import re
import unicodedata

MAX_TEXT = 20_000
MAX_WORDS = 4_000
WORD = re.compile(r"[^\W_]+(?:[\u2019'\-][^\W_]+)*", re.UNICODE)


@dataclass(frozen=True)
class TimedWord:
    text: str
    start: float
    end: float


@dataclass(frozen=True)
class WordCue:
    start_character: int
    end_character: int
    start_seconds: float
    end_seconds: float


def _canonical(value):
    return unicodedata.normalize("NFKC", value).replace("\u2019", "'").casefold()


def _measured_token(value):
    if not isinstance(value, str):
        raise ValueError("alignment-word-text")
    matches = tuple(WORD.finditer(value.strip()))
    if len(matches) != 1:
        raise ValueError("alignment-word-shape")
    return _canonical(matches[0].group())


def align_exact(source, measured, duration):
    """Return exact source spans with measured timings, or reject everything.

    Exact token equality is deliberately required.  Insertions, omissions,
    substitutions and normalization that changes a spoken word must be handled
    by a future source-to-spoken manifest, never by guessed interpolation.
    """
    if not isinstance(source, str) or not source or len(source) > MAX_TEXT:
        raise ValueError("alignment-source")
    if isinstance(duration, bool) or not isinstance(duration, numbers.Real) \
            or not math.isfinite(duration) or duration <= 0:
        raise ValueError("alignment-duration")
    spans = tuple(WORD.finditer(source))
    if not spans or len(spans) > MAX_WORDS:
        raise ValueError("alignment-source-words")
    try:
        words = tuple(measured)
    except TypeError as exc:
        raise ValueError("alignment-measurements") from exc
    if len(words) != len(spans):
        raise ValueError("alignment-count")

    cues = []
    previous = 0.0
    for span, word in zip(spans, words):
        if not isinstance(word, TimedWord):
            raise ValueError("alignment-measurement-type")
        if _canonical(span.group()) != _measured_token(word.text):
            raise ValueError("alignment-text-mismatch")
        if (isinstance(word.start, bool) or isinstance(word.end, bool)
                or not isinstance(word.start, numbers.Real) or not isinstance(word.end, numbers.Real)
                or not math.isfinite(word.start) or not math.isfinite(word.end)):
            raise ValueError("alignment-time")
        start = float(word.start); end = float(word.end)
        if start < previous or end <= start or end > float(duration):
            raise ValueError("alignment-time-order")
        cues.append(WordCue(span.start(), span.end(), start, end))
        previous = end
    return tuple(cues)
