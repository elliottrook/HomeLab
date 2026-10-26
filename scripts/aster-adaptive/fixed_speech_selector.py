"""Offline selector boundary for the fixed Aster Speech observation.

This module proposes one local route and validates its returned answer.  It
never grants the broker capability or enables automatic routing.
"""

from __future__ import annotations

from typing import Any

from contracts import (
    RequestInterpretation,
    RouteProposal,
    contract_digest,
    validate_route,
)


CAPABILITY = "diagnostic.aster-speech.latest"
BACKEND = "aster-fixed-speech-caller"
SOURCE = "homelab-doctor-catalogue/v3"
MAX_ANSWER_BYTES = 4096


def select_route(
    interpretation: RequestInterpretation, *, now: int, ttl_seconds: int = 30,
) -> RouteProposal | None:
    """Return the one exact local proposal, or decline this narrow selector."""
    if type(now) is not int or type(ttl_seconds) is not int or not 1 <= ttl_seconds <= 30:
        raise ValueError("fixed Speech route time boundary differs")
    if (
        interpretation.request_family != "read-only-investigation"
        or interpretation.sensitivity not in {"public", "internal"}
        or interpretation.capability_needs != (CAPABILITY,)
        or interpretation.ambiguity != "clear"
        or interpretation.disposition != "route"
        or interpretation.reason != "understood"
        or interpretation.authorization != "not-granted"
    ):
        return None
    route = RouteProposal(
        request_id=interpretation.request_id,
        principal_ref=interpretation.principal_ref,
        interpretation_digest=contract_digest(interpretation),
        status="local",
        backend_id=BACKEND,
        egress="local",
        reason="deterministic-match",
        policy_digest=interpretation.policy_digest,
        expires_at=now + ttl_seconds,
        authorization="not-granted",
    )
    validate_route(interpretation, route, now=now)
    return route


def accept_answer(
    interpretation: RequestInterpretation,
    route: RouteProposal,
    result: Any,
    *,
    now: int,
) -> dict[str, Any]:
    """Validate a fixed-caller result without widening its evidence or authority."""
    validate_route(interpretation, route, now=now)
    if (
        interpretation.capability_needs != (CAPABILITY,)
        or route.status != "local"
        or route.backend_id != BACKEND
        or route.egress != "local"
        or route.authorization != "not-granted"
    ):
        raise ValueError("fixed Speech route boundary differs")
    if not isinstance(result, dict) or set(result) != {
        "schema", "capability", "observation", "answer", "authority",
    }:
        raise ValueError("fixed Speech answer fields differ")
    if result["schema"] != 2 or result["capability"] != CAPABILITY:
        raise ValueError("fixed Speech answer identity differs")
    if result["authority"] != "not-granted":
        raise ValueError("fixed Speech answer claims authority")
    answer = result["answer"]
    if not isinstance(answer, str) or not answer.strip() or len(answer.encode()) > MAX_ANSWER_BYTES:
        raise ValueError("fixed Speech answer text differs")
    observation = result["observation"]
    if not isinstance(observation, dict) or set(observation) != {
        "source", "state", "observed_at", "age_seconds", "facts",
    }:
        raise ValueError("fixed Speech observation fields differ")
    state = observation.get("state")
    expected_facts = {} if state == "unavailable" else {"check_id": "aster.speech"}
    if (
        observation.get("source") != SOURCE
        or state not in {"ok", "warn", "fail", "unavailable"}
        or not isinstance(observation.get("observed_at"), str)
        or type(observation.get("age_seconds")) is not int
        or not 0 <= observation["age_seconds"] <= 129600
        or observation.get("facts") != expected_facts
    ):
        raise ValueError("fixed Speech observation boundary differs")
    return {
        "schema": "selected-answer.v1",
        "request_id": interpretation.request_id,
        "route_digest": contract_digest(route),
        "answer": answer,
        "evidence": {"capability": CAPABILITY, "state": state},
        "authorization": "not-granted",
    }
