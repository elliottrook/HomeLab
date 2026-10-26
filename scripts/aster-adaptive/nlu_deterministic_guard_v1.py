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
    }
    internal = {
        "homelab", "proxmox", "server", "service", "configuration", "log",
        "database", "backup", "snapshot", "rollback", "training", "sample",
        "demo", "device", "lamp", "fan", "door", "speaker", "timer",
    }
    if words & personal:
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

    caps: set[str] = set(value["capability_needs"])
    if value["request_family"] == "general-answer":
        caps = {"facts.answer"}
    if value["request_family"] == "household-command":
        caps.add("home.control")
        explicit_timer = "timer" in words and bool(words & {"start", "stop", "set", "cancel"})
        if explicit_timer:
            caps.add("timer.control")
        else:
            caps.discard("timer.control")
    if value["request_family"] == "external-research":
        if words & {"search", "research", "online", "website", "official", "web"}:
            caps.add("web.read")
        if not words & publication:
            caps.discard("web.publish")
    explicit_delete = bool(words & {"delete", "erase", "destroy", "remove"})
    recovery = bool(words & {"backup", "snapshot", "rollback", "recovery", "checkpoint"})
    if explicit_delete and recovery:
        caps.add("backup.delete")
    else:
        caps.discard("backup.delete")
    if words & {"compare", "combine", "join"}:
        caps.add("local.join")
    if words & {"supplied", "provided", "included", "pasted"}:
        caps.discard("lab.read")
        caps.discard("calendar.read")
    value["capability_needs"] = _ordered(caps)
    contract._validate_semantics(value)
    return value
