#!/usr/bin/env python3
"""Reproduce the superseded v1 Kokoro audio for audit evidence."""

from __future__ import annotations

import argparse
from pathlib import Path

import soundfile as sf
from kokoro_onnx import Kokoro


TEST_TEXT = (
    "Good evening. This is Aster."
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--voices", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    engine = Kokoro(str(args.model), str(args.voices))
    try:
        audio, sample_rate = engine.create(
            TEST_TEXT, voice="bm_daniel", speed=0.95, lang="en-gb"
        )
    finally:
        engine.voices.close()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    sf.write(args.output, audio, sample_rate, subtype="PCM_16")
    print(f"rendered {len(audio) / sample_rate:.3f}s at {sample_rate} Hz")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
