#!/usr/bin/env python3
"""Render a private benchmark plan with the unchanged canonical Aster voice."""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time

import numpy as np
import soundfile as sf
from kokoro_onnx import Kokoro


MODEL_SHA256 = "f3a290d384fbb27966d462905c71a46cef9e5fd00516b40df32a0b4afe77ac96"
VOICE = "bm_daniel"
LANGUAGE = "en-gb"
SPEED = 0.95
SAMPLE_RATE = 24_000
BITRATE = "48k"
WORD = re.compile(r"\b[^\W_]+(?:['’][^\W_]+)?\b", re.UNICODE)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while block := handle.read(1024 * 1024):
            digest.update(block)
    return digest.hexdigest()


def service_pid(unit: str) -> int:
    result = subprocess.run(
        ["systemctl", "show", unit, "-p", "MainPID", "--value"],
        check=True,
        capture_output=True,
        text=True,
        timeout=10,
    )
    return int(result.stdout.strip())


def encode_opus(waveform: np.ndarray, output: Path) -> tuple[float, int]:
    with tempfile.NamedTemporaryFile(suffix=".wav", dir=output.parent) as handle:
        sf.write(handle.name, waveform, SAMPLE_RATE, subtype="PCM_16")
        result = subprocess.run(
            [
                "ffmpeg", "-v", "error", "-y", "-i", handle.name,
                "-map_metadata", "-1", "-ac", "1", "-c:a", "libopus",
                "-b:a", BITRATE, "-application", "audio", "-vbr", "on", str(output),
            ],
            capture_output=True,
            timeout=300,
        )
    if result.returncode != 0:
        raise RuntimeError("benchmark-opus-encode")
    probe = subprocess.run(
        [
            "ffprobe", "-v", "error", "-select_streams", "a:0",
            "-show_entries", "stream=sample_rate,channels:format=duration",
            "-of", "json", str(output),
        ],
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )
    detail = json.loads(probe.stdout)
    stream = detail["streams"][0]
    if int(stream["sample_rate"]) != 48_000 or int(stream["channels"]) != 1:
        raise RuntimeError("benchmark-opus-format")
    duration = float(detail["format"]["duration"])
    expected = len(waveform) / SAMPLE_RATE
    if abs(duration - expected) > 0.1:
        raise RuntimeError("benchmark-opus-duration")
    return duration, output.stat().st_size


def render_plan(plan_path: Path, output: Path, model: Path, voices: Path, cleanup_dir: Path) -> dict:
    if sha256_file(model) != MODEL_SHA256:
        raise RuntimeError("benchmark-model-hash")
    sys.path.insert(0, str(cleanup_dir))
    cleanup = importlib.import_module("digest_text")
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    samples = plan.get("samples")
    if plan.get("schema") != 1 or not isinstance(samples, list) or len(samples) != 20:
        raise RuntimeError("benchmark-plan")
    output.mkdir(parents=True, exist_ok=False, mode=0o700)
    os.chmod(output, 0o700)
    initial_pids = {
        "aster-speech.service": service_pid("aster-speech.service"),
        "aster-voice-candidate.service": service_pid("aster-voice-candidate.service"),
    }
    engine = Kokoro(str(model), str(voices))
    results = []
    started = time.monotonic()
    try:
        for sample in samples:
            slot = int(sample["slot"])
            text = cleanup.speech_text(sample["sample_text"])
            units = cleanup.narration_units(text)
            if not units:
                raise RuntimeError("benchmark-empty-units")
            rendered = []
            timings = []
            cursor = 0
            render_started = time.monotonic()
            for unit_text, pause_seconds in units:
                audio, sample_rate = engine.create(
                    unit_text,
                    voice=VOICE,
                    speed=SPEED,
                    lang=LANGUAGE,
                )
                audio = np.asarray(audio, dtype=np.float32).reshape(-1)
                if sample_rate != SAMPLE_RATE or len(audio) < 1 or not np.isfinite(audio).all():
                    raise RuntimeError("benchmark-render-format")
                start, end = cursor, cursor + len(audio)
                if end <= start:
                    raise RuntimeError("benchmark-timing-order")
                timings.append({
                    "unit": len(timings) + 1,
                    "start_sample": start,
                    "end_sample": end,
                    "spoken_sha256": hashlib.sha256(unit_text.encode("utf-8")).hexdigest(),
                })
                rendered.append(audio)
                cursor = end
                pause_count = round(float(pause_seconds) * SAMPLE_RATE)
                if pause_count:
                    rendered.append(np.zeros(pause_count, dtype=np.float32))
                    cursor += pause_count
            waveform = np.concatenate(rendered)
            opus = output / f"slot-{slot:02d}.opus"
            duration, opus_bytes = encode_opus(waveform, opus)
            timing_path = output / f"slot-{slot:02d}.timing.json"
            timing_path.write_text(
                json.dumps({
                    "schema": 1,
                    "timing_level": "sentence-clause-sample-index",
                    "sample_rate": SAMPLE_RATE,
                    "total_samples": len(waveform),
                    "units": timings,
                }, sort_keys=True, separators=(",", ":")),
                encoding="utf-8",
            )
            os.chmod(opus, 0o600)
            os.chmod(timing_path, 0o600)
            render_seconds = time.monotonic() - render_started
            results.append({
                "slot": slot,
                "full_word_count": int(sample["word_count"]),
                "sample_word_count": len(WORD.findall(text)),
                "chapter_count": int(sample["chapter_count"]),
                "audio_seconds": duration,
                "render_seconds": render_seconds,
                "real_time_factor": render_seconds / duration,
                "opus_bytes": opus_bytes,
                "opus_sha256": sha256_file(opus),
                "timing_sha256": sha256_file(timing_path),
            })
            print(json.dumps({
                "slot": slot,
                "state": "complete",
                "audio_seconds": round(duration, 3),
                "real_time_factor": round(render_seconds / duration, 4),
                "opus_bytes": opus_bytes,
            }, sort_keys=True), flush=True)
    finally:
        engine.voices.close()
    final_pids = {
        "aster-speech.service": service_pid("aster-speech.service"),
        "aster-voice-candidate.service": service_pid("aster-voice-candidate.service"),
    }
    if final_pids != initial_pids:
        raise RuntimeError("benchmark-service-pid-change")
    report = {
        "schema": 1,
        "plan_sha256": sha256_file(plan_path),
        "voice": {
            "engine": "kokoro-onnx",
            "model": model.name,
            "model_sha256": MODEL_SHA256,
            "voice": VOICE,
            "language": LANGUAGE,
            "speed": SPEED,
        },
        "codec": {"name": "opus", "bitrate": 48_000, "channels": 1, "sample_rate": 48_000},
        "cleanup": "news-digest-digest_text.py-current-repository-snapshot",
        "service_pids_unchanged": True,
        "wall_seconds": time.monotonic() - started,
        "results": results,
    }
    report_path = output / "report.json"
    report_path.write_text(json.dumps(report, sort_keys=True, separators=(",", ":")), encoding="utf-8")
    os.chmod(report_path, 0o600)
    return {
        "sample_count": len(results),
        "audio_seconds": sum(item["audio_seconds"] for item in results),
        "wall_seconds": report["wall_seconds"],
        "opus_bytes": sum(item["opus_bytes"] for item in results),
        "service_pids_unchanged": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--voices", type=Path, required=True)
    parser.add_argument("--cleanup-dir", type=Path, required=True)
    args = parser.parse_args()
    summary = render_plan(args.plan, args.output, args.model, args.voices, args.cleanup_dir)
    print(json.dumps(summary, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
