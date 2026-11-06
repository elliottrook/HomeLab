"""Post-install, no-authority release packet for the first SA4 repair."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import sa4_runtime_control_inactive_upgrade_result_v1 as upgrade_result


ROOT = Path(__file__).parents[2]
UPGRADE_RESULT = ROOT / (
    "docs/projects/AI Projects/evidence/"
    "SA4-runtime-control-inactive-upgrade-result-2026-11-05.json")
UPGRADE_RESULT_SHA256 = (
    "10895012375e346b9fb633f287e44d00953ce1ad8e26c3af867540098e02332b")
RETAINED_PACKET = ROOT / (
    "docs/projects/AI Projects/evidence/"
    "SA4-post-install-first-repair-release-candidate-2026-11-05.json")
SOURCES = {
    "scripts/aster-adaptive/sa4_preflight_composition_v1.py":
        "a38ccb0b33bbc828f7ae96fd68304776cd840ea49bb07986044383e42fb1ad11",
    "scripts/aster-adaptive/sa4_effect_admission_v1.py":
        "16d6bba03357c90da29591513d3e39019400c36dbfe1a6d64f9aef85226c040b",
    "scripts/aster-adaptive/sa4_root_transaction_owner_v1.py":
        "e250bb2cf8bddf86634c973e968a787196ff0ae3fa7eaac10b2cd2d488404e3e",
    "scripts/aster-adaptive/sa4_runtime_control_owner_v1.py":
        "6d6e89d22829395373089c50eece2ffcdcc042c70c85a25a2f38867f2b330daa",
    "scripts/aster-adaptive/sa4_receipt_ledger_reconciler_v1.py":
        "9688ae6e6d50062a5b31e70bdec87d763d5b378ea681a35c07329f772cd669a1",
}
PLAN_SHA256 = "596417038ccef2ad49b689417437877820b2e918968dfd8a0eb97485c7eb6956"
TARGET_BEFORE_SHA256 = (
    "19b4e02d7f4edd9b38d9a0c3e9e3b49c4209473694fab39db0494c5fe523df1a")
TARGET_AFTER_SHA256 = (
    "4529dee5c9b58b607a9025b62aa3a4871660de98c4bafbb7fd69d7bc2a1e1065")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_static_evidence() -> None:
    for path, expected in SOURCES.items():
        if _sha256(ROOT / path) != expected:
            raise ValueError("SA4 post-install release source hash changed")
    if _sha256(UPGRADE_RESULT) != UPGRADE_RESULT_SHA256:
        raise ValueError("SA4 runtime-control installation result changed")
    result = upgrade_result.validate(UPGRADE_RESULT.read_bytes())
    if (result["result_sha256"] != UPGRADE_RESULT_SHA256
            or result["changes_validated"] != 2
            or result["inactive"] is not True
            or result["effect_authorized"] is not False
            or result["maximum_effects"] != 0
            or result["rollback_ready"] is not True
            or result["automatic_routing"] != "off"):
        raise ValueError("SA4 runtime-control installation is not inert and exact")


def packet() -> dict[str, object]:
    validate_static_evidence()
    return {
        "schema": "aster-sa4-first-repair-transaction-release.v4",
        "release_id": "sa4-canary-first-repair-root-owner-v4",
        "target_id": "sa4-lxc104-canary-adapter-v1",
        "plan_sha256": PLAN_SHA256,
        "target_before_sha256": TARGET_BEFORE_SHA256,
        "target_after_sha256": TARGET_AFTER_SHA256,
        "runtime_control_install_result_sha256": UPGRADE_RESULT_SHA256,
        "installed_source_sha256": dict(SOURCES),
        "required_fresh_authority": {
            "owner": "new-exact-plan-detached-proof",
            "ai_pam": "new-exact-plan-one-use-grant-and-proof",
            "grant_id": "new-unique-id-not-used-by-any-prior-ceremony",
            "deadline_intersection": True,
            "prior_approval_reusable": False,
        },
        "required_fresh_runtime": {
            "whole_host_lease": "ready-no-active-lease",
            "operation_lock": "owner-created-exclusively-at-runtime",
            "emergency_stop": "owner-created-plan-bound-at-runtime",
            "fresh_measurement": True,
            "exclusive_checkpoint": True,
            "one_use_ledger": "absent-then-created-and-claimed-once",
            "independent_postcheck": True,
            "production_postcheck": True,
            "installed_hash_recheck": True,
        },
        "transaction_limits": {
            "maximum_repairs": 1,
            "maximum_rollbacks": 1,
            "automatic_retry": False,
            "service_restart": False,
            "automatic_routing": "off",
        },
        "status": "release-candidate-awaiting-new-exact-repair-approval",
        "effect_authorized": False,
        "exclusions": [
            "other-targets", "credentials", "firewall", "network", "model",
            "service-restart", "shared-infrastructure", "automatic-promotion",
        ],
    }


def canonical_packet() -> bytes:
    return (json.dumps(packet(), sort_keys=True, separators=(",", ":"))
            + "\n").encode("utf-8")


def packet_sha256() -> str:
    return hashlib.sha256(canonical_packet()).hexdigest()


def validate_retained_packet() -> None:
    if RETAINED_PACKET.read_bytes() != canonical_packet():
        raise ValueError("SA4 retained post-install release packet changed")


validate_static_evidence()
