# AsterTV v3 M6 Jen candidate — 2026-11-04

Target: `AsterTV-Jen` only  
State: accepted, installed and reboot-stable

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

## Completed live gate

The candidate was installed only while Jen was idle. Home/Cameras navigation,
the active Jason profile, direct-window Guest denial, stale/invalid feed,
camera unavailable behavior, Back/focus, active-playback non-interruption,
rollback/reinstall and reboot all passed.

## Live acceptance to date

- Jen was idle and every predecessor hash matched before installation.
- Checkpoint `/storage/.aster-checkpoints/astertv-v3-m6-jen` covers every
  touched source plus current and previous profile state.
- Jason has only `home_status` and `camera_view`; the Home Assistant mapping is
  an opaque display identity. Guest has no Home mapping or entitlement.
- Home → Cameras, Cameras → Back and direct window navigation passed. Guest
  direct-window attempts were redirected to News; Jason was restored.
- One 79,392-byte JPEG passed through the existing source-restricted viewer.
  Leaving Cameras stopped its systemd service. The first intentionally early
  frame request returned the explicit unavailable path rather than stale art.
- Opening Cameras from Home did not stop or replace a playing local digest
  fixture. The fixture was stopped explicitly after the test.
- A complete rollback restored all predecessor hashes, removed the new window
  and identity, and removed both Jason permissions. This exposed an installer
  resumability defect: the valid checkpoint blocked clean reinstall. The
  installer now verifies and reuses that checkpoint without deleting it; all
  seven M6 tests pass and the identical candidate was reinstalled.
- Full reboot completed at 21:34 MST. The M6 service ran successfully before
  Kodi, Kodi returned active and no failed unit was reported.

## Publisher and reboot closure

The owner approved one bounded Home Assistant restart. Home Assistant returned
HTTP 200 on its configured port 80. The startup publication deliberately held
zero readings while Core populated its registry; the first scheduled refresh
at `2026-11-05T04:56:15Z` published 63 allow-listed readings successfully to
`lab`, `low-spec` and `production`. Jen received the matching schema-4 snapshot
with 63 entities and the same observation time. No configuration, credential,
entity or automation changed.

The post-reboot audit found one inherited privacy defect: the existing camera
service was enabled and remained active even though no Cameras page was open.
An exact-hash, independently reversible correction now makes the M6 boot overlay
disable and stop that service. Checkpoint
`/storage/.aster-checkpoints/astertv-v3-m6-camera-on-demand-r1` preserves the
predecessor file and unit state. Exact rollback restored both enabled/active
state and the predecessor hash; reinstall returned disabled/inactive state.
A second reboot at 21:59 MST left Kodi active, the M6 service successful, the
camera unit disabled/inactive and no failed units. Opening Cameras alone kept
the proxy stopped; selecting Live view started it, and Back stopped it again.

Final regression totals are 8 M6, 30 account, 15 Aster-client and 37 shared v3
tests. Family, Bedroom, Home Assistant controls, camera source/credential/path,
door events and M7 remain unchanged.
