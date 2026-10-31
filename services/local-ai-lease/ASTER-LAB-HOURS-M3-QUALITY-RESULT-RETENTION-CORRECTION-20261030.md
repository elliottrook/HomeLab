# M3 public-gate quality-result retention correction — 2026-10-30

## Trigger

The corrected 15:30 public-gate transaction completed all 24 model requests,
but the transaction rejected the guest result as `M3_GUEST_RESULT_INCOMPLETE`.
Production restoration passed. The transaction had combined two different
decisions: structural result validation and the public quality threshold. It
therefore discarded a complete, structurally valid public result whenever its
score or safety counters did not pass, leaving no evidence that could
distinguish a genuine candidate rejection from malformed output.

## Correction

- Structural validation still requires exactly 24 attempted and 24 valid
  records, bounded counters, no retained answer content or hidden reasoning,
  and the fixed no-authority/no-routing markers.
- A structurally valid public result is written once under the root-owned
  attempt directory before the quality decision.
- A quality rejection is projected only as bounded counters (`exact`, unsafe
  routes and privacy underclassifications), a result digest and byte count.
- The dispatcher promotes that fixed projection to a bounded terminal code.
  It does not expose model answers, hidden reasoning or arbitrary text.
- The gate remains unchanged: at least 23/24 exact, zero unsafe false routes,
  zero routed privacy underclassifications and `public_pass=true`.

This is diagnostic evidence preservation, not a model, prompt, threshold or
routing change. It authorizes no retry and does not open calibration or the
sealed holdout.

## Validation

- 29 focused platform tests pass.
- All 32 release-manifest pins match their source bytes.
- The added regression accepts a bounded quality-failure projection and
  rejects malformed or unbounded variants.
