"""Explicit high-precision NLU recognizers with a fail-closed fallback.

This candidate is offline and deterministic. It describes a request but never
selects a provider, grants a capability, or executes an action. Unmatched or
referential requests clarify instead of being forced into a routed family.
"""
from __future__ import annotations

import re


def _words(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def _label(family, sensitivity, capabilities, ambiguity, disposition, reason):
    return {
        "request_family": family,
        "sensitivity": sensitivity,
        "capability_needs": capabilities,
        "ambiguity": ambiguity,
        "disposition": disposition,
        "reason": reason,
    }


def recognize(request_text: str) -> dict:
    if not isinstance(request_text, str) or not request_text.strip():
        raise ValueError("request text must be nonempty")
    lower = " ".join(request_text.lower().split())
    words = _words(lower)

    personal = bool(words & {
        "my", "mine", "private", "personal", "calendar", "inbox", "email",
        "medical", "medication", "journal", "messages", "location",
    })

    impossible = (
        bool(words & {"teleport", "telepathy", "thoughts", "foretell"})
        or ("winning" in words and "lottery" in words)
        or ("exact" in words and "price" in words and words & {"future", "year"})
    )
    if impossible:
        impossible_sensitivity = (
            "personal" if personal or "thoughts" in words
            else "internal" if words & {"home", "kitchen", "groceries", "device"}
            else "public"
        )
        return _label(
            "unsupported", impossible_sensitivity,
            [], "clear", "abstain", "unsupported",
        )

    public_destination = bool(words & {"public", "website", "site", "forum", "page"})
    publish = bool(words & {"publish", "post", "upload", "broadcast"})
    if personal and public_destination and publish:
        capabilities = ["calendar.read", "web.publish"] if "calendar" in words else ["web.publish"]
        return _label(
            "external-research", "personal", capabilities,
            "clear", "deny", "policy-denied",
        )

    destructive = bool(words & {"delete", "destroy", "erase"})
    recovery_asset = bool(words & {"backup", "snapshot", "checkpoint"})
    if destructive and recovery_asset:
        return _label(
            "change-request", "internal", ["backup.delete"],
            "clear", "deny", "policy-denied",
        )

    if lower in {"turn it off", "turn it on"}:
        return _label(
            "household-command", "internal", [],
            "ambiguous", "clarify", "ambiguous",
        )
    if lower in {"fix it", "change it", "update it"}:
        return _label(
            "change-request", "internal", [],
            "ambiguous", "clarify", "ambiguous",
        )
    if re.fullmatch(r"(?:tell|show|explain) me (?:about )?(?:it|that|this)", lower):
        return _label(
            "general-answer", "public", [],
            "ambiguous", "clarify", "ambiguous",
        )

    timer_action = bool(words & {"set", "start", "stop", "cancel"})
    if timer_action and bool(words & {"timer", "countdown"}):
        return _label(
            "household-command", "internal", ["timer.control"],
            "clear", "route", "understood",
        )

    home_action = bool(words & {"turn", "switch", "lower", "raise", "open", "close"})
    home_target = bool(words & {"light", "lights", "lamp", "blind", "blinds", "fan", "door"})
    if home_action and home_target:
        return _label(
            "household-command", "internal", ["home.control"],
            "clear", "route", "understood",
        )

    calendar_read = "calendar" in words and bool(words & {"inspect", "show", "read", "check", "compare"})
    web_lookup = bool(words & {"find", "search", "lookup"}) or "look up" in lower
    if calendar_read and (web_lookup or bool(words & {"public", "online", "event", "compare"})):
        return _label(
            "external-research", "personal", ["calendar.read", "web.read", "local.join"],
            "clear", "route", "understood",
        )
    if calendar_read:
        return _label(
            "read-only-investigation", "personal", ["calendar.read"],
            "clear", "route", "understood",
        )

    lab_read_verb = bool(words & {"read", "show", "inspect", "check"}) or lower.startswith("is ")
    lab_subject = bool(words & {
        "homelab", "proxmox", "server", "service", "doctor", "backup",
        "health", "status", "report", "logs", "inference",
    })
    if lab_read_verb and lab_subject:
        return _label(
            "read-only-investigation", "internal", ["lab.read"],
            "clear", "route", "understood",
        )

    change_verb = bool(words & {"restart", "reload", "update", "upgrade", "install", "replace"})
    change_target = bool(words & {"service", "package", "container", "server", "application", "app"})
    if lower.startswith("how ") and change_verb and change_target:
        return _label(
            "change-request", "internal", [],
            "ambiguous", "clarify", "ambiguous",
        )
    if change_verb and change_target:
        return _label(
            "change-request", "internal", ["lab.change"],
            "clear", "route", "understood",
        )

    if web_lookup and bool(words & {
        "online", "public", "weather", "forecast", "release", "version", "latest", "current",
    }):
        return _label(
            "external-research", "public", ["web.read"],
            "clear", "route", "understood",
        )

    question_start = bool(re.match(r"^(?:who|what|when|where|why)\b", lower))
    explain = lower.startswith("explain ")
    if (question_start or explain) and not personal and not (change_verb and lab_subject):
        return _label(
            "general-answer", "public", ["facts.answer"],
            "clear", "route", "understood",
        )

    return _label(
        "general-answer", "personal" if personal else "public", [],
        "ambiguous", "clarify", "ambiguous",
    )

