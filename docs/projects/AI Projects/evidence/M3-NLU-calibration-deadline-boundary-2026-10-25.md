# M3 NLU calibration deadline boundary — 2026-10-25

> Result: **PASS — OFFLINE RUNNER CORRECTION ONLY**

## Finding

The sealed calibration runner checked its 1,200-second budget before each
case, but every request still received the full 90-second timeout. A request
started near the outer deadline could therefore overrun the declared wall
budget. A transport failure or deadline exhaustion also produced a partial
owner-only artifact while the command returned exit status zero.

Those behaviours could make a bounded calibration occupy the B60 longer than
the reviewed card allows or let an operator mistake a preserved partial run
for a completed command. The scorer already rejected an incomplete 60-case
artifact, but that downstream rejection was not a substitute for a fail-closed
runner status.

## Correction

Local commit `17a12ae8a9e7e6b8126279a63bb2426b84b7a3f9` changes only the offline
runner and its tests:

- each request timeout is the smaller of 90 seconds and the remaining total
  wall budget;
- no request starts after the total budget is exhausted;
- invalid model output still counts as one completed attempt and remains in
  the denominator; and
- a transport-stopped or deadline-stopped partial artifact is retained but
  the CLI returns exit status `2`.

The deadline-only runner SHA-256 was
`4951ecb6aad8fe96df305cd9cb402445b57db92daab142ad1dcad19d831040f6`.
It is superseded by the durable attempt-journal correction recorded in the run
card; the timeout and nonzero partial-run guarantees remain unchanged.

## Verification

The dependency-free NLU suite passes **100/100**. New regression cases prove
that a request with 50 seconds remaining receives a 50-second timeout, an
exhausted budget starts no request, and a transport-stopped partial run is not
complete. `git diff --check` also passed.

No model request, lease, deployment, holdout access, shadow collection, route,
tool grant or production change occurred. The live calibration remains blocked
until a compatible lease can preserve the accepted local endpoint and the
bounded model-call action is approved.
