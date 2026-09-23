#!/usr/bin/env python3
"""Read-only speech and login-dependency probe; prints no keys or credentials."""
import json
import urllib.request


def check():
    results = {}
    for name, url in {
        "speech": "http://192.168.70.14:9130/health",
        "authentik_jwks": "https://auth.elliottrook.com/application/o/aster-companion/jwks/",
    }.items():
        try:
            with urllib.request.urlopen(url, timeout=5) as response:
                data = json.load(response)
                valid = (data.get("status") == "ok" if name == "speech"
                         else bool(data.get("keys")))
                results[name] = "ok" if response.status == 200 and valid else "invalid_response"
        except Exception as exc:
            results[name] = type(exc).__name__
    return results


if __name__ == "__main__":
    result = check()
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if all(value == "ok" for value in result.values()) else 1)
