"""Deterministic safety and capability guard for an NLU proposal.

The guard consumes request text and a schema-valid, non-authorizing proposal.
It can only make the result safer or normalize capabilities; it executes
nothing and never grants authority.
"""
from __future__ import annotations

import copy
import re

import nlu_local_model_adapter as contract


CANONICAL = contract.CAPABILITIES


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z]+", text.lower()))


def _ordered(values: set[str]) -> list[str]:
    return [item for item in CANONICAL if item in values]


def apply(request_text: str, proposal: dict) -> dict:
    if not isinstance(request_text, str) or not request_text.strip():
        raise ValueError("request text must be nonempty")
    value = copy.deepcopy(proposal)
    contract._validate_semantics(value)
    words = _tokens(request_text)
    lower = request_text.lower()

    personal = {
        "private", "personal", "journal", "medication", "appointment",
        "calendar", "inbox", "messages", "sleep", "bedtime", "unread",
        "account", "health", "medical", "email", "mail", "location",
    }
    internal = {
        "homelab", "proxmox", "server", "service", "configuration", "log",
        "database", "backup", "snapshot", "rollback", "training", "sample",
        "demo", "device", "lamp", "fan", "door", "speaker", "timer",
    }
    # First-person ownership is conservatively personal. Overclassification is
    # recoverable; underclassification could expose user-specific context.
    possessive_private = bool(words & {"my", "mine"})
    if words & personal or possessive_private:
        value["sensitivity"] = "personal"
    elif value["sensitivity"] == "public" and words & internal:
        value["sensitivity"] = "internal"

    impossible = {
        "imaginary", "impossible", "unspoken", "thoughts", "telepathy",
        "guarantee", "predict", "foretell", "never-recorded", "unverifiable",
    }
    if words & impossible or "never recorded" in lower:
        value.update(
            request_family="unsupported", capability_needs=[], ambiguity="clear",
            disposition="abstain", reason="unsupported",
        )
        return value

    safety = {"safety", "alarm", "interlock", "guard", "failsafe"}
    disable = {"disable", "bypass", "defeat", "remove", "override"}
    if words & safety and words & disable:
        value.update(
            request_family="household-command", capability_needs=["home.control"],
            ambiguity="clear", disposition="deny", reason="policy-denied",
        )
        return value

    publication = {"publish", "upload", "post", "send"}
    public_destination = {"public", "forum", "website", "board", "page"}
    if words & personal and words & publication and words & public_destination:
        value.update(
            request_family="external-research", capability_needs=["web.publish"],
            sensitivity="personal", ambiguity="clear", disposition="deny",
            reason="policy-denied",
        )
        return value

    # Short external lookups frequently omit the subject or referent. They are
    # never eligible to route until the missing object is supplied.
    if value["request_family"] == "external-research" and len(words) <= 7:
        value.update(
            ambiguity="ambiguous", disposition="clarify", reason="ambiguous",
        )

    family = value["request_family"]
    caps: set[str] = set()
    if family == "general-answer":
        caps.add("facts.answer")
    elif family == "household-command":
        caps.add("home.control")
        explicit_timer = bool(words & {"timer", "countdown"}) and bool(
            words & {"start", "stop", "set", "cancel", "create"}
        )
        if explicit_timer:
            caps.add("timer.control")
    elif family == "read-only-investigation":
        caps.add("lab.read")
    elif family == "change-request":
        caps.add("lab.change")
        if words & {"timer", "schedule", "scheduled", "delay"}:
            caps.add("timer.control")
    elif family == "external-research":
        if words & publication:
            caps.add("web.publish")
        else:
            caps.add("web.read")
    explicit_delete = bool(words & {"delete", "erase", "destroy", "remove"})
    recovery = bool(words & {"backup", "snapshot", "rollback", "recovery", "checkpoint"})
    if explicit_delete and recovery:
        caps.add("backup.delete")
    else:
        caps.discard("backup.delete")
    if words & {"compare", "combine", "join", "crosscheck", "cross-check"}:
        caps.add("local.join")
    if "calendar" in words and family in {"read-only-investigation", "external-research"}:
        caps.add("calendar.read")
    if words & {"supplied", "provided", "included", "pasted", "attached"}:
        caps.discard("lab.read")
        caps.discard("calendar.read")
    value["capability_needs"] = _ordered(caps)
    contract._validate_semantics(value)
    return value
