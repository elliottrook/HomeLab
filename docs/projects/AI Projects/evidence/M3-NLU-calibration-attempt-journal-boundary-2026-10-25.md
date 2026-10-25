# M3 NLU calibration attempt-journal boundary — 2026-10-25

> Result: **PASS — OFFLINE EVIDENCE-CUSTODY CORRECTION ONLY**

## Finding

The calibration runner previously created its owner-only result only after the
entire model loop returned. An interruption during a request or a late output
creation failure could therefore lose all completed rows and make the active
case unknowable. Repeating that run would risk replaying an uncertain request;
abandoning it would leave no durable explanation. This is the same class of
custody problem that invalidated the first A1 answer holdout attempt.

## Correction

Local commit `b5b235742ad120f9e40c795ab4352061da2218bb` adds a separate owner-only
content-free attempt journal and pre-request output reservation:

- output and journal paths are distinct, mode `0600`, no-follow and
  create-exclusive;
- both paths are reserved before the first model request, so a late existing-
  file failure cannot discard completed work;
- `attempt_started` is flushed and `fsync`ed before each request;
- `attempt_recorded` is flushed and `fsync`ed before another request starts;
- the journal stores only opaque case IDs, validity and allowlisted error type,
  never request text, response text or credentials;
- a journal failure stops through a dedicated evidence exception before any
  later request; and
- the final content-free run atomically replaces the reserved output and
  synchronizes its directory.

A started row without a matching recorded row is an uncertain model attempt.
It forbids replay under this card. The corrected runner SHA-256 is
`484a09d4d1655336808767ead76d7803f6eadf783bbda5bdf1eaec8726389833`.

## Verification

The dependency-free NLU suite passes **104/104**. New tests prove content-free
attempt boundaries, stop-before-request on a journal failure, atomic mode-0600
sealing, and cleanup of a partial pre-inference path reservation. The earlier
deadline and incomplete-run regressions remain covered.

No model request, lease, deployment, holdout access, shadow collection, route,
tool grant or production change occurred. This closes an evidence-custody gap;
it does not lift the compatible-lease or model-call gates.
