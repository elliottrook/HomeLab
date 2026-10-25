# M1/D4 fixed Doctor frozen bundle and rollback

**Date:** 2026-10-25  
**Status:** source and target shape frozen; nothing installed, enrolled, started or exposed

## Result

The source-only producer and fixed-caller candidates now have one machine-
validated deployment manifest. It pins 12 files across the Mac mini and LXC104:
four exact replacements and eight additions whose target paths must still be
absent. Every source byte, target path, owner, group, mode, predecessor and
rollback action is explicit.

The manifest is an exact **final target shape**, not permission to copy its
files into those paths. Replacing either Mac script would affect the next
scheduled 08:15 execution even if the LaunchAgent itself were unchanged, and
replacing the running broker's source would create a latent change on its next
restart. The safe staging boundary is therefore an isolated, non-live target-
Linux directory.

The target boundary deliberately excludes LaunchAgent changes, service start
or enablement, broker restart, database enrollment, capability grant, live
read, model route and model call. The broker database must be checkpointed
before the later, separate enrollment change. The two new services must remain
disabled after file staging.

## Measured target state

Read-only checks on the actual targets found:

- the two Mac producer predecessors at the exact manifest hashes;
- the two LXC104 broker predecessors at the exact manifest hashes;
- all eight additive LXC104 targets absent;
- `aster-doctor-caller` and `aster-doctor-client` absent, allowing
  `systemd-sysusers` to allocate collision-free system IDs at a later reviewed
  installation;
- the broker active and enabled under `hlabroker`, with supplementary groups
  `hlabroker-clients aster-lab-broker`;
- the Aster health directory still `root:aster` mode `0750`, aggregate report
  `root:aster` mode `0640`, and the new structured sidecar absent; and
- the existing 08:15 LaunchAgent installed and idle. Its recorded last exit is
  `1`; the bounded error log attributes recent failures to a Mail AppleEvent
  timeout. That pre-existing alert-delivery fault does not block disabled file
  staging, but it must not be mistaken for a successful first live producer
  run.

The proposed Linux shape contains no replacement of the broker unit: the new
broker source has the fixed gateway path as a default. A later activation still
requires a separately reviewed broker restart and postcheck.

## Validation

`validate_fixed_doctor_bundle.py` recomputes all source hashes and rejects
source drift, activation broadening, duplicate/non-absolute targets, a changed
replacement/addition split, unsupported rollback, database-boundary changes or
missing exclusions. Its focused suite passes **3/3**.

Pinned bundle tooling:

| File | SHA-256 |
|---|---|
| `fixed-doctor-bundle-manifest.json` | `2d70860f4b83bd2b5fe214dfebba78fc7eae20f1e20eb5e995af4e8a192ea178` |
| `validate_fixed_doctor_bundle.py` | `bcf63d912d06ff31a04e27ea1ba307a52950e4a2dbb7d7505627db6e15721966` |
| `test_validate_fixed_doctor_bundle.py` | `137f1cefbca2eacc11f4294547cae5c077d3a0f6f8827d0634280825509de428` |

## Next gates

The next operational step is isolated validation only: copy the pinned Linux
sources and units to a fresh root-only staging directory, verify every source
hash, run target-Linux imports plus `systemd-analyze verify`, and remove the
staging directory after retaining content-free results. It must not replace a
live file, create a system identity, reload systemd or touch the Mac producer.
That bounded remote write needs its own approval.

Only after the staged validation passes should an inactive final-path install
card be prepared. That later card must checkpoint the four replacements,
require every predecessor/absence to match, copy the exact files, create the
system identities, and prove both new units remain disabled/inactive. The Mac
producer replacements remain part of their own activation card.

Producer activation, broker restart, caller/gateway activation, AI-PAM database
enrollment, first live fixed read and model-route exposure remain separate
changes. Offline usefulness work can continue independently.
