# F2 exact-cycle activation result — 2026-10-28

Status: **PASS — ONE-SHOT TIMERS ACTIVE; RUNTIME GATES REMAIN CONDITIONAL**

Jason authorized a same-day mitigation, real daytime archive scan and the
stable candidate's test against the October 28 fresh backup cycle.

Before activation, the installed corrected baseline matched the exact hashes
in the refreshed card. The target packet passed 63/63 tests and the installed
no-scan rehearsal completed across all three current archives. The new cycle
state, lease, locks and retained receipt were absent.

The following exact root-owned mode `0644` timer files were installed and
enabled:

| Unit | SHA-256 | Next elapse |
|---|---|---|
| `f2-preflight-prepare-20261028.timer` | `69d0e4d2cafed2c1567009cfa87d1146c17440a7de8ac21dce76eaffa843` | 2026-10-28 01:15 PDT |
| `f2-preflight-final-20261028.timer` | `b71e87d036ad70da437dba1c897b5b0f520ee4dff814af7f998522243ecd5545` | 2026-10-28 01:20 PDT |

Both units are enabled, active and waiting. The recurring prepare/final timers
remain disabled/inactive. No service was manually started, and no lease,
receipt or new-cycle state was created during activation. LXC104/110/116 are
running and `pvescheduler`/`pvestatd` are active.

The same chat has one one-occurrence observation/cleanup heartbeat for 01:42
PDT. Runtime backup, task-1, identity, load and quiet-host checks remain fresh
and fail closed. This activation authorizes no retry, F3 receipt, lease,
service stop, restart or model call.
