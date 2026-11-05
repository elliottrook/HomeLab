# AsterTV v3 M5B eBook alignment registration evidence

Date: 2026-11-04

Stream: SA-M5B

State: registered and booked; benchmark execution pending

## Authorized boundary

This milestone retires the unsafe legacy EPUB scheduler, registers one fixed
word-alignment benchmark in the existing Lab Hours full-drain controller and
books one execution window. It does not authorize backlog narration, recurring
bookings, reader/catalogue promotion, deletion of failed evidence, or changes
to AsterTV Family or Bedroom.

## Scheduler correction and recovery

- The enabled host `epub-narration-scheduler.timer` checked the ledger but did
  not create a registered workload booking or acquire the whole-host lease and
  shared operation lock.
- Its timer, service and script were checkpointed at
  `/var/lib/epub-narration/checkpoints/sa-m5b-20261104`.
- The timer is now disabled/inactive. The narration worker and its worker timer
  are inactive/disabled; the read-only `epub-narration-monitor.timer` remains
  enabled and active.
- A pre-existing unregistered resource-ladder service started the old worker
  during validation. It was stopped immediately, the worker was proven
  inactive, and its reservation was deliberately left intact through its
  recovery period rather than falsely releasing capacity.

## Registered workload

- Workload: `astertv-v3-ebook-word-alignment-v1`
- Owner: `astertv-v3-m5`
- Runner kind: `ebook-word-alignment`
- Request count: 1
- Per-request timeout: 600 seconds
- Deadline: 900 seconds
- Minimum booking: 1,800 seconds
- Recovery reserve: 900 seconds
- Maximum retained result: 65,536 bytes
- Guest script:
  `/opt/epub-narration/tools/ebook_word_alignment_benchmark.py`
- Guest script SHA-256:
  `b0197a4566536df599bc772dc50483d78468c5ffa91de4aec6a12a0d37e41127`

The benchmark pins one ready generation for book 81, chapter 0002, the first
ten sentence cues, exactly 1,390,063 samples at 24 kHz, the source prefix and
all input/model/runtime hashes. Model download and network access are denied.
The retained result contains hashes, counts and a pass/rejection code only; it
contains no book text or transcript. A recognizer mismatch is a valid negative
result and cannot promote inferred timing.

Registration checkpoint:
`/var/lib/local-ai-lab/checkpoints/astertv-v3-m5b-registration-20261105T030043Z`

Full-drain baseline reconciliation checkpoint:
`/var/lib/local-ai-lab/checkpoints/astertv-v3-m5b-retired-scheduler-20261105T030549Z`

## Validation

- Nine repository unit tests pass.
- Python compilation passes for all M5B modules.
- Seventy-one retained Lab Hours platform tests pass after reconciling the
  accepted baseline to require the retired scheduler and worker to remain
  inactive.
- Live health reports the retained EPUB monitor healthy.
- The adapter target is absent before execution.
- The local-AI lease reports ready.
- No model ran during installation or validation.

## Authoritative booking

The authoritative ledger reported the complete proposed execution and recovery
window clear before reservation.

- Booking: `astertv-v3-m5b-align-20261104-2215`
- Start: `2026-11-04T22:15:00-07:00`
- End: `2026-11-04T22:45:00-07:00`
- Recovery reserve: 900 seconds
- Current state at evidence capture: `scheduled`

At dispatch the controller must recheck admission and fail closed unless the
booking identity, registered hashes, whole-host lease, shared operation lock,
deadline guardian and restoration gates all pass. SA-M5B remains incomplete
until content-free result and restoration evidence have been retained.
