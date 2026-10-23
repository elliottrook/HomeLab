# D4 journal resume-validation boundary — 2026-10-22

## Finding

The fresh investigation package verified the hash chain when reopening its
private journal, but it did not reapply the current engine-result contract to
stored `finished` events or require exact row and event fields. A correctly
rehashed row produced by faulty local code could therefore carry an unexpected
field across restart even though new results are now rejected before writing.

## Correction

Resume now requires exact outer-row fields and exact `started`, `finished` and
`paused` event shapes. Every stored finished result is revalidated through the
same field, identity, finite-JSON and size boundary used before append. The
session-sequence and hash-chain checks remain in force.

## Verification and limit

Tests rehashed a row with an unexpected outer field and separately rehashed a
finished result containing synthetic private reasoning. Both were rejected on
resume. The complete eval unit suite passed 117/117.

This is defence against malformed private evidence. It does not make the hash
chain a signature, reconcile an uncertain run, call a model or advance M1.
