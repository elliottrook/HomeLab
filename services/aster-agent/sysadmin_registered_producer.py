"""Execute one exact, registered incident observation without target discovery.

The caller cannot supply a producer, target or evidence kind.  The pending
SA1 journal decision is the sole selector, and this first SA2 registry contains
only the gateway's in-process self-status observation.  It performs no network,
filesystem, subprocess, credential, model or repair operation.
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone

from sysadmin_incident_store import IncidentStore
from sysadmin_investigation import InvestigationError


PRODUCER = "aster-gateway-self-status/v1"
REGISTERED_PAIR = ("aster-gateway", "status")


def _gateway_status_envelope(incident_id: str, now: datetime) -> dict:
    if not isinstance(now, datetime) or now.tzinfo is None or now.utcoffset() is None:
        raise InvestigationError("registered observation requires an aware clock")
    observed = now.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    evidence_id = "gateway-self-status-" + hashlib.sha256(
        (incident_id + "\0" + observed).encode()
    ).hexdigest()[:24]
    return {
        "schema_version": 1,
        "producer": PRODUCER,
        "produced_at": observed,
        "observation": {
            "evidence_id": evidence_id,
            "incident_id": incident_id,
            "target": REGISTERED_PAIR[0],
            "kind": REGISTERED_PAIR[1],
            "observed_at": observed,
            "state": "ok",
            "summary": "The Aster gateway handled its registered self-status observation.",
            "facts": {"service": "aster-agent", "availability": "serving"},
            "truncated": False,
        },
    }


def execute_registered_pending_observation(
    store: IncidentStore, incident_id: str, now: datetime,
) -> dict:
    """Run only the exact source registered for the pending journal decision."""
    if not isinstance(store, IncidentStore):
        raise InvestigationError("invalid incident store")
    pending = store.pending_follow_up(incident_id, now)
    if pending is None or pending.get("disposition") != "observe":
        raise InvestigationError("incident has no pending observation")
    request = pending.get("request")
    if not isinstance(request, dict):
        raise InvestigationError("pending observation request is invalid")
    pair = (request.get("target"), request.get("kind"))
    if pair != REGISTERED_PAIR:
        raise InvestigationError("pending observation has no registered producer")
    return store.ingest(_gateway_status_envelope(incident_id, now), now)
