"""Outbound-only, capability-scoped Aster room equipment bridge."""

from __future__ import annotations

import asyncio
from contextlib import suppress
from pathlib import Path
import stat

import voluptuous as vol

from homeassistant.const import EVENT_HOMEASSISTANT_STOP
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .contract import EQUIPMENT_ACTIONS, RoomContract, observation


DOMAIN = "aster_room_bridge"
CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Required("gateway_url"): cv.url,
        vol.Required("client_id"): cv.string,
        vol.Required("room_id"): cv.string,
        vol.Required("key_file"): cv.string,
        vol.Required("power_entity"): cv.entity_id,
        vol.Required("volume_entity"): cv.entity_id,
        vol.Required("actions"): vol.All(cv.ensure_list, [vol.In(EQUIPMENT_ACTIONS)]),
    })
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

    async def run(self):
        while True:
            try:
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
    key = await hass.async_add_executor_job(_private_key,
                                            config[DOMAIN]["key_file"])
    bridge = RoomBridge(hass, config[DOMAIN], key)
    task = hass.async_create_background_task(bridge.run(), "aster-room-bridge")

    async def stop(_event):
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task

    hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, stop)
    hass.data[DOMAIN] = bridge
    return True
