"""Pure export contract vendored with the Home Assistant integration."""

from __future__ import annotations

import re
import json
import os
import tempfile
import math
from collections.abc import Mapping
from pathlib import Path


SCHEMA_VERSION = 2
_ID = re.compile(r"^[a-z0-9_]+\.[a-z0-9_]+$")
_ALIAS = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 ._-]{0,63}$")
_DOMAINS = {"entities": {"light", "switch"}, "timers": {"timer"},
            "media": {"media_player"}, "temperatures": {"sensor"}}


def safe_output_path(raw: str) -> Path:
    path = Path(raw)
    root = Path("/share/aster-registry")
    if path.parent != root or path.name != "latest.json":
        raise ValueError("output path must be /share/aster-registry/latest.json")
    return path


def write_atomic(path: Path, report: dict) -> None:
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=".latest.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(report, handle, sort_keys=True, separators=(",", ":"))
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def validate_aliases(aliases: Mapping[str, Mapping[str, str]]) -> None:
    seen: list[str] = []
    for group, domains in _DOMAINS.items():
        mapping = aliases.get(group, {})
        for entity_id, alias in mapping.items():
            if not _ID.fullmatch(entity_id) or entity_id.split(".", 1)[0] not in domains:
                raise ValueError("alias configuration contains an invalid entity id")
            if not _ALIAS.fullmatch(alias):
                raise ValueError("alias configuration contains an invalid alias")
            seen.append(alias.casefold())
    for area_id, alias in aliases.get("rooms", {}).items():
        if not re.fullmatch(r"[a-z0-9_]{1,64}", area_id) or not _ALIAS.fullmatch(alias):
            raise ValueError("alias configuration contains an invalid area")
        seen.append(alias.casefold())
    if len(seen) != len(set(seen)):
        raise ValueError("aliases must be unique across the exported registry")


def build_snapshot(*, snapshot_id: str, aliases: Mapping[str, Mapping[str, str]],
                   entity_ids: set[str], area_ids: set[str], states: Mapping[str, str],
                   units: Mapping[str, str] | None = None) -> dict:
    validate_aliases(aliases)
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}", snapshot_id):
        raise ValueError("invalid snapshot id")
    if set(states) - entity_ids:
        raise ValueError("state input contains an entity absent from the registry")
    units = units or {}
    if set(units) - entity_ids:
        raise ValueError("unit input contains an entity absent from the registry")
    lights = []
    for entity_id, alias in aliases.get("entities", {}).items():
        if (entity_id.startswith("light.") and entity_id in entity_ids
                and states.get(entity_id) in {"on", "off"}):
            lights.append({"alias": alias, "state": states[entity_id]})
    temperatures = []
    for entity_id, alias in aliases.get("temperatures", {}).items():
        if entity_id not in entity_ids or units.get(entity_id) not in {"°C", "°F"}:
            continue
        try:
            value = float(states[entity_id])
        except (KeyError, ValueError, TypeError):
            continue
        minimum, maximum = (-50, 60) if units[entity_id] == "°C" else (-58, 140)
        if math.isfinite(value) and minimum <= value <= maximum:
            temperatures.append({"alias": alias, "value": round(value, 1),
                                 "unit": units[entity_id]})
    return {
        "schema_version": SCHEMA_VERSION,
        "snapshot_id": snapshot_id,
        "lights": sorted(lights, key=lambda item: item["alias"]),
        "temperatures": sorted(temperatures, key=lambda item: item["alias"]),
        "timers": sorted(alias for entity_id, alias in aliases.get("timers", {}).items()
                         if entity_id in entity_ids and states.get(entity_id) in {"active", "paused"}),
        "rooms": sorted(alias for area_id, alias in aliases.get("rooms", {}).items() if area_id in area_ids),
        "entities": sorted(alias for entity_id, alias in aliases.get("entities", {}).items()
                           if entity_id in entity_ids and states.get(entity_id) not in {None, "unavailable", "unknown"}),
        "media_providers": sorted(alias for entity_id, alias in aliases.get("media", {}).items()
                                  if entity_id in entity_ids and states.get(entity_id) not in {None, "unavailable", "unknown"}),
    }
