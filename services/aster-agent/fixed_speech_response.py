"""Deterministic user-facing text for the fixed Aster Speech observation."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from speech_catalogue_incident_adapter import MAX_AGE


SOURCE = "homelab-doctor-catalogue/v3"
STATES = {"ok": "OK", "warn": "WARNING", "fail": "FAILED"}
LIMITATION = (
    "This fixed observation cannot identify which speech component caused a "
    "failure or authorize a repair, and it does not establish broader system health."
)


class FixedSpeechResponseDenied(ValueError):
    pass


def render_observation(observation: Any) -> str:
    if not isinstance(observation, dict) or set(observation) != {
        "source", "state", "observed_at", "age_seconds", "facts",
    }:
        raise FixedSpeechResponseDenied("fixed speech observation fields differ")
    if observation["source"] != SOURCE:
        raise FixedSpeechResponseDenied("fixed speech source differs")
    state = observation["state"]
    if state not in {*STATES, "unavailable"}:
        raise FixedSpeechResponseDenied("fixed speech state differs")
    age = observation["age_seconds"]
    if type(age) is not int or not 0 <= age <= int(MAX_AGE.total_seconds()):
        raise FixedSpeechResponseDenied("fixed speech age differs")
    observed_at = observation["observed_at"]
    if not isinstance(observed_at, str):
        raise FixedSpeechResponseDenied("fixed speech timestamp differs")
    try:
        timestamp = datetime.fromisoformat(observed_at.replace("Z", "+00:00"))
    except ValueError as error:
        raise FixedSpeechResponseDenied("fixed speech timestamp differs") from error
    if timestamp.tzinfo is None:
        raise FixedSpeechResponseDenied("fixed speech timestamp must be timezone-aware")
    if state == "unavailable":
        if observation["facts"] != {}:
            raise FixedSpeechResponseDenied("unavailable speech facts differ")
        opening = "The named Aster Speech check is unavailable."
        scope = "No speech-health fact is available from this observation."
    else:
        if observation["facts"] != {"check_id": "aster.speech"}:
            raise FixedSpeechResponseDenied("fixed speech fact boundary differs")
        opening = f"The aster.speech check reports {STATES[state]}."
        scope = "This evidence covers only the named aster.speech check."
    freshness = f"It was observed at {observed_at} and is {age} seconds old."
    return " ".join((opening, freshness, scope, LIMITATION))
