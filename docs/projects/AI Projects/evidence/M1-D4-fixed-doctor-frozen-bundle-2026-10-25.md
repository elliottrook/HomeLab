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

The import audit also identified three installed dependencies and pins their
observed hashes: `doctor_incident_adapter.py`, `sysadmin_investigation.py` and
`broker_core.py`. The first and third match repository source. The installed
`sysadmin_investigation.py` is an older revision, so it is retained as a pinned
dependency rather than silently replaced. A local mixed-version import check
passed against the exact observed bytes.

## Isolated target-Linux staging result

The first deterministic archive, 17,673 bytes at SHA-256
`793c94d85346c9d7928c6089ed1d014608c6f818d2cbf0bdc280db2978a9671f`,
was validated in a fresh root-only LXC104 staging directory. The transfer hash
matched; every extracted file was `root:root` mode `0600`; the manifest
validator passed; Python 3.13 compilation and imports passed for all candidate
modules using the existing LXC104 dependency paths; and `systemd-analyze
verify` returned zero for both units. The staging directory and transferred
archive were then removed.

No final path, identity, daemon state, service, database, grant, live read,
route, model call, Mac file or F2 state changed. This proves target-Linux source
and unit compatibility; it is not a final-path installation or activation.

## Validation

`validate_fixed_doctor_bundle.py` recomputes all source hashes and rejects
source drift, activation broadening, duplicate/non-absolute targets, a changed
replacement/addition split, unsupported rollback, database-boundary changes or
missing exclusions. It now also rejects missing, changed or duplicate installed
dependency pins. A deterministic archive builder adds the manifest,
validator and all 12 source files to one root-owned, mode-0600 archive with
normalized metadata; it refuses overwrite. The focused suite passes **5/5**.

The focused suite passes **7/7** after the dependency and exact target-path
checks. The current archive at
`/private/tmp/aster-fixed-doctor-v1-staging-v3.tar.gz` is 18,147
bytes with SHA-256
`f57c1cf64f140c3bc64603402f6ea925bb34b559fc63ce41a5b19051f10feb81`.
It contains the same 12 executable/config source files as the target-Linux
validated archive plus the stricter manifest/validator metadata; it is a
transfer candidate, not a deployed artifact.

Pinned bundle tooling:

| File | SHA-256 |
|---|---|
| `fixed-doctor-bundle-manifest.json` | `43a3bfae841467b010cc0df4bef15e5dc90c48eab7847247fa6b3f9860904c49` |
| `validate_fixed_doctor_bundle.py` | `269c6bb9733ad74dbb0a6584f1ac9d7dd22810014fab41142cb6a46e9bcf5964` |
| `test_validate_fixed_doctor_bundle.py` | `ec2c053664bd35d221597480dce582f00dad65f434e76419574f8d085e3e70a8` |
| `build_fixed_doctor_staging_archive.py` | `09e0472027cd789f80cb4c7cc2cf1e2bd8cb63b2ed8b6746cb72dfb0965490bc` |
| `test_build_fixed_doctor_staging_archive.py` | `416a8191ed76c1d6961b681eab9790bd139e8d78579e4ade74fff596ad77e156` |

## Next gates

The isolated staging gate has passed. The next operational step is an inactive
**additive-only** final-path install card for the eight currently absent LXC104
files. That card must require every absence to match, copy the exact files,
create the system identities, run unit verification and prove both new units
remain disabled/inactive. It must not replace either broker or Mac producer
file. The Mac producer replacements remain part of their own activation card;
the two broker source replacements, checkpoint and restart remain part of the
later broker activation card.

Producer activation, broker restart, caller/gateway activation, AI-PAM database
enrollment, first live fixed read and model-route exposure remain separate
changes. Offline usefulness work can continue independently.
