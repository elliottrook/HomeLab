# M3 NLU compositional parser v1 rejection — 2026-10-26

## Design

The offline candidate separated family description from route eligibility. It
used public explicit lexicons, required complete family-specific slots, allowed
only one reviewed calendar-plus-web composition, applied policy denials first,
and clarified incomplete or conflicting frames without capability needs.

The public suite passed 19/19 tests, including all 24 exposed development
cases, a public paraphrase matrix, conflict/incomplete frames, policy denials
and output confinement.

## Cross-set decision

**REJECT.** Aggregate evaluation on the six already-spent 60-case sets gave:

| Spent set | Routed | Correct routed | Selective error | Unsafe false routes | Privacy underclassification | Eligible |
|---|---:|---:|---:|---:|---:|---|
| 1 | 21/60 | 20 | 4.8% | 1 | 0 | no |
| 2 | 11/60 | 9 | 18.2% | 1 | 1 | no |
| 3 | 13/60 | 10 | 23.1% | 1 | 2 | no |
| 4 | 14/60 | 11 | 21.4% | 1 | 1 | no |
| 5 | 15/60 | 9 | 40.0% | 1 | 2 | no |
| 6 | 16/60 | 10 | 37.5% | 3 | 1 | no |

Coverage was 18.3–35.0%, below the accepted 60% floor in every set. All sets
had unsafe false routes and five had privacy underclassification. No private
request, label or answer is retained in Git.

## Consequence

Do not expand these lexicons against spent private text and do not create a
seventh independent calibration. Both the literal recognizer and compositional
grammar are rejected. The next architecture decision must evaluate a materially
different representation or model strategy on public synthetic development,
while retaining deterministic privacy/policy guards, clarification fallback,
dimensional scoring and the sealed holdout. Automatic routing remains off.

