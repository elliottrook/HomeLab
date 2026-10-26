# D4 fixed Doctor deterministic limitation boundary — 2026-10-26

## Decision

The local model must not be responsible for stating the cause/repair
limitation. The v2 prompt repeated that instruction, but a fresh eight-case
development run still omitted it on the same warning case. The new v3 adapter
therefore appends one fixed statement after every nonempty model answer:

> This fixed observation alone cannot establish a cause or a repair, and it
> does not establish broader system health.

This is a presentation safety boundary. It does not infer health, alter the
model's observed state, recommend a repair, grant a tool or enable routing.

## Measured development results

Both runs used the already-running accepted local 9B/SYCL service through the
fixed private endpoint. No service was stopped or restarted and the lease
state remained `ready`.

The v2 prompt-only run completed `8/8`. Independent blind review found:

- state accuracy: `8/8`;
- evidence scope: `8/8`;
- freshness: `8/8`;
- limitation calibration: `7/8`;
- unsafe claims: `0`;
- raw-attempts SHA-256:
  `42ab58e471a4711c662a9c30870941c9bf6951e53cedec4fbae84294397c0820`;
- review SHA-256:
  `5ac982b60df72edd9af2dcc237b3a240f4896a91aa7a753acfc143bc565a0233`;
- score SHA-256:
  `77539916cc059188ad954d687b383db87236c72d23ad44e955d5209715986f55`.

The v3 deterministic-boundary run then completed `8/8`. A different blind
reviewer found:

- state accuracy: `8/8`;
- evidence scope: `8/8`;
- freshness: `7/8`;
- limitation calibration: `8/8`;
- unsafe claims: `0`;
- raw-attempts SHA-256:
  `85e03b2e52d1e78c5b9f7663c067e5e3a98ca273b815c59cc0cdbc3acf17ad40`;
- review SHA-256:
  `ae21c383fff3c697c80dc168a73199c63c8b1b0b898245dbc76c1823460af442`;
- score SHA-256:
  `003b80938c08bcfe36672f668839dbf9667e74f9539f620d88c5a1cece43b78b`.

The deterministic boundary fixed the intended limitation dimension. The new
freshness miss remains a model-quality issue. Both results are development
regressions over an already exposed packet and cannot replace a newly frozen
qualification packet.

## Deterministic fixed-path result

The fixed Doctor input already contains the complete bounded fact set: state,
timestamp, age and exact check identity. A separate deterministic formatter
now validates those fields and renders the answer without a model call. A
third independent blind reviewer measured:

- state accuracy: `8/8`;
- evidence scope: `8/8`;
- freshness: `8/8`;
- limitation calibration: `8/8`;
- unsafe claims: `0`;
- attempts SHA-256:
  `cd47e0545c8cd5c6c7557637a23b743899eabac6651690fd5eea68af6301e7fc`;
- review SHA-256:
  `7e528854047db386c9b7b6f38ea16128e6b6681cbb3c9ce220033f2844adab36`;
- score SHA-256:
  `70be0132f3405b0907169ffd272f5945d31ff6ed58d611369655f90ea954a707`.

This is the preferred architecture for this fixed check because generation
adds variability without adding information. It remains exposed development
evidence and is not deployed. Candidate-H remains relevant for open-ended,
bounded investigation questions that cannot be answered by a fixed formatter.

## Validation and authority

Six focused v3 adapter/runner tests and three deterministic-answer tests pass.
The model service remained active
with zero restarts; Aster Agent and Speech remained active. Answers and reviews
remain in owner-only local evidence outside Git. No repair tool, automatic
route, provider egress or production deployment is authorized.
