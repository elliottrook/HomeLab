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
WEATHER = "weather.forecast_home"
ENTITY_IDS = frozenset({LIGHT, HALL, OUTSIDE, CLOSET, WEATHER})
ALIASES = {LIGHT: "laundry lights", HALL: "hall temperature",
           OUTSIDE: "outside temperature", CLOSET: "closet temperature",
           WEATHER: "home weather"}
WEATHER_CONDITIONS = frozenset({
    "clear-night", "cloudy", "exceptional", "fog", "hail", "lightning",
    "lightning-rainy", "partlycloudy", "pouring", "rainy", "snowy",
    "snowy-rainy", "sunny", "windy", "windy-variant",
})


def build_snapshot(states: dict[str, str], units: dict[str, str],
                   attributes: dict[str, dict] | None = None) -> dict:
    attributes = attributes or {}
    if (set(states) - ENTITY_IDS or set(units) - {HALL, OUTSIDE, CLOSET}
            or set(attributes) - {WEATHER}):
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
    weather = []
    condition = states.get(WEATHER)
    details = attributes.get(WEATHER, {})
    if condition in WEATHER_CONDITIONS and isinstance(details, dict):
        unit = details.get("temperature_unit")
        try:
            temperature = float(details["temperature"])
        except (KeyError, TypeError, ValueError):
            temperature = math.nan
        minimum, maximum = ((-50, 60) if unit == "°C" else
                            (-58, 140) if unit == "°F" else (1, 0))
        if math.isfinite(temperature) and minimum <= temperature <= maximum:
            item = {"alias": ALIASES[WEATHER], "condition": condition,
                    "temperature": round(temperature, 1), "unit": unit}
            humidity = details.get("humidity")
            if (not isinstance(humidity, bool)
                    and isinstance(humidity, (int, float))
                    and math.isfinite(humidity) and 0 <= humidity <= 100):
                item["humidity"] = round(float(humidity), 1)
            weather.append(item)
    return {"schema_version": 3, "snapshot_id": "ha-home-pilot-v3",
            "lights": lights, "temperatures": temperatures,
            "weather": weather, "rooms": [], "entities": [], "timers": [],
            "media_providers": []}


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
