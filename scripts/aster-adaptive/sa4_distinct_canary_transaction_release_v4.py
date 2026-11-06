"""No-authority release candidate with corrected v2 postchecks."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import sa4_distinct_canary_authority_packet_v3 as authority_source
import sa4_distinct_canary_plan_v1 as plan_source
import sa4_postcheck_lineage_inactive_install_result_v1 as result_validator


ROOT = Path(__file__).parents[2]
RESULT = ROOT / ("docs/projects/AI Projects/evidence/"
                 "SA4-postcheck-lineage-inactive-install-result-2026-11-06.json")
RESULT_SHA256 = "a81d8303bd87a232efa93ee70f3820beb1cf7e2ad17df6de03d663d89cc92e5a"
RETAINED = ROOT / ("docs/projects/AI Projects/evidence/"
                   "SA4-distinct-canary-v4-transaction-release-2026-11-06.json")
INSTALLED_SOURCES = {
    "scripts/aster-adaptive/sa4_canary_v2_target_bytes_check_v1.py":
        "74ee440c6f7617c726c634fd79ccfaf0e5d3df77cba4ba1b0aafcb78a64b0e06",
    "scripts/aster-adaptive/sa4_canary_v2_target_metadata_check_v1.py":
        "23fb5ac611c0e7e04ab672c0ab17eb86c92e4a9c9e334b6879d56066ae395fea",
    "scripts/aster-adaptive/sa4_canary_v2_consumer_health_check_v1.py":
        "4b792ff436a605a699dac3b73d4eb319b22ca4302ccf83ad3904379ba7fb4b28",
    "scripts/aster-adaptive/sa4_target_registry_v3.py":
        "35e7f680a10d4936ba246cd51e844d9cacbf47c6bda018ab27a88295ad304857",
    "scripts/aster-adaptive/sa4_distinct_postcheck_receipt_producer_v1.py":
        "96fa810011429f8da9fc1208a60471d745c452ed1ea9186552abf1ac4edeab29",
    "scripts/aster-adaptive/sa4_distinct_registry_bindings_v2.py":
        "b40a9b657cb3f1b9087d5621fb96e11735bb578c06bbfdea3fd342cdd8baa370",
    "scripts/aster-adaptive/sa4_root_transaction_owner_v6.py":
        "74ebd4e13137646dfff7a608bb3a9bb77050639968eaac321a15e7fb126dbd6f",
    "scripts/aster-adaptive/sa4_fixed_transaction_runner_v7.py":
        "8b3f030b06d2cb677a5a106ee3a4a8f4ca27360ad19403bd927dc672dd7c322d",
}
RELEASE_SOURCES = {
    "scripts/aster-adaptive/sa4_postcheck_lineage_inactive_install_plan_v1.py":
        "639c10f902580db3704e8bec7b222288484040da292500a1cb57b6697d9d5db7",
    "scripts/aster-adaptive/sa4_postcheck_lineage_inactive_install_result_v1.py":
        "91b7f7e888c0e6c064bc546ef7e742a941953b94481d2daa940a8adaca7f76c6",
    "scripts/aster-adaptive/sa4_distinct_canary_plan_v1.py":
        "8b9561145f78dbdf77356b6b43ca201e416b498f02614c703c82216a62840dd1",
    "scripts/aster-adaptive/sa4_distinct_canary_authority_packet_v3.py":
        "4c50f02cd2f6124602be6ba7cd15bbb574e3657faaafd40776cb8437d8afd284",
}


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_static_evidence() -> None:
    for path, expected in {**INSTALLED_SOURCES, **RELEASE_SOURCES}.items():
        if _sha(ROOT / path) != expected:
            raise ValueError("SA4 distinct-canary v4 release source changed")
    raw = RESULT.read_bytes()
    if _sha(RESULT) != RESULT_SHA256:
        raise ValueError("SA4 distinct-canary v4 installation result changed")
    value = result_validator.validate(raw)
    if value["inactive"] is not True or value["repair_authorized"] is not False:
        raise ValueError("SA4 distinct-canary v4 installation is not inert")


def packet() -> dict[str, object]:
    validate_static_evidence()
    return {
        "schema": "aster-sa4-distinct-canary-transaction-release.v4",
        "release_id": "sa4-canary-v2-third-repair-release-v1",
        "target_id": plan_source.TARGET_ID,
        "plan_sha256": plan_source.PLAN_SHA256,
        "target_before_sha256": plan_source.BEFORE_SHA256,
        "target_after_sha256": plan_source.AFTER_SHA256,
        "inactive_install_result_sha256": RESULT_SHA256,
        "installed_source_sha256": dict(INSTALLED_SOURCES),
        "release_source_sha256": dict(RELEASE_SOURCES),
        "failed_predecessors": [
            {"grant_id": "sa4-canary-v2-first-grant-v1-20261106",
             "result": "pre-effect-no-go", "reusable": False},
            {"grant_id": "sa4-canary-v2-second-grant-v1-20261106",
             "result": "postcheck-failed-rollback-complete", "reusable": False},
        ],
        "required_fresh_authority": {
            "owner": "new-exact-plan-detached-proof",
            "ai_pam": "new-exact-plan-one-use-grant-and-proof",
            "grant_id": authority_source.GRANT_ID,
            "prior_approval_reusable": False, "deadline_intersection": True,
        },
        "required_fresh_runtime": {
            "whole_host_lease": "ready-no-active-lease",
            "operation_lock": "owner-created-exclusively-at-runtime",
            "emergency_stop": "owner-created-plan-bound-at-runtime",
            "fresh_measurement": True, "exclusive_checkpoint": True,
            "one_use_ledger": "fresh-v4-absent-then-created-and-claimed-once",
            "observer_exchange": "fixed-controller-bridge-protocol",
            "installed_hash_recheck": True, "production_postcheck": True,
        },
        "runtime_paths": {
            "input": "/var/lib/aster/sa4/transaction-input-v4",
            "evidence": "/var/lib/aster/sa4/transaction-evidence-v4",
            "ledger": "/var/lib/aster/sa4/one-use-ledger-v4",
            "operation_id": "sa4-canary-v2-third-operation-v1",
        },
        "transaction_limits": {
            "maximum_repairs": 1, "maximum_rollbacks": 1,
            "observer_signatures_success": 1, "observer_signatures_rollback": 2,
            "automatic_retry": False, "service_restart": False,
            "automatic_routing": "off",
        },
        "status": "release-candidate-awaiting-fresh-runtime-gates",
        "effect_authorized": False,
        "exclusions": ["other-targets", "credentials", "firewall", "network",
                       "model", "service-restart", "shared-infrastructure",
                       "automatic-promotion"],
    }


def canonical_packet() -> bytes:
    return (json.dumps(packet(), sort_keys=True, separators=(",", ":")) + "\n").encode()


def packet_sha256() -> str:
    return hashlib.sha256(canonical_packet()).hexdigest()


def validate_retained_packet() -> None:
    if RETAINED.read_bytes() != canonical_packet():
        raise ValueError("SA4 distinct-canary v4 retained release changed")


validate_static_evidence()
