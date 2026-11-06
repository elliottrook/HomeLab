# AsterTV v3 M10 — Bedroom Doctor reconciliation

Date: 2026-11-05

Status: clean sanitized composition observation committed

## Scope and safety

The bounded M10 check read only file hashes, byte counts, modes, Kodi add-on
state, audio settings, Wi-Fi power-save state, one component-manifest hash and
content-free TCP reachability. It did not read credential values, media titles,
household state, camera content or personal service responses.

The first comparison found exactly two declared payload drifts:

- `/storage/.aster-release/release_guard.py` was the older 6,858-byte
  `c00e9d67…b1be` executable rather than the current 7,455-byte
  `fee72859…b2a6` materialized guard;
- `/storage/.aster-v3/m8-remote/apply_room_remote.py` had the correct
  `35ab084c…d6ac0` contents but mode `0644` rather than declared mode `0700`.

Both originals were preserved with metadata at
`/storage/.aster-checkpoints/m10-bedroom-doctor-20261105/`. The guard was
atomically replaced from the hash-pinned materialized source and the helper's
mode alone was corrected. No service or Kodi restart occurred.

## Validation

- all 25 payloads now match declared SHA-256, byte count and mode;
- AC3/E-AC3 passthrough is enabled over the Bedroom stereo contract; DTS,
  DTS-HD and TrueHD passthrough remain disabled;
- Wi-Fi power saving remains off;
- `service.asterremote` and `plugin.video.astersearch` are enabled;
- the Remote client key remains mode `0600` without reading its value;
- the accepted TV-series component manifest remains
  `aa589c89…b2dba0`;
- Aster Remote, Audiobookshelf, Books/narration, Home Assistant, Jellyfin,
  News Digest, Seerr/ARR and YouTube passed content-free reachability from the
  appliance; and
- OPNsense and NetBox availability were checked through their authorized
  control paths. The Bedroom remains correctly unable to reach OPNsense's
  management UI directly.

`composition_guard.py` reports `clean` with no missing, unknown, mismatched or
unavailable entries. Fleet Doctor now reports Bedroom and Jen clean, Family
unobserved, and no drift, invalid or stale observation.

## Rollback

If either correction causes a later fault, restore only the matching `.before`
file from the checkpoint, preserve its recorded mode and rerun the exact
content-free comparison. Do not roll back unrelated Bedroom state or replace
its accepted Kodi manifest.
