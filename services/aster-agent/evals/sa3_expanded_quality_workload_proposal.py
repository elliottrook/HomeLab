"""Fail-closed validator for the non-admitted SA3 Lab Hours proposal."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


WORKLOAD_ID = "sa3-expanded-source-quality-v1"
RUNTIME_FILES = {
    "sa3-expanded-source-quality-v1.json",
    "sa3_expanded_quality_packet.py",
    "sa3_expanded_quality_runner.py",
    "sa3_fair_scorer.py",
}
EXCLUDED = {
    "sa3-expanded-source-quality-keys-v1.json",
    "sa3-expanded-source-quality-independent-review-v1.json",
}


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate(proposal: object, root: Path) -> dict[str, object]:
    if not isinstance(proposal, dict) or proposal.get("schema_version") != 1:
        raise ValueError("proposal schema is invalid")
    if proposal.get("status") != "not-admitted" or proposal.get("workload_id") != WORKLOAD_ID:
        raise ValueError("proposal is admitted or has the wrong workload identity")
    runtime = proposal.get("runtime_files")
    if not isinstance(runtime, dict) or set(runtime) != RUNTIME_FILES:
        raise ValueError("runtime file set is not exact")
    for name, expected in runtime.items():
        if not isinstance(expected, str) or len(expected) != 64 or _sha(root / name) != expected:
            raise ValueError(f"runtime pin mismatch: {name}")
    if set(proposal.get("excluded_runtime_files", [])) != EXCLUDED:
        raise ValueError("answer keys or review receipt could enter runtime")

    execution = proposal.get("execution")
    if not isinstance(execution, dict) or execution != {
        "request_count": 20,
        "retry_count": 0,
        "per_request_timeout_seconds": 120,
        "workload_deadline_seconds": 2700,
        "minimum_booking_seconds": 3600,
        "recovery_reserve_seconds": 900,
        "temperature": 0,
        "max_tokens": 512,
        "tools": "none",
        "authority": "none",
        "effect": "none",
    }:
        raise ValueError("execution boundary is not exact")
    if execution["workload_deadline_seconds"] + execution["recovery_reserve_seconds"] > execution["minimum_booking_seconds"]:
        raise ValueError("booking cannot contain workload and recovery")

    admission = proposal.get("admission")
    required = {
        "authoritative_window_check_required",
        "exact_booking_required",
        "whole_host_lease_required",
        "shared_operation_lock_required",
        "immediate_pre_effect_recheck_required",
        "guardian_required",
        "production_restore_required",
    }
    if not isinstance(admission, dict) or set(admission) != required or not all(admission.values()):
        raise ValueError("admission or restoration gate is missing")

    result = proposal.get("result")
    if (not isinstance(result, dict)
            or result.get("packet_id") != WORKLOAD_ID
            or result.get("packet_sha256") != "d8c7945924a98bfae45522fd4ac9f377871db3243136b4a00617263cf44e9066"
            or result.get("root_custody_mode") != "0600"
            or result.get("maximum_bytes") != 262144
            or result.get("retain_predictions") is not True
            or result.get("retain_error_classes") is not True
            or result.get("model_blind_review_required_later") is not True
            or result.get("automatic_qualification") is not False):
        raise ValueError("result custody or qualification boundary is invalid")
    for field in ("routing_authorized", "repair_authorized", "model_change_authorized",
                  "restart_authorized", "schedule_authorized"):
        if proposal.get(field) is not False:
            raise ValueError(f"{field} must remain false")
    return {
        "workload_id": WORKLOAD_ID,
        "runtime_file_count": len(runtime),
        "request_count": execution["request_count"],
        "status": proposal["status"],
    }


def load_and_validate(path: Path) -> dict[str, object]:
    return validate(json.loads(path.read_text()), path.parent)
