# SA3 Candidate-J R3 EPUB policy reconciliation — 2026-11-05

## Decision

The R3 transaction is complete and restored. Its retained 6/6 public result is
eligible for a distinct untouched evaluation freeze. The earlier external
postcheck NO-GO used the superseded host-scheduled EPUB predicate and is not a
reason to repeat the spent transaction.

## Installed-policy evidence

Before R3, the installed Lab Hours release had adopted the registered-workload
EPUB baseline. Its pinned `full_inference_lab_sources.py` requires:

- legacy host `epub-narration-scheduler.timer` disabled/inactive;
- guest `epub-narration-monitor.timer` enabled/active;
- retired guest worker timer disabled/inactive; and
- guest worker inactive with last result `success` between booked workloads.

The authoritative Doctor returned healthy with no codes at 04:11:46,
04:16:36 and 04:22:11 PST. These observations bracket the 04:15:00–04:18:44
R3 transaction. The ledger and root terminal are complete, production is
restored, and the retained result independently scores 6/6.

## Bounded recovery-check rollback

At 07:09 a check against the older EPUB project branch temporarily enabled the
legacy scheduler after an authoritative clear-window query and exact file-pin
comparison. The current Doctor rejected that obsolete architecture. The timer
was disabled again and only the admitted EPUB worker was stopped. Final state
matches the installed policy: scheduler disabled/inactive, worker
inactive/success, lease ready, no shared state or locks, and Doctor healthy
with no codes. The rollback changed no model, backend, route or core production
service.

## Next boundary

Keep the legacy scheduler retired. Any EPUB work requiring exclusive local-AI
use must use a registered, hash-pinned workload and authoritative booking.
Candidate-J may proceed only to an offline untouched-evaluation freeze; later
execution remains separately booked and fail closed.
