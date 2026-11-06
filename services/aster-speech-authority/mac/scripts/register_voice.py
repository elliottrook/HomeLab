#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import json
import time
import urllib.request
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True)
    parser.add_argument("--wav", type=Path, required=True)
    parser.add_argument("--text", type=Path, required=True)
    parser.add_argument("--name", required=True)
    args = parser.parse_args()
    deadline = time.monotonic() + 90
    health = args.url.rstrip("/") + "/health"
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(health, timeout=2) as response:
                if response.status == 200:
                    break
        except OSError:
            time.sleep(1)
    else:
        raise SystemExit("TTS server did not become healthy")
    body = json.dumps({
        "name": args.name,
        "ref_text": args.text.read_text(encoding="utf-8").strip(),
        "wav_b64": base64.b64encode(args.wav.read_bytes()).decode("ascii"),
    }).encode("utf-8")
    request = urllib.request.Request(
        args.url.rstrip("/") + "/v1/audio/voices",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=90) as response:
        if response.status not in (200, 201):
            raise SystemExit(f"voice registration failed: HTTP {response.status}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

