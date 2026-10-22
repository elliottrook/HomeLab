# F2 exact-cycle activation result — 2026-10-22

Status: approved one-shot activation completed; observation-only post-run
cleanup is scheduled for 01:42 PDT. F3 remains blocked pending the measured
F2 outcome and clean postcheck.

## Activated date-specific timers

Target-side `systemd-analyze verify` and exact-calendar validation passed before
activation. Both units are nonpersistent, have zero randomized delay, and were
enabled without manually starting either service.

| Unit | SHA-256 | State at activation | Exact elapse |
|---|---|---|---|
| `f2-preflight-prepare-20261022.timer` | `8abd7ddb82fbedb38d72c10957998b6f533f09155dc4fa6e2fd56a0fc605f9a0` | loaded, active, enabled | 2026-10-22 01:15 PDT |
| `f2-preflight-final-20261022.timer` | `ef38ebc9d2fe761498813ab8c2c1182c3283eb7ba46f23577f78fb287bf1ee6d` | loaded, active, enabled | 2026-10-22 01:20 PDT |

## Activation post-check

- Recurring F2 timers remain disabled/inactive.
- No 2026-10-22 terminal state, preflight snapshot, lease, lock, or receipt
  existed at activation.
- Neither F2 service was manually started.
- The one-time observation-only 01:42 heartbeat is active. It may disable and
  remove only the spent 2026-10-22 units after the cycle; it cannot retry,
  reschedule, launch F2, acquire a lease, or advance F3.
- No backup schedule, production service, model endpoint, or historical state
  was changed.

At the 01:40 hard deadline or terminal outcome, the two date-specific units
must be disabled/stopped and reconciled observation-only. Preserve the terminal
state and do not retry automatically. F3/F4 remain separately gated on a
successful F2 result and clean postcheck.
