#!/usr/bin/env python3
"""Render the synthetic pilot through Aster's current local speech authority."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import urllib.request


TEST_TEXT = "Good evening. This is Aster."


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--endpoint",
        default="http://127.0.0.1:18140/v1/audio/speech",
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not args.endpoint.startswith("http://127.0.0.1:"):
        raise ValueError("the direct renderer must remain loopback-only")

    payload = json.dumps(
        {
            "input": TEST_TEXT.replace("Aster", "Asster"),
            "voice": "aster",
            "language": "English",
            "response_format": "wav",
            "seed": 20261104,
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        args.endpoint,
        data=payload,
        headers={"Content-Type": "application/json", "Accept": "audio/wav"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=45) as response:
        audio = response.read(32 * 1024 * 1024 + 1)
        if response.status != 200 or response.headers.get_content_type() != "audio/wav":
            raise RuntimeError("speech authority returned an invalid response")
    if len(audio) > 32 * 1024 * 1024 or not audio.startswith(b"RIFF"):
        raise RuntimeError("speech authority returned an invalid WAV")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(audio)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
