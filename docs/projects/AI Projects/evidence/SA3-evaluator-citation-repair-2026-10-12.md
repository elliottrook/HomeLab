# SA3 evaluator citation-boundary candidate — 2026-10-12

The sealed holdout exposed a repeatable contract failure: the model sometimes
listed a capability or future result in `evidence_ids` before that check had
returned. The candidate repair strengthens the synthetic investigation prompt
with an explicit current-observation boundary and includes
`observed_evidence_ids` plus a machine-readable citation rule in each request.

The runner already rejected unseen citations; this change makes the boundary
visible to the model and preserves the rejection as a safety check. It does
not change the production service, model settings, tool authority, holdout
bundle, labels or scoring rules.

Validation: 51/51 local evaluator tests passed. No connected model rerun has
occurred after this candidate change, so it is not evidence of improved Qwen
quality and cannot alter the failed holdout decision without a separately
authorized rerun.
