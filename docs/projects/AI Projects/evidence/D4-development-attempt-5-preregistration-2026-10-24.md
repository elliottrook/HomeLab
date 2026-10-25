# D4 development attempt 5 preregistration — 2026-10-24

## Frozen candidate

The offline diagnosis/verification correction produces dry-run digest
`7cb33aec4ac580774e884923b223ddd2427cd68fbc6e2b1da3899479d6630fb6`.
It binds twelve exposed development cases, nonthinking mode, a maximum of 36
model calls, no connected tools and no effects. Authentication is not read by
the dry run. Candidate alias `candidate-B` is reserved for its model-blind
review packet.

No model call or production change occurred while preparing this candidate.

## Predeclared decision

The frozen `sa3-development-decision-rule-v1.json` has SHA-256
`02c8016396afe4de3103e3f18a8e6c32ee4734dfc5311614fb4f54946d923b2f`.
It requires all twelve cases to pass every one of the six model-blind rubric
dimensions and therefore requires 12/12 all-dimension passes. A single failed
case or dimension is a semantic NO-GO and returns the work to offline contract
correction before another model attempt.

Even a pass means only that Stream A may design a separately reviewed connected
read-only pilot. The rule retains `authority: not-granted`; it cannot release a
role, route, tool or deployment.

## Review and evaluator boundary

The version-two review packet binds the exact run digest and candidate alias
while retaining model/runtime and timing blindness. It also carries the new
discrimination and verification fields for review. The scorer preserves those
identities in its bounded summary. The decision evaluator requires the
preregistered rule digest, exact run/candidate identity, twelve unique review
rows and internally consistent counts before returning a decision.

- `evaluate_sa3_development_gate.py` SHA-256:
  `761798251b990f8ad486b27ad683ec16b0192a999a8e88a302114f909d86ca52`
- `prepare_sa3_development_review.py` SHA-256:
  `9807eab521dcbbce675dfbd5cd5153c40e09be25bedf3a55d8111ca3a7fcda65`
- `score_sa3_development_review.py` SHA-256:
  `b4afb776c36ab647913bb1612f51ffe2fe00496052377a3ba6f1feb0f4d2e4e1`
- Complete evaluation suite: 161/161 passed.

The next effectful step is one explicitly approved development model run at the
exact digest above. It must use a new owner-only journal and cannot overwrite
attempt 4. Afterward, a fresh model-blind reviewer must complete candidate-B's
private review before the frozen rule is applied.
