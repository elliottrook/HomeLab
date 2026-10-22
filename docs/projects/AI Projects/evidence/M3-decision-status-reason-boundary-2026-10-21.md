# M3 decision status/reason boundary — 2026-10-21

## Decision

Require the typed Decision Plane contract to keep its terminal status and
policy implication semantically consistent. This is an offline contract
change only; automatic routing remains disabled.

## Finding

`decision.v1` already required a known status and reason, but validated the
two fields independently. It therefore admitted contradictory records such as
`deny` with reason `supported`, or `plan` with reason `policy-denied`. Such a
record grants no authority, but it would make audit, explanation and later
policy evaluation ambiguous.

## Correction

The contract now permits only:

| Status | Allowed reason |
|---|---|
| `plan`, `answer` | `supported` |
| `clarify`, `abstain` | `ambiguous` or `unavailable` |
| `unsupported` | `unavailable` |
| `deny` | `policy-denied` |

The existing rule remains: only `plan` may contain steps, and a route never
grants authorization.

## Verification and limit

A focused Pydantic test accepted all eight allowed combinations and rejected
five contradictory examples. The broader historical adapter test set remains
closed by its intentional reviewed-source pin after repository source drift;
that pin was not changed merely to make tests pass.

This correction does not classify a request, calibrate confidence, choose a
model, enable automatic handover, create a policy decision or grant a tool.
