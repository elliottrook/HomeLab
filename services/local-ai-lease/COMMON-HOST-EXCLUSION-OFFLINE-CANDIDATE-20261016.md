# Common host exclusion — offline candidate

**State:** source-only; uninstalled and unexecuted on Proxmox. No timer,
backup, archive, receipt, lease or service was changed.

The prior cross-lease checks were pre-start observations. A lease could still
start between an archive scanner's check and its first `zstd` invocation. This
candidate uses a nonblocking advisory `flock` on the existing
`/var/lib/local-ai-lab` directory. It creates no lock file and accepts only a
non-symlink directory owned by the executing identity with mode 0700. Failure
to acquire the lock fails closed.

- The read-only timing observer holds the lock through the entire fixed-source
  scan. The retained producer holds it through the scan and receipt write.
- The full-stop and application-B60 candidate controllers each acquire the
  same lock, recheck both lease namespaces while holding it, then create their
  own durable state and lock before releasing it. Subsequent scanners see
  that state and refuse to start.
- The full-stop CLI also makes an early cross-lease check, but the check inside
  its controller is authoritative for this source candidate.

Synthetic tests prove a second entrant fails while the directory lock is
held, both lease controllers refuse before issuing stop commands, and both
scanner entrypoints hold the exclusion through their producer call. The full
`scripts/local-ai` suite passed **188 tests, two macOS root-custody skips**.
No live archive or host service was contacted.
The application lease directory is also checked for owner, mode 0700 and
non-symlink directory type before state is written.

| Source file | SHA-256 |
|---|---|
| `host_exclusion.py` | `f8c60ad720a8ac1c6c4f3e51c84ce67747b50f25534c02e0ee6ed38efc302563` |
| `retained_archive_timing_observer.py` | `f07071d3544fafd0579a4e360674664ec95dd32bd2c4114c3e073c849805e363` |
| `retained_archive_producer_candidate.py` | `7e9b82a0c5216aad99ca1350849abb486a482586548c00ae6d7b6f309a1516c8` |
| `lease_controller_candidate.py` | `f46509e49227cf7ba78ce662184722192059277202e7315616d12456f0385217` |
| `application_b60_controller.py` | `ac5667add59acd7d3d767b1abebfa11f24315ec4edd9c1e4ddf75a7a366eb4ac` |

**Release blockers:** advisory locking works only when every permitted
entrypoint participates. The installed old manual `acquire --light` controller
does **not** take this lock; it must be disabled for the observation window or
upgraded under a separately reviewed card before unattended use. Root can
also bypass advisory locking, so the operator run card must prohibit manual
effects during the bounded scan. Backup and TrueNAS jobs do not take this
lock: a host release needs deterministic competing-job/load checks and a
non-overlapping schedule. Prove `flock` on this exact directory and the
installed Python imports on target Linux, hold/release behavior under process
death, bounded outer process termination, module hashes, rollback and
watchdog behavior before installing or enabling anything.

This candidate alone is not F2 timing evidence, an F3 trusted receipt, F6
independent recovery, A1 admission, or permission for a live drill.
