# D4 engine-result finite-JSON boundary — 2026-10-22

## Finding

The fresh investigation package bounded an injected engine result and rejected
unexpected fields before writing it to the private journal, but Python's
default JSON encoder still accepts non-finite numbers such as `NaN` and
infinity. Such a result is not portable JSON and could leave future scoring or
review code interpreting the same evidence differently.

## Correction

The package now encodes the validated result with `allow_nan=False` before its
size check. A non-finite or otherwise non-JSON result is rejected before the
`finished` event is written. The earlier durable `started` event remains, so
the session is visibly uncertain and cannot be replayed automatically.

## Verification and limit

A synthetic engine returned `NaN` as elapsed time. The package rejected it,
the journal contained no `NaN`, and a second run refused replay because the
started session was unresolved. The complete eval unit suite passed 114/114.

This strengthens future private benchmark evidence only. It does not call or
qualify a model, connect a live tool, grant authority, or advance M1.
