# F2 exact-cycle activation result — 2026-10-25

**Activated:** 2026-10-24 America/Vancouver for the October 25 cycle.
**Platform source:** `3b15f8c6412180bf2340c89e293c2e23f82d9912`.
**Authorization:** Jason explicitly approved this exact activation.

## Installed one-shot units

| Unit | Trigger | Installed SHA-256 | State after activation |
|---|---:|---|---|
| `f2-preflight-prepare-20261025.timer` | 2026-10-25 01:15 PDT | `5902182e3da484cda6f5fc8503127840aaf752adb36e73d3a521571f3e52b5b8` | enabled, active, waiting |
| `f2-preflight-final-20261025.timer` | 2026-10-25 01:20 PDT | `0b6783ab6ae2e8625d48730cd8e5c2858cee9df9e619f62a9e55d77a0d00eeed` | enabled, active, waiting |

Both units are `root:root 0644`, nonpersistent, exact-date timers. Neither
service was manually started. The recurring prepare/final timers remain absent
and inactive.

## Static gates

- Installed diagnostic hashes still match the reviewed `770107df` correction.
- No October 25 terminal state, cooperative lease state/lock or trusted F2
  receipt existed at activation.
- LXC104, LXC110 and LXC116 were running; `pvescheduler` and `pvestatd` were
  active.
- The prior failed final service state is retained as historical evidence and
  does not start the October 25 services early.
- One observation-only reconciliation automation is active for 01:42 PDT under
  id `aster-f2-october-25-reconciliation`.

## Decision

**TIMED TEST: GO — SCHEDULED / CONDITIONAL.** Static activation gates pass.
At runtime, the current 00:30 backup, 01:00 TrueNAS task 1, exact archive
identities, host load, exclusion, lease absence/readiness, quiet-process and
snapshot freshness gates must all pass. Any failed or uncertain gate yields
NO-GO without retry. This activation authorizes no receipt, lease, service
stop, model call, F3 or recurring schedule.
