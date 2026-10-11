#!/usr/bin/env python3
"""Local, content-free STT accuracy and latency benchmark for Aster M7."""

from __future__ import annotations

import argparse
import json
import re
import statistics
import time
import wave
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Protocol

DEFAULT_FIXTURES = Path(__file__).with_name("stt_benchmark_fixtures.json")


@dataclass(frozen=True)
class Fixture:
    id: str
    category: str
    audio: str
    text: str


@dataclass(frozen=True)
class Sample:
    fixture_id: str
    category: str
    iteration: int
    audio_seconds: float
    transcribe_seconds: float
    real_time_factor: float
    expected_words: int
    recognized_words: int
    word_errors: int
    word_error_rate: float
    exact: bool


class Transcriber(Protocol):
    name: str
    load_seconds: float

    def transcribe(self, audio: Path) -> str: ...


def normalize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+(?:'[a-z0-9]+)?", text.casefold().replace("’", "'"))


def edit_distance(expected: list[str], actual: list[str]) -> int:
    previous = list(range(len(actual) + 1))
    for expected_word in expected:
        current = [previous[0] + 1]
        for index, actual_word in enumerate(actual, start=1):
            current.append(min(
                current[-1] + 1,
                previous[index] + 1,
                previous[index - 1] + (expected_word != actual_word),
            ))
        previous = current
    return previous[-1]


def load_fixtures(path: Path) -> list[Fixture]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, list) or not raw:
        raise ValueError("Fixture file must contain a non-empty list")
    fixtures: list[Fixture] = []
    seen: set[str] = set()
    for item in raw:
        if not isinstance(item, dict) or set(item) != {"id", "category", "audio", "text"}:
            raise ValueError("Each fixture must contain only id, category, audio and text")
        fixture = Fixture(**item)
        if (
            not fixture.id
            or fixture.id in seen
            or not fixture.category
            or not fixture.audio.endswith(".wav")
            or not fixture.text.strip()
        ):
            raise ValueError("Fixtures require unique IDs, WAV paths and non-empty values")
        seen.add(fixture.id)
        fixtures.append(fixture)
    return fixtures


def wav_duration(path: Path) -> float:
    with wave.open(str(path), "rb") as audio:
        if audio.getnframes() < 1 or audio.getframerate() < 1:
            raise ValueError(f"invalid WAV fixture: {path.name}")
        return audio.getnframes() / audio.getframerate()


class FasterWhisperTranscriber:
    def __init__(
        self,
        model: str,
        cache_dir: Path,
        vad: bool,
        hotwords: str | None,
        cpu_threads: int,
    ) -> None:
        from faster_whisper import WhisperModel

        started = time.perf_counter()
        self.engine = WhisperModel(
            model,
            device="cpu",
            compute_type="int8",
            download_root=str(cache_dir),
            cpu_threads=cpu_threads,
        )
        self.load_seconds = time.perf_counter() - started
        self.name = model
        self.vad = vad
        self.hotwords = hotwords

    def transcribe(self, audio: Path) -> str:
        segments, _ = self.engine.transcribe(
            str(audio),
            beam_size=1,
            language="en",
            condition_on_previous_text=False,
            vad_filter=self.vad,
            hotwords=self.hotwords,
        )
        return "".join(segment.text for segment in segments).strip()


def run(
    transcriber: Transcriber,
    fixtures: list[Fixture],
    audio_root: Path,
    warmups: int,
    iterations: int,
) -> list[Sample]:
    resolved = [(fixture, audio_root / fixture.audio) for fixture in fixtures]
    missing = [path.name for _, path in resolved if not path.is_file()]
    if missing:
        raise FileNotFoundError("missing audio fixture(s): " + ", ".join(missing))
    for _ in range(warmups):
        transcriber.transcribe(resolved[0][1])
    samples: list[Sample] = []
    for iteration in range(1, iterations + 1):
        for fixture, audio_path in resolved:
            duration = wav_duration(audio_path)
            started = time.perf_counter()
            recognized_text = transcriber.transcribe(audio_path)
            elapsed = time.perf_counter() - started
            expected = normalize(fixture.text)
            recognized = normalize(recognized_text)
            errors = edit_distance(expected, recognized)
            samples.append(Sample(
                fixture_id=fixture.id,
                category=fixture.category,
                iteration=iteration,
                audio_seconds=round(duration, 6),
                transcribe_seconds=round(elapsed, 6),
                real_time_factor=round(elapsed / duration, 6),
                expected_words=len(expected),
                recognized_words=len(recognized),
                word_errors=errors,
                word_error_rate=round(errors / len(expected), 6),
                exact=expected == recognized,
            ))
    return samples


def nearest_rank(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, int(len(ordered) * fraction + 0.999999) - 1))
    return ordered[index]


def summarize(samples: list[Sample]) -> dict[str, Any]:
    total_words = sum(sample.expected_words for sample in samples)
    total_errors = sum(sample.word_errors for sample in samples)
    latencies = [sample.transcribe_seconds for sample in samples]
    return {
        "samples": len(samples),
        "exact_accuracy": round(sum(sample.exact for sample in samples) / len(samples), 6),
        "word_error_rate": round(total_errors / total_words, 6),
        "latency_p50_seconds": round(statistics.median(latencies), 6),
        "latency_p95_seconds": round(nearest_rank(latencies, 0.95), 6),
        "target_p95_pass": nearest_rank(latencies, 0.95) <= 1.5,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--fixtures", type=Path, default=DEFAULT_FIXTURES)
    parser.add_argument("--audio-root", type=Path, required=True)
    parser.add_argument("--cache-dir", type=Path, required=True)
    parser.add_argument("--iterations", type=int, default=3)
    parser.add_argument("--warmups", type=int, default=1)
    parser.add_argument("--cpu-threads", type=int, default=4)
    parser.add_argument("--vad", action="store_true")
    parser.add_argument("--hotwords")
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.iterations < 1 or args.warmups < 0 or args.cpu_threads < 1:
        raise SystemExit("iterations/threads must be positive and warmups cannot be negative")
    fixtures = load_fixtures(args.fixtures)
    transcriber = FasterWhisperTranscriber(
        args.model, args.cache_dir, args.vad, args.hotwords, args.cpu_threads
    )
    samples = run(transcriber, fixtures, args.audio_root, args.warmups, args.iterations)
    result = {
        "schema": 1,
        "engine": "faster-whisper",
        "model": transcriber.name,
        "compute": "cpu-int8",
        "cpu_threads": args.cpu_threads,
        "vad": args.vad,
        "hotwords_enabled": bool(args.hotwords),
        "load_seconds": round(transcriber.load_seconds, 6),
        "summary": summarize(samples),
        "samples": [asdict(sample) for sample in samples],
    }
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
