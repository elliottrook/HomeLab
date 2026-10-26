"""Build an implementation-blind comparison of fixed Speech and aggregate answers."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from fixed_speech_response import render_observation


SCHEMA = "aster-fixed-speech-blind-comparison.v1"
REVIEW_SCHEMA = "aster-fixed-speech-blind-review.v1"
SALT = "aster-fixed-speech-comparison-v1"


def canonical(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def _aggregate_answer(case: dict[str, Any]) -> str:
    aggregate = case["aggregate"]
    checks = aggregate["checks"]
    summaries = "; ".join(
        f"{check['name']}: {check['status']} — {check['summary']}" for check in checks
    )
    return (
        f"The sanitized HomeLab health report is {aggregate['status']} as of "
        f"{aggregate['generated_at']}. Reported checks: {summaries}"
    )


def fixed_slot(case_id: str) -> str:
    digest = hashlib.sha256(f"{SALT}:{case_id}".encode()).digest()
    return "A" if digest[0] % 2 == 0 else "B"


def validate_source(value: dict[str, Any]) -> None:
    if set(value) != {"schema", "status", "cases"} or value["schema"] != SCHEMA:
        raise ValueError("source fields differ")
    if value["status"] != "preregistered-synthetic":
        raise ValueError("source status differs")
    cases = value["cases"]
    if not isinstance(cases, list) or len(cases) != 8:
        raise ValueError("exactly eight cases required")
    expected_ids = [f"fs-cmp-{number:02d}" for number in range(1, 9)]
    if [case.get("id") for case in cases] != expected_ids:
        raise ValueError("case identities differ")
    states: dict[str, int] = {state: 0 for state in ("ok", "warn", "fail", "unavailable")}
    for case in cases:
        if set(case) != {"id", "question", "observation", "aggregate"}:
            raise ValueError("case fields differ")
        observation = case["observation"]
        state = observation.get("state") if isinstance(observation, dict) else None
        if state not in states:
            raise ValueError("observation state differs")
        states[state] += 1
        # render_observation is the strict fixed-observation validator.
        render_observation(observation)
        aggregate = case["aggregate"]
        if not isinstance(aggregate, dict) or set(aggregate) != {
            "generated_at", "status", "checks"
        }:
            raise ValueError("aggregate fields differ")
        if aggregate["status"] not in {"healthy", "warning", "failed"}:
            raise ValueError("aggregate state differs")
        if not isinstance(aggregate["checks"], list) or not aggregate["checks"]:
            raise ValueError("aggregate checks differ")
        for check in aggregate["checks"]:
            if not isinstance(check, dict) or set(check) != {"name", "status", "summary"}:
                raise ValueError("aggregate check fields differ")
            if check["status"] not in {"pass", "warn", "fail"}:
                raise ValueError("aggregate check state differs")
            if not all(isinstance(check[key], str) for key in ("name", "summary")):
                raise ValueError("aggregate check text differs")
    if states != {state: 2 for state in states}:
        raise ValueError("states must be balanced")


def build_packet(raw: bytes) -> tuple[dict[str, Any], dict[str, Any]]:
    source = json.loads(raw)
    validate_source(source)
    source_sha = hashlib.sha256(raw).hexdigest()
    packet_cases = []
    key_rows = []
    for case in source["cases"]:
        fixed = render_observation(case["observation"])
        aggregate = _aggregate_answer(case)
        slot = fixed_slot(case["id"])
        responses = {slot: fixed, "B" if slot == "A" else "A": aggregate}
        packet_cases.append({
            "id": case["id"],
            "question": case["question"],
            "responses": responses,
        })
        key_rows.append({"id": case["id"], "fixed_slot": slot})
    packet = {
        "schema": "aster-fixed-speech-blind-packet.v1",
        "source_sha256": source_sha,
        "candidate_identity": "hidden",
        "acceptance_result": "hidden",
        "rubric": {
            "preferred": ["A", "B", "tie", "neither"],
            "dimensions": [
                "answers_question", "state_accuracy", "evidence_scope",
                "freshness", "limitation_calibration",
            ],
            "unsafe_claims": ["cause", "repair", "authority", "broader_health"],
        },
        "cases": packet_cases,
    }
    packet_sha = hashlib.sha256(canonical(packet)).hexdigest()
    template = {
        "schema": REVIEW_SCHEMA,
        "packet_sha256": packet_sha,
        "reviewer": "",
        "implementation_blind": True,
        "cases": [{
            "id": case["id"], "preferred": "",
            "dimensions": {dimension: {"A": False, "B": False} for dimension in packet["rubric"]["dimensions"]},
            "unsafe_claims": {"A": [], "B": []},
            "note": "",
        } for case in packet_cases],
    }
    key = {
        "schema": "aster-fixed-speech-blind-key.v1",
        "source_sha256": source_sha,
        "packet_sha256": packet_sha,
        "rows": key_rows,
    }
    return packet, {"template": template, "key": key}


def main() -> None:
    source_path = Path(__file__).with_name("fixed-speech-blind-comparison-v1.json")
    packet, artifacts = build_packet(source_path.read_bytes())
    print(json.dumps({"packet": packet, **artifacts}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
