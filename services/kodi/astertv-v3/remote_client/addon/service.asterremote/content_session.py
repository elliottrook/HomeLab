"""Content-free playback-session identity for AsterTV room observations."""

from __future__ import annotations

import secrets


class ContentSession:
    """Rotate identity only when a new playback session begins."""

    def __init__(self, token_factory=None):
        self._token_factory = token_factory or (lambda: secrets.token_hex(16))
        self._session_id = "play-" + self._token_factory()
        self._sequence = 0
        self._previous_playback = None

    def observe(self, playback: str) -> tuple[str, int]:
        if playback not in {"idle", "playing", "paused"}:
            raise ValueError("playback-state")
        if (self._previous_playback == "idle"
                and playback in {"playing", "paused"}):
            self._session_id = "play-" + self._token_factory()
            self._sequence = 0
        self._previous_playback = playback
        self._sequence += 1
        return self._session_id, self._sequence
