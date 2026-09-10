"""Allowlisted, fail-closed acquisition and atomic corpus acceptance."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
import time
import urllib.request
from urllib.error import HTTPError
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
RUN_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,95}$")
MINIMUM_HOST_INTERVAL_SECONDS = 2.0


class Quarantine(ValueError):
    pass


@dataclass(frozen=True)
class Fetched:
    body: bytes
    media_type: str
    final_url: str
    etag: str | None = None
    last_modified: str | None = None
    not_modified: bool = False


def fetch_https(source: dict, timeout: int = 30, etag: str | None = None,
                last_modified: str | None = None) -> Fetched:
    headers = {"User-Agent": "HomeLabWikiCollector/1"}
    if etag:
        headers["If-None-Match"] = etag
    if last_modified:
        headers["If-Modified-Since"] = last_modified
    request = urllib.request.Request(source["canonical_url"], headers=headers)
    try:
        response = urllib.request.urlopen(request, timeout=timeout)
    except HTTPError as exc:
        if exc.code == 304:
            return Fetched(b"", source["media_type"], source["canonical_url"],
                           etag, last_modified, True)
        raise
    with response:
        limit = source["size_limit_bytes"]
        body = response.read(limit + 1)
        return Fetched(body, response.headers.get_content_type(), response.geturl(),
                       response.headers.get("ETag"), response.headers.get("Last-Modified"))


def _git_paths(value: str) -> list[str]:
    paths = [item.strip().lstrip("/") for item in value.split(",") if item.strip()]
    if not paths or any(".." in Path(item).parts or item.startswith("-") for item in paths):
        raise Quarantine("invalid-repository-path-boundary")
    return paths


def fetch_git(source: dict) -> Fetched:
    allowed = _git_paths(source["boundary"]["value"])
    with tempfile.TemporaryDirectory() as directory:
        repository = Path(directory) / "repo.git"
        subprocess.run(
            ["git", "clone", "--bare", "--filter=blob:none", "--depth", "1", "--no-tags",
             "--", source["canonical_url"], str(repository)],
            check=True, capture_output=True, timeout=60,
            env={"PATH": os.environ.get("PATH", ""), "GIT_TERMINAL_PROMPT": "0"},
        )
        listing = subprocess.run(
            ["git", "--git-dir", str(repository), "ls-tree", "-r", "--name-only", "HEAD"],
            check=True, capture_output=True, text=True, timeout=15,
        ).stdout.splitlines()
        selected = sorted(path for path in listing if any(path == item or path.startswith(item.rstrip("/") + "/") for item in allowed))
        selected = [path for path in selected if Path(path).suffix.lower() in {".md", ".txt", ".html"}]
        if not selected or len(selected) > 256:
            raise Quarantine("repository-path-selection-empty-or-too-large")
        chunks = []
        total = 0
        for path in selected:
            data = subprocess.run(
                ["git", "--git-dir", str(repository), "show", f"HEAD:{path}"],
                check=True, capture_output=True, timeout=15,
            ).stdout
            total += len(data)
            if total > source["size_limit_bytes"]:
                raise Quarantine("size-limit-exceeded")
            chunks.append(f"\n\n<!-- source-file: {path} -->\n".encode() + data)
        commit = subprocess.run(
            ["git", "--git-dir", str(repository), "rev-parse", "HEAD"],
            check=True, capture_output=True, text=True, timeout=15,
        ).stdout.strip()
        return Fetched(b"".join(chunks).lstrip(), source["media_type"], source["canonical_url"], etag=commit)


def fetch_manual(source: dict, upload_root: Path) -> Fetched:
    filename = Path(source["boundary"]["value"])
    if filename.name != str(filename) or filename.name.startswith("."):
        raise Quarantine("invalid-upload-name")
    path = upload_root / source["id"] / filename.name
    if not path.is_file() or path.is_symlink():
        raise Quarantine("protected-upload-missing")
    with path.open("rb") as handle:
        body = handle.read(source["size_limit_bytes"] + 1)
    return Fetched(body, source["media_type"], source["canonical_url"])


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
    def __init__(self, wiki_root: Path, state_root: Path, fetcher: Callable[[dict], Fetched] | None = None):
        self.wiki_root = wiki_root
        self.state_root = state_root
        self.fetcher = fetcher or self._fetch
        self.state = State(state_root / "pipeline.sqlite3")

    def _fetch(self, source: dict) -> Fetched:
        if source["kind"] == "git":
            return fetch_git(source)
        if source["kind"] == "manual":
            return fetch_manual(source, self.state_root / "uploads")
        hostname = urlparse(source["canonical_url"]).hostname
        if not hostname:
            raise Quarantine("network-source-hostname-missing")
        delay = self.state.host_delay(hostname, time.time(), MINIMUM_HOST_INTERVAL_SECONDS)
        if delay:
            time.sleep(delay)
        self.state.record_host_request(hostname, time.time())
        etag, last_modified = self.state.validators(source["id"])
        return fetch_https(source, etag=etag, last_modified=last_modified)

    def _accepted_entry(self, source_id: str) -> dict | None:
        lock = self.wiki_root / "sources/accepted-lock.json"
        if not lock.is_file():
            return None
        data = json.loads(lock.read_text(encoding="utf-8"))
        return next((item for item in data.get("sources", [])
                     if item.get("source_id") == source_id), None)

    def run(self, sources: list[dict], run_id: str) -> dict[str, int | str]:
        if not RUN_ID.fullmatch(run_id):
            raise ValueError("invalid run id")
        self.state.start(run_id)
        stage = self.wiki_root / "docs/.aster-wiki-runs" / run_id
        stage.mkdir(parents=True, exist_ok=True)
        accepted = []
        for source in sources:
            try:
                validate_source(source)
                fetched = self.fetcher(source)
                self.state.checkpoint(run_id, source["id"], "fetched", "ok")
                if fetched.not_modified:
                    prior = self._accepted_entry(source["id"])
                    if prior is None:
                        raise Quarantine("not-modified-without-accepted-input")
                    prior_path = self.wiki_root / prior["path"]
                    if (not prior_path.is_file() or
                            hashlib.sha256(prior_path.read_bytes()).hexdigest() != prior["normalized_sha256"]):
                        raise Quarantine("not-modified-accepted-input-mismatch")
                    staged_prior = stage / prior["path"]
                    staged_prior.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(prior_path, staged_prior)
                    provenance = prior_path.parent / "provenance.json"
                    if provenance.is_file():
                        shutil.copyfile(provenance, staged_prior.parent / "provenance.json")
                    self.state.checkpoint(run_id, source["id"], "verified", "unchanged",
                                          prior["original_sha256"])
                    accepted.append(prior)
                    continue
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
                if source["kind"] == "web":
                    self.state.save_validators(source["id"], fetched.etag, fetched.last_modified)
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
        backup = self.wiki_root / "docs/.aster-wiki-last-good"
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
        backup = self.wiki_root / "docs/.aster-wiki-last-good"
        if not backup.is_dir():
            raise RuntimeError("no last-good corpus retained")
        failed = self.wiki_root / f"docs/.aster-wiki-rolled-back-{int(time.time())}"
        if generated.exists():
            os.replace(generated, failed)
        os.replace(backup, generated)
