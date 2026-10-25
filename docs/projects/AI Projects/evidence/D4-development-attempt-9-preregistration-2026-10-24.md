# D4 development attempt 9 preregistration — 2026-10-24

## Candidate-F correction

Candidate-E's blind review identified three bounded development defects:

1. five verification proposals lacked a relevant, testable acceptance
   condition;
2. two diagnoses exceeded what the retained observations established; and
3. one answer gave stale evidence unsupported causal weight.

Candidate-F changes only the investigation instruction. It now requires the
model to:

- avoid identity, ownership, topology or causal inference from correlation;
- use stale evidence as history rather than proof of a current cause;
- conclude only when retained observations uniquely support the diagnosis,
  otherwise clarify and preserve the alternatives;
- name only supplied capability or observed evidence IDs in verification;
- state a concrete expected condition that distinguishes the diagnosis or
  remaining alternatives; and
- verify the full success/recovery condition, safe ordering and authoritative
  reconciliation when relevant, rather than a proxy.

The response schema, budgets, fixtures, model/runtime, tool-free boundary and
frozen 12/12 all-dimension threshold are unchanged.

## Frozen identities

- Exact run digest:
  `3d746f45f39e496a3f8eb998f367b59847d81dc0506afcd0b53425fc2b7fa827`.
- Exact eleven-file source manifest SHA-256:
  `ba5d5951c7776d9f833f1adc8a93bd370f06dbbb1dd251bae34516e4acd59e8a`.
- Frozen candidate-F decision rule SHA-256:
  `e10c2c16b48047888021a13c43ed6b29a9bef1e9064cbc6d9d9b1316b7a1cb`.
- Complete offline suite: 164/164 passed.

Candidate-F has not run. A later approval must bind this exact digest, a new
owner-only attempt-9 journal, no retry and the existing 36-call maximum. A
fresh-history blind review remains conditional on 12/12 structural admission.
No result automatically grants authority.
