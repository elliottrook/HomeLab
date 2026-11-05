"""Exact no-retry public-development batch for candidate-j."""

from __future__ import annotations

from sa3_evidence_matrix_candidate_j_public import validate
from sa3_evidence_matrix_candidate_j_runner import run_case


def run_public(fixture: dict, transport, *, model: str, monotonic) -> dict:
    summary = validate(fixture)
    predictions = []
    errors = []
    requests = 0
    for row in fixture["cases"]:
        result = run_case(row["input"], transport, model=model,
                          monotonic=monotonic)
        predictions.append(result)
        requests += int(result["model_requested"])
        if result["error_class"] is not None:
            errors.append({"id": row["id"], "class": result["error_class"]})
    return {
        "schema": "aster-sa3-evidence-matrix-public-result.v1",
        "candidate_alias": "candidate-j", "model": model,
        "fixture_sha256": summary["fixture_sha256"], "case_count": 6,
        "model_request_count": requests, "retry_count": 0,
        "predictions": predictions, "errors": errors,
        "authority": "none", "automatic_routing": "off",
    }
