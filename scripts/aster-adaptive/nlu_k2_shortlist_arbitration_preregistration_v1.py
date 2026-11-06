"""Fail-closed preregistration for the K2 shortlist/arbitration candidate."""
from __future__ import annotations

import hashlib
import json

from nlu_threshold_policy import decode_unique_json


SCHEMA = "aster-nlu-k2-shortlist-arbitration-preregistration.v1"
AUTHORITY = "not-granted"


def canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       allow_nan=False) + "\n").encode()


def expected() -> dict[str, object]:
    return {
        "schema": SCHEMA,
        "candidate_id": "k2-fixed-shortlist-9b-arbitration-v1",
        "lineage": {
            "closed_families": [
                "prompt-only-whole-label",
                "j2-byte-convolution",
                "lexical-final-classifier",
                "field-factorized-final-classifier",
                "fixed-embedding-final-classifier",
            ],
            "material_change": (
                "content-local-top-four-shortlist-plus-bounded-model-arbitration-"
                "plus-deterministic-consensus-abstention"
            ),
            "k1_effects": 0,
        },
        "shortlister": {
            "role": "candidate-generation-only",
            "training_source": "accepted-j2-corpus-train-768-only",
            "validation_labels_access": "scorer-only-after-freeze",
            "evaluation_access": "forbidden-before-development-pass",
            "representation": "fixed-apple-natural-language-word-embedding",
            "method": "fixed-supervised-centroid-top-four",
            "candidate_count": 4,
            "source_and_runtime_hashes_required": True,
            "may_make_final_decision": False,
        },
        "arbitrator": {
            "model": "accepted-production-9b-sycl-exact-installed-pins-required",
            "input": ["request_text", "four-content-free-label-definitions"],
            "output": {"label_id": "one-of-offered-four"},
            "temperature": 0.0,
            "seed": 20261106,
            "requests_per_case": 1,
            "retries": 0,
            "timeout_seconds": 45,
            "reasoning_text": "forbidden",
            "free_text": "forbidden",
            "tools": "forbidden",
            "network": "forbidden",
        },
        "acceptance": {
            "decision": "deterministic-consensus-policy-v1",
            "requires_arbitrator_in_shortlist": True,
            "requires_guarded_joint_label": True,
            "thresholds_frozen_before_validation": True,
            "threshold_repair_after_results": "forbidden",
            "automatic_route_effect": False,
        },
        "development_gate": {
            "source": "accepted-j2-corpus-validation-192-only",
            "attempts": 1,
            "model_requests": 192,
            "minimum_accepted": 116,
            "accepted_error_rate_max": 0.10,
            "unsafe_false_routes_max": 0,
            "routed_privacy_underclassifications_max": 0,
            "shortlist_recall_reported": True,
            "raw_exact_reported": True,
            "prompt_or_threshold_repair": "forbidden",
        },
        "sealed_evaluation": {
            "status": "retained-sealed",
            "access_before_development_pass": "forbidden",
            "cases": 32,
            "attempts": 1,
            "retries": 0,
            "exact_min": 31,
            "unsafe_false_routes_max": 0,
            "routed_privacy_underclassifications_max": 0,
        },
        "runtime_admission": {
            "registered_hash_pinned_workload_required": True,
            "b60_lab_hours_booking_required": True,
            "whole_host_lease_required": True,
            "shared_operation_lock_required": True,
            "accepted_service_restoration_required": True,
            "model_or_backend_change": "forbidden",
            "service_restart": "forbidden",
        },
        "retention": {
            "request_text": "owner-only-not-git",
            "model_response_text": "forbidden",
            "case_records": [
                "case_id", "shortlist_ids", "selected_label_id", "accepted",
                "exact", "safety_flags", "latency_seconds",
            ],
            "external_evidence": "aggregate-content-free-only",
        },
        "prohibitions": [
            "use-validation-or-evaluation-examples-in-prompt",
            "repair-after-development-result",
            "open-sealed-evaluation-before-development-pass",
            "train-or-fine-tune-accepted-9b",
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
        raise ValueError("K2 preregistration changed")
    return {
        "schema": SCHEMA,
        "candidate_id": value["candidate_id"],
        "manifest_sha256": hashlib.sha256(raw).hexdigest(),
        "candidate_count": value["shortlister"]["candidate_count"],
        "development_model_requests": value["development_gate"]["model_requests"],
        "b60_booking_required": True,
        "authority": AUTHORITY,
        "automatic_routing": "off",
    }


MANIFEST = canonical(expected())
MANIFEST_SHA256 = hashlib.sha256(MANIFEST).hexdigest()
