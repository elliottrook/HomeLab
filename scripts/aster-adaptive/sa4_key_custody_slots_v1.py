"""Compiled empty custody slots for future SA4 public trust anchors."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class KeySlot:
    role: str
    custody_domain: str
    signer_location: str
    status: str = "empty"
    public_key_sha256: None = None
    private_key_export_allowed: bool = False
    runtime_key_nomination: bool = False


SLOTS = (
    KeySlot("owner-approval", "human-owner-device", "owner-mac-signing-surface"),
    KeySlot("ai-pam-grant", "ai-pam-broker", "broker-controlled-signer"),
    KeySlot("independent-observer", "proxmox-observer", "dedicated-observer-identity"),
)


def validate() -> None:
    if (len(SLOTS) != 3 or len({slot.role for slot in SLOTS}) != 3
            or len({slot.custody_domain for slot in SLOTS}) != 3
            or any(slot.status != "empty" or slot.public_key_sha256 is not None
                   or slot.private_key_export_allowed is not False
                   or slot.runtime_key_nomination is not False for slot in SLOTS)):
        raise ValueError("SA4 key custody slots changed")


validate()
