"""Read-only embedded subtitle and sidecar evidence for one media file."""

from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Callable


SUBTITLE_SUFFIXES = frozenset({".srt", ".ass", ".ssa", ".vtt", ".sub", ".idx", ".sup"})
VIDEO_SUFFIXES = frozenset({".mkv", ".mp4", ".m4v", ".avi", ".ts", ".m2ts", ".mpg", ".mov", ".wmv"})


@dataclass(frozen=True)
class EmbeddedSubtitle:
    language: str | None
    codec: str
    forced: bool
    hearing_impaired: bool


@dataclass(frozen=True)
class HashedSidecar:
    name: str
    sha256: str


@dataclass(frozen=True)
class SubtitleEvidence:
    embedded: tuple[EmbeddedSubtitle, ...]
    sidecars: tuple[HashedSidecar, ...]


Probe = Callable[[Path], dict]


def _ffprobe(path: Path) -> dict:
    return _run_probe(["ffprobe", "-v", "error", "-print_format", "json",
                       "-show_streams", str(path)])


def jellyfin_container_probe(path: Path, *, data_root: Path) -> dict:
    """Probe through Jellyfin's existing /media mount; no host ffprobe needed."""
    root = data_root.resolve()
    if not path.is_file() or path.is_symlink() or not path.resolve().is_relative_to(root):
        raise RuntimeError("media path cannot be verified for subtitle probe")
    media_path = "/media/" + path.resolve().relative_to(root).as_posix()
    return _run_probe(["docker", "exec", "jellyfin",
                       "/usr/lib/jellyfin-ffmpeg/ffprobe", "-v", "error",
                       "-print_format", "json", "-show_streams", media_path])


def _run_probe(command: list[str]) -> dict:
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=120)
    except (OSError, subprocess.TimeoutExpired) as error:
        raise RuntimeError("subtitle stream probe unavailable") from error
    if result.returncode != 0:
        raise RuntimeError("subtitle stream probe failed")
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError as error:
        raise RuntimeError("subtitle stream probe malformed") from error
    if not isinstance(data, dict):
        raise RuntimeError("subtitle stream probe malformed")
    return data


def _digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def inspect_subtitles(video: Path, *, data_root: Path,
                      probe: Probe = _ffprobe) -> SubtitleEvidence:
    """Fail closed on uncertain sidecar ownership, symlinks or probe data."""
    root = data_root.resolve()
    if (not video.is_file() or video.is_symlink() or not video.resolve().is_relative_to(root)
            or video.suffix.lower() not in VIDEO_SUFFIXES):
        raise RuntimeError("media path cannot be verified for subtitle manifest")
    siblings = tuple(video.parent.iterdir())
    if any(folder.is_symlink() and folder.is_dir() for folder in siblings):
        raise RuntimeError("symlinked media subdirectory needs explicit review")
    if any(child.suffix.lower() in SUBTITLE_SUFFIXES
           for folder in siblings if folder.is_dir()
           for child in folder.rglob("*")):
        raise RuntimeError("nested subtitle sidecar needs explicit ownership")
    videos = tuple(path for path in siblings if path.is_file() and path.suffix.lower() in VIDEO_SUFFIXES)
    target = video.name.casefold()
    target_stem = video.stem.casefold()
    if sum(path.name.casefold() == target for path in videos) != 1:
        raise RuntimeError("video filename is ambiguous")
    sidecars: list[HashedSidecar] = []
    for path in siblings:
        if path.suffix.lower() not in SUBTITLE_SUFFIXES:
            continue
        if not path.is_file() or path.is_symlink() or not path.resolve().is_relative_to(root):
            raise RuntimeError("subtitle sidecar path is unverified")
        name_without_ext = path.name[:-len(path.suffix)].casefold()
        owners = [candidate.stem.casefold() for candidate in videos
                  if name_without_ext == candidate.stem.casefold()
                  or name_without_ext.startswith(candidate.stem.casefold() + ".")]
        if not owners:
            raise RuntimeError("subtitle sidecar ownership ambiguous")
        longest = max(len(owner) for owner in owners)
        closest = [owner for owner in owners if len(owner) == longest]
        if len(closest) != 1:
            raise RuntimeError("subtitle sidecar ownership duplicated")
        if closest[0] == target_stem:
            sidecars.append(HashedSidecar(path.name, _digest(path)))
    payload = probe(video)
    streams = payload.get("streams") if isinstance(payload, dict) else None
    if not isinstance(streams, list):
        raise RuntimeError("subtitle stream probe incomplete")
    embedded: list[EmbeddedSubtitle] = []
    for stream in streams:
        if not isinstance(stream, dict):
            raise RuntimeError("subtitle stream malformed")
        if stream.get("codec_type") != "subtitle":
            continue
        codec = stream.get("codec_name")
        tags = stream.get("tags") or {}
        disposition = stream.get("disposition") or {}
        if (not isinstance(codec, str) or not codec or not isinstance(tags, dict)
                or not isinstance(disposition, dict)):
            raise RuntimeError("subtitle stream metadata incomplete")
        language = tags.get("language")
        if language is not None and not isinstance(language, str):
            raise RuntimeError("subtitle language malformed")
        if any(disposition.get(name, 0) not in (0, 1, False, True)
               for name in ("forced", "hearing_impaired")):
            raise RuntimeError("subtitle disposition malformed")
        embedded.append(EmbeddedSubtitle(
            language, codec, bool(disposition.get("forced")),
            bool(disposition.get("hearing_impaired")),
        ))
    return SubtitleEvidence(tuple(embedded), tuple(sorted(sidecars, key=lambda row: row.name)))
