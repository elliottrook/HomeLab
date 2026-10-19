"""Trusted-transport boundary for the source-bound MacBook lab manifest.

The caller supplies a transport-attested session object, not JSON fields that
claim to be an identity.  A real adapter must construct this object only after
the authenticated SSH/session layer has reported the principal, client-key
fingerprint and pinned host key.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from lab_workload_admission import LabAdmissionError, LabAdmissionManifest


@dataclass(frozen=True)
class AuthenticatedMacBookSession:
    principal: str
    client_key_fingerprint: str
    host_key_sha256: str
    session_id: str


def _validate_session(session: AuthenticatedMacBookSession) -> None:
    if session.principal != "jelliott":
        raise LabAdmissionError("authenticated SSH principal is not approved")
    if not re.fullmatch(r"SHA256:[A-Za-z0-9+/=]+", session.client_key_fingerprint):
        raise LabAdmissionError("authenticated client fingerprint is invalid")
    if len(session.host_key_sha256) != 64 or any(c not in "0123456789abcdef" for c in session.host_key_sha256):
        raise LabAdmissionError("authenticated host key is invalid")
    if not re.fullmatch(r"[A-Za-z0-9_-]{8,128}", session.session_id):
        raise LabAdmissionError("authenticated session identity is invalid")


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
