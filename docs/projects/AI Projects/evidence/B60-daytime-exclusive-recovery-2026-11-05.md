# B60 daytime exclusive recovery — 2026-11-05

## Outcome

Booking `b60-exclusive-20261105-day-r1` did not qualify, but its bounded
recovery completed before the restore deadline. The authoritative reservation
is terminal `failed` with `result_code=FAILED_RESTORED`, finish epoch
`1793908345`, owner `b60-stream-a`, claimant
`b60-8183c59f0d69a186bca6`, and entry identity
`3fb57d79aadd1d9ecd98ab30039537acbaf9e442c9b6f2a269ce42d27bb5f9f2`.

The root-custodied session is `released` with `production_restored=true`,
`deadline_missed=false`, `trial_failed=true`, and
`manual_assistance_required=true`. This is recovery evidence, not a successful
candidate result and not authority to retry the spent booking.

## Failure and recovery analysis

The booked owner stopped while the session was restoring. Its guardian then
failed with `UNIT_FAILURE_UNCLASSIFIED`, leaving the exact reservation-bound
lease and operation locks retained and the News timers inactive.

The installed recovery command first failed before effects with
`OWNER_SCOPE_NOT_FENCED`: its fence path treated the already absent owner unit
as a stop failure even though the unit had no PID or tasks. A bounded transient
no-op owner scope established the missing fence. The next recovery attempt
exposed a second deterministic mismatch: the timer resume helper accepts only
persistent calendar timers, while the captured active
`paperless-summary.timer` is a non-persistent monotonic timer. It therefore
aborted before timer rearming.

A separately launched root-custodied assisted recovery already held the
session lock when a prepared one-shot helper attempted entry. The second path
failed safely on that lock and did not race or mutate the session. The lock
owner completed restoration, verified the production boundary, released both
locks, and closed the reservation as `FAILED_RESTORED`.

Two source corrections are required before this transaction family can be
considered unattended:

1. owner-scope fencing must accept a provably absent/not-found unit with zero
   PID and tasks as fenced; and
2. timer restoration must have an explicit reviewed policy for active
   non-persistent monotonic timers, starting the schedule from recovery rather
   than replaying a missed event.

Neither defect justifies retrying this booking.

## Independent postcheck

- The reservation-bound lease lock and shared operation lock are absent.
- The temporary `/run/b60-exclusive-20261105-day-r1-recover.py` helper is
  absent, and its failed transient unit is inactive.
- LXC 104, 110, 114, 115 and 116 are running.
- Aster Agent, accepted `aster-llama.service`, and Aster Speech are active with
  zero recorded restarts.
- `news-aggregator-ingest.timer` and `news-aggregator-digest.timer` are active
  and enabled in LXC 114.
- `paperless-summary.timer` is active and enabled in LXC 115.
- The registered EPUB baseline remains intact: the guest monitor timer is
  active/enabled and its worker's last result is success. The legacy host
  scheduler remains disabled as required by the reconciled production policy.
- `pvescheduler` and `pvestatd` are active.
- No owner, guardian, recovery, candidate, lease or operation-lock process
  remains.

No TTS file, workload registration, reservation or booking was changed. The
stack is released for the next independently admitted workload; the failed
qualification cannot be counted as a pass.
