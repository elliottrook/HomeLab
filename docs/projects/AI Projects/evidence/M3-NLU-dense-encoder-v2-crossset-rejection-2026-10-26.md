# M3 NLU dense encoder v2 exposed cross-set rejection — 2026-10-26

## Decision

**REJECT. Do not create a fresh calibration, open the sealed holdout or enable
automatic routing.**

Candidate v2 retained the BGE small English v1.5 Q4_K_M representation but
replaced independent field voting with coherent whole-label voting. Its route
score was bounded by the weakest weighted support among route disposition,
sensitivity and capability set. Candidate configuration and policy thresholds
were selected only inside each outer fold's five-set nested partition.

## Frozen inputs

- candidate source SHA-256:
  `56bce07f4b967d9ab91047d85e86d6b87b7b51ba2b54dfc7ed4b5c74611102e3`;
- nested selector SHA-256:
  `ca5be09626b145ec07263ec58f47e5c403087a930171b8efa39d265cccff42f5`;
- runtime wrapper SHA-256:
  `f1532fcbab4d9c5b4388509a146f22c0b5da31d166b9b9a1278b5afdbdd22789`;
- owner-only six-set packet: 15,202 bytes, SHA-256
  `c84ee98021e0c2cbcbb95b244a3f64adeed4796f8602035f09a5ac159efb6af9`;
- final source packet SHA-256:
  `3870e7cb69ebdc229bb46d58cb6b305536969202553f5b9f81aa85cca2aa1ad2`;
- BGE Q4_K_M: 24,808,576 bytes, SHA-256
  `363a0a4855dff6c653e06efe3209157debcf7f74e52d0d7c71e2747cd523043e`.

The dependency-free NLU suite passed 369/369 before the run.

## Nested result

The single private evaluation completed in **206.230 seconds**. The terminal
aggregate SHA-256 is
`46320d52cace0fa1b607ef84867251700216fa23ca0b6bdcfeabd1fc8e40f13c`.

| Outer set | Inner selection | Outer result |
|---|---|---|
| v1 | k=7, power=8; 87.0% coverage, 9.96% error, zero inner safety failures | 81.7% coverage, 14.29% error, **one unsafe false route** |
| v2 | no eligible inner threshold | not evaluated |
| v3 | no eligible inner threshold | not evaluated |
| v4 | no eligible inner threshold | not evaluated |
| v5 | k=9, power=8; 64.3% coverage, 9.84% error, zero inner safety failures | 71.7% coverage, 13.95% error, zero route-safety failures |
| v6 | k=9, power=8; 65.7% coverage, 9.64% error, zero inner safety failures | 66.7% coverage, 22.50% error, zero route-safety failures |

The three selected folds all exceeded the 10% outer accepted-decision error
limit, and v1 also violated the zero-unsafe-route rule. The remaining three
folds could not select an inner threshold. `nested_pass` is `false`.

## Runtime and custody

The BGE model ran as a temporary CPU-only loopback embeddings process in
LXC110. The accepted Qwen3.5-9B/SYCL service was not stopped, replaced,
reconfigured or restarted. Private text was sent only to the loopback process;
vectors existed only in memory. Retained output contains set digests/counts,
configuration, thresholds and aggregate metrics.

After reconciliation, the temporary encoder process, model, source, inputs and
result were removed from LXC110, Proxmox and the Mac. `local-ai-lease status`
returned `ready`; the accepted model service and Aster Agent remained active
and running with zero restarts.

## Practical consequence

Coherent nearest-neighbour voting improves the boundary but does not produce a
stable cross-set confidence ranking. Do not tune k, power or thresholds again
against these spent sets. The next distinct M3 hypothesis is a regularized
supervised head over fixed dense embeddings, trained only inside each nested
partition, with the deterministic route-safety envelope retained. A different
encoder family is the fallback if that learned dense head also fails.
