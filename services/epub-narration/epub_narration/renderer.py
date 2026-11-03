"""Canonical Kokoro chapter rendering with exact sample-index timing."""

from __future__ import annotations

from dataclasses import asdict
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
from typing import Callable

from .epub import Chapter
from .publication import VOICE, sha256_file
from .timing import SentenceCue, SentenceSpan, build_sentence_cues, validate_cues


MODEL_SHA256 = VOICE["model_sha256"]
CLEANUP_SHA256 = "0476a393afd237833835b8e5499f64250bfc5e382a1603b94803cb99e7a350b9"
BENCHMARK_CLEANUP_SHA256 = "8179b2cefc88bfa08591494759b9c09aa7074263e8686d4e8946511657f16720"
SAMPLE_RATE = 24_000
OPUS_RATE = 48_000
BITRATE = "48k"


class RenderFailure(RuntimeError):
    pass


class RenderSuspended(RuntimeError):
    """Cooperative stop requested between bounded narration units."""


def _atomic_private_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=path.parent, prefix=".checkpoint-", delete=False
    ) as handle:
        json.dump(payload, handle, sort_keys=True, separators=(",", ":"))
        handle.flush()
        os.fsync(handle.fileno())
        temporary = Path(handle.name)
    os.chmod(temporary, 0o600)
    os.replace(temporary, path)


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

    @staticmethod
    def _checkpoint_files(staging: Path, stem: str) -> tuple[Path, Path, Path]:
        return (
            staging / "chapters" / f"{stem}.opus",
            staging / "timing" / f"{stem}.json",
            staging / "content" / f"{stem}.json",
        )

    def _resume_chapter(
        self,
        chapter: Chapter,
        cleaned_sha256: str,
        staging: Path,
    ) -> list[dict] | None:
        stem = f"{chapter.index:04d}"
        checkpoint = staging / "checkpoints" / f"{stem}.json"
        if not checkpoint.is_file() or checkpoint.is_symlink():
            return None

    def _adopt_legacy_chapter(
        self,
        chapter: Chapter,
        cleaned: str,
        cleaned_sha256: str,
        staging: Path,
    ) -> list[dict] | None:
        """Validate and checkpoint a complete chapter made by the old worker.

        The pre-resume renderer wrote the three final chapter artifacts before
        moving on, but had no checkpoint file.  Adoption is deliberately strict:
        any mismatch removes the untrusted partial set and causes a fresh render.
        """
        stem = f"{chapter.index:04d}"
        opus_path, timing_path, content_path = self._checkpoint_files(staging, stem)
        expected = (opus_path, timing_path, content_path)
        if not any(path.exists() for path in expected):
            return None
        try:
            if any(path.is_symlink() or not path.is_file() for path in expected):
                raise ValueError("legacy-files")
            content = json.loads(content_path.read_text(encoding="utf-8"))
            if content != {
                "schema": 1,
                "chapter": chapter.index,
                "text": cleaned,
                "text_sha256": cleaned_sha256,
            }:
                raise ValueError("legacy-content")
            timing = json.loads(timing_path.read_text(encoding="utf-8"))
            if (
                timing.get("schema") != 1
                or timing.get("timing_level") != "sentence-sample-index"
                or timing.get("sample_rate") != SAMPLE_RATE
                or timing.get("cleaned_text_sha256") != cleaned_sha256
                or not isinstance(timing.get("cues"), list)
            ):
                raise ValueError("legacy-timing")
            total_samples = timing.get("total_samples")
            cues = tuple(SentenceCue(**item) for item in timing["cues"])
            validate_cues(cues, total_samples)
            for cue in cues:
                spoken = cleaned[cue.source_start:cue.source_end]
                if hashlib.sha256(spoken.encode("utf-8")).hexdigest() != cue.spoken_sha256:
                    raise ValueError("legacy-cue")
            _probe_opus(opus_path, total_samples / SAMPLE_RATE)
            chapter_files = [{
                "path": str(path.relative_to(staging)),
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            } for path in expected]
            _atomic_private_json(staging / "checkpoints" / f"{stem}.json", {
                "schema": 1,
                "chapter": chapter.index,
                "source_text_sha256": chapter.text_sha256,
                "cleaned_text_sha256": cleaned_sha256,
                "files": chapter_files,
            })
            return chapter_files
        except (KeyError, OSError, TypeError, ValueError, json.JSONDecodeError, subprocess.SubprocessError):
            for path in expected:
                path.unlink(missing_ok=True)
            return None
        try:
            payload = json.loads(checkpoint.read_text(encoding="utf-8"))
            expected = self._checkpoint_files(staging, stem)
            files = payload["files"]
            if (
                payload.get("schema") != 1
                or payload.get("chapter") != chapter.index
                or payload.get("source_text_sha256") != chapter.text_sha256
                or payload.get("cleaned_text_sha256") != cleaned_sha256
                or not isinstance(files, list)
                or len(files) != len(expected)
            ):
                raise ValueError("checkpoint-contract")
            records = {item["path"]: item for item in files if isinstance(item, dict)}
            if len(records) != len(expected):
                raise ValueError("checkpoint-files")
            for path in expected:
                relative = str(path.relative_to(staging))
                item = records.get(relative)
                if (
                    item is None
                    or path.is_symlink()
                    or not path.is_file()
                    or path.stat().st_size != item.get("bytes")
                    or sha256_file(path) != item.get("sha256")
                ):
                    raise ValueError("checkpoint-integrity")
            return [records[str(path.relative_to(staging))] for path in expected]
        except (KeyError, OSError, TypeError, ValueError, json.JSONDecodeError):
            checkpoint.unlink(missing_ok=True)
            for path in self._checkpoint_files(staging, stem):
                path.unlink(missing_ok=True)
            return None

    def render(
        self,
        chapters: tuple[Chapter, ...],
        staging: Path,
        should_stop: Callable[[], bool] | None = None,
    ) -> list[dict]:
        try:
            import numpy as np
            import soundfile as sf
        except ImportError as exc:
            raise RenderFailure("voice-contract") from exc

        chapter_root = staging / "chapters"
        timing_root = staging / "timing"
        content_root = staging / "content"
        chapter_root.mkdir(parents=True, exist_ok=True, mode=0o700)
        timing_root.mkdir(parents=True, exist_ok=True, mode=0o700)
        content_root.mkdir(parents=True, exist_ok=True, mode=0o700)
        checkpoint_root = staging / "checkpoints"
        checkpoint_root.mkdir(parents=True, exist_ok=True, mode=0o700)
        for abandoned in staging.glob(".chapter-*"):
            if abandoned.is_dir() and not abandoned.is_symlink():
                shutil.rmtree(abandoned)
        files: list[dict] = []
        for chapter in chapters:
            if should_stop is not None and should_stop():
                raise RenderSuspended("suspended")
            cleaned = self.cleanup.speech_text(chapter.text)
            units = self.cleanup.narration_units(cleaned)
            if not cleaned or not units:
                raise RenderFailure("timing-invalid")
            cleaned_sha256 = hashlib.sha256(cleaned.encode("utf-8")).hexdigest()
            resumed = self._resume_chapter(chapter, cleaned_sha256, staging)
            if resumed is not None:
                files.extend(resumed)
                continue
            adopted = self._adopt_legacy_chapter(
                chapter, cleaned, cleaned_sha256, staging
            )
            if adopted is not None:
                files.extend(adopted)
                continue
            spans: list[SentenceSpan] = []
            lengths: list[int] = []
            pauses: list[int] = []
            search_from = 0
            stem = f"{chapter.index:04d}"
            opus_path = chapter_root / f"{stem}.opus"
            timing_path = timing_root / f"{stem}.json"
            content_path = content_root / f"{stem}.json"
            with tempfile.TemporaryDirectory(prefix=f".chapter-{stem}-", dir=staging) as tmp:
                temporary_root = Path(tmp)
                wave_path = temporary_root / "chapter.wav"
                temporary_opus = temporary_root / "chapter.opus"
                total_samples = 0
                with sf.SoundFile(
                    wave_path, mode="w", samplerate=SAMPLE_RATE, channels=1, subtype="PCM_16"
                ) as wave:
                    for unit_text, pause_seconds in units:
                        if should_stop is not None and should_stop():
                            raise RenderSuspended("suspended")
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
                        wave.write(audio)
                        if pause_samples:
                            wave.write(np.zeros(min(pause_samples, SAMPLE_RATE), dtype=np.float32))
                            remaining = pause_samples - min(pause_samples, SAMPLE_RATE)
                            while remaining:
                                block = min(remaining, SAMPLE_RATE)
                                wave.write(np.zeros(block, dtype=np.float32))
                                remaining -= block
                        total_samples += len(audio) + pause_samples
                        del audio
                cues = build_sentence_cues(tuple(spans), tuple(lengths), tuple(pauses))
                validate_cues(cues, total_samples)
                encoded = subprocess.run(
                    [
                        "ffmpeg", "-v", "error", "-y", "-i", str(wave_path),
                        "-map_metadata", "-1", "-ac", "1", "-c:a", "libopus",
                        "-b:a", BITRATE, "-application", "audio", "-vbr", "on", str(temporary_opus),
                    ],
                    capture_output=True,
                    timeout=600,
                )
                if encoded.returncode != 0:
                    raise RenderFailure("voice-contract")
                _probe_opus(temporary_opus, total_samples / SAMPLE_RATE)
                temporary_timing = temporary_root / "timing.json"
                temporary_timing.write_text(json.dumps({
                    "schema": 1,
                    "timing_level": "sentence-sample-index",
                    "sample_rate": SAMPLE_RATE,
                    "total_samples": total_samples,
                    "cleaned_text_sha256": cleaned_sha256,
                    "cues": [asdict(cue) for cue in cues],
                }, sort_keys=True, separators=(",", ":")), encoding="utf-8")
                temporary_content = temporary_root / "content.json"
                temporary_content.write_text(json.dumps({
                    "schema": 1,
                    "chapter": chapter.index,
                    "text": cleaned,
                    "text_sha256": cleaned_sha256,
                }, ensure_ascii=False, sort_keys=True, separators=(",", ":")), encoding="utf-8")
                for temporary, destination in (
                    (temporary_opus, opus_path),
                    (temporary_timing, timing_path),
                    (temporary_content, content_path),
                ):
                    os.chmod(temporary, 0o600)
                    os.replace(temporary, destination)
            chapter_files = [{
                "path": str(path.relative_to(staging)),
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            } for path in (opus_path, timing_path, content_path)]
            _atomic_private_json(checkpoint_root / f"{stem}.json", {
                "schema": 1,
                "chapter": chapter.index,
                "source_text_sha256": chapter.text_sha256,
                "cleaned_text_sha256": cleaned_sha256,
                "files": chapter_files,
            })
            files.extend(chapter_files)
        return files
