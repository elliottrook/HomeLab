# Aster Home isolated display exporter

This is a deployed, explicitly enabled Home Assistant custom integration
pilot. It uses the separate `aster_home_registry` domain and fixed
`/share/aster-home-registry/latest.json` path. It does not modify the deployed
schema-v1 `aster_registry` component, configuration, or report used by Aster's
no-effect recording pilot. Installing the files alone has no effect; the
reviewed YAML block opts in. It registers no entities, services, actions,
network listener or credentials.

The exact allowlist is compiled into `contract.py`: the Laundry main light,
hall temperature, outside temperature and the owner-approved closet
temperature. The light exports only on/off;
temperatures export only finite values from -50 to 60 °C or -58 to 140 °F.
Unknown, unavailable, stale-at-source or unexpected units are omitted. The
schema-v2 output retains empty compatibility arrays for the Kodi Home reader.
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
omitted. The old v1 report kept its schema and Laundry alias. A real state
transition has not been induced merely for testing.

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
