"""No-authority release candidate for the corrected fresh-path SA4 canary."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import sa4_distinct_canary_authority_packet_v2 as authority_source
import sa4_distinct_canary_plan_v1 as plan_source
import sa4_fresh_path_runner_inactive_install_result_v1 as result_validator


ROOT = Path(__file__).parents[2]
RESULT = ROOT / (
    "docs/projects/AI Projects/evidence/"
    "SA4-fresh-path-runner-inactive-install-result-2026-11-06.json")
RESULT_SHA256 = (
    "6ea88d231fe89d35a437746682af89245cfa17947e5e8b5e069fe0de889eccbc")
RETAINED = ROOT / (
    "docs/projects/AI Projects/evidence/"
    "SA4-distinct-canary-v3-transaction-release-2026-11-06.json")
INSTALLED_SOURCES = {
    "scripts/aster-adaptive/sa4_distinct_registry_bindings_v1.py":
        "c88640a32fb9a413afcd01e2dcdadcb4a5fc68f0bdd99a59e976aa5f83476330",
    "scripts/aster-adaptive/sa4_root_transaction_owner_v5.py":
        "a4fd70730a9e752e12430c1ab2179eb0c876118ab839c946850dd3377df6167a",
    "scripts/aster-adaptive/sa4_fixed_transaction_runner_v6.py":
        "a91d6a34ac251970a9d83452e085cbc4d0a51adaf065ec75d6879e122b38a397",
}
RELEASE_SOURCES = {
    "scripts/aster-adaptive/sa4_fresh_path_runner_inactive_install_plan_v1.py":
        "a4a1e5b7d20e4fcde22c7a0d17d7677e68e4a53faf2840c1376634ca20e23085",
    "scripts/aster-adaptive/sa4_fresh_path_runner_inactive_install_result_v1.py":
        "240254fe3fe325f3f45a1140419e6b6f41e474605fd8104a39c255cf9eb9c234",
    "scripts/aster-adaptive/sa4_distinct_canary_plan_v1.py":
        "8b9561145f78dbdf77356b6b43ca201e416b498f02614c703c82216a62840dd1",
    "scripts/aster-adaptive/sa4_distinct_canary_authority_packet_v2.py":
        "0b398ad8069be029dc8d550995520500f1951c6bb2e549a156a0362faeeb58fc",
}


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_static_evidence() -> None:
    for path, expected in {**INSTALLED_SOURCES, **RELEASE_SOURCES}.items():
        if _sha(ROOT / path) != expected:
            raise ValueError("SA4 distinct-canary v3 release source changed")
    raw = RESULT.read_bytes()
    if _sha(RESULT) != RESULT_SHA256:
        raise ValueError("SA4 distinct-canary v3 installation result changed")
    value = result_validator.validate(raw)
    if value["inactive"] is not True or value["repair_authorized"] is not False:
        raise ValueError("SA4 distinct-canary v3 installation is not inert")


def packet() -> dict[str, object]:
    validate_static_evidence()
    return {
        "schema": "aster-sa4-distinct-canary-transaction-release.v3",
        "release_id": "sa4-canary-v2-second-repair-release-v1",
        "target_id": plan_source.TARGET_ID,
        "plan_sha256": plan_source.PLAN_SHA256,
        "target_before_sha256": plan_source.BEFORE_SHA256,
        "target_after_sha256": plan_source.AFTER_SHA256,
        "inactive_install_result_sha256": RESULT_SHA256,
        "installed_source_sha256": dict(INSTALLED_SOURCES),
        "release_source_sha256": dict(RELEASE_SOURCES),
        "failed_predecessor": {
            "grant_id": "sa4-canary-v2-first-grant-v1-20261106",
            "attempt_result": "pre-effect-no-go",
            "grant_claimed": False,
            "reusable": False,
            "retained_paths": [
                "/var/lib/aster/sa4/transaction-input-v2",
                "/var/lib/aster/sa4/transaction-evidence-v2",
            ],
        },
        "required_fresh_authority": {
            "owner": "new-exact-plan-detached-proof",
            "ai_pam": "new-exact-plan-one-use-grant-and-proof",
            "grant_id": authority_source.GRANT_ID,
            "prior_approval_reusable": False,
            "deadline_intersection": True,
        },
        "required_fresh_runtime": {
            "whole_host_lease": "ready-no-active-lease",
            "operation_lock": "owner-created-exclusively-at-runtime",
            "emergency_stop": "owner-created-plan-bound-at-runtime",
            "fresh_measurement": True,
            "exclusive_checkpoint": True,
            "one_use_ledger": "fresh-v3-absent-then-created-and-claimed-once",
            "observer_exchange": "fixed-controller-bridge-protocol",
            "installed_hash_recheck": True,
            "production_postcheck": True,
        },
        "runtime_paths": {
            "input": "/var/lib/aster/sa4/transaction-input-v3",
            "evidence": "/var/lib/aster/sa4/transaction-evidence-v3",
            "ledger": "/var/lib/aster/sa4/one-use-ledger-v3",
            "operation_id": "sa4-canary-v2-second-operation-v1",
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
        raise ValueError("SA4 distinct-canary v3 retained release changed")


validate_static_evidence()
