# Aster Home isolated display exporter

## Automatic restricted HP delivery — 2026-10-26

The expanded report below is now automatically delivered to the HP every five
minutes. The source-local identity in `/config/.aster-home-delivery` can invoke
only the HP's bounded display-file receiver; it cannot obtain a shell or
forward ports. The private key stays on HA, never on the TV or in Git. Existing
reports, configuration and source observation timestamps remain authoritative.
The HP rejects stale/replayed/malformed data and hides observations older than
ten minutes. `services/kodi/v2/tools/check_home_transport.py` verifies freshness
read-only; it neither publishes data nor reads private keys.

The exact HA-to-HP SSH firewall exception, key revocation, source code rollback
and independent restore evidence are recorded in the Version2 project under
Restricted Home delivery. Camera delivery uses a separate HP-held identity and
does not use this report or receiver. Production BOSGAME is unchanged. Review
protected HA backup custody for the source-local key before graduation.

## Expanded household display — HP v2 lab, 2026-10-25

Jason approved the relevant HA lab data and a bounded exporter checkpoint,
update and Core restart. The same opted-in integration now also writes
`/share/aster-home-registry/dashboard.json` (schema4,
`ha-home-dashboard-v4`). The original schema3 `latest.json`, its allowlist and
the separate schema1 `aster_registry` report are preserved. No new service,
account, credential, HTTP listener, device action or scheduled transport was
introduced. A proposed source-local Supervisor API read returned HTTP401 and
was abandoned; the implementation instead uses the existing in-process state
access, not another authentication path.

`dashboard_contract.py` projects useful lighting, temperature, humidity,
battery, illuminance, leak/motion/opening/safety, weather, camera status and
structured timer fields only. Raw attributes, token/stream URLs, coordinates,
people, phone activity and system-maintenance data are not exported. Camera
status is not a stream authorization. Unknown/unavailable readings retain
their status, not a fabricated numeric value. Maximum256 display entities,
262144bytes, atomic0600 output and an explicit source observation timestamp.
Relevant state events are coalesced into a one-second refresh without
continually postponing it; the existing five-minute refresh remains. A lock
serializes writes. Collection failure preserves the last report and its old
timestamp, allowing the consumer to mark it stale.

Checkpoint: HA `/config/aster-checkpoints/home-dashboard-20261026`.
`deploy_dashboard.py prepare` verified five private backups, including an
isolated restore of code/config/old reports, then changed only `__init__.py`
and the added pure projection module. `ha core check` passed before and after
the Core-only restart. Verification found fresh63 entities:33 lights,
10battery,5illuminance,6moisture,5motion,3temperature and1weather;24 were
unknown/unavailable. Both original reports retain their contracts/modes,
configuration and old contract code remain byte-identical. Eighteen local
contract/runtime tests pass normally and with optimized Python.

Code rollback uses `deploy_dashboard.py rollback`, then `ha core check` and
a Core-only restart. It restores only the pinned predecessor `__init__.py`;
the unreferenced new module/report are retained for recovery. Never restore
old report values, configuration or listening/household state as a code rollback.
This report initially had only a one-shot consumer; the separately approved
automatic HP delivery described above is now active.

## Original compatibility pilot

This is a deployed, explicitly enabled Home Assistant custom integration
pilot. It uses the separate `aster_home_registry` domain and fixed
`/share/aster-home-registry/latest.json` path. It does not modify the deployed
schema-v1 `aster_registry` component, configuration, or report used by Aster's
no-effect recording pilot. Installing the files alone has no effect; the
reviewed YAML block opts in. It registers no entities, services, actions,
network listener or credentials.

The exact allowlist is compiled into `contract.py`: the Laundry main light,
hall temperature, outside temperature, the owner-approved closet temperature,
and `weather.forecast_home` from the built-in MET integration. The light
exports only on/off; temperatures export only finite values from -50 to 60 °C
or -58 to 140 °F. Current weather exports only a reviewed condition enum, a
bounded temperature and optional 0–100% humidity; forecast arrays, pressure,
wind, attribution, coordinates and service calls are excluded. Unknown,
unavailable, stale-at-source or unexpected units are omitted. The schema-v3
output retains empty compatibility arrays for the Kodi Home reader.
Output is atomic and mode 0600, initially and on reviewed state changes or
every five minutes. Kodi is not connected automatically: a separate protected
delivery step must wrap this snapshot with a timestamp and copy only the
approved fields to the Kodi profile.

Read-only preflight on 2026-10-14 found both Hue temperature entities registered
and Celsius-configured, but the latest Recorder states for both were
`unavailable`; the recent history was also unavailable. The Laundry light was
`on` and the closet temperature 17.0 °C at their latest recorded states. Jason
approved the closet reading as an interim source. The two unavailable Hue
temperatures remain in the allowlist but are omitted until genuinely
available; do not treat this as a hall/outside acceptance test.

The deployment checkpoint is Proxmox VM 103 snapshot
`aster-home-pre-20261014`; the private YAML copy is
`/config/configuration.yaml.before-aster-home-20261014` (mode 0600).
`ha core check` passed before and after the Core-only restart. Both v1 and v2
reports are mode 0600 and independently refreshed after five minutes. The v2
report showed Laundry `on` and closet 16.6 °C, with unavailable Hue values
omitted. Schema v3 was deployed on 2026-10-17 after preserving both replaced
Python files as `.before-weather-20261017` copies. Pre- and post-restart
`ha core check` passed, Core and HTTP recovered, and the mode-0600 report
contained only Laundry `on`, closet 16.9 °C and current MET weather (`sunny`,
15.9 °C, 60% humidity) plus the existing empty compatibility arrays. The
one-shot Kodi projection visibly rendered that weather card in skin v0.8.24.
The old v1 report kept its schema and Laundry alias. A real state transition
has not been induced merely for testing.

The Mac Kodi feed is a **manual, one-shot** projection and expires after ten
minutes. Run `python3 services/kodi/skin.asterhome/tools/pilot_home_feed.py`
from the repository to refresh it; Kodi's own Refresh button only reloads the
local file. The script additionally projects Frigate's single
`front_of_house` online/offline status, but no camera frame or stream. It
stores no credential and does not make Kodi a household-control client.

File-level rollback: restore only the private YAML copy, remove only
`/config/custom_components/aster_home_registry` and
`/share/aster-home-registry/latest.json`, run `ha core check`, then restart
Core only. Never remove the existing `aster_registry` block or file. Use the
VM snapshot only if file-level rollback cannot recover a healthy Core; a VM
rollback can also revert unrelated household state, so it is not the first
step. This rollback is documented, not yet rehearsed on production.
