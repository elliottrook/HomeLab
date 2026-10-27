# M3 NLU E5 encoder v1 public gate and cross-set card — 2026-10-26

## Decision

**PUBLIC GATE PASS. PRIVATE CROSS-SET RUN NOT YET AUTHORIZED.**

The BGE nearest-neighbour and supervised-head families are closed. This
candidate changes the semantic representation to E5-small-v2 and uses its
documented asymmetric `query:` / `passage:` inputs. It retains coherent
whole-label voting, the accepted v2 confidence policy and the deterministic
route-safety envelope.

## Public-only result

The fixed 20-example support bank and 24-case evaluation contain authored
public development text in tracked source. The E5 Q8_0 encoder ran once in a
temporary CPU-only loopback process in LXC110.

- attempted: **24/24**;
- exact interpretations: **22/24**;
- unsafe false routes: **0**;
- routed privacy underclassifications: **0**;
- canonical aggregate SHA-256:
  `1f50809db5153c3637737c6e5ff9216ef54da9b0a61c5804467fe0225e775882`;
- authority: `not-granted`;
- automatic routing: `off`.

This meets the preregistered public threshold of at least 22/24 exact with no
safety or privacy failure.

## Frozen source and model

- public gate source SHA-256:
  `80d111b9a7d77cf661c7f8945c2dc957e8a74e4064e183ccd83971d75c7a8330`;
- asymmetric nested evaluator SHA-256:
  `223a4f4b28f11f0dc70e5075f8a3de54e634210af22867a2ab4456382c383b4b`;
- owner-only cross-set runtime SHA-256:
  `c4f635034b5956109b0342ab600a4a16e96c68cc8af8b0959add149bcdcaca75`;
- coherent whole-label candidate SHA-256:
  `56bce07f4b967d9ab91047d85e86d6b87b7b51ba2b54dfc7ed4b5c74611102e3`;
- nested policy implementation SHA-256:
  `ca5be09626b145ec07263ec58f47e5c403087a930171b8efa39d265cccff42f5`;
- encoder repository: `ggml-org/e5-small-v2-Q8_0-GGUF`, revision
  `14aa7ca88ca627e2ea0051929636561158e289ab`;
- encoder artifact: 36,685,088 bytes, SHA-256
  `afdfb5c342d2efc2a051c426dd1d00913495d5f2bbceaea100d2f3892aa31cbc`;
- dependency-free NLU suite: **381/381**.

The public source packet used for the live gate was 0600 and SHA-256
`36200d8bc13c8f06cc76630114d2100363429567b90a11cecc19f65559050368`.

## Next gate

The next step is one nested leave-one-set-out evaluation over the six already
spent 60-case development sets. Every case receives both an E5 `passage:`
vector for training and an E5 `query:` vector for evaluation. Similarities are
precomputed once; candidate configuration and thresholds remain selected only
inside each outer fold's five-set partition.

Pass requires all six outer folds to meet at least 60% decision coverage, at
most 10% accepted-decision error, zero unsafe false routes and zero routed
privacy underclassification. Any missing inner threshold or failed outer
constraint rejects E5 v1. It does not permit tuning against these sets.

The cross-set run requires a new exact private-packet transfer approval. It
does not authorize holdout access, fresh calibration, routing, deployment,
service restart, model replacement, tool grant or remote push.

## Runtime cleanup

The temporary E5 process, model and public source were removed from LXC110,
Proxmox and the Mac. The accepted Qwen3.5-9B/SYCL service and Aster Agent
remained active/running with zero restarts; `local-ai-lease status` returned
`ready`.
