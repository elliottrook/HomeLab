#!/usr/bin/env python3
"""Render a prepared private EPUB shadow through loopback Kokopop/Vulkan."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import tempfile
import time
from typing import Union
import urllib.request
import wave


MODEL_SHA256 = "e8242a1321e580599c26981692adf088ebfdc4c7b7555959b13f4d6667d0d206"
BINARY_SHA256 = "57c5f7547277c4c18834512149f33c37da31e4cfea91e154822c9d8453e841b6"
SAMPLE_RATE = 24_000
PACING_MINIMUM_WORDS = 50
PACING_MINIMUM_WPM = 120.0
PACING_MAXIMUM_WPM = 240.0


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while block := handle.read(1024 * 1024):
            digest.update(block)
    return digest.hexdigest()


def _atomic_private(path: Path, value: bytes) -> None:
    with tempfile.NamedTemporaryFile("wb", dir=path.parent, delete=False) as handle:
        handle.write(value)
        handle.flush()
        os.fsync(handle.fileno())
        temporary = Path(handle.name)
    os.chmod(temporary, 0o600)
    os.replace(temporary, path)


def _audio(url: str, text: str, voice: str, speed: float, timeout: int) -> bytes:
    body = json.dumps({"text": text, "voice": voice, "speed": speed,
                       "mode": "long_form", "format": "wav"}).encode()
    request = urllib.request.Request(url, data=body,
                                     headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(request, timeout=timeout) as response:
        value = response.read()
    if len(value) < 64 or not value.startswith(b"RIFF") or value[8:12] != b"WAVE":
        raise ValueError("pilot-wav-shape")
    return value


def _pacing(source: Union[Path, bytes], text: str) -> dict:
    stream = io.BytesIO(source) if isinstance(source, bytes) else source
    with wave.open(str(stream) if isinstance(stream, Path) else stream, "rb") as audio:
        if (audio.getnchannels() != 1 or audio.getsampwidth() != 2
                or audio.getframerate() != SAMPLE_RATE or audio.getcomptype() != "NONE"
                or audio.getnframes() <= 0):
            raise ValueError("pilot-wav-contract")
        seconds = audio.getnframes() / SAMPLE_RATE
    words = len(text.split())
    words_per_minute = words * 60.0 / seconds
    state = "insufficient-words"
    if words >= PACING_MINIMUM_WORDS:
        if not PACING_MINIMUM_WPM <= words_per_minute <= PACING_MAXIMUM_WPM:
            raise ValueError("pilot-pacing")
        state = "accepted"
    return {
        "state": state,
        "words": words,
        "audio_seconds": round(seconds, 6),
        "words_per_minute": round(words_per_minute, 6),
    }


def run(job_path: Path, output_root: Path, url: str, timeout: int) -> dict:
    job = json.loads(job_path.read_text(encoding="utf-8"))
    if (job.get("schema") != 1 or job.get("sample_rate") != SAMPLE_RATE
            or job.get("voice") != "bm_daniel" or job.get("speed") != 0.95):
        raise ValueError("pilot-job-contract")
    root = output_root / job["pilot_id"]
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    if (root / "manifest.json").exists():
        raise FileExistsError("pilot-output-complete")
    (root / "FAILED").unlink(missing_ok=True)
    files = []
    pacing_records = []
    started = time.monotonic()
    try:
        for chapter in job["chapters"]:
            stem = f"{chapter['index']:04d}"
            chapter_root = root / "chapters"
            content_root = root / "content"
            for directory in (chapter_root, content_root):
                directory.mkdir(exist_ok=True, mode=0o700)
            audio = chapter_root / f"{stem}.wav"
            content = content_root / f"{stem}.json"
            try:
                prior = json.loads(content.read_text(encoding="utf-8"))
                if (not audio.is_file() or audio.is_symlink()
                        or audio.stat().st_size < 64):
                    raise ValueError("pilot-wav-file")
                pacing = _pacing(audio, chapter["text"])
                if (prior.get("schema") == 1
                        and prior.get("chapter") == chapter["index"]
                        and prior.get("text_sha256") == chapter["text_sha256"]
                        and prior.get("pacing") == pacing):
                    pacing_records.append(pacing)
                    for path in (audio, content):
                        files.append({"path": str(path.relative_to(root)),
                                      "bytes": path.stat().st_size, "sha256": _sha(path)})
                    continue
            except (EOFError, OSError, ValueError, json.JSONDecodeError, wave.Error):
                pass
            audio.unlink(missing_ok=True)
            content.unlink(missing_ok=True)
            before = time.monotonic()
            encoded = _audio(url, chapter["text"], job["voice"], job["speed"], timeout)
            request_seconds = time.monotonic() - before
            pacing = _pacing(encoded, chapter["text"])
            pacing_records.append(pacing)
            _atomic_private(audio, encoded)
            content_payload = json.dumps({
                "schema": 1, "chapter": chapter["index"], "text": chapter["text"],
                "text_sha256": chapter["text_sha256"],
                "renderer_seconds": round(request_seconds, 6),
                "pacing": pacing,
            }, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
            _atomic_private(content, content_payload)
            for path in (audio, content):
                files.append({"path": str(path.relative_to(root)), "bytes": path.stat().st_size,
                              "sha256": _sha(path)})
        manifest = {
            "schema": 1, "state": "shadow-candidate", "pilot_id": job["pilot_id"],
            "book_id": job["book_id"], "source_sha256": job["source_sha256"],
            "voice": {"engine": "kokopop-vulkan", "model": "kokoro-v1_0.gguf",
                      "model_sha256": MODEL_SHA256, "binary_sha256": BINARY_SHA256,
                      "voice": job["voice"], "speed": job["speed"]},
            "sample_rate": SAMPLE_RATE, "files": files,
            "pacing": {
                "minimum_words": PACING_MINIMUM_WORDS,
                "minimum_wpm": PACING_MINIMUM_WPM,
                "maximum_wpm": PACING_MAXIMUM_WPM,
                "words": sum(item["words"] for item in pacing_records),
                "audio_seconds": round(sum(item["audio_seconds"] for item in pacing_records), 6),
                "words_per_minute": round(
                    sum(item["words"] for item in pacing_records) * 60.0
                    / sum(item["audio_seconds"] for item in pacing_records), 6
                ),
            },
            "wall_seconds": round(time.monotonic() - started, 6),
        }
        manifest_path = root / "manifest.json"
        _atomic_private(manifest_path, json.dumps(
            manifest, sort_keys=True, separators=(",", ":")
        ).encode("utf-8"))
        return {"state": "rendered", "chapters": len(job["chapters"]),
                "wall_seconds": manifest["wall_seconds"], "manifest_sha256": _sha(manifest_path)}
    except BaseException:
        (root / "FAILED").touch(mode=0o600, exist_ok=True)
        raise


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--job", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--url", default="http://127.0.0.1:18131/tts")
    parser.add_argument("--timeout", type=int, default=3600)
    args = parser.parse_args()
    print(json.dumps(run(args.job, args.output_root, args.url, args.timeout), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
