# Home Assistant Operational Reference

> Authority: current-with-exclusions
>
> Reviewed: 2026-09-10
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

The Aster report excludes entity/device/user/area names and counts, state
values, presence, locks, alarms, cameras, media, locations, automation traces,
logs, configuration, URLs, tokens and credentials. Aster has no Home Assistant
credential, network client, arbitrary file access or mutation tool. It may
explain, diagnose from reviewed sources and bounded report fields, and produce
a reviewable proposal. Natural-language chat cannot call services or change
Home Assistant. Frigate/MQTT integration remains a bounded future project, not
a current fact.
