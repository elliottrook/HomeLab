"""Allowlisted, fail-closed acquisition and atomic corpus acceptance."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import tempfile
import time
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Callable
from urllib.parse import urlparse

from .manifest import canonical_json, validate_source
from .state import State

SECRET = re.compile(rb"(?im)^\s*(?:api[_-]?key|password|passwd|secret|token)\s*[:=]\s*\S{8,}")
INJECTION = re.compile(rb"(?i)(ignore (?:all |any )?(?:previous|prior) instructions|system prompt|call (?:a )?tool|exfiltrat)")
EXECUTABLE_MAGIC = (b"MZ", b"\x7fELF", b"#!")
SAFE_TYPES = {"text/html", "text/markdown", "text/plain", "application/pdf"}


class Quarantine(ValueError):
    pass


@dataclass(frozen=True)
class Fetched:
    body: bytes
    media_type: str
    final_url: str
    etag: str | None = None
    last_modified: str | None = None


def fetch_https(source: dict, timeout: int = 30) -> Fetched:
    request = urllib.request.Request(source["canonical_url"], headers={"User-Agent": "HomeLabWikiCollector/1"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        limit = source["size_limit_bytes"]
        body = response.read(limit + 1)
        return Fetched(body, response.headers.get_content_type(), response.geturl(),
                       response.headers.get("ETag"), response.headers.get("Last-Modified"))


def validate_fetch(source: dict, fetched: Fetched) -> None:
    if len(fetched.body) > source["size_limit_bytes"]:
        raise Quarantine("size-limit-exceeded")
    if fetched.media_type not in SAFE_TYPES or fetched.media_type != source["media_type"]:
        raise Quarantine("media-type-not-allowed")
    expected = urlparse(source["canonical_url"])
    final = urlparse(fetched.final_url)
    if source["kind"] != "manual" and (final.scheme != "https" or final.hostname != expected.hostname):
        raise Quarantine("redirect-outside-allowlisted-host")
    if fetched.body.startswith(EXECUTABLE_MAGIC) or b"\x00" in fetched.body[:4096]:
        if fetched.media_type != "application/pdf" or not fetched.body.startswith(b"%PDF-"):
            raise Quarantine("unsafe-active-or-binary-content")
    if SECRET.search(fetched.body):
        raise Quarantine("secret-pattern-detected")
    if INJECTION.search(fetched.body):
        raise Quarantine("prompt-injection-pattern-detected")
    if source["license_status"] == "review-required":
        raise Quarantine("license-review-required")


def normalize(fetched: Fetched) -> bytes:
    if fetched.media_type == "application/pdf":
        return fetched.body
    text = fetched.body.decode("utf-8", errors="strict").replace("\r\n", "\n").replace("\r", "\n")
    return ("\n".join(line.rstrip() for line in text.splitlines()).strip() + "\n").encode("utf-8")


class Collector:
    def __init__(self, wiki_root: Path, state_root: Path, fetcher: Callable[[dict], Fetched] = fetch_https):
        self.wiki_root = wiki_root
        self.state_root = state_root
        self.fetcher = fetcher
        self.state = State(state_root / "pipeline.sqlite3")

    def run(self, sources: list[dict], run_id: str) -> dict[str, int | str]:
        self.state.start(run_id)
        stage = self.state_root / "runs" / run_id
        stage.mkdir(parents=True, exist_ok=True)
        accepted = []
        for source in sources:
            try:
                validate_source(source)
                fetched = self.fetcher(source)
                self.state.checkpoint(run_id, source["id"], "fetched", "ok")
                validate_fetch(source, fetched)
                digest = hashlib.sha256(fetched.body).hexdigest()
                data = normalize(fetched)
                normalized_digest = hashlib.sha256(data).hexdigest()
                destination = Path("docs/upstream") / source["id"] / ("original.pdf" if fetched.media_type == "application/pdf" else "content.txt")
                if not str(destination).startswith("docs/upstream/"):
                    raise Quarantine("destination-outside-generated-tree")
                output = stage / destination
                output.parent.mkdir(parents=True, exist_ok=True)
                output.write_bytes(data)
                metadata = {
                    "schema_version": 1, "source_id": source["id"],
                    "canonical_url": source["canonical_url"], "final_url": fetched.final_url,
                    "original_sha256": digest, "normalized_sha256": normalized_digest,
                    "media_type": fetched.media_type, "etag": fetched.etag,
                    "last_modified": fetched.last_modified, "authority": "upstream-reference",
                }
                (output.parent / "provenance.json").write_bytes(canonical_json(metadata))
                self.state.checkpoint(run_id, source["id"], "normalized", "ok", digest)
                accepted.append({**metadata, "path": str(destination)})
            except Quarantine as exc:
                self.state.checkpoint(run_id, source.get("id", "invalid"), "validation", "quarantined", reason=str(exc))
            except Exception as exc:
                self.state.checkpoint(run_id, source.get("id", "invalid"), "fetch", "failed",
                                      reason=type(exc).__name__)
        summary = self.state.summary(run_id)
        if summary["quarantined"] or summary["failed"]:
            self.state.finish(run_id, "failed")
            self._write_report(run_id, summary)
            return summary
        candidate = {"schema_version": 1, "run_id": run_id, "sources": sorted(accepted, key=lambda x: x["source_id"])}
        (stage / "accepted-lock.json").write_bytes(canonical_json(candidate))
        self._atomic_publish(stage)
        self.state.finish(run_id, "accepted")
        self._write_report(run_id, summary)
        return summary

    def _atomic_publish(self, stage: Path) -> None:
        generated = self.wiki_root / "docs/upstream"
        lock = self.wiki_root / "sources/accepted-lock.json"
        generated.parent.mkdir(parents=True, exist_ok=True)
        lock.parent.mkdir(parents=True, exist_ok=True)
        incoming = stage / "docs/upstream"
        backup = self.state_root / "last-good-upstream"
        if backup.exists():
            shutil.rmtree(backup)
        if generated.exists():
            os.replace(generated, backup)
        os.replace(incoming, generated)
        fd, temporary = tempfile.mkstemp(prefix=".accepted-lock-", dir=str(lock.parent))
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write((stage / "accepted-lock.json").read_bytes())
                handle.flush(); os.fsync(handle.fileno())
            os.replace(temporary, lock)
        finally:
            if os.path.exists(temporary): os.unlink(temporary)

    def _write_report(self, run_id: str, summary: dict) -> None:
        reports = self.state_root / "reports"
        reports.mkdir(parents=True, exist_ok=True)
        (reports / f"{run_id}.json").write_bytes(canonical_json({"schema_version": 1, **summary}))

    def verify(self) -> dict[str, int | str]:
        lock = self.wiki_root / "sources/accepted-lock.json"
        if not lock.is_file():
            raise RuntimeError("accepted lock missing")
        data = json.loads(lock.read_text(encoding="utf-8"))
        checked = 0
        for item in data.get("sources", []):
            path = self.wiki_root / item["path"]
            if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != item["normalized_sha256"]:
                raise RuntimeError(f"accepted content mismatch: {item['source_id']}")
            checked += 1
        return {"status": "ok", "checked": checked}

    def rollback(self) -> None:
        generated = self.wiki_root / "docs/upstream"
        backup = self.state_root / "last-good-upstream"
        if not backup.is_dir():
            raise RuntimeError("no last-good corpus retained")
        failed = self.state_root / f"rolled-back-{int(time.time())}"
        if generated.exists():
            os.replace(generated, failed)
        os.replace(backup, generated)
