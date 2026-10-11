"""Bounded client for Aster's authenticated batch speech route."""

from __future__ import annotations

import hmac
import json
import struct
import urllib.error
import urllib.request
from pathlib import Path

FRAME_MAGIC = b"AVS1"
FRAME_MEDIA_TYPE = "application/vnd.aster.audio-frames"
MAX_HEADER_BYTES = 4096
MAX_PAYLOAD_BYTES = 2 * 1024 * 1024
MAX_RESPONSE_BYTES = 32 * 1024 * 1024


def decode_audio_frames(data: bytes) -> tuple[bytes, int]:
    offset = 0
    audio: list[bytes] = []
    sample_rate: int | None = None
    expected_index = 0
    ended = False
    while offset < len(data):
        if data[offset:offset + 4] != FRAME_MAGIC or len(data) - offset < 12:
            raise RuntimeError("invalid or truncated Aster frame")
        header_size, payload_size = struct.unpack(">II", data[offset + 4:offset + 12])
        if header_size > MAX_HEADER_BYTES or payload_size > MAX_PAYLOAD_BYTES:
            raise RuntimeError("Aster frame exceeds protocol limits")
        end = offset + 12 + header_size + payload_size
        if end > len(data):
            raise RuntimeError("truncated Aster frame")
        try:
            metadata = json.loads(data[offset + 12:offset + 12 + header_size])
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise RuntimeError("invalid Aster frame metadata") from exc
        payload = data[offset + 12 + header_size:end]
        frame_type = metadata.get("type") if isinstance(metadata, dict) else None
        if frame_type == "audio":
            if ended or metadata.get("index") != expected_index:
                raise RuntimeError("Aster audio frames are out of order")
            if metadata.get("channels") != 1 or metadata.get("sample_format") != "pcm_s16le":
                raise RuntimeError("Aster returned unsupported audio")
            rate = metadata.get("sample_rate")
            if not isinstance(rate, int) or rate != 24000:
                raise RuntimeError("Aster returned an unexpected sample rate")
            if sample_rate is not None and rate != sample_rate:
                raise RuntimeError("Aster changed sample rate within a response")
            if not payload or len(payload) % 2:
                raise RuntimeError("Aster returned invalid PCM")
            sample_rate = rate
            expected_index += 1
            audio.append(payload)
        elif frame_type == "end":
            if payload or ended:
                raise RuntimeError("invalid Aster end frame")
            ended = True
        elif frame_type in {"error", "cancelled"}:
            raise RuntimeError(f"Aster batch synthesis returned {frame_type}")
        else:
            raise RuntimeError("Aster returned an unknown frame type")
        offset = end
    if not ended or not audio or sample_rate is None:
        raise RuntimeError("Aster batch response is incomplete")
    return b"".join(audio), sample_rate


class AsterBatchTTS:
    def __init__(self, endpoint: str, key_file: Path, timeout: float = 180.0):
        if not endpoint.startswith("http://"):
            raise RuntimeError("Aster batch endpoint must use the private HTTP transport")
        key = key_file.read_text(encoding="utf-8").strip()
        if len(key) < 32 or any(character.isspace() for character in key):
            raise RuntimeError("Aster batch credential is invalid")
        if timeout <= 0:
            raise RuntimeError("Aster batch timeout must be positive")
        self.endpoint = endpoint
        self.key = key
        self.timeout = timeout

    def synthesize(self, text: str) -> tuple[bytes, int]:
        request = urllib.request.Request(
            self.endpoint,
            data=json.dumps({"text": text}, separators=(",", ":")).encode(),
            headers={
                "Authorization": f"Bearer {self.key}",
                "Content-Type": "application/json",
                "Accept": FRAME_MEDIA_TYPE,
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                if response.status != 200 or response.headers.get_content_type() != FRAME_MEDIA_TYPE:
                    raise RuntimeError("Aster batch service returned an invalid response")
                body = response.read(MAX_RESPONSE_BYTES + 1)
        except (TimeoutError, urllib.error.URLError) as exc:
            raise RuntimeError("Aster batch service is unavailable") from exc
        if len(body) > MAX_RESPONSE_BYTES:
            raise RuntimeError("Aster batch response exceeds the maximum size")
        return decode_audio_frames(body)
