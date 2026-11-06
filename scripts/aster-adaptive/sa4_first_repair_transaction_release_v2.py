"""Frozen no-authority release packet for the first root-owned SA4 repair."""
from __future__ import annotations

import hashlib
from pathlib import Path

ROOT = Path(__file__).parents[2]
SOURCES = {
    "scripts/aster-adaptive/sa4_preflight_composition_v1.py":
        "a38ccb0b33bbc828f7ae96fd68304776cd840ea49bb07986044383e42fb1ad11",
    "scripts/aster-adaptive/sa4_effect_admission_v1.py":
        "16d6bba03357c90da29591513d3e39019400c36dbfe1a6d64f9aef85226c040b",
    "scripts/aster-adaptive/sa4_root_transaction_owner_v1.py":
        "d8a6d69a7780e37d483cdc857859314f1613d8ddad56de3c78e46623ea041c39",
    "scripts/aster-adaptive/sa4_receipt_ledger_reconciler_v1.py":
        "9688ae6e6d50062a5b31e70bdec87d763d5b378ea681a35c07329f772cd669a1",
}
INSTALL_RESULT_SHA256 = (
    "1a4fe00593c4590d15aaf69a9a2dfacde3b1404133bcaa1b989f3937c5e548ff")
PLAN_SHA256 = "596417038ccef2ad49b689417437877820b2e918968dfd8a0eb97485c7eb6956"
TARGET_BEFORE_SHA256 = (
    "19b4e02d7f4edd9b38d9a0c3e9e3b49c4209473694fab39db0494c5fe523df1a")
TARGET_AFTER_SHA256 = (
    "4529dee5c9b58b607a9025b62aa3a4871660de98c4bafbb7fd69d7bc2a1e1065")


def validate_sources() -> None:
    for path, expected in SOURCES.items():
        if hashlib.sha256((ROOT / path).read_bytes()).hexdigest() != expected:
            raise ValueError("SA4 first-repair source hash changed")


def packet() -> dict[str, object]:
    validate_sources()
    return {
        "schema": "aster-sa4-first-repair-transaction-release.v2",
        "release_id": "sa4-canary-first-repair-root-owner-v2",
        "target_id": "sa4-lxc104-canary-adapter-v1",
        "plan_sha256": PLAN_SHA256,
        "target_before_sha256": TARGET_BEFORE_SHA256,
        "target_after_sha256": TARGET_AFTER_SHA256,
        "installed_result_sha256": INSTALL_RESULT_SHA256,
        "installed_source_sha256": dict(SOURCES),
        "required_runtime": {
            "root_transaction_owner": "single-in-memory-owner",
            "whole_host_lease": "ready-no-active-lease",
            "shared_operation_lock": "/run/aster-sa4-operation.lock",
            "emergency_stop": "armed-and-plan-bound",
            "fresh_measurement": True, "exclusive_checkpoint": True,
            "one_use_ledger": "ready-then-claimed-once",
            "independent_observer_signing": True,
            "production_postcheck": True},
        "required_fresh_authority": {
            "owner": "new-exact-plan-detached-proof",
            "ai_pam": "new-exact-plan-one-use-grant-and-proof",
            "grant_id": "must-not-reuse-prior-ceremony-grant",
            "deadline_intersection": True},
        "transaction_limits": {
            "maximum_repairs": 1, "maximum_rollbacks": 1,
            "automatic_retry": False, "service_restart": False,
            "automatic_routing": "off"},
        "status": "release-candidate-pending-exact-effect-approval",
        "effect_authorized": False,
        "exclusions": ["credentials", "firewall", "network", "model",
                       "service-restart", "shared-infrastructure",
                       "automatic-promotion"]}


validate_sources()
