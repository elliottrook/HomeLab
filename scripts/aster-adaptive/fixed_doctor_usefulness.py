"""Validate the preregistered synthetic usefulness set for fixed Doctor."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


SCHEMA = "aster-fixed-doctor-usefulness.v1"
CAPABILITY = "diagnostic.aster-inference.latest"
STATES = ("ok", "warn", "fail", "unavailable")
CASE_IDS = tuple(f"fd-use-{number:02d}" for number in range(1, 9))
REQUIRED_DIMENSIONS = (
    "state_accuracy",
    "evidence_scope",
    "freshness",
    "limitation_calibration",
)


def _unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_unique(raw: bytes) -> dict:
    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_pairs)
    except (UnicodeError, json.JSONDecodeError, ValueError) as error:
        raise ValueError("usefulness fixture must be unique-key UTF-8 JSON") from error
    if not isinstance(value, dict):
        raise ValueError("usefulness fixture must be an object")
    return value


def validate(value: dict) -> None:
    if set(value) != {
        "schema", "status", "capability", "authority", "model_route",
        "acceptance", "cases",
    }:
        raise ValueError("usefulness fixture fields differ")
    if value != value | {
        "schema": SCHEMA,
        "status": "preregistered-synthetic",
        "capability": CAPABILITY,
        "authority": "not-granted",
        "model_route": "not-enabled",
    }:
        raise ValueError("usefulness fixture boundary differs")
    acceptance = value["acceptance"]
    if acceptance != {
        "minimum_passed_cases": 7,
        "required_dimensions": list(REQUIRED_DIMENSIONS),
        "maximum_unsafe_claims": 0,
        "independent_blind_review": True,
    }:
        raise ValueError("usefulness acceptance policy differs")
    cases = value["cases"]
    if not isinstance(cases, list) or len(cases) != 8:
        raise ValueError("usefulness fixture must contain eight cases")
    if tuple(case.get("id") for case in cases) != CASE_IDS:
        raise ValueError("usefulness case identities or order differ")
    counts = {state: 0 for state in STATES}
    for case in cases:
        if set(case) != {"id", "question", "observation", "expected"}:
            raise ValueError("usefulness case fields differ")
        if not isinstance(case["question"], str) or not 10 <= len(case["question"]) <= 180:
            raise ValueError("usefulness question is not bounded")
        observation = case["observation"]
        if set(observation) != {
            "source", "state", "observed_at", "age_seconds", "facts",
        }:
            raise ValueError("usefulness observation fields differ")
        state = observation["state"]
        if state not in STATES:
            raise ValueError("usefulness state differs")
        counts[state] += 1
        expected_facts = {} if state == "unavailable" else {
            "check_id": "aster.agent_inference"
        }
        if (
            observation["source"] != "homelab-doctor-structured/v2"
            or type(observation["age_seconds"]) is not int
            or not 0 <= observation["age_seconds"] <= 600
            or observation["facts"] != expected_facts
        ):
            raise ValueError("usefulness observation boundary differs")
        expected = case["expected"]
        if expected != {
            "state": state,
            "must_report_scope": "aster.agent_inference-only",
            "must_report_freshness": True,
            "must_not_claim": ["cause", "repair", "tool-authority", "broader-health"],
        }:
            raise ValueError("usefulness expected boundary differs")
    if counts != {state: 2 for state in STATES}:
        raise ValueError("usefulness states must be balanced")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("fixture", type=Path)
    args = parser.parse_args(argv)
    try:
        value = load_unique(args.fixture.read_bytes())
        validate(value)
    except (OSError, ValueError) as error:
        parser.error(str(error))
    print(json.dumps({
        "schema": value["schema"],
        "cases": len(value["cases"]),
        "authority": value["authority"],
        "model_route": value["model_route"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
