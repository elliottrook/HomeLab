# D4 candidate-g booked run — 2026-11-03

**TIMED TEST: GO — SCHEDULED / CONDITIONAL.**

The authoritative Lab Hours ledger was checked for the complete execution and
recovery interval. Booking `aster-stream-a-sa3-envelope-20261103-1300` is
scheduled for owner `aster-stream-a` and registered workload
`sa3-evidence-envelope-quality-v1`:

- execution starts `2026-11-03T13:00:00-07:00`;
- execution ends `2026-11-03T14:00:00-07:00`;
- the mandatory recovery reserve extends through
  `2026-11-03T14:15:00-07:00`.

The booking is the sole authority for this transaction. The normal dispatcher
must claim it; no manual start or retry is permitted. Fresh runtime admission
still requires the exact installed hashes, authoritative booking, whole-host
lease, shared operation lock, accepted production baseline and quiet-host
checks. The transaction permits exactly 14 no-retry prose requests for the 20
fixed cases, preserves six deterministic abstentions, grants no tools or
authority, and must restore production before it can report complete.

Reconciliation must accept only the root-custodied terminal result, exact
retained public result, zero remaining candidate/listener/lease/lock state and
healthy Aster Agent, accepted llama/SYCL, Speech and platform daemons. The
booking does not authorize promotion, routing, repair, model/backend changes,
restart or retry.
