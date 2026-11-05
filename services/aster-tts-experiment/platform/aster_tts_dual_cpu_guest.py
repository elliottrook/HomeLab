#!/usr/bin/env python3
"""Fixed guest workload for the two-candidate Aster TTS CPU screen."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import time
import wave


WORKLOAD_ID = "aster-tts-dual-cpu-screen-v1"
LEASE_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:-]{1,127}")
ROOT = Path("/opt/aster-qwentts-candidate")
BINARY = ROOT / "build-cpu/qwen-tts"
CODEC = ROOT / "models/qwen-tokenizer-12hz-Q8_0.gguf"
PLAN = ROOT / "experiment/plan.json"
REFERENCE_WAV = ROOT / "experiment/aster-synthetic-reference.wav"
REFERENCE_TEXT = ROOT / "experiment/aster-synthetic-reference.txt"
OUTPUT_ROOT = Path("/var/lib/aster-tts-experiment")
SEED = 20261104
SAMPLE_RATE = 24_000
PER_CANDIDATE_TIMEOUT = 2_000
MAX_STDERR_BYTES = 65_536
PINS = {
    BINARY: "aea3907bfda5c95763e0e53c48d09602c83cac80858eb673aa67f71923aefba6",
    CODEC: "1883beeed99348fc35e23dd225e9082f93f6f8c109330a33d935baa8acdbfd94",
    PLAN: "83616d4e4e5329d626e23597542487f0e43903622f0daea4c5648d53d74a6f90",
    REFERENCE_WAV: "1b026d7883793e7eb75f384629101a8a7994dda341719dc6ebd090319cae8e39",
    REFERENCE_TEXT: "3b51c819ae7bd04bdf13c8a9183696f76ba77cce04ddcbb02d024927944e6733",
}
CANDIDATES = (
    ("qwen3-tts-0.6b-base-q8-cpu",
     ROOT / "models/qwen-talker-0.6b-base-Q8_0.gguf",
     "d54dbaf10591421fa764ed630d764efa717ae40cd959bd48c66d4eb1af226426"),
    ("qwen3-tts-1.7b-base-q8-cpu",
     ROOT / "models/qwen-talker-1.7b-base-Q8_0.gguf",
     "4b9a33a236908dd9435a42f7a396e38038329d053b704342a6413c08544c4fda"),
)


class ScreenError(RuntimeError):
    pass


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def verify(path: Path, expected: str) -> None:
    try:
        stat = path.lstat()
    except FileNotFoundError as error:
        raise ScreenError("TTS_SCREEN_PIN_MISSING") from error
    if (not path.is_file() or path.is_symlink() or stat.st_nlink != 1
            or sha256_file(path) != expected):
        raise ScreenError("TTS_SCREEN_PIN_DRIFT")


def atomic_json(path: Path, value: dict[str, object]) -> None:
    descriptor, raw = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(raw)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(value, stream, sort_keys=True, separators=(",", ":"), allow_nan=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def wav_metrics(path: Path, word_count: int) -> dict[str, object]:
    with wave.open(str(path), "rb") as audio:
        if (audio.getnchannels() != 1 or audio.getsampwidth() != 2
                or audio.getframerate() != SAMPLE_RATE or audio.getcomptype() != "NONE"):
            raise ScreenError("TTS_SCREEN_WAV_CONTRACT")
        frames = audio.getnframes()
    if frames <= 0:
        raise ScreenError("TTS_SCREEN_WAV_EMPTY")
    seconds = frames / SAMPLE_RATE
    words_per_minute = word_count * 60.0 / seconds
    if not 90.0 <= words_per_minute <= 260.0:
        raise ScreenError("TTS_SCREEN_PACING")
    return {
        "audio_seconds": round(seconds, 6),
        "words_per_minute": round(words_per_minute, 6),
        "wav_bytes": path.stat().st_size,
        "wav_sha256": sha256_file(path),
    }


def run(lease_id: str, generation: int) -> dict[str, object]:
    if not LEASE_RE.fullmatch(lease_id) or generation < 1:
        raise ScreenError("TTS_SCREEN_LEASE_IDENTITY")
    for path, expected in PINS.items():
        verify(path, expected)
    for _identifier, model, expected in CANDIDATES:
        verify(model, expected)
    plan = json.loads(PLAN.read_text(encoding="utf-8"))
    passages = plan.get("passages") if isinstance(plan, dict) else None
    selected = next((item for item in passages or [] if item.get("id") == "homographs"), None)
    if (not isinstance(selected, dict)
            or not isinstance(selected.get("normalized_text"), str)
            or not isinstance(selected.get("normalized_sha256"), str)):
        raise ScreenError("TTS_SCREEN_PLAN")
    text = selected["normalized_text"]
    if hashlib.sha256(text.encode()).hexdigest() != selected["normalized_sha256"]:
        raise ScreenError("TTS_SCREEN_TEXT_DRIFT")
    word_count = len(text.split())
    run_id = hashlib.sha256(f"{lease_id}:{generation}".encode()).hexdigest()[:20]
    output = OUTPUT_ROOT / f"dual-cpu-{run_id}"
    output.mkdir(parents=True, exist_ok=False, mode=0o700)
    results = []
    try:
        for identifier, model, model_sha in CANDIDATES:
            wav = output / f"{identifier}.wav"
            partial = output / f".{identifier}.wav.partial"
            command = (
                str(BINARY), "--model", str(model), "--codec", str(CODEC),
                "--device", "CPU", "--lang", "English",
                "--ref-wav", str(REFERENCE_WAV), "--ref-text", str(REFERENCE_TEXT),
                "--seed", str(SEED), "--format", "wav16", "-o", str(partial),
            )
            started = time.monotonic()
            try:
                process = subprocess.run(
                    command, input=text + "\n", text=True, capture_output=True,
                    timeout=PER_CANDIDATE_TIMEOUT,
                    env={**os.environ, "GGML_BACKEND": "CPU"}, check=False,
                )
            except subprocess.TimeoutExpired as error:
                raise ScreenError("TTS_SCREEN_TIMEOUT") from error
            elapsed = time.monotonic() - started
            if len(process.stderr.encode()) > MAX_STDERR_BYTES:
                raise ScreenError("TTS_SCREEN_STDERR_SIZE")
            if process.returncode != 0 or not partial.is_file():
                raise ScreenError("TTS_SCREEN_RENDER_FAILED")
            os.chmod(partial, 0o600)
            os.replace(partial, wav)
            metrics = wav_metrics(wav, word_count)
            results.append({
                "candidate_id": identifier,
                "model_sha256": model_sha,
                "backend": "CPU",
                "seed": SEED,
                "input_sha256": selected["normalized_sha256"],
                "render_seconds": round(elapsed, 6),
                "real_time_factor": round(elapsed / metrics["audio_seconds"], 6),
                **metrics,
            })
        manifest = {
            "schema": "aster-tts-dual-cpu-screen-result.v1",
            "workload_id": WORKLOAD_ID,
            "lease_id": lease_id,
            "generation": generation,
            "binary_sha256": PINS[BINARY],
            "codec_sha256": PINS[CODEC],
            "reference_wav_sha256": PINS[REFERENCE_WAV],
            "input_sha256": selected["normalized_sha256"],
            "candidate_count": 2,
            "gpu_used": False,
            "network_used": False,
            "production_route_changed": False,
            "results": results,
        }
        atomic_json(output / "manifest.json", manifest)
        return manifest
    except BaseException:
        shutil.rmtree(output, ignore_errors=True)
        raise


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lease-id", required=True)
    parser.add_argument("--generation", required=True, type=int)
    args = parser.parse_args()
    try:
        result = run(args.lease_id, args.generation)
    except ScreenError as error:
        print(json.dumps({"schema": "aster-tts-dual-cpu-screen-error.v1",
                          "code": str(error)}, sort_keys=True), file=os.sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
