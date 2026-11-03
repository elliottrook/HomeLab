"""One-time public gate for the frozen J1 artifact; source-only until approved."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path

import nlu_j1_training_recipe_v1 as recipe
from nlu_threshold_policy import decode_unique_json


FIXTURE_SHA256 = "1565a21c78875f64f4f25a190e977ae34dc01bdfcfd5e49c056e8365268b3785"
ARTIFACT_FILE_SHA256 = "7153f630c64b3823011b733826c11ee70c415e6066b42e869f203fa09ae2ba5e"
ARTIFACT_SHA256 = "606bd761857f39932862df16780521a7ba4ba4923a9bd26b39ba44d9d7e7ae7c"
EXECUTION_RECEIPT_SHA256 = "d769d2a1c81ace428dea308e6704b877f9aefc3615ed458400e8e5ddc489d5df"
RELEASE_CANDIDATE_SHA256 = "81a4f40a41a9e31efeb663f7e7be0a47fcce6e91a122555e1b105296cb7cbbfb"
GUARD_SHA256 = "d7d62d19008519ae50aa9b46799ab1f277a51904f2e80e65c30517abca8a7135"


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _validate_inputs(fixture_raw: bytes, artifact_raw: bytes, receipt_raw: bytes
                     ) -> tuple[dict[str, object], dict[str, object], list[dict[str, object]]]:
    if sha(fixture_raw) != FIXTURE_SHA256 or sha(artifact_raw) != ARTIFACT_FILE_SHA256:
        raise ValueError("public fixture or artifact identity changed")
    if sha(receipt_raw) != EXECUTION_RECEIPT_SHA256:
        raise ValueError("training execution receipt identity changed")
    fixture = decode_unique_json(fixture_raw)
    artifact = decode_unique_json(artifact_raw)
    receipt = decode_unique_json(receipt_raw)
    cases = fixture.get("cases") if isinstance(fixture, dict) else None
    if not isinstance(cases, list) or len(cases) != 24:
        raise ValueError("public fixture must contain exactly 24 cases")
    if (not isinstance(receipt, dict) or receipt.get("schema") != "aster-nlu-j1-training-execution.v1"
            or receipt.get("status") != "complete" or receipt.get("reproductions") != 2
            or receipt.get("reproductions_identical") is not True
            or receipt.get("artifact_sha256") != ARTIFACT_SHA256
            or receipt.get("artifact_file_sha256") != ARTIFACT_FILE_SHA256
            or receipt.get("release_candidate_sha256") != RELEASE_CANDIDATE_SHA256
            or receipt.get("public_gate_opened") is not False
            or receipt.get("sealed_holdout_read") is not False
            or receipt.get("authority") != "not-granted"
            or receipt.get("automatic_routing") != "off"):
        raise ValueError("training execution receipt boundary changed")
    recipe.model_from_artifact(artifact,
        release_candidate_sha256=RELEASE_CANDIDATE_SHA256,
        guard_sha256=GUARD_SHA256, expected_artifact_sha256=ARTIFACT_SHA256)
    return artifact, receipt, cases


def run(fixture_raw: bytes, artifact_raw: bytes, receipt_raw: bytes) -> dict[str, object]:
    artifact, _receipt, cases = _validate_inputs(fixture_raw, artifact_raw, receipt_raw)
    records = []
    for case in cases:
        if (not isinstance(case, dict) or set(case) != {"id", "text", "expected"}
                or not isinstance(case["id"], str) or not case["id"]):
            raise ValueError("public case schema changed")
        result = recipe.project(artifact, case["text"],
            release_candidate_sha256=RELEASE_CANDIDATE_SHA256,
            guard_sha256=GUARD_SHA256, expected_artifact_sha256=ARTIFACT_SHA256)
        records.append({"id": case["id"], "accepted": result["accepted"],
                        "label_id": result["label_id"],
                        "confidence": result["confidence"], "margin": result["margin"],
                        "interpretation": result["interpretation"]})
    return {"schema": "aster-nlu-j1-public-run.v1", "fixture_sha256": FIXTURE_SHA256,
            "artifact_sha256": ARTIFACT_SHA256, "attempted": len(records),
            "records": records, "authority": "not-granted", "automatic_routing": "off"}


def summarize(fixture_raw: bytes, result: dict[str, object]) -> dict[str, object]:
    fixture = decode_unique_json(fixture_raw)
    expected = {case["id"]: case["expected"] for case in fixture["cases"]}
    if (not isinstance(result, dict)
            or set(result) != {"schema", "fixture_sha256", "artifact_sha256", "attempted",
                               "records", "authority", "automatic_routing"}
            or result.get("schema") != "aster-nlu-j1-public-run.v1"
            or result.get("fixture_sha256") != FIXTURE_SHA256
            or result.get("artifact_sha256") != ARTIFACT_SHA256
            or result.get("attempted") != 24
            or result.get("authority") != "not-granted"
            or result.get("automatic_routing") != "off"):
        raise ValueError("public result boundary changed")
    records = result["records"]
    if not isinstance(records, list) or len(records) != 24:
        raise ValueError("public result records changed")
    if {row.get("id") for row in records if isinstance(row, dict)} != set(expected):
        raise ValueError("public result identifiers changed")
    for row in records:
        if (not isinstance(row, dict)
                or set(row) != {"id", "accepted", "label_id", "confidence", "margin",
                                "interpretation"}
                or type(row["accepted"]) is not bool
                or row["label_id"] not in recipe.ontology.CATALOGUE):
            raise ValueError("public result record schema changed")
        for field in ("confidence", "margin"):
            value = row[field]
            if type(value) not in {int, float} or not math.isfinite(value) or not 0 <= value <= 1:
                raise ValueError("public result confidence changed")
        recipe.guard.contract._validate_semantics(row["interpretation"])
    exact = sum(row["interpretation"] == expected[row["id"]] for row in records)
    routed = [row for row in records if row["interpretation"]["disposition"] == "route"]
    unsafe = sum(expected[row["id"]]["disposition"] != "route" for row in routed)
    sensitivity = {"public": 0, "internal": 1, "personal": 2}
    privacy = sum(sensitivity[row["interpretation"]["sensitivity"]]
                  < sensitivity[expected[row["id"]]["sensitivity"]] for row in routed)
    summary = {"schema": "aster-nlu-j1-public-summary.v1",
               "run_sha256": sha(recipe.canonical(result)), "attempted": 24,
               "exact": exact, "unsafe_false_routes": unsafe,
               "routed_privacy_underclassifications": privacy,
               "failed_ids": [row["id"] for row in records
                              if row["interpretation"] != expected[row["id"]]],
               "public_pass": exact >= 23 and unsafe == 0 and privacy == 0,
               "authority": "not-granted", "automatic_routing": "off"}
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--fixture", required=True, type=Path)
    parser.add_argument("--artifact", required=True, type=Path)
    parser.add_argument("--execution-receipt", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = run(args.fixture.read_bytes(), args.artifact.read_bytes(),
                 args.execution_receipt.read_bytes())
    raw = recipe.canonical(result)
    descriptor = os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "wb") as handle:
        handle.write(raw); handle.flush(); os.fsync(handle.fileno())
    print(json.dumps(summarize(args.fixture.read_bytes(), result),
                     sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
