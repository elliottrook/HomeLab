"""Effect-free SA1 follow-up selection for a bounded incident.

The caller may obtain a proposal from a model or a human, but this boundary
decides whether that proposal is valid.  It can select only an unfilled pair
from the incident's preregistered read-only plan.  It cannot execute the check,
contact a target, grant authority, or claim an investigation succeeded.
"""
from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from typing import Any

from sysadmin_investigation import Incident, InvestigationError


PROPOSAL_FIELDS = frozenset({
    "schema_version",
    "incident_id",
    "state_digest",
    "hypothesis_summary",
    "disposition",
    "target",
    "kind",
})
DISPOSITIONS = frozenset({"observe", "complete", "escalate"})
SHA256 = re.compile(r"^[0-9a-f]{64}$")


def incident_state_digest(incident: Incident) -> str:
    """Bind a proposal to the exact validated incident state it considered."""
    encoded = json.dumps(
        incident.to_record(),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode()
    return hashlib.sha256(encoded).hexdigest()


def _remaining_pairs(incident: Incident) -> Counter[tuple[str, str]]:
    planned = Counter((item.target, item.kind) for item in incident.observation_plan)
    recorded = Counter((item["target"], item["kind"]) for item in incident.observations)
    return planned - recorded


def select_follow_up(incident: Incident, proposal: Any) -> dict[str, Any]:
    """Validate one state-bound proposal and return an effect-free decision."""
    if not isinstance(incident, Incident):
        raise InvestigationError("invalid incident")
    if not isinstance(proposal, dict) or frozenset(proposal) != PROPOSAL_FIELDS:
        raise InvestigationError("invalid follow-up proposal fields")
    if type(proposal.get("schema_version")) is not int or proposal["schema_version"] != 1:
        raise InvestigationError("unsupported follow-up proposal version")
    if proposal.get("incident_id") != incident.incident_id:
        raise InvestigationError("follow-up proposal belongs to another incident")
    digest = proposal.get("state_digest")
    if not isinstance(digest, str) or not SHA256.fullmatch(digest):
        raise InvestigationError("invalid incident state digest")
    if digest != incident_state_digest(incident):
        raise InvestigationError("stale incident state digest")
    hypothesis = proposal.get("hypothesis_summary")
    if not isinstance(hypothesis, str) or not hypothesis.strip() or len(hypothesis) > 500:
        raise InvestigationError("invalid hypothesis summary")
    disposition = proposal.get("disposition")
    if not isinstance(disposition, str) or disposition not in DISPOSITIONS:
        raise InvestigationError("invalid follow-up disposition")

    request = None
    target = proposal.get("target")
    kind = proposal.get("kind")
    if disposition == "observe":
        if not isinstance(target, str) or not isinstance(kind, str):
            raise InvestigationError("observation selection requires target and kind")
        remaining = _remaining_pairs(incident)
        if remaining[(target, kind)] < 1:
            raise InvestigationError("observation is not an unfilled planned step")
        selected = next(
            item for item in incident.observation_plan
            if item.target == target and item.kind == kind
        )
        request = {
            "target": selected.target,
            "kind": selected.kind,
            "reason": selected.reason,
            "execution": "not performed",
        }
    elif target is not None or kind is not None:
        raise InvestigationError("terminal follow-up cannot select an observation")

    return {
        "schema_version": 1,
        "incident_ref": hashlib.sha256(incident.incident_id.encode()).hexdigest()[:16],
        "bound_state_digest": digest,
        "disposition": disposition,
        "hypothesis_summary": hypothesis.strip(),
        "request": request,
        "authority": "none",
        "effect": "none",
    }
