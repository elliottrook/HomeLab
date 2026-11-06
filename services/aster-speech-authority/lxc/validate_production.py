#!/usr/bin/env python3
"""Source-local production validation without printing speech credentials."""

from __future__ import annotations

import argparse
import json
import uuid
import urllib.request
from pathlib import Path


def key_from_env(path: Path) -> str:
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("ASTER_SPEECH_API_KEY="):
            key = line.split("=", 1)[1].strip()
            if len(key) >= 32:
                return key
    raise RuntimeError("speech key is missing")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--expect-model", required=True)
    parser.add_argument("--skip-stt", action="store_true")
    args = parser.parse_args()
    base = "http://192.168.20.37:9131"
    with urllib.request.urlopen(base + "/health", timeout=5) as response:
        health = json.load(response)
    if health.get("voice_model") != args.expect_model:
        raise RuntimeError(f"unexpected voice model: {health.get('voice_model')}")
    key = key_from_env(Path("/etc/aster-voice/voice.env"))
    request = urllib.request.Request(
        base + "/v1/tts",
        data=json.dumps({"text": "Aster speech authority production validation."}).encode(),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        wav = response.read(32 * 1024 * 1024)
    if not wav.startswith(b"RIFF") or len(wav) < 1000:
        raise RuntimeError("production TTS returned invalid audio")
    result: dict[str, object] = {"health": health, "tts_bytes": len(wav)}
    if not args.skip_stt:
        boundary = "aster-" + uuid.uuid4().hex
        body = (
            f"--{boundary}\r\nContent-Disposition: form-data; name=\"audio\"; filename=\"validation.wav\"\r\n"
            "Content-Type: audio/wav\r\n\r\n"
        ).encode() + wav + f"\r\n--{boundary}--\r\n".encode()
        request = urllib.request.Request(
            base + "/v1/stt",
            data=body,
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": f"multipart/form-data; boundary={boundary}",
            },
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=60) as response:
            result["stt"] = json.load(response).get("text")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
