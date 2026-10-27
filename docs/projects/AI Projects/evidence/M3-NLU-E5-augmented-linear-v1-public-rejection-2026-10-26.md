# M3 NLU E5 augmented linear v1 public rejection — 2026-10-26

## Decision

**REJECTED AT PUBLIC GATE.** This candidate changed both the training method and
the public training data: a deterministic regularized whole-label linear head
was trained on the original 20 E5 support examples plus 20 authored public
counterfactuals. It did not retune the rejected nearest-neighbour boundary or
use any of the six private development sets.

The exact first run and one bounded diagnostic rerun agreed:

- attempted: **24/24** public cases;
- exact interpretations: **18/24**;
- failed zero-based indices: `3, 7, 13, 17, 18, 23`;
- unsafe false routes: **0**;
- routed privacy underclassifications: **0**;
- authority: `not-granted`;
- automatic routing: `off`.

The registered public bar was at least 22/24 exact with zero safety and privacy
failures. V1 therefore stops before any private cross-set packet or holdout.
The failed cases span household control, summarization, package change, public
research, personal/public joining and unsupported transformation, so the miss
is not one threshold defect.

## Frozen source and cleanup

- linear head SHA-256: `f25311b25e608c96f86da0859c60cb74e10dd3a33f87ea678b09c568ddebc980`;
- public gate SHA-256: `969150e0b7815a7d1ce4c96b5787bf02d95e8b4d7b3aa2ae4ff7800a992e78d6`;
- E5 Q8_0 artifact: 36,685,088 bytes, SHA-256
  `afdfb5c342d2efc2a051c426dd1d00913495d5f2bbceaea100d2f3892aa31cbc`;
- focused tests: **6/6**;
- complete dependency-free NLU suite before the diagnostic-field addition:
  **398/398**.

The temporary CPU-only loopback encoder, source and model copies were removed.
Port 18085 is closed, the accepted 9B/SYCL service remains active, and the
whole-host lease reports `ready`. No service restart, production model change,
route, threshold, calibration, holdout access or authority followed.

The next public candidate may use the six public failure indices to improve
counterfactual coverage, but must remain public-only until it passes the fixed
gate. This record does not authorize private evaluation.
