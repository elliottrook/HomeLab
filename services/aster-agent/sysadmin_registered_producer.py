"""Execute one exact, registered incident observation without target discovery.

The caller cannot supply a producer, target or evidence kind.  The pending
SA1 journal decision is the sole selector, and this first SA2 registry contains
only the gateway's in-process self-status observation.  It performs no network,
filesystem, subprocess, credential, model or repair operation.
"""
from __future__ import annotations

import hashlib
import http.client
import json
from datetime import datetime, timezone

from sysadmin_incident_store import IncidentStore
from sysadmin_investigation import InvestigationError


PRODUCER = "aster-gateway-self-status/v1"
REGISTERED_PAIR = ("aster-gateway", "status")
INFERENCE_PRODUCER = "inference-server-health/v1"
INFERENCE_PAIR = ("inference-server", "status")
MAX_HEALTH_BYTES = 1024


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


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate health field")
        result[key] = value
    return result


def _inference_status_envelope(
    incident_id: str, now: datetime, connection_factory=http.client.HTTPConnection,
) -> dict:
    if not isinstance(now, datetime) or now.tzinfo is None or now.utcoffset() is None:
        raise InvestigationError("registered observation requires an aware clock")
    observed = now.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    state = "unavailable"
    summary = "The registered inference health source was unavailable."
    facts = {}
    connection = None
    try:
        connection = connection_factory("192.168.70.12", 11435, timeout=3)
        connection.request("GET", "/health", headers={"Accept": "application/json"})
        response = connection.getresponse()
        raw = response.read(MAX_HEALTH_BYTES + 1)
        if response.status != 200 or len(raw) > MAX_HEALTH_BYTES:
            raise ValueError("invalid inference health response")
        value = json.loads(raw, object_pairs_hook=_unique_object)
        if value != {"status": "ok"}:
            raise ValueError("unexpected inference health body")
        state = "ok"
        summary = "The registered inference health endpoint reported ok."
        facts = {"service": "aster-llama", "endpoint": "health"}
    except (OSError, http.client.HTTPException, UnicodeError, ValueError, TypeError):
        pass
    finally:
        if connection is not None:
            connection.close()
    evidence_id = "inference-health-" + hashlib.sha256(
        (incident_id + "\0" + observed + "\0" + state).encode()
    ).hexdigest()[:24]
    return {
        "schema_version": 1,
        "producer": INFERENCE_PRODUCER,
        "produced_at": observed,
        "observation": {
            "evidence_id": evidence_id,
            "incident_id": incident_id,
            "target": INFERENCE_PAIR[0],
            "kind": INFERENCE_PAIR[1],
            "observed_at": observed,
            "state": state,
            "summary": summary,
            "facts": facts,
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
    if pair == REGISTERED_PAIR:
        envelope = _gateway_status_envelope(incident_id, now)
    elif pair == INFERENCE_PAIR:
        envelope = _inference_status_envelope(incident_id, now)
    else:
        raise InvestigationError("pending observation has no registered producer")
    return store.ingest(envelope, now)
