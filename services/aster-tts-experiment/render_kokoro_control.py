#!/usr/bin/env python3
"""Render the experiment plan with the installed, unchanged Kokoro worker."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import time
import wave


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


def service_pid(unit: str) -> int:
    import subprocess
    result = subprocess.run(
        ["systemctl", "show", unit, "-p", "MainPID", "--value"],
        check=True, capture_output=True, text=True, timeout=10,
    )
    return int(result.stdout.strip())


def render(plan_path: Path, output: Path, voice_root: Path) -> dict:
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    if plan.get("schema") != "aster-tts-experiment-plan.v1" or plan.get("repeats") != [1, 2]:
        raise ValueError("invalid experiment plan")
    output.mkdir(parents=True, mode=0o700)
    sys.path.insert(0, str(voice_root))
    from kokoro_candidate import KokoroWorker, verify_assets

    verify_assets()
    initial_pid = service_pid("aster-voice-prod.service")
    worker = KokoroWorker()
    try:
        for passage in plan["passages"]:
            phonemes = [worker._engine.tokenizer.phonemize(unit, "en-gb")
                        for unit in passage["units"]]
            for repeat in plan["repeats"]:
                started = time.monotonic()
                chunks = []
                for unit in passage["units"]:
                    pcm, sample_rate = worker.render(unit)
                    if sample_rate != SAMPLE_RATE or not pcm:
                        raise ValueError("Kokoro output contract mismatch")
                    chunks.append(pcm)
                stem = f"{passage['id']}-r{repeat}"
                wav_path = output / f"{stem}.wav"
                with wave.open(str(wav_path), "wb") as audio:
                    audio.setnchannels(1)
                    audio.setsampwidth(2)
                    audio.setframerate(SAMPLE_RATE)
                    audio.writeframes(b"".join(chunks))
                os.chmod(wav_path, 0o600)
                atomic_json(output / f"{stem}.timing.json", {
                    "schema": "aster-tts-render-timing.v1",
                    "render_seconds": round(time.monotonic() - started, 6),
                    "unit_count": len(chunks),
                    "phonemes": phonemes,
                    "phoneme_sha256": [hashlib.sha256(item.encode()).hexdigest()
                                       for item in phonemes],
                })
    finally:
        worker.close()
    final_pid = service_pid("aster-voice-prod.service")
    if final_pid != initial_pid:
        raise RuntimeError("production voice service PID changed during control render")
    return {"state": "complete", "passages": len(plan["passages"]),
            "repeats": len(plan["repeats"]), "production_pid_unchanged": True}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--voice-root", type=Path, default=Path("/opt/aster-voice"))
    args = parser.parse_args()
    print(json.dumps(render(args.plan, args.output, args.voice_root), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
