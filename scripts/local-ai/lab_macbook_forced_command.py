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
import stat
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from lab_macbook_admission_adapter import AuthenticatedMacBookSession

FORCED_COMMAND = "aster-lab-session-attest"
ATTESTATION_SECONDS = 120
CONFIG_PATH = Path("/etc/local-ai-lab/aster-lab-session.json")
ATTESTATION_PATH = Path("/var/lib/local-ai-lease/macbook-attestation/session.json")


class ForcedCommandError(ValueError):
    pass


@dataclass(frozen=True)
class ForcedCommandConfig:
    principal: str
    client_key_fingerprint: str
    host_key_sha256: str


def load_forced_command_config(path: Path) -> ForcedCommandConfig:
    """Load the fixed root-owned key configuration, never request data."""
    parent = path.parent.lstat()
    if (not stat.S_ISDIR(parent.st_mode) or parent.st_uid != 0
            or stat.S_IMODE(parent.st_mode) != 0o700):
        raise ForcedCommandError("forced-command config custody is invalid")
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0)
    try:
        fd = os.open(path, flags)
        info = os.fstat(fd)
        if (not stat.S_ISREG(info.st_mode) or info.st_uid != 0
                or info.st_nlink != 1 or stat.S_IMODE(info.st_mode) != 0o600):
            raise ForcedCommandError("forced-command config custody is invalid")
        with os.fdopen(fd, "r", encoding="utf-8") as stream:
            payload = stream.read(4097)
        if len(payload) > 4096:
            raise ForcedCommandError("forced-command config is oversized")
        value = json.loads(payload)
    except (OSError, json.JSONDecodeError) as exc:
        raise ForcedCommandError("forced-command config is unreadable") from exc
    if type(value) is not dict or set(value) != {"principal", "client_key_fingerprint", "host_key_sha256"}:
        raise ForcedCommandError("forced-command config schema is invalid")
    return ForcedCommandConfig(**value)


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
    expires_epoch = now_epoch + ATTESTATION_SECONDS
    session_id = hashlib.sha256(f"{connection}|{nonce}|{now_epoch}".encode()).hexdigest()[:32]
    return AuthenticatedMacBookSession(config.principal, config.client_key_fingerprint,
                                      config.host_key_sha256, session_id,
                                      hashlib.sha256(connection.encode()).hexdigest(),
                                      now_epoch, expires_epoch), expires_epoch


def write_fresh_attestation(path: Path, session: AuthenticatedMacBookSession,
                            *, parent_mode: int = 0o700) -> None:
    """Atomically publish only the fresh session fields to a private path."""
    parent = path.parent
    try:
        parent_info = parent.lstat()
        if (not stat.S_ISDIR(parent_info.st_mode) or parent_info.st_uid != 0
                or stat.S_IMODE(parent_info.st_mode) != parent_mode):
            raise ForcedCommandError("forced-command attestation parent custody is invalid")
        if path.exists() or path.is_symlink():
            info = path.lstat()
            if (stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode)
                    or info.st_uid != 0 or info.st_nlink != 1
                    or stat.S_IMODE(info.st_mode) != 0o600):
                raise ForcedCommandError("forced-command attestation file custody is invalid")
    except FileNotFoundError as exc:
        raise ForcedCommandError("forced-command attestation parent is missing") from exc
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


def main() -> int:
    """Fixed authorized_keys command; no request-controlled arguments."""
    config = load_forced_command_config(CONFIG_PATH)
    session, _ = create_fresh_session(config, ssh_env=dict(os.environ),
                                      now_epoch=int(time.time()))
    write_fresh_attestation(ATTESTATION_PATH, session)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
