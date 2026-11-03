#!/usr/bin/env python3
"""Render a prepared private EPUB shadow through loopback Kokopop/Vulkan."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import tempfile
import time
import urllib.request


MODEL_SHA256 = "e8242a1321e580599c26981692adf088ebfdc4c7b7555959b13f4d6667d0d206"
BINARY_SHA256 = "57c5f7547277c4c18834512149f33c37da31e4cfea91e154822c9d8453e841b6"
SAMPLE_RATE = 24_000


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
                with audio.open("rb") as handle:
                    wave_header = handle.read(12)
                if (audio.is_file() and not audio.is_symlink() and audio.stat().st_size >= 64
                        and wave_header[:4] == b"RIFF" and wave_header[8:12] == b"WAVE"
                        and prior.get("schema") == 1
                        and prior.get("chapter") == chapter["index"]
                        and prior.get("text_sha256") == chapter["text_sha256"]):
                    for path in (audio, content):
                        files.append({"path": str(path.relative_to(root)),
                                      "bytes": path.stat().st_size, "sha256": _sha(path)})
                    continue
            except (OSError, ValueError, json.JSONDecodeError):
                pass
            audio.unlink(missing_ok=True)
            content.unlink(missing_ok=True)
            before = time.monotonic()
            encoded = _audio(url, chapter["text"], job["voice"], job["speed"], timeout)
            request_seconds = time.monotonic() - before
            _atomic_private(audio, encoded)
            content_payload = json.dumps({
                "schema": 1, "chapter": chapter["index"], "text": chapter["text"],
                "text_sha256": chapter["text_sha256"],
                "renderer_seconds": round(request_seconds, 6),
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
