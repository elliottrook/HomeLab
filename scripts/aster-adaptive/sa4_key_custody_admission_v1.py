"""Validate an SA4 three-custodian public-key candidate without installing it."""
from __future__ import annotations

import re

import sa4_authenticated_authority_v1 as authority
import sa4_key_custody_slots_v1 as custody
from nlu_threshold_policy import decode_unique_json


IDENTITY = re.compile(r"[a-z0-9][a-z0-9._-]{2,127}")
ROLE_FIELDS = {
    "role", "custody_domain", "signer_location", "signer_id", "public_key",
    "creation_method", "private_key_exported", "private_key_read_by_codex",
    "runtime_key_nomination",
}
TOP_FIELDS = {
    "schema", "status", "target_id", "roles", "authority",
    "effect_authorized", "automatic_routing",
}


def validate_candidate(raw: bytes) -> dict[str, object]:
    custody.validate()
    value = decode_unique_json(raw)
    if (not isinstance(value, dict) or set(value) != TOP_FIELDS
            or value["schema"] != "aster-sa4-key-custody-candidate.v1"
            or value["status"] != "candidate-for-owner-review"
            or value["target_id"] != "sa4-lxc104-canary-adapter-v1"
            or value["authority"] != "public-trust-proposal-no-effect"
            or value["effect_authorized"] is not False
            or value["automatic_routing"] != "off"
            or not isinstance(value["roles"], list)
            or len(value["roles"]) != len(custody.SLOTS)):
        raise ValueError("SA4 custody candidate envelope changed")

    digests: list[str] = []
    signer_ids: list[str] = []
    for row, slot in zip(value["roles"], custody.SLOTS):
        if (not isinstance(row, dict) or set(row) != ROLE_FIELDS
                or row["role"] != slot.role
                or row["custody_domain"] != slot.custody_domain
                or row["signer_location"] != slot.signer_location
                or not isinstance(row["signer_id"], str)
                or not IDENTITY.fullmatch(row["signer_id"])
                or row["creation_method"] != "external-custodian-generated"
                or row["private_key_exported"] is not False
                or row["private_key_read_by_codex"] is not False
                or row["runtime_key_nomination"] is not False):
            raise ValueError("SA4 custody role changed")
        digests.append(authority.key_sha256(row["public_key"]))
        signer_ids.append(row["signer_id"])
    if len(set(digests)) != 3 or len(set(signer_ids)) != 3:
        raise ValueError("SA4 custody identities must be distinct")

    return {
        "schema": "aster-sa4-key-custody-admission.v1",
        "target_id": value["target_id"],
        "public_key_sha256_by_role": {
            slot.role: digest for slot, digest in zip(custody.SLOTS, digests)
        },
        "custody_domains_distinct": True,
        "private_material_accepted": False,
        "ready_for_owner_review": True,
        "ready_for_installation": False,
        "effect_authorized": False,
        "automatic_routing": "off",
    }
