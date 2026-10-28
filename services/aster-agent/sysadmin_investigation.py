"""Typed, read-only incident evidence for Aster's sysadmin capability.

This is deliberately an offline policy component.  It validates observations
produced by a future registered adapter, records a bounded incident timeline,
and returns the next *proposed* observation.  It has no network, filesystem
discovery, subprocess, credential, or job-execution capability.
"""
from __future__ import annotations

import copy
import json
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


MAX_FACT_BYTES = 12_000
MAX_OBSERVATIONS = 4
MAX_HYPOTHESES = 3
EVIDENCE_KINDS = frozenset({"git", "log", "status", "network", "backup", "config"})
EVIDENCE_STATES = frozenset({"ok", "warn", "fail", "unavailable"})

# The catalogue is policy, not an inventory discovery mechanism.  An adapter
# may only produce the listed kind for the listed target; every other request
# fails closed before it can reach a producer.
REGISTERED_OBSERVATIONS: dict[str, frozenset[str]] = {
    "aster-gateway": frozenset({"status", "log", "config"}),
    "inference-server": frozenset({"status", "log", "config"}),
    "forgejo-main": frozenset({"git"}),
    "netbox-main": frozenset({"network"}),
    "homelab-doctor": frozenset({"status", "network"}),
    "backup-catalog": frozenset({"backup"}),
}


class InvestigationError(ValueError):
    """A policy/shape violation which must not become a live action."""


def _parse_utc(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (AttributeError, TypeError, ValueError) as exc:
        raise InvestigationError("observed_at must be an ISO-8601 UTC timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise InvestigationError("observed_at must be UTC")
    return parsed.astimezone(timezone.utc)


def _safe_facts(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise InvestigationError("facts must be an object")
    try:
        encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise InvestigationError("facts must be finite JSON data") from exc
    if len(encoded.encode()) > MAX_FACT_BYTES:
        raise InvestigationError("facts exceed the evidence size limit")
    blocked = {"secret", "password", "token", "credential", "authorization", "cookie"}
    def check_keys(item: Any) -> None:
        if isinstance(item, dict):
            for key, nested in item.items():
                if not isinstance(key, str) or any(word in key.lower() for word in blocked):
                    raise InvestigationError("facts contain a prohibited field")
                check_keys(nested)
        elif isinstance(item, list):
            for nested in item:
                check_keys(nested)
    check_keys(value)
    return copy.deepcopy(value)


@dataclass(frozen=True)
class Observation:
    """Sanitized output of exactly one registered, read-only observation."""

    evidence_id: str
    incident_id: str
    target: str
    kind: str
    observed_at: str
    source: str
    state: str
    summary: str
    facts: dict[str, Any]
    truncated: bool = False

    def validate(self, now: datetime) -> dict[str, Any]:
        if not isinstance(now, datetime) or now.tzinfo is None or now.utcoffset() is None:
            raise InvestigationError("observation requires an aware clock")
        if not isinstance(self.evidence_id, str) or not self.evidence_id or len(self.evidence_id) > 80:
            raise InvestigationError("invalid evidence_id")
        if not isinstance(self.incident_id, str) or not self.incident_id or len(self.incident_id) > 80:
            raise InvestigationError("invalid incident_id")
        if (not isinstance(self.target, str) or not isinstance(self.kind, str) or
                self.target not in REGISTERED_OBSERVATIONS or self.kind not in REGISTERED_OBSERVATIONS[self.target]):
            raise InvestigationError("observation target or kind is not registered")
        if not isinstance(self.state, str) or self.state not in EVIDENCE_STATES:
            raise InvestigationError("invalid evidence state")
        if not isinstance(self.source, str) or not self.source or len(self.source) > 160:
            raise InvestigationError("invalid evidence source")
        if not isinstance(self.summary, str) or not self.summary or len(self.summary) > 800:
            raise InvestigationError("invalid evidence summary")
        if type(self.truncated) is not bool:
            raise InvestigationError("truncated must be boolean")
        observed = _parse_utc(self.observed_at)
        age_seconds = int((now - observed).total_seconds())
        if age_seconds < 0:
            raise InvestigationError("observation is in the future")
        return {
            "evidence_id": self.evidence_id,
            "incident_id": self.incident_id,
            "target": self.target,
            "kind": self.kind,
            "observed_at": observed.isoformat().replace("+00:00", "Z"),
            "source": self.source,
            "state": self.state,
            "summary": self.summary,
            "facts": _safe_facts(self.facts),
            "truncated": self.truncated,
            "age_seconds": age_seconds,
        }


@dataclass(frozen=True)
class EvidenceRequest:
    target: str
    kind: str
    reason: str

    def validate(self) -> None:
        if (not isinstance(self.target, str) or not isinstance(self.kind, str) or
                self.target not in REGISTERED_OBSERVATIONS or self.kind not in REGISTERED_OBSERVATIONS[self.target]):
            raise InvestigationError("requested observation is not registered")
        if not isinstance(self.reason, str) or not self.reason or len(self.reason) > 400:
            raise InvestigationError("invalid observation reason")


@dataclass
class Incident:
    incident_id: str
    title: str
    observation_plan: list[EvidenceRequest]
    observations: list[dict[str, Any]] = field(default_factory=list)
    hypotheses: list[str] = field(default_factory=list)
    cursor: int = 0

    def add_hypothesis(self, text: str) -> None:
        if not isinstance(text, str) or not text.strip() or len(text) > 500:
            raise InvestigationError("invalid hypothesis")
        if len(self.hypotheses) >= MAX_HYPOTHESES:
            raise InvestigationError("hypothesis limit reached")
        self.hypotheses.append(text.strip())

    def add_observation(self, observation: Observation, now: datetime) -> dict[str, Any]:
        if observation.incident_id != self.incident_id:
            raise InvestigationError("evidence belongs to another incident")
        if len(self.observations) >= MAX_OBSERVATIONS:
            raise InvestigationError("observation limit reached")
        record = observation.validate(now)
        if any(item["evidence_id"] == record["evidence_id"] for item in self.observations):
            raise InvestigationError("duplicate evidence_id")
        pair = (record["target"], record["kind"])
        planned = Counter((item.target, item.kind) for item in self.observation_plan)
        recorded = Counter((item["target"], item["kind"]) for item in self.observations)
        if recorded[pair] >= planned[pair]:
            raise InvestigationError("observation is not an unfilled planned step")
        self.observations.append(record)
        # Evidence can arrive out of order. Advance only over plan steps for
        # which a corresponding observation has already been recorded.
        recorded[pair] += 1
        seen: Counter[tuple[str, str]] = Counter()
        self.cursor = 0
        for request in self.observation_plan:
            step = (request.target, request.kind)
            seen[step] += 1
            if recorded[step] < seen[step]:
                break
            self.cursor += 1
        return copy.deepcopy(record)

    def next_observation(self) -> dict[str, Any]:
        if len(self.observations) >= MAX_OBSERVATIONS:
            return {"state": "bounded", "reason": "observation limit reached"}
        if self.cursor >= len(self.observation_plan):
            return {"state": "sufficient_or_escalate", "reason": "planned evidence exhausted"}
        proposed = self.observation_plan[self.cursor]
        return {
            "state": "proposed_read_only",
            "target": proposed.target,
            "kind": proposed.kind,
            "reason": proposed.reason,
            "execution": "not performed by the investigation loop",
        }

    def public_state(self) -> dict[str, Any]:
        return {
            "incident_id": self.incident_id,
            "title": self.title,
            "observation_count": len(self.observations),
            "hypotheses": list(self.hypotheses),
            "observations": copy.deepcopy(self.observations),
            "next": self.next_observation(),
        }

    def to_record(self) -> dict[str, Any]:
        """Stable, local-only persistence shape; no model transcript is stored."""
        return {
            "schema_version": 1,
            "incident_id": self.incident_id,
            "title": self.title,
            "observation_plan": [request.__dict__.copy() for request in self.observation_plan],
            "observations": copy.deepcopy(self.observations),
            "hypotheses": list(self.hypotheses),
            "cursor": self.cursor,
        }

    @classmethod
    def from_record(cls, record: dict[str, Any], now: datetime) -> "Incident":
        expected = {"schema_version", "incident_id", "title", "observation_plan", "observations", "hypotheses", "cursor"}
        if (not isinstance(record, dict) or set(record) != expected or
                type(record.get("schema_version")) is not int or record["schema_version"] != 1):
            raise InvestigationError("invalid persisted incident record")
        plan_items = record.get("observation_plan")
        if (not isinstance(plan_items, list) or
                any(not isinstance(item, dict) or set(item) != {"target", "kind", "reason"}
                    for item in plan_items)):
            raise InvestigationError("invalid persisted observation plan")
        plan = [EvidenceRequest(**item) for item in plan_items]
        incident = create_incident(record["incident_id"], record["title"], plan)
        if not isinstance(record["observations"], list) or not isinstance(record["hypotheses"], list):
            raise InvestigationError("invalid persisted incident contents")
        for hypothesis in record["hypotheses"]:
            incident.add_hypothesis(hypothesis)
        # Stored records have already been validated, but reapply the full
        # evidence contract when restoring so an altered SQLite row fails closed.
        required_observation = {"evidence_id", "incident_id", "target", "kind",
                                "observed_at", "source", "state", "summary", "facts"}
        for item in record["observations"]:
            if (not isinstance(item, dict) or not required_observation <= set(item)
                    or not set(item) <= required_observation | {"truncated", "age_seconds"}):
                raise InvestigationError("invalid persisted observation")
            copy_item = dict(item)
            copy_item.pop("age_seconds", None)
            incident.add_observation(Observation(**copy_item), now)
        if type(record["cursor"]) is not int or record["cursor"] != incident.cursor:
            raise InvestigationError("invalid persisted incident cursor")
        return incident


def create_incident(incident_id: str, title: str, observation_plan: list[EvidenceRequest]) -> Incident:
    if (not isinstance(incident_id, str) or not incident_id or len(incident_id) > 80 or
            not isinstance(title, str) or not title or len(title) > 300):
        raise InvestigationError("invalid incident identity")
    if not isinstance(observation_plan, list) or not observation_plan or len(observation_plan) > MAX_OBSERVATIONS:
        raise InvestigationError("incident must have one to four planned observations")
    for request in observation_plan:
        if not isinstance(request, EvidenceRequest):
            raise InvestigationError("invalid observation plan entry")
        request.validate()
    return Incident(incident_id=incident_id, title=title, observation_plan=list(observation_plan))
