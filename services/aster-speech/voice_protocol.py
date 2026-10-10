"""Dependency-free frame protocol for Aster's streaming voice API."""

from __future__ import annotations

import asyncio
import io
import json
import re
import struct
import uuid
import wave
from collections.abc import AsyncIterator

from voice_candidate import CallerClass, VoiceScheduler

FRAME_MAGIC = b"AVS1"
FRAME_MEDIA_TYPE = "application/vnd.aster.audio-frames"
MAX_HEADER_BYTES = 4096
MAX_PAYLOAD_BYTES = 2 * 1024 * 1024
_REQUEST_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")


def validated_request_id(value: str | None) -> str:
    if value is None:
        return uuid.uuid4().hex
    if not _REQUEST_ID.fullmatch(value):
        raise ValueError("request_id must be 1-64 safe ASCII characters")
    return value


def encode_frame(metadata: dict[str, object], payload: bytes = b"") -> bytes:
    header = json.dumps(metadata, sort_keys=True, separators=(",", ":")).encode()
    if len(header) > MAX_HEADER_BYTES:
        raise ValueError("frame header is too large")
    if len(payload) > MAX_PAYLOAD_BYTES:
        raise ValueError("frame payload is too large")
    return FRAME_MAGIC + struct.pack(">II", len(header), len(payload)) + header + payload


def decode_frames(data: bytes) -> list[tuple[dict[str, object], bytes]]:
    frames: list[tuple[dict[str, object], bytes]] = []
    offset = 0
    while offset < len(data):
        if data[offset:offset + 4] != FRAME_MAGIC or len(data) - offset < 12:
            raise ValueError("invalid or truncated frame prefix")
        header_size, payload_size = struct.unpack(">II", data[offset + 4:offset + 12])
        if header_size > MAX_HEADER_BYTES or payload_size > MAX_PAYLOAD_BYTES:
            raise ValueError("frame exceeds protocol limits")
        end = offset + 12 + header_size + payload_size
        if end > len(data):
            raise ValueError("truncated frame")
        header_start = offset + 12
        try:
            metadata = json.loads(data[header_start:header_start + header_size])
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("invalid frame metadata") from exc
        if not isinstance(metadata, dict):
            raise ValueError("frame metadata must be an object")
        payload = data[header_start + header_size:end]
        frames.append((metadata, payload))
        offset = end
    return frames


def pcm_to_wav(pcm: bytes, sample_rate: int) -> bytes:
    if sample_rate <= 0 or len(pcm) % 2:
        raise ValueError("PCM must be even-length 16-bit audio with a valid sample rate")
    output = io.BytesIO()
    with wave.open(output, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(pcm)
    return output.getvalue()


async def stream_frames(
    scheduler: VoiceScheduler,
    request_id: str,
    text: str,
    caller: CallerClass,
) -> AsyncIterator[bytes]:
    completed = False
    try:
        async for unit in scheduler.stream(request_id, text, caller):
            yield encode_frame(
                {
                    "type": "audio",
                    "request_id": request_id,
                    "index": unit.index,
                    "total": unit.total,
                    "sample_rate": unit.sample_rate,
                    "sample_format": "pcm_s16le",
                    "channels": 1,
                },
                unit.pcm,
            )
        yield encode_frame({"type": "end", "request_id": request_id})
        completed = True
    except asyncio.CancelledError:
        if scheduler.is_cancelled(request_id):
            yield encode_frame({"type": "cancelled", "request_id": request_id})
            completed = True
        else:
            scheduler.cancel(request_id)
            raise
    except Exception as exc:
        yield encode_frame(
            {"type": "error", "request_id": request_id, "error": type(exc).__name__}
        )
    finally:
        if not completed:
            scheduler.cancel(request_id)
