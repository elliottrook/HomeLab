#!/usr/bin/env python3
"""Content-free, repeatable Piper/Kokoro latency benchmark for Aster M1.

The fixture text is synthetic and versioned in Git. Results contain fixture IDs,
sizes and timings, never text or audio. Generated WAV data is temporary.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import resource
import statistics
import subprocess
import tempfile
import time
import wave
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Protocol

DEFAULT_FIXTURES = Path(__file__).with_name("tts_benchmark_fixtures.json")


@dataclass(frozen=True)
class Fixture:
    id: str
    category: str
    text: str


@dataclass(frozen=True)
class Sample:
    fixture_id: str
    category: str
    iteration: int
    characters: int
    synth_seconds: float
    audio_seconds: float
    real_time_factor: float


class Renderer(Protocol):
    name: str
    load_seconds: float

    def render(self, text: str) -> tuple[float, float]: ...

    def close(self) -> None: ...


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_fixtures(path: Path) -> list[Fixture]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, list) or not raw:
        raise ValueError("Fixture file must contain a non-empty list")
    fixtures = []
    seen = set()
    for item in raw:
        if not isinstance(item, dict) or set(item) != {"id", "category", "text"}:
            raise ValueError("Each fixture must contain only id, category and text")
        fixture = Fixture(**item)
        if not fixture.id or fixture.id in seen or not fixture.category or not fixture.text.strip():
            raise ValueError("Fixture IDs must be unique and all values must be non-empty")
        seen.add(fixture.id)
        fixtures.append(fixture)
    return fixtures


def wav_duration(path: Path) -> float:
    with wave.open(str(path), "rb") as wav:
        return wav.getnframes() / wav.getframerate()


class PiperRenderer:
    name = "piper"
    load_seconds = 0.0

    def __init__(self, binary: Path, model: Path, length_scale: str) -> None:
        self.binary = binary
        self.model = model
        self.length_scale = length_scale

    def render(self, text: str) -> tuple[float, float]:
        with tempfile.NamedTemporaryFile(suffix=".wav") as output:
            started = time.perf_counter()
            subprocess.run(
                [
                    str(self.binary),
                    "--model",
                    str(self.model),
                    "--length_scale",
                    self.length_scale,
                    "--output_file",
                    output.name,
                ],
                input=text,
                text=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=60,
                check=True,
            )
            elapsed = time.perf_counter() - started
            return elapsed, wav_duration(Path(output.name))

    def close(self) -> None:
        return None


class KokoroRenderer:
    name = "kokoro"

    def __init__(
        self,
        model: Path,
        voices: Path,
        voice: str,
        speed: float,
        language: str,
        intra_op_threads: int | None,
        inter_op_threads: int | None,
    ) -> None:
        from kokoro_onnx import Kokoro
        from kokoro_onnx.session import resolve_providers

        started = time.perf_counter()
        if intra_op_threads is None and inter_op_threads is None:
            self.engine = Kokoro(str(model), str(voices))
        else:
            import onnxruntime as ort

            options = ort.SessionOptions()
            if intra_op_threads is not None:
                options.intra_op_num_threads = intra_op_threads
            if inter_op_threads is not None:
                options.inter_op_num_threads = inter_op_threads
            session = ort.InferenceSession(
                str(model), sess_options=options, providers=resolve_providers()
            )
            # kokoro-onnx 0.6.1 does not expose SessionOptions in its public
            # constructor. The pinned benchmark deliberately uses its setup
            # method so M1 can measure explicit LXC-safe thread counts.
            self.engine = Kokoro.__new__(Kokoro)
            self.engine._setup(
                session=session,
                model_path=str(model),
                voices_path=str(voices),
                espeak_config=None,
                vocab_config=None,
            )
        self.load_seconds = time.perf_counter() - started
        self.voice = voice
        self.speed = speed
        self.language = language

    def render(self, text: str) -> tuple[float, float]:
        started = time.perf_counter()
        audio, sample_rate = self.engine.create(
            text, voice=self.voice, speed=self.speed, lang=self.language
        )
        elapsed = time.perf_counter() - started
        return elapsed, len(audio) / sample_rate

    def close(self) -> None:
        self.engine.voices.close()


def percentile(values: list[float], fraction: float) -> float:
    if not values:
        raise ValueError("Cannot calculate a percentile of no values")
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, int((len(ordered) * fraction) + 0.999999) - 1))
    return ordered[index]


def summarize(samples: list[Sample]) -> dict[str, float]:
    synth = [sample.synth_seconds for sample in samples]
    rtf = [sample.real_time_factor for sample in samples]
    return {
        "synth_p50_seconds": round(statistics.median(synth), 6),
        "synth_p95_seconds": round(percentile(synth, 0.95), 6),
        "rtf_p50": round(statistics.median(rtf), 6),
        "rtf_p95": round(percentile(rtf, 0.95), 6),
    }


def run(renderer: Renderer, fixtures: list[Fixture], warmups: int, iterations: int) -> list[Sample]:
    for _ in range(warmups):
        renderer.render(fixtures[0].text)
    samples = []
    for iteration in range(1, iterations + 1):
        for fixture in fixtures:
            elapsed, duration = renderer.render(fixture.text)
            samples.append(
                Sample(
                    fixture_id=fixture.id,
                    category=fixture.category,
                    iteration=iteration,
                    characters=len(fixture.text),
                    synth_seconds=round(elapsed, 6),
                    audio_seconds=round(duration, 6),
                    real_time_factor=round(elapsed / duration, 6),
                )
            )
    return samples


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("engine", choices=("piper", "kokoro"))
    parser.add_argument("--fixtures", type=Path, default=DEFAULT_FIXTURES)
    parser.add_argument(
        "--fixture-id",
        action="append",
        dest="fixture_ids",
        help="run only this fixture ID; repeat to select more than one",
    )
    parser.add_argument("--iterations", type=int, default=5)
    parser.add_argument("--warmups", type=int, default=1)
    parser.add_argument("--piper-binary", type=Path)
    parser.add_argument("--piper-model", type=Path)
    parser.add_argument("--length-scale", default="1.15")
    parser.add_argument("--kokoro-model", type=Path)
    parser.add_argument("--kokoro-voices", type=Path)
    parser.add_argument("--voice", default="bm_daniel")
    parser.add_argument("--speed", type=float, default=0.95)
    parser.add_argument("--language", default="en-gb")
    parser.add_argument("--intra-op-threads", type=int)
    parser.add_argument("--inter-op-threads", type=int)
    return parser.parse_args()


def require_path(value: Path | None, flag: str) -> Path:
    if value is None or not value.is_file():
        raise SystemExit(f"{flag} must name an existing file")
    return value


def main() -> int:
    args = parse_args()
    if args.iterations < 1 or args.warmups < 0:
        raise SystemExit("iterations must be positive and warmups cannot be negative")
    fixtures = load_fixtures(args.fixtures)
    if args.fixture_ids:
        requested = set(args.fixture_ids)
        known = {fixture.id for fixture in fixtures}
        unknown = sorted(requested - known)
        if unknown:
            raise SystemExit(f"unknown fixture ID(s): {', '.join(unknown)}")
        fixtures = [fixture for fixture in fixtures if fixture.id in requested]
    assets: dict[str, Any]
    if args.engine == "piper":
        binary = require_path(args.piper_binary, "--piper-binary")
        model = require_path(args.piper_model, "--piper-model")
        renderer: Renderer = PiperRenderer(binary, model, args.length_scale)
        assets = {"model_sha256": sha256(model), "length_scale": args.length_scale}
    else:
        model = require_path(args.kokoro_model, "--kokoro-model")
        voices = require_path(args.kokoro_voices, "--kokoro-voices")
        for value, flag in (
            (args.intra_op_threads, "--intra-op-threads"),
            (args.inter_op_threads, "--inter-op-threads"),
        ):
            if value is not None and value < 1:
                raise SystemExit(f"{flag} must be positive")
        renderer = KokoroRenderer(
            model,
            voices,
            args.voice,
            args.speed,
            args.language,
            args.intra_op_threads,
            args.inter_op_threads,
        )
        assets = {
            "model_sha256": sha256(model),
            "voices_sha256": sha256(voices),
            "voice": args.voice,
            "speed": args.speed,
            "language": args.language,
            "intra_op_threads": args.intra_op_threads,
            "inter_op_threads": args.inter_op_threads,
        }
    try:
        samples = run(renderer, fixtures, args.warmups, args.iterations)
    finally:
        renderer.close()
    report = {
        "schema_version": 1,
        "engine": renderer.name,
        "fixture_file_sha256": sha256(args.fixtures),
        "fixture_count": len(fixtures),
        "warmups": args.warmups,
        "iterations": args.iterations,
        "engine_load_seconds": round(renderer.load_seconds, 6),
        "max_rss_kb": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "thread_environment": {
            name: os.environ.get(name)
            for name in ("OMP_NUM_THREADS", "OMP_WAIT_POLICY", "ORT_LOG_SEVERITY_LEVEL")
        },
        "assets": assets,
        "summary": summarize(samples),
        "samples": [asdict(sample) for sample in samples],
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
