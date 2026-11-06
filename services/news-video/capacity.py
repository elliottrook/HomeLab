#!/usr/bin/env python3
"""Estimate news-video pilot wall time from measured local render rates."""

from __future__ import annotations

import argparse
import json


FPS = 25
FACE_SECONDS_PER_FRAME = 300 / 46
COMPOSITING_SECONDS_PER_FRAME = 16 / 46
QWEN_TTS_RTF = 0.865


def estimate(duration_minutes: float) -> dict[str, float]:
    audio_seconds = duration_minutes * 60
    frames = audio_seconds * FPS
    video_seconds = frames * (
        FACE_SECONDS_PER_FRAME + COMPOSITING_SECONDS_PER_FRAME
    )
    tts_seconds = audio_seconds * QWEN_TTS_RTF
    return {
        "digest_minutes": duration_minutes,
        "frames": frames,
        "tts_minutes": round(tts_seconds / 60, 2),
        "video_render_hours": round(video_seconds / 3600, 2),
        "serial_total_hours": round((tts_seconds + video_seconds) / 3600, 2),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("minutes", type=float, nargs="+", default=[15, 20])
    args = parser.parse_args()
    if any(value <= 0 for value in args.minutes):
        parser.error("minutes must be positive")
    print(json.dumps([estimate(value) for value in args.minutes], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
