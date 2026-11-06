# British Columbia permanent-time alignment

> **Status:** Active — Stream M; Arista corrected, Synology handoff pending
>
> **Owner:** Jason
>
> **Started:** 2026-11-06
>
> **Authorization stream:** Stream M

## Purpose and desired outcome

Ensure every managed HomeLab system that presents or schedules British Columbia
local time uses permanent Pacific time at UTC−07:00 after November 1, 2026.
Systems intentionally operated in UTC remain in UTC; their Vancouver timezone
data and local-time schedule conversion must still resolve to UTC−07:00.

This project produces no speech.

## Current state and evidence

The Province of British Columbia made the March 8, 2026 clock advance the final
seasonal change. Most of the province remains at UTC−07:00 after November 1.
The 2026-11-06 audit found that current Apple, Debian and appliance timezone
data already encode this rule, commonly displaying the post-transition
abbreviation `MST` while retaining the `America/Vancouver` zone identity.

| System or layer | Observed state | Decision |
|---|---|---|
| Mac mini, macOS 26.6.2 | `America/Vancouver`, UTC−07:00 | Correct; retain |
| Proxmox | `America/Vancouver`, UTC−07:00, NTP synchronized | Correct; retain |
| All 19 running LXCs | Every `TZ=America/Vancouver` resolution returned UTC−07:00 | Correct; retain UTC guests where intentional |
| Frigate VM 102 and Home Assistant VM 103 | UTC−07:00 | Correct; retain |
| TrueNAS | Fixed `Etc/GMT+7`, UTC−07:00 | Correct; retain |
| NUT host | `America/Vancouver`, UTC−07:00 | Correct; retain |
| OPNsense | Intentional UTC; NTP offset below 1 ms; Vancouver rules available to clients | Correct; retain UTC |
| Docker applications inspected on LXC 100 | Pi-hole and code-server resolve `America/Vancouver` to UTC−07:00 | Correct; retain |
| Synology DS920+ | `Pacific` → `US/Pacific`, currently UTC−08:00 despite an updated `America/Vancouver` zone file | Incorrect; correction required |
| Arista core | UTC retained; OPNsense selected as NTP peer; clock corrected and configuration saved | Correct |
| VM 127 | Disposable LibreELEC/Kodi UI test without production data, credentials or autostart | Excluded from production-time graduation |

Repository search found no live UTC−08:00 schedule. Current recurring timers use
either UTC, fixed `Etc/GMT+7`, or `America/Vancouver`; the deployed Linux
timezone data resolves the last form to permanent UTC−07:00.

## Scope and exclusions

In scope: Mac, Proxmox, running guests, TrueNAS, Synology, OPNsense, Arista,
NUT, deployed application timezone data and tracked scheduler configuration.

Excluded: changing intentionally UTC systems merely for display preference;
altering historical timestamps; personal phones, televisions and unmanaged IoT
clocks; East Kootenay locations that legally remain aligned with Alberta.

## Authority model

The Province of British Columbia is authoritative for the civil-time rule.
NTP is authoritative for clock synchronization. Each operating system or
appliance owns its timezone selection; the repository records intended
schedules but does not override deployed state without a reviewed change.

## Architecture, privacy and security

No network path, credential, firewall rule, DNS record, public exposure or user
data changes are required. Read-only checks use existing administration paths.
Operational changes are limited to timezone selection on the Synology and NTP
configuration on the Arista core.

## Pre-start risk assessment

Changing a timezone can move local-time scheduled tasks by one hour. Enabling
NTP can step an incorrect appliance clock. Controls are: capture exact
pre-state, change one system at a time, avoid changing UTC-based services,
validate current offset plus future winter/summer behavior, and inspect
scheduled-job health after each correction. No destructive action is required.

Synology rollback is its current `Pacific`/`US/Pacific` selection. Arista
rollback removes only the added NTP server/configuration and restores the saved
running configuration. Abort on unavailable configuration backup, unsupported
timezone selection, unexpected package restart, or schedule drift.

## Persistence and milestones

- [x] Verify the legal rule from official provincial sources.
- [x] Audit the Mac, Proxmox, running LXCs, principal VMs, storage, firewall,
  switch, NUT host, Docker timezone consumers and tracked schedules.
- [ ] Correct Synology from seasonal `US/Pacific` to permanent UTC−07:00 and
  validate DSM, cron, storage services and NTP health.
- [x] Enable Arista NTP against the existing OPNsense management-VLAN NTP
  listener while retaining UTC display; validate synchronization and save the
  running configuration.
- [x] Document VM 127's intentional exclusion as a disposable, non-production,
  non-autostart UI test guest.
- [ ] Run a final estate audit and close the project.

## Validation, observability and rollback

Validation requires current timestamps, UTC offsets, NTP state and the next
scheduled execution for affected services. HomeLab Doctor/NetBox/Beszel changes
are not required because no host or service identity changes. Configuration
backups and this evidence record are sufficient; each pending remote change
retains a one-command or UI rollback to its captured pre-state.

## Evidence log

### 2026-11-06 — Legal and estate audit

- Official B.C. guidance confirmed permanent UTC−07:00 for most of the province.
- Corrected the operator-facing interpretation after a stale UTC−08:00 lookup.
- Verified the Mac, Proxmox, every running LXC, Frigate, Home Assistant,
  TrueNAS, NUT, OPNsense and inspected Docker applications.
- Found exactly two actionable defects: Synology on seasonal `US/Pacific` and
  Arista running an unsynchronized local clock in UTC.
- No remote state was changed during the audit.

### 2026-11-06 — Arista time-integrity correction

- Added only `ntp server 192.168.50.1 iburst` to the Arista core.
- OPNsense was already listening on the Management VLAN NTP address and was
  synchronized to its upstream pool.
- Arista selected OPNsense as the active peer, advanced from its roughly
  five-minute error, recorded three consecutive successful polls (`reach 7`),
  measured an 0.081 ms offset, and matched the Mac UTC clock within one second.
- Saved the exact NTP line to startup configuration. Rollback is
  `no ntp server 192.168.50.1` followed by `write memory`.
- Follow-up at `reach 17` retained the selected peer and an 0.089 ms offset,
  but EOS still printed `unsynchronised`; retain this as an open validation
  observation until the reach history fills or the status label clears.

## Close-out

Not ready. Synology DSM remains on seasonal `US/Pacific`; its SSH administration
identity has no elevation and local browser control is disabled, so the
supported DSM timezone change requires owner interaction. Arista also needs a
later read-only confirmation that EOS clears its stale `unsynchronised` status
after more good polls. Final validation follows those observations.
