# M3 NLU calibration custody boundary — 2026-10-24

## Result

The offline NLU threshold path now has a content-free calibration release
boundary. It closes the structural gap between an accepted registered policy
and the calibration score used to freeze a threshold. No calibration cases,
labels, predictions or numeric acceptance values were created.

The empty template intentionally leaves total and per-family targets unset.
When a policy is later registered, a sealed calibration manifest must:

- use the exact candidate bundle bound by that policy;
- meet its total and six per-family sample minima;
- contain only opaque case, label and review-receipt digests;
- use distinct case-custodian, label-reviewer and scoring-operator identities;
- carry exact family counts and a canonical release digest; and
- match the exact calibration-artifact digest already bound by the policy.

Content, prompts, entities, labels, predictions, scores, notes and reasoning
are rejected from the manifest. The validator never reads the independent
holdout. Every artifact retains `authority: not-granted`.

## Evidence

- Validator SHA-256:
  `e31e1a52cfee8a0f09c18e48646ee2cd245957ade32994f96d4b2cbc5d77d314`
- Empty-template SHA-256:
  `4575c65aae5ca877628f385442baf3b537b74c0133e74b8f456c35545e0ea814`
- Focused NLU custody, policy, selection, holdout and scoring tests: 42/42
  passed.

Tests cover exact policy/artifact and candidate binding, forbidden content,
sample minima and an empty non-claiming template. They use synthetic metadata
only and perform no model call, routing, egress, collection or deployment.

## Remaining gate

Jason must accept the numeric policy constraints and sample minima before the
policy can be registered. Separate authorization and role assignment are then
needed to create and label an S0 calibration set. Only after candidate and
calibration bytes are frozen may the scoring operator produce a content-free
score and select the threshold. The independent holdout remains sealed and
untouched throughout selection.
