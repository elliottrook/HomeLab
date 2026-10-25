# M3 NLU independent holdout conditional creation card — 2026-10-25

> State: prepared, **not eligible until a calibration threshold is frozen**
>
> Authority: no case creation, model run, routing or deployment

## Purpose and prerequisite

Create the independent 36-case qualification holdout only after the exact
calibration run produces a valid frozen threshold policy. If calibration
rejects the candidate, this card expires unused. The holdout must never inform
prompt changes, candidate selection or threshold selection.

The activation input is the exact frozen policy artifact whose registered
predecessor is
`scripts/aster-adaptive/fixtures/nlu-policy-registration-v1.json` at SHA-256
`85b5090f929c50cba02d914418c1187bb9a7d848f05c38b174f125f77442df0a`.
Activation must verify its status is `frozen`, its candidate and calibration
pins are unchanged, and `holdout_accessed` is false.

## Separate fresh roles

Five fresh contexts must remain distinct:

1. `stream-a-nlu-holdout-case-custodian-v1` creates 36 synthetic cases, six
   per family, without model output, calibration labels or threshold metrics;
2. `stream-a-nlu-holdout-label-reviewer-v1` labels the frozen cases before any
   candidate output is visible;
3. `stream-a-nlu-holdout-nonoverlap-reviewer-v1` independently proves zero
   normalized-text overlap with both reference sets;
4. `stream-a-nlu-holdout-evaluation-operator-v1` runs the already frozen
   candidate and threshold once; and
5. `stream-a-nlu-holdout-score-reviewer-v1` scores only the sealed output and
   cannot alter labels, candidate, policy or threshold.

No role may be reused. The custodian and label reviewer must not inspect
candidate output. The evaluation operator and score reviewer must not revise
cases or labels.

## Fixed exclusions and custody

- development artifact SHA-256:
  `1565a21c78875f64f4f25a190e977ae34dc01bdfcfd5e49c056e8365268b3785`;
- development normalized-text-set SHA-256:
  `53d1e0e098a4785f81e8213e1b3ed700ad8c61c48bc2f9726aa5462442445456`;
- calibration source SHA-256:
  `6ba07b680d8f49722559a7b2774e151f613428a106cc7f740b43cd972021726e`;
- calibration normalized-text-set SHA-256:
  `c5b555b806a1cf57c35797bd97d8c691c5258593f7783a46b4e45041e39e12e3`;
- calibration cases and labels remain private and must not be copied into the
  holdout context; only the exclusion-set digest and source-local comparison
  are exposed; and
- raw holdout cases, labels and model output remain owner-only outside Git.
  Git receives only content-free manifests, receipts, metrics and digests.

The two non-overlap receipts must pass
`nlu_nonoverlap_receipt.py`, bind the same 36-case holdout source/text-set and
report zero overlap. The sealed holdout must pass `nlu_holdout_release.py` and
bind the exact frozen policy, candidate, contract, scorer and both receipts.

## Stop conditions

Do not create or label cases before the frozen threshold exists. Stop if a role
is reused, a reference digest changes, any overlap is nonzero, family balance is
not six each, real/private data appears, labels are changed after output is
seen, or a receipt/manifest fails validation. Replace a flawed unopened release
under a new version; never repair a used holdout in place.

Creation and review still do not authorize inference. The later holdout run
needs its own exact candidate/policy card, compatible lease and bounded local
model-call approval.
