"""Deterministic answer for the fixed Aster inference Doctor observation."""
from __future__ import annotations

import datetime as dt


STATES = {
    "ok": "OK",
    "warn": "WARNING",
    "fail": "FAILED",
}
LIMITATION = (
    "This fixed observation alone cannot establish a cause or a repair, and "
    "it does not establish broader system health."
)


def answer(case: dict) -> str:
    if not isinstance(case, dict) or set(case) != {
        "id", "question", "observation", "expected",
    }:
        raise ValueError("fixed Doctor case fields differ")
    observation = case["observation"]
    if not isinstance(observation, dict) or set(observation) != {
        "source", "state", "observed_at", "age_seconds", "facts",
    }:
        raise ValueError("fixed Doctor observation fields differ")
    if observation["source"] != "homelab-doctor-structured/v2":
        raise ValueError("fixed Doctor source differs")
    state = observation["state"]
    if state not in {*STATES, "unavailable"}:
        raise ValueError("fixed Doctor state differs")
    age = observation["age_seconds"]
    if type(age) is not int or not 0 <= age <= 600:
        raise ValueError("fixed Doctor age differs")
    observed_at = observation["observed_at"]
    if not isinstance(observed_at, str):
        raise ValueError("fixed Doctor timestamp differs")
    try:
        parsed = dt.datetime.fromisoformat(observed_at.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError("fixed Doctor timestamp differs") from error
    if parsed.tzinfo is None:
        raise ValueError("fixed Doctor timestamp must be timezone-aware")

    if state == "unavailable":
        opening = "The named Aster inference check is unavailable."
        scope = "No inference-health fact is available from this observation."
    else:
        if observation["facts"] != {"check_id": "aster.agent_inference"}:
            raise ValueError("fixed Doctor fact boundary differs")
        opening = f"The aster.agent_inference check reports {STATES[state]}."
        scope = "This evidence covers only the named aster.agent_inference check."
    freshness = f"It was observed at {observed_at} and is {age} seconds old."
    return " ".join((opening, freshness, scope, LIMITATION))

