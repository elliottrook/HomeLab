# AsterTV v3 M10 automated closure and M11 repository freeze — 2026-11-06

## Outcome

The autonomous M10 work is complete. The remaining walkthrough and room
observations are explicitly owner-assisted acceptance, not missing automated
implementation.

The integrated gate passed 72 test files, a 93-file secret-pattern scan and
15 pages with 127 focus controls and zero conformance failures. The connected
Jen HEVC result, gateway environment, operations/recovery audit and measured
performance envelope all report `pass`. Doctor, Beszel, NetBox, wiki,
reference and derived-mirror readiness have zero gaps.

The evidence set collectively proves the originally open low-spec cases:

- functional playback and navigation across Movies, Archive Movies, TV,
  Archive TV, Music, Audiobooks, News, Home, Requests, Cameras and the Aster
  screensaver;
- Jason/Guest account isolation, direct-route denial, restart persistence and
  separately scoped Guest catalogue playback;
- wrong-key, wrong-role, malformed-state, stale-state, dependency-outage and
  unavailable-dependency failure paths;
- real H.264, HEVC, audio, News and Music playback plus the accepted Jen-only
  1080p/stereo ceiling;
- two full Jen reboots, accepted-release guard drift recovery, exact
  rollback/reinstall exercises for accounts, Guest, Home/cameras and Remote;
  and
- isolated corrupt-package, interrupted-install and accepted-state restore
  rehearsals for Bedroom and Family.

A new content-free disposable-root rehearsal then seeded the complete immutable
v2 add-on snapshot, installed Jen's complete frozen composition and invoked the
real composition runner's rollback. It restored all v2 add-on bytes, removed
v3-only targets and restored both accepted-state directories: 577 v2 files,
127 composition paths and two accepted-state directories, with tree digest
`d8560284…17ed`. This closes the
named full-v2 rollback gate without moving the live canary. The v2.0.7 archive
and target checkpoints remain the independent recovery authority; v3 overlays
continue to run after the v2 guard rather than replacing the accepted baseline.

## Repository freeze

The repository-side release candidate is frozen as
`astertv-v3-rc1-2026-11-06` at source commit
`762628afac45ece9646cffb3a1a346840ca42892`. It composes the immutable
v2.0.7 artifact (`e813de8a…3cf7`) with exact per-device payloads and guards.

Two deterministic real-artifact builds produced identical bundle hashes:

| Device | Composition | Bundle | State |
| --- | --- | --- | --- |
| Bedroom | `9be4b045…8e829` | `0f3817aa…42164` | owner soak required |
| Family | `8341abe7…2f1b` | `5ed4768a…0e6e6` | Bedroom acceptance and explicit promotion required |
| Jen | `8fb73ef4…b5601` | `d6032f21…5fc40` | standing canary |
| Guest | `5ca63262…339e` | `4d79b20a…201e0` | candidate, deliberately non-deployable |

The freeze manifest is
`services/kodi/astertv-fleet/releases/astertv-v3-rc1-2026-11-06.json`.
The release-pipeline test rebuilds the real bundles and fails if any frozen
composition or bundle digest changes.

## Deliberately open boundaries

Automation cannot mark these complete:

1. physical remote key-code capture and room-equipment observation;
2. owner-selected content-class volume targets;
3. the non-author physical walkthrough, Bedroom soak and explicit Family
   promotion; and
4. the external unified Media Lifecycle replacement-view artifact/identity
   handoff.

Until item 4 arrives, the release preserves the four exact v2 smart-playlist
fallbacks. No unapproved v3 `.xsp` is shipped.
