"""Pure allowlist contract for the outbound Aster room bridge."""

from __future__ import annotations

from dataclasses import dataclass


EQUIPMENT_ACTIONS = frozenset({
    "equipment.power_on", "equipment.power_off",
    "equipment.volume_up", "equipment.volume_down",
    "equipment.mute_on", "equipment.mute_off",
})


@dataclass(frozen=True)
class ServiceCall:
    domain: str
    service: str
    data: dict[str, object]


@dataclass(frozen=True)
class RoomContract:
    power_entity: str
    volume_entity: str
    actions: frozenset[str]

    def __post_init__(self):
        if not self.power_entity.startswith("media_player."):
            raise ValueError("invalid-power-entity")
        if not self.volume_entity.startswith("media_player."):
            raise ValueError("invalid-volume-entity")
        if not self.actions or not self.actions <= EQUIPMENT_ACTIONS:
            raise ValueError("invalid-equipment-actions")

    def service_call(self, action: str) -> ServiceCall:
        if action not in self.actions:
            raise ValueError("equipment-action-denied")
        mapping = {
            "equipment.power_on": ("turn_on", self.power_entity, {}),
            "equipment.power_off": ("turn_off", self.power_entity, {}),
            "equipment.volume_up": ("volume_up", self.volume_entity, {}),
            "equipment.volume_down": ("volume_down", self.volume_entity, {}),
            "equipment.mute_on": ("volume_mute", self.volume_entity,
                                  {"is_volume_muted": True}),
            "equipment.mute_off": ("volume_mute", self.volume_entity,
                                   {"is_volume_muted": False}),
        }
        service, entity, extra = mapping[action]
        return ServiceCall("media_player", service,
                           {"entity_id": entity, **extra})


def observation(power_state: str | None, volume_attributes: dict | None) -> dict:
    power = power_state if power_state in {"on", "off"} else "unavailable"
    attributes = volume_attributes or {}
    level = attributes.get("volume_level")
    muted = attributes.get("is_volume_muted")
    if not isinstance(level, (int, float)) or isinstance(level, bool) or not 0 <= level <= 1:
        level = None
    if not isinstance(muted, bool):
        muted = None
    return {"power": power, "volume_level": level, "muted": muted}
