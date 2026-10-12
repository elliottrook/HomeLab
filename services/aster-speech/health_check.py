#!/usr/bin/env python3
"""Read-only speech and login-dependency probe; prints no keys or credentials."""
import json
import socket
import urllib.request
from pathlib import Path


EXPECTED_CANONICAL = {
    "status": "ok",
    "service": "aster-voice-candidate",
    "voice": "aster-bm-daniel",
    "voice_model": "kokoro-v1.0",
    "voice_policy_version": "1",
    "stt_model": "aster-base-en",
}
CANDIDATE_ENV = Path("/etc/aster-speech/voice-candidate.env")
CANARY_TEXT = "Aster health check."


def candidate_api_key():
    for line in CANDIDATE_ENV.read_text().splitlines():
        name, separator, value = line.partition("=")
        if separator and name.strip() == "ASTER_SPEECH_API_KEY":
            return value.strip().strip('"').strip("'")
    return ""


def check():
    results = {}
    for name, url in {
        "speech": "http://192.168.70.14:9130/health",
        "canonical_speech": "http://192.168.70.14:9131/health",
        "authentik_jwks": "https://auth.elliottrook.com/application/o/aster-companion/jwks/",
        "speech_https": "https://aster.elliottrook.com/voice/health",
        "companion_oidc": "https://auth.elliottrook.com/application/o/aster-companion/.well-known/openid-configuration",
    }.items():
        try:
            with urllib.request.urlopen(url, timeout=5) as response:
                data = json.load(response)
                if name == "canonical_speech":
                    valid = all(data.get(key) == value for key, value in EXPECTED_CANONICAL.items())
                elif name in {"speech", "speech_https"}:
                    valid = data.get("status") == "ok"
                elif name == "authentik_jwks":
                    valid = bool(data.get("keys"))
                else:
                    valid = data.get("issuer") == "https://auth.elliottrook.com/application/o/aster-companion/"
                results[name] = "ok" if response.status == 200 and valid else "invalid_response"
        except Exception as exc:
            results[name] = type(exc).__name__
    try:
        with socket.create_connection(("192.168.70.14", 10300), timeout=2):
            results["home_assistant_wyoming"] = "ok"
    except Exception as exc:
        results["home_assistant_wyoming"] = type(exc).__name__
    try:
        key = candidate_api_key()
        if not key:
            raise RuntimeError("candidate credential is not configured")
        request = urllib.request.Request(
            "http://192.168.70.14:9131/v1/tts",
            data=json.dumps({"text": CANARY_TEXT}).encode(),
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=5) as response:
            audio = response.read(2 * 1024 * 1024 + 1)
            valid = (
                response.status == 200
                and 44 < len(audio) <= 2 * 1024 * 1024
                and audio[:4] == b"RIFF"
                and audio[8:12] == b"WAVE"
            )
            results["canonical_synthesis"] = "ok" if valid else "invalid_response"
    except Exception as exc:
        results["canonical_synthesis"] = type(exc).__name__
    return results


if __name__ == "__main__":
    result = check()
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if all(value == "ok" for value in result.values()) else 1)
