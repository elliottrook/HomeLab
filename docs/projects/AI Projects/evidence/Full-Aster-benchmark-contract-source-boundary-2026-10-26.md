# Full-Aster benchmark contract source boundary — 2026-10-26

## Result

**PASS — source validator complete; owner-frozen values and case packet remain
open.**

The new dependency-free validator prevents a component score, NLU calibration
or informal latency observation from being treated as the matched full-Aster
baseline for a 27B-plus reasoning challenger.

It accepts only an `owner-frozen` contract containing:

- a hash-bound packet with at least twelve cases across at least three
  complete-Aster request families;
- exact baseline and challenger model/runtime identities, with the accepted
  baseline marked reasoning-off and challenger marked reasoning-on/27B-plus;
- overall and per-family complete-useful-answer floors plus at least two
  reviewers;
- immutable zero-tolerance safety floors for fabricated effects, unsafe action
  advice, privacy underclassification and out-of-allowlist capability claims;
- absolute baseline/challenger p50/p95, challenger TTFT and timeout bounds;
- GPU/host memory, model-call and retry budgets;
- identical inputs, retrieval snapshot, response schema and retry policy, with
  reasoning content excluded from retention; and
- mandatory F6 admission, exact baseline restoration, independent observation
  and rejection of any result with uncertain recovery.

The validator always returns `authority: not-granted`. Five focused tests pass,
including rejection of drafts, component-only packets, loosened safety floors
and optional recovery.

- validator SHA-256:
  `b18a14d88814bcb01084ffed9944cff3007677398862b6a7fe3fa2f752a2b141`;
- tests SHA-256:
  `335f8602f923c3c4fb86b081c45de0416adc402d525cdb8bb7216bdd02b8a519`.

## Remaining decision

Jason still needs a concrete reviewable proposal for the packet composition,
numeric quality and latency floors, exact accepted 9B identity and one exact
27B-plus challenger identity. Source completion does not choose those values,
authorize model installation, start a lease or waive F2–F6 recovery gates.

No model request, private-data access, service change, restart, lease, routing,
deployment or remote write occurred.
