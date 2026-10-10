"""Offline candidate boundary for deterministic household work and grounded analysis.

This module has no network, service, credential, or production side effects.  A caller must
provide an explicit adapter before a validated household plan can be executed.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Protocol


@dataclass(frozen=True)
class HouseholdState:
    timers: tuple[str, ...] = ()
    rooms: tuple[str, ...] = ()
    entities: tuple[str, ...] = ()
    media_available: bool = False


@dataclass(frozen=True)
class HouseholdDecision:
    status: str
    capability: str | None = None
    arguments: dict = field(default_factory=dict)
    reason: str = ""


class HouseholdAdapter(Protocol):
    def apply(self, capability: str, arguments: dict) -> dict: ...


class RecordingAdapter:
    """Disposable adapter used by tests; it records rather than performs effects."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, dict]] = []

    def apply(self, capability: str, arguments: dict) -> dict:
        self.calls.append((capability, dict(arguments)))
        return {"accepted": True, "capability": capability, "arguments": dict(arguments)}


def plan_household(text: str, state: HouseholdState) -> HouseholdDecision:
    lowered = text.casefold().strip()
    durations = [float(value) for value in re.findall(r"(\d+(?:\.\d+)?)\s*(?:minute|min)", lowered)]
    if "timer" in lowered:
        if "cancel" in lowered:
            matches = [label for label in state.timers if label.casefold() in lowered]
            if len(matches) != 1:
                return HouseholdDecision("clarify", reason="timer target is not unique")
            return HouseholdDecision("plan", "timer.cancel", {"label": matches[0]}, "exact timer")
        if len(set(durations)) != 1:
            return HouseholdDecision("clarify", reason="exactly one duration is required")
        label = next((word for word in ("egg", "pasta", "cake") if word in lowered), "timer")
        return HouseholdDecision("plan", "timer.create", {"seconds": int(durations[0] * 60), "label": label}, "explicit duration")
    if "alarm" in lowered:
        if re.search(r"\b(?:am|pm|morning|afternoon|evening)\b", lowered) is None:
            return HouseholdDecision("clarify", reason="alarm meridiem is required")
        return HouseholdDecision("unsupported", reason="alarm adapter is not implemented")
    if lowered.startswith("play "):
        if not state.media_available:
            return HouseholdDecision("unavailable", reason="media provider is unavailable")
        rooms = [room for room in state.rooms if room.casefold() in lowered]
        if len(rooms) != 1:
            return HouseholdDecision("clarify", reason="one playback target is required")
        query = lowered.removeprefix("play ").split(" in ", 1)[0].strip()
        return HouseholdDecision("plan", "media.play", {"query": query, "target": rooms[0]}, "exact media target")
    if "turn " in lowered:
        entities = [entity for entity in state.entities if entity.casefold() in lowered]
        desired = "off" if "off" in lowered else "on" if "on" in lowered else None
        if len(entities) != 1 or desired is None:
            return HouseholdDecision("clarify", reason="exact device and state are required")
        return HouseholdDecision("plan", "home.control", {"target": entities[0], "state": desired}, "exact device and state")
    return HouseholdDecision("unsupported", reason="no deterministic household intent")


def execute_household(decision: HouseholdDecision, adapter: HouseholdAdapter) -> dict:
    if decision.status != "plan" or not decision.capability:
        raise ValueError("only a deterministic plan may reach an execution adapter")
    return adapter.apply(decision.capability, decision.arguments)


@dataclass(frozen=True)
class Evidence:
    evidence_id: str
    text: str
    sensitivity: str


@dataclass(frozen=True)
class Claim:
    statement: str
    evidence_ids: tuple[str, ...]
    quote: str


@dataclass(frozen=True)
class AnalysisDraft:
    summary: str
    claims: tuple[Claim, ...]
    uncertainties: tuple[str, ...] = ()


@dataclass(frozen=True)
class AnalysisContext:
    deep_sysadmin: bool = False
    has_conflict: bool = False
    missing_material_evidence: bool = False
    retrieved_instruction: bool = False
    requests_credentials: bool = False
    cross_family: bool = False
    consent: bool = False


@dataclass(frozen=True)
class PolicyDecision:
    outcome: str
    route: str
    sensitivity: str
    reason: str
    cloud_packet: dict | None = None
    grounded_facts: tuple[str, ...] = ()


_SENSITIVITY = {"public": 0, "internal": 1, "private": 2}
_SECRET = re.compile(r"(?i)(password|passwd|api[_ -]?key|token|secret|bearer|credential)\s*[:=]")


def validate_grounding(draft: AnalysisDraft, evidence: tuple[Evidence, ...]) -> list[str]:
    failures: list[str] = []
    indexed = {item.evidence_id: item for item in evidence}
    if not draft.claims:
        failures.append("at least one grounded claim is required")
    for position, claim in enumerate(draft.claims):
        sources = [indexed[item] for item in claim.evidence_ids if item in indexed]
        missing = sorted(set(claim.evidence_ids) - set(indexed))
        if missing:
            failures.append(f"claim {position}: unknown evidence ids {missing!r}")
        if not sources:
            failures.append(f"claim {position}: no evidence source")
            continue
        combined = "\n".join(item.text for item in sources)
        if not claim.quote.strip() or claim.quote.casefold() not in combined.casefold():
            failures.append(f"claim {position}: quote is not present in cited evidence")
    return failures


def decide_analysis(context: AnalysisContext, draft: AnalysisDraft, evidence: tuple[Evidence, ...]) -> PolicyDecision:
    sensitivity = max((item.sensitivity for item in evidence), key=lambda value: _SENSITIVITY[value], default="public")
    if context.requests_credentials or context.retrieved_instruction:
        return PolicyDecision("refuse", "none", sensitivity, "untrusted instruction or credential request")
    if context.cross_family and not context.consent:
        return PolicyDecision("refuse", "none", sensitivity, "cross-family consent is absent")
    failures = validate_grounding(draft, evidence)
    if failures:
        return PolicyDecision("blocked", "none", sensitivity, "; ".join(failures))
    if context.has_conflict or context.missing_material_evidence:
        return PolicyDecision("clarify", "local", sensitivity, "material evidence is conflicting or missing")
    if context.deep_sysadmin:
        if sensitivity == "private":
            return PolicyDecision("blocked", "none", sensitivity, "private evidence cannot enter the cloud packet")
        packet = {
            "facts": [{"quote": claim.quote, "evidence_ids": list(claim.evidence_ids)} for claim in draft.claims],
            "uncertainties": list(draft.uncertainties),
        }
        encoded = repr(packet)
        if _SECRET.search(encoded):
            return PolicyDecision("blocked", "none", sensitivity, "secret-like material detected")
        return PolicyDecision("escalate", "cloud_sysadmin", sensitivity, "validated sanitized evidence packet", packet, tuple(claim.quote for claim in draft.claims))
    return PolicyDecision("answer", "local", sensitivity, "grounded local analysis", None, tuple(claim.quote for claim in draft.claims))
