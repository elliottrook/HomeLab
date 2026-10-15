"""Disabled-by-default, read-only Aster registry export integration."""

from __future__ import annotations

from datetime import timedelta

import voluptuous as vol
from homeassistant.core import HomeAssistant
from homeassistant.helpers import area_registry as ar, config_validation as cv, entity_registry as er
from homeassistant.helpers.event import async_track_state_change_event, async_track_time_interval
from homeassistant.helpers.typing import ConfigType

from .contract import build_snapshot, safe_output_path, validate_aliases, write_atomic


DOMAIN = "aster_registry"
CONF_OUTPUT_PATH = "output_path"
CONF_SNAPSHOT_ID = "snapshot_id"
CONF_ALIASES = "aliases"
_GROUPS = ("entities", "rooms", "timers", "media", "temperatures")

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Required(CONF_OUTPUT_PATH): cv.string,
        vol.Required(CONF_SNAPSHOT_ID): cv.string,
        vol.Required(CONF_ALIASES): {vol.Required(group): {cv.string: cv.string} for group in _GROUPS},
    })
}, extra=vol.ALLOW_EXTRA)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Activate only when an explicit YAML block exists; register no services."""
    if DOMAIN not in config:
        return True
    settings = config[DOMAIN]
    output = safe_output_path(settings[CONF_OUTPUT_PATH])
    aliases = {group: dict(settings[CONF_ALIASES][group]) for group in _GROUPS}
    validate_aliases(aliases)
    configured_entities = set().union(*(aliases[group] for group in ("entities", "timers", "media", "temperatures")))

    async def refresh(*_args) -> None:
        entity_registry = er.async_get(hass)
        area_registry = ar.async_get(hass)
        existing_entities = {entity_id for entity_id in configured_entities if entity_registry.async_get(entity_id)}
        existing_areas = {area_id for area_id in aliases["rooms"] if area_registry.async_get_area(area_id)}
        states = {entity_id: state.state for entity_id in existing_entities
                  if (state := hass.states.get(entity_id)) is not None}
        units = {entity_id: state.attributes.get("unit_of_measurement")
                 for entity_id in aliases["temperatures"] if entity_id in existing_entities
                 if (state := hass.states.get(entity_id)) is not None}
        report = build_snapshot(snapshot_id=settings[CONF_SNAPSHOT_ID], aliases=aliases,
                                entity_ids=existing_entities, area_ids=existing_areas,
                                states=states, units=units)
        await hass.async_add_executor_job(write_atomic, output, report)

    await refresh()
    if configured_entities:
        async_track_state_change_event(hass, configured_entities, refresh)
    async_track_time_interval(hass, refresh, timedelta(minutes=5))
    return True
