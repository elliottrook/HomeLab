# M3 NLU narrow recognizer v1 cross-set rejection — 2026-10-26

## Decision

**REJECT.** The explicit narrow recognizer passed the 24 exposed development
cases but failed every one of the six already-spent, disjoint 60-case sets.
No new corpus was created, no model was called and the independent holdout
remained sealed.

Only aggregate metrics were retained:

| Spent set | Routed | Correct routed | Selective error | Unsafe false routes | Privacy underclassification | Eligible |
|---|---:|---:|---:|---:|---:|---|
| 1 | 19/60 | 16 | 15.8% | 1 | 0 | no |
| 2 | 8/60 | 6 | 25.0% | 2 | 0 | no |
| 3 | 7/60 | 6 | 14.3% | 1 | 0 | no |
| 4 | 10/60 | 8 | 20.0% | 1 | 0 | no |
| 5 | 13/60 | 9 | 30.8% | 2 | 0 | no |
| 6 | 13/60 | 9 | 30.8% | 2 | 0 | no |

Every set missed the accepted 60% all-case route-coverage floor and the 10%
selective-error ceiling. Every set also had at least one unsafe false route.
The candidate therefore fails without threshold selection or another private
calibration.

## Implication

The result exposes a design tension: a small literal recognizer set cannot meet
the accepted coverage floor on diverse requests, while broad learned and
deterministic classifiers already failed the safety/error bar. Do not tune this
candidate from the spent private text and do not create a seventh calibration.
The next NLU implementation needs a separately designed compositional grammar
or other interpretable structured parser, developed on public synthetic cases,
with an explicit safety proof for route eligibility and the existing clarify
fallback. Automatic routing remains off.

