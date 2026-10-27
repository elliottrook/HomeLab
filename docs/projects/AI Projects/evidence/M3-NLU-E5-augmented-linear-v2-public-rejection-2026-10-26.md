# M3 NLU E5 augmented linear v2 public rejection — 2026-10-26

## Decision

**REJECTED / E5 LINEAR FAMILY CLOSED.** V2 added twelve public-only
counterfactuals for the six heterogeneous misses in v1. It retained the same
deterministic regularized whole-label linear head and fixed E5 representation.
No private cross-set case, calibration set or holdout was read.

The fixed public gate returned:

- attempted: **24/24**;
- exact interpretations: **19/24**;
- failed zero-based indices: `9, 11, 13, 21, 22`;
- unsafe false routes: **0**;
- routed privacy underclassifications: **2**;
- authority: `not-granted`;
- automatic routing: `off`.

V2 misses the 22/24 quality floor and violates the zero-privacy-failure rule.
The v1 failures did not disappear cleanly; new errors appeared in personal
calendar and unsupported-personal semantics. Further E5 linear-head or public
counterfactual tuning is therefore closed rather than adapting repeatedly to
the same 24 public cases.

## Frozen source and cleanup

- v2 public gate SHA-256:
  `204c154dc424b38a571601bbbdbb4ee1fffaea4e4bc054442501a3aa3322fa44`;
- v2 focused-test SHA-256:
  `d6761f30e0095ed20f0067134442d198323f31c6c64ada9c321002b7180d2c4b`;
- source tests: **3/3**;
- complete dependency-free NLU suite: **401/401**;
- E5 Q8_0 artifact: 36,685,088 bytes, SHA-256
  `afdfb5c342d2efc2a051c426dd1d00913495d5f2bbceaea100d2f3892aa31cbc`.

The temporary CPU-only process, model and source copies were removed, port
18085 is closed, the whole-host lease is `ready`, and the accepted 9B/SYCL
service remains active with the same process. No restart, production-model
change, route, threshold, calibration, holdout access or authority followed.

Another M3 attempt now needs a different representation or task formulation,
not another E5 neighbour, prefix, threshold, linear head or augmentation pass.
