# M1/D4 fixed Doctor frozen bundle and rollback

**Date:** 2026-10-25  
**Status:** source and target shape frozen; nothing installed, enrolled, started or exposed

## Result

The source-only producer and fixed-caller candidates now have one machine-
validated deployment manifest. It pins 12 files across the Mac mini and LXC104:
four exact replacements and eight additions whose target paths must still be
absent. Every source byte, target path, owner, group, mode, predecessor and
rollback action is explicit.

The staging boundary deliberately excludes LaunchAgent changes, service start
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
| `fixed-doctor-bundle-manifest.json` | `8b5da16e1def82cf7569e254986484b7fc7ee43d2a76752fd44cc95140caa624` |
| `validate_fixed_doctor_bundle.py` | `a9f8363fcfddeebff26ef6424343bf0e8f29e264ef4d2a3acddff9f6e444b0e3` |
| `test_validate_fixed_doctor_bundle.py` | `5a33542c26a2df5c5cccfe32ea1eebb865e58f3c83c76c0ec7788efb12ac686a` |

## Next gates

The next operational step is a disabled installation only: checkpoint the four
replaced files, require every observed predecessor/absence to match, copy the
12 exact files, run target-Linux imports plus `systemd-analyze verify`, create
the system identities through the pinned sysusers fragment, and prove both new
units remain disabled/inactive. That change needs its own approval.

Producer activation, broker restart, caller/gateway activation, AI-PAM database
enrollment, first live fixed read and model-route exposure remain separate
changes. Offline usefulness work can continue independently.
