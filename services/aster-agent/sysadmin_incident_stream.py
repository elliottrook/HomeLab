"""Presentation-only SSE frames for persisted sysadmin incident state.

This module deliberately reads local incident state only. It does not expose
facts, hypotheses, prompts, model reasoning, credentials or a live adapter.
The gateway integration remains a separately reviewed later change.
"""
from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from sysadmin_incident_store import IncidentStore


def incident_presentation(snapshot: dict[str, Any]) -> dict[str, Any]:
    """Reduce a persisted incident to a safe, concise UI presentation shape."""
    incident = snapshot["incident"]
    evidence = [
        {
            "evidence_id": item["evidence_id"],
            "target": item["target"],
            "kind": item["kind"],
            "state": item["state"],
            "observed_at": item["observed_at"],
            "age_seconds": item["age_seconds"],
            "source": item["source"],
            "summary": item["summary"],
            "truncated": item["truncated"],
        }
        for item in incident["observations"]
    ]
    return {
        "schema_version": 1,
        "incident_id": incident["incident_id"],
        "title": incident["title"],
        "observation_count": incident["observation_count"],
        "evidence": evidence,
        "next": incident["next"],
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
