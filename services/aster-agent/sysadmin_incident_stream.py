"""Presentation-only SSE frames for persisted sysadmin incident state.

This module deliberately reads local incident state only. It does not expose
facts, hypotheses, prompts, model reasoning, credentials or a live adapter.
The gateway integration remains a separately reviewed later change.
"""
from __future__ import annotations

import json
import hashlib
from datetime import datetime
from typing import Any

from sysadmin_incident_store import IncidentStore


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
    next_step = dict(incident["next"])
    if "reason" in next_step:
        next_step["reason"] = "Review the next registered observation."
    return {
        "schema_version": 2,
        "incident_id": incident["incident_id"],
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
        "incident_id": presentation["incident_id"],
        "observation_count": presentation["observation_count"],
    }
    return [
        "event: aster.progress\ndata: " + json.dumps(progress, separators=(",", ":")) + "\n\n",
        "event: aster.incident\ndata: " + json.dumps(presentation, separators=(",", ":")) + "\n\n",
        "data: [DONE]\n\n",
    ]
