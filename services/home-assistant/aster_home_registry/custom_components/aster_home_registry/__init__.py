"""Aster Home's isolated, read-only Home Assistant display exporter."""

from __future__ import annotations

from datetime import timedelta

import voluptuous as vol
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.event import async_track_state_change_event, async_track_time_interval
from homeassistant.helpers.typing import ConfigType

from .contract import ENTITY_IDS, HALL, OUTSIDE, CLOSET, build_snapshot, write_atomic


DOMAIN = "aster_home_registry"
CONFIG_SCHEMA = vol.Schema({DOMAIN: vol.Schema({})}, extra=vol.ALLOW_EXTRA)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Observe exactly three reviewed IDs; never register a service or action."""
    if DOMAIN not in config:
        return True

    async def refresh(*_args) -> None:
        registry = er.async_get(hass)
        present = {entity_id for entity_id in ENTITY_IDS if registry.async_get(entity_id)}
        current = {entity_id: hass.states.get(entity_id) for entity_id in present}
        states = {entity_id: state.state for entity_id, state in current.items()
                  if state is not None}
        units = {entity_id: current[entity_id].attributes.get("unit_of_measurement")
                 for entity_id in (HALL, OUTSIDE, CLOSET) if current.get(entity_id) is not None}
        report = build_snapshot(states, units)
        await hass.async_add_executor_job(write_atomic, report)

    await refresh()
    async_track_state_change_event(hass, ENTITY_IDS, refresh)
    async_track_time_interval(hass, refresh, timedelta(minutes=5))
    return True
