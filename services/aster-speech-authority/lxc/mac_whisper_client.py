"""Multipart client for the loopback-forwarded Mac whisper.cpp server."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
import uuid

ENDPOINT = os.environ.get("ASTER_MAC_STT_URL", "http://127.0.0.1:18141/inference")
TIMEOUT = float(os.environ.get("ASTER_MAC_STT_TIMEOUT", "45"))


def healthy() -> bool:
    if not ENDPOINT.startswith("http://127.0.0.1:"):
        return False
    try:
        with urllib.request.urlopen(ENDPOINT.rsplit("/", 1)[0] + "/health", timeout=2) as response:
            return response.status == 200
    except (TimeoutError, urllib.error.URLError):
        return False


def transcribe_wav(data: bytes, filename: str = "audio.wav") -> str:
    if not ENDPOINT.startswith("http://127.0.0.1:"):
        raise RuntimeError("Mac STT must use the loopback tunnel")
    boundary = "aster-" + uuid.uuid4().hex
    parts = []
    for name, value in (("response_format", "json"), ("language", "en"), ("beam_size", "1"), ("best_of", "1")):
        parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"{name}\"\r\n\r\n{value}\r\n".encode())
    parts.append(
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{filename}\"\r\nContent-Type: audio/wav\r\n\r\n".encode()
        + data + b"\r\n"
    )
    parts.append(f"--{boundary}--\r\n".encode())
    request = urllib.request.Request(
        ENDPOINT,
        data=b"".join(parts),
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            if response.status != 200:
                raise RuntimeError("Mac STT returned an invalid response")
            payload = json.loads(response.read(1024 * 1024))
    except (TimeoutError, urllib.error.URLError, json.JSONDecodeError) as exc:
        raise RuntimeError("Mac STT is unavailable") from exc
    text = payload.get("text")
    if not isinstance(text, str):
        raise RuntimeError("Mac STT response omitted text")
    return text.strip()

