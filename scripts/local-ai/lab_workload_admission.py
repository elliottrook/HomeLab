"""Offline source-bound admission contract for a MacBook lab workload.

This module is deliberately only a contract and verifier.  It does not open a
socket, read credentials, or grant GPU access.  A future installed adapter must
bind these values to the authenticated MacBook session and the persistent lab
lease before forwarding a request to the fixed in-guest wrapper.
"""

from __future__ import annotations

import hashlib
import re
import time
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


class LabAdmissionVerifier:
    """Verifier-owned clock and replay state for one durable lease."""

    _REQUEST_ID = re.compile(r"req-[a-z0-9]{16,32}\Z")

    def __init__(self, manifest: LabAdmissionManifest):
        validate_manifest(manifest)
        self.manifest = manifest
        self._seen_request_ids: set[str] = set()

    def authorize(self, request: LabAdmissionRequest) -> dict[str, object]:
        """Return a content-free receipt using the verifier's current clock."""
        manifest = self.manifest
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
        now_epoch = int(time.time())
        if not (manifest.issued_epoch <= now_epoch < manifest.expires_epoch):
            raise LabAdmissionError("request is outside the lease admission window")
        if not self._REQUEST_ID.fullmatch(request.request_id):
            raise LabAdmissionError("request identity is invalid")
        if request.request_id in self._seen_request_ids:
            raise LabAdmissionError("request identity has already been admitted")
        self._seen_request_ids.add(request.request_id)
        return {
            "admitted": True,
            "owner_id": manifest.owner_id,
            "lease_id": manifest.lease_id,
            "generation": manifest.generation,
            "request_id_sha256": hashlib.sha256(request.request_id.encode()).hexdigest(),
            "source_sha256": manifest.source_sha256,
            "profile_sha256": manifest.profile_sha256,
        }
