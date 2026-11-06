"""Owner-accepted public SA4 custody slots; private material is never present."""
from __future__ import annotations

from dataclasses import dataclass

import sa4_public_trust_candidate_v1 as trust


@dataclass(frozen=True)
class KeySlot:
    role: str
    custody_domain: str
    signer_location: str
    signer_id: str
    public_key_sha256: str
    public_key: dict[str, object]
    status: str = "accepted-public-source"
    private_key_export_allowed: bool = False
    runtime_key_nomination: bool = False


SLOTS = (
    KeySlot("owner-approval", "human-owner-device", "owner-mac-signing-surface",
            trust.SIGNER_IDS["owner-approval"],
            trust.EXPECTED_DIGESTS["owner-approval"],
            trust.PUBLIC_KEYS["owner-approval"]),
    KeySlot("ai-pam-grant", "ai-pam-broker", "broker-controlled-signer",
            trust.SIGNER_IDS["ai-pam-grant"],
            trust.EXPECTED_DIGESTS["ai-pam-grant"],
            trust.PUBLIC_KEYS["ai-pam-grant"]),
    KeySlot("independent-observer", "proxmox-observer",
            "dedicated-observer-identity",
            trust.SIGNER_IDS["independent-observer"],
            trust.EXPECTED_DIGESTS["independent-observer"],
            trust.PUBLIC_KEYS["independent-observer"]),
)

OWNER_ACCEPTANCE_SHA256 = \
    "3374e8edba5f3a4bc7050d5563f8e4d9f2d2e8168d03a173ff5e1e9a12873207"


def validate() -> None:
    if (len(SLOTS) != 3 or len({slot.role for slot in SLOTS}) != 3
            or len({slot.custody_domain for slot in SLOTS}) != 3
            or len({slot.signer_id for slot in SLOTS}) != 3
            or len({slot.public_key_sha256 for slot in SLOTS}) != 3
            or any(slot.status != "accepted-public-source"
                   or trust.key_sha256(slot.public_key) != slot.public_key_sha256
                   or slot.private_key_export_allowed is not False
                   or slot.runtime_key_nomination is not False for slot in SLOTS)
            or OWNER_ACCEPTANCE_SHA256 !=
            "3374e8edba5f3a4bc7050d5563f8e4d9f2d2e8168d03a173ff5e1e9a12873207"):
        raise ValueError("SA4 key custody slots changed")


validate()
