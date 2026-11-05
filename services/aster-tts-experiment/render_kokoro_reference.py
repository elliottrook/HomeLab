#!/usr/bin/env python3
"""Create the synthetic Aster reference used for local Qwen voice cloning."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import wave


REFERENCE_TEXT = (
    "This is Aster, speaking clearly for the local voice comparison. "
    "The weather is calm, and the evening briefing is ready."
)
SAMPLE_RATE = 24_000


def atomic_json(path: Path, value: dict) -> None:
    descriptor, raw = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(raw)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as output:
            json.dump(value, output, ensure_ascii=False, sort_keys=True, indent=2)
            output.write("\n")
            output.flush()
            os.fsync(output.fileno())
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def render(output: Path, voice_root: Path) -> dict:
    output.mkdir(parents=True, exist_ok=False, mode=0o700)
    sys.path.insert(0, str(voice_root))
    from kokoro_candidate import KokoroWorker, verify_assets

    verify_assets()
    worker = KokoroWorker()
    try:
        pcm, sample_rate = worker.render(REFERENCE_TEXT)
        phonemes = worker._engine.tokenizer.phonemize(REFERENCE_TEXT, "en-gb")
    finally:
        worker.close()
    if sample_rate != SAMPLE_RATE or not pcm:
        raise ValueError("Kokoro reference output contract mismatch")
    wav_path = output / "aster-synthetic-reference.wav"
    with wave.open(str(wav_path), "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(SAMPLE_RATE)
        audio.writeframes(pcm)
    os.chmod(wav_path, 0o600)
    text_path = output / "aster-synthetic-reference.txt"
    text_path.write_text(REFERENCE_TEXT + "\n", encoding="utf-8")
    os.chmod(text_path, 0o600)
    manifest = {
        "schema": "aster-tts-synthetic-reference.v1",
        "source": "kokoro-bm-daniel-synthetic",
        "text": REFERENCE_TEXT,
        "text_sha256": hashlib.sha256(REFERENCE_TEXT.encode()).hexdigest(),
        "phonemes": phonemes,
        "phonemes_sha256": hashlib.sha256(phonemes.encode()).hexdigest(),
        "wav_sha256": hashlib.sha256(wav_path.read_bytes()).hexdigest(),
        "audio_seconds": round(len(pcm) / 2 / SAMPLE_RATE, 6),
    }
    atomic_json(output / "manifest.json", manifest)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--voice-root", type=Path, default=Path("/opt/aster-voice"))
    args = parser.parse_args()
    manifest = render(args.output, args.voice_root)
    print(json.dumps({"state": "complete", "audio_seconds": manifest["audio_seconds"],
                      "wav_sha256": manifest["wav_sha256"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
