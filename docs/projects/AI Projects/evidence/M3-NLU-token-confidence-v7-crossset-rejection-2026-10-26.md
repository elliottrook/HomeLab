# M3 NLU token-confidence v7 exposed cross-set rejection — 2026-10-26

## Decision

**REJECT. Do not create a fresh calibration, open the sealed holdout or enable
automatic routing.**

Candidate v7 retained the unchanged accepted Qwen3.5-9B service and the frozen
three-perspective semantic ensemble, but replaced self-reported confidence with
the endpoint's per-token log probabilities. Perspective confidence was the
geometric mean output-token probability; decision and route confidence combined
that value with semantic agreement. Missing or invalid token confidence failed
the affected vote closed.

## Public development gate

The exact candidate source at SHA-256
`81df2137c69445361446d6e02ec8a16ff3fc93092c3a499a2f9a614a7605afe7`
completed the 24 public cases with:

- valid results: **24/24**;
- exact interpretations: **23/24**;
- unsafe false routes: **0**;
- routed privacy underclassifications: **0**.

That was sufficient only to enter the exposed six-set development gate.

## Nested exposed-set result

The runner at SHA-256
`f21db8e84001beac6f64ca5ae8714aebca665df9196eebfe9f2efa5ebbc20db7`
used the six already-spent 60-case development sets, ten cases per family. The
single inference attempt completed in **1,548.572 seconds**. All six source and
label digests were bound in the content-free terminal result.

Every leave-one-set-out fold stopped at inner threshold selection:

| Outer set | Result | Invalid perspective votes |
|---|---|---:|
| v1 | no inner threshold | 4 |
| v2 | no inner threshold | 4 |
| v3 | no inner threshold | 5 |
| v4 | no inner threshold | 6 |
| v5 | no inner threshold | 11 |
| v6 | no inner threshold | 11 |

No decision/route threshold pair satisfied the accepted v2 policy across any
five-set inner partition. `nested_pass` is `false`; no outer-fold transfer
claim is permitted. The terminal aggregate SHA-256 is
`dff7c72df2e078b5d9e192b79e0f503723f996ff54e5db928aa53f3a1b98191b`.

The first runner invocation found the packet's temporary set directories under
their archival names while the runner required `v1` through `v6`. It failed in
input loading before any model call. Renaming only those extracted temporary
directories corrected the packaging mismatch; the measured run above is the
single inference attempt.

## Custody and production postcheck

The exact source packet was 23,611 bytes at SHA-256
`ab956d54fb8d52a7568dbfe939737943137d76b4751936c405eb6f541d4a35ac`.
The owner-only spent-set packet was 85,602 bytes at SHA-256
`dc5e5946fdfebd43920d4ac0afbb1313a5b73448d6b00bf0f206b3bdb219e7b5`.
All temporary packets, extracted private inputs and terminal result copies were
removed from LXC110, Proxmox and the Mac after bounded reconciliation. No
request text, labels or response content were written to Git.

`local-ai-lease status` returned `ready`. The accepted model service and Aster
Agent remained active and running with zero restarts, and no evaluation process
remained.

## Practical consequence

Endpoint token probability does not stabilize this generative ensemble under
the accepted cross-set policy. Stop this candidate line. Do not tune another
prompt or confidence transform against the same spent sets. The next M3 work
must return to a materially different semantic representation, beginning with
the dedicated dense encoder and deterministic envelope under the now-accepted
v2 decision-coverage semantics.
