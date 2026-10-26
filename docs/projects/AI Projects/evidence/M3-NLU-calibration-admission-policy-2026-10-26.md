# M3 NLU calibration admission policy — 2026-10-26

## Decision

Retain the owner-accepted coverage definition: routed cases divided by all
calibration cases. Do not weaken or reinterpret the 60% threshold after seeing
results. Instead, admit a future calibration only when its independent labels
make that target mathematically possible with zero unsafe routes.

For a 60-case calibration this requires at least 36 labels whose accepted
disposition is `route`. The existing minimum of ten cases in each of the six
families remains unchanged. This is a corpus-admission constraint; it does not
require every family to have the same route proportion and it does not expose
labels to the candidate.

## Enforcement

`nlu_calibration_admission.py` now rejects a labelled packet before any model
execution when:

- it has fewer than 60 cases;
- any family has fewer than its accepted ten cases;
- an identity is duplicated;
- or the number of safe-route targets cannot reach the frozen total-case
  coverage requirement within the frozen unsafe-route limit.

The admission receipt records only counts, denominator semantics and the
unchanged `authority: not-granted` boundary. Four focused tests cover the exact
36/60 pass boundary, the 35/60 impossible boundary, family imbalance and
identity/policy drift.

## Practical effect

Calibration-v6 would now have failed before spending model time. A new
independent calibration is still premature: the deterministic-first challenger
must first pass all six spent development sets under the unchanged selective
error, privacy and unsafe-route constraints. The sealed holdout remains closed
and automatic routing remains off.
