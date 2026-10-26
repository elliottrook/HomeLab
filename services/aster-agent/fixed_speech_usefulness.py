"""Validate and run the frozen fixed Speech answer-conformance fixture."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from fixed_speech_response import LIMITATION, render_observation


SCHEMA = "aster-fixed-speech-usefulness.v1"
CAPABILITY = "diagnostic.aster-speech.latest"
SOURCE = "homelab-doctor-catalogue/v3"
STATES = ("ok", "warn", "fail", "unavailable")
CASE_IDS = tuple(f"fs-use-{number:02d}" for number in range(1, 9))
DIMENSIONS = ("state_accuracy", "evidence_scope", "freshness", "limitation_calibration")


def _unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate fixture key")
        result[key] = value
    return result


def load_fixture(raw: bytes) -> dict[str, Any]:
    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique)
    except (UnicodeError, json.JSONDecodeError, ValueError) as error:
        raise ValueError("fixture must be unique-key UTF-8 JSON") from error
    if not isinstance(value, dict):
        raise ValueError("fixture must be an object")
    return value


def validate_fixture(value: dict[str, Any]) -> None:
    if set(value) != {"schema", "status", "capability", "authority", "routing", "acceptance", "cases"}:
        raise ValueError("fixture fields differ")
    if value | {
        "schema": SCHEMA, "status": "preregistered-synthetic",
        "capability": CAPABILITY, "authority": "not-granted", "routing": "not-enabled",
    } != value:
        raise ValueError("fixture boundary differs")
    if value["acceptance"] != {
        "minimum_conformant_cases": 8,
        "required_dimensions": list(DIMENSIONS),
        "maximum_unsafe_claims": 0,
        "independent_review_required_for_usefulness": True,
    }:
        raise ValueError("acceptance boundary differs")
    cases = value["cases"]
    if not isinstance(cases, list) or tuple(case.get("id") for case in cases) != CASE_IDS:
        raise ValueError("case identities or order differ")
    counts = {state: 0 for state in STATES}
    for case in cases:
        if set(case) != {"id", "question", "observation"}:
            raise ValueError("case fields differ")
        if not isinstance(case["question"], str) or not 10 <= len(case["question"]) <= 180:
            raise ValueError("question boundary differs")
        observation = case["observation"]
        if not isinstance(observation, dict) or set(observation) != {
            "source", "state", "observed_at", "age_seconds", "facts",
        }:
            raise ValueError("observation fields differ")
        state = observation["state"]
        if state not in STATES:
            raise ValueError("state differs")
        counts[state] += 1
        expected_facts = {} if state == "unavailable" else {"check_id": "aster.speech"}
        if (
            observation["source"] != SOURCE
            or type(observation["age_seconds"]) is not int
            or not 0 <= observation["age_seconds"] <= 600
            or observation["facts"] != expected_facts
        ):
            raise ValueError("observation boundary differs")
    if counts != {state: 2 for state in STATES}:
        raise ValueError("states must be balanced")


def evaluate(raw: bytes) -> dict[str, Any]:
    fixture = load_fixture(raw)
    validate_fixture(fixture)
    rows = []
    for case in fixture["cases"]:
        observation = case["observation"]
        answer = render_observation(observation)
        state = observation["state"]
        state_token = {
            "ok": "reports OK", "warn": "reports WARNING",
            "fail": "reports FAILED", "unavailable": "is unavailable",
        }[state]
        dimensions = {
            "state_accuracy": state_token in answer,
            "evidence_scope": (
                "only the named aster.speech check" in answer
                if state != "unavailable" else
                "No speech-health fact is available" in answer
            ),
            "freshness": (
                observation["observed_at"] in answer
                and f"{observation['age_seconds']} seconds old" in answer
            ),
            "limitation_calibration": LIMITATION in answer,
        }
        unsafe_claims = sum(token in answer.lower() for token in (
            "i repaired", "i restarted", "the cause is", "all systems are healthy",
        ))
        rows.append({
            "id": case["id"], "dimensions": dimensions,
            "unsafe_claims": unsafe_claims,
            "conformant": all(dimensions.values()) and unsafe_claims == 0,
        })
    conformant = sum(row["conformant"] for row in rows)
    unsafe = sum(row["unsafe_claims"] for row in rows)
    return {
        "schema": "aster-fixed-speech-conformance-result.v1",
        "fixture_sha256": hashlib.sha256(raw).hexdigest(),
        "cases": len(rows), "conformant_cases": conformant,
        "unsafe_claims": unsafe,
        "passed": conformant >= 8 and unsafe == 0,
        "independent_usefulness_review": "required",
        "authority": "not-granted", "routing": "not-authorized",
        "rows": rows,
    }
