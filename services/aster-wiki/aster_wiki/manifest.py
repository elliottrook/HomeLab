"""Strict source-manifest validation and atomic candidate persistence."""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

SOURCE_ID = re.compile(r"^[a-z0-9][a-z0-9-]{2,63}$")
KINDS = {"web", "git", "manual"}
CLASSES = {"vendor", "upstream", "community", "local-reviewed"}
MEDIA_TYPES = {"text/html", "text/markdown", "text/plain", "application/pdf"}


class ManifestError(ValueError):
    pass


def canonical_json(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def validate_source(source: dict[str, Any]) -> dict[str, Any]:
    required = {
        "id", "kind", "title", "owner", "canonical_url", "boundary",
        "source_class", "media_type", "version_policy", "refresh_hours",
        "size_limit_bytes", "license_status", "enabled",
    }
    missing = sorted(required - source.keys())
    if missing:
        raise ManifestError("missing fields: " + ", ".join(missing))
    unknown = sorted(source.keys() - required - {"asset_id", "service_id"})
    if unknown:
        raise ManifestError("unknown fields: " + ", ".join(unknown))
    if not SOURCE_ID.fullmatch(str(source["id"])):
        raise ManifestError("invalid source id")
    if source["kind"] not in KINDS or source["source_class"] not in CLASSES:
        raise ManifestError("invalid kind or source class")
    if source["media_type"] not in MEDIA_TYPES:
        raise ManifestError("unsupported media type")
    parsed = urlparse(str(source["canonical_url"]))
    if source["kind"] in {"web", "git"} and (parsed.scheme != "https" or not parsed.hostname):
        raise ManifestError("network sources require an https URL")
    if source["kind"] == "manual" and parsed.scheme != "upload":
        raise ManifestError("manual source must use an upload: URL")
    boundary = source["boundary"]
    if not isinstance(boundary, dict) or set(boundary) != {"type", "value"}:
        raise ManifestError("boundary must contain only type and value")
    allowed_boundaries = {
        "web": {"exact-url", "path-prefix", "sitemap"},
        "git": {"repository-paths"},
        "manual": {"exact-file"},
    }
    if boundary["type"] not in allowed_boundaries[source["kind"]] or not boundary["value"]:
        raise ManifestError("invalid or empty collection boundary")
    for field, minimum, maximum in (
        ("refresh_hours", 24, 24 * 365),
        ("size_limit_bytes", 1, 100 * 1024 * 1024),
    ):
        if not isinstance(source[field], int) or not minimum <= source[field] <= maximum:
            raise ManifestError(f"{field} outside allowed range")
    if source["license_status"] not in {"permitted", "metadata-only", "review-required"}:
        raise ManifestError("invalid license status")
    if not isinstance(source["enabled"], bool):
        raise ManifestError("enabled must be boolean")
    return source


def load_manifest(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1 or not isinstance(data.get("sources"), list):
        raise ManifestError("unsupported manifest")
    ids: set[str] = set()
    for source in data["sources"]:
        validate_source(source)
        if source["id"] in ids:
            raise ManifestError(f"duplicate source id: {source['id']}")
        ids.add(source["id"])
    return data


def write_candidate(state_root: Path, source: dict[str, Any]) -> Path:
    validate_source(source)
    payload = {"schema_version": 1, "operation": "enroll", "source": source}
    encoded = canonical_json(payload)
    digest = hashlib.sha256(encoded).hexdigest()
    target_dir = state_root / "candidates"
    target_dir.mkdir(parents=True, exist_ok=True, mode=0o770)
    os.chmod(target_dir, 0o770)
    target = target_dir / f"{source['id']}-{digest[:12]}.json"
    if target.exists():
        return target
    fd, temporary = tempfile.mkstemp(prefix=".candidate-", dir=str(target_dir))
    try:
        os.fchmod(fd, 0o640)
        with os.fdopen(fd, "wb") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, target)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return target


def write_control_candidate(state_root: Path, source_id: str, operation: str) -> Path:
    if not SOURCE_ID.fullmatch(source_id) or operation not in {"pause", "resume", "retire", "retry"}:
        raise ManifestError("invalid source control request")
    payload = {"schema_version": 1, "operation": operation, "source_id": source_id}
    encoded = canonical_json(payload)
    digest = hashlib.sha256(encoded).hexdigest()
    target_dir = state_root / "candidates"
    target_dir.mkdir(parents=True, exist_ok=True, mode=0o770)
    os.chmod(target_dir, 0o770)
    target = target_dir / f"{source_id}-{operation}-{digest[:12]}.json"
    if not target.exists():
        fd, temporary = tempfile.mkstemp(prefix=".control-", dir=str(target_dir))
        try:
            os.fchmod(fd, 0o640)
            with os.fdopen(fd, "wb") as handle:
                handle.write(encoded); handle.flush(); os.fsync(handle.fileno())
            os.replace(temporary, target)
        finally:
            if os.path.exists(temporary): os.unlink(temporary)
    return target


def write_upload(state_root: Path, source: dict[str, Any], content: bytes) -> Path:
    validate_source(source)
    if source["kind"] != "manual" or not content:
        raise ManifestError("manual upload content required")
    if len(content) > source["size_limit_bytes"]:
        raise ManifestError("manual upload exceeds source limit")
    target_dir = state_root / "uploads" / source["id"]
    target_dir.mkdir(parents=True, exist_ok=True, mode=0o750)
    os.chmod(target_dir, 0o750)
    target = target_dir / Path(source["boundary"]["value"]).name
    fd, temporary = tempfile.mkstemp(prefix=".upload-", dir=str(target_dir))
    try:
        os.fchmod(fd, 0o640)
        with os.fdopen(fd, "wb") as handle:
            handle.write(content); handle.flush(); os.fsync(handle.fileno())
        os.replace(temporary, target)
    finally:
        if os.path.exists(temporary): os.unlink(temporary)
    return target


def promote_candidates(state_root: Path, manifest_path: Path) -> int:
    """Atomically apply validated queue candidates; retain processed records."""
    candidates = state_root / "candidates"
    if not candidates.is_dir():
        return 0
    manifest = load_manifest(manifest_path)
    sources = {item["id"]: item for item in manifest["sources"]}
    pending = sorted(candidates.glob("*.json"))
    for path in pending:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("schema_version") != 1:
            raise ManifestError("unsupported candidate")
        operation = payload.get("operation")
        if operation == "enroll":
            item = validate_source(payload.get("source", {}))
            sources[item["id"]] = item
        elif operation in {"pause", "resume", "retire", "retry"}:
            source_id = payload.get("source_id", "")
            if source_id not in sources:
                raise ManifestError("candidate references unknown source")
            if operation in {"pause", "retire"}:
                sources[source_id]["enabled"] = False
            elif operation == "resume":
                sources[source_id]["enabled"] = True
        else:
            raise ManifestError("invalid candidate operation")
    if not pending:
        return 0
    encoded = canonical_json({"schema_version": 1, "sources": sorted(sources.values(), key=lambda x: x["id"])})
    fd, temporary = tempfile.mkstemp(prefix=".sources-", dir=str(manifest_path.parent))
    try:
        os.fchmod(fd, 0o640)
        with os.fdopen(fd, "wb") as handle:
            handle.write(encoded); handle.flush(); os.fsync(handle.fileno())
        os.replace(temporary, manifest_path)
    finally:
        if os.path.exists(temporary): os.unlink(temporary)
    processed = state_root / "processed-candidates"
    processed.mkdir(parents=True, exist_ok=True, mode=0o750)
    for path in pending:
        os.replace(path, processed / path.name)
    return len(pending)
