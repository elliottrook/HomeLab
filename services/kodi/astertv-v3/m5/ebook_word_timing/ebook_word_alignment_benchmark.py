#!/opt/whisper-bench/bin/python
"""Fixed, content-private word-alignment benchmark for one canonical chapter.

This is a registered Lab Hours workload target, not a general CLI.  It accepts
only the lease identity supplied by the host adapter, permits no model download
and never emits source or recognized text.  A recognition mismatch is a valid
negative benchmark result; it is never repaired with inferred timestamps.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import time
import wave


WORKLOAD_ID = "astertv-v3-ebook-word-alignment-v1"
LEASE_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:-]{1,127}")
SHA = re.compile(r"[0-9a-f]{64}")
ROOT = Path("/mnt/aster-reader")
POINTER = ROOT / "ready/81.json"
GENERATION = ROOT / "generations/81/221bb0c3c80d80005e05e5d2a4bbe4f2bf74debdf0fd55ce9f8de4ba77c4e830"
MANIFEST = GENERATION / "manifest.json"
CONTENT = GENERATION / "content/0002.json"
TIMING = GENERATION / "timing/0002.json"
AUDIO = GENERATION / "chapters/0002.opus"
PREFIX_CUES = 10
PREFIX_END_SAMPLE = 1_390_063
PREFIX_SOURCE_END = 930
PREFIX_SOURCE_SHA256 = "5c2b6901b2272e7cbda32c451b1bf598f9f70cb213259f36e8b2513d4d65ee5f"
INPUT_PINS = {
    POINTER: "94bc52445f6dedf6e640b5aa54da6eebf14ed8d33b33d69f3d6404b21ed2dbe2",
    MANIFEST: "1fde84377288795f522d5946380734e43dc643fd58b06720fdf79b56d59dd257",
    CONTENT: "6282f431277992b4cb0856aa103d3da60124c78633f7dbd9cf89b6bca037db98",
    TIMING: "04522f54880e46338b3e0bfff33e1d9b0ea49e52f4f3645b08cc5c9cbdd34bcf",
    AUDIO: "ac0875e06eee85f27977f5e03f518b43d54e3fa6e0acddad6edeb739f53a802b",
}
ALIGNMENT = Path("/var/lib/aster-speech/word-alignment-harness-20261026/word_alignment.py")
ALIGNMENT_SHA256 = "4a2b040ebbd459eee6e5b7f59dca2398f574a51766028e75369cdace2f96b5d4"
MODEL = Path("/root/.cache/huggingface/hub/models--Systran--faster-whisper-small.en/snapshots/d1d751a5f8271d482d14ca55d9e2deeebbae577f")
MODEL_CACHE = Path("/root/.cache/huggingface/hub")
MODEL_PINS = {
    "config.json": "666a9605530ac1f61fa8177f3702b4dacec9966749e42610839fcc32661d5fae",
    "model.bin": "62b2a45b05ee59acb4a5341b33ee35e041395d378d418a18acfe4c9e768ee37a",
    "tokenizer.json": "929c5252409436dce1b38a75d1abbcb5e132d170d8e324e4e04ed915fa2d22df",
    "vocabulary.txt": "ff77588746d3a2595d32ab5b69ffd7b95ce2441ac57533cb66fc3eb575a115cf",
}
PYTHON_SHA256 = "889c603f0d17cb54060951bcf4c4f9b8c9ebd9e52b392c70209bbb9755d797d9"
PYTHON_TARGET = Path("/usr/bin/python3.13")
FFMPEG = Path("/usr/bin/ffmpeg")
FFMPEG_SHA256 = "e8a8d46f5225f3062cec7c07fb145d58ae73c603cb740dcd5bad34bfb54e455a"
RESULT_ROOT = Path("/var/lib/aster-speech/word-alignment-benchmarks")


class BenchmarkError(RuntimeError):
    pass


def sha256(path: Path, *, limit: int | None = None) -> str:
    info = path.lstat()
    if (not stat.S_ISREG(info.st_mode) or path.is_symlink() or info.st_nlink != 1
            or (limit is not None and info.st_size > limit)):
        raise BenchmarkError("PINNED_FILE_CUSTODY")
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def require_hash(path: Path, expected: str, *, limit: int | None = None) -> None:
    if not SHA.fullmatch(expected) or sha256(path, limit=limit) != expected:
        raise BenchmarkError("PINNED_FILE_DRIFT")


def require_model_hash(path: Path, expected: str, *, limit: int) -> None:
    """Accept snapshot links only when they resolve inside the pinned cache."""
    try:
        resolved = path.resolve(strict=True)
        cache = MODEL_CACHE.resolve(strict=True)
        resolved.relative_to(cache)
    except (OSError, ValueError):
        raise BenchmarkError("PINNED_MODEL_CUSTODY") from None
    info = resolved.lstat()
    if (not stat.S_ISREG(info.st_mode) or resolved.is_symlink() or info.st_nlink != 1
            or info.st_size > limit):
        raise BenchmarkError("PINNED_MODEL_CUSTODY")
    digest = hashlib.sha256()
    with resolved.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    if not SHA.fullmatch(expected) or digest.hexdigest() != expected:
        raise BenchmarkError("PINNED_FILE_DRIFT")


def require_runtime_hash(path: Path, target: Path, expected: str, *, limit: int) -> None:
    """Accept the fixed venv interpreter link only at its pinned system target."""
    try:
        resolved = path.resolve(strict=True)
        pinned = target.resolve(strict=True)
    except OSError:
        raise BenchmarkError("PINNED_RUNTIME_CUSTODY") from None
    if resolved != pinned:
        raise BenchmarkError("PINNED_RUNTIME_CUSTODY")
    require_hash(pinned, expected, limit=limit)


def load_inputs() -> tuple[str, float]:
    for path, expected in INPUT_PINS.items():
        require_hash(path, expected, limit=1_073_741_824)
    pointer = json.loads(POINTER.read_text(encoding="utf-8"))
    if (pointer.get("schema") != 1 or pointer.get("book_id") != 81
            or pointer.get("generation") != str(GENERATION.relative_to(ROOT))
            or pointer.get("manifest_sha256") != INPUT_PINS[MANIFEST]):
        raise BenchmarkError("POINTER_IDENTITY")
    content = json.loads(CONTENT.read_text(encoding="utf-8"))
    timing = json.loads(TIMING.read_text(encoding="utf-8"))
    if (set(content) != {"schema", "chapter", "text", "text_sha256"}
            or content.get("schema") != 1 or content.get("chapter") != 2
            or not isinstance(content.get("text"), str)):
        raise BenchmarkError("CONTENT_SCHEMA")
    text = content["text"]
    if hashlib.sha256(text.encode()).hexdigest() != content.get("text_sha256"):
        raise BenchmarkError("CONTENT_IDENTITY")
    if (set(timing) != {"schema", "timing_level", "sample_rate", "total_samples",
                       "cleaned_text_sha256", "cues"}
            or timing.get("schema") != 1
            or timing.get("timing_level") != "sentence-sample-index"
            or timing.get("sample_rate") != 24_000
            or timing.get("cleaned_text_sha256") != content["text_sha256"]
            or not isinstance(timing.get("cues"), list)
            or len(timing["cues"]) < PREFIX_CUES):
        raise BenchmarkError("TIMING_SCHEMA")
    cues = timing["cues"][:PREFIX_CUES]
    previous_source = previous_sample = 0
    for cue in cues:
        if set(cue) != {"source_start", "source_end", "start_sample", "end_sample", "spoken_sha256"}:
            raise BenchmarkError("CUE_SCHEMA")
        values = (cue["source_start"], cue["source_end"], cue["start_sample"], cue["end_sample"])
        if (not all(type(value) is int for value in values)
                or not previous_source <= values[0] < values[1] <= len(text)
                or not previous_sample <= values[2] < values[3] <= timing["total_samples"]
                or hashlib.sha256(text[values[0]:values[1]].encode()).hexdigest()
                   != cue["spoken_sha256"]):
            raise BenchmarkError("CUE_IDENTITY")
        previous_source, previous_sample = values[1], values[3]
    if (cues[0]["source_start"] != 0 or cues[-1]["source_end"] != PREFIX_SOURCE_END
            or cues[-1]["end_sample"] != PREFIX_END_SAMPLE):
        raise BenchmarkError("PREFIX_BOUNDARY")
    source = text[:PREFIX_SOURCE_END]
    if hashlib.sha256(source.encode()).hexdigest() != PREFIX_SOURCE_SHA256:
        raise BenchmarkError("PREFIX_IDENTITY")
    return source, PREFIX_END_SAMPLE / 24_000


def load_alignment():
    require_hash(ALIGNMENT, ALIGNMENT_SHA256, limit=32_768)
    spec = importlib.util.spec_from_file_location("aster_word_alignment", ALIGNMENT)
    if spec is None or spec.loader is None:
        raise BenchmarkError("ALIGNMENT_IMPORT")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def require_runtime() -> None:
    require_runtime_hash(Path(sys.executable), PYTHON_TARGET, PYTHON_SHA256,
                         limit=32 * 1024 * 1024)
    require_hash(FFMPEG, FFMPEG_SHA256, limit=128 * 1024 * 1024)
    for name, expected in MODEL_PINS.items():
        require_model_hash(MODEL / name, expected, limit=600 * 1024 * 1024)


def atomic_json(path: Path, value: object) -> None:
    encoded = (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()
    descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(encoded)
        stream.flush()
        os.fsync(stream.fileno())


def run(lease_id: str, generation: int) -> dict[str, object]:
    if not LEASE_RE.fullmatch(lease_id) or type(generation) is not int or generation < 1:
        raise BenchmarkError("LEASE_IDENTITY")
    require_runtime()
    source, wanted_duration = load_inputs()
    alignment = load_alignment()
    attempt_id = hashlib.sha256(f"{lease_id}:{generation}".encode()).hexdigest()[:24]
    RESULT_ROOT.mkdir(mode=0o700, parents=True, exist_ok=True)
    if RESULT_ROOT.lstat().st_mode & 0o077:
        raise BenchmarkError("RESULT_ROOT_CUSTODY")
    attempt = RESULT_ROOT / attempt_id
    attempt.mkdir(mode=0o700)
    started = time.monotonic()
    outcome: dict[str, object] = {
        "schema": "astertv-ebook-word-alignment-benchmark.v1",
        "workload_id": WORKLOAD_ID,
        "input_manifest_sha256": INPUT_PINS[MANIFEST],
        "input_audio_sha256": INPUT_PINS[AUDIO],
        "source_prefix_sha256": PREFIX_SOURCE_SHA256,
        "model_sha256": MODEL_PINS["model.bin"],
        "prefix_cues": PREFIX_CUES,
        "network_used": False,
        "text_exported": False,
        "timestamps_inferred": False,
        "passed": False,
        "failure_code": "NOT_RUN",
    }
    temporary = Path(tempfile.mkdtemp(prefix="audio-", dir=attempt))
    wav_path = temporary / "prefix.wav"
    try:
        duration_arg = f"{wanted_duration:.9f}"
        converted = subprocess.run(
            (str(FFMPEG), "-nostdin", "-v", "error", "-i", str(AUDIO), "-t", duration_arg,
             "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", str(wav_path)),
            capture_output=True, timeout=120, check=False,
        )
        if converted.returncode != 0 or converted.stdout or len(converted.stderr) > 16_384:
            raise BenchmarkError("AUDIO_DECODE")
        with wave.open(str(wav_path), "rb") as stream:
            if (stream.getnchannels(), stream.getsampwidth(), stream.getframerate()) != (1, 2, 16_000):
                raise BenchmarkError("AUDIO_FORMAT")
            duration = stream.getnframes() / stream.getframerate()
        if not math.isfinite(duration) or abs(duration - wanted_duration) > 0.08:
            raise BenchmarkError("AUDIO_DURATION")
        os.environ.update({"HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1"})
        from faster_whisper import WhisperModel
        model = WhisperModel(str(MODEL), device="cpu", compute_type="int8",
                             cpu_threads=2, num_workers=1, local_files_only=True)
        segments, info = model.transcribe(
            str(wav_path), beam_size=5, language="en", word_timestamps=True,
            vad_filter=False, condition_on_previous_text=False,
        )
        measured = []
        private = []
        for segment in segments:
            for item in segment.words or ():
                measured.append(alignment.TimedWord(item.word, item.start, item.end))
                private.append({
                    "token_sha256": hashlib.sha256(item.word.encode()).hexdigest(),
                    "start": item.start, "end": item.end,
                })
        atomic_json(attempt / "measurements.json", private)
        try:
            cues = alignment.align_exact(source, measured, duration)
        except ValueError as error:
            code = str(error)
            outcome["failure_code"] = code if re.fullmatch(r"alignment-[a-z-]+", code) else "ALIGNMENT_REJECTED"
            outcome["measured_word_count"] = len(measured)
        else:
            atomic_json(attempt / "cues.json", [cue.__dict__ for cue in cues])
            outcome.update({"passed": True, "failure_code": "NONE",
                            "measured_word_count": len(measured), "word_count": len(cues)})
        outcome["detected_language"] = getattr(info, "language", None)
    finally:
        shutil.rmtree(temporary, ignore_errors=True)
    outcome["elapsed_seconds"] = round(time.monotonic() - started, 3)
    atomic_json(attempt / "result.json", outcome)
    return outcome


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lease-id", required=True)
    parser.add_argument("--generation", required=True, type=int)
    args = parser.parse_args()
    os.umask(0o077)
    os.nice(10)
    if os.geteuid() != 0 or os.uname().nodename != "aster-speech":
        raise SystemExit("ASTER_SPEECH_ROOT_REQUIRED")
    try:
        value = run(args.lease_id, args.generation)
    except (BenchmarkError, OSError, ValueError, json.JSONDecodeError, subprocess.SubprocessError) as error:
        code = str(error)
        if not re.fullmatch(r"[A-Z0-9_-]{1,80}", code):
            code = type(error).__name__
        print(json.dumps({"schema": "astertv-ebook-word-alignment-failure.v1", "code": code},
                         sort_keys=True), file=sys.stderr)
        return 1
    print(json.dumps(value, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
