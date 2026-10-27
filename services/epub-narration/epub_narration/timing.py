"""Exact sentence-level cues expressed in PCM sample indexes."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib


@dataclass(frozen=True)
class SentenceSpan:
    source_start: int
    source_end: int
    spoken_text: str


@dataclass(frozen=True)
class SentenceCue:
    source_start: int
    source_end: int
    start_sample: int
    end_sample: int
    spoken_sha256: str


def build_sentence_cues(
    spans: tuple[SentenceSpan, ...],
    rendered_samples: tuple[int, ...],
    pause_samples: tuple[int, ...],
) -> tuple[SentenceCue, ...]:
    """Bind source sentences to measured render lengths without interpolation."""
    if not spans or len(spans) != len(rendered_samples) or len(spans) != len(pause_samples):
        raise ValueError("sentence-timing-count")
    cues: list[SentenceCue] = []
    cursor = 0
    previous_source_end = 0
    for span, samples, pause in zip(spans, rendered_samples, pause_samples):
        if (
            span.source_start < previous_source_end
            or span.source_end <= span.source_start
            or not span.spoken_text
        ):
            raise ValueError("sentence-source-span")
        if isinstance(samples, bool) or not isinstance(samples, int) or samples <= 0:
            raise ValueError("sentence-render-samples")
        if isinstance(pause, bool) or not isinstance(pause, int) or pause < 0:
            raise ValueError("sentence-pause-samples")
        cues.append(SentenceCue(
            source_start=span.source_start,
            source_end=span.source_end,
            start_sample=cursor,
            end_sample=cursor + samples,
            spoken_sha256=hashlib.sha256(span.spoken_text.encode("utf-8")).hexdigest(),
        ))
        cursor += samples + pause
        previous_source_end = span.source_end
    return tuple(cues)


def validate_cues(cues: tuple[SentenceCue, ...], total_samples: int) -> None:
    if isinstance(total_samples, bool) or not isinstance(total_samples, int) or total_samples <= 0:
        raise ValueError("sentence-total-samples")
    previous = 0
    for cue in cues:
        if cue.start_sample < previous or cue.end_sample <= cue.start_sample or cue.end_sample > total_samples:
            raise ValueError("sentence-time-order")
        previous = cue.end_sample

