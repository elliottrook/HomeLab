"""No-authority release candidate for the corrected distinct SA4 canary."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import sa4_distinct_canary_plan_v1 as plan_source
import sa4_distinct_registry_fix_inactive_install_result_v1 as result_validator


ROOT = Path(__file__).parents[2]
RESULT = ROOT / (
    "docs/projects/AI Projects/evidence/"
    "SA4-distinct-registry-fix-inactive-install-result-2026-11-06.json")
RESULT_SHA256 = (
    "ce44e3abf21695bdc0d2b63266ac85af7db6b1ed42d2bea6097e516a87021a02")
RETAINED = ROOT / (
    "docs/projects/AI Projects/evidence/"
    "SA4-distinct-canary-v2-transaction-release-2026-11-06.json")
INSTALLED_SOURCES = {
    "scripts/aster-adaptive/sa4_distinct_registry_bindings_v1.py":
        "c88640a32fb9a413afcd01e2dcdadcb4a5fc68f0bdd99a59e976aa5f83476330",
    "scripts/aster-adaptive/sa4_root_transaction_owner_v4.py":
        "9da52be5fba3d9a5c628e94a887f034944d6a75f31bf8dbb86471005ff5453e6",
    "scripts/aster-adaptive/sa4_fixed_transaction_runner_v4.py":
        "ab2c67cd1640cbb60b3da89aadc9f90ee34132873295f8736f10ed0af3b79d0f",
}
RELEASE_SOURCES = {
    "scripts/aster-adaptive/sa4_distinct_registry_fix_inactive_install_plan_v1.py":
        "5323cea8d3190d761cd2c60f0a293bc815db1c9e0ffea2215234e0ffc981e8f3",
    "scripts/aster-adaptive/sa4_distinct_registry_fix_inactive_install_result_v1.py":
        "52e1933482f234c9098ae48149f54da35a7ab20e0e531d8c05c1cdf09110e419",
    "scripts/aster-adaptive/sa4_distinct_canary_plan_v1.py":
        "8b9561145f78dbdf77356b6b43ca201e416b498f02614c703c82216a62840dd1",
    "scripts/aster-adaptive/sa4_distinct_canary_authority_packet_v1.py":
        "8885ed19bce7e89b2b32ee1a5b9926dccfef4ddbc656586716672fee35138e0c",
}
GRANT_ID = "sa4-canary-v2-first-grant-v1-20261106"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_static_evidence() -> None:
    for path, expected in {**INSTALLED_SOURCES, **RELEASE_SOURCES}.items():
        if _sha(ROOT / path) != expected:
            raise ValueError("SA4 distinct-canary v2 release source changed")
    raw = RESULT.read_bytes()
    if _sha(RESULT) != RESULT_SHA256:
        raise ValueError("SA4 distinct-canary v2 installation result changed")
    value = result_validator.validate(raw)
    if value["inactive"] is not True or value["repair_authorized"] is not False:
        raise ValueError("SA4 distinct-canary v2 installation is not inert")


def packet() -> dict[str, object]:
    validate_static_evidence()
    return {
        "schema": "aster-sa4-distinct-canary-transaction-release.v2",
        "release_id": "sa4-canary-v2-first-repair-release-v1",
        "target_id": plan_source.TARGET_ID,
        "plan_sha256": plan_source.PLAN_SHA256,
        "target_before_sha256": plan_source.BEFORE_SHA256,
        "target_after_sha256": plan_source.AFTER_SHA256,
        "inactive_install_result_sha256": RESULT_SHA256,
        "installed_source_sha256": dict(INSTALLED_SOURCES),
        "release_source_sha256": dict(RELEASE_SOURCES),
        "required_fresh_authority": {
            "owner": "new-exact-plan-detached-proof",
            "ai_pam": "new-exact-plan-one-use-grant-and-proof",
            "grant_id": GRANT_ID,
            "prior_approval_reusable": False,
            "deadline_intersection": True,
        },
        "required_fresh_runtime": {
            "whole_host_lease": "ready-no-active-lease",
            "operation_lock": "owner-created-exclusively-at-runtime",
            "emergency_stop": "owner-created-plan-bound-at-runtime",
            "fresh_measurement": True,
            "exclusive_checkpoint": True,
            "one_use_ledger": "absent-then-created-and-claimed-once",
            "observer_exchange": "fixed-controller-bridge-protocol",
            "installed_hash_recheck": True,
            "production_postcheck": True,
        },
        "runtime_paths": {
            "input": "/var/lib/aster/sa4/transaction-input-v2",
            "evidence": "/var/lib/aster/sa4/transaction-evidence-v2",
            "ledger": "/var/lib/aster/sa4/one-use-ledger-v2",
            "operation_id": "sa4-canary-v2-first-operation-v1",
        },
        "transaction_limits": {
            "maximum_repairs": 1, "maximum_rollbacks": 1,
            "observer_signatures_success": 1,
            "observer_signatures_rollback": 2,
            "automatic_retry": False, "service_restart": False,
            "automatic_routing": "off",
        },
        "status": "release-candidate-awaiting-exact-repair-approval",
        "effect_authorized": False,
        "exclusions": [
            "other-targets", "credentials", "firewall", "network", "model",
            "service-restart", "shared-infrastructure", "automatic-promotion",
        ],
    }


def canonical_packet() -> bytes:
    return (json.dumps(packet(), sort_keys=True, separators=(",", ":"))
            + "\n").encode()


def packet_sha256() -> str:
    return hashlib.sha256(canonical_packet()).hexdigest()


def validate_retained_packet() -> None:
    if RETAINED.read_bytes() != canonical_packet():
        raise ValueError("SA4 distinct-canary v2 retained release changed")


validate_static_evidence()

