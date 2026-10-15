# Home Assistant Operational Reference

> Authority: current-with-exclusions
>
> Reviewed: 2026-10-10
>
> Sources: live HAOS Supervisor CLI through Proxmox guest agent; `docs/01-Architecture.md`; `docs/04-Operations.md`; `docs/05-Backups.md`; `PROJECTS.md`

This is Aster's reviewed Home Assistant curriculum. Live transient claims come
only from the fixed-path sanitized report. This page owns reviewed operational
relationships; project logs own historical evidence.

## Current platform and boundaries

Home Assistant OS runs as VM 103 on Proxmox at `192.168.20.11`, Servers VLAN
20. It is the sole automation authority for rebuilt household automations.
Vendor applications remain responsible for firmware, recovery, safety
functions and unsupported features. Only the Home Assistant host may initiate
the approved broad TCP/UDP integration traffic to IoT VLAN 30; IoT does not
receive a general path back to Servers.

The 2026-09-10 live review found Core 2026.9.1 and Supervisor 2026.09.0 healthy,
supported and current. The Matter Server app was running and the dedicated
TrueNAS backup mount was active. These are dated observations, not substitutes
for the sanitized current report.

## Integration ownership

Philips Hue, Lutron Caseta, Aqara Matter and Sonos are integrated. Aqara retains
ownership of water-leak/shutoff safety behavior. HomeKit Bridge is a filtered
presentation layer for Apple Home and Siri; Home Assistant remains authoritative.
Published domains are light, switch, lock, climate, cover, fan, vacuum, scene,
script and binary_sensor. Media players, cameras, general sensors, automations,
buttons and helpers remain excluded to avoid duplicate control and clutter.

## Automation pattern

The validated Laundry workflow uses the Hue Hall motion trigger, `Laundry
bright` scene, `Laundry motion lighting` script, a five-minute `Laundry
occupancy timer`, and a separate `timer.finished` automation that turns the
Lutron light off. Use traces to validate each stage. Existing vendor automation
history must not be imported blindly; rebuild and validate one owner at a time.

## Backup and recovery

VM 103 has mirrored Proxmox guest archives. Home Assistant also creates
encrypted native backups locally and on the dedicated TrueNAS SMB backup share
at `192.168.20.40`. The old Backup Synology `.42` destination is historical and
must not be reported as current. An isolated VM 903 restore previously proved
HAOS, Supervisor and Core startup. Recovery decisions remain operator-owned.

## Known exclusions and AI boundary

The aggregate Aster health report excludes entity/device/user/area names and
counts, state values, presence, locks, alarms, cameras, media, locations,
automation traces, logs, configuration, URLs, tokens and credentials. A
separate source-local pilot may export only exact human-reviewed aliases: as of
2026-10-10 that allowlist contains only `laundry lights`, backed by
`light.laundry_laundry_main_lights`. It does not export the raw friendly name,
attributes or unrelated registry entries.

Aster has no Home Assistant credential, network client, arbitrary file access
or mutation tool. The pilot report can reach only the recording adapter, which
sets `effect_permitted: false`; natural-language chat still cannot call services
or change Home Assistant. Frigate/MQTT integration remains a bounded future
project, not a current fact.

## Aster registry pilot operation and rollback

The disabled-effect custom integration lives at
`/config/custom_components/aster_registry` and writes only
`/share/aster-registry/latest.json`, mode 0600. Configuration is under the
top-level `aster_registry` key in `/config/configuration.yaml`. It registers no
services, actions, entities, HTTP route or credentials. Home Assistant Core
must pass `ha core check` before any restart.

The pre-change recovery points are Proxmox snapshot
`aster-registry-pre-20261010`, the fresh 2026-10-10 02:33 VM 103 archive, and
`/config/configuration.yaml.before-aster-registry-20261010`. Normal rollback is:
restore that configuration copy, remove only
`/config/custom_components/aster_registry` and
`/share/aster-registry/latest.json`, run `ha core check`, then restart only
Home Assistant Core. Use the VM snapshot only if file-level rollback cannot
restore a healthy Core. Do not roll back unrelated Home Assistant state.

## Aster Home read-only display pilot

VM 103 also runs a separate `aster_home_registry` custom integration with
`aster_home_registry: {}` in `/config/configuration.yaml`. It writes only
`/share/aster-home-registry/latest.json` (schema v2, mode 0600), on the
reviewed light/temperature state changes and every five minutes. It is
independent of the schema-v1 `aster_registry` report above, which must not be
replaced. The fixed display allowlist is Laundry main light, hall, outside and
owner-approved closet temperature. Hall/outside Hue readings were unavailable
at the October 14 pilot; their values are omitted, not guessed. The report
registers no service, action, entity or HTTP route.

Recovery points: Proxmox snapshot `aster-home-pre-20261014` and mode-0600
`/config/configuration.yaml.before-aster-home-20261014`. For file-level
rollback, restore that YAML copy, remove only
`/config/custom_components/aster_home_registry` and
`/share/aster-home-registry/latest.json`, run `ha core check`, then restart
Core only. Preserve the schema-v1 Aster registry files and report. Use the
snapshot only if file-level recovery fails; it can roll back unrelated HA
state. No production rollback drill has been performed.

The Mac Kodi Home test uses a manual source-local projection, not a persistent
HA endpoint. Frigate contributes one `front_of_house` online/offline status
only; camera frames and recordings never enter the Kodi feed. A live preview
or persistent delivery path needs a separate security and privacy gate.
