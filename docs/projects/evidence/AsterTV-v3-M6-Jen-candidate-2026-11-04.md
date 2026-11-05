# AsterTV v3 M6 Jen candidate — 2026-11-04

Target: `AsterTV-Jen` only  
State: locally complete; not yet installed

## Candidate

- Home remains window `11112` and continues to consume only the exact schema-4
  local snapshot. Its existing ten-minute freshness failure and explicit
  invalid/unavailable states are unchanged.
- The Home camera actions now route to separate window `11134`; Home no longer
  starts, refreshes or stops the camera process.
- Cameras owns the existing on-demand viewer lifecycle. The proxy, source key,
  forced command, network path, five-minute expiry, two-second refresh, 2 MiB
  image cap and no-disk-cache behavior are unchanged.
- A root-owned, credential-free display identity marker binds the profile
  mapping to the existing `ha-home-dashboard-v4` publisher contract.
- `home_status` and `camera_view` are separate entitlements. Jason receives only
  those two read-only permissions. Guest receives neither; legacy
  `home_control` and `cameras` are rejected if present on the migrated profile.
- Voice `open cameras` routes to window `11134`, but no Home Assistant action,
  service call or equipment control is introduced.
- Installation is hostname-, root-, idle- and predecessor-hash-bound. It
  checkpoints every touched source and both current/previous profile state,
  installs after M5P and before Kodi, and has a byte-exact rollback path.

## Tests

- 7 M6 overlay/authority/installer tests passed.
- 30 account registry, authority, migration and Guest tests passed.
- 15 AsterTV client/installer tests passed.
- 37 shared page-language, Movie/TV/trailer and package regressions passed.
- Python compile and XML parse checks passed with a sandbox-local bytecode
  cache; no credential-like assignment is part of the candidate.

## Remaining live gate

Checkpoint and install only while Jen is idle. Validate Home and Cameras with
the active Jason profile, direct-window Guest denial, stale/invalid feed,
camera unavailable/expiry, Back/focus, active-playback non-interruption,
restart and reboot. Then prove rollback and reinstall the identical accepted
candidate before closing the slice.
