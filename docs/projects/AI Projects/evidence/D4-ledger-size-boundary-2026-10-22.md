# D4 private-ledger size boundary — 2026-10-22

## Finding

The fresh investigation package locks and validates its owner-only,
hash-chained journal before resuming, but it previously read an existing file
without first bounding its size. The fixed forty-session run and per-result
limit bound legitimate evidence well below four MiB; an altered or misplaced
large file at the ledger path could otherwise consume unbounded memory before
integrity validation.

## Correction

After locking the open file and checking owner-only custody, the package now
uses the open descriptor's size and rejects a ledger larger than four MiB
before reading or parsing it. The check is on the descriptor, so a path change
cannot substitute another file between the custody and size decisions.

## Verification and limit

A synthetic owner-only ledger one byte over the limit was rejected before
parsing. The complete eval unit suite passed 115/115.

This protects the offline evaluation evidence boundary. It does not call a
model, alter an existing journal, authorize reconciliation, or advance M1.
