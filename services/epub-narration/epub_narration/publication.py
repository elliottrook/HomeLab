"""Validate immutable generations and atomically expose a ready pointer."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import tempfile

from . import MANIFEST_SCHEMA


SHA256 = re.compile(r"^[0-9a-f]{64}$")
VOICE = {
    "engine": "kokoro-onnx",
    "model": "kokoro-v1.0.fp16.onnx",
    "model_sha256": "f3a290d384fbb27966d462905c71a46cef9e5fd00516b40df32a0b4afe77ac96",
    "voice": "bm_daniel",
    "language": "en-gb",
    "speed": 0.95,
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while block := handle.read(1024 * 1024):
            digest.update(block)
    return digest.hexdigest()


def _contained(root: Path, candidate: Path) -> bool:
    try:
        candidate.relative_to(root)
    except ValueError:
        return False
    return True


def validate_generation(staging: Path) -> dict:
    staging = staging.resolve(strict=True)
    manifest_path = staging / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("schema") != MANIFEST_SCHEMA or manifest.get("state") != "ready-candidate":
        raise ValueError("manifest-schema-state")
    contracts = manifest.get("contracts")
    if not isinstance(contracts, dict) or set(contracts) != {"compiler", "parser", "cleanup", "encoder"}:
        raise ValueError("manifest-contracts")
    if not all(isinstance(value, str) and value for value in contracts.values()):
        raise ValueError("manifest-contracts")
    if not isinstance(manifest.get("book_id"), int) or manifest["book_id"] < 1:
        raise ValueError("manifest-book")
    if not SHA256.fullmatch(str(manifest.get("source_sha256", ""))):
        raise ValueError("manifest-source-hash")
    if manifest.get("voice") != VOICE:
        raise ValueError("manifest-voice")
    if manifest.get("timing_level") != "sentence-sample-index":
        raise ValueError("manifest-timing")
    if manifest.get("sample_rate") != 24_000:
        raise ValueError("manifest-sample-rate")
    if manifest.get("codec") != {"name": "opus", "bitrate": 48000, "channels": 1}:
        raise ValueError("manifest-codec")
    files = manifest.get("files")
    if not isinstance(files, list) or not files:
        raise ValueError("manifest-files")
    seen: set[str] = set()
    for item in files:
        if not isinstance(item, dict):
            raise ValueError("manifest-file-record")
        relative = item.get("path")
        if not isinstance(relative, str) or relative in seen:
            raise ValueError("manifest-file-path")
        unresolved = staging / relative
        if unresolved.is_symlink():
            raise ValueError("manifest-file-path")
        path = unresolved.resolve(strict=True)
        if not _contained(staging, path) or not path.is_file():
            raise ValueError("manifest-file-path")
        if path.stat().st_size != item.get("bytes") or sha256_file(path) != item.get("sha256"):
            raise ValueError("manifest-file-integrity")
        seen.add(relative)
    return manifest


def publish_generation(staging: Path, output_root: Path) -> Path:
    """Move a complete generation, then atomically switch its ready pointer."""
    manifest = validate_generation(staging)
    output_root.mkdir(parents=True, exist_ok=True)
    generations = output_root / "generations" / str(manifest["book_id"])
    ready = output_root / "ready"
    generations.mkdir(parents=True, exist_ok=True)
    ready.mkdir(parents=True, exist_ok=True)
    destination = generations / manifest["source_sha256"]
    if destination.exists():
        raise FileExistsError("immutable-generation-exists")
    os.replace(staging, destination)

    pointer = {
        "schema": MANIFEST_SCHEMA,
        "book_id": manifest["book_id"],
        "source_sha256": manifest["source_sha256"],
        "generation": str(destination.relative_to(output_root)),
        "manifest_sha256": sha256_file(destination / "manifest.json"),
    }
    pointer_path = ready / f"{manifest['book_id']}.json"
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=ready, prefix=".ready-", delete=False
    ) as handle:
        json.dump(pointer, handle, sort_keys=True, separators=(",", ":"))
        handle.flush()
        os.fsync(handle.fileno())
        temporary = Path(handle.name)
    os.replace(temporary, pointer_path)
    return pointer_path

