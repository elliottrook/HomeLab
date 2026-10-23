# F2 exact-cycle activation result — 2026-10-24

Status: approved one-shot activation completed; observation-only reconciliation
is active for 01:42 PDT. F3 remains blocked pending the measured F2 outcome and
clean postcheck.

## Activated date-specific timers

Platform commit: `92ef17ac`.

Both candidate units passed target-side calendar/custody validation and were
installed and enabled without manually starting either service.

| Unit | SHA-256 | State | Exact elapse |
|---|---|---|---|
| `f2-preflight-prepare-20261024.timer` | `0b13bcd78b6ec1623f35942bcbc9f7ae63a03433223058eac25ce0920df53376` | loaded, active, enabled | 2026-10-24 01:15 PDT |
| `f2-preflight-final-20261024.timer` | `81c7cb6a57c95f946d85348f856852db9839f469acd76ad21a3c15511a666860` | loaded, active, enabled | 2026-10-24 01:20 PDT |

## Safety post-check

- Recurring F2 timers remain disabled/inactive.
- Proxmox and guest postchecks passed.
- The 01:42 PDT observation-only reconciliation heartbeat is active. It may
  disable and stop only the spent October 24 units; it cannot invoke, retry,
  reschedule, acquire a lease, delete historical evidence, or advance F3.
- No service was manually started, and no scan, lease, receipt, or F3 action
  occurred at activation.

At the terminal outcome or 01:40 hard deadline, preserve the new terminal
state and historical October 19–23 evidence. Cleanup must remain observation-only
and no automatic retry is permitted.
