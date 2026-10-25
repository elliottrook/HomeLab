# F2 exact-cycle activation result — 2026-10-26

Status: approved one-shot timer activation completed; services were not
manually started. Observation-only cleanup remains the required post-cycle
boundary. F3 remains gated.

## Activated timers

| Unit | SHA-256 | State | Next elapse |
|---|---|---|---|
| `f2-preflight-prepare-20261026.timer` | `e356915e419afa6199afa86bd997231b1d48c2a2e9f46356069d8ee5ce4788fe` | enabled, active, waiting | 2026-10-26 01:15 PDT |
| `f2-preflight-final-20261026.timer` | `fd05327676d3a5dc9383d23ca747b81be7dba1dfb88fe39a2ee535679bc6a8f4` | enabled, active, waiting | 2026-10-26 01:20 PDT |

Both units passed `systemd-analyze verify` and exact-calendar validation. They
are `Persistent=no` with zero randomized delay. Recurring F2 timers remain
disabled/inactive.

## Activation gates and boundaries

Before arming the timers, the October 26 cycle state, cooperative lease/lock,
and trusted receipt were absent. Timer activation did not create a state,
lease, receipt, scan, model call, service stop, retry, or F3 action.

The services were not manually started. Any pre-existing service status was
left unchanged. The observation-only cleanup owner remains the approved Stream
A/Codex heartbeat at 01:42 PDT; it may disable and stop only the spent
October 26 units, preserve historical evidence, and report the result. It
cannot retry, reschedule, acquire a lease, or advance F3.
