"""Outbound-only, capability-scoped Aster room equipment bridge."""

from __future__ import annotations

import asyncio
from contextlib import suppress
from pathlib import Path
import stat
import time

import voluptuous as vol

from homeassistant.const import EVENT_HOMEASSISTANT_STOP
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .contract import EQUIPMENT_ACTIONS, RoomContract, observation
from .content_policy import (
    CONTENT_CLASSES, CurrentState, PlaybackObservation, VolumeProfile,
    VolumeSessionController,
)


DOMAIN = "aster_room_bridge"
VOLUME_TARGETS = CONTENT_CLASSES - {"Unknown"}
VOLUME_PROFILE_SCHEMA = vol.Schema({
    vol.Optional("enabled", default=False): cv.boolean,
    vol.Required("targets"): vol.Schema({
        vol.Required(name): vol.All(vol.Coerce(float), vol.Range(min=0, max=1))
        for name in sorted(VOLUME_TARGETS)
    }),
    vol.Required("nighttime_ceiling"): vol.All(
        vol.Coerce(float), vol.Range(min=0, max=1)
    ),
    vol.Required("nighttime_entity"): cv.entity_id,
    vol.Required("nighttime_on_state"): cv.string,
    vol.Required("nighttime_off_state"): cv.string,
    vol.Optional("maximum_step", default=0.02): vol.All(
        vol.Coerce(float), vol.Range(min=0.001, max=0.05)
    ),
    vol.Optional("ramp_delay", default=0.25): vol.All(
        vol.Coerce(float), vol.Range(min=0.1, max=2.0)
    ),
})
ROOM_SCHEMA = vol.Schema({
    vol.Required("gateway_url"): cv.url,
    vol.Required("client_id"): cv.string,
    vol.Required("room_id"): cv.string,
    vol.Required("key_file"): cv.string,
    vol.Required("power_entity"): cv.entity_id,
    vol.Required("volume_entity"): cv.entity_id,
    vol.Required("actions"): vol.All(cv.ensure_list, [vol.In(EQUIPMENT_ACTIONS)]),
    vol.Optional("content_volume"): VOLUME_PROFILE_SCHEMA,
})
CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Any(
        ROOM_SCHEMA,
        vol.Schema({vol.Required("rooms"): vol.All(cv.ensure_list, [ROOM_SCHEMA])}),
    )
}, extra=vol.ALLOW_EXTRA)


def _private_key(path: str) -> str:
    target = Path(path)
    details = target.stat()
    if not stat.S_ISREG(details.st_mode) or details.st_mode & 0o077:
        raise ValueError("equipment-key-boundary")
    value = target.read_text(encoding="utf-8").strip()
    if len(value) < 32 or any(character.isspace() for character in value):
        raise ValueError("equipment-key-invalid")
    return value


class RoomBridge:
    def __init__(self, hass: HomeAssistant, config: dict, key: str):
        self.hass = hass
        self.url = config["gateway_url"].rstrip("/") + "/v1/remote/equipment"
        self.client_id = config["client_id"]
        self.room_id = config["room_id"]
        self.key = key
        self.contract = RoomContract(
            config["power_entity"], config["volume_entity"],
            frozenset(config["actions"]),
        )
        self.session = async_get_clientsession(hass)
        self.content_state = CurrentState()
        self.content_supported = True
        volume = config.get("content_volume")
        self.volume_controller = None
        self.nighttime_entity = None
        self.nighttime_on_state = None
        self.nighttime_off_state = None
        self.ramp_delay = None
        if volume and volume["enabled"]:
            self.volume_controller = VolumeSessionController(VolumeProfile(
                targets=dict(volume["targets"]),
                nighttime_ceiling=volume["nighttime_ceiling"],
                maximum_step=volume["maximum_step"],
            ))
            self.nighttime_entity = volume["nighttime_entity"]
            self.nighttime_on_state = volume["nighttime_on_state"]
            self.nighttime_off_state = volume["nighttime_off_state"]
            self.ramp_delay = volume["ramp_delay"]

    def _headers(self) -> dict[str, str]:
        return {"Authorization": "Bearer " + self.key,
                "X-AsterTV-Client": self.client_id}

    def _payload(self) -> dict:
        power = self.hass.states.get(self.contract.power_entity)
        volume = self.hass.states.get(self.contract.volume_entity)
        return {"client_id": self.client_id, "room_id": self.room_id,
                **observation(power.state if power else None,
                              dict(volume.attributes) if volume else None)}

    async def _ack(self, request_id: str, outcome: str):
        payload = {"client_id": self.client_id, "room_id": self.room_id,
                   "request_id": request_id, "outcome": outcome}
        async with self.session.post(self.url + "/ack", json=payload,
                                     headers=self._headers(), timeout=10) as response:
            if response.status != 200:
                raise RuntimeError("equipment-ack-failed")

    async def _content(self):
        if not self.content_supported:
            return
        payload = {"client_id": self.client_id, "room_id": self.room_id}
        async with self.session.post(self.url + "/content", json=payload,
                                     headers=self._headers(), timeout=10) as response:
            if response.status == 204:
                return
            if response.status in {404, 405}:
                # The deployed predecessor has no content endpoint. Keep the
                # existing equipment bridge live during a gateway-first roll.
                self.content_supported = False
                return
            if response.status != 200:
                raise RuntimeError("content-state-poll-failed")
            value = await response.json()
        state = PlaybackObservation.parse(value, now_epoch=int(time.time()))
        if state.room_id != self.room_id:
            raise ValueError("content-state-room")
        previous = self.content_state.get(self.room_id)
        if (previous is not None and previous.session_id == state.session_id
                and previous.sequence == state.sequence):
            return
        self.content_state.accept(state)
        self.hass.data.setdefault(DOMAIN, {}).setdefault(
            "content_states", {}
        )[self.room_id] = state
        await self._content_volume(state)

    async def _content_volume(self, state: PlaybackObservation):
        controller = self.volume_controller
        if controller is None:
            return
        volume = self.hass.states.get(self.contract.volume_entity)
        nighttime = self.hass.states.get(self.nighttime_entity)
        level = volume.attributes.get("volume_level") if volume else None
        level_valid = (isinstance(level, (int, float))
                       and not isinstance(level, bool) and 0 <= level <= 1)
        nighttime_valid = (nighttime is not None
                           and nighttime.state in {
                               self.nighttime_on_state,
                               self.nighttime_off_state,
                           })
        if not level_valid or not nighttime_valid:
            controller.suppress(
                state, current_level=float(level) if level_valid else None
            )
            return
        decision = controller.observe(
            state, current_level=float(level),
            nighttime=nighttime.state == self.nighttime_on_state,
        )
        for target in decision.ramp:
            await self.hass.services.async_call(
                "media_player", "volume_set",
                {"entity_id": self.contract.volume_entity,
                 "volume_level": target},
                blocking=True,
            )
            controller.applied(target)
            await asyncio.sleep(self.ramp_delay)

    async def run(self):
        while True:
            try:
                try:
                    await self._content()
                except asyncio.CancelledError:
                    raise
                except Exception:
                    # Content observation must fail closed without taking down
                    # already accepted Family power/volume/mute controls.
                    pass
                async with self.session.post(
                    self.url + "/poll", json=self._payload(),
                    headers=self._headers(), timeout=25,
                ) as response:
                    if response.status == 204:
                        continue
                    if response.status != 200:
                        raise RuntimeError("equipment-poll-failed")
                    command = await response.json()
                request_id = command.get("request_id")
                action = command.get("action")
                if not isinstance(request_id, str) or not isinstance(action, str):
                    raise ValueError("equipment-command-invalid")
                try:
                    call = self.contract.service_call(action)
                    await self.hass.services.async_call(
                        call.domain, call.service, call.data, blocking=True)
                    outcome = "completed"
                except ValueError:
                    outcome = "denied"
                except Exception:
                    outcome = "unavailable"
                await self._ack(request_id, outcome)
            except asyncio.CancelledError:
                raise
            except Exception:  # fail closed; reconnect without widening authority
                await asyncio.sleep(2)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    if DOMAIN not in config:
        return True
    domain_config = config[DOMAIN]
    rows = domain_config.get("rooms", [domain_config])
    room_ids = [row["room_id"] for row in rows]
    if len(rows) == 0 or len(room_ids) != len(set(room_ids)):
        raise ValueError("equipment-room-cardinality")
    bridges = []
    tasks = []
    for row in rows:
        key = await hass.async_add_executor_job(_private_key, row["key_file"])
        bridge = RoomBridge(hass, row, key)
        bridges.append(bridge)
        tasks.append(hass.async_create_background_task(
            bridge.run(), "aster-room-bridge-" + bridge.room_id
        ))

    async def stop(_event):
        for task in tasks:
            task.cancel()
        for task in tasks:
            with suppress(asyncio.CancelledError):
                await task

    hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, stop)
    hass.data[DOMAIN] = {"bridges": {bridge.room_id: bridge for bridge in bridges}}
    if len(bridges) == 1:  # compatibility for accepted Family-only diagnostics
        hass.data[DOMAIN]["bridge"] = bridges[0]
    return True
