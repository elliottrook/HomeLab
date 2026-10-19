"""Trusted-transport boundary for the source-bound MacBook lab manifest.

The caller supplies a transport-attested session object, not JSON fields that
claim to be an identity.  A real adapter must construct this object only after
the authenticated SSH/session layer has reported the principal, client-key
fingerprint and pinned host key.
"""

from __future__ import annotations

import re
import json
import os
import stat
import hashlib
from dataclasses import dataclass
from pathlib import Path

from lab_workload_admission import LabAdmissionError, LabAdmissionManifest


@dataclass(frozen=True)
class AuthenticatedMacBookSession:
    principal: str
    client_key_fingerprint: str
    host_key_sha256: str
    session_id: str
    connection_sha256: str
    issued_epoch: int
    expires_epoch: int


def _validate_session(session: AuthenticatedMacBookSession) -> None:
    if session.principal != "jelliott":
        raise LabAdmissionError("authenticated SSH principal is not approved")
    if not re.fullmatch(r"SHA256:[A-Za-z0-9+/=]+", session.client_key_fingerprint):
        raise LabAdmissionError("authenticated client fingerprint is invalid")
    if len(session.host_key_sha256) != 64 or any(c not in "0123456789abcdef" for c in session.host_key_sha256):
        raise LabAdmissionError("authenticated host key is invalid")
    if not re.fullmatch(r"[A-Za-z0-9_-]{8,128}", session.session_id):
        raise LabAdmissionError("authenticated session identity is invalid")
    if (len(session.connection_sha256) != 64
            or any(c not in "0123456789abcdef" for c in session.connection_sha256)
            or type(session.issued_epoch) is not int
            or type(session.expires_epoch) is not int
            or not session.issued_epoch < session.expires_epoch
            or session.expires_epoch - session.issued_epoch > 120):
        raise LabAdmissionError("authenticated session envelope is invalid")


def manifest_from_authenticated_session(
    session: AuthenticatedMacBookSession, *, lease_id: str, generation: int,
    source_sha256: str, profile_sha256: str, issued_epoch: int, expires_epoch: int,
) -> LabAdmissionManifest:
    """Build a manifest from transport evidence, never from request JSON."""
    _validate_session(session)
    return LabAdmissionManifest(
        owner_id=session.principal,
        lease_id=lease_id,
        generation=generation,
        client_key_fingerprint=session.client_key_fingerprint,
        host_key_sha256=session.host_key_sha256,
        source_sha256=source_sha256,
        profile_sha256=profile_sha256,
        issued_epoch=issued_epoch,
        expires_epoch=expires_epoch,
    )


def load_forced_command_session(path: Path, *, now_epoch: int,
                                connection: str) -> AuthenticatedMacBookSession:
    """Consume one fresh root-owned attestation for the current SSH session."""
    parent = path.parent.lstat()
    if (not stat.S_ISDIR(parent.st_mode) or parent.st_uid != 0
            or stat.S_IMODE(parent.st_mode) != 0o700):
        raise LabAdmissionError("forced-command attestation custody is invalid")
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0)
    try:
        fd = os.open(path, flags)
    except OSError as exc:
        raise LabAdmissionError("forced-command attestation is unreadable") from exc
    try:
        info = os.fstat(fd)
        if (stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode)
                or info.st_uid != 0 or info.st_nlink != 1
                or stat.S_IMODE(info.st_mode) != 0o600):
            raise LabAdmissionError("forced-command attestation custody is invalid")
        with os.fdopen(fd, "r", encoding="utf-8") as stream:
            payload = stream.read(8193)
        if len(payload) > 8192:
            raise LabAdmissionError("forced-command attestation is oversized")
        value = json.loads(payload)
    except (OSError, json.JSONDecodeError) as exc:
        raise LabAdmissionError("forced-command attestation is unreadable") from exc
    if type(value) is not dict or set(value) != {"principal", "client_key_fingerprint", "host_key_sha256", "session_id", "connection_sha256", "issued_epoch", "expires_epoch"}:
        raise LabAdmissionError("forced-command attestation schema is invalid")
    session = AuthenticatedMacBookSession(**value)
    _validate_session(session)
    if (type(now_epoch) is not int or now_epoch < session.issued_epoch
            or now_epoch >= session.expires_epoch
            or session.connection_sha256 != hashlib.sha256(connection.encode()).hexdigest()):
        raise LabAdmissionError("forced-command attestation is expired or for another session")
    try:
        os.unlink(path)
    except OSError as exc:
        raise LabAdmissionError("forced-command attestation could not be consumed") from exc
    return session
