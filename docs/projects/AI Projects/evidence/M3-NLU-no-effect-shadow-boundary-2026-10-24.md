# M3 NLU no-effect shadow boundary — 2026-10-24

## Result

The offline NLU path now has a content-free shadow evidence boundary. Its
initial version accepts only S0 synthetic sources and records the baseline and
candidate route proposed for each opaque case. It cannot call either route,
contact a provider, execute a capability or grant authority.

A sealed shadow manifest must bind the exact frozen threshold policy and its
candidate bundle. Each row contains only an opaque identity, request family,
interpretation/proposal digests, baseline/candidate route and a consistent
route-change flag. Raw requests, answers, entities, notes, reasoning, tools and
tool arguments are forbidden. Both `execution_attempted` and
`provider_egress_attempted` must be false.

## Evidence

- Validator SHA-256:
  `4d56f8cf7d4e7c461d82d48b2f75e70995c6d27d81b806e20ea5e0c06fcf52bc`
- Empty-template SHA-256:
  `84b5d1ef4efdf4e8ba760662cf06ff2b4c9425fcece7c0125b5b59287bc0912b`
- Focused NLU shadow, calibration, threshold, holdout and scoring tests:
  46/46 passed.

The tests cover exact frozen-policy and candidate binding, content rejection,
route-change consistency and the no-effect/no-egress attestations. They use
synthetic metadata only and make no model, network or production call.

## Limits and next gate

The empty template is not shadow evidence and does not authorize collection.
An S0 shadow run needs an accepted numeric threshold policy, assigned custody
roles, a frozen candidate and separately approved synthetic cases. A future
real-interaction shadow would require a new contract and explicit privacy,
retention and collection approval. Even a successful shadow comparison would
remain advisory and could not enable automatic routing.
