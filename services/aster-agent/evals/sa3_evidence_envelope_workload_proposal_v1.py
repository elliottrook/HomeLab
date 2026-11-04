"""Validate candidate-g's exact non-admitted Lab Hours proposal."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


WORKLOAD_ID = "sa3-evidence-envelope-quality-v1"
RUNTIME_FILES = {
    "sa3-evidence-envelope-quality-v1.json": "a01c6d71dce91141f2eae9bad21a56641f6aa269cdc3561a165385d210e3ec2a",
    "sa3_deterministic_evidence_envelope_v1.py": "9f8b14f8f1a4d162eed03f39e82b868118b0c5bdcb3a7fce744a28e9d13e3da3",
    "sa3_evidence_envelope_batch_v1.py": "78abc29951fe80a469c49ee44af6a9380f032648ad757f3182c11bd0f0464500",
    "sa3_evidence_envelope_quality_freeze_v1.py": "95cf006fc7e3b2aeb3acf0e926336e65e3c3a8b5e5f8cb5cc083e4e5ab7b3483",
    "sa3_evidence_envelope_runner_v1.py": "372c19ef3c2f5e8f0965167011c4bba47d9326e5f5ffe7d0b77d9ac5898fc352",
}
EXCLUDED = {
    "sa3-evidence-envelope-quality-keys-v1.json",
    "sa3_evidence_envelope_blind_review_v1.py",
}


def validate(value: object, root: Path) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != {
        "schema", "status", "workload_id", "owner", "candidate_alias",
        "runtime_files", "excluded_runtime_files", "execution", "admission",
        "result", "effect_authorized", "repair_authorized",
        "automatic_routing_authorized", "model_change_authorized",
        "model_promotion_authorized", "restart_authorized", "schedule_authorized",
    }:
        raise ValueError("candidate-g proposal fields differ")
    if (value["schema"] != "aster-sa3-evidence-envelope-workload-proposal.v1"
            or value["status"] != "not-admitted"
            or value["workload_id"] != WORKLOAD_ID
            or value["owner"] != "aster-stream-a"
            or value["candidate_alias"] != "candidate-g"
            or value["runtime_files"] != RUNTIME_FILES
            or set(value["excluded_runtime_files"]) != EXCLUDED):
        raise ValueError("candidate-g proposal identity differs")
    for name, expected in RUNTIME_FILES.items():
        path = root / name
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"candidate-g runtime source missing: {name}")
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError(f"candidate-g runtime source changed: {name}")
    execution = value["execution"]
    if execution != {
        "case_count": 20, "model_request_count": 14, "retry_count": 0,
        "per_request_timeout_seconds": 120, "workload_deadline_seconds": 2700,
        "minimum_booking_seconds": 3600, "recovery_reserve_seconds": 900,
        "temperature": 0, "max_tokens": 384, "tools": "none",
        "authority": "none", "effect": "none",
    }:
        raise ValueError("candidate-g execution boundary differs")
    if (execution["workload_deadline_seconds"] + execution["recovery_reserve_seconds"]
            > execution["minimum_booking_seconds"]):
        raise ValueError("candidate-g booking lacks recovery reserve")
    required_admission = {
        "authoritative_window_check_required", "exact_booking_required",
        "whole_host_lease_required", "shared_operation_lock_required",
        "immediate_pre_effect_recheck_required", "guardian_required",
        "production_restore_required",
    }
    if (not isinstance(value["admission"], dict)
            or set(value["admission"]) != required_admission
            or not all(value["admission"].values())):
        raise ValueError("candidate-g admission boundary differs")
    result = value["result"]
    if result != {
        "schema": "aster-sa3-evidence-envelope-result.v1",
        "packet_id": WORKLOAD_ID,
        "packet_sha256": RUNTIME_FILES["sa3-evidence-envelope-quality-v1.json"],
        "root_custody_mode": "0600", "maximum_bytes": 524288,
        "retain_predictions": True, "retain_error_classes": True,
        "model_blind_review_required_later": True,
        "automatic_qualification": False,
    }:
        raise ValueError("candidate-g result boundary differs")
    denied = {
        "effect_authorized", "repair_authorized", "automatic_routing_authorized",
        "model_change_authorized", "model_promotion_authorized",
        "restart_authorized", "schedule_authorized",
    }
    if any(value[field] is not False for field in denied):
        raise ValueError("candidate-g proposal attempts to grant authority")
    return {
        "schema": value["schema"], "workload_id": WORKLOAD_ID,
        "runtime_file_count": len(RUNTIME_FILES), "model_request_count": 14,
        "status": "not-admitted", "authority": "none",
    }


def load_and_validate(path: Path) -> dict[str, object]:
    return validate(json.loads(path.read_text()), path.parent)
