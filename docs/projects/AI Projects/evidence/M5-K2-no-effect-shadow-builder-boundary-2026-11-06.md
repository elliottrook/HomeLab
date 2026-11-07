# M5 K2 no-effect shadow builder boundary — 2026-11-06

## Outcome

The missing content-minimizing builder for the frozen 60-case M5 shadow
contract is source-ready. It does not supply or manufacture the representative
S0 rows and does not call a model. It converts a later exact sanitized,
labelled result set into the already frozen no-effect envelope.

## Exact source

| File | SHA-256 |
|---|---|
| `scripts/aster-adaptive/nlu_k2_no_effect_shadow_builder_v1.py` | `b639628861642f88fb5b46c6a3d0751ec7d01bce599d5671808622a44ead531b` |
| `scripts/aster-adaptive/test_nlu_k2_no_effect_shadow_builder_v1.py` | `0c596ae3b1d7aac3d0e64e87ce502270fb74f81e0946d8a40ca286bd6b27ce24` |

## Boundary

The builder requires exactly 60 unique sanitized S0 rows, ten for each request
family. It validates the expected and candidate label IDs, explicit acceptance,
baseline status and finite latency no greater than 45 seconds. It runs the
non-authorizing selector only to calculate the proposed route and its digest;
no proposed route or provider egress is executed.

Request text is reduced to SHA-256 in the output. The envelope contains only
case identity, request digest, expected/final label IDs, acceptance, proposed
route projection, baseline status, latency and the recomputed route-proposal
digest. It fixes 60 model requests, zero retries/errors, zero external cost,
`route_execution_attempted=false`, `provider_egress_attempted=false`,
`authority=not-granted` and `automatic_routing=off`, then validates the complete
envelope with the frozen M5 scorer.

## Verification

- focused builder tests: 4/4 passed;
- syntax compilation: passed;
- balanced exact synthetic fixture: 60/60 accepted and exact, shadow pass;
- duplicate, unbalanced, unknown-field, unknown-label and effect mutations:
  fail closed;
- model, provider, route and production effects: none.

The representative sanitized S0 fixture, its independent labels and the later
qualified candidate collection remain separate gates.

The matching [fixture preregistration](M5-K2-shadow-fixture-preregistration-2026-11-06.md)
now fixes those gates before authoring: 60 unique cases, ten per family, no
development/sealed overlap, distinct fixture custodian and label reviewer,
labels frozen before candidate collection, and request digests only in public
evidence. Its focused suite passes 4/4; no fixture has been created.
