"""Deterministic user-facing text for the fixed Aster inference observation."""
from __future__ import annotations

from datetime import datetime
from typing import Any


SOURCE = "homelab-doctor-structured/v2"
STATES = {"ok": "OK", "warn": "WARNING", "fail": "FAILED"}
LIMITATION = (
    "This fixed observation alone cannot establish a cause or a repair, and "
    "it does not establish broader system health."
)


class FixedDoctorResponseDenied(ValueError):
    pass


def render_observation(observation: Any) -> str:
    """Validate the complete fixed observation and render bounded text."""
    if not isinstance(observation, dict) or set(observation) != {
        "source", "state", "observed_at", "age_seconds", "facts",
    }:
        raise FixedDoctorResponseDenied("fixed Doctor observation fields differ")
    if observation["source"] != SOURCE:
        raise FixedDoctorResponseDenied("fixed Doctor source differs")
    state = observation["state"]
    if state not in {*STATES, "unavailable"}:
        raise FixedDoctorResponseDenied("fixed Doctor state differs")
    age = observation["age_seconds"]
    if type(age) is not int or not 0 <= age <= 600:
        raise FixedDoctorResponseDenied("fixed Doctor age differs")
    observed_at = observation["observed_at"]
    if not isinstance(observed_at, str):
        raise FixedDoctorResponseDenied("fixed Doctor timestamp differs")
    try:
        timestamp = datetime.fromisoformat(observed_at.replace("Z", "+00:00"))
    except ValueError as error:
        raise FixedDoctorResponseDenied("fixed Doctor timestamp differs") from error
    if timestamp.tzinfo is None:
        raise FixedDoctorResponseDenied("fixed Doctor timestamp must be timezone-aware")

    if state == "unavailable":
        if observation["facts"] != {}:
            raise FixedDoctorResponseDenied("unavailable fixed Doctor facts differ")
        opening = "The named Aster inference check is unavailable."
        scope = "No inference-health fact is available from this observation."
    else:
        if observation["facts"] != {"check_id": "aster.agent_inference"}:
            raise FixedDoctorResponseDenied("fixed Doctor fact boundary differs")
        opening = f"The aster.agent_inference check reports {STATES[state]}."
        scope = "This evidence covers only the named aster.agent_inference check."
    freshness = f"It was observed at {observed_at} and is {age} seconds old."
    return " ".join((opening, freshness, scope, LIMITATION))
