# M3 NLU v2 threshold and registration boundary — 2026-10-26

## Result

The accepted confidence-policy v2 now has a separate source-only registration
and threshold-selection path. It does not reinterpret or overwrite the v1
artifacts.

The v2 boundary:

- reconstructs the accepted decision from the exact proposal and acceptance
  artifacts;
- binds one exact sealed candidate and one exact disjoint calibration release;
- counts accepted route, clarify, deny and abstain decisions toward decision
  coverage;
- applies accepted-decision accuracy across every accepted disposition;
- applies privacy underclassification and unsafe false-route gates only to the
  subset that would route;
- selects separate decision and route thresholds;
- freezes the exact score digest without accessing the holdout; and
- retains `authority: not-granted` through registration and selection.

The selector rejects v1 acceptance, changed candidate/calibration identities,
duplicate case identifiers, malformed or nonfinite confidence values,
under-sized family partitions, unsafe routes, routed privacy
underclassification and excessive accepted-decision error.

## Verification

- Focused v2 policy/acceptance/threshold tests: **15/15 passed**.
- Complete dependency-free NLU suite: **324/324 passed**.
- `git diff --check`: passed.

The optional Pydantic-backed benchmark test is outside the system-Python
dependency-free suite and was not needed for this boundary.

## Limit

This is offline evaluation machinery. It does not select a candidate, create a
new calibration corpus, open the sealed holdout, call a model, install a
service or enable automatic routing. The next M3 task is a v2 score producer
that binds real candidate output to these fields, followed by nested exposed-
set evaluation of a materially stronger semantic candidate.
