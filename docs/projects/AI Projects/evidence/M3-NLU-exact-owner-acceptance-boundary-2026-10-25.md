# M3 NLU exact owner-acceptance boundary — 2026-10-25

Status: offline gate complete; no acceptance record exists and the proposed
policy values remain unaccepted.

## Gap closed

The policy decision required a digest-shaped acceptance reference, but the
registration gate did not validate the referenced acceptance bytes. A
fabricated digest could therefore satisfy the structural accepted-decision
shape without proving which proposal Jason accepted.

## Boundary

`nlu_policy_acceptance.py` defines a unique-key, self-hashed acceptance record
that binds:

- the exact proposal artifact bytes;
- the proposal's internal decision digest and identifier;
- acceptance of the exact proposed values only; and
- explicit `not-granted` routing authority.

It derives an accepted decision only from a valid exact proposal plus those
exact acceptance bytes. The registration gate now takes the proposal and
acceptance separately and reconstructs the accepted decision itself; it no
longer trusts a caller-supplied accepted status or arbitrary acceptance digest.

## Verification

The focused NLU suite passes 77/77. Tests cover exact derivation, proposal
drift, fabricated acceptance hashes, unknown fields, duplicate keys and an
attempted authority claim.

## Effect boundary

This is code and synthetic evidence only. It does not create or imply owner
acceptance, select or seal a candidate, open calibration or holdout data,
enable shadow traffic, choose a threshold, route a request, or grant any tool
or execution authority. Owner acceptance of proposal digest
`2e0def84…64a3d` remains a separate explicit decision.
