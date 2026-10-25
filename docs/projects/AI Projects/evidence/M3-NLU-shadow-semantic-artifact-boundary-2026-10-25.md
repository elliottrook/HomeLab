# M3 NLU shadow semantic artifact boundary — 2026-10-25

## Problem

The no-effect shadow bundle verified the exact bytes behind each interpretation
and route-proposal digest, but arbitrary content-free JSON bytes could still
satisfy those hashes. It did not prove that the artifacts were valid contracts
or that the proposal actually bound the interpretation and recorded candidate
route.

## Correction

Bundle validation now parses unique-key JSON and enforces the complete
`request-interpretation.v1` and `route-proposal.v1` boundaries without requiring
the optional Pydantic runtime. It checks:

- exact fields, candidate engine/policy pins and no confidence/authority claim;
- family, sensitivity, capability, ambiguity, disposition and reason semantics;
- request, principal, interpretation digest and policy cross-binding;
- candidate route equality, backend/egress/reason consistency and positive
  expiry;
- interpretation-disposition agreement; and
- the existing prohibition on personal-context cloud routing.

Malformed or semantically invalid artifacts fail even when the manifest is
rehashed to match their bytes.

## Validation and effect

Seven focused shadow tests and the full 97-test dependency-free NLU suite pass.
New negative cases reject an authority-bearing interpretation and a proposal
whose route contradicts the interpretation. No shadow cases were collected,
no provider was contacted, no route executed and no authority was granted.
