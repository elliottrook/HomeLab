# M3 NLU v2 confidence-score boundary — 2026-10-26

## Result

A new content-free score producer now translates one exact candidate confidence
run into the rows consumed by confidence-policy v2.

Each input case contains only its opaque identifier, family, decision score,
route score, proposed interpretation dimensions and independently reviewed
expected dimensions. Request text is not accepted. The output records:

- decision and route confidence separately;
- whether the candidate proposes a route;
- exact accepted-decision correctness;
- routed privacy underclassification; and
- unsafe false routing.

The producer preserves the exact candidate, calibration and attempt-journal
digests. It rejects duplicate JSON keys and case identifiers, unknown fields,
request text, malformed semantic dimensions, nonfinite confidence, changed
authority and invalid custody digests.

## Verification

- Confidence producer plus v2 selector tests: **12/12 passed**.
- Complete dependency-free NLU suite: **329/329 passed**.
- `git diff --check`: passed.

## Limit

This boundary derives evaluation metadata only. It neither calls a model nor
accepts a candidate, and it grants no route or tool authority. Before a new
private calibration is justified, a candidate must produce these confidence
rows and pass nested threshold selection across all six already exposed
development sets.
