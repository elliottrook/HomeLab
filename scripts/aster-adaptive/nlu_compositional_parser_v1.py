"""Offline compositional NLU parser with a separate route-eligibility gate.

The parser uses explicit public lexicons and structural conjunctions. Family
description never grants a route: routing requires exactly one fully supported
family with all of its required slots. Conflicts and incomplete frames clarify.
"""
from __future__ import annotations

import re


TOKEN = re.compile(r"[a-z0-9]+")

HOME_ACTION = {"activate", "close", "deactivate", "dim", "lock", "lower", "open", "raise", "switch", "turn", "unlock"}
HOME_TARGET = {"blind", "blinds", "curtain", "curtains", "door", "fan", "heater", "light", "lights", "lamp", "speaker", "thermostat"}
TIMER_ACTION = {"cancel", "create", "set", "start", "stop"}
TIMER_TARGET = {"alarm", "countdown", "timer"}
READ_ACTION = {"check", "get", "inspect", "list", "read", "show", "status", "verify", "view"}
LAB_TARGET = {"backup", "backups", "cluster", "container", "database", "doctor", "gpu", "health", "homelab", "host", "inference", "log", "logs", "model", "network", "node", "proxmox", "report", "server", "service", "storage", "vm"}
CHANGE_ACTION = {"change", "configure", "deploy", "install", "reload", "replace", "restart", "start", "stop", "update", "upgrade"}
CHANGE_TARGET = {"application", "app", "container", "database", "host", "model", "node", "package", "server", "service", "vm"}
WEB_ACTION = {"find", "lookup", "research", "search"}
WEB_CONTEXT = {"current", "internet", "latest", "online", "public", "today", "web"}
WEB_TARGET = {"documentation", "docs", "forecast", "news", "price", "release", "schedule", "version", "weather"}
PERSONAL = {"calendar", "email", "inbox", "journal", "location", "mail", "medical", "medication", "messages", "my", "private"}


def _label(family, sensitivity, capabilities, ambiguity, disposition, reason):
    return {
        "request_family": family, "sensitivity": sensitivity,
        "capability_needs": capabilities, "ambiguity": ambiguity,
        "disposition": disposition, "reason": reason,
    }


def parse(request_text: str) -> dict:
    if not isinstance(request_text, str) or not request_text.strip():
        raise ValueError("request text must be nonempty")
    lower = " ".join(request_text.lower().split())
    words = set(TOKEN.findall(lower))
    sensitivity = "personal" if words & PERSONAL else "internal" if words & (LAB_TARGET | HOME_TARGET | TIMER_TARGET) else "public"
    if "thoughts" in words and words & {"another", "person", "persons"}:
        sensitivity = "personal"
    elif words & {"groceries", "kitchen"}:
        sensitivity = "internal"

    impossible = (
        bool(words & {"teleport", "telepathy", "thoughts", "foretell"})
        or ({"winning", "lottery"} <= words)
        or ({"exact", "price"} <= words and bool(words & {"future", "year"}))
    )
    if impossible:
        return _label("unsupported", sensitivity, [], "clear", "abstain", "unsupported")

    publish = bool(words & {"broadcast", "post", "publish", "upload"})
    public_destination = bool(words & {"forum", "page", "public", "site", "website"})
    if sensitivity == "personal" and publish and public_destination:
        caps = ["calendar.read", "web.publish"] if "calendar" in words else ["web.publish"]
        return _label("external-research", "personal", caps, "clear", "deny", "policy-denied")
    if words & {"delete", "destroy", "erase"} and words & {"backup", "snapshot", "checkpoint"}:
        return _label("change-request", "internal", ["backup.delete"], "clear", "deny", "policy-denied")

    referential = bool(words & {"it", "that", "this"}) and len(words) <= 6
    timer = bool(words & TIMER_ACTION) and bool(words & TIMER_TARGET)
    home = bool(words & HOME_ACTION) and bool(words & HOME_TARGET)
    calendar = "calendar" in words and bool(words & READ_ACTION | {"compare"})
    web = (bool(words & WEB_ACTION) or "look up" in lower) and bool(words & WEB_CONTEXT | WEB_TARGET)
    lab_read = bool(words & READ_ACTION) and bool(words & LAB_TARGET)
    if lower.startswith("is ") and words & LAB_TARGET and words & {"healthy", "running", "available", "status"}:
        lab_read = True
    change = bool(words & CHANGE_ACTION) and bool(words & CHANGE_TARGET)
    factual = bool(re.match(r"^(?:who|what|when|where|why)\b", lower)) or bool(
        re.match(r"^(?:define|explain|summarize)\b", lower)
    )

    # An advice question that names a state-changing operation describes a
    # possible change but lacks a concrete execution/answer boundary.
    if lower.startswith("how ") and change:
        return _label("change-request", sensitivity, [], "ambiguous", "clarify", "ambiguous")
    if referential:
        family = "change-request" if words & (CHANGE_ACTION | {"fix"}) else "household-command" if words & HOME_ACTION else "general-answer"
        if family in {"change-request", "household-command"}:
            sensitivity = "internal"
        return _label(family, sensitivity, [], "ambiguous", "clarify", "ambiguous")

    frames = [name for name, present in (
        ("timer", timer), ("home", home), ("calendar", calendar),
        ("web", web), ("lab_read", lab_read), ("change", change),
        ("factual", factual),
    ) if present]

    # Calendar+web is the one reviewed compositional multi-source frame.
    if calendar and (web or words & {"online", "public", "event"}):
        return _label("external-research", "personal", ["calendar.read", "web.read", "local.join"], "clear", "route", "understood")
    if len(frames) != 1:
        return _label("general-answer", sensitivity, [], "ambiguous", "clarify", "ambiguous")

    frame = frames[0]
    if frame == "timer":
        return _label("household-command", "internal", ["timer.control"], "clear", "route", "understood")
    if frame == "home":
        return _label("household-command", "internal", ["home.control"], "clear", "route", "understood")
    if frame == "calendar":
        return _label("read-only-investigation", "personal", ["calendar.read"], "clear", "route", "understood")
    if frame == "web":
        return _label("external-research", "public", ["web.read"], "clear", "route", "understood")
    if frame == "lab_read":
        return _label("read-only-investigation", "internal", ["lab.read"], "clear", "route", "understood")
    if frame == "change":
        return _label("change-request", "internal", ["lab.change"], "clear", "route", "understood")
    return _label("general-answer", "public", ["facts.answer"], "clear", "route", "understood")

