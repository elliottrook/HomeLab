"""Pure, credential-free contract for a source-local Home Assistant registry exporter.

Home Assistant supplies registry identifiers and current states in-process.  The
caller supplies reviewed aliases.  This module emits aliases and availability
only: it has no HTTP client, token, service-call interface or effect path.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Mapping


SCHEMA_VERSION = 1
_ID = re.compile(r"^[a-z0-9_]+\.[a-z0-9_]+$")
_ALIAS = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 ._-]{0,63}$")
_ALLOWED_ENTITY_DOMAINS = frozenset({"light", "switch"})


@dataclass(frozen=True)
class AliasConfig:
    entity_aliases: Mapping[str, str]
    room_aliases: Mapping[str, str]
    timer_aliases: Mapping[str, str]
    media_aliases: Mapping[str, str]

    def validate(self) -> None:
        groups = (
            (self.entity_aliases, _ALLOWED_ENTITY_DOMAINS),
            (self.timer_aliases, frozenset({"timer"})),
            (self.media_aliases, frozenset({"media_player"})),
        )
        aliases: list[str] = []
        for mapping, domains in groups:
            for entity_id, alias in mapping.items():
                if not _ID.fullmatch(entity_id) or entity_id.split(".", 1)[0] not in domains:
                    raise ValueError("alias configuration contains an invalid entity id")
                if not _ALIAS.fullmatch(alias):
                    raise ValueError("alias configuration contains an invalid alias")
                aliases.append(alias.casefold())
        for area_id, alias in self.room_aliases.items():
            if not re.fullmatch(r"[a-z0-9_]{1,64}", area_id) or not _ALIAS.fullmatch(alias):
                raise ValueError("alias configuration contains an invalid area")
            aliases.append(alias.casefold())
        if len(aliases) != len(set(aliases)):
            raise ValueError("aliases must be unique across the exported registry")


def build_snapshot(*, snapshot_id: str, config: AliasConfig,
                   entity_ids: set[str], area_ids: set[str], states: Mapping[str, str]) -> dict:
    """Return only reviewed aliases whose backing registry objects still exist."""
    config.validate()
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}", snapshot_id):
        raise ValueError("invalid snapshot id")
    if set(states) - entity_ids:
        raise ValueError("state input contains an entity absent from the registry")

    entities = sorted(alias for entity_id, alias in config.entity_aliases.items()
                      if entity_id in entity_ids and states.get(entity_id) not in {"unavailable", "unknown"})
    rooms = sorted(alias for area_id, alias in config.room_aliases.items() if area_id in area_ids)
    timers = sorted(alias for entity_id, alias in config.timer_aliases.items()
                    if entity_id in entity_ids and states.get(entity_id) in {"active", "paused"})
    media = sorted(alias for entity_id, alias in config.media_aliases.items()
                   if entity_id in entity_ids and states.get(entity_id) not in {None, "unavailable", "unknown"})
    return {
        "schema_version": SCHEMA_VERSION,
        "snapshot_id": snapshot_id,
        "timers": timers,
        "rooms": rooms,
        "entities": entities,
        "media_providers": media,
    }
