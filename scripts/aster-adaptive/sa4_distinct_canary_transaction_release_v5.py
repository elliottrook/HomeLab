"""Release packet for the fresh unique-plan SA4 v8 transaction."""
from __future__ import annotations

import hashlib
from pathlib import Path

import sa4_distinct_canary_authority_packet_v4 as authority
import sa4_distinct_canary_plan_v2 as plan
import sa4_single_file_repair_contract_v1 as contract


ROOT = Path(__file__).parents[2]
RESULT = (ROOT / "docs/projects/AI Projects/evidence/"
          "SA4-unique-checkpoint-inactive-install-and-v7-reconciliation-2026-11-06.json")
INSTALLED = {
    "scripts/aster-adaptive/sa4_preclaim_failure_reconciler_v1.py":
        "dc3cc24e98550fbb8732dc89eaccfedb92ef980b5037d6e83939d027193a7a9c",
    "scripts/aster-adaptive/sa4_fixed_transaction_runner_v8.py":
        "8be3e587c4bbc787f21a7f34ae3ab2abae31829faf8862d581303ce75bd5fea6",
}


def packet() -> dict[str, object]:
    for path, digest in INSTALLED.items():
        if hashlib.sha256((ROOT / path).read_bytes()).hexdigest() != digest:
            raise ValueError("SA4 v5 release source changed")
    result_raw = RESULT.read_bytes()
    result = contract.decode_unique_json(result_raw)
    if (result.get("schema")
            != "aster-sa4-unique-checkpoint-install-and-reconciliation-result.v1"
            or result.get("repair_effects") != 0
            or result.get("v4_use_count") != 0
            or result.get("runtime_controls_absent") is not True
            or result.get("production_healthy") is not True):
        raise ValueError("SA4 v5 release predecessor result changed")
    return {
        "schema": "aster-sa4-distinct-canary-transaction-release.v5",
        "release_id": "sa4-canary-v2-fourth-repair-release-v1",
        "status": "release-candidate-awaiting-fresh-runtime-gates",
        "plan_sha256": plan.PLAN_SHA256,
        "plan_id": plan.PLAN_ID,
        "target_id": plan.TARGET_ID,
        "target_before_sha256": plan.BEFORE_SHA256,
        "target_after_sha256": plan.AFTER_SHA256,
        "predecessor_result_sha256": hashlib.sha256(result_raw).hexdigest(),
        "required_fresh_authority": {
            "grant_id": authority.GRANT_ID,
            "owner": "new-exact-plan-detached-proof",
            "ai_pam": "new-exact-plan-one-use-grant-and-proof",
            "deadline_intersection": True, "prior_approval_reusable": False,
        },
        "runtime_paths": {
            "input": "/var/lib/aster/sa4/transaction-input-v5",
            "evidence": "/var/lib/aster/sa4/transaction-evidence-v5",
            "ledger": "/var/lib/aster/sa4/one-use-ledger-v5",
            "operation_id": "sa4-canary-v2-fourth-operation-v1",
            "checkpoint": (
                "/var/lib/aster/sa4/checkpoints/"
                "sa4-canary-v2-second-repair-v1.original"),
        },
        "installed_source_sha256": INSTALLED,
        "required_fresh_runtime": {
            "installed_hash_recheck": True, "fresh_measurement": True,
            "exclusive_checkpoint": True,
            "one_use_ledger": "fresh-v5-absent-then-created-and-claimed-once",
            "operation_lock": "owner-created-exclusively-at-runtime",
            "emergency_stop": "owner-created-plan-bound-at-runtime",
            "observer_exchange": "fixed-controller-bridge-protocol",
            "whole_host_lease": "ready-no-active-lease",
            "production_postcheck": True,
        },
        "transaction_limits": {
            "maximum_repairs": 1, "maximum_rollbacks": 1,
            "observer_signatures_success": 1,
            "observer_signatures_rollback": 2,
            "automatic_retry": False, "automatic_routing": "off",
            "service_restart": False,
        },
        "effect_authorized": False,
        "exclusions": [
            "other-targets", "credentials", "firewall", "network", "model",
            "service-restart", "shared-infrastructure", "automatic-promotion",
        ],
    }


def canonical() -> bytes:
    return contract.canonical(packet())


packet()
