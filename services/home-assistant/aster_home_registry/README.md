# Aster Home isolated display exporter

This is an offline, disabled-by-default Home Assistant custom integration
candidate. It uses the separate `aster_home_registry` domain and fixed
`/share/aster-home-registry/latest.json` path. It does not modify the deployed
schema-v1 `aster_registry` component, configuration, or report used by Aster's
no-effect recording pilot. Installing the files alone has no effect; the
reviewed YAML block opts in. It registers no entities, services, actions,
network listener or credentials.

The exact allowlist is compiled into `contract.py`: the Laundry main light,
hall temperature and outside temperature. The light exports only on/off;
temperatures export only finite values from -50 to 60 °C or -58 to 140 °F.
Unknown, unavailable, stale-at-source or unexpected units are omitted. The
schema-v2 output retains empty compatibility arrays for the Kodi Home reader.
Output is atomic and mode 0600, initially and on reviewed state changes or
every five minutes. Kodi is not connected automatically: a separate protected
delivery step must wrap this snapshot with a timestamp and copy only the
approved fields to the Kodi profile.

Read-only preflight on 2026-10-14 found both temperature entities registered
and Celsius-configured, but the latest Recorder states for both were
`unavailable`; the recent history was also unavailable. The Laundry light was
`on` at its latest recorded state. **Do not deploy as a three-value acceptance
test until the temperature source is restored or Jason accepts a light-only
pilot.** No VM 103 snapshot, copy, configuration edit, or Core restart has
occurred for this sidecar.

If deployment is approved after that decision, first capture a fresh VM 103
recovery checkpoint and a private copy of `/config/configuration.yaml`.
Confirm the v1 report and hashes, copy only this sidecar, append only
`aster_home_registry: {}` to the HA YAML, run `ha core check`, and restart
Core only. Validate both reports independently, output mode, state-change and
five-minute refresh, then the Kodi delivery. File-level rollback removes the
new block, component and its own output only, followed by `ha core check` and
a Core-only restart. Never remove the existing `aster_registry` block or file.
