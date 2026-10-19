"""Source-only forced-command attestation producer for MacBook lab access.

The authorized_keys entry must invoke this fixed command and provide only its
reviewed key fingerprint/host-key configuration.  The SSH session variables
are read from sshd, not from request JSON.  A fresh short-lived attestation is
written for each connection; it is not a reusable static identity file.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from lab_macbook_admission_adapter import AuthenticatedMacBookSession

FORCED_COMMAND = "aster-lab-session-attest"
ATTESTATION_SECONDS = 120


class ForcedCommandError(ValueError):
    pass


@dataclass(frozen=True)
class ForcedCommandConfig:
    principal: str
    client_key_fingerprint: str
    host_key_sha256: str


def create_fresh_session(config: ForcedCommandConfig, *, ssh_env: dict[str, str],
                         now_epoch: int, nonce: Optional[str] = None) -> tuple[AuthenticatedMacBookSession, int]:
    if config.principal != "jelliott" or not re.fullmatch(r"SHA256:[A-Za-z0-9+/=]+", config.client_key_fingerprint):
        raise ForcedCommandError("forced-command key configuration is invalid")
    if len(config.host_key_sha256) != 64 or any(c not in "0123456789abcdef" for c in config.host_key_sha256):
        raise ForcedCommandError("forced-command host key configuration is invalid")
    if ssh_env.get("SSH_ORIGINAL_COMMAND") != FORCED_COMMAND:
        raise ForcedCommandError("unexpected SSH command")
    connection = ssh_env.get("SSH_CONNECTION", "")
    if not re.fullmatch(r"\S+ \d+ \S+ \d+", connection):
        raise ForcedCommandError("SSH session is not bound")
    if type(now_epoch) is not int or now_epoch < 0:
        raise ForcedCommandError("forced-command clock is invalid")
    nonce = nonce or secrets.token_urlsafe(18)
    if not re.fullmatch(r"[A-Za-z0-9_-]{16,64}", nonce):
        raise ForcedCommandError("forced-command nonce is invalid")
    session_id = hashlib.sha256(f"{connection}|{nonce}|{now_epoch}".encode()).hexdigest()[:32]
    return AuthenticatedMacBookSession(config.principal, config.client_key_fingerprint,
                                      config.host_key_sha256, session_id), now_epoch + ATTESTATION_SECONDS


def write_fresh_attestation(path: Path, session: AuthenticatedMacBookSession,
                            *, parent_mode: int = 0o700) -> None:
    """Atomically publish only the fresh session fields to a private path."""
    parent = path.parent
    parent.mkdir(mode=parent_mode, parents=True, exist_ok=True)
    os.chmod(parent, parent_mode)
    payload = json.dumps(session.__dict__, sort_keys=True, separators=(",", ":")) + "\n"
    fd, name = tempfile.mkstemp(prefix=f".{path.name}.", dir=parent)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
        parent_fd = os.open(parent, os.O_RDONLY)
        try:
            os.fsync(parent_fd)
        finally:
            os.close(parent_fd)
    except Exception:
        try:
            os.unlink(name)
        except FileNotFoundError:
            pass
        raise
