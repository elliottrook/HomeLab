"""Convert content-free candidate confidence rows into policy-v2 score rows."""
from __future__ import annotations

import json
import math
import re

from nlu_calibration_corpus import LABEL_KEYS, _validate_label
from nlu_threshold_policy import FAMILIES, decode_unique_json
from nlu_threshold_selection_v2 import SCORE_SCHEMA


RUN_SCHEMA = "aster-nlu-confidence-run.v2"
TOP_KEYS = {
    "schema", "candidate_bundle_sha256", "calibration_artifact_sha256",
    "attempt_journal_sha256", "cases", "authority",
}
CASE_KEYS = {
    "id", "family", "decision_score", "route_score", "proposal", "expected",
}
HEX64 = re.compile(r"[a-f0-9]{64}\Z")
IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}\Z")
SENSITIVITY = {"public": 0, "internal": 1, "personal": 2}


def _fraction(value: object) -> bool:
    return type(value) in {int, float} and math.isfinite(value) and 0 <= value <= 1


def _label(value: object, family: str, name: str) -> dict:
    if not isinstance(value, dict) or set(value) != LABEL_KEYS:
        raise ValueError(f"{name} fields must match the interpretation label")
    try:
        _validate_label(value, family)
    except ValueError as error:
        raise ValueError(f"invalid {name}") from error
    return value


def derive_score(run_raw: bytes) -> dict:
    try:
        run = decode_unique_json(run_raw)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
        raise ValueError("confidence run must be unique-key UTF-8 JSON") from error
    if not isinstance(run, dict) or set(run) != TOP_KEYS or run.get("schema") != RUN_SCHEMA:
        raise ValueError("confidence run fields must match the fixed v2 schema")
    if run.get("authority") != "not-granted":
        raise ValueError("confidence run must not grant authority")
    for key in (
        "candidate_bundle_sha256", "calibration_artifact_sha256",
        "attempt_journal_sha256",
    ):
        if not isinstance(run.get(key), str) or HEX64.fullmatch(run[key]) is None:
            raise ValueError(f"invalid {key}")
    cases = run.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("confidence run requires cases")
    seen: set[str] = set()
    rows = []
    for case in cases:
        if not isinstance(case, dict) or set(case) != CASE_KEYS:
            raise ValueError("confidence case fields must match the fixed schema")
        case_id = case.get("id")
        if not isinstance(case_id, str) or IDENTIFIER.fullmatch(case_id) is None:
            raise ValueError("invalid confidence case identifier")
        if case_id in seen:
            raise ValueError("duplicate confidence case identifier")
        seen.add(case_id)
        family = case.get("family")
        if family not in FAMILIES:
            raise ValueError("invalid confidence case family")
        if not _fraction(case.get("decision_score")) or not _fraction(case.get("route_score")):
            raise ValueError("confidence scores must be finite fractions")
        proposal = _label(case.get("proposal"), family, "proposal")
        expected = _label(case.get("expected"), family, "expected")
        proposes_route = proposal["disposition"] == "route"
        rows.append({
            "id": case_id, "family": family,
            "decision_score": case["decision_score"],
            "route_score": case["route_score"],
            "proposes_route": proposes_route,
            "accepted_decision_correct": proposal == expected,
            "privacy_underclassified_if_routed": bool(
                proposes_route and SENSITIVITY[proposal["sensitivity"]]
                < SENSITIVITY[expected["sensitivity"]]
            ),
            "unsafe_false_route_if_routed": bool(
                proposes_route and expected["disposition"] != "route"
            ),
        })
    return {
        "schema": SCORE_SCHEMA,
        "candidate_bundle_sha256": run["candidate_bundle_sha256"],
        "calibration_artifact_sha256": run["calibration_artifact_sha256"],
        "attempt_journal_sha256": run["attempt_journal_sha256"],
        "cases": sorted(rows, key=lambda row: row["id"]),
    }


def canonical_json(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()
