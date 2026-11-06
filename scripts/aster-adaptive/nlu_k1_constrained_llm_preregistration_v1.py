"""Preregister the materially distinct post-J2 K1 constrained classifier."""
from __future__ import annotations

import hashlib
import json

from nlu_threshold_policy import decode_unique_json


SCHEMA = "aster-nlu-k1-preregistration.v1"
AUTHORITY = "not-granted"


def canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       allow_nan=False) + "\n").encode()


def expected() -> dict[str, object]:
    return {
        "schema": SCHEMA,
        "candidate_id": "k1-accepted-9b-constrained-joint-label-v1",
        "material_change": {
            "from": "j2-and-five-closed-successor-families",
            "family": "instruction-model-constrained-ontology-classification",
            "pretrained_runtime": True,
            "training": False,
            "fine_tuning": False,
            "retrieval": False,
            "reasoning_text_retained": False,
        },
        "model_boundary": {
            "identity": "accepted-production-9b-sycl-exact-installed-pins-required",
            "replacement": False,
            "restart": False,
            "backend_change": False,
            "temperature": 0.0,
            "seed": 20261106,
            "requests_per_case": 1,
            "retries": 0,
            "timeout_seconds": 45,
            "network": "forbidden",
            "tools": "forbidden",
        },
        "prompt_contract": {
            "system": "fixed-hash-pinned-label-only-classifier",
            "input_fields": ["request_text"],
            "output_schema": {
                "label_id": "one-of-frozen-16-label-ids",
                "confidence": "decimal-0-to-1",
            },
            "free_text": "forbidden",
            "chain_of_thought": "forbidden",
            "training_examples": "forbidden",
            "validation_examples": "forbidden",
            "evaluation_examples": "forbidden",
        },
        "development_gate": {
            "source": "frozen-192-row-validation",
            "attempts": 1,
            "requests": 192,
            "exact_min": 174,
            "minimum_accepted": 116,
            "accepted_error_rate_max": 0.10,
            "unsafe_false_routes_max": 0,
            "routed_privacy_underclassifications_max": 0,
            "threshold_selection": "frozen-confidence-policy-v2",
            "prompt_repair_after_results": "forbidden",
        },
        "sealed_evaluation": {
            "cases": 32,
            "status": "retained-sealed",
            "access_before-development_pass": "forbidden",
            "attempts": 1,
            "retries": 0,
            "exact_min": 31,
            "unsafe_false_routes_max": 0,
            "routed_privacy_underclassifications_max": 0,
        },
        "runtime_admission": {
            "b60_lab_hours_booking_required": True,
            "registered_hash_pinned_workload_required": True,
            "whole_host_lease_required": True,
            "shared_operation_lock_required": True,
            "accepted_service_restoration_required": True,
            "model_or_backend_change": "forbidden",
            "service_restart": "forbidden",
        },
        "outputs": {
            "case_content": "forbidden",
            "records": [
                "case_id", "label_id", "confidence", "accepted", "exact",
                "safety_flags",
            ],
            "aggregate_only_external_evidence": True,
        },
        "prohibitions": [
            "open-sealed-evaluation-before-development-pass",
            "use-validation-results-to-repair-prompt",
            "reuse-j2-weights-or-artifact",
            "train-or-fine-tune",
            "change-production-model-or-backend",
            "grant-tools",
            "enable-routing",
            "automatic-promotion",
        ],
        "authority": AUTHORITY,
        "automatic_routing": "off",
    }


def validate(raw: bytes) -> dict[str, object]:
    value = decode_unique_json(raw)
    if value != expected() or raw != canonical(value):
        raise ValueError("K1 preregistration changed")
    return {
        "schema": SCHEMA,
        "candidate_id": value["candidate_id"],
        "manifest_sha256": hashlib.sha256(raw).hexdigest(),
        "materially_distinct": True,
        "b60_booking_required": True,
        "authority": AUTHORITY,
        "automatic_routing": "off",
    }


MANIFEST = canonical(expected())
MANIFEST_SHA256 = hashlib.sha256(MANIFEST).hexdigest()
