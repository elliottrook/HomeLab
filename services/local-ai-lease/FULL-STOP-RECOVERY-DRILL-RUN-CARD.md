# Full-stop Local AI recovery drill

Status: PAUSED / approval-ready for a separate window. This scope is
mutually exclusive with the application-only A1 benchmark; approving this
drill means A1 is NO-GO for the same cycle.

## Fixed installed candidate

The installed disabled full-stop candidate must remain unchanged until this
card is approved. Source pins are:

| Artifact | SHA-256 |
|---|---|
| `lease_recovery_executor.py` | `d75ddfae4ccb3de4bd059aca75d41f4cdac6c60f4951d0ea6ab11a13b9f98e4d` |
| `lease_watchdog_cli.py` | `e79521ae4cfacb61e1232df3b62cdfbb2d5181c0697770b8c1ff6c88c575990d` |
| `trusted_observer.py` | `fdc64fc200b87d0faba64a02762df3197fc49366dd0bec12b491ed83fb1aa93f` |
| `local-ai-lease-watchdog.service` | `3041ed62efadcb1bcffe0c66e9c311933fc90c0cb101ea08f24b546fc9bc656d` |
| `local-ai-lease-watchdog.timer` | `9f09de46e3ee55d8f765e1f279d34632ea914c8c6506416f0455853ef538b744` |
| `local-ai-lease-recovery` | `46ddd8a031ecdeb2f227fadb18f5bc76ee9ad6042bf59d7056522c13ffe5b81c` |

The candidate timer is currently disabled and must remain so until the exact
approval immediately before the drill.

## Timing and preflight

- 00:30 Proxmox backup, 01:00 guest pull, 02:00 LXC110 mirror, 03:00 Mac
  pull; all four must have current-cycle success/integrity receipts.
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
  complete by this point, retain the lock, mark the drill FAILED/UNKNOWN, and
  make A1 NO-GO for the cycle. 03:30–04:15 remains reconciliation only. Any ambiguity retains the lock and
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
before the 03:15 window.
