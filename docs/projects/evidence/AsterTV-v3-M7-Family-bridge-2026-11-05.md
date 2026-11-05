# AsterTV v3 M7 Family equipment bridge — 2026-11-05

## Outcome

The Family Aster Remote now controls only the accepted Family television and
receiver functions: explicit power on/off, volume up/down and mute on/off.
Home Assistant initiates one outbound, long-polled connection to Aster Agent;
Aster has no Home Assistant token and cannot name an entity, domain, service or
payload. Bedroom and Jen expose no equipment capability.

## Installed boundary

- Home Assistant client `HA-Family`, room `family`, uses an independently
  revocable mode-`0600` key read from
  `/config/.aster-private/aster-room-bridge.key`.
- Aster Agent reads the matching mode-`0600` key from
  `/etc/aster/remote-family-equipment.key`. The key never entered Git or this
  evidence.
- OPNsense permits only `192.168.20.11` to `192.168.70.10:9120/TCP`. Rule UUID
  is `5e3a94b5-8059-45f7-b45c-f3b7484c4cf1`; the before/proof records are
  `/conf/backup/config-astertv-m7-ha-bridge-before-20261105.xml` and
  `/conf/backup/config-astertv-m7-ha-bridge-proof-20261105.json`.
- Home Assistant maps Family power to `media_player.family_room_tv` and
  volume/mute to `media_player.tx_rz30`. No generic HA service or inbound view
  was registered.
- Gateway connection freshness, per-room capability, request-ID deduplication,
  queue bounds and acknowledgements remain mandatory. Power, volume and mute
  now also fail closed independently if their corresponding reported state is
  unavailable. The PWA disables each control on the same state boundary.

## Recovery and regression evidence

Home Assistant full backup `astertv-m7-family-bridge-pre-20261105` has slug
`35b3cbd9`. Aster Agent rollback material is retained under
`/var/lib/aster/checkpoints/astertv-v3-m7-family-bridge-20261105/`; Home
Assistant configuration/component rollback material is under
`/config/.aster-checkpoints/astertv-v3-m7-family-bridge-20261105/`.

The first Home Assistant start exposed two integration defects rather than
silently accepting them: synchronous key loading produced an event-loop
warning, and registering the permanent poll as a startup task delayed startup
completion. Key reading now runs in the executor and the poll is a Home
Assistant background task. A subsequent configuration check and Core restart
completed normally with no new bridge, blocking-call or startup-wait warning.

The first end-to-end semantic `volume_down` request completed and changed the
native Onkyo value from `0.590` to `0.585`. During the restart investigation the
receiver entity was briefly unavailable, so no further command was sent until
Core, the entity and the equipment heartbeat had recovered. After the
availability guards were installed, one semantic `volume_up` restored exactly
`0.590`. Recorder and the live bounded session independently reported the
receiver `on`, unmuted and at `0.59`; the bridge acknowledgement was
`completed`. No power, source, playback or navigation command was used during
this deployment.

Ten gateway tests pass in Aster Agent's pinned environment. The static Remote
suite and Home Assistant contract/source checks pass locally, as do JavaScript
syntax and diff checks. Installed hashes match the candidate:

- Aster gateway: `f2780775df560903ecf6a0b4efe224343f327914bd680fe8fdd4abb24484e983`
- Remote client: `c4b3b371c18a7b3f53dad298ad8440f303b47f8c9c96cafbbb5c4c364e0df52b`
- Home Assistant bridge: `213a813d3c6b71ab5b6208223060bd24ed7f4a030a247aebe43bc0b012d95fac`

All transient key and package handoffs were removed. The live revocable keys
and recovery checkpoints were deliberately retained.

## Residual scope

This completes only the accepted Family equipment surface. It does not add
Kodi, playback, source selection, fixed volume profiles, Bedroom equipment or
Guest/Jen authority. Those remain separate M7 gates.
