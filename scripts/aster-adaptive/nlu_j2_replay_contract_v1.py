"""Validate two exact clean-CPU J2 validation replays."""
from __future__ import annotations

import hashlib
import math
import re

import nlu_j2_artifact_contract_v1 as artifact_contract
import nlu_local_model_adapter as semantics
import nlu_whole_label_choice_v1 as ontology
from nlu_threshold_policy import decode_unique_json


CASE_ID = re.compile(r"j2-validation-l(0[0-9]|1[0-5])-case-(0[0-9]|1[01])")


def records_sha256(records: object) -> str:
    return hashlib.sha256(artifact_contract.canonical(records)).hexdigest()


def _replay(raw: bytes, artifact_sha256: str, run_id: str) -> dict[str, object]:
    value = decode_unique_json(raw)
    fields = {"schema", "artifact_sha256", "run_id", "backend",
              "cpu_threads", "rows", "records", "authority",
              "automatic_routing"}
    if (not isinstance(value, dict) or set(value) != fields
            or value["schema"] != "aster-nlu-j2-validation-replay.v1"
            or value["artifact_sha256"] != artifact_sha256
            or value["run_id"] != run_id
            or value["backend"] != "portable-python-cpu-reference"
            or value["cpu_threads"] != 1 or value["rows"] != 192
            or not isinstance(value["records"], list)
            or len(value["records"]) != 192
            or value["authority"] != "none"
            or value["automatic_routing"] != "off"):
        raise ValueError("J2 replay shape changed")
    seen = set()
    for row in value["records"]:
        if (not isinstance(row, dict) or set(row) != {
                "id", "label_id", "confidence", "margin",
                "guarded_interpretation", "accepted"}
                or not isinstance(row["id"], str)
                or not CASE_ID.fullmatch(row["id"]) or row["id"] in seen
                or row["label_id"] not in ontology.CATALOGUE
                or type(row["confidence"]) not in {int, float}
                or not math.isfinite(row["confidence"])
                or not 0.0 <= row["confidence"] <= 1.0
                or round(row["confidence"], 10) != row["confidence"]
                or type(row["margin"]) not in {int, float}
                or not math.isfinite(row["margin"])
                or not 0.0 <= row["margin"] <= row["confidence"]
                or round(row["margin"], 10) != row["margin"]
                or type(row["accepted"]) is not bool
                or not isinstance(row["guarded_interpretation"], dict)):
            raise ValueError("J2 replay record changed")
        semantics._validate_semantics(row["guarded_interpretation"])
        seen.add(row["id"])
    expected = {f"j2-validation-l{label:02d}-case-{case:02d}"
                for label in range(16) for case in range(12)}
    if seen != expected:
        raise ValueError("J2 replay case set changed")
    return value


def validate(artifact_raw: bytes, replay_one_raw: bytes, replay_two_raw: bytes,
             expected_corpus_release_sha256: str,
             expected_training_admission_sha256: str) -> dict[str, object]:
    artifact = artifact_contract.validate(
        artifact_raw, expected_corpus_release_sha256,
        expected_training_admission_sha256)
    first = _replay(replay_one_raw, artifact["artifact_sha256"], "clean-cpu-1")
    second = _replay(replay_two_raw, artifact["artifact_sha256"], "clean-cpu-2")
    if (first["records"] != second["records"]
            or records_sha256(first["records"])
            != decode_unique_json(artifact_raw)["validation_replay_sha256"]
            or sum(row["accepted"] for row in first["records"])
            != artifact["accepted_validation_rows"]):
        raise ValueError("J2 clean replay differs")
    return {"schema": "aster-nlu-j2-replay-validation.v1",
            "artifact_sha256": artifact["artifact_sha256"],
            "records_sha256": records_sha256(first["records"]),
            "rows": 192, "accepted": artifact["accepted_validation_rows"],
            "clean_cpu_reproductions": 2, "exact_record_equality": True,
            "deployment": False, "authority": "none",
            "automatic_routing": "off"}
