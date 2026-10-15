# Full-stop Local AI recovery drill

Status: NO-GO for the proposed 03:10 window. This scope is
mutually exclusive with the application-only A1 benchmark. A full-stop drill
always makes A1 NO-GO for that same backup cycle, even if recovery succeeds.

## Fixed installed candidate

The installed disabled full-stop candidate must remain unchanged until this
card is approved. Source pins are:

| Artifact | SHA-256 |
|---|---|
| `lease_recovery_executor.py` | `d75ddfae4ccb3de4bd059aca75d41f4cdac6c60f4951d0ea6ab11a13b9f98e4d` |
| `lease_watchdog_cli.py` (source-only; not installed/executed) | `e79521ae4cfacb61e1232df3b62cdfbb2d5181c0697770b8c1ff6c88c575990d` |
| `trusted_observer.py` | `849ad81a24f3505e808af53b2605005ab195c95416ea0951f75290b04f1b7b99` |
| `lease_controller_candidate.py` (source-only) | `6ee4334c49a351383f8108c3d6a4682d9061aa562da2dd79ec4f9cd8cf1085cf` |
| `local-ai-lease-watchdog.service` | `3041ed62efadcb1bcffe0c66e9c311933fc90c0cb101ea08f24b546fc9bc656d` |
| `local-ai-lease-watchdog.timer` | `9f09de46e3ee55d8f765e1f279d34632ea914c8c6506416f0455853ef538b744` |
| `local-ai-lease-recovery` | `46ddd8a031ecdeb2f227fadb18f5bc76ee9ad6042bf59d7056522c13ffe5b81c` |

The candidate timer is currently disabled and must remain so until the exact
approval immediately before the drill.

## Blocking integration issue

The installed `/usr/local/sbin/local-ai-lease` is still the older manual
`acquire --light` controller, whose `lease.json` schema does not match the
installed watchdog/recovery executor's strict `AdmissionRecord` schema. The
watchdog must not be enabled around that controller. A schema-compatible
source-bound acquisition entrypoint and effect-free integration test are
required first; the older controller must remain available only as the
recorded rollback implementation.

## Measured timing blocker

The fixed source adapter's 300-second `zstd -t` check does not fit the
proposed preflight. On 2026-10-14, the current LXC110 archive was 43.585 GB;
its integrity check was still running at 300 seconds and was terminated. The
104 archive passed in 17.4 seconds and the 116 archive was not reached. Do
not merely increase the timeout into the 04:15 recovery reserve. A future
approval packet must use either an independently retained, source-bound
integrity receipt from the 00:30 backup job or a measured pre-03:00 integrity
scan with freshness and source identity, then recompute the full-stop/A1
window. Until that evidence exists, the drill is NO-GO.

## 2026-10-15 cycle result

The read-only overnight observation confirmed the 00:30 Proxmox backup and
TrueNAS task order: task 1 at 01:00, task 3 at 02:00, and task 2 at 03:00
all reported `SUCCESS`; current-cycle 104/110/116 artifact identities were
present. The Mac A1 source snapshot and post-task-2 destination snapshot also
matched the pinned nine-file, 57,692-byte subset and canonical digest.

This does not clear either drill. The 01:10 low-I/O archive scan completed
104, but the 110 result was unavailable when the observation was interrupted
and 116 was not scanned. No root-owned retained-integrity receipt was created,
so archive integrity is unproven for this cycle. The watchdog remained
disabled/inactive, the lease remained `ready`, and no drill or model call ran.

## Timing and preflight

- 00:30 Proxmox backup, 01:00 guest pull, 02:00 LXC110 mirror, 03:00 Mac
  pull; Proxmox artifacts, archive integrity, TrueNAS task order and the
  LXC110 mirror must have current-cycle success/integrity receipts. The Mac
  point is scheduler/task-2 success only here, not content-transfer proof;
  exact Mac subset proof is an A1-specific gate.
- 03:05–03:10: capture exact Qwen3.5-9B Q4_K_M model, b11429 SYCL/Level Zero
  binary, unit, GPU, authentication, service, schedule and control-plane
  state. Confirm no other lease or active conflicting job.
- 03:10: conditionally acquire the full-stop lease and host lock, persist the receipt, then
  stop only the allowlisted Aster Agent, llama.cpp and Speech services. Do not
  stop or modify the News timer.
- 03:10–03:25: watchdog-enabled recovery fault window. The test may induce
  only the approved bounded recovery condition; no arbitrary host reboot,
  credentials or model prompt is permitted.
- 03:25–03:30: restore services and verify exact runtime/device/auth state,
  four backup points, News at 06:15/17:15, and control-plane health.
- 03:30: hard release cutoff for this drill. If exact restoration is not
  complete by this point, retain the lock and mark the drill FAILED/UNKNOWN.
  03:30–04:15 remains reconciliation only. Any ambiguity retains the lock and
  makes the result FAILED/UNKNOWN rather than READY.

## Bounded effects

The full-stop controller may touch only the three production service units in
LXC104, LXC110 and LXC116. It may not change schedules, News, network policy,
keys, sidecar files, host boot state or unrelated guests. The independent
watchdog must be enabled only for this window and must be disabled again after
the postchecks. It must retain state on any failed or unmatched effect.

## Restoration checks

The accepted model, exact SYCL binary, unit hash, GPU visibility,
authenticated generation, service active state, Proxmox backup schedule,
TrueNAS guest/LXC110/Mac schedule and News timer must all match the preflight
receipt. A service-active result alone is insufficient. The model hash may use
the approved long-running probe timeout; it must not be replaced by a short
timeout.

## Rollback

Disable the candidate timer, preserve the lease lock/journal, restore only
services whose stop intent was observed, and rerun every exact observer check.
Do not replay an uncertain start/stop. If any postcheck fails, leave the lock
and evidence for operator reconciliation and do not run A1 in the same window.

This card does not authorize execution, timer enablement, a host reboot, an A1
benchmark, or a Git push. It requires separate explicit approval immediately
before the 03:10 window. A1 requires a later cycle with its own fresh
source-bound application lease and admission proof.
