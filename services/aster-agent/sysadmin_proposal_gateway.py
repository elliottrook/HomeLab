"""Bind one sanitized SA3 model proposal to the current incident journal.

This adapter composes the existing local-model transport, trusted proposal
boundary and incident store.  It cannot execute an observation or effect.  A
proposal is accepted only if the incident state is still current when the
journal performs its atomic state-digest check.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable

from sysadmin_incident_store import IncidentStore
from sysadmin_investigation import InvestigationError
from sysadmin_proposal_boundary import propose_follow_up
from sysadmin_proposal_transport import request_model_proposal


def propose_and_bind_follow_up(
    store: IncidentStore,
    incident_id: str,
    api_key: str,
    *,
    transport: Callable[[dict[str, Any], str], dict[str, Any]] = request_model_proposal,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Request and journal exactly one no-effect proposal for current state."""
    if not isinstance(store, IncidentStore):
        raise InvestigationError("invalid incident store")
    if not isinstance(incident_id, str) or not incident_id:
        raise InvestigationError("invalid incident identity")
    if not isinstance(api_key, str) or not api_key:
        raise InvestigationError("existing model authentication is required")
    if not callable(transport):
        raise InvestigationError("proposal transport is not callable")
    now = now or datetime.now(timezone.utc)

    # Refuse before a model call when a decision already awaits consumption.
    if store.pending_follow_up(incident_id, now) is not None:
        raise InvestigationError("incident already has a pending follow-up")

    incident = store.load(incident_id, now)
    decision = propose_follow_up(
        incident,
        lambda request: transport(request, api_key),
    )

    # bind_follow_up reloads the incident and rechecks its state digest inside
    # the journal transaction.  Any observation written during the model call
    # therefore makes this proposal stale and fails closed.
    store.bind_follow_up(
        {
            "schema_version": decision["schema_version"],
            "incident_id": incident_id,
            "state_digest": decision["bound_state_digest"],
            "hypothesis_summary": decision["hypothesis_summary"],
            "disposition": decision["disposition"],
            "target": None if decision["request"] is None else decision["request"]["target"],
            "kind": None if decision["request"] is None else decision["request"]["kind"],
        },
        now,
    )
    return store.followup_journal_snapshot(incident_id, now)
