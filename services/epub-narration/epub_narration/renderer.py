"""Canonical Kokoro chapter rendering with exact sample-index timing."""

from __future__ import annotations

from dataclasses import asdict
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile

from .epub import Chapter
from .publication import VOICE, sha256_file
from .timing import SentenceSpan, build_sentence_cues, validate_cues


MODEL_SHA256 = VOICE["model_sha256"]
CLEANUP_SHA256 = "0476a393afd237833835b8e5499f64250bfc5e382a1603b94803cb99e7a350b9"
BENCHMARK_CLEANUP_SHA256 = "8179b2cefc88bfa08591494759b9c09aa7074263e8686d4e8946511657f16720"
SAMPLE_RATE = 24_000
OPUS_RATE = 48_000
BITRATE = "48k"


class RenderFailure(RuntimeError):
    pass


def _load_cleanup(path: Path):
    if sha256_file(path) != CLEANUP_SHA256:
        raise RenderFailure("voice-contract")
    spec = importlib.util.spec_from_file_location("epub_narration_cleanup", path)
    if spec is None or spec.loader is None:
        raise RenderFailure("voice-contract")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not callable(getattr(module, "speech_text", None)) or not callable(
        getattr(module, "narration_units", None)
    ):
        raise RenderFailure("voice-contract")
    return module


def _probe_opus(path: Path, expected_seconds: float) -> None:
    result = subprocess.run(
        [
            "ffprobe", "-v", "error", "-select_streams", "a:0",
            "-show_entries", "stream=codec_name,sample_rate,channels:format=duration",
            "-of", "json", str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )
    detail = json.loads(result.stdout)
    stream = detail["streams"][0]
    duration = float(detail["format"]["duration"])
    if not (
        stream.get("codec_name") == "opus"
        and int(stream["sample_rate"]) == OPUS_RATE
        and int(stream["channels"]) == 1
        and abs(duration - expected_seconds) <= 0.1
    ):
        raise RenderFailure("timing-invalid")


class KokoroChapterRenderer:
    def __init__(self, *, model: Path, voices: Path, cleanup: Path) -> None:
        if sha256_file(model) != MODEL_SHA256:
            raise RenderFailure("voice-contract")
        self.cleanup = _load_cleanup(cleanup)
        try:
            from kokoro_onnx import Kokoro
        except ImportError as exc:
            raise RenderFailure("voice-contract") from exc
        self.engine = Kokoro(str(model), str(voices))

    def close(self) -> None:
        self.engine.voices.close()

    def render(self, chapters: tuple[Chapter, ...], staging: Path) -> list[dict]:
        try:
            import numpy as np
            import soundfile as sf
        except ImportError as exc:
            raise RenderFailure("voice-contract") from exc

        chapter_root = staging / "chapters"
        timing_root = staging / "timing"
        chapter_root.mkdir(parents=True, mode=0o700)
        timing_root.mkdir(parents=True, mode=0o700)
        files: list[dict] = []
        for chapter in chapters:
            cleaned = self.cleanup.speech_text(chapter.text)
            units = self.cleanup.narration_units(cleaned)
            if not cleaned or not units:
                raise RenderFailure("timing-invalid")
            rendered = []
            spans: list[SentenceSpan] = []
            lengths: list[int] = []
            pauses: list[int] = []
            search_from = 0
            for unit_text, pause_seconds in units:
                source_start = cleaned.find(unit_text, search_from)
                if source_start < 0:
                    raise RenderFailure("timing-invalid")
                source_end = source_start + len(unit_text)
                search_from = source_end
                audio, sample_rate = self.engine.create(
                    unit_text,
                    voice=VOICE["voice"],
                    speed=VOICE["speed"],
                    lang=VOICE["language"],
                )
                audio = np.asarray(audio, dtype=np.float32).reshape(-1)
                if sample_rate != SAMPLE_RATE or len(audio) < 1 or not np.isfinite(audio).all():
                    raise RenderFailure("voice-contract")
                pause_samples = round(float(pause_seconds) * SAMPLE_RATE)
                spans.append(SentenceSpan(source_start, source_end, unit_text))
                lengths.append(len(audio))
                pauses.append(pause_samples)
                rendered.append(audio)
                if pause_samples:
                    rendered.append(np.zeros(pause_samples, dtype=np.float32))
            waveform = np.concatenate(rendered)
            cues = build_sentence_cues(tuple(spans), tuple(lengths), tuple(pauses))
            validate_cues(cues, len(waveform))

            stem = f"{chapter.index:04d}"
            opus_path = chapter_root / f"{stem}.opus"
            with tempfile.NamedTemporaryFile(suffix=".wav", dir=staging) as wave:
                sf.write(wave.name, waveform, SAMPLE_RATE, subtype="PCM_16")
                encoded = subprocess.run(
                    [
                        "ffmpeg", "-v", "error", "-y", "-i", wave.name,
                        "-map_metadata", "-1", "-ac", "1", "-c:a", "libopus",
                        "-b:a", BITRATE, "-application", "audio", "-vbr", "on",
                        str(opus_path),
                    ],
                    capture_output=True,
                    timeout=600,
                )
            if encoded.returncode != 0:
                raise RenderFailure("voice-contract")
            _probe_opus(opus_path, len(waveform) / SAMPLE_RATE)

            timing_path = timing_root / f"{stem}.json"
            timing_path.write_text(
                json.dumps(
                    {
                        "schema": 1,
                        "timing_level": "sentence-sample-index",
                        "sample_rate": SAMPLE_RATE,
                        "total_samples": len(waveform),
                        "cleaned_text_sha256": hashlib.sha256(cleaned.encode("utf-8")).hexdigest(),
                        "cues": [asdict(cue) for cue in cues],
                    },
                    sort_keys=True,
                    separators=(",", ":"),
                ),
                encoding="utf-8",
            )
            for path in (opus_path, timing_path):
                os.chmod(path, 0o600)
                files.append({
                    "path": str(path.relative_to(staging)),
                    "bytes": path.stat().st_size,
                    "sha256": sha256_file(path),
                })
        return files
