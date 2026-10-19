"""Offline source-bound admission contract for a MacBook lab workload.

This module is deliberately only a contract and verifier.  It does not open a
socket, read credentials, or grant GPU access.  A future installed adapter must
bind these values to the authenticated MacBook session and the persistent lab
lease before forwarding a request to the fixed in-guest wrapper.
"""

from __future__ import annotations

from dataclasses import dataclass


class LabAdmissionError(ValueError):
    pass


@dataclass(frozen=True)
class LabAdmissionManifest:
    owner_id: str
    lease_id: str
    generation: int
    client_key_fingerprint: str
    host_key_sha256: str
    source_sha256: str
    profile_sha256: str
    issued_epoch: int
    expires_epoch: int


@dataclass(frozen=True)
class LabAdmissionRequest:
    owner_id: str
    lease_id: str
    generation: int
    client_key_fingerprint: str
    host_key_sha256: str
    source_sha256: str
    profile_sha256: str
    now_epoch: int
    request_id: str


def _hex(value: str, label: str) -> None:
    if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise LabAdmissionError(f"{label} is not a lowercase SHA-256 digest")


def validate_manifest(manifest: LabAdmissionManifest) -> None:
    if not manifest.owner_id or not manifest.lease_id:
        raise LabAdmissionError("owner and lease identity are required")
    if type(manifest.generation) is not int or manifest.generation < 1:
        raise LabAdmissionError("lease generation is invalid")
    if not manifest.client_key_fingerprint.startswith("SHA256:"):
        raise LabAdmissionError("MacBook key fingerprint is not pinned")
    _hex(manifest.host_key_sha256, "host key")
    _hex(manifest.source_sha256, "source")
    _hex(manifest.profile_sha256, "profile")
    if type(manifest.issued_epoch) is not int or type(manifest.expires_epoch) is not int:
        raise LabAdmissionError("admission epochs are invalid")
    if not manifest.issued_epoch < manifest.expires_epoch:
        raise LabAdmissionError("admission expiry is invalid")


def authorize_request(manifest: LabAdmissionManifest, request: LabAdmissionRequest) -> dict[str, object]:
    """Return a content-free receipt only when every source-bound value matches."""
    validate_manifest(manifest)
    if request.owner_id != manifest.owner_id or request.lease_id != manifest.lease_id:
        raise LabAdmissionError("owner or lease identity does not match")
    if request.generation != manifest.generation:
        raise LabAdmissionError("lease generation does not match")
    if request.client_key_fingerprint != manifest.client_key_fingerprint:
        raise LabAdmissionError("MacBook identity does not match")
    if request.host_key_sha256 != manifest.host_key_sha256:
        raise LabAdmissionError("Proxmox host key does not match")
    if request.source_sha256 != manifest.source_sha256:
        raise LabAdmissionError("source digest does not match")
    if request.profile_sha256 != manifest.profile_sha256:
        raise LabAdmissionError("workload profile does not match")
    if type(request.now_epoch) is not int or not (manifest.issued_epoch <= request.now_epoch < manifest.expires_epoch):
        raise LabAdmissionError("request is outside the lease admission window")
    if not request.request_id or len(request.request_id) > 128:
        raise LabAdmissionError("request identity is invalid")
    return {
        "admitted": True,
        "owner_id": manifest.owner_id,
        "lease_id": manifest.lease_id,
        "generation": manifest.generation,
        "request_id": request.request_id,
        "source_sha256": manifest.source_sha256,
        "profile_sha256": manifest.profile_sha256,
    }
