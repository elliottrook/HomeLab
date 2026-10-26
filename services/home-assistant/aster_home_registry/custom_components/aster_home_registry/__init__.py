"""Aster Home's isolated, read-only Home Assistant display exporter."""

from __future__ import annotations

from datetime import timedelta
import asyncio
import logging

import voluptuous as vol
from homeassistant.core import HomeAssistant
from homeassistant.const import EVENT_STATE_CHANGED
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.event import async_call_later, async_track_time_interval
from homeassistant.helpers.typing import ConfigType

from .contract import ENTITY_IDS, HALL, OUTSIDE, CLOSET, WEATHER, build_snapshot, write_atomic
from .dashboard_contract import relevant, project, write_dashboard
from .delivery import publish


DOMAIN = "aster_home_registry"
CONFIG_SCHEMA = vol.Schema({DOMAIN: vol.Schema({})}, extra=vol.ALLOW_EXTRA)
LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Preserve legacy output; add household display data without device actions."""
    if DOMAIN not in config:
        return True

    lock = asyncio.Lock()
    pending = None

    async def refresh(*_args) -> None:
        async with lock:
            registry = er.async_get(hass)
            present = {entity_id for entity_id in ENTITY_IDS if registry.async_get(entity_id)}
            current = {entity_id: hass.states.get(entity_id) for entity_id in present}
            states = {entity_id: state.state for entity_id, state in current.items()
                      if state is not None}
            units = {entity_id: current[entity_id].attributes.get("unit_of_measurement")
                     for entity_id in (HALL, OUTSIDE, CLOSET) if current.get(entity_id) is not None}
            attributes = ({WEATHER: dict(current[WEATHER].attributes)}
                          if current.get(WEATHER) is not None else {})
            report = build_snapshot(states, units, attributes)
            await hass.async_add_executor_job(write_atomic, report)
            # State objects and their raw attributes never leave Core.
            try:
                rows = [dict(entity_id=state.entity_id, state=state.state,
                             attributes=dict(state.attributes))
                        for state in hass.states.async_all() if relevant(state.entity_id)]
                dashboard = project(rows)
                await hass.async_add_executor_job(write_dashboard, dashboard)
            except (ValueError, OSError):
                # Keep the last file with its old timestamp: TV must show stale,
                # never pretend a failed collection is a current healthy report.
                LOGGER.warning("Aster Home dashboard refresh failed; legacy export preserved")

    async def scheduled_refresh(*_args):
        nonlocal pending
        pending = None
        await refresh()

    async def periodic_refresh(*_args):
        await refresh()
        await publish()

    def changed(event):
        nonlocal pending
        if relevant(event.data.get('entity_id')) and pending is None:
            pending = async_call_later(hass, 1, scheduled_refresh)

    await periodic_refresh()
    hass.bus.async_listen(EVENT_STATE_CHANGED, changed)
    async_track_time_interval(hass, periodic_refresh, timedelta(minutes=5))
    return True
