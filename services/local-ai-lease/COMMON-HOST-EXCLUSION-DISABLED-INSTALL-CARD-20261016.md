# Common host exclusion — proposed disabled installation card

**Status: REVIEW CANDIDATE; NOT APPROVED OR INSTALLED.** This card is only for
staging and target-Linux validation of the common exclusion source. It does
not authorize a timer, archive scan, receipt, lease, service stop, model call
or full-stop/A1 drill. The platform owner must reconcile the exact installed
bytes and obtain a separate bounded host-change approval before executing it.

## Target and frozen source

Target: Proxmox only, Python modules under
`/usr/local/libexec/local-ai-lease/`. Source branch:
`codex/aster-lease-compat`, source checkpoint `a38da489`. Recompute these
full-file SHA-256 values immediately before any staging; a mismatch is a stop.

| File | SHA-256 | Expected operation |
|---|---|---|
| `host_exclusion.py` | `f8c60ad720a8ac1c6c4f3e51c84ce67747b50f25534c02e0ee6ed38efc302563` | Add only if absent |
| `retained_archive_timing_observer.py` | `f07071d3544fafd0579a4e360674664ec95dd32bd2c4114c3e073c849805e363` | Add only if absent |
| `retained_archive_producer_candidate.py` | `7e9b82a0c5216aad99ca1350849abb486a482586548c00ae6d7b6f309a1516c8` | Replace only pinned installed candidate |
| `lease_controller_candidate.py` | `f46509e49227cf7ba78ce662184722192059277202e7315616d12456f0385217` | Replace only pinned installed candidate |
| `application_b60_controller.py` | `ac5667add59acd7d3d767b1abebfa11f24315ec4edd9c1e4ddf75a7a366eb4ac` | Replace only pinned installed candidate |
| `full_stop_acquire_candidate.py` | `5859aba6cccb8f0eb8a971ccc4e3ff7054c1039482f0838c800ed7a10fc0f791` | Replace only pinned installed candidate |

No other Python module, unit, binary, script, schedule, LXC, TrueNAS task,
network rule, credential or model is in scope. The four existing destination
bytes must be preserved in a newly named root-only mode-0700 checkpoint
before replacement. The old `/usr/local/sbin/local-ai-lease` manual
controller, recovery executor, watchdog units and runtime manifest remain
byte-identical.

## Preflight and staged change

1. Verify a fresh read-only host status: `/var/lib/local-ai-lab` is a
   non-symlink root-owned directory mode 0700; whole-host and application-B60
   state and lock paths are absent; watchdog, heartbeat and application test
   timers/services are disabled/inactive; no bounded lab lease or backup/pull
   is active. Record only status and hashes, never credentials. If any check
   differs, stop.
2. Capture ownership, mode and SHA-256 for the four replacement targets, old
   manual controller, recovery executor and existing units. Require the two
   add-only paths to be absent. Stop if an unexpected path exists. Preserve
   the four originals and their metadata in the root-only checkpoint.
3. Stage exactly the six hash-pinned source files under a root-only temporary
   directory. Compare source, stage and destination bytes. Install the new
   `host_exclusion.py` before replacing any module that imports it; install
   the observer without an executable bit or unit. Replace only the four
   named modules, root-owned mode 0644. No process is started and no unit is
   enabled or reloaded for this code-only change.

## Target-Linux validation while inactive

- Import the six installed modules with `python3 -B` and
  `PYTHONPATH=/usr/local/libexec/local-ai-lease`, using the installed
  dependency set. Confirm producer and full-stop CLI effect flags are false;
  invoking their disabled entrypoints must report `not-attempted` without
  creating state or calling an archive tool.
- On a disposable root-owned mode-0700 directory, prove the installed
  `host_exclusion` rejects a symlink/insecure directory, rejects a second
  entrant while held, and releases after normal and abnormal process exit.
  Then, only while the production lease namespaces are absent and the host is
  idle, prove a brief lock/unlock on the exact existing
  `/var/lib/local-ai-lab` directory succeeds on target Linux. Record status
  and duration only. Do not scan an archive.
- Run synthetic installed-path controller/observer/producer tests with fake
  runners and temporary state directories. Prove the exclusion remains held
  through producer completion and controller state+lock creation, and that
  both controllers refuse an already held exclusion before any stop command.
- Recheck installed hashes, both effect flags, absence of lease/lock/receipt
  changes, inactive timers/services, exact old manual controller and recovery
  hashes, production service health and unchanged backup/News schedules.

## Release blockers beyond the disabled installation

The installed old manual `acquire --light` controller does **not** take this
common lock. Leave it untouched in this installation, but **do not** schedule
an unattended archive observer or promote a new lease path while that manual
acquisition route can be used in the same window. A later card must either
make the old route participate in the same lock or explicitly and verifiably
disable its acquisition entry for the observation window while preserving an
administrative recovery path.

Backup and TrueNAS jobs also do not participate in the lock. A later live
observation card must pin fixed-source proof of the successful 00:30 Proxmox
job and 01:00 TrueNAS task 1, prove no concurrent backup/pull/maintenance,
define a measured acceptable host-load bound, and preserve the 02:00 pull.
Its whole process must be independently terminated by the earlier of 20
minutes after actual start and 01:40 Vancouver, with a kill/verify path if
the scanner does not stop. A scheduler trigger alone is not a complete
three-archive F2 result. The trusted receipt producer needs a separate F3
effect release and current-cycle custody proof. Watchdog arming, full-stop
acquisition and A1 remain later, separate decisions.

## Abort and rollback

If staging, hash, import, exclusion, disabled-entry or postcheck proof fails,
stop before any live test. While **both** lease namespaces remain absent,
restore only the four captured original modules, remove only the two new
modules, and verify original hashes, target-Linux imports, inactive units and
unchanged service/schedule state. Preserve failure evidence and checkpoint.
If a state or lock unexpectedly appears, do not swap code beneath a possible
lease; retain the checkpoint and require operator reconciliation. Neither a
successful install nor a successful synthetic test marks F2/F3/F6 complete.
