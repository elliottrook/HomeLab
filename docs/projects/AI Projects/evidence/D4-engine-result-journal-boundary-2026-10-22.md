# D4 engine-result journal boundary — 2026-10-22

## Finding

The fresh investigation package wrote the injected engine's result directly to
its hash-chained journal. The normal investigation engine returns a bounded,
sanitized result, but the package boundary did not independently reject an
unexpected raw field or an oversized result. A faulty replacement engine could
therefore persist private reasoning or unbounded output before scoring.

## Correction

Before a `finished` event is appended, the package now requires a result record
with the registered case and mode, a non-empty status, a list of steps, only
the bounded investigation result fields, and a maximum canonical size of
65,536 bytes. The accepted result is deep-copied before journalling. Invalid
results leave only the prior `started` marker, so later execution fails closed
as an uncertain session instead of replaying it.

## Verification and limit

Tests inject a synthetic private-reasoning field and a 70,000-character result.
Neither value reaches the journal, both attempts require manual reconciliation,
and replay is refused. The complete eval unit suite passed 113/113.

This protects future private benchmark evidence. It does not call or qualify a
model, authenticate a producer, connect a live tool, grant authority or advance
M1.
