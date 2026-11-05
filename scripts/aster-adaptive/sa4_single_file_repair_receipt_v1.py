"""Reconcile one bounded SA4 repair without inferring uncertain success."""
from __future__ import annotations

import hashlib
import re

import sa4_single_file_repair_contract_v1 as contract
from nlu_threshold_policy import decode_unique_json


HEX64 = re.compile(r"[0-9a-f]{64}")
CHECKS = frozenset(contract.POSTCHECKS)


def reconcile(plan_raw: bytes, admission_raw: bytes,
              terminal_raw: bytes) -> dict[str, object]:
    plan = contract.validate_plan(plan_raw)
    admission = decode_unique_json(admission_raw)
    terminal = decode_unique_json(terminal_raw)
    admission_fields = {"schema", "plan_sha256", "plan_id",
                        "target_before_sha256", "target_after_sha256",
                        "checkpoint_sha256", "approval_expires_epoch",
                        "grant_expires_epoch", "maximum_effects",
                        "preflight_eligible", "automatic_retry",
                        "automatic_routing"}
    terminal_fields = {"schema", "plan_sha256", "admission_sha256", "state",
                       "effect_count", "retry_count", "precondition_sha256",
                       "observed_after_sha256", "checkpoint_sha256",
                       "postchecks", "rollback_performed", "final_target_sha256",
                       "evidence_retained", "authority", "automatic_routing"}
    plan_digest = hashlib.sha256(plan_raw).hexdigest()
    admission_digest = hashlib.sha256(admission_raw).hexdigest()
    if (not isinstance(admission, dict) or set(admission) != admission_fields
            or admission["schema"] != "aster-sa4-single-file-repair-admission.v1"
            or admission["plan_sha256"] != plan_digest
            or admission["plan_id"] != plan["plan_id"]
            or admission["target_before_sha256"]
            != plan["precondition"]["expected_sha256"]
            or admission["target_after_sha256"] != plan["change"]["artifact_sha256"]
            or not isinstance(admission["checkpoint_sha256"], str)
            or not HEX64.fullmatch(admission["checkpoint_sha256"])
            or admission["maximum_effects"] != 1
            or admission["preflight_eligible"] is not True
            or admission["automatic_retry"] is not False
            or admission["automatic_routing"] != "off"):
        raise ValueError("SA4 repair admission changed")
    if (not isinstance(terminal, dict) or set(terminal) != terminal_fields
            or terminal["schema"] != "aster-sa4-single-file-repair-terminal.v1"
            or terminal["plan_sha256"] != plan_digest
            or terminal["admission_sha256"] != admission_digest
            or terminal["state"] not in {"complete", "no_go", "rolled_back", "uncertain"}
            or terminal["effect_count"] not in {0, 1}
            or terminal["retry_count"] != 0
            or terminal["precondition_sha256"]
            != plan["precondition"]["expected_sha256"]
            or terminal["checkpoint_sha256"] != admission["checkpoint_sha256"]
            or not isinstance(terminal["observed_after_sha256"], str)
            or not HEX64.fullmatch(terminal["observed_after_sha256"])
            or not isinstance(terminal["final_target_sha256"], str)
            or not HEX64.fullmatch(terminal["final_target_sha256"])
            or not isinstance(terminal["postchecks"], dict)
            or set(terminal["postchecks"]) != CHECKS
            or any(value not in {True, False, "not-run", "uncertain"}
                   for value in terminal["postchecks"].values())
            or type(terminal["rollback_performed"]) is not bool
            or terminal["evidence_retained"] is not True
            or terminal["authority"] != "one-use-consumed"
            or terminal["automatic_routing"] != "off"):
        raise ValueError("SA4 repair terminal changed")
    before = plan["precondition"]["expected_sha256"]
    after = plan["change"]["artifact_sha256"]
    checks = list(terminal["postchecks"].values())
    state = terminal["state"]
    valid = (
        state == "complete" and terminal["effect_count"] == 1
        and terminal["observed_after_sha256"] == after
        and terminal["final_target_sha256"] == after
        and checks == [True, True, True]
        and terminal["rollback_performed"] is False
    ) or (
        state == "no_go" and terminal["effect_count"] == 0
        and terminal["observed_after_sha256"] == before
        and terminal["final_target_sha256"] == before
        and all(value == "not-run" for value in checks)
        and terminal["rollback_performed"] is False
    ) or (
        state == "rolled_back" and terminal["effect_count"] == 1
        and terminal["final_target_sha256"] == before
        and terminal["rollback_performed"] is True
        and not all(value is True for value in checks)
    ) or (
        state == "uncertain" and terminal["final_target_sha256"] in {before, after}
        and not all(value is True for value in checks)
    )
    if not valid:
        raise ValueError("SA4 repair outcome is internally inconsistent")
    return {"schema": "aster-sa4-single-file-repair-reconciliation.v1",
            "plan_sha256": plan_digest, "admission_sha256": admission_digest,
            "terminal_sha256": hashlib.sha256(terminal_raw).hexdigest(),
            "state": state, "effect_count": terminal["effect_count"],
            "rollback_performed": terminal["rollback_performed"],
            "final_target_sha256": terminal["final_target_sha256"],
            "postchecks_complete": all(value is True for value in checks),
            "evidence_retained": True,
            "completion_accepted": state == "complete",
            "manual_reconciliation_required": state == "uncertain",
            "automatic_retry": False, "automatic_routing": "off"}
