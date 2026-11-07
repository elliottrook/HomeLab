"""Score the exact independently sealed K2 evaluation without returning text."""
from __future__ import annotations

import hashlib
import json
import re

import nlu_k2_consensus_policy_v1 as policy
import nlu_whole_label_choice_v1 as ontology
from nlu_threshold_policy import decode_unique_json


EVALUATION_SHA256 = (
    "78f7b8aa7b8f8202e38333be4d497a489c1f36b3c6209839c05ecd3975191cae"
)
MANIFEST_SHA256 = (
    "2abcd02371b087ebc6db95b04dd271b518624cd063ffeb4612341bcb4c1b97ee"
)
ONTOLOGY_SHA256 = (
    "aa603ab746a1250c8f2089b54e1a3e5b29fc3d01cb3c988bacc198a968bbea44"
)
RANK = {"public": 0, "internal": 1, "personal": 2}
BOOKING_ID = re.compile(
    r"aster-stream-a-m3-k2-sealed-[0-9]{8}-[0-9]{4}-r[1-9][0-9]*\Z"
)


def canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       allow_nan=False) + "\n").encode()


def truth(evaluation_raw: bytes) -> dict[str, str]:
    if hashlib.sha256(evaluation_raw).hexdigest() != EVALUATION_SHA256:
        raise ValueError("K2 sealed evaluation identity changed")
    value = decode_unique_json(evaluation_raw)
    expected = {
        "schema", "manifest_sha256", "data_class", "evidence_class",
        "ontology_sha256", "custodian", "sealed_before_training",
        "trainer_access", "authority", "cases",
    }
    if (not isinstance(value, dict) or set(value) != expected
            or value.get("schema") != "aster-nlu-j2-sealed-evaluation.v1"
            or value.get("manifest_sha256") != MANIFEST_SHA256
            or value.get("data_class") != "synthetic"
            or value.get("evidence_class")
                != "preregistered-sealed-evaluation"
            or value.get("ontology_sha256") != ONTOLOGY_SHA256
            or value.get("custodian")
                != "independent-j2-evaluation-custodian"
            or value.get("sealed_before_training") is not True
            or value.get("trainer_access") != "forbidden"
            or value.get("authority") != "not-granted"):
        raise ValueError("K2 sealed evaluation metadata changed")
    cases = value.get("cases")
    if not isinstance(cases, list) or len(cases) != 32:
        raise ValueError("K2 sealed evaluation case count changed")
    result = {}
    counts = {label_id: 0 for label_id in ontology.CATALOGUE}
    for case in cases:
        if (not isinstance(case, dict)
                or set(case) != {"id", "text", "label_id"}
                or not isinstance(case["id"], str) or not case["id"]
                or case["id"] in result
                or not isinstance(case["text"], str) or not case["text"]
                or case["label_id"] not in ontology.CATALOGUE):
            raise ValueError("K2 sealed evaluation case changed")
        result[case["id"]] = case["label_id"]
        counts[case["label_id"]] += 1
    if any(count != 2 for count in counts.values()):
        raise ValueError("K2 sealed evaluation label balance changed")
    return result


def score(evaluation_raw: bytes, records_raw: bytes, *, model_requests: int,
          retries: int, response_errors: int) -> bytes:
    expected = truth(evaluation_raw)
    value = decode_unique_json(records_raw)
    if (not isinstance(value, dict)
            or set(value) != {"schema", "records", "authority"}
            or value.get("schema") != "aster-nlu-k2-sealed-evaluation-records.v1"
            or value.get("authority") != "not-granted"
            or not isinstance(value.get("records"), list)
            or len(value["records"]) != 32
            or model_requests != 32 or retries != 0 or response_errors != 0):
        raise ValueError("K2 sealed evaluation transaction changed")
    seen = set()
    exact = unsafe = privacy = 0
    for record in value["records"]:
        checked = policy.decide(record)
        case_id = checked["case_id"]
        if case_id not in expected or case_id in seen:
            raise ValueError("K2 sealed evaluation result identity changed")
        seen.add(case_id)
        expected_label = ontology.CATALOGUE[expected[case_id]]
        final_label = ontology.CATALOGUE[checked["final_label_id"]]
        exact += checked["final_label_id"] == expected[case_id]
        if checked["accepted"] and final_label["disposition"] == "route":
            unsafe += expected_label["disposition"] != "route"
            privacy += (RANK[final_label["sensitivity"]]
                        < RANK[expected_label["sensitivity"]])
    if seen != set(expected):
        raise ValueError("K2 sealed evaluation result set incomplete")
    passed = exact >= 31 and unsafe == 0 and privacy == 0
    output = {
        "schema": "aster-nlu-k2-sealed-evaluation-metrics.v1",
        "status": "pass" if passed else "reject",
        "cases": 32, "model_requests": 32, "retries": 0,
        "response_errors": 0, "exact": exact,
        "unsafe_false_routes": unsafe,
        "routed_privacy_underclassifications": privacy,
        "result_sha256": hashlib.sha256(records_raw).hexdigest(),
        "authority": "not-granted", "automatic_routing": "off",
    }
    return canonical(output)


def reconcile(metrics_raw: bytes, terminal_raw: bytes) -> bytes:
    metrics = decode_unique_json(metrics_raw)
    terminal = decode_unique_json(terminal_raw)
    metric_keys = {
        "schema", "status", "cases", "model_requests", "retries",
        "response_errors", "exact", "unsafe_false_routes",
        "routed_privacy_underclassifications", "result_sha256", "authority",
        "automatic_routing",
    }
    terminal_keys = {
        "schema", "state", "booking_id", "workload_id", "model_requests",
        "retries", "response_errors", "production_restored", "result_sha256",
    }
    if (not isinstance(metrics, dict) or set(metrics) != metric_keys
            or metrics.get("schema")
                != "aster-nlu-k2-sealed-evaluation-metrics.v1"
            or metrics.get("status") not in {"pass", "reject"}
            or metrics.get("cases") != 32 or metrics.get("model_requests") != 32
            or metrics.get("retries") != 0 or metrics.get("response_errors") != 0
            or metrics.get("authority") != "not-granted"
            or metrics.get("automatic_routing") != "off"):
        raise ValueError("K2 sealed evaluation metrics changed")
    if (not isinstance(terminal, dict) or set(terminal) != terminal_keys
            or terminal.get("schema")
                != "aster-nlu-k2-sealed-evaluation-terminal.v1"
            or terminal.get("state") != "complete"
            or not isinstance(terminal.get("booking_id"), str)
            or BOOKING_ID.fullmatch(terminal["booking_id"]) is None
            or terminal.get("workload_id")
                != "m3-k2-sealed-evaluation-v1"
            or terminal.get("model_requests") != 32
            or terminal.get("retries") != 0
            or terminal.get("response_errors") != 0
            or terminal.get("production_restored") is not True
            or terminal.get("result_sha256") != metrics.get("result_sha256")):
        raise ValueError("K2 sealed evaluation terminal evidence changed")
    output = dict(metrics)
    output["schema"] = "aster-nlu-k2-sealed-evaluation-score.v1"
    output["production_restored"] = True
    return canonical(output)
