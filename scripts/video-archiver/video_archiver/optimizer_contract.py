"""Fail-closed stream checks for a staged media-optimizer candidate.

This is a pure validation contract. It does not encode, replace, or delete a
file. Picture quality and AsterTV playback still require a human pilot.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from .lifecycle_policy import ARCHIVE_CEILING_BYTES


ENGLISH = {"en", "eng"}
UNKNOWN = {"", "und"}
HDR_TRANSFERS = {"smpte2084", "arib-std-b67"}


@dataclass(frozen=True)
class Video:
    width: int
    height: int
    transfer: str | None = None
    primaries: str | None = None
    dolby_vision_profile: int | None = None


@dataclass(frozen=True)
class Audio:
    language: str | None
    channels: int


@dataclass(frozen=True)
class Subtitle:
    language: str | None
    codec: str
    forced: bool = False
    hearing_impaired: bool = False


@dataclass(frozen=True)
class Sidecar:
    suffix: str
    sha256: str


@dataclass(frozen=True)
class Manifest:
    size_bytes: int
    duration_seconds: float
    video: Video
    audio: tuple[Audio, ...]
    subtitles: tuple[Subtitle, ...]
    sidecars: tuple[Sidecar, ...] = ()


def _language(value: str | None) -> str:
    return (value or "").lower().replace("_", "-").split("-", 1)[0]


def _required_subtitles(manifest: Manifest) -> Counter:
    return Counter(
        (_language(track.language), track.codec, track.forced, track.hearing_impaired)
        for track in manifest.subtitles
        if _language(track.language) in ENGLISH | UNKNOWN
    )


def check_candidate(source: Manifest, output: Manifest) -> tuple[str, ...]:
    """Return every blocking mismatch; an empty tuple passes machine checks."""
    problems: list[str] = []
    if source.size_bytes <= ARCHIVE_CEILING_BYTES:
        problems.append("source already fits Archive; do not recompress")
    if output.size_bytes <= 0 or output.size_bytes > ARCHIVE_CEILING_BYTES:
        problems.append("output exceeds the exact 5 GB ceiling or has invalid size")
    if source.duration_seconds <= 0 or output.duration_seconds <= 0:
        problems.append("invalid duration")
    elif abs(output.duration_seconds - source.duration_seconds) > max(3.0, source.duration_seconds * 0.002):
        problems.append("duration mismatch")

    sv, ov = source.video, output.video
    if min(sv.width, sv.height, ov.width, ov.height) <= 0:
        problems.append("invalid video dimensions")
    else:
        if ov.width > sv.width or ov.height > sv.height:
            problems.append("output upscales the source")
        if abs((ov.width / ov.height) - (sv.width / sv.height)) / (sv.width / sv.height) > 0.01:
            problems.append("aspect ratio changed")
        scale = min(1.0, 1920 / sv.width, 1080 / sv.height)
        floor_w, floor_h = round(sv.width * scale), round(sv.height * scale)
        if ov.width < floor_w - 2 or ov.height < floor_h - 2:
            problems.append("output falls below the 1080p-tier floor")

    if sv.dolby_vision_profile == 5:
        problems.append("Dolby Vision profile 5 needs a separate colour-safe path")
    if sv.transfer in HDR_TRANSFERS:
        if ov.transfer != sv.transfer or ov.primaries != "bt2020":
            problems.append("HDR transfer or BT.2020 primaries lost")
    elif ov.transfer in HDR_TRANSFERS:
        problems.append("output invents HDR from an SDR source")
    elif sv.primaries and ov.primaries != sv.primaries:
        problems.append("source colour primaries changed")

    source_surround = [track for track in source.audio if track.channels >= 6]
    english_surround = [track for track in source_surround if _language(track.language) in ENGLISH]
    if english_surround and not any(
        track.channels >= 6 and _language(track.language) in ENGLISH for track in output.audio
    ):
        problems.append("English 5.1 or better audio lost")
    elif source_surround and not english_surround and not any(track.channels >= 6 for track in output.audio):
        problems.append("unlabelled surround audio lost")
    if not output.audio:
        problems.append("output has no audio")
    if any(_language(track.language) in ENGLISH for track in source.audio) and not any(
        _language(track.language) in ENGLISH for track in output.audio
    ):
        problems.append("English audio lost")

    missing_subtitles = _required_subtitles(source) - _required_subtitles(output)
    if missing_subtitles:
        problems.append("English or unlabelled subtitle track or flag lost")
    missing_sidecars = Counter(source.sidecars) - Counter(output.sidecars)
    if missing_sidecars:
        problems.append("subtitle sidecar missing or changed")
    return tuple(problems)
