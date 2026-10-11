"""Fail-closed client for Aster's private Kokoro/Vulkan renderer bridge."""

from __future__ import annotations

import io
import os
import urllib.error
import urllib.request
import wave
from pathlib import Path

from kokoro_candidate import ACKNOWLEDGEMENT

ENDPOINT = os.environ.get(
    "ASTER_VULKAN_RENDERER_URL", "http://192.168.70.12:9132/render"
)
KEY_FILE = Path(os.environ.get(
    "ASTER_VULKAN_RENDERER_KEY_FILE", "/etc/aster-speech/vulkan-renderer.key"
))
TIMEOUT_SECONDS = float(os.environ.get("ASTER_VULKAN_RENDERER_TIMEOUT", "15"))
MAX_WAV_BYTES = 16 * 1024 * 1024


def _read_key(path: Path = KEY_FILE) -> str:
    key = path.read_text(encoding="utf-8").strip()
    if len(key) < 32 or any(character.isspace() for character in key):
        raise RuntimeError("Vulkan renderer credential is invalid")
    return key


def _wav_to_pcm(payload: bytes) -> tuple[bytes, int]:
    if len(payload) > MAX_WAV_BYTES:
        raise RuntimeError("Vulkan renderer response exceeds the maximum size")
    try:
        with wave.open(io.BytesIO(payload), "rb") as source:
            if source.getnchannels() != 1 or source.getsampwidth() != 2:
                raise RuntimeError("Vulkan renderer returned unsupported audio")
            sample_rate = source.getframerate()
            if sample_rate != 24000:
                raise RuntimeError("Vulkan renderer changed the sample rate")
            pcm = source.readframes(source.getnframes())
    except (EOFError, wave.Error) as exc:
        raise RuntimeError("Vulkan renderer returned an invalid WAV") from exc
    if not pcm or len(pcm) % 2:
        raise RuntimeError("Vulkan renderer returned invalid PCM")
    return pcm, sample_rate


class VulkanRendererPool:
    """Two scheduler callables backed by one bounded private GPU service."""

    def __init__(
        self,
        endpoint: str = ENDPOINT,
        key_file: Path = KEY_FILE,
        timeout: float = TIMEOUT_SECONDS,
    ):
        if not endpoint.startswith("http://"):
            raise RuntimeError("Vulkan renderer must use the private HTTP transport")
        if timeout <= 0:
            raise RuntimeError("Vulkan renderer timeout must be positive")
        self.endpoint = endpoint
        self.key = _read_key(key_file)
        self.timeout = timeout
        self._cache = {ACKNOWLEDGEMENT: self._render_uncached(ACKNOWLEDGEMENT)}

    def _render_uncached(self, text: str) -> tuple[bytes, int]:
        request = urllib.request.Request(
            self.endpoint,
            data=text.encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.key}",
                "Content-Type": "text/plain; charset=utf-8",
                "Accept": "audio/wav",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                content_type = response.headers.get_content_type()
                if response.status != 200 or content_type != "audio/wav":
                    raise RuntimeError("Vulkan renderer returned an invalid response")
                payload = response.read(MAX_WAV_BYTES + 1)
        except (TimeoutError, urllib.error.URLError) as exc:
            raise RuntimeError("Vulkan renderer is unavailable") from exc
        return _wav_to_pcm(payload)

    def _render(self, text: str) -> tuple[bytes, int]:
        cached = self._cache.get(text)
        return cached if cached is not None else self._render_uncached(text)

    @property
    def renderers(self):
        return (self._render, self._render)

    def close(self) -> None:
        return None

    def healthy(self) -> bool:
        health_url = self.endpoint.rsplit("/", 1)[0] + "/health"
        try:
            with urllib.request.urlopen(health_url, timeout=min(self.timeout, 2.0)) as response:
                return response.status == 200
        except (TimeoutError, urllib.error.URLError):
            return False
