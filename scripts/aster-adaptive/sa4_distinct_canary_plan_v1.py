"""Exact no-authority repair plan for the accepted distinct SA4 canary."""
from __future__ import annotations

import sa4_distinct_registry_bindings_v1 as bindings
import sa4_single_file_repair_contract_v1 as contract
import sa4_target_registry_v2 as registry


TARGET_ID = bindings.TARGET_ID
BEFORE_SHA256 = (
    "a9831e6295abd632ad0646b38a253fce71c29f76850d918d1761685c40824da0")
AFTER_SHA256 = (
    "fae178a1558199b66f4dc9abec18690ed22a7cbee398f411b47f93daf1d3a0c2")


def build_plan() -> bytes:
    target = registry.resolve_production(TARGET_ID)
    value = {
        "schema": "aster-sa4-single-file-repair-plan.v1",
        "plan_id": "sa4-canary-v2-first-repair-v1",
        "target_id": target.target_id,
        "candidate_release_sha256": AFTER_SHA256,
        "repair_class": "single-file-configuration-drift",
        "target": {
            "host_id": target.host_id, "path": target.path,
            "type": "regular-file", "follow_symlinks": False,
            "owner": target.owner, "group": target.group, "mode": target.mode,
        },
        "precondition": {
            "expected_sha256": BEFORE_SHA256,
            "observed_mode": target.mode,
            "service_restart_required": False,
        },
        "change": {
            "artifact_sha256": AFTER_SHA256,
            "method": "atomic-replace-no-follow",
            "temporary_same_filesystem": True,
        },
        "checkpoint": {
            "required": True, "immutable_copy_required": True,
            "digest_required": True,
        },
        "postchecks": list(contract.POSTCHECKS),
        "rollback": {
            "method": "atomic-restore-checkpoint-no-follow",
            "trigger": "any-failed-or-uncertain-postcheck",
            "verify_digest": True,
        },
        "uncertainty": {
            "automatic_retry": False, "preserve_evidence": True,
            "outcome": "stop-and-reconcile",
        },
        "exclusions": list(contract.EXCLUSIONS),
        "authority": "none", "effect_authorized": False,
        "automatic_routing": "off",
    }
    raw = contract.canonical(value)
    with bindings.accepted_registry(raw):
        contract.validate_plan(raw)
    return raw


PLAN_SHA256 = contract.sha256(build_plan())

