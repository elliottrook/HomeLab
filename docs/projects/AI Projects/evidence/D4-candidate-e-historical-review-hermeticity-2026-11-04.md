# D4 candidate-E historical review hermeticity — 2026-11-04

## Decision

**PASS — historical review is hermetic.**

The broad SA3 regression suite exposed a maintenance defect in the retained
candidate-E review: it compared the historical manifest against the current
working-tree versions of two source files. Those files have legitimately
evolved since candidate E was frozen, so the retained review failed even
though its historical evidence had not changed.

The review now binds each retained artifact to its proper immutable Git blob:

- candidate source files at `73901010`;
- the frozen packet at `8d1cfb2a`; and
- the retained result at `7d3d3508`.

The manifest requires those three exact commit identities and the exact four
file paths. Commit drift, path drift, unavailable history, digest drift,
duplicate JSON keys, and semantic disagreement all fail closed. Tests using a
temporary root still validate supplied bytes, which preserves tamper-test
coverage without consulting unrelated working-tree state.

## Verification

- focused candidate-E review: **3/3 passed**;
- complete `test_sa3_*.py` suite: **201/201 passed**;
- complete Aster Agent `test_*.py` suite in a disposable environment with the
  exact service requirements: **403/403 passed**;
- no production access, model call, booking, lease, service change, restart,
  route, authority or promotion occurred.

This maintenance result restores reproducibility of the retained candidate-E
evidence. It does not alter candidate E's historical decision and does not
affect candidate-i R2's separate runtime gates.
