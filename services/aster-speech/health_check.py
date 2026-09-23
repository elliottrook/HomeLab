#!/usr/bin/env python3
"""Read-only speech and login-dependency probe; prints no keys or credentials."""
import json
import urllib.request


def check():
    results = {}
    for name, url in {
        "speech": "http://192.168.70.14:9130/health",
        "authentik_jwks": "https://auth.elliottrook.com/application/o/aster-companion/jwks/",
        "speech_https": "https://aster.elliottrook.com/voice/health",
        "companion_oidc": "https://auth.elliottrook.com/application/o/aster-companion/.well-known/openid-configuration",
    }.items():
        try:
            with urllib.request.urlopen(url, timeout=5) as response:
                data = json.load(response)
                if name in {"speech", "speech_https"}:
                    valid = data.get("status") == "ok"
                elif name == "authentik_jwks":
                    valid = bool(data.get("keys"))
                else:
                    valid = data.get("issuer") == "https://auth.elliottrook.com/application/o/aster-companion/"
                results[name] = "ok" if response.status == 200 and valid else "invalid_response"
        except Exception as exc:
            results[name] = type(exc).__name__
    return results


if __name__ == "__main__":
    result = check()
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if all(value == "ok" for value in result.values()) else 1)
