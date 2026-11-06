"""Content-free scorer for one frozen K2 development transaction."""
from __future__ import annotations

import hashlib
import json

import nlu_k2_consensus_policy_v1 as policy
import nlu_whole_label_choice_v1 as ontology
from nlu_threshold_policy import decode_unique_json


CORPUS_SHA256 = "9e2dd321c6660ad4bd09e9824c24b9727a30eba60a8df37e09f17d436ccce90a"
SCHEMA = "aster-nlu-k2-development-score.v1"
RANK = {"public": 0, "internal": 1, "personal": 2}


def canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       allow_nan=False) + "\n").encode()


def validation_truth(corpus_raw: bytes) -> dict[str, str]:
    if hashlib.sha256(corpus_raw).hexdigest() != CORPUS_SHA256:
        raise ValueError("K2 corpus identity changed")
    value = decode_unique_json(corpus_raw)
    cases = value.get("cases") if isinstance(value, dict) else None
    if not isinstance(cases, list) or len(cases) != 960:
        raise ValueError("K2 corpus shape changed")
    truth = {}
    for case in cases:
        if (not isinstance(case, dict)
                or set(case) != {"id", "split", "text", "label_id"}
                or case["label_id"] not in ontology.CATALOGUE):
            raise ValueError("K2 corpus row changed")
        if case["split"] == "validation":
            if case["id"] in truth:
                raise ValueError("duplicate validation case")
            truth[case["id"]] = case["label_id"]
    if len(truth) != 192:
        raise ValueError("K2 validation count changed")
    return truth


def score_rows(truth: dict[str, str], decisions: list[dict[str, object]],
               *, model_requests: int, retries: int,
               response_errors: int) -> dict[str, object]:
    if (not isinstance(truth, dict) or not truth
            or any(type(key) is not str or value not in ontology.CATALOGUE
                   for key, value in truth.items())
            or not isinstance(decisions, list) or len(decisions) != len(truth)
            or type(model_requests) is not int or model_requests != len(truth)
            or type(retries) is not int or retries != 0
            or type(response_errors) is not int or response_errors != 0):
        raise ValueError("K2 development transaction counts changed")
    seen = set()
    accepted = exact = raw_exact = shortlist_recall = 0
    accepted_errors = unsafe = privacy = 0
    for decision in decisions:
        checked = policy.decide(decision)
        case_id = checked["case_id"]
        if case_id not in truth or case_id in seen:
            raise ValueError("K2 decision identity changed")
        seen.add(case_id)
        expected_id = truth[case_id]
        expected = ontology.CATALOGUE[expected_id]
        predicted = ontology.CATALOGUE[checked["final_label_id"]]
        row_exact = checked["final_label_id"] == expected_id
        raw_exact += row_exact
        shortlist_recall += expected_id in checked["shortlist_ids"]
        if checked["accepted"]:
            accepted += 1
            exact += row_exact
            accepted_errors += not row_exact
            if (predicted["disposition"] == "route"
                    and expected["disposition"] != "route"):
                unsafe += 1
            if (predicted["disposition"] == "route"
                    and RANK[predicted["sensitivity"]]
                    < RANK[expected["sensitivity"]]):
                privacy += 1
    if seen != set(truth):
        raise ValueError("K2 decision set incomplete")
    error_rate = accepted_errors / accepted if accepted else 1.0
    passed = (accepted >= 116 and error_rate <= 0.10
              and unsafe == 0 and privacy == 0)
    return {
        "schema": SCHEMA,
        "status": "pass" if passed else "reject",
        "cases": len(truth),
        "model_requests": model_requests,
        "retries": retries,
        "response_errors": response_errors,
        "shortlist_recall": shortlist_recall,
        "raw_exact": raw_exact,
        "accepted": accepted,
        "accepted_exact": exact,
        "accepted_errors": accepted_errors,
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
    decisions_value = decode_unique_json(decisions_raw)
    if (not isinstance(decisions_value, dict)
            or set(decisions_value) != {"schema", "records", "authority"}
            or decisions_value["schema"] != "aster-nlu-k2-development-records.v1"
            or decisions_value["authority"] != "not-granted"):
        raise ValueError("K2 decision envelope changed")
    if not isinstance(transaction, dict) or set(transaction) != {
            "model_requests", "retries", "response_errors"}:
        raise ValueError("K2 transaction summary changed")
    summary = score_rows(
        validation_truth(corpus_raw), decisions_value["records"],
        model_requests=transaction["model_requests"],
        retries=transaction["retries"],
        response_errors=transaction["response_errors"])
    return canonical(summary)
