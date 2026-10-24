# D4 private-journal strict-JSON boundary — 2026-10-24

**Scope:** offline hardening of the future label-free D4 investigation runner.
This change did not read the private holdout, access a credential, call a
model, connect a tool or change a live service.

## Finding

The case, manifest and local-service response paths already rejected repeated
JSON keys and non-standard numeric constants. Journal resume still used the
permissive standard decoder. A deliberately formed local journal could
therefore contain ambiguous repeated keys or `NaN`/infinity tokens before the
shape, sequence and hash-chain checks ran.

## Correction

`sa3_fresh_package.py` now decodes every persisted journal row with a strict
loader that rejects repeated object keys and non-JSON numeric constants. The
existing row shape, release binding, hash chain, sequence validation, result
schema and no-replay rules remain unchanged.

## Evidence

- Normal journal creation, pause/resume and completed-session no-replay tests
  still pass.
- Synthetic repeated-key journal JSON is rejected.
- Synthetic `NaN`, positive infinity and negative infinity journal values are
  rejected before journal reconciliation.
- The complete evaluation test suite passes **122/122**.

## Decision

This closes one offline parser ambiguity in the future private evidence
journal. It does not make the development corpus qualification evidence,
authorize a holdout run or advance the D4/M1 live gates.
