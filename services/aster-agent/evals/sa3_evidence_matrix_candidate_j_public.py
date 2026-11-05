"""Validate candidate-j's separate public-development semantics."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from sa3_evidence_matrix_candidate_j_contract import (
    eligible_hypothesis_ids, project,
)


FIXTURE = Path(__file__).with_name(
    "sa3-evidence-matrix-candidate-j-public-v1.json")


def canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       allow_nan=False) + "\n").encode()


def validate(value: object) -> dict[str, object]:
    if (not isinstance(value, dict) or set(value) != {
            "schema", "candidate_alias", "authority", "automatic_routing",
            "cases"}
            or value["schema"] != "aster-sa3-evidence-matrix-public-development.v1"
            or value["candidate_alias"] != "candidate-j"
            or value["authority"] != "none"
            or value["automatic_routing"] != "off"
            or not isinstance(value["cases"], list)
            or len(value["cases"]) != 6):
        raise ValueError("invalid candidate-j public fixture")
    seen = set(); plans = 0; abstentions = 0
    for row in value["cases"]:
        if (not isinstance(row, dict)
                or set(row) != {"id", "input", "selection", "expected"}
                or not isinstance(row["id"], str) or row["id"] in seen
                or row["input"].get("id") != row["id"]
                or not isinstance(row["expected"], dict)
                or set(row["expected"]) != {
                    "outcome", "checks", "model_requested"}):
            raise ValueError("invalid candidate-j public case")
        eligible = eligible_hypothesis_ids(row["input"])
        model_requested = bool(eligible)
        result = project(row["input"], row["selection"])
        if (result["outcome"] != row["expected"]["outcome"]
                or result["checks"] != row["expected"]["checks"]
                or model_requested is not row["expected"]["model_requested"]
                or result["effects"] != [] or result["authority"] != "none"
                or "no action has been performed" not in result["summary"]):
            raise ValueError("candidate-j public expectation mismatch")
        plans += int(result["outcome"] == "plan")
        abstentions += int(result["outcome"] == "clarify")
        seen.add(row["id"])
    if plans != 2 or abstentions != 4:
        raise ValueError("candidate-j public composition differs")
    return {
        "schema": "aster-sa3-evidence-matrix-public-result.v1",
        "candidate_alias": "candidate-j", "case_count": 6,
        "plans": plans, "abstentions": abstentions,
        "fixture_sha256": hashlib.sha256(canonical(value)).hexdigest(),
        "authority": "none", "automatic_routing": "off",
    }


def load_and_validate(path: Path = FIXTURE) -> dict[str, object]:
    return validate(json.loads(path.read_text(encoding="utf-8")))
