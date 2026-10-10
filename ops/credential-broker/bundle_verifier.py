#!/usr/bin/env python3
"""Fail-closed verifier for one-file Forgejo safe-write bundles.

This module performs no network, Git, Forgejo, OpenBao or broker I/O.  It turns
an authenticated immutable bundle into the exact payload accepted by the
existing ``forgejo.write.safe-branch`` capability.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
import stat
import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Callable, Mapping

from mcp_policy_adapter import SECRET_OUTPUT_PATTERNS


SHA256 = re.compile(r"^[0-9a-f]{64}$")
GIT_SHA = re.compile(r"^[0-9a-f]{40}$")
NONCE = re.compile(r"^[A-Za-z0-9_-]{22,128}$")
BRANCH = re.compile(r"^ai-pam/[a-z0-9][a-z0-9._-]{0,62}$")
SIGNER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9@._-]{0,127}$")
CANARY_PATH = re.compile(r"^ai-pam-pilot/cloud-runner/[a-z0-9][a-z0-9._/-]{0,160}$")
EXPECTED_KEYS = frozenset({
    "version", "repository", "base_revision", "target_branch", "nonce",
    "issued_at", "expires_at", "policy_digest", "signer", "action",
})
ACTION_KEYS = frozenset({"file_path", "content_file", "content_sha256", "content_size", "commit_message"})
MAX_MANIFEST_BYTES = 32 * 1024
MAX_SIGNATURE_BYTES = 64 * 1024
MAX_CONTENT_BYTES = 4096


class Denied(ValueError):
    """A non-secret, fail-closed rejection."""


def canonical_json(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _regular_file(path: Path, *, max_bytes: int) -> bytes:
    try:
        descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    except OSError as exc:
        raise Denied("bundle file cannot be opened safely") from exc
    try:
        info = os.fstat(descriptor)
        if not stat.S_ISREG(info.st_mode) or info.st_size > max_bytes:
            raise Denied("bundle file is not a bounded regular file")
        data = bytearray()
        while len(data) <= max_bytes:
            chunk = os.read(descriptor, min(65_536, max_bytes + 1 - len(data)))
            if not chunk:
                break
            data.extend(chunk)
        if len(data) > max_bytes:
            raise Denied("bundle file is oversized")
        return bytes(data)
    except OSError as exc:
        raise Denied("bundle file cannot be read safely") from exc
    finally:
        os.close(descriptor)


def verify_openssh_signature(
    body: bytes,
    signature: bytes,
    *,
    allowed_signers: Path,
    principal: str,
    namespace: str = "homelab-change-bundle",
    binary: str = "/usr/bin/ssh-keygen",
) -> bool:
    """Verify an sshsig and the configured signer principal without a shell."""
    if not SIGNER.fullmatch(principal) or not namespace or len(namespace) > 128:
        return False
    try:
        policy = allowed_signers.resolve(strict=True)
        policy_info = policy.stat()
        if not stat.S_ISREG(policy_info.st_mode) or policy_info.st_mode & 0o022:
            return False
        with tempfile.NamedTemporaryFile(prefix="bundle-signature-", mode="wb") as handle:
            handle.write(signature)
            handle.flush()
            result = subprocess.run(
                [binary, "-Y", "verify", "-f", str(policy), "-I", principal,
                 "-n", namespace, "-s", handle.name],
                input=body,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=5,
                check=False,
                env={"PATH": "/usr/bin:/bin", "LANG": "C"},
            )
        return result.returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


@dataclass(frozen=True)
class VerifiedBundle:
    request_digest: str
    signer: str
    repository: str
    base_revision: str
    target_branch: str
    nonce: str
    expires_at: int
    policy_digest: str
    content_digest: str
    payload: Mapping[str, str]


class ReplayLedger:
    """Durable intake ledger with explicit, monotonic state transitions."""

    def __init__(self, path: Path):
        self.db = sqlite3.connect(path, isolation_level=None)
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("PRAGMA synchronous=FULL")
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS requests("
            "nonce TEXT PRIMARY KEY,digest TEXT NOT NULL,signer TEXT NOT NULL,"
            "state TEXT NOT NULL CHECK(state IN ('validated','pending','consumed','revoked')),"
            "broker_request_id TEXT UNIQUE,created_at INTEGER NOT NULL,updated_at INTEGER NOT NULL)"
        )

    def close(self) -> None:
        self.db.close()

    def reserve(self, bundle: VerifiedBundle, now: int) -> None:
        try:
            self.db.execute("BEGIN IMMEDIATE")
            self.db.execute(
                "INSERT INTO requests(nonce,digest,signer,state,created_at,updated_at) VALUES(?,?,?,'validated',?,?)",
                (bundle.nonce, bundle.request_digest, bundle.signer, now, now),
            )
            self.db.execute("COMMIT")
        except sqlite3.IntegrityError as exc:
            self.db.execute("ROLLBACK")
            raise Denied("nonce or request is already recorded") from exc

    def bind_broker_request(self, nonce: str, request_digest: str, request_id: str, now: int) -> None:
        self._transition(nonce, request_digest, "validated", "pending", now, request_id=request_id)

    def consume(self, nonce: str, request_digest: str, now: int) -> None:
        self._transition(nonce, request_digest, "pending", "consumed", now)

    def revoke(self, nonce: str, request_digest: str, now: int) -> None:
        self.db.execute("BEGIN IMMEDIATE")
        changed = self.db.execute(
            "UPDATE requests SET state='revoked',updated_at=? WHERE nonce=? AND digest=? "
            "AND state IN ('validated','pending')", (now, nonce, request_digest),
        ).rowcount
        if changed != 1:
            self.db.execute("ROLLBACK")
            raise Denied("request is absent, changed, or terminal")
        self.db.execute("COMMIT")

    def pending_request_id(self, nonce: str, request_digest: str) -> str:
        row = self.db.execute(
            "SELECT broker_request_id,state FROM requests WHERE nonce=? AND digest=?",
            (nonce, request_digest),
        ).fetchone()
        if row is None or row[1] != "pending" or not row[0]:
            raise Denied("request is absent, changed, or not pending")
        return str(row[0])

    def _transition(
        self, nonce: str, request_digest: str, before: str, after: str, now: int,
        *, request_id: str | None = None,
    ) -> None:
        self.db.execute("BEGIN IMMEDIATE")
        assignment = "state=?,updated_at=?"
        values: list[object] = [after, now]
        if request_id is not None:
            if not re.fullmatch(r"[0-9a-f-]{36}", request_id):
                self.db.execute("ROLLBACK")
                raise Denied("broker request identifier is invalid")
            assignment += ",broker_request_id=?"
            values.append(request_id)
        values.extend((nonce, request_digest, before))
        try:
            changed = self.db.execute(
                f"UPDATE requests SET {assignment} WHERE nonce=? AND digest=? AND state=?", values,
            ).rowcount
        except sqlite3.IntegrityError as exc:
            self.db.execute("ROLLBACK")
            raise Denied("broker request is already bound") from exc
        if changed != 1:
            self.db.execute("ROLLBACK")
            raise Denied("request is absent, changed, replayed, or in the wrong state")
        self.db.execute("COMMIT")


def verify_bundle(
    bundle_dir: Path,
    *,
    current_base_revision: str,
    policy_digest: str,
    verify_signature: Callable[[bytes, bytes, str], bool],
    now: int | None = None,
    repository: str = "jason/homelab",
    max_lifetime: int = 900,
) -> VerifiedBundle:
    """Verify one bundle and return the exact existing safe-write payload."""
    now = int(time.time()) if now is None else now
    root = bundle_dir.resolve(strict=True)
    manifest_path = root / "request.json"
    signature_path = root / "request.sig"
    try:
        manifest_raw = _regular_file(manifest_path, max_bytes=MAX_MANIFEST_BYTES)
        signature = _regular_file(signature_path, max_bytes=MAX_SIGNATURE_BYTES)
        request = json.loads(manifest_raw.decode("utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise Denied("request metadata is invalid") from exc
    if not isinstance(request, dict) or frozenset(request) != EXPECTED_KEYS:
        raise Denied("request schema mismatch")
    body = canonical_json(request)
    signer = request["signer"]
    if not isinstance(signer, str) or not SIGNER.fullmatch(signer):
        raise Denied("signer principal is invalid")
    if not verify_signature(body, signature, signer):
        raise Denied("request signature or signer is invalid")
    if request["version"] != 1 or request["repository"] != repository:
        raise Denied("request version or repository is not allowed")
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
    if request["policy_digest"] != policy_digest or not SHA256.fullmatch(policy_digest):
        raise Denied("policy digest changed or is invalid")
    action = request["action"]
    if not isinstance(action, dict) or frozenset(action) != ACTION_KEYS:
        raise Denied("action schema mismatch")
    file_path = action["file_path"]
    if not isinstance(file_path, str) or not CANARY_PATH.fullmatch(file_path):
        raise Denied("target path is outside the canary scope")
    target = PurePosixPath(file_path)
    if target.is_absolute() or ".." in target.parts or target.name in {"", "."}:
        raise Denied("target path is invalid")
    content_file = action["content_file"]
    if content_file != "content.txt":
        raise Denied("content artifact name is fixed")
    expected_hash, expected_size = action["content_sha256"], action["content_size"]
    if not isinstance(expected_hash, str) or not SHA256.fullmatch(expected_hash):
        raise Denied("content digest is invalid")
    if not isinstance(expected_size, int) or expected_size < 1 or expected_size > MAX_CONTENT_BYTES:
        raise Denied("content size is outside policy")
    content_raw = _regular_file(root / content_file, max_bytes=MAX_CONTENT_BYTES)
    if len(content_raw) != expected_size or digest(content_raw) != expected_hash:
        raise Denied("content does not match the signed request")
    try:
        content = content_raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise Denied("content must be UTF-8 text") from exc
    if "\x00" in content or any(pattern.search(content) for pattern in SECRET_OUTPUT_PATTERNS):
        raise Denied("content appears secret-bearing")
    message = action["commit_message"]
    if not isinstance(message, str) or not message.startswith("AI-PAM pilot: "):
        raise Denied("commit message prefix is required")
    if len(message.encode("utf-8")) > 160 or "\n" in message or "\r" in message:
        raise Denied("commit message is malformed")
    payload = {
        "owner": "jason", "repo": "homelab", "filePath": file_path,
        "content": content, "message": message, "branch_name": "main",
        "new_branch_name": branch,
    }
    return VerifiedBundle(
        digest(body), signer, repository, base, branch, nonce, expires,
        policy_digest, expected_hash, payload,
    )


def reverify_for_promotion(
    verified: VerifiedBundle,
    *,
    bundle_dir: Path,
    current_base_revision: str,
    policy_digest: str,
    now: int | None = None,
) -> None:
    """Repeat mutable facts and content checks immediately before consumption."""
    now = int(time.time()) if now is None else now
    if now >= verified.expires_at or current_base_revision != verified.base_revision:
        raise Denied("request expired or canonical base revision changed")
    if policy_digest != verified.policy_digest:
        raise Denied("policy digest changed")
    content = _regular_file(bundle_dir.resolve(strict=True) / "content.txt", max_bytes=MAX_CONTENT_BYTES)
    if digest(content) != verified.content_digest or content.decode("utf-8") != verified.payload["content"]:
        raise Denied("content changed after validation")
