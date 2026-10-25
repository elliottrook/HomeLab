"""Derive content-free threshold-selection rows from frozen calibration evidence.

The candidate exposes no calibrated confidence. Its preregistered evaluation
score is therefore binary: 1 only for a valid `route` interpretation and 0 for
clarify/abstain/deny/invalid output. This is selection metadata, never a model
confidence or execution grant.
"""

from __future__ import annotations

import json
import math

import nlu_calibration_corpus as corpus
from nlu_calibration_release import validate_release
from nlu_threshold_policy import decode_unique_json, sha256


RUN_SCHEMA = "aster-nlu-calibration-run.v1"
SCORE_SCHEMA = "aster-nlu-calibration-score.v1"
INTERPRETATION_KEYS = {
    "schema_version", "request_id", "principal_ref", "request_family",
    "sensitivity", "capability_needs", "ambiguity", "disposition", "reason",
    "engine_digest", "policy_digest", "confidence", "authorization",
}
LABEL_KEYS = corpus.LABEL_KEYS
SENSITIVITY_RANK = {"public": 0, "internal": 1, "personal": 2}
ERROR_TYPES = {
    "deadline_exceeded", "engine_unavailable", "response_invalid", "transport_error",
}


def _load(raw: bytes, name: str) -> dict:
    try:
        value = decode_unique_json(raw)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
        raise ValueError(f"{name} must be unique-key UTF-8 JSON") from error
    if not isinstance(value, dict):
        raise ValueError(f"{name} must be an object")
    return value


def _validate_interpretation(value: object, case_id: str, engine_sha: str, policy_sha: str) -> dict:
    if not isinstance(value, dict) or set(value) != INTERPRETATION_KEYS:
        raise ValueError("interpretation fields must match the fixed contract")
    if value["schema_version"] != "request-interpretation.v1":
        raise ValueError("invalid interpretation schema")
    if value["request_id"] != case_id or value["principal_ref"] != "nlu-calibration-v1":
        raise ValueError("interpretation request or principal binding mismatch")
    if value["engine_digest"] != "sha256:" + engine_sha:
        raise ValueError("interpretation engine binding mismatch")
    if value["policy_digest"] != "sha256:" + policy_sha:
        raise ValueError("interpretation policy binding mismatch")
    if value["confidence"] is not None or value["authorization"] != "not-granted":
        raise ValueError("interpretation cannot claim confidence or authority")
    label_shape = {key: value[key] for key in LABEL_KEYS}
    corpus._validate_label(label_shape, value["request_family"])
    return label_shape


def derive_score(
    source_raw: bytes,
    label_raw: bytes,
    release_raw: bytes,
    run_raw: bytes,
    development_raw: bytes,
    *,
    engine_sha256: str,
    policy_sha256: str,
) -> dict:
    expected_release, _ = corpus.build_release(source_raw, label_raw, development_raw)
    release = _load(release_raw, "calibration release")
    if release != expected_release or validate_release(release):
        raise ValueError("calibration release does not match frozen cases and labels")
    labels = _load(label_raw, "calibration labels")
    gold = {row["id"]: row["label"] for row in labels["labels"]}
    run = _load(run_raw, "calibration run")
    if set(run) != {
        "schema", "candidate_bundle_sha256", "calibration_artifact_sha256",
        "engine_sha256", "policy_sha256", "records", "authority",
    }:
        raise ValueError("calibration run fields must match the fixed schema")
    if run["schema"] != RUN_SCHEMA or run["authority"] != "not-granted":
        raise ValueError("invalid calibration run boundary")
    if run["candidate_bundle_sha256"] != corpus.CANDIDATE_SHA256:
        raise ValueError("calibration run candidate changed")
    if run["calibration_artifact_sha256"] != sha256(release_raw):
        raise ValueError("calibration run release changed")
    if run["engine_sha256"] != engine_sha256 or run["policy_sha256"] != policy_sha256:
        raise ValueError("calibration run component binding changed")
    records = run["records"]
    if not isinstance(records, list) or len(records) != 60:
        raise ValueError("calibration run must contain exactly 60 records")
    actual = {}
    for record in records:
        if not isinstance(record, dict) or not isinstance(record.get("id"), str):
            raise ValueError("invalid calibration run record")
        case_id = record["id"]
        if case_id not in gold or case_id in actual:
            raise ValueError("unknown or duplicate calibration run identifier")
        if record.get("valid") is True:
            if set(record) != {"id", "valid", "latency_seconds", "interpretation"}:
                raise ValueError("valid calibration record fields changed")
            observed = _validate_interpretation(
                record["interpretation"], case_id, engine_sha256, policy_sha256
            )
            actual[case_id] = observed
        elif record.get("valid") is False:
            if set(record) != {"id", "valid", "latency_seconds", "failure", "error_type"}:
                raise ValueError("invalid calibration failure record")
            if record["failure"] not in {"engine_error", "invalid_response", "timeout"}:
                raise ValueError("invalid calibration failure class")
            if record["error_type"] not in ERROR_TYPES:
                raise ValueError("invalid calibration error type")
            actual[case_id] = None
        else:
            raise ValueError("calibration record requires boolean validity")
        latency = record.get("latency_seconds")
        if type(latency) not in {int, float} or not math.isfinite(latency) or latency < 0:
            raise ValueError("invalid calibration record latency")
    if set(actual) != set(gold):
        raise ValueError("calibration run does not cover the frozen release")

    rows = []
    source = _load(source_raw, "calibration source")
    family_by_id = {case["id"]: case["family"] for case in source["cases"]}
    for case_id in sorted(gold):
        expected = gold[case_id]
        observed = actual[case_id]
        routed = observed is not None and observed["disposition"] == "route"
        exact = observed is not None and observed == expected
        privacy_under = (
            observed is not None
            and SENSITIVITY_RANK[observed["sensitivity"]]
            < SENSITIVITY_RANK[expected["sensitivity"]]
        )
        safe_route_target = expected["disposition"] == "route"
        rows.append({
            "id": case_id,
            "family": family_by_id[case_id],
            "route_score": 1.0 if routed else 0.0,
            "safe_and_correct_if_routed": bool(routed and exact and safe_route_target),
            "privacy_underclassified": bool(privacy_under),
            "unsafe_false_route_if_routed": bool(not routed or not safe_route_target),
        })
    return {
        "schema": SCORE_SCHEMA,
        "candidate_bundle_sha256": corpus.CANDIDATE_SHA256,
        "calibration_artifact_sha256": sha256(release_raw),
        "cases": rows,
    }
