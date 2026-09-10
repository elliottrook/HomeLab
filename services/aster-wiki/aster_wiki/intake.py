"""Non-mutating intake discovery and acceptance-preview construction."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from .manifest import ManifestError, validate_source


def slug(value: str) -> str:
    result = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return (result or "source")[:64]


def preview(form: dict[str, str], upload: bytes | None = None) -> dict[str, Any]:
    kind = form.get("kind", "")
    title = form.get("title", "").strip()
    location = form.get("location", "").strip()
    if kind not in {"web", "git", "manual"} or not title:
        raise ManifestError("kind and title are required")
    if kind == "manual":
        if upload is None or not upload:
            raise ManifestError("manual upload is empty")
        location = "upload:" + slug(form.get("filename", title))
        sample = upload[:500].decode("utf-8", errors="replace")
        final_host = "local-upload"
        content_hash = hashlib.sha256(upload).hexdigest()
    else:
        parsed = urlparse(location)
        if parsed.scheme != "https" or not parsed.hostname:
            raise ManifestError("URL must use https")
        sample = "Discovery is metadata-only in the prototype; collection occurs after acceptance."
        final_host = parsed.hostname.lower()
        content_hash = None
    boundary_type = form.get("boundary_type") or {
        "web": "exact-url", "git": "repository-paths", "manual": "exact-file"
    }[kind]
    boundary_value = form.get("boundary", "").strip() or location
    source = {
        "id": slug(form.get("source_id", "") or title),
        "kind": kind,
        "title": title,
        "owner": form.get("owner", "unknown").strip() or "unknown",
        "canonical_url": location,
        "boundary": {"type": boundary_type, "value": boundary_value},
        "source_class": form.get("source_class", "vendor"),
        "media_type": form.get("media_type", "application/pdf" if kind == "manual" else "text/html"),
        "version_policy": form.get("version_policy", "pinned"),
        "refresh_hours": int(form.get("refresh_hours", "24")),
        "size_limit_bytes": int(form.get("size_limit_bytes", str(10 * 1024 * 1024))),
        "license_status": form.get("license_status", "review-required"),
        "enabled": True,
    }
    validate_source(source)
    warnings = []
    if source["license_status"] == "review-required":
        warnings.append("License requires review; collection will quarantine instead of publish.")
    return {
        "source": source,
        "resolved_host": final_host,
        "sample": sample,
        "uploaded_sha256": content_hash,
        "mirror_entry_types": ["component", "dependencies", "symptoms", "recovery"],
        "warnings": warnings,
        "mutated": False,
    }
