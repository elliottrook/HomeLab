"""Synthetic, side-effect-free reference contract for deterministic household intents."""

from __future__ import annotations

import re


def decide(text: str, state: dict) -> dict:
    lowered = text.casefold().strip()
    minute_values = [float(value) for value in re.findall(r"(\d+(?:\.\d+)?)\s*(?:minute|min)", lowered)]
    if "timer" in lowered:
        if len(set(minute_values)) > 1:
            return {"status": "clarify", "reason": "conflicting durations", "effect": None}
        if "cancel" in lowered:
            labels = [name for name in state.get("timers", []) if name.casefold() in lowered]
            if len(labels) != 1:
                return {"status": "clarify", "reason": "timer target is not unique", "effect": None}
            return {"status": "plan", "reason": "exact timer", "effect": {"capability": "timer.cancel", "label": labels[0]}}
        if len(minute_values) != 1:
            return {"status": "clarify", "reason": "one duration required", "effect": None}
        label = next((word for word in ("egg", "pasta", "cake") if word in lowered), "timer")
        return {"status": "plan", "reason": "explicit duration", "effect": {"capability": "timer.create", "seconds": int(minute_values[0] * 60), "label": label}}
    if "alarm" in lowered:
        if re.search(r"\b(?:am|pm|morning|afternoon|evening)\b", lowered) is None:
            return {"status": "clarify", "reason": "alarm meridiem required", "effect": None}
        return {"status": "plan", "reason": "explicit alarm time", "effect": {"capability": "alarm.create"}}
    if lowered.startswith("play "):
        if not state.get("media_available", False):
            return {"status": "unavailable", "reason": "media provider unavailable", "effect": None}
        rooms = [room for room in state.get("rooms", []) if room.casefold() in lowered]
        if len(rooms) != 1:
            return {"status": "clarify", "reason": "one playback target required", "effect": None}
        query = lowered.removeprefix("play ").split(" in ", 1)[0].strip()
        return {"status": "plan", "reason": "explicit media target", "effect": {"capability": "media.play", "query": query, "target": rooms[0]}}
    if "turn " in lowered:
        matches = [entity for entity in state.get("entities", []) if entity.casefold() in lowered]
        if len(matches) != 1:
            return {"status": "clarify", "reason": "device target is not unique", "effect": None}
        desired = "off" if "off" in lowered else "on" if "on" in lowered else None
        if desired is None:
            return {"status": "clarify", "reason": "device state required", "effect": None}
        return {"status": "plan", "reason": "exact device and state", "effect": {"capability": "home.control", "target": matches[0], "state": desired}}
    return {"status": "unsupported", "reason": "no deterministic household intent", "effect": None}
