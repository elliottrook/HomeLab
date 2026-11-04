# D4 candidate-g booking v2 result — 2026-11-04

## Decision

**TIMED TEST: GO — SCHEDULED / CONDITIONAL.**

Booking `aster-stream-a-sa3-envelope-20261104-1230` is recorded as scheduled
for 12:30–14:00 host-local. The authoritative ledger was clear, the lease was
ready, shared state/locks were absent and the installed reserved-runner
verified all 34 release pins immediately before reservation.

Jason's standing Stream A candidate authorization covers this in-scope run and
its fixed stop/restoration transaction. Runtime remains fail closed and permits
one attempt with no retry or extension. No production model change, deployment,
routing promotion or tool authority is included.
