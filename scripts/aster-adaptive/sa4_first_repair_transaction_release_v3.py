"""Corrected no-authority SA4 release after runtime-control NO-GO."""
from __future__ import annotations

import hashlib
from pathlib import Path


ROOT = Path(__file__).parents[2]
SOURCES = {
    "scripts/aster-adaptive/sa4_root_transaction_owner_v1.py":
        "e250bb2cf8bddf86634c973e968a787196ff0ae3fa7eaac10b2cd2d488404e3e",
    "scripts/aster-adaptive/sa4_runtime_control_owner_v1.py":
        "6d6e89d22829395373089c50eece2ffcdcc042c70c85a25a2f38867f2b330daa",
}
INSTALLED_ROOT_OWNER_SHA256 = (
    "d8a6d69a7780e37d483cdc857859314f1613d8ddad56de3c78e46623ea041c39")
PLAN_SHA256 = "596417038ccef2ad49b689417437877820b2e918968dfd8a0eb97485c7eb6956"


def validate_sources() -> None:
    for path, expected in SOURCES.items():
        if hashlib.sha256((ROOT / path).read_bytes()).hexdigest() != expected:
            raise ValueError("SA4 corrected release source hash changed")


def packet() -> dict[str, object]:
    validate_sources()
    return {
        "schema": "aster-sa4-first-repair-transaction-release.v3",
        "release_id": "sa4-canary-first-repair-root-owner-v3",
        "plan_sha256": PLAN_SHA256,
        "runtime_control_correction": {
            "root_owner_before_sha256": INSTALLED_ROOT_OWNER_SHA256,
            "root_owner_after_sha256": SOURCES[
                "scripts/aster-adaptive/sa4_root_transaction_owner_v1.py"],
            "runtime_owner_before": "absent",
            "runtime_owner_after_sha256": SOURCES[
                "scripts/aster-adaptive/sa4_runtime_control_owner_v1.py"],
            "real_lock_owned": True, "operator_stop_owned": True,
            "caller_supplied_control_claim_rejected": True,
            "uncertainty_retains_state": True},
        "transaction_limits": {"maximum_repairs": 1,
                               "maximum_rollbacks": 1,
                               "automatic_retry": False,
                               "service_restart": False,
                               "automatic_routing": "off"},
        "status": "candidate-pending-inactive-runtime-control-install",
        "effect_authorized": False,
        "exclusions": ["no-authority", "no-signature", "no-ledger-claim",
                       "no-checkpoint", "no-repair", "no-service-action",
                       "no-automatic-promotion"]}


validate_sources()
