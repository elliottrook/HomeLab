# D4 fair-scorer malformed-input boundary — 2026-10-20

## Classification

- **VERIFIED CURRENT STATE:** the offline SA3/D4 fair scorer now rejects
  malformed case, capability, key and review containers with a bounded
  `ValueError` before calculating a qualification result.
- **REPOSITORY INTENT:** future sysadmin comparisons must fail closed when
  evaluation metadata is incomplete or has an unexpected shape.
- **UNKNOWN / REQUIRES VERIFICATION:** no model answer, connected tool,
  production Aster request or operational outcome was evaluated here.

## Change and result

`services/aster-agent/evals/sa3_fair_scorer.py` now validates exact case and
key record shapes, non-empty visible capability descriptions, list-shaped
check-set and review collections, and exact independent-review records. An
empty review list remains a valid *unqualified* input; a mapping, string,
`null` or unexpected review field is rejected rather than being mistaken for
“no review.” Unknown case or key fields also fail closed so hidden labels
cannot silently enter the grading boundary.

The focused D4 intake, plan and scoring suite passed **28/28** tests. The new
tests cover malformed capability/check-set containers, non-list reviews,
unexpected review fields and hidden case/key fields.

## Practical implication

The offline scorer is safer to use once a separately reviewed qualification
corpus exists. This work does not review the current draft, call a model,
grant a tool, establish a promotion threshold or authorize deployment.
