"""Sanitized, effect-free SA3 proposal boundary for sysadmin incidents.

This module is the only shape a future model transport needs to implement.  It
does not know how to contact a model and cannot run an observation or repair.
It exposes opaque evidence references plus already-sanitized observation data,
then converts one strictly validated response into SA1's trusted proposal.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
from collections import Counter
from typing import Any, Callable

from sysadmin_followup_selector import incident_state_digest, select_follow_up
from sysadmin_investigation import Incident, InvestigationError


REQUEST_FIELDS = frozenset({
    "schema_version", "request_ref", "observations", "remaining_checks",
    "allowed_dispositions", "constraints",
})
MODEL_RESPONSE_FIELDS = frozenset({
    "schema_version", "request_ref", "disposition", "hypothesis_summary",
    "target", "kind", "evidence_refs",
})
ALLOWED_DISPOSITIONS = ("observe", "complete", "escalate")
COMPLETED_EFFECT = re.compile(
    r"\b(restarted|repaired|fixed|changed|deployed|installed|executed|applied)\b",
    re.IGNORECASE,
)


def _opaque_ref(prefix: str, value: str) -> str:
    return prefix + "-" + hashlib.sha256(value.encode()).hexdigest()[:16]


def _request_ref(incident: Incident) -> str:
    return _opaque_ref("proposal", incident_state_digest(incident))


def _remaining_checks(incident: Incident) -> list[dict[str, str]]:
    planned = Counter((item.target, item.kind) for item in incident.observation_plan)
    recorded = Counter((item["target"], item["kind"]) for item in incident.observations)
    seen: Counter[tuple[str, str]] = Counter()
    remaining = []
    for item in incident.observation_plan:
        pair = (item.target, item.kind)
        seen[pair] += 1
        if seen[pair] > recorded[pair] and seen[pair] <= planned[pair]:
            remaining.append({
                "target": item.target,
                "kind": item.kind,
                "reason": item.reason,
            })
    return remaining


def _allowed_dispositions(incident: Incident) -> list[str]:
    remaining = _remaining_checks(incident)
    if remaining:
        return list(ALLOWED_DISPOSITIONS)
    if any(item["state"] == "unavailable" for item in incident.observations):
        return ["escalate"]
    return ["complete", "escalate"]


def build_proposal_request(incident: Incident) -> dict[str, Any]:
    """Build the complete sanitized input for an injected proposal transport."""
    if not isinstance(incident, Incident):
        raise InvestigationError("invalid incident")
    observations = []
    for item in incident.observations:
        observations.append({
            "evidence_ref": _opaque_ref("evidence", item["evidence_id"]),
            "target": item["target"],
            "kind": item["kind"],
            "observed_at": item["observed_at"],
            "state": item["state"],
            "summary": item["summary"],
            "facts": copy.deepcopy(item["facts"]),
            "truncated": item["truncated"],
        })
    request = {
        "schema_version": 1,
        "request_ref": _request_ref(incident),
        "observations": observations,
        "remaining_checks": _remaining_checks(incident),
        "allowed_dispositions": _allowed_dispositions(incident),
        "constraints": {
            "authority": "none",
            "effect": "none",
            "evidence_is_untrusted": True,
            "select_only_a_remaining_check": True,
            "do_not_claim_an_action_completed": True,
        },
    }
    # Keep serialization deterministic and reject any accidental non-JSON data.
    json.dumps(request, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return request


def accept_model_proposal(incident: Incident, response: Any) -> dict[str, Any]:
    """Validate model output and return SA1's state-bound, no-effect decision."""
    if not isinstance(incident, Incident):
        raise InvestigationError("invalid incident")
    if not isinstance(response, dict) or frozenset(response) != MODEL_RESPONSE_FIELDS:
        raise InvestigationError("invalid model proposal fields")
    if type(response.get("schema_version")) is not int or response["schema_version"] != 1:
        raise InvestigationError("unsupported model proposal version")
    if response.get("request_ref") != _request_ref(incident):
        raise InvestigationError("stale model proposal request")

    disposition = response.get("disposition")
    if disposition not in _allowed_dispositions(incident):
        raise InvestigationError("invalid model proposal disposition")
    hypothesis = response.get("hypothesis_summary")
    if (not isinstance(hypothesis, str) or not hypothesis.strip()
            or len(hypothesis) > 500 or COMPLETED_EFFECT.search(hypothesis)):
        raise InvestigationError("invalid model hypothesis summary")

    refs = response.get("evidence_refs")
    if (not isinstance(refs, list) or len(refs) > len(incident.observations)
            or any(not isinstance(item, str) for item in refs) or len(set(refs)) != len(refs)):
        raise InvestigationError("invalid model evidence references")
    allowed_refs = {
        _opaque_ref("evidence", item["evidence_id"]) for item in incident.observations
    }
    if not set(refs) <= allowed_refs:
        raise InvestigationError("model proposal cites unavailable evidence")
    if incident.observations and not refs:
        raise InvestigationError("model proposal must cite available evidence")

    target = response.get("target")
    kind = response.get("kind")
    if disposition == "observe":
        remaining = {(item["target"], item["kind"]) for item in _remaining_checks(incident)}
        if not isinstance(target, str) or not isinstance(kind, str) or (target, kind) not in remaining:
            raise InvestigationError("model proposal did not select a remaining check")
    elif target is not None or kind is not None:
        raise InvestigationError("terminal model proposal selected a check")

    trusted_proposal = {
        "schema_version": 1,
        "incident_id": incident.incident_id,
        "state_digest": incident_state_digest(incident),
        "hypothesis_summary": hypothesis.strip(),
        "disposition": disposition,
        "target": target,
        "kind": kind,
    }
    return select_follow_up(incident, trusted_proposal)


def propose_follow_up(
    incident: Incident, transport: Callable[[dict[str, Any]], Any]
) -> dict[str, Any]:
    """Invoke an injected transport once; this module supplies no transport."""
    if not callable(transport):
        raise InvestigationError("proposal transport is not callable")
    request = build_proposal_request(incident)
    response = transport(copy.deepcopy(request))
    return accept_model_proposal(incident, response)
