"""Convert native canonical-voice phoneme timing into exact source-word cues.

The caller must phonemize the complete source first, then synthesize that exact
phoneme string with ``is_phonemes=True``.  Spaces in that immutable phoneme
string are the only accepted word boundaries.  Nothing in this module invents
or interpolates a time.
"""
from dataclasses import dataclass
import math
import numbers
import unicodedata

from word_alignment import MAX_TEXT, MAX_WORDS, WORD, WordCue

MAX_PHONEMES = 40_000


@dataclass(frozen=True)
class TimedPhoneme:
    phoneme: str
    start: float
    end: float


def _require(ok, code):
    if not ok:
        raise ValueError(code)


def align_phoneme_groups(source, phonemes, measured, duration, source_group_sizes):
    """Bind measured phoneme groups to explicit exact source-word groups."""
    _require(isinstance(source, str) and 0 < len(source) <= MAX_TEXT,
             "phoneme-alignment-source")
    _require(isinstance(phonemes, str) and 0 < len(phonemes) <= MAX_PHONEMES,
             "phoneme-alignment-plan")
    _require(not phonemes.startswith(" ") and not phonemes.endswith(" ")
             and "  " not in phonemes, "phoneme-alignment-boundaries")
    _require(not isinstance(duration, bool) and isinstance(duration, numbers.Real)
             and math.isfinite(duration) and duration > 0,
             "phoneme-alignment-duration")

    spans = tuple(WORD.finditer(source))
    _require(0 < len(spans) <= MAX_WORDS, "phoneme-alignment-source-words")
    try:
        values = tuple(measured)
    except TypeError as exc:
        raise ValueError("phoneme-alignment-measurements") from exc
    _require(len(values) == len(phonemes), "phoneme-alignment-count")

    groups = []
    current = []
    previous = 0.0
    for expected, value in zip(phonemes, values):
        _require(isinstance(value, TimedPhoneme), "phoneme-alignment-type")
        _require(value.phoneme == expected and len(value.phoneme) == 1,
                 "phoneme-alignment-sequence")
        _require(not isinstance(value.start, bool) and not isinstance(value.end, bool)
                 and isinstance(value.start, numbers.Real)
                 and isinstance(value.end, numbers.Real)
                 and math.isfinite(value.start) and math.isfinite(value.end),
                 "phoneme-alignment-time")
        start = float(value.start); end = float(value.end)
        separator = expected.isspace() or unicodedata.category(expected).startswith("P")
        _require(start >= previous and end >= start and end <= float(duration),
                 "phoneme-alignment-time-order")
        # Kokoro can assign no acoustic frame to punctuation at an utterance
        # edge.  That is an honest measured absence, not a missing spoken cue.
        _require(end > start or separator, "phoneme-alignment-spoken-zero")
        previous = end
        if expected == " ":
            _require(bool(current), "phoneme-alignment-empty-group")
            groups.append(tuple(current)); current = []
        else:
            current.append((expected, start, end))
    _require(bool(current), "phoneme-alignment-empty-group")
    groups.append(tuple(current))
    try:
        widths = tuple(source_group_sizes)
    except TypeError as exc:
        raise ValueError("phoneme-alignment-source-groups") from exc
    _require(len(widths) == len(groups)
             and all(type(width) is int and 1 <= width <= 4 for width in widths)
             and sum(widths) == len(spans), "phoneme-alignment-source-groups")

    cues = []
    cursor = 0
    for width, group in zip(widths, groups):
        # A punctuation-only group cannot honestly represent a source word.
        _require(any(unicodedata.category(char).startswith("L")
                     for char, _, _ in group), "phoneme-alignment-unspoken-word")
        spoken = tuple(value for value in group if value[2] > value[1])
        _require(bool(spoken), "phoneme-alignment-unspoken-word")
        selected = spans[cursor:cursor + width]
        cues.append(WordCue(selected[0].start(), selected[-1].end(),
                            spoken[0][1], spoken[-1][2]))
        cursor += width
    return tuple(cues)


def align_phonemes(source, phonemes, measured, duration):
    """Require one model phoneme group for every exact source word."""
    spans = tuple(WORD.finditer(source)) if isinstance(source, str) else ()
    return align_phoneme_groups(source, phonemes, measured, duration,
                                (1,) * len(spans))
