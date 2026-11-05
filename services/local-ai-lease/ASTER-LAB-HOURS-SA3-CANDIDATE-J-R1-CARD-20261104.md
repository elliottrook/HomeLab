# Aster Lab Hours SA3 candidate-j R1 card — 2026-11-04

## Exact reservation

- Booking: `aster-stream-a-sa3-candidate-j-20261104-2100-r1`
- Owner/workload: `aster-stream-a` /
  `sa3-evidence-matrix-candidate-j-public-v1`
- Window: 2026-11-04 21:00–21:45 host-local offset `-07:00`
- Epochs: start `1793851200`, end `1793853900`
- Recovery reserve: 900 seconds

The authoritative ledger rejected 19:30 and 20:15 proposals because EPUB
narration booking `epub-ladder-20261104-2000` owns 20:00–20:45 plus recovery
through 21:00. The complete 21:00–21:45 window returned `clear` before this
exact registered booking was saved as `scheduled`. EPUB is not cancelled,
shortened or overlapped.

## Static GO evidence

Candidate-j's inactive install passed at platform evidence commit `f0b73045`:
39 release pins match, the five-file self-contained runtime and wrapper match
inside LXC110, rollback checkpoints are retained, and no candidate unit,
process, scope, lease state or operation lock remains. LXC104/110/114/116,
Aster Agent, accepted 9B/SYCL llama, Speech, News timers, pvescheduler and
pvestatd passed independent postchecks. Dispatcher and Doctor timers are active
and enabled; the dispatcher last result is success and fires each minute.

## Runtime and terminal boundary

At claim, the dispatcher must freshly recheck the exact reservation, installed
pins, ready lease, shared lock, quiet host, production health, exact start and
recovery allowance. It may make exactly two accepted-model requests across six
public cases; four abstention cases must never reach transport. Accept success
only for six valid rows, zero retries/errors/effects, canonical retained digest,
exit zero, `production_restored=true`, absent candidate state/scope/locks and
healthy production postchecks.

Any changed, missing, late, conflicting or uncertain gate is terminal NO-GO
without retry. This booking authorizes only candidate-j R1. It does not
authorize a model/backend change, restart, retry, route, tool grant, repair
authority, untouched quality packet or automatic promotion.
