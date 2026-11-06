"""Fail-closed client for the loopback-forwarded Mac Qwen renderer."""

from __future__ import annotations

import io
import json
import os
import urllib.error
import urllib.request
import wave

ENDPOINT = os.environ.get("ASTER_QWEN_RENDERER_URL", "http://127.0.0.1:18140/v1/audio/speech")
TIMEOUT_SECONDS = float(os.environ.get("ASTER_QWEN_RENDERER_TIMEOUT", "45"))
VOICE = os.environ.get("ASTER_QWEN_VOICE", "aster")
SEED = int(os.environ.get("ASTER_QWEN_SEED", "20261104"))
MAX_WAV_BYTES = 32 * 1024 * 1024


def _wav_to_pcm(payload: bytes) -> tuple[bytes, int]:
    if len(payload) > MAX_WAV_BYTES:
        raise RuntimeError("Qwen renderer response exceeds the maximum size")
    try:
        with wave.open(io.BytesIO(payload), "rb") as source:
            if source.getnchannels() != 1 or source.getsampwidth() != 2:
                raise RuntimeError("Qwen renderer returned unsupported audio")
            rate = source.getframerate()
            if rate != 24000:
                raise RuntimeError("Qwen renderer changed the sample rate")
            pcm = source.readframes(source.getnframes())
    except (EOFError, wave.Error) as exc:
        raise RuntimeError("Qwen renderer returned an invalid WAV") from exc
    if not pcm or len(pcm) % 2:
        raise RuntimeError("Qwen renderer returned invalid PCM")
    return pcm, rate


class QwenRendererPool:
    def __init__(self, endpoint: str = ENDPOINT, timeout: float = TIMEOUT_SECONDS):
        if not endpoint.startswith("http://127.0.0.1:"):
            raise RuntimeError("Qwen renderer must use the loopback tunnel")
        self.endpoint = endpoint
        self.timeout = timeout

    def _render(self, text: str) -> tuple[bytes, int]:
        body = json.dumps({
            "input": text,
            "voice": VOICE,
            "language": "English",
            "response_format": "wav",
            "seed": SEED,
        }).encode("utf-8")
        request = urllib.request.Request(
            self.endpoint,
            data=body,
            headers={"Content-Type": "application/json", "Accept": "audio/wav"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                if response.status != 200 or response.headers.get_content_type() != "audio/wav":
                    raise RuntimeError("Qwen renderer returned an invalid response")
                payload = response.read(MAX_WAV_BYTES + 1)
        except (TimeoutError, urllib.error.URLError) as exc:
            raise RuntimeError("Qwen renderer is unavailable") from exc
        return _wav_to_pcm(payload)

    @property
    def renderers(self):
        return (self._render,)

    def close(self) -> None:
        return None

    def healthy(self) -> bool:
        health_url = self.endpoint.rsplit("/v1/", 1)[0] + "/health"
        try:
            with urllib.request.urlopen(health_url, timeout=2) as response:
                return response.status == 200
        except (TimeoutError, urllib.error.URLError):
            return False

