#!/usr/bin/env python3
"""Read-only canonical speech dependency probe; prints no credentials."""

from __future__ import annotations

import json
import socket
import urllib.request
from pathlib import Path

EXPECTED_CANONICAL = {
    "status": "ok",
    "service": "aster-voice-candidate",
    "voice": "aster-qwen",
    "voice_model": "qwen3-tts-1.7b-base-q8-metal",
    "voice_policy_version": "2",
    "stt_model": "whisper.cpp-base.en-metal",
}
VOICE_ENV = Path("/etc/aster-voice/voice.env")
BASE = "http://192.168.20.37:9131"


def api_key() -> str:
    for line in VOICE_ENV.read_text(encoding="utf-8").splitlines():
        name, separator, value = line.partition("=")
        if separator and name.strip() == "ASTER_SPEECH_API_KEY":
            return value.strip().strip('"').strip("'")
    return ""


def check() -> dict[str, str]:
    results: dict[str, str] = {}
    for name, url in {
        "canonical_speech": BASE + "/health",
        "authentik_jwks": "https://auth.elliottrook.com/application/o/aster-companion/jwks/",
        "speech_https": "https://aster.elliottrook.com/voice/health",
        "companion_oidc": "https://auth.elliottrook.com/application/o/aster-companion/.well-known/openid-configuration",
    }.items():
        try:
            with urllib.request.urlopen(url, timeout=5) as response:
                data = json.load(response)
                if name == "canonical_speech":
                    valid = all(data.get(key) == value for key, value in EXPECTED_CANONICAL.items())
                elif name == "speech_https":
                    valid = data.get("status") == "ok"
                elif name == "authentik_jwks":
                    valid = bool(data.get("keys"))
                else:
                    valid = data.get("issuer") == "https://auth.elliottrook.com/application/o/aster-companion/"
                results[name] = "ok" if response.status == 200 and valid else "invalid_response"
        except Exception as exc:
            results[name] = type(exc).__name__
    try:
        with socket.create_connection(("192.168.20.37", 10300), timeout=2):
            results["home_assistant_wyoming"] = "ok"
    except Exception as exc:
        results["home_assistant_wyoming"] = type(exc).__name__
    try:
        key = api_key()
        if not key:
            raise RuntimeError("speech credential is not configured")
        request = urllib.request.Request(
            BASE + "/v1/tts",
            data=json.dumps({"text": "Aster health check."}).encode(),
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=60) as response:
            audio = response.read(2 * 1024 * 1024 + 1)
            valid = response.status == 200 and 44 < len(audio) <= 2 * 1024 * 1024 and audio[:4] == b"RIFF" and audio[8:12] == b"WAVE"
            results["canonical_synthesis"] = "ok" if valid else "invalid_response"
    except Exception as exc:
        results["canonical_synthesis"] = type(exc).__name__
    return results


if __name__ == "__main__":
    result = check()
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if all(value == "ok" for value in result.values()) else 1)
