# AsterTV v3 M6 Jen read-only audit — 2026-11-04

Target: `AsterTV-Jen` (`192.168.1.180`) only  
Effect: read-only discovery; no Home Assistant, camera, Kodi or profile mutation

## Findings

- Kodi was active and idle, with no failed systemd units.
- Home window `11112` is a monolithic v2 surface. It combines household
  readings, the only camera viewer and a local timer. There is no separate
  Cameras window.
- The Home adapter reads only
  `/storage/.kodi/userdata/addon_data/skin.asterhome/feeds/home-dashboard.json`.
  The file is a root-owned mode-`0600` schema-4 snapshot with 63 allowlisted
  entities; this audit recorded schema and count, not household values.
- `home_status_model.py` accepts only exact root fields, bounded entity kinds,
  domain-consistent identifiers and typed/ranged values. It marks a snapshot
  stale after 600 seconds, rejects future timestamps beyond ten seconds and
  displays an explicit unavailable state for malformed input.
- The profile registry is active as `jason`/`recovery_admin`, but it has no
  Home Assistant mapping and no Home/camera entitlement. The current profile
  gate therefore denies window `11112`; the old surface and the v3 account
  authority have not been reconciled.
- The camera viewer is already narrow: a localhost-only HTTP process on
  `127.0.0.1:15102`, an exact `Host` check, no origin/proxy headers, 2 MiB JPEG
  limit, four-request bound, five-minute view lifetime and no disk image cache.
  It reaches only the existing forced command `aster-camera-front-v1` using
  Jen's private client key and pinned host key. The systemd unit is hardened,
  starts on demand and is stopped by page leave/expiry handling.
- The current camera action starts from Home and refreshes the same image URL
  every two seconds. Its availability failure is explicit and does not invoke
  a Kodi media player.

## Decision

M6 begins with a Jen-only presentation and authorization separation. Home
status and camera viewing receive distinct read-only entitlements; `home_control`
is not granted. The existing publisher, forced source command, credential,
network path and camera proxy security boundary remain unchanged. Guest denial,
direct-window bypass denial and active-playback non-interruption are graduation
tests rather than assumptions.

Door-event previews remain deferred because no reviewed event adapter, debounce
contract or quiet-hours authority has yet been identified. This slice produces
no speech and does not use the local AI stack.

## Recovery contract

Before installation, checkpoint every touched skin/runtime/profile/manifest
file plus the accepted-release manifest. Install only while Kodi is idle.
Rollback restores the checkpoint byte-for-byte, restarts Kodi and re-runs the
accepted release guard. Any unknown predecessor hash, credential output,
camera exposure beyond loopback or Home Assistant write surface fails closed.
