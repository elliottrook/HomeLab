"""Offline candidate: minimal Doctor evidence permitted in model context.

The incident record is a local audit object, not a prompt. This projection
accepts only the two registered Doctor producers and reconstructs a small,
typed view; producer summaries and arbitrary facts never cross this boundary.
No live gateway imports this module.
"""
from __future__ import annotations

import re
from datetime import datetime, timedelta
from typing import Any

from doctor_incident_adapter import SOURCE as AGGREGATE_SOURCE
from doctor_structured_incident_adapter import CHECK_ID, SOURCE as STRUCTURED_SOURCE
from sysadmin_investigation import InvestigationError, Observation


MAX_MODEL_AGE = timedelta(hours=36)
UNAVAILABLE_REASONS = frozenset({
    "unsafe_file", "oversized", "invalid_schema", "invalid_timestamp",
    "future", "stale", "invalid_checks", "unreadable",
})


def project_doctor_for_model(observation: Observation, now: datetime) -> dict[str, Any]:
    """Return a fixed Doctor status view or refuse model egress.

    This is a source-specific allowlist, not a sanitizer for arbitrary text.
    An unavailable report may be displayed as unavailable, never as healthy.
    """
    if not isinstance(observation, Observation):
        raise InvestigationError("model projection requires an observation")
    if not isinstance(now, datetime) or now.tzinfo is None:
        raise InvestigationError("model projection requires an aware clock")
    record = observation.validate(now)
    if record["target"] != "homelab-doctor" or record["kind"] != "status":
        raise InvestigationError("unregistered model projection target")
    if record["source"] not in {AGGREGATE_SOURCE, STRUCTURED_SOURCE}:
        raise InvestigationError("unregistered Doctor producer")
    if timedelta(seconds=record["age_seconds"]) > MAX_MODEL_AGE:
        raise InvestigationError("Doctor evidence is stale")
    if record["truncated"]:
        raise InvestigationError("truncated Doctor evidence")

    facts = record["facts"]
    state = record["state"]
    source = record["source"]
    if source == AGGREGATE_SOURCE:
        if state == "unavailable":
            if (set(facts) != {"reason"} or type(facts["reason"]) is not str or
                    facts["reason"] not in UNAVAILABLE_REASONS):
                raise InvestigationError("invalid aggregate unavailability")
            projected_facts = {"unavailable_reason": facts["reason"]}
        else:
            if (set(facts) != {"check_count", "report_digest"} or
                    type(facts["check_count"]) is not int or not 0 <= facts["check_count"] <= 32 or
                    not isinstance(facts["report_digest"], str) or
                    not re.fullmatch(r"[0-9a-f]{24}", facts["report_digest"])):
                raise InvestigationError("invalid aggregate Doctor facts")
            projected_facts = {"check_count": facts["check_count"]}
    else:
        if state == "unavailable":
            if facts:
                raise InvestigationError("invalid structured unavailability")
            projected_facts = {}
        else:
            if (set(facts) != {"check_id", "report_digest"} or
                    facts["check_id"] != CHECK_ID or
                    not isinstance(facts["report_digest"], str) or
                    not re.fullmatch(r"[0-9a-f]{24}", facts["report_digest"])):
                raise InvestigationError("invalid structured Doctor facts")
            projected_facts = {"check_id": CHECK_ID}

    return {
        "source": source,
        "state": state,
        "observed_at": record["observed_at"],
        "age_seconds": record["age_seconds"],
        "facts": projected_facts,
    }
