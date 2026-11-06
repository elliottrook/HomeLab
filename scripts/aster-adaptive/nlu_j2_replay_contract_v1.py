"""Recompute and validate two exact clean-CPU J2 validation replays."""
from __future__ import annotations

import hashlib
import json
import math
import re
from typing import Callable

import nlu_j2_artifact_contract_v1 as artifact_contract
import nlu_j2_reference_forward_v1 as reference_forward
import nlu_j2_validation_selection_v1 as selection
import nlu_local_model_adapter as semantics
import nlu_whole_label_choice_v1 as ontology
from nlu_threshold_policy import decode_unique_json


CASE_ID = re.compile(r"j2-validation-l(0[0-9]|1[0-5])-case-(4[89]|5[0-9])")


def records_sha256(records: object) -> str:
    return hashlib.sha256(artifact_contract.canonical(records)).hexdigest()


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _truth(raw: bytes) -> list[dict[str, object]]:
    value = decode_unique_json(raw)
    if (not isinstance(value, dict) or set(value) != {
            "schema", "rows", "authority", "automatic_routing"}
            or value["schema"] != "aster-nlu-j2-validation-truth.v1"
            or not isinstance(value["rows"], list) or len(value["rows"]) != 192
            or value["authority"] != "none"
            or value["automatic_routing"] != "off"):
        raise ValueError("J2 validation truth shape changed")
    seen = set()
    for row in value["rows"]:
        if (not isinstance(row, dict) or set(row) != {"id", "text", "label_id"}
                or not isinstance(row["id"], str)
                or not CASE_ID.fullmatch(row["id"]) or row["id"] in seen
                or not isinstance(row["text"], str) or not row["text"].strip()
                or len(row["text"].encode("utf-8")) > 4096
                or row["label_id"] not in ontology.CATALOGUE):
            raise ValueError("J2 validation truth row changed")
        seen.add(row["id"])
    expected = {f"j2-validation-l{label:02d}-case-{case:02d}"
                for label in range(16) for case in range(48, 60)}
    if seen != expected:
        raise ValueError("J2 validation truth case set changed")
    return value["rows"]


def _guarded(text: str, label_id: str) -> dict[str, object]:
    content = json.dumps({"label_id": label_id}, sort_keys=True,
                         separators=(",", ":"))
    envelope = {"choices": [{"finish_reason": "stop", "message": {
        "role": "assistant", "content": content}}]}
    return ontology.interpret(
        text, json.dumps(envelope, sort_keys=True,
                         separators=(",", ":")).encode())


def _recomputed_records(truth: list[dict[str, object]], tensors: object,
                        threshold: float,
                        forward_fn: Callable[[object, object], dict[str, object]]) \
        -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    replay_rows = []
    selection_rows = []
    for truth_row in truth:
        prediction = forward_fn(truth_row["text"], tensors)
        if (not isinstance(prediction, dict)
                or not {"label_id", "confidence", "margin"}.issubset(prediction)
                or prediction["label_id"] not in ontology.CATALOGUE
                or type(prediction["confidence"]) not in {int, float}
                or not math.isfinite(prediction["confidence"])
                or not 0.0 <= prediction["confidence"] <= 1.0
                or type(prediction["margin"]) not in {int, float}
                or not math.isfinite(prediction["margin"])
                or not 0.0 <= prediction["margin"] <= prediction["confidence"]):
            raise ValueError("J2 reference forward result changed")
        guarded = _guarded(truth_row["text"], prediction["label_id"])
        expected_guarded = _guarded(truth_row["text"], truth_row["label_id"])
        raw_exact = prediction["label_id"] == truth_row["label_id"]
        guarded_exact = guarded == expected_guarded
        confidence = round(prediction["confidence"], 10)
        margin = round(prediction["margin"], 10)
        accepted = margin >= threshold and raw_exact and guarded_exact
        replay_rows.append({
            "id": truth_row["id"], "label_id": prediction["label_id"],
            "confidence": confidence, "margin": margin,
            "guarded_interpretation": guarded, "accepted": accepted,
        })
        selection_rows.append({
            "id": truth_row["id"], "margin": margin,
            "raw_exact": raw_exact, "guarded_exact": guarded_exact,
        })
    return replay_rows, selection_rows


def _selection_receipt(raw: bytes, *, truth_sha256: str, tensors_sha256: str,
                       records: list[dict[str, object]]) -> dict[str, object]:
    value = decode_unique_json(raw)
    fields = {"schema", "validation_truth_sha256", "checkpoint_tensors_sha256",
              "selected_epoch", "epoch_summaries", "threshold_records_sha256",
              "threshold", "accepted_validation_rows", "validation_rows",
              "minimum_accepted", "all_accepted_raw_and_guarded_exact",
              "authority", "automatic_routing"}
    if (not isinstance(value, dict) or set(value) != fields
            or value["schema"] != "aster-nlu-j2-validation-selection.v1"
            or value["validation_truth_sha256"] != truth_sha256
            or value["checkpoint_tensors_sha256"] != tensors_sha256
            or value["threshold_records_sha256"] != records_sha256(records)
            or value["validation_rows"] != 192
            or value["minimum_accepted"] != 116
            or value["all_accepted_raw_and_guarded_exact"] is not True
            or value["authority"] != "none"
            or value["automatic_routing"] != "off"):
        raise ValueError("J2 validation selection receipt changed")
    selected_epoch = selection.select_epoch(value["epoch_summaries"])
    selected_threshold = selection.select_threshold(records)
    if (value["selected_epoch"] != selected_epoch
            or value["threshold"] != selected_threshold["threshold"]
            or value["accepted_validation_rows"] != selected_threshold["accepted"]):
        raise ValueError("J2 validation selection result differs")
    return value


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
                for label in range(16) for case in range(48, 60)}
    if seen != expected:
        raise ValueError("J2 replay case set changed")
    return value


def validate(artifact_raw: bytes, replay_one_raw: bytes, replay_two_raw: bytes,
             expected_corpus_release_sha256: str,
             expected_training_admission_sha256: str,
             validation_truth_raw: bytes, validation_selection_raw: bytes, *,
             forward_fn: Callable[[object, object], dict[str, object]] =
             reference_forward.forward) -> dict[str, object]:
    artifact = artifact_contract.validate(
        artifact_raw, expected_corpus_release_sha256,
        expected_training_admission_sha256)
    artifact_value = decode_unique_json(artifact_raw)
    truth = _truth(validation_truth_raw)
    truth_sha256 = _sha256(validation_truth_raw)
    tensors_sha256 = _sha256(artifact_contract.canonical(artifact_value["tensors"]))
    expected_records, selection_records = _recomputed_records(
        truth, artifact_value["tensors"], artifact["threshold"], forward_fn)
    receipt = _selection_receipt(
        validation_selection_raw, truth_sha256=truth_sha256,
        tensors_sha256=tensors_sha256, records=selection_records)
    if (truth_sha256 != artifact["validation_truth_sha256"]
            or _sha256(validation_selection_raw)
            != artifact["validation_selection_sha256"]
            or receipt["selected_epoch"] != artifact["selected_epoch"]
            or receipt["threshold"] != artifact["threshold"]
            or receipt["accepted_validation_rows"]
            != artifact["accepted_validation_rows"]):
        raise ValueError("J2 artifact validation selection binding differs")
    first = _replay(replay_one_raw, artifact["artifact_sha256"], "clean-cpu-1")
    second = _replay(replay_two_raw, artifact["artifact_sha256"], "clean-cpu-2")
    if (first["records"] != expected_records
            or second["records"] != expected_records
            or records_sha256(expected_records)
            != artifact_value["validation_replay_sha256"]
            or sum(row["accepted"] for row in expected_records)
            != artifact["accepted_validation_rows"]):
        raise ValueError("J2 clean replay differs from recomputed validation truth")
    return {"schema": "aster-nlu-j2-replay-validation.v1",
            "artifact_sha256": artifact["artifact_sha256"],
            "validation_truth_sha256": truth_sha256,
            "validation_selection_sha256": _sha256(validation_selection_raw),
            "records_sha256": records_sha256(expected_records),
            "rows": 192, "accepted": artifact["accepted_validation_rows"],
            "clean_cpu_reproductions": 2, "exact_record_equality": True,
            "recomputed_from_validation_truth": True,
            "deployment": False, "authority": "none",
            "automatic_routing": "off"}
