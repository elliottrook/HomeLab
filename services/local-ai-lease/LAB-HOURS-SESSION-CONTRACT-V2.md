# B60 Lab Hours Session Contract V2

Date: 2026-11-06

## Intent

A valid B60 Lab Hours booking is a temporary grant of the shared lab, not a
single-use execution token. The booking owner retains the booked interval
after a successful attempt or a failed attempt that has restored production.
This permits bounded diagnosis and retry without allowing arbitrary commands
or weakening the lease, shared-lock, pin, recovery, or ledger controls.

## Session attempts

- A retryable workload explicitly declares `retryable_session`, a bounded
  per-attempt deadline and a time-budgeted retry policy in the root-installed
  workload registry. A count ceiling is optional rather than the primary bound.
- Every attempt uses the booking's registered workload and current hash pins.
- An attempt has its own deadline, evidence directory, terminal receipt, and
  production-restoration result.
- A failed attempt is retryable only when production restoration is proven,
  any optional count ceiling permits it, and its complete bounded deadline fits
  before the booking end.
- Retry dispatch is explicit and evidence-driven. The admitted owner may
  diagnose, repin and retry autonomously within the approved booking envelope;
  there is no blind automatic retry and no command supplied by the record.
- An unrestored failure is terminal and cannot be retried.
- An idle retryable session remains `claimed` until early release or booked
  end, so the ledger continues to exclude other B60 work.
- Restoration replay evidence is lease-scoped. A restore command observed for
  an older lease may never satisfy or suppress the current lease's command.
- Retry admission includes any fixed runner setup lead in addition to the
  attempt deadline; the complete setup plus attempt must fit before booked end.

## Independent pre-run evaluation

Every V2 retryable session requires an independent read-only evaluation after
the final controller/registry activation and booking, and before its first
attempt. The evaluator must inspect the exact booking, release manifest,
registered attempt limits, dispatcher path, lease/locks, runtime prerequisites,
recovery path, and evidence boundaries. It must not claim the booking,
initialize the backend, or mutate B60.

The evaluation records concrete blockers and a `WILL RUN`, `LIKELY RUN`, or
`WILL NOT RUN` verdict. `WILL NOT RUN` blocks execution until correction and
re-evaluation. `LIKELY RUN` is acceptable only for irreducible first-use
behavior that remains bounded by the session deadline and recovery controls.

## Early release

The root administrative CLI provides `release`:

- An unclaimed scheduled booking can be surrendered immediately.
- A claimed session can be surrendered only when no attempt is running and the
  most recent attempt proves production restored.
- A release after use retains the recovery buffer in the ledger.
- A successful released session closes complete; a failed-restored released
  session closes failed, preserving its actual outcome.

## Moving a waiting booking forward

A booking may opt in to earlier execution with `--promotable`. The dispatcher
may move one opted-in booking forward when a complete window opens. Promotion:

- preserves the booking's requested duration;
- records the original start and end;
- starts no earlier than the recovery boundary;
- rechecks every active and recently completed ledger record; and
- leaves a booking at its original time if the entire promoted window cannot
  fit safely.

Promotion is an admission-time change only. It does not change the registered
owner, workload, pins, attempt budget, lease, shared operation lock, or runtime
restoration requirements.

## MuseTalk XPU pilot profile

The initial Aster news-video XPU session is a 90-minute booking with a
15-minute recovery reserve. Attempts are individually bounded to 20 minutes;
the number is governed by remaining booked time and proven restoration, not an
arbitrary three-try limit. The owner may review, hash-pin and activate bounded
corrections, then explicitly retry or release during the still-claimed session
without repeated conversational approval.
