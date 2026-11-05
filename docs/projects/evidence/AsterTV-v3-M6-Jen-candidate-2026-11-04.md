# AsterTV v3 M6 Jen candidate — 2026-11-04

Target: `AsterTV-Jen` only  
State: installed and reboot-stable; Home publisher runtime reload pending

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

## Current authorization boundary

Home correctly displays its stale state. The source-local Home Assistant health
record shows a new 63-reading publication, but its running module delivered
only to the two older targets. The on-disk publisher is already the reviewed
three-target version and contains Jen exactly once. It was patched previously
without restarting Home Assistant, so the long-running process retained the
old module after subsequent publications.

Completing the fresh-data gate needs one bounded Home Assistant restart to load
the already-installed publisher, followed by a content-free three-target health
check and fresh Jen snapshot test. No configuration, credential, entity or
automation change is proposed. That Home Assistant restart is outside the
current Jen-only mutation list and therefore requires explicit authorization.
