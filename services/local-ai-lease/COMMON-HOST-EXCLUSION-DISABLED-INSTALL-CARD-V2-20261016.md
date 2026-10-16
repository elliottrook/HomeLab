# Common host exclusion — corrected two-root disabled-install card

**Status: REVIEW CANDIDATE; NOT APPROVED OR INSTALLED.** This replaces the
six-path card after its target-Linux import failure and verified rollback.
The [result](COMMON-HOST-EXCLUSION-DISABLED-INSTALL-RESULT-20261016.md)
records the exact failure. This card requires a **new exact host-change
approval**. It does not authorize an archive scan, trusted receipt, lease,
timer, service stop, model call, schedule change or full-stop/A1 drill.

## Observed topology and frozen bytes

Proxmox has two Python roots. Whole-host helpers are in
`/usr/local/libexec/local-ai-lease/` (`L` below). The application-B60
controller and its existing `application_b60_lease.py` dependency are in
`/usr/local/libexec/aster-a1/` (`A` below); the installed drill wrapper sets
`PYTHONPATH` to `A`. The common `host_exclusion.py` must be installed at the
same SHA in **both** roots so each controller's normal import resolves without
changing a wrapper, environment or `sys.path`.

Source: `codex/aster-lease-compat` checkpoint `a38da489`; recompute all
source hashes immediately before staging. Observed installed bytes below are
preconditions to recheck on Proxmox. Any drift, unexpected path or active
lease/job stops the operation.

| Root/file | New SHA-256 | Observed installed SHA-256 / operation |
|---|---|---|
| L `host_exclusion.py` | `f8c60ad720a8ac1c6c4f3e51c84ce67747b50f25534c02e0ee6ed38efc302563` | absent; add |
| A `host_exclusion.py` | `f8c60ad720a8ac1c6c4f3e51c84ce67747b50f25534c02e0ee6ed38efc302563` | absent; add same bytes |
| L `retained_archive_timing_observer.py` | `f07071d3544fafd0579a4e360674664ec95dd32bd2c4114c3e073c849805e363` | absent; add |
| L `retained_archive_producer_candidate.py` | `7e9b82a0c5216aad99ca1350849abb486a482586548c00ae6d7b6f309a1516c8` | `f3ae1a83f16e5b9c1bca571826029603e4c8d88fc6b529bfe79ffcd465288a3b`; replace |
| L `lease_controller_candidate.py` | `f46509e49227cf7ba78ce662184722192059277202e7315616d12456f0385217` | `e5d328937ea482de4b365e0be1869cabd3cd589eae86a2240b1d72bd5ae47226`; replace |
| L `full_stop_acquire_candidate.py` | `5859aba6cccb8f0eb8a971ccc4e3ff7054c1039482f0838c800ed7a10fc0f791` | `bb0e1a2cc1efa2c904d374a9fc4c5cac5891bf69d63b689e2c130fa84ccd9e3b`; replace |
| A `application_b60_controller.py` | `ac5667add59acd7d3d767b1abebfa11f24315ec4edd9c1e4ddf75a7a366eb4ac` | `3daa4204b1e9515e397680dc51bb2ed96994d2a273e0c2c3ef87f728ce6a41af`; replace |

The existing A `application_b60_lease.py` must remain at
`deaf278c8bc3234f3150f1c3ee696b3cc0cdb55e97c575fec6efb65d6ef9c95d`.
The old manual `/usr/local/sbin/local-ai-lease`, recovery executors, wrappers,
systemd units, runtime manifest and other modules remain byte-identical.
Stage from a tar archive containing **only** the six named source files;
disable macOS AppleDouble metadata and verify member names and hashes before
any installed-file change.

## Bounded staging and Linux proof

1. Recheck both root directories' owner/mode, all seven target paths and
   source hashes, the A dependency, root-owned mode-0700 state directory,
   absence of both lease namespaces, disabled/inactive watchdog and heartbeat
   timers, no active backup/TrueNAS pull or lab lease, and normal production
   service health. Save non-secret baseline hashes and schedule digest.
2. Under the nonblocking advisory lock on the existing state directory,
   preserve exactly the four replacement originals and metadata in a newly
   named root-only mode-0700 checkpoint; verify every copy before mutation.
   Install L and A `host_exclusion.py` first, then the observer, then the four
   replacements. Use root ownership and mode 0644 with atomic same-directory
   replacement. Never change a unit or start a process.
3. With bytecode writing disabled, import the five L modules using
   `PYTHONPATH=L`, then import A `application_b60_lease` and
   `application_b60_controller` using `PYTHONPATH=A`. Confirm the two copies of
   `host_exclusion.py` have the same exact hash. Producer and full-stop CLI
   effect flags must remain false; their disabled entrypoints must perform no
   scan, receipt write or lease action.
4. On a disposable root-owned mode-0700 directory, prove symlink/insecure
   custody rejection, exclusive admission against a second process, and
   release after normal and abnormal exit. With no lease/job active, briefly
   lock/unlock the actual state directory on target Linux. Run only synthetic
   fake-runner controller/observer/producer tests; no real archive or service
   call.
5. Recheck all seven installed hashes, existing A dependency and untouched
   old-controller/recovery/unit hashes; no lease/receipt delta; inactive
   timers; active production services; unchanged backup/News schedules.

## Rollback and later release gates

On any staging, import or postcheck failure, stop. If both lease namespaces
remain absent, atomically restore only the four captured originals and remove
only the three new paths; verify hashes, imports, inactive units and normal
services/schedules. Preserve the checkpoint and failure record. If a lease
state/lock appears, do not swap code beneath it; retain the checkpoint and
require operator reconciliation.

The old manual `acquire --light` route still bypasses the common advisory
lock. Backup and TrueNAS jobs do too. This disabled installation does **not**
make an unattended archive observation safe. A later release must cover the
manual-route conflict, fixed backup/task-1 completion and competing-job/load
checks, a hard outer process deadline ending before the 02:00 pull, target
Linux proof and a separately reviewed producer effect. F2/F3/F6 remain open
until their actual evidence passes.
