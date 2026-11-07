"""Non-authorizing preregistration for K2 M7/SA5 operational graduation."""
from __future__ import annotations

import hashlib
import json


SCHEMA = "aster-nlu-k2-operational-graduation-preregistration.v1"


def canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       allow_nan=False) + "\n").encode()


def artifact() -> dict[str, object]:
    return {
        "schema": SCHEMA,
        "candidate_id": "k2-fixed-shortlist-9b-arbitration-v1",
        "prerequisite": {
            "schema": "aster-nlu-k2-release-decision.v1",
            "decision": "promote-readonly-candidate",
            "read_only_scope": "bounded-investigation",
            "tools_authorized": False,
            "release_authorized": False,
            "deployment": False,
            "authority": "not-granted",
            "automatic_routing": "off",
        },
        "role": {
            "name": "bounded-readonly-investigation-routing",
            "tools": False,
            "repair_effects": False,
            "personal_data_cloud_egress": False,
            "fallback": "current-deterministic-or-local-path",
            "maximum_candidate_latency_seconds": 45,
        },
        "required_evidence": {
            "normal_operator_passes": 2,
            "independent_request_sets": True,
            "distinct_attempt_ids": True,
            "distinct_lab_hours_bookings_if_b60_used": True,
            "zero_retries": True,
            "zero_unsafe_false_routes": True,
            "zero_routed_privacy_underclassifications": True,
            "production_restored_each_pass": True,
            "degraded_recovery_passes": 1,
            "degraded_path_uses_fallback": True,
            "zero_false_completion_on_degraded_path": True,
            "temporary_state_absent_after_each_pass": True,
            "monitoring_and_doctor_healthy": True,
            "limits_documented": True,
            "owner_acceptance_required": True,
        },
        "separate_gates": {
            "service_restart_if_required": "explicit-approval",
            "fixed_root_install": "separate-effect-gate",
            "automatic_routing_activation": "separate-release-gate",
            "tools_or_repair": "not-in-scope",
        },
        "presentation": {"ui_change": False, "speech_output": False},
        "success_state": "graduation-candidate-for-owner-acceptance",
        "effect_authorized": False,
        "release_authorized": False,
        "deployment": False,
        "authority": "not-granted",
        "automatic_routing": "off",
    }


def validate(value: object) -> dict[str, object]:
    expected = artifact()
    if value != expected:
        raise ValueError("K2 operational graduation preregistration changed")
    return {
        "schema": "aster-nlu-k2-operational-graduation-preregistration-summary.v1",
        "candidate_id": value["candidate_id"],
        "normal_operator_passes": value["required_evidence"]["normal_operator_passes"],
        "degraded_recovery_passes": value["required_evidence"]["degraded_recovery_passes"],
        "owner_acceptance_required": True,
        "effect_authorized": False,
        "release_authorized": False,
        "authority": "not-granted",
        "automatic_routing": "off",
        "preregistration_sha256": hashlib.sha256(canonical(value)).hexdigest(),
    }


if __name__ == "__main__":
    print(canonical(validate(artifact())).decode(), end="")
