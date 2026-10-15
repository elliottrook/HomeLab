"""Fixed-scope, credential-free Aster Home display snapshot."""

from __future__ import annotations

import json
import math
import os
import tempfile
from pathlib import Path


OUTPUT = Path("/share/aster-home-registry/latest.json")
LIGHT = "light.laundry_laundry_main_lights"
HALL = "sensor.hall_hall_sensor_temperature"
OUTSIDE = "sensor.outside_outdoor_sensor_temperature"
CLOSET = "sensor.jasons_room_jasons_closet_temperature"
ENTITY_IDS = frozenset({LIGHT, HALL, OUTSIDE, CLOSET})
ALIASES = {LIGHT: "laundry lights", HALL: "hall temperature",
           OUTSIDE: "outside temperature", CLOSET: "closet temperature"}


def build_snapshot(states: dict[str, str], units: dict[str, str]) -> dict:
    if set(states) - ENTITY_IDS or set(units) - {HALL, OUTSIDE, CLOSET}:
        raise ValueError("unreviewed entity supplied")
    lights = []
    if states.get(LIGHT) in {"on", "off"}:
        lights.append({"alias": ALIASES[LIGHT], "state": states[LIGHT]})
    temperatures = []
    for entity_id in (HALL, OUTSIDE, CLOSET):
        unit = units.get(entity_id)
        if unit not in {"°C", "°F"}:
            continue
        try:
            value = float(states[entity_id])
        except (KeyError, TypeError, ValueError):
            continue
        minimum, maximum = (-50, 60) if unit == "°C" else (-58, 140)
        if math.isfinite(value) and minimum <= value <= maximum:
            temperatures.append({"alias": ALIASES[entity_id],
                                 "value": round(value, 1), "unit": unit})
    return {"schema_version": 2, "snapshot_id": "ha-home-pilot-v2",
            "lights": lights, "temperatures": temperatures,
            "rooms": [], "entities": [], "timers": [], "media_providers": []}


def write_atomic(report: dict) -> None:
    OUTPUT.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=".latest.", dir=OUTPUT.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(report, handle, sort_keys=True, separators=(",", ":"))
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, 0o600)
        os.replace(temporary, OUTPUT)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
