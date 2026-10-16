"""Presentation-only SSE frames for persisted sysadmin incident state.

This module deliberately reads local incident state only. It does not expose
incident identity, facts, hypotheses, prompts, model reasoning, credentials
or a live adapter. The caller keeps the internal incident ID for reconnect;
the presentation stream needs no copy of that unrestricted text field.
The gateway integration remains a separately reviewed later change.
"""
from __future__ import annotations

import json
import hashlib
from datetime import datetime
from typing import Any

from sysadmin_incident_store import IncidentStore
from sysadmin_investigation import InvestigationError, REGISTERED_OBSERVATIONS


NEXT_REASONS = {
    "bounded": "Observation limit reached; review or close the investigation.",
    "sufficient_or_escalate": "Planned observations complete; review the evidence.",
    "proposed_read_only": "Review the next registered observation.",
}


def incident_presentation(snapshot: dict[str, Any]) -> dict[str, Any]:
    """Reduce a persisted incident to a safe, concise UI presentation shape."""
    incident = snapshot["incident"]
    evidence = [
        {
            # Producer-controlled IDs, summaries and source labels are retained
            # in the owner-only incident record, never copied into the UI.
            "evidence_ref": hashlib.sha256(item["evidence_id"].encode()).hexdigest()[:16],
            "target": item["target"],
            "kind": item["kind"],
            "state": item["state"],
            "observed_at": item["observed_at"],
            "age_seconds": item["age_seconds"],
            "summary": f"{item['target']} {item['kind']}: {item['state']}",
            "truncated": item["truncated"],
        }
        for item in incident["observations"]
    ]
    # Build the presentation from a fixed contract. Copying the persisted
    # next-step dict would turn future producer fields into accidental egress.
    raw_next = incident["next"]
    if not isinstance(raw_next, dict):
        raise InvestigationError("invalid next observation state")
    state = raw_next.get("state")
    if not isinstance(state, str) or state not in NEXT_REASONS:
        raise InvestigationError("invalid next observation state")
    next_step = {"state": state, "reason": NEXT_REASONS[state]}
    if state == "proposed_read_only":
        target = raw_next.get("target")
        kind = raw_next.get("kind")
        if (not isinstance(target, str) or not isinstance(kind, str)
                or target not in REGISTERED_OBSERVATIONS
                or kind not in REGISTERED_OBSERVATIONS[target]):
            raise InvestigationError("next observation is not registered")
        next_step.update({"target": target, "kind": kind, "execution": "not performed by the investigation loop"})
    return {
        "schema_version": 2,
        "title": "Read-only investigation",
        "observation_count": incident["observation_count"],
        "evidence": evidence,
        "next": next_step,
    }


def reconnect_frames(store: IncidentStore, incident_id: str, now: datetime) -> list[str]:
    """Build deterministic frames a later authenticated SSE route can relay."""
    presentation = incident_presentation(store.reconnect_snapshot(incident_id, now))
    progress = {
        "type": "aster.progress",
        "state": "reconnected",
        "observation_count": presentation["observation_count"],
    }
    return [
        "event: aster.progress\ndata: " + json.dumps(progress, separators=(",", ":")) + "\n\n",
        "event: aster.incident\ndata: " + json.dumps(presentation, separators=(",", ":")) + "\n\n",
        "data: [DONE]\n\n",
    ]
