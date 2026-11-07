"""Score fixed K2 M7/SA5 operational evidence without authorizing release."""
from __future__ import annotations

import hashlib
import math
import re

from nlu_threshold_policy import decode_unique_json


ATTEMPT_ID = re.compile(r"k2-readonly-(?:normal|recovery)-[0-9a-f]{16}\Z")
BOOKING_ID = re.compile(
    r"aster-stream-a-m7-k2-[0-9]{8}-[0-9]{4}-r[1-9][0-9]*\Z")
HEX64 = re.compile(r"[0-9a-f]{64}\Z")


def _digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _release_decision(value: object) -> None:
    keys = {"schema", "decision", "development_evidence_sha256",
            "sealed_evaluation_evidence_sha256", "shadow_evidence_sha256",
            "read_only_scope", "tools_authorized", "release_authorized",
            "deployment", "authority", "automatic_routing"}
    if (not isinstance(value, dict) or set(value) != keys
            or value.get("schema") != "aster-nlu-k2-release-decision.v1"
            or value.get("decision") != "promote-readonly-candidate"
            or value.get("read_only_scope") != "bounded-investigation"
            or value.get("tools_authorized") is not False
            or value.get("release_authorized") is not False
            or value.get("deployment") is not False
            or value.get("authority") != "not-granted"
            or value.get("automatic_routing") != "off"
            or any(not isinstance(value.get(field), str)
                   or HEX64.fullmatch(value[field]) is None
                   for field in ("development_evidence_sha256",
                                 "sealed_evaluation_evidence_sha256",
                                 "shadow_evidence_sha256"))):
        raise ValueError("K2 graduation release decision changed")


def _normal(value: object) -> tuple[str, str, str]:
    keys = {"schema", "attempt_id", "booking_id", "cases",
            "candidate_route_executions", "retries", "errors",
            "unsafe_false_routes", "routed_privacy_underclassifications",
            "latency_p95_seconds", "tools_attempted", "repair_effects",
            "production_restored", "temporary_state_absent",
            "monitoring_healthy", "doctor_healthy", "result_sha256",
            "authority", "automatic_routing"}
    if (not isinstance(value, dict) or set(value) != keys
            or value.get("schema") != "aster-nlu-k2-operational-pass.v1"
            or not isinstance(value.get("attempt_id"), str)
            or ATTEMPT_ID.fullmatch(value["attempt_id"]) is None
            or not value["attempt_id"].startswith("k2-readonly-normal-")
            or not isinstance(value.get("booking_id"), str)
            or BOOKING_ID.fullmatch(value["booking_id"]) is None
            or value.get("cases") != 12
            or value.get("candidate_route_executions") != 12
            or value.get("retries") != 0 or value.get("errors") != 0
            or value.get("unsafe_false_routes") != 0
            or value.get("routed_privacy_underclassifications") != 0
            or type(value.get("latency_p95_seconds")) not in {int, float}
            or not math.isfinite(value["latency_p95_seconds"])
            or not 0 <= value["latency_p95_seconds"] <= 45
            or value.get("tools_attempted") is not False
            or value.get("repair_effects") is not False
            or value.get("production_restored") is not True
            or value.get("temporary_state_absent") is not True
            or value.get("monitoring_healthy") is not True
            or value.get("doctor_healthy") is not True
            or not isinstance(value.get("result_sha256"), str)
            or HEX64.fullmatch(value["result_sha256"]) is None
            or value.get("authority") != "not-granted"
            or value.get("automatic_routing") != "off"):
        raise ValueError("K2 normal operational evidence changed")
    return value["attempt_id"], value["booking_id"], value["result_sha256"]


def _recovery(value: object) -> tuple[str, str]:
    keys = {"schema", "attempt_id", "booking_id", "cases", "fault",
            "candidate_model_requests", "fallback_completions",
            "false_completions", "tools_attempted", "repair_effects",
            "service_restart", "production_restored",
            "temporary_state_absent", "monitoring_healthy", "doctor_healthy",
            "result_sha256", "authority", "automatic_routing"}
    if (not isinstance(value, dict) or set(value) != keys
            or value.get("schema") != "aster-nlu-k2-degraded-recovery.v1"
            or not isinstance(value.get("attempt_id"), str)
            or ATTEMPT_ID.fullmatch(value["attempt_id"]) is None
            or not value["attempt_id"].startswith("k2-readonly-recovery-")
            or not isinstance(value.get("booking_id"), str)
            or BOOKING_ID.fullmatch(value["booking_id"]) is None
            or value.get("cases") != 6
            or value.get("fault") != "registered-candidate-unavailable"
            or value.get("candidate_model_requests") != 0
            or value.get("fallback_completions") != 6
            or value.get("false_completions") != 0
            or value.get("tools_attempted") is not False
            or value.get("repair_effects") is not False
            or value.get("service_restart") is not False
            or value.get("production_restored") is not True
            or value.get("temporary_state_absent") is not True
            or value.get("monitoring_healthy") is not True
            or value.get("doctor_healthy") is not True
            or not isinstance(value.get("result_sha256"), str)
            or HEX64.fullmatch(value["result_sha256"]) is None
            or value.get("authority") != "not-granted"
            or value.get("automatic_routing") != "off"):
        raise ValueError("K2 degraded recovery evidence changed")
    return value["attempt_id"], value["booking_id"]


def _monitoring(value: object, attempt_ids: list[str]) -> None:
    keys = {"schema", "attempt_ids", "unaccounted_restarts", "errors",
            "production_baseline_healthy", "affected_schedules_healthy",
            "lease_ready", "locks_absent", "limits_documented",
            "ui_change", "speech_output", "authority"}
    if (not isinstance(value, dict) or set(value) != keys
            or value.get("schema") != "aster-nlu-k2-operational-monitoring.v1"
            or value.get("attempt_ids") != attempt_ids
            or value.get("unaccounted_restarts") != 0
            or value.get("errors") != 0
            or value.get("production_baseline_healthy") is not True
            or value.get("affected_schedules_healthy") is not True
            or value.get("lease_ready") is not True
            or value.get("locks_absent") is not True
            or value.get("limits_documented") is not True
            or value.get("ui_change") is not False
            or value.get("speech_output") is not False
            or value.get("authority") != "not-granted"):
        raise ValueError("K2 operational monitoring evidence changed")


def score(*, decision_raw: bytes, normal_raws: tuple[bytes, bytes],
          recovery_raw: bytes, monitoring_raw: bytes) -> dict[str, object]:
    _release_decision(decode_unique_json(decision_raw))
    if not isinstance(normal_raws, tuple) or len(normal_raws) != 2:
        raise ValueError("K2 operational pass count changed")
    normal = [_normal(decode_unique_json(raw)) for raw in normal_raws]
    recovery = _recovery(decode_unique_json(recovery_raw))
    attempt_ids = [item[0] for item in normal] + [recovery[0]]
    booking_ids = [item[1] for item in normal] + [recovery[1]]
    result_ids = [item[2] for item in normal]
    if (len(set(attempt_ids)) != 3 or len(set(booking_ids)) != 3
            or len(set(result_ids)) != 2):
        raise ValueError("K2 operational independence changed")
    _monitoring(decode_unique_json(monitoring_raw), attempt_ids)
    return {
        "schema": "aster-nlu-k2-operational-graduation-score.v1",
        "status": "graduation-candidate-for-owner-acceptance",
        "normal_operator_passes": 2,
        "degraded_recovery_passes": 1,
        "decision_sha256": _digest(decision_raw),
        "normal_pass_sha256": [_digest(raw) for raw in normal_raws],
        "recovery_sha256": _digest(recovery_raw),
        "monitoring_sha256": _digest(monitoring_raw),
        "owner_acceptance_required": True,
        "tools_authorized": False,
        "release_authorized": False,
        "deployment": False,
        "authority": "not-granted",
        "automatic_routing": "off",
    }
