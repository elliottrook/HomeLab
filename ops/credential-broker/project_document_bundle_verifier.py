#!/usr/bin/env python3
"""Offline verifier for the narrow Forgejo project-document package.

This is a separate M1 capability from the existing one-file canary.  It reads
only a complete immutable package directory and returns the exact bounded
document payloads that a later, separately approved gateway could consume.
It performs no network, Git, Forgejo, OpenBao, broker or package-controlled
code execution.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import time
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Callable, Mapping

from mcp_policy_adapter import ProjectDocumentWritePolicyAdapter


SHA256 = re.compile(r"^[0-9a-f]{64}$")
GIT_SHA = re.compile(r"^[0-9a-f]{40}$")
NONCE = re.compile(r"^[A-Za-z0-9_-]{22,128}$")
BRANCH = re.compile(r"^ai-pam/[a-z0-9][a-z0-9._-]{0,62}$")
SIGNER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9@._-]{0,127}$")

EXPECTED_KEYS = frozenset({
    "version", "repository", "base_revision", "target_branch", "nonce",
    "issued_at", "expires_at", "policy_digest", "signer", "action",
})
ACTION_KEYS = frozenset({"files", "commit_message"})
FILE_KEYS = frozenset({"path", "content_sha256", "content_size"})
ALLOWED_ROOT_ENTRIES = frozenset({"manifest.json", "manifest.sig", "files"})
ALLOWED_SUFFIXES = frozenset({".md", ".markdown", ".txt"})

MAX_MANIFEST_BYTES = 256 * 1024
MAX_SIGNATURE_BYTES = 64 * 1024
MAX_FILES = 32
MAX_FILE_BYTES = 1024 * 1024
MAX_TOTAL_BYTES = 8 * 1024 * 1024
MAX_COMMIT_MESSAGE_BYTES = 160


class Denied(ValueError):
    """A fail-closed package rejection."""


def canonical_json(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _safe_relative(raw: object) -> PurePosixPath:
    if not isinstance(raw, str) or not raw or "\x00" in raw or "\\" in raw:
        raise Denied("document path is malformed")
    path = PurePosixPath(raw)
    if path.is_absolute() or ".." in path.parts or str(path) != raw:
        raise Denied("document path is not normalized")
    if any(not part or part.startswith(".") for part in path.parts):
        raise Denied("hidden document path is prohibited")
    if path.suffix.lower() not in ALLOWED_SUFFIXES:
        raise Denied("document type is not allowlisted")
    if not (raw.startswith("docs/projects/") or raw.startswith("docs/handovers/")):
        raise Denied("document path is outside the project allowlist")
    return path


def _lstat_regular(root: Path, relative: PurePosixPath, *, max_bytes: int) -> bytes:
    """Read a regular file after checking every path component for symlinks."""
    current = root
    for component in relative.parts:
        current = current / component
        try:
            info = current.lstat()
        except OSError as exc:
            raise Denied("package file is unavailable") from exc
        if stat.S_ISLNK(info.st_mode):
            raise Denied("package symlinks are prohibited")
        if component != relative.name and not stat.S_ISDIR(info.st_mode):
            raise Denied("package path component is not a directory")
    if not stat.S_ISREG(info.st_mode) or info.st_size > max_bytes:
        raise Denied("package file is not a bounded regular file")
    try:
        with current.open("rb") as handle:
            data = handle.read(max_bytes + 1)
    except OSError as exc:
        raise Denied("package file cannot be read") from exc
    if len(data) > max_bytes:
        raise Denied("package file is oversized")
    return data


def _private_detail(text: str) -> bool:
    return ProjectDocumentWritePolicyAdapter._private_detail(text)


def _ensure_package_tree(root: Path, expected: set[PurePosixPath]) -> None:
    try:
        root_info = root.lstat()
    except OSError as exc:
        raise Denied("package directory is unavailable") from exc
    if not stat.S_ISDIR(root_info.st_mode) or stat.S_ISLNK(root_info.st_mode):
        raise Denied("package root is not a directory")
    try:
        entries = {entry.name for entry in os.scandir(root)}
    except OSError as exc:
        raise Denied("package directory cannot be listed") from exc
    if entries != ALLOWED_ROOT_ENTRIES:
        raise Denied("package contains unexpected root entries")
    try:
        files_info = (root / "files").lstat()
    except OSError as exc:
        raise Denied("package files directory is unavailable") from exc
    if stat.S_ISLNK(files_info.st_mode) or not stat.S_ISDIR(files_info.st_mode):
        raise Denied("package files entry is not a directory")

    expected_tree: set[PurePosixPath] = {PurePosixPath("files")}
    for path in expected:
        current = PurePosixPath("files")
        for part in path.parts:
            current /= part
            expected_tree.add(current)

    def visit(directory: Path, relative: PurePosixPath) -> None:
        try:
            children = list(os.scandir(directory))
        except OSError as exc:
            raise Denied("package tree cannot be listed") from exc
        for entry in children:
            entry_relative = relative / entry.name
            if entry_relative not in expected_tree:
                raise Denied("package contains an unexpected file or directory")
            try:
                info = entry.stat(follow_symlinks=False)
            except OSError as exc:
                raise Denied("package tree entry cannot be inspected") from exc
            if stat.S_ISLNK(info.st_mode):
                raise Denied("package symlinks are prohibited")
            if stat.S_ISDIR(info.st_mode):
                visit(Path(entry.path), entry_relative)
            elif not stat.S_ISREG(info.st_mode):
                raise Denied("package contains a non-regular file")

    visit(root / "files", PurePosixPath("files"))


@dataclass(frozen=True)
class VerifiedDocument:
    path: str
    content: str
    content_sha256: str
    content_size: int


@dataclass(frozen=True)
class VerifiedDocumentBundle:
    request_digest: str
    signer: str
    repository: str
    base_revision: str
    target_branch: str
    nonce: str
    expires_at: int
    policy_digest: str
    commit_message: str
    documents: tuple[VerifiedDocument, ...]


def verify_document_bundle(
    bundle_dir: Path,
    *,
    current_base_revision: str,
    policy_digest: str,
    verify_signature: Callable[[bytes, bytes, str], bool],
    now: int | None = None,
    repository: str = "jason/homelab",
    max_lifetime: int = 900,
) -> VerifiedDocumentBundle:
    """Verify a complete project-document package without external I/O."""
    now = int(time.time()) if now is None else now
    try:
        bundle_info = bundle_dir.lstat()
    except OSError as exc:
        raise Denied("package directory is unavailable") from exc
    if stat.S_ISLNK(bundle_info.st_mode) or not stat.S_ISDIR(bundle_info.st_mode):
        raise Denied("package root is not a directory")
    root = bundle_dir.resolve(strict=True)
    manifest_raw = _lstat_regular(root, PurePosixPath("manifest.json"), max_bytes=MAX_MANIFEST_BYTES)
    signature = _lstat_regular(root, PurePosixPath("manifest.sig"), max_bytes=MAX_SIGNATURE_BYTES)
    try:
        request = json.loads(manifest_raw.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise Denied("manifest is invalid") from exc
    if not isinstance(request, dict) or frozenset(request) != EXPECTED_KEYS:
        raise Denied("manifest schema mismatch")
    body = canonical_json(request)
    signer = request["signer"]
    if not isinstance(signer, str) or not SIGNER.fullmatch(signer):
        raise Denied("signer principal is invalid")
    if not verify_signature(body, signature, signer):
        raise Denied("manifest signature or signer is invalid")
    if request["version"] != 1 or request["repository"] != repository:
        raise Denied("manifest version or repository is not allowed")
    base = request["base_revision"]
    if not isinstance(base, str) or not GIT_SHA.fullmatch(base) or base != current_base_revision:
        raise Denied("canonical base revision changed or is invalid")
    branch = request["target_branch"]
    if not isinstance(branch, str) or not BRANCH.fullmatch(branch):
        raise Denied("target branch is outside policy")
    nonce = request["nonce"]
    if not isinstance(nonce, str) or not NONCE.fullmatch(nonce):
        raise Denied("nonce is invalid")
    issued, expires = request["issued_at"], request["expires_at"]
    if not isinstance(issued, int) or not isinstance(expires, int):
        raise Denied("request time is invalid")
    if issued > now + 30 or expires <= now or expires - issued > max_lifetime:
        raise Denied("request is expired, future-dated, or too long-lived")
    if not isinstance(policy_digest, str) or not SHA256.fullmatch(policy_digest):
        raise Denied("current policy digest is invalid")
    if request["policy_digest"] != policy_digest:
        raise Denied("policy digest changed")

    action = request["action"]
    if not isinstance(action, dict) or frozenset(action) != ACTION_KEYS:
        raise Denied("action schema mismatch")
    entries = action["files"]
    if not isinstance(entries, list) or not entries or len(entries) > MAX_FILES:
        raise Denied("file count is outside policy")
    message = action["commit_message"]
    if not isinstance(message, str) or not message.startswith("AI-PAM project: "):
        raise Denied("commit message prefix is required")
    if len(message.encode("utf-8")) > MAX_COMMIT_MESSAGE_BYTES or "\n" in message or "\r" in message:
        raise Denied("commit message is malformed")

    parsed: list[tuple[PurePosixPath, str, int]] = []
    seen: set[str] = set()
    for entry in entries:
        if not isinstance(entry, dict) or frozenset(entry) != FILE_KEYS:
            raise Denied("file entry schema mismatch")
        path = _safe_relative(entry["path"])
        lowered = str(path).casefold()
        if lowered in seen:
            raise Denied("case-colliding or duplicate document path")
        seen.add(lowered)
        expected_hash, expected_size = entry["content_sha256"], entry["content_size"]
        if not isinstance(expected_hash, str) or not SHA256.fullmatch(expected_hash):
            raise Denied("document digest is invalid")
        if not isinstance(expected_size, int) or expected_size < 1 or expected_size > MAX_FILE_BYTES:
            raise Denied("document size is outside policy")
        parsed.append((path, expected_hash, expected_size))

    expected_paths = {path for path, _, _ in parsed}
    _ensure_package_tree(root, expected_paths)
    documents: list[VerifiedDocument] = []
    total = 0
    for path, expected_hash, expected_size in sorted(parsed, key=lambda item: str(item[0])):
        content_raw = _lstat_regular(root, PurePosixPath("files") / path, max_bytes=MAX_FILE_BYTES)
        if len(content_raw) != expected_size or digest(content_raw) != expected_hash:
            raise Denied("document does not match the signed manifest")
        total += len(content_raw)
        if total > MAX_TOTAL_BYTES:
            raise Denied("package total size is outside policy")
        try:
            content = content_raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise Denied("documents must be UTF-8 text") from exc
        if "\x00" in content or _private_detail(content):
            raise Denied("document appears secret-bearing or private")
        documents.append(VerifiedDocument(str(path), content, expected_hash, expected_size))

    return VerifiedDocumentBundle(
        request_digest=digest(body), signer=signer, repository=repository,
        base_revision=base, target_branch=branch, nonce=nonce, expires_at=expires,
        policy_digest=policy_digest, commit_message=message, documents=tuple(documents),
    )


def reverify_document_bundle(
    verified: VerifiedDocumentBundle,
    *,
    bundle_dir: Path,
    current_base_revision: str,
    policy_digest: str,
    now: int | None = None,
) -> None:
    """Recheck mutable policy facts and every content digest before promotion."""
    now = int(time.time()) if now is None else now
    if now >= verified.expires_at or current_base_revision != verified.base_revision:
        raise Denied("request expired or canonical base revision changed")
    if policy_digest != verified.policy_digest:
        raise Denied("policy digest changed")
    try:
        bundle_info = bundle_dir.lstat()
    except OSError as exc:
        raise Denied("package directory is unavailable") from exc
    if stat.S_ISLNK(bundle_info.st_mode) or not stat.S_ISDIR(bundle_info.st_mode):
        raise Denied("package root is not a directory")
    root = bundle_dir.resolve(strict=True)
    expected = {document.path: document for document in verified.documents}
    _ensure_package_tree(
        root,
        {PurePosixPath(path) for path in expected},
    )
    for path, document in expected.items():
        raw = _lstat_regular(root, PurePosixPath("files") / path, max_bytes=MAX_FILE_BYTES)
        if digest(raw) != document.content_sha256 or raw.decode("utf-8") != document.content:
            raise Denied("document changed after validation")
