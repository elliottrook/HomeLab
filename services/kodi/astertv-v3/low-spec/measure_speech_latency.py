#!/usr/bin/env python3
"""Measure content-free canonical Aster Voice STT latency in LXC 128."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import time
import urllib.request
import uuid


HOST = "aster-voice-prod"
BASE = "http://192.168.20.37:9131"
ENVIRONMENT = Path("/etc/aster-voice/voice.env")
EXPECTED_HEALTH = {
    "status": "ok",
    "service": "aster-voice-candidate",
    "voice": "aster-qwen",
    "voice_model": "qwen3-tts-1.7b-base-q8-metal",
    "voice_policy_version": "2",
    "stt_model": "whisper.cpp-base.en-metal",
}
FIXTURE_TEXT = "What time is it?"
EXPECTED_DIGEST = "cbe649f8e0039474b8f9860b9c39e740883affb4f1c0ac850404572172a08a9a"
LATENCY_BUDGET_MS = 1500.0


def api_key(path: Path = ENVIRONMENT) -> str:
    for raw in path.read_text(encoding="utf-8").splitlines():
        name, separator, value = raw.partition("=")
        if separator and name.strip() == "ASTER_SPEECH_API_KEY":
            value = value.strip().strip("\"").strip("'")
            if len(value) >= 32:
                return value
    raise RuntimeError("speech-key-unavailable")


def normalize(value: str) -> str:
    words = re.findall(
        r"[a-z0-9]+(?:'[a-z0-9]+)?",
        value.casefold().replace("’", "'"),
    )
    return " ".join(words)


def digest(value: str) -> str:
    return hashlib.sha256(normalize(value).encode()).hexdigest()


def percentile(values: list[float], fraction: float) -> float:
    if not values or not 0 < fraction <= 1:
        raise ValueError("invalid-percentile")
    ordered = sorted(values)
    return ordered[math.ceil(len(ordered) * fraction) - 1]


def request_json(opener, url: str, *, data: bytes | None = None,
                 headers: dict[str, str] | None = None) -> dict:
    request = urllib.request.Request(
        url, data=data, headers=headers or {}, method="POST" if data else "GET"
    )
    with opener(request, timeout=60) as response:
        value = json.load(response)
    if not isinstance(value, dict):
        raise RuntimeError("speech-response-shape")
    return value


def request_audio(opener, key: str) -> bytes:
    request = urllib.request.Request(
        BASE + "/v1/tts",
        data=json.dumps({"text": FIXTURE_TEXT}).encode(),
        headers={"Authorization": "Bearer " + key,
                 "Content-Type": "application/json"},
        method="POST",
    )
    with opener(request, timeout=60) as response:
        audio = response.read(4 * 1024 * 1024 + 1)
    if (not audio.startswith(b"RIFF") or audio[8:12] != b"WAVE"
            or not 1000 < len(audio) <= 4 * 1024 * 1024):
        raise RuntimeError("speech-fixture-invalid")
    return audio


def multipart(audio: bytes) -> tuple[bytes, str]:
    boundary = "astertv-" + uuid.uuid4().hex
    body = (
        (f"--{boundary}\r\nContent-Disposition: form-data; name=\"audio\"; "
         "filename=\"fixture.wav\"\r\nContent-Type: audio/wav\r\n\r\n").encode()
        + audio + f"\r\n--{boundary}--\r\n".encode()
    )
    return body, boundary


def run(iterations: int, *, opener=urllib.request.urlopen,
        hostname: str | None = None, key: str | None = None) -> dict:
    if hostname is None:
        hostname = os.uname().nodename
    if hostname != HOST:
        raise RuntimeError("speech-target")
    health = request_json(opener, BASE + "/health")
    if any(health.get(name) != value for name, value in EXPECTED_HEALTH.items()):
        raise RuntimeError("speech-authority-drift")
    key = key or api_key()
    audio = request_audio(opener, key)
    body, boundary = multipart(audio)
    rows = []
    for iteration in range(iterations):
        started = time.monotonic()
        result = request_json(
            opener, BASE + "/v1/stt", data=body,
            headers={"Authorization": "Bearer " + key,
                     "Content-Type": "multipart/form-data; boundary=" + boundary},
        )
        elapsed_ms = (time.monotonic() - started) * 1000
        text = result.get("text")
        valid = isinstance(text, str) and digest(text) == EXPECTED_DIGEST
        rows.append({"iteration": iteration + 1,
                     "latency_ms": round(elapsed_ms, 1), "exact": valid})
    latencies = [row["latency_ms"] for row in rows]
    p95 = percentile(latencies, 0.95)
    outcome = "pass" if all(row["exact"] for row in rows) and p95 <= LATENCY_BUDGET_MS else "fail"
    return {
        "schema_version": 1,
        "kind": "astertv-canonical-speech-latency",
        "host": HOST,
        "authority": EXPECTED_HEALTH,
        "iterations": iterations,
        "exact": sum(row["exact"] for row in rows),
        "latency_ms": {
            "minimum": min(latencies),
            "median": percentile(latencies, 0.5),
            "p95": p95,
            "maximum": max(latencies),
        },
        "budget_ms": LATENCY_BUDGET_MS,
        "results": rows,
        "retained_audio": False,
        "retained_transcript": False,
        "outcome": outcome,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--iterations", type=int, default=6)
    args = parser.parse_args(argv)
    if not 3 <= args.iterations <= 12:
        raise RuntimeError("speech-iterations")
    result = run(args.iterations)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["outcome"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
