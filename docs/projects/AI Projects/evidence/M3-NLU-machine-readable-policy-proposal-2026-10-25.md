# M3 NLU machine-readable policy proposal — 2026-10-25

> Status: exact proposal; owner acceptance not recorded

## Result

The initial numeric threshold draft now has a content-free,
machine-validated `aster-nlu-policy-decision.v1` proposal. It records:

- zero privacy-underclassification and unsafe-false-route tolerance;
- maximum selective error `0.10`;
- minimum coverage `0.60`;
- 60 calibration cases, ten in each request family;
- the fixed coverage-maximizing selection rule and higher-threshold tie-breaker;
  and
- literal `authority: not-granted`.

The proposal has canonical decision digest
`2e0def84e095aa39f975d19257f2255d823210dc3aa066af71424203cd964a3d`.
Its status is `proposed` and its acceptance-record field is empty. The validator
rejects vacuous or unsafe values, structural drift, duplicate JSON keys,
authority claims, a proposal that claims acceptance, and an accepted decision
without an exact acceptance-record digest.

## Verification and effect

The focused NLU suite passed **68/68** tests with the bundled workspace Python
runtime on 2026-10-25. This artifact makes the owner decision exact and
reviewable; it does not itself record acceptance, register a threshold policy,
select a candidate, open calibration or enable routing.

After explicit acceptance is recorded separately, a later registration step
must still bind the accepted decision, one sealed candidate and one sealed
calibration release before calibration scoring begins.
