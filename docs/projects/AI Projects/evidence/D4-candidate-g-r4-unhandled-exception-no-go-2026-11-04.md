# D4 candidate-g r4 unhandled-exception NO-GO — 2026-11-04

## Decision

Booking `aster-stream-a-sa3-envelope-20261104-1400-r4` is spent and **NO-GO**.
It must not be retried. It produced no retained result and cannot be scored or
sent to blind review.

## Exact transaction

- Ledger was clear for the complete 14:00–15:30 window before reservation.
- Dispatcher claim: exactly 14:00:00, claimant `lh-896e3a1208dec607aac5`.
- Terminal: 14:03:13, after exactly 193 seconds.
- State: `no_go`.
- First failure phase: `owner-transaction`.
- Failure code: `OWNER_TRANSACTION_FAILED_RESTORED`.
- Production restored: `true`.
- Retained owner error: `candidate-g listener exited nonzero: unclassified guest failure`.
- Retained candidate result: absent.

The installed line-oriented host parser therefore received no standalone
bounded guest JSON code. R4 proves that the first correction did not cover this
guest exit path; it does not prove the underlying exception class.

## Independent restoration

- lease exactly `ready`;
- Doctor `healthy`, codes empty;
- no drain/shared lock, port-11436 listener, transient guest scope, or candidate
  process;
- LXC104/110/116 running;
- Aster Agent, accepted 9B/SYCL llama, Speech, News, EPUB, Lab Hours Doctor,
  `pvescheduler`, and `pvestatd` healthy;
- Aster Agent, llama and Speech restart counts remained zero.

Production was not left degraded.

## Deterministic gap and source correction

The guest wrapper serialized only a fixed exception tuple. Another ordinary
`Exception` could escape as a traceback, which contains no standalone JSON code;
the host then correctly failed closed as unclassified and required cleanup
removed the raw guest capture.

Mirrored platform commit `9da52e86ca9a6b09653789f826ebdfde7f1d5447`
adds a final class-only exception boundary. It emits only
`candidate-g guest exception-class:<ClassName>`, validates the class against a
bounded identifier pattern, excludes the exception message and leaves
`BaseException` uncaught. The corrected wrapper is
`626f235bbbecfe74a8f19be547c399881d38568008145a9be75875378fef0abe`.

Focused tests pass 28/28 and the wrapper passes 4/4 under target Python,
including proof that a private `KeyError` message is absent from the retained
code.

## Next gate

Build, review and install a reversible one-file inactive wrapper correction,
then validate exact installed custody and class-only output. Only a new
authoritative conflict-free booking may make one fresh attempt. R4 remains
spent; no automatic retry, model/backend change, restart, blind review, routing
change or promotion follows.
