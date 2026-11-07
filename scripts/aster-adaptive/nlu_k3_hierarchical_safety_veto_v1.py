"""Independent hierarchical safety veto for the K3 routing candidate.

The safety stage never sees final label IDs and cannot grant authority. K3 may
accept a shortlist arbitration only when this independently produced semantic
verdict agrees with the final coherent label on family, disposition,
sensitivity and ambiguity. No accepted decision executes a route.
"""
from __future__ import annotations

import json

import nlu_k2_consensus_policy_v1 as k2
import nlu_whole_label_choice_v1 as ontology
from nlu_threshold_policy import FAMILIES, decode_unique_json


MODEL = "aster-qwen3.5-9b"
SCHEMA = "aster-nlu-k3-hierarchical-safety-verdict.v1"
DECISION_SCHEMA = "aster-nlu-k3-hierarchical-safety-decision.v1"
DISPOSITIONS = ("route", "clarify", "abstain", "deny")
SENSITIVITIES = ("public", "internal", "personal")
AMBIGUITIES = ("clear", "ambiguous")
VERDICT_KEYS = {
    "schema", "request_family", "disposition", "sensitivity", "ambiguity",
    "route_eligible", "authority",
}
MODEL_VERDICT_KEYS = VERDICT_KEYS - {"schema", "authority"}
DECISION_KEYS = {
    "schema", "case_id", "shortlist_ids", "selected_label_id",
    "final_label_id", "safety_verdict", "accepted", "disposition",
    "authority", "route_effect", "automatic_routing",
}


def response_schema() -> dict[str, object]:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "request_family", "disposition", "sensitivity", "ambiguity",
            "route_eligible",
        ],
        "properties": {
            "request_family": {"type": "string", "enum": list(FAMILIES)},
            "disposition": {"type": "string", "enum": list(DISPOSITIONS)},
            "sensitivity": {"type": "string", "enum": list(SENSITIVITIES)},
            "ambiguity": {"type": "string", "enum": list(AMBIGUITIES)},
            "route_eligible": {"type": "boolean"},
        },
    }


def build_payload(request_text: str) -> bytes:
    if not isinstance(request_text, str) or not request_text.strip():
        raise ValueError("request text must be nonempty")
    policy = (
        "Independently classify one assistant request for safety evaluation. "
        "Return only request_family, disposition, sensitivity, ambiguity and "
        "route_eligible in the required JSON object. route_eligible must be "
        "true exactly when disposition is route and ambiguity is clear. Do "
        "not choose or mention a final label ID, provider, tool, permission, "
        "route target, reasoning or result."
    )
    value = {
        "model": MODEL,
        "temperature": 0,
        "seed": 20261107,
        "stream": False,
        "max_tokens": 64,
        "messages": [
            {"role": "system", "content": policy},
            {"role": "user", "content": request_text},
        ],
        "response_format": {"type": "json_object", "schema": response_schema()},
    }
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def validate_verdict(value: object) -> dict[str, object]:
    if (not isinstance(value, dict) or set(value) != VERDICT_KEYS
            or value.get("schema") != SCHEMA
            or value.get("request_family") not in FAMILIES
            or value.get("disposition") not in DISPOSITIONS
            or value.get("sensitivity") not in SENSITIVITIES
            or value.get("ambiguity") not in AMBIGUITIES
            or type(value.get("route_eligible")) is not bool
            or value.get("authority") != "not-granted"):
        raise ValueError("K3 safety verdict changed")
    eligible = value["disposition"] == "route" and value["ambiguity"] == "clear"
    if value["route_eligible"] is not eligible:
        raise ValueError("K3 route eligibility is inconsistent")
    return dict(value)


def parse_verdict(response_raw: bytes) -> dict[str, object]:
    envelope = decode_unique_json(response_raw)
    if not isinstance(envelope, dict) or set(envelope) != {"choices"}:
        raise ValueError("K3 response envelope changed")
    choices = envelope["choices"]
    if not isinstance(choices, list) or len(choices) != 1:
        raise ValueError("K3 response choice changed")
    choice = choices[0]
    if (not isinstance(choice, dict)
            or set(choice) != {"message", "finish_reason"}
            or choice["finish_reason"] != "stop"):
        raise ValueError("K3 response completion changed")
    message = choice["message"]
    if (not isinstance(message, dict) or set(message) != {"role", "content"}
            or message["role"] != "assistant"
            or not isinstance(message["content"], str)):
        raise ValueError("K3 response message changed")
    value = decode_unique_json(message["content"].encode())
    if not isinstance(value, dict) or set(value) != MODEL_VERDICT_KEYS:
        raise ValueError("K3 model verdict fields changed")
    value = {"schema": SCHEMA, **value, "authority": "not-granted"}
    return validate_verdict(value)


def decide(arbitration_record: dict[str, object],
           safety_verdict: object) -> dict[str, object]:
    arbitration = k2.decide(arbitration_record)
    verdict = validate_verdict(safety_verdict)
    final = ontology.CATALOGUE[arbitration["final_label_id"]]
    agreed = (
        verdict["request_family"] == final["request_family"]
        and verdict["disposition"] == final["disposition"]
        and verdict["sensitivity"] == final["sensitivity"]
        and verdict["ambiguity"] == final["ambiguity"]
        and verdict["route_eligible"]
            is (final["disposition"] == "route" and final["ambiguity"] == "clear")
    )
    return validate_decision({
        "schema": DECISION_SCHEMA,
        "case_id": arbitration["case_id"],
        "shortlist_ids": arbitration["shortlist_ids"],
        "selected_label_id": arbitration["selected_label_id"],
        "final_label_id": arbitration["final_label_id"],
        "safety_verdict": verdict,
        "accepted": agreed,
        "disposition": final["disposition"] if agreed else "abstain",
        "authority": "not-granted",
        "route_effect": False,
        "automatic_routing": "off",
    })


def validate_decision(value: object) -> dict[str, object]:
    if (not isinstance(value, dict) or set(value) != DECISION_KEYS
            or value.get("schema") != DECISION_SCHEMA
            or not isinstance(value.get("case_id"), str)
            or not value["case_id"]
            or not isinstance(value.get("shortlist_ids"), list)
            or len(value["shortlist_ids"]) != 4
            or len(set(value["shortlist_ids"])) != 4
            or any(type(item) is not str or item not in ontology.CATALOGUE
                   for item in value["shortlist_ids"])
            or value.get("selected_label_id") not in value["shortlist_ids"]
            or value.get("final_label_id") not in ontology.CATALOGUE
            or type(value.get("accepted")) is not bool
            or value.get("disposition") not in DISPOSITIONS
            or value.get("authority") != "not-granted"
            or value.get("route_effect") is not False
            or value.get("automatic_routing") != "off"):
        raise ValueError("K3 decision changed")
    verdict = validate_verdict(value["safety_verdict"])
    final = ontology.CATALOGUE[value["final_label_id"]]
    agreed = (
        verdict["request_family"] == final["request_family"]
        and verdict["disposition"] == final["disposition"]
        and verdict["sensitivity"] == final["sensitivity"]
        and verdict["ambiguity"] == final["ambiguity"]
        and verdict["route_eligible"]
            is (final["disposition"] == "route" and final["ambiguity"] == "clear")
    )
    expected_disposition = final["disposition"] if agreed else "abstain"
    if value["accepted"] is not agreed or value["disposition"] != expected_disposition:
        raise ValueError("K3 decision disagrees with safety verdict")
    return dict(value)
