# D4 engine-status vocabulary boundary — 2026-10-23

## Finding and correction

The fresh private journal required a nonempty engine status but did not restrict
that value to the investigation engine's terminal vocabulary. A faulty injected
engine could therefore persist an invented status and have the package count
the session as completed.

Engine-result validation now accepts only the engine's defined terminal states
or a bounded `transport_error:<ExceptionClass>` value. The exception class must
be an identifier no longer than 128 characters. Unknown, whitespace-bearing and
oversized statuses are rejected before the finished event is journalled; the
durable started marker continues to make the uncertain attempt non-replayable.

## Verification and limit

Synthetic invented, malformed transport-error and oversized transport-error
statuses were rejected and absent from the journal. The complete evaluation
unit suite passed 121/121.

This protects offline evidence semantics. It does not execute the private
holdout, call a model, qualify an investigation, connect a tool or grant
authority.
