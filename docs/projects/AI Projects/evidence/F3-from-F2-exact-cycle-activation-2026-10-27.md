# F3 from F2 exact-cycle activation — 2026-10-27

## Decision

**APPROVED AND SCHEDULED / CONDITIONAL.**

Jason approved the single October 27 F3 conversion after reviewing the exact
action, deadline, effects and exclusions. The heartbeat
`aster-f3-october-27-exact-cycle-conversion` is active for 01:50
America/Vancouver with `FREQ=DAILY;COUNT=1;BYHOUR=1;BYMINUTE=50`.

## Bound source

- platform card commit: `35b5f61d80fdc65a3cde17751eedcfe94ac6093b`;
- Stream A independent review commit: `8fae86f8`;
- prerequisite observation: the separately active 01:42 October 27 F2
  reconciliation.

## Runtime gate

The conversion may run exactly once only if the 01:42 reconciliation accepts
exactly three independently validated exit-zero archive rows and all production
postchecks pass. It must also recheck installed hashes and custody, absent
receipt, root-only receipt parent, ready lease with no locks, no competing work,
and healthy guests, services, daemons and schedules. Any missing, stale, failed
or uncertain condition is terminal NO-GO without invocation or retry.

A successful invocation may write only the root-owned mode-0600 retained
integrity receipt and must independently verify it against unchanged F2 bytes.
This approval grants no F4, lease, service stop, model call, candidate-H/M3
workload, retry, reschedule, Git push or promotion.
