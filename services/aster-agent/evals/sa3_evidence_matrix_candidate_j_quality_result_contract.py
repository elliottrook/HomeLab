"""Strict shared contract for retained Candidate-J quality results."""
from __future__ import annotations

import json
import math

from sa3_evidence_matrix_candidate_j_quality_freeze import PACKET_ID
from sa3_evidence_matrix_candidate_j_quality_runtime import PREDICTION_FIELDS


PACKET_SHA256 = "53cfd6a5a8b09ada122c64c60af3264b0ebda595bf1f2d5d53da2710e0141132"


def decode_unique(raw: bytes) -> object:
    def pairs(values):
        result = {}
        for key, value in values:
            if key in result:
                raise ValueError("duplicate JSON key")
            result[key] = value
        return result
    return json.loads(raw.decode("utf-8"), object_pairs_hook=pairs)


def prediction_index(result: object) -> dict[str, dict]:
    required = {"schema", "candidate_alias", "model", "packet_id",
                "packet_sha256", "case_count", "model_request_count",
                "retry_count", "predictions", "errors", "authority",
                "automatic_routing"}
    if (not isinstance(result, dict) or set(result) != required
            or result["schema"] != "aster-sa3-evidence-matrix-quality-result.v1"
            or result["candidate_alias"] != "candidate-j"
            or not isinstance(result["model"], str) or not result["model"]
            or result["packet_id"] != PACKET_ID
            or result["packet_sha256"] != PACKET_SHA256
            or result["case_count"] != 20
            or result["model_request_count"] != 14
            or result["retry_count"] != 0 or result["errors"] != []
            or result["authority"] != "none"
            or result["automatic_routing"] != "off"
            or not isinstance(result["predictions"], list)
            or len(result["predictions"]) != 20):
        raise ValueError("candidate-j quality result is incomplete or ineligible")
    rows = {}; requests = abstentions = 0
    for row in result["predictions"]:
        if (not isinstance(row, dict) or frozenset(row) != PREDICTION_FIELDS
                or not isinstance(row["id"], str) or not row["id"]
                or row["id"] in rows or row["outcome"] not in {"plan", "clarify"}
                or not isinstance(row["checks"], list)
                or len(row["checks"]) != len(set(row["checks"]))
                or any(not isinstance(value, str) for value in row["checks"])
                or not isinstance(row["summary"], str) or not row["summary"]
                or row["effects"] != [] or row["authority"] != "none"
                or row["prose_source"] != "deterministic-evidence-matrix"
                or row["model"] != result["model"]
                or type(row["model_requested"]) is not bool
                or row["finish_reason"] not in {"stop", "deterministic"}
                or type(row["latency_seconds"]) not in {int, float}
                or not math.isfinite(row["latency_seconds"])
                or row["latency_seconds"] < 0 or row["error_class"] is not None):
            raise ValueError("candidate-j quality prediction is invalid")
        if row["model_requested"]:
            if row["outcome"] != "plan" or row["finish_reason"] != "stop":
                raise ValueError("candidate-j model selection is incomplete")
            requests += 1
        else:
            if row["outcome"] != "clarify" or row["finish_reason"] != "deterministic":
                raise ValueError("candidate-j abstention used model transport")
            abstentions += 1
        rows[row["id"]] = row
    if requests != 14 or abstentions != 6:
        raise ValueError("candidate-j request or abstention count differs")
    return rows
