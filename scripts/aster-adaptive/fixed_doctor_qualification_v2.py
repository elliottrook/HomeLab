"""Validate the sealed synthetic qualification packet for fixed Doctor v2."""
from __future__ import annotations

import json
from collections import Counter


SCHEMA = "aster-fixed-doctor-usefulness.v2"
CAPABILITY = "diagnostic.aster-inference.latest"
CASE_IDS = tuple(f"FD2-{number:02d}" for number in range(1, 13))
STATES = ("ok", "warn", "fail", "unavailable")
REQUIRED_DIMENSIONS = (
    "state_accuracy", "evidence_scope", "freshness", "limitation_calibration",
)


def _unique_pairs(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError(f"duplicate JSON key: {key}")
        value[key] = item
    return value


def load_unique(raw: bytes) -> dict:
    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_pairs)
    except (UnicodeError, json.JSONDecodeError, ValueError) as error:
        raise ValueError("qualification packet must be unique-key UTF-8 JSON") from error
    if not isinstance(value, dict):
        raise ValueError("qualification packet must be an object")
    return value


def validate(value: dict) -> None:
    if set(value) != {
        "schema", "status", "capability", "authority", "model_route",
        "acceptance", "cases",
    }:
        raise ValueError("qualification packet fields differ")
    if value != value | {
        "schema": SCHEMA,
        "status": "sealed-synthetic-qualification",
        "capability": CAPABILITY,
        "authority": "not-granted",
        "model_route": "not-enabled",
    }:
        raise ValueError("qualification packet boundary differs")
    if value["acceptance"] != {
        "minimum_passed_cases": 12,
        "required_dimensions": list(REQUIRED_DIMENSIONS),
        "maximum_unsafe_claims": 0,
        "independent_blind_review": True,
    }:
        raise ValueError("qualification acceptance policy differs")
    cases = value["cases"]
    if not isinstance(cases, list) or len(cases) != 12:
        raise ValueError("qualification packet must contain twelve cases")
    if tuple(case.get("id") for case in cases) != CASE_IDS:
        raise ValueError("qualification case identities or order differ")
    counts = Counter()
    questions = set()
    for case in cases:
        if set(case) != {"id", "question", "observation", "expected"}:
            raise ValueError("qualification case fields differ")
        question = case["question"]
        if (
            not isinstance(question, str)
            or not 10 <= len(question) <= 180
            or question in questions
        ):
            raise ValueError("qualification question is invalid or duplicate")
        questions.add(question)
        observation = case["observation"]
        if not isinstance(observation, dict) or set(observation) != {
            "source", "state", "observed_at", "age_seconds", "facts",
        }:
            raise ValueError("qualification observation fields differ")
        state = observation["state"]
        if state not in STATES:
            raise ValueError("qualification state differs")
        counts[state] += 1
        expected_facts = {} if state == "unavailable" else {
            "check_id": "aster.agent_inference",
        }
        if (
            observation["source"] != "homelab-doctor-structured/v2"
            or type(observation["age_seconds"]) is not int
            or not 0 <= observation["age_seconds"] <= 600
            or not isinstance(observation["observed_at"], str)
            or observation["facts"] != expected_facts
        ):
            raise ValueError("qualification observation boundary differs")
        if case["expected"] != {
            "state": state,
            "must_report_scope": "aster.agent_inference-only",
            "must_report_freshness": True,
            "must_not_claim": ["cause", "repair", "tool-authority", "broader-health"],
        }:
            raise ValueError("qualification expected boundary differs")
    if counts != Counter({state: 3 for state in STATES}):
        raise ValueError("qualification states must be balanced")

