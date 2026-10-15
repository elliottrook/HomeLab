"""Guest-local production llama authentication probe; never prints keys."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

KEY_PATH = "/etc/aster-llama-api-keys"
URL = "http://192.168.70.12:11435/v1/chat/completions"


def probe() -> bool:
    keys = [line.strip() for line in open(KEY_PATH, encoding="ascii") if line.strip()]
    body = json.dumps({"model": "aster-qwen3.5-9b", "messages": [{"role": "user", "content": "health"}], "max_tokens": 1}).encode()
    for key in keys:
        request = urllib.request.Request(URL, data=body, headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(request, timeout=5) as response:
                payload = json.loads(response.read())
            if payload.get("model") == "aster-qwen3.5-9b" and payload.get("choices"):
                return True
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError):
            continue
    return False


if __name__ == "__main__":
    raise SystemExit(0 if probe() else 1)
