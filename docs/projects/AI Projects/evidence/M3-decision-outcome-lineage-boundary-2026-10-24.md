# M3 decision-to-outcome lineage boundary — 2026-10-24

**Scope:** offline synthetic evidence contracts only. Automatic routing remains
disabled; no model, production request, permission or tool was used.

## Finding

The append-only store bound each outcome to the exact registered run and its
budget. A run whose frozen Decision was `deny`, `clarify`, `abstain` or
`unsupported` could nevertheless be paired with a synthetic `completed`
fixture-conformance Outcome when both claimed zero tool calls. That would make
the evidence chain internally inconsistent even though it granted no live
authority.

## Correction and evidence

Outcome admission now re-reads the registered Decision. When its status is not
the executable `plan` or `answer` class, the only admissible Outcome status is
`denied`. A synthetic denied Decision paired with a completed Outcome was
rejected; the same run paired with `denied` / `not-executed` was accepted.

The focused Decision, Outcome, evidence-store, lineage, paired-evidence and
export-verification suites pass **30/30**. The broader historical adapter suite
still intentionally refuses its drifted reviewed source pin; this change does
not repin it.

## Decision

This closes an offline provenance inconsistency. It supplies no routing
accuracy evidence, execution authority or promotion decision.
