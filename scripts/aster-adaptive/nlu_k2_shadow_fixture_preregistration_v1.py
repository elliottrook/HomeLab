"""Non-authorizing preregistration for the representative K2 M5 shadow set."""
from __future__ import annotations

import hashlib
import json


def canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       allow_nan=False) + "\n").encode()


def artifact() -> dict[str, object]:
    return {
        "schema": "aster-nlu-k2-shadow-fixture-preregistration.v1",
        "candidate_id": "k2-fixed-shortlist-9b-arbitration-v1",
        "prerequisites": {
            "development": "complete-pass-restored",
            "sealed_evaluation": "complete-pass-restored",
            "automatic_routing": "off",
        },
        "fixture": {
            "source_class": "representative-sanitized-S0",
            "cases": 60,
            "request_families": 6,
            "cases_per_family": 10,
            "unique_case_ids": True,
            "request_text_retained_only_in_private_fixture": True,
            "public_evidence_contains_request_digest_only": True,
            "personal_or_secret_material": False,
            "credentials_or_tool_arguments": False,
        },
        "independence": {
            "development_corpus_sha256":
                "9e2dd321c6660ad4bd09e9824c24b9727a30eba60a8df37e09f17d436ccce90a",
            "sealed_evaluation_sha256":
                "78f7b8aa7b8f8202e38333be4d497a489c1f36b3c6209839c05ecd3975191cae",
            "zero_text_or_case_id_overlap_with_development": True,
            "zero_text_or_case_id_overlap_with_sealed_evaluation": True,
            "fixture_custodian_and_label_reviewer_distinct": True,
            "case_labels_reviewed_before_candidate_collection": True,
            "candidate_output_hidden_from_label_reviewer": True,
        },
        "collection": {
            "model_requests": 60,
            "retries": 0,
            "route_execution": False,
            "provider_egress": False,
            "external_cost_microunits": 0,
            "own_lab_hours_booking_if_b60_used": True,
            "production_restoration_required": True,
        },
        "effect_authorized": False,
        "deployment": False,
        "authority": "not-granted",
        "automatic_routing": "off",
    }


def validate(value: object) -> dict[str, object]:
    if value != artifact():
        raise ValueError("K2 shadow fixture preregistration changed")
    return {
        "schema": "aster-nlu-k2-shadow-fixture-preregistration-summary.v1",
        "cases": 60, "request_families": 6, "cases_per_family": 10,
        "independent_label_review_required": True,
        "overlap_proof_required": True,
        "effect_authorized": False, "authority": "not-granted",
        "automatic_routing": "off",
        "preregistration_sha256": hashlib.sha256(canonical(value)).hexdigest(),
    }


if __name__ == "__main__":
    print(canonical(validate(artifact())).decode(), end="")
