# M3 NLU calibration creation card — 2026-10-25

> State: approval-ready; no cases or labels created

## Purpose

Create the disjoint synthetic calibration set needed to measure the exact
sealed Qwen3.5-9B/SYCL NLU candidate against Jason's accepted threshold policy.
This stage creates and reviews evidence only. It does not call a model, inspect
the independent holdout, select a threshold, enable routing or grant tools.

## Frozen inputs

- accepted policy proposal decision SHA-256:
  `2e0def84e095aa39f975d19257f2255d823210dc3aa066af71424203cd964a3d`;
- accepted decision artifact SHA-256:
  `8ef60a8b63e0a99f151505520bb0c82d5a22719f8f226f1fdc8fbf9d1e7614da`;
- sealed candidate artifact SHA-256:
  `456cf5af3d36bfea4c6cff3c9b5782d7f594696302e0973f510a661ab4132897`;
  and
- sealed candidate canonical bundle SHA-256:
  `2245879f287bb58c502ae178c6e244edf98d29371b296c8ceee4881acc79f00c`.

## Exact creation scope

1. A case custodian creates exactly 60 synthetic requests: ten for each of
   `household-command`, `general-answer`, `read-only-investigation`,
   `change-request`, `external-research` and `unsupported`.
2. The set must include public, internal and personal sensitivity; clear and
   ambiguous requests; mixed-intent and changed-intent examples; and safe
   clarify, abstain and deny outcomes. It must contain no real credential,
   token, private message, actual address or production action.
3. A distinct label reviewer assigns the six `request-interpretation.v1`
   dimensions without seeing model output.
4. A scoring operator receives the sealed cases only after labels and review
   receipts are frozen. This role does not create or change labels.
5. Exact normalized text hashes must not overlap the 24 exposed development
   cases. The independent 36-case holdout remains unopened; its custodian
   provides only a content-free non-overlap receipt when the calibration set
   is sealed.
6. Raw cases, labels and receipts remain owner-only outside Git. Git receives
   only the content-free calibration release: opaque IDs, family, case hash,
   label hash and review-receipt hash.

Role identifiers will be:

- `stream-a-nlu-calibration-case-custodian-v1`;
- `stream-a-nlu-calibration-label-reviewer-v1`; and
- `stream-a-nlu-calibration-scoring-operator-v1`.

The roles must be carried by separate fresh review contexts. The case
custodian cannot act as label reviewer or scoring operator.

## Stop conditions

Stop before sealing if the count or family balance differs, a role is reused,
any development overlap appears, a real/private datum appears, a review
receipt is missing, or holdout non-overlap cannot be confirmed without opening
the holdout. Do not repair a reviewed label after seeing candidate output;
replace the entire unrun release under a new version if pre-run review finds a
fault.

## Subsequent gates

Case creation and blind label review do not authorize inference. After the
content-free release is validated and committed, a separate exact run card
must bind its hash, the accepted policy and the sealed candidate. That later
card needs a compatible live lease and a bounded model-call approval. Threshold
selection occurs from calibration scores only; the independent holdout remains
sealed until the threshold is frozen.
