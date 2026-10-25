# M3 NLU local candidate seal — 2026-10-25

## Result

The existing production Qwen3.5-9B Q4_K_M model on the accepted llama.cpp
SYCL profile is now sealed as an **evaluation candidate** for the NLU boundary.
This does not deploy the adapter, call the model, enable a route or grant a
tool. It gives later calibration one exact candidate identity instead of a
digest-shaped placeholder.

The new strict local adapter:

- asks only for the six `request-interpretation.v1` dimensions;
- sends no tool definitions and accepts no route, provider, permission,
  execution-result or confidence field;
- rejects duplicate JSON keys, extra envelope/classification fields, unknown
  capabilities, incomplete output and inconsistent disposition semantics; and
- constructs a benchmark record without retaining the request or raw model
  response.

## Exact candidate

The sealed manifest is
`scripts/aster-adaptive/fixtures/nlu-candidate-bundle-qwen35-9b-sycl-v1.json`:

- artifact SHA-256:
  `456cf5af3d36bfea4c6cff3c9b5782d7f594696302e0973f510a661ab4132897`;
- canonical bundle SHA-256:
  `2245879f287bb58c502ae178c6e244edf98d29371b296c8ceee4881acc79f00c`;
- Qwen3.5-9B Q4_K_M model SHA-256:
  `cd76ec205963b3b33350093e6904d9de16c4e666fd104e1f632d25c7f15f2a13`;
- local policy artifact SHA-256:
  `57887883010ac682d50af9931b0dc80c71d2fe3b41309bf7b772fec70f4ed179`;
- request contract SHA-256:
  `49f442d73bfa77ea9a2dc55263dc9c91aaca9c88003fd9b60b68e9d63aee00c3`;
- adapter SHA-256:
  `3a3b09f12bcd2088f0d604363a5bc0e69190c177eced50dc5a14eb582749aed0`;
  and
- accepted SYCL runtime profile SHA-256:
  `a4c75169673a1a230682b73d362a05c1bdd30f7a5c41cfb9c77463204dfd4cb3`.

A read-only LXC110 check confirmed the live model and runtime-profile hashes
match the sealed source identities. The dependency-free focused NLU suite now
passes 74/74.

## Effect and next gate

The candidate is local-only, carries no case data, has tools disabled and
retains literal `authority: not-granted`. It is not promoted and its quality is
unknown under the accepted policy. The next gate is independently custodied
creation and review of 60 synthetic calibration cases, ten per request family,
followed by a lease-protected, no-tool model run. The independent holdout stays
sealed until the calibration threshold is frozen.
