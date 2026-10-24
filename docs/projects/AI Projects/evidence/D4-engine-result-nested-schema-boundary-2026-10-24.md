# D4 engine-result nested-schema boundary — 2026-10-24

**Scope:** offline hardening of the future D4 private evidence journal. No
holdout, credential, model, network service or connected tool was used.

## Finding

The journal admission layer already restricted top-level result fields,
terminal status, total size and finite JSON encoding. It did not independently
validate the nested step, metadata, answer, observation and failure shapes.
A faulty injected engine could therefore place an unexpected nested field in a
private journal even though the current engine itself emits sanitized data.

## Correction and evidence

The result validator now checks:

- no more than three steps, each containing only bounded metadata and a
  sanitized answer or `null`;
- finite metadata, fixed decision/check/evidence/summary/effects fields and no
  nested reasoning field;
- bounded unique checks and typed observations;
- finite elapsed time, a zero-to-three attempt count and a closed failure
  record; and
- the exact development-only limitation string when present.

Synthetic nested reasoning, nonfinite metadata and unexpected nested fields
were rejected before a finished event was journalled. Existing finite-JSON and
65,536-byte envelope classifications remain intact. The complete evaluation
suite passes **124/124**.

## Decision

This closes an offline nested-record boundary. It does not establish answer
quality, read the holdout, authorize execution, connect a tool or advance
D4/M1.
