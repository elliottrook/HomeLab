"""Validate Jellyfin trailer metadata before handing it to Kodi YouTube.

This module is deliberately side-effect free.  The Stream M controller may use
the returned plugin URL only after it has separately proved that playback is
idle and that the official YouTube add-on is installed.
"""

from __future__ import annotations

from collections.abc import Iterable
from urllib.parse import parse_qs, quote, urlparse


YOUTUBE_HOSTS = frozenset(
    {
        "youtube.com",
        "www.youtube.com",
        "m.youtube.com",
        "music.youtube.com",
        "youtu.be",
    }
)
VIDEO_ID_CHARS = frozenset(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
)


def _valid_video_id(value: str) -> bool:
    return len(value) == 11 and all(char in VIDEO_ID_CHARS for char in value)


def extract_youtube_video_id(url: str) -> str | None:
    """Return one canonical video ID from a supported HTTPS YouTube URL."""

    if not isinstance(url, str) or len(url) > 2048:
        return None
    try:
        parsed = urlparse(url)
    except ValueError:
        return None
    host = (parsed.hostname or "").lower()
    if parsed.scheme != "https" or host not in YOUTUBE_HOSTS:
        return None

    candidate = ""
    if host == "youtu.be":
        parts = [part for part in parsed.path.split("/") if part]
        if len(parts) == 1:
            candidate = parts[0]
    elif parsed.path == "/watch":
        values = parse_qs(parsed.query, keep_blank_values=True).get("v", [])
        if len(values) == 1:
            candidate = values[0]
    else:
        parts = [part for part in parsed.path.split("/") if part]
        if len(parts) == 2 and parts[0] in {"embed", "shorts", "live"}:
            candidate = parts[1]
    return candidate if _valid_video_id(candidate) else None


def kodi_youtube_plugin_url(video_id: str) -> str:
    """Build the narrow official-add-on route for an already validated ID."""

    if not isinstance(video_id, str) or not _valid_video_id(video_id):
        raise ValueError("invalid-youtube-video-id")
    return "plugin://plugin.video.youtube/play/?video_id=" + quote(
        video_id, safe=""
    )


def validated_kodi_youtube_plugin_url(url: str) -> str | None:
    """Accept only the exact trailer route written by Jellyfin for Kodi."""

    if not isinstance(url, str) or len(url) > 256:
        return None
    try:
        parsed = urlparse(url)
    except ValueError:
        return None
    if (
        parsed.scheme != "plugin"
        or parsed.netloc != "plugin.video.youtube"
        or parsed.path != "/play/"
        or parsed.fragment
    ):
        return None
    values = parse_qs(parsed.query, keep_blank_values=True)
    if set(values) != {"video_id"} or len(values["video_id"]) != 1:
        return None
    video_id = values["video_id"][0]
    return kodi_youtube_plugin_url(video_id) if _valid_video_id(video_id) else None


def first_supported_remote_trailer(urls: Iterable[str]) -> str | None:
    """Select the first supported Jellyfin remote trailer, without searching."""

    for url in urls:
        video_id = extract_youtube_video_id(url)
        if video_id:
            return kodi_youtube_plugin_url(video_id)
    return None
