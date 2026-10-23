# M3 outcome-budget lineage boundary — 2026-10-23

## Finding

The append-only synthetic evidence store bound each outcome to an exact
registered run and validated the standalone Outcome schema, but it did not
independently compare a completed outcome with that run's frozen budget. A
synthetic producer could therefore record fixture conformance with the wrong
tool-call count or with elapsed/output measurements beyond the registered
limits.

## Correction

When accepting a linked outcome, the store now rejects tool calls beyond the
registered budget. A completed outcome must also record exactly the number of
steps in the frozen Decision and remain within the registered wall-time and
output-byte budgets. Non-completed statuses retain their existing
`not-executed` verification rule and may still report the measurement that
caused a budget-exceeded result.

## Verification and limit

Focused contract/evidence tests rejected completed outcomes with too few or
too many tool calls, elapsed time beyond the wall budget, or output beyond the
byte budget. The evidence lineage, store, paired-evidence and verification
suites passed 27/27 using the bundled dependency runtime. The broader adaptive
discovery remains deliberately blocked by historical reviewed-source pin drift
and unrelated legacy environments; no pin was changed.

This protects offline evidence lineage. It does not establish routing quality,
enable automatic routing, grant tools, or promote a candidate.
