# D4 Candidate-J blind-review and decision boundary — 2026-11-05

## Result

Candidate-J's untouched-quality post-run path is source-complete before any
quality packet materialization, registration, booking or model call. The
boundary accepts only the exact strengthened packet identity and a complete
20-row result with exactly 14 model requests, six deterministic no-transport
abstentions, zero retries, zero errors, zero effects, authority none and
automatic routing off.

The blind packet removes the model identity, per-row model identity, transport
flag, finish reason, latency, error metadata and answer keys. It exposes only
the synthetic prompt, observations, registered capabilities, registered
hypotheses and deterministic candidate answer. Registered hypotheses remain
visible because Candidate-J's bounded task is hypothesis selection; hiding
them would make semantic review impossible. Every review is bound to the
canonical blind-packet digest and must score all six dimensions for all 20
rows: hypothesis selection, evidence, freshness, scope, verification and no
false completion.

The decision path requires exactly three distinct model-identity-blind
reviewers and uses their conservative intersection. It passes only at 18/20 or
better when all six deterministic abstentions pass and no reviewer reports a
false-completion failure. Even a pass leaves authority `none`, automatic
routing `off` and promotion `not-authorized`.

## Frozen source

- blind packet and response validator:
  `8c22abce9539407a0e7bc8427faaf48c0199f836a47146614fbcc40bc1e23cc7`;
- three-reviewer decision:
  `990e435a58fa6a642be970ad382fc48a3133dd6914ae2feab88db25510e6ce32`;
- quality packet:
  `53cfd6a5a8b09ada122c64c60af3264b0ebda595bf1f2d5d53da2710e0141132`;
- answer keys:
  `cab2790dbb6e84b0bbe269c876dee8c4b116abfb4fa6fc2a119782e4b7fcd526`.

The complete Candidate-J source suite passes 36/36, including packet and
result drift, request-count drift, per-row identity exposure, transport on an
abstention, runtime errors, incomplete or identity-exposed reviews, duplicate
reviewers, conservative threshold, mandatory-abstention and false-completion
failures.

## Boundary

This milestone does not materialize the untouched packet or keys, register a
workload, query or reserve Lab Hours, invoke a model, pre-score a case, appoint
the eventual reviewers, authorize a retry, disclose model identity or promote
a route. Separate custody, hash-pinned workload registration and one exact
booked run remain later gates. The three independent reviews may occur only
after a complete eligible retained result exists.
