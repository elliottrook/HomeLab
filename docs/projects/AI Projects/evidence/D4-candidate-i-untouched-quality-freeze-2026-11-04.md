# D4 candidate-i untouched quality freeze — 2026-11-04

Candidate-i's new synthetic evaluation boundary is now frozen without running
the candidate. It has 20 new `i-quality-*` identities, a distinct eight-source
evidence vocabulary, 14 plan cases and six deterministic abstentions. Every
source appears at least twice. Neither candidate-f nor candidate-g's spent
packet identity is permitted.

Exact content-free bindings are:

- packet SHA-256:
  `0b9bfb86ef0e3381aca520e294b90b01f9616c51caea21e71d559467837625d0`;
- keys SHA-256:
  `5c04992b998cc4834a538583594959b614e46faa4e3d0f8606f151e3ae69a145`;
- cases / abstentions: 20 / 6.

The generator and source-freeze suite passes 13/13, including exact repository
reproduction, control/identity drift, answer-key and coverage drift, both spent
packet exclusions, and proof that construction emits no prediction, review or
quality decision. The packet has not been exposed to candidate-i, a model or a
reviewer. No booking, runner, route, authority or promotion exists. The next
milestone is the diagnosis-only runner and key-free batch path, still offline.
