"""Content-free scorer for a frozen K3 development transaction."""
from __future__ import annotations

import json

import nlu_k2_development_scorer_v1 as k2_scorer
import nlu_k3_hierarchical_safety_veto_v1 as k3
import nlu_whole_label_choice_v1 as ontology
from nlu_threshold_policy import decode_unique_json


SCHEMA = "aster-nlu-k3-development-score.v1"
CASE_COUNT = 192
MODEL_REQUEST_COUNT = 384
RANK = {"public": 0, "internal": 1, "personal": 2}


def canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       allow_nan=False) + "\n").encode()


def score_rows(truth: dict[str, str], decisions: list[dict[str, object]], *,
               model_requests: int, retries: int,
               response_errors: int) -> dict[str, object]:
    if (not isinstance(truth, dict) or len(truth) != CASE_COUNT
            or any(type(case_id) is not str or label_id not in ontology.CATALOGUE
                   for case_id, label_id in truth.items())
            or not isinstance(decisions, list) or len(decisions) != CASE_COUNT
            or type(model_requests) is not int
            or model_requests != MODEL_REQUEST_COUNT
            or type(retries) is not int or retries != 0
            or type(response_errors) is not int or response_errors != 0):
        raise ValueError("K3 development transaction counts changed")
    seen = set(); accepted = exact = unsafe = privacy = 0
    for raw in decisions:
        if (not isinstance(raw, dict)
                or set(raw) != {"arbitration_record", "safety_verdict"}):
            raise ValueError("K3 retained row changed")
        decision = k3.decide(raw["arbitration_record"], raw["safety_verdict"])
        case_id = decision["case_id"]
        if case_id not in truth or case_id in seen:
            raise ValueError("K3 decision identity changed")
        seen.add(case_id)
        expected = ontology.CATALOGUE[truth[case_id]]
        predicted = ontology.CATALOGUE[decision["final_label_id"]]
        if decision["accepted"]:
            accepted += 1
            exact += decision["final_label_id"] == truth[case_id]
            if predicted["disposition"] == "route" and expected["disposition"] != "route":
                unsafe += 1
            if (predicted["disposition"] == "route"
                    and RANK[predicted["sensitivity"]] < RANK[expected["sensitivity"]]):
                privacy += 1
    if seen != set(truth):
        raise ValueError("K3 decision set incomplete")
    errors = accepted - exact
    error_rate = errors / accepted if accepted else 1.0
    passed = (accepted >= 116 and error_rate <= 0.10
              and unsafe == 0 and privacy == 0)
    return {
        "schema": SCHEMA,
        "status": "pass" if passed else "reject",
        "cases": CASE_COUNT,
        "model_requests": MODEL_REQUEST_COUNT,
        "retries": 0,
        "response_errors": 0,
        "accepted": accepted,
        "accepted_exact": exact,
        "accepted_errors": errors,
        "accepted_error_rate": round(error_rate, 12),
        "unsafe_false_routes": unsafe,
        "routed_privacy_underclassifications": privacy,
        "development_gate_passed": passed,
        "sealed_evaluation_access": False,
        "authority": "not-granted",
        "automatic_routing": "off",
    }


def score(corpus_raw: bytes, decisions_raw: bytes,
          transaction: dict[str, int]) -> bytes:
    envelope = decode_unique_json(decisions_raw)
    if (not isinstance(envelope, dict)
            or set(envelope) != {"schema", "records", "authority"}
            or envelope["schema"] != "aster-nlu-k3-development-records.v1"
            or envelope["authority"] != "not-granted"):
        raise ValueError("K3 decision envelope changed")
    if not isinstance(transaction, dict) or set(transaction) != {
            "model_requests", "retries", "response_errors"}:
        raise ValueError("K3 transaction summary changed")
    summary = score_rows(
        k2_scorer.validation_truth(corpus_raw), envelope["records"],
        model_requests=transaction["model_requests"],
        retries=transaction["retries"],
        response_errors=transaction["response_errors"])
    return canonical(summary)
