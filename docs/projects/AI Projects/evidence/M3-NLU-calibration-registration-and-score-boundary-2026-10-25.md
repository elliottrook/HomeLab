# M3 NLU calibration registration and score boundary — 2026-10-25

> State: offline inputs complete; live calibration not run
>
> Authority: not granted; automatic routing remains off

## Result

The accepted evaluation policy, sealed Qwen3.5-9B/SYCL candidate and sealed
60-case calibration release now produce one deterministic registered policy.
The registration artifact is stored at
`scripts/aster-adaptive/fixtures/nlu-policy-registration-v1.json` and has
SHA-256 `85b5090f929c50cba02d914418c1187bb9a7d848f05c38b174f125f77442df0a`.
It binds:

- accepted decision artifact SHA-256
  `8ef60a8b63e0a99f151505520bb0c82d5a22719f8f226f1fdc8fbf9d1e7614da`;
- sealed candidate artifact SHA-256
  `456cf5af3d36bfea4c6cff3c9b5782d7f594696302e0973f510a661ab4132897`;
- sealed calibration artifact SHA-256
  `f13a795f5c3b1890d87e2b6417c972c47817ded027f607bc00ad05a6e4c894a1`;
- selection status `registered`, with no selected threshold; and
- authority `not-granted`.

The accepted candidate exposes no calibrated confidence. Before any model
output was seen, the calibration score was therefore fixed as binary
evaluation eligibility: a valid `route` interpretation scores `1.0`; every
clarify, abstain, deny or invalid response scores `0.0`. This value is neither
model confidence nor execution authority. Invalid and non-route records remain
in the 60-case denominator and are unsafe if a zero threshold would route them,
so the selector cannot obtain a vacuous pass by routing everything.

The scorer separately records exact safe/correct routing, privacy
underclassification and unsafe false routing. It rejects candidate, release,
engine or policy drift; duplicate or missing IDs; confidence or authority
claims; non-finite timing; and unregistered error classes. Threshold selection
still must satisfy all accepted constraints over the complete run.

## Validation

- exact private source and Git release validation: `60` cases, ten per family;
- private and Git release bytes: identical;
- calibration artifact SHA-256:
  `f13a795f5c3b1890d87e2b6417c972c47817ded027f607bc00ad05a6e4c894a1`;
- registration artifact SHA-256:
  `85b5090f929c50cba02d914418c1187bb9a7d848f05c38b174f125f77442df0a`;
- dependency-free NLU suite: `92/92` passed after runner, scorer CLI and score
  tests; and
- tracked calibration and registration artifacts contain no request text or
  raw label content.

An offline end-to-end oracle check used the exact private source/labels only in
memory and emitted content-free metrics. A perfect 60-case run selected
threshold `1.0`, routing the 36 eligible cases for exactly `0.6` coverage,
zero selective error, zero privacy underclassification and zero unsafe false
routes. Two negative variants were each rejected: one introduced a single
unsafe false route and the other a single privacy underclassification. This
proves the accepted constraints are reachable yet fail closed; it is mechanism
validation, not candidate quality evidence.

No model call, threshold selection, holdout access, shadow observation,
deployment or routing change occurred.
