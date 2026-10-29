# SA3 expanded-source quality run and blind-review packet — 2026-10-29

Status: **RUNTIME COMPLETE; INDEPENDENT MODEL-BLIND REVIEW OPEN**

The distinct booked workload `aster-stream-a-sa3-20261029-1415` claimed at
14:15 PDT after an authoritative clear-window check and the previous attempt's
restoration buffer. Its fixed transaction drained the registered consumers,
used the accepted Qwen 3.5 9B Q4_K_M model on the pinned b11429 SYCL runtime,
and restored the exact production stack.

The retained canonical result is root-custodied on Proxmox and has SHA-256
`13003c0d2c75c1a600b9e5f7ffa1a71f8be8f2966e1b12936613a9c21ba960f5`.
It contains exactly 20 predictions, zero retries, zero errors and zero effect
claims. Outcomes are 3 `plan`, 17 `clarify` and 0 `invalid`. Model-call latency
was 42.944 seconds total, 2.0905-second p50, 2.998-second p95 and 3.244-second
maximum. These are descriptive observations, not quality acceptance.

The reservation terminal state is `complete`, `production_restored=true` and
`request_count=20`. Independent postcheck found the whole-host lease ready;
drain state, drain lock, operation lock, SA3 listener and guardian absent; Aster
Agent, the accepted llama.cpp/SYCL service, Speech, `pvescheduler` and
`pvestatd` active; and the Lab Hours Doctor passing.

The frozen builder accepted the exact result and produced
[`SA3-expanded-source-quality-blind-review-packet-run-2026-10-29.json`](SA3-expanded-source-quality-blind-review-packet-run-2026-10-29.json).
It contains all 20 cases under neutral alias `candidate-f`, discloses no model
identity, omits latency and answer keys, and has canonical SHA-256
`329a0e2ca13042a9f8a24c97097ebfa288525cff6261c84e8fd9ccd38c0f02ff`.
The complete offline review/decision suite passes 31/31.

The remaining gate is an independent reviewer response covering all six frozen
semantic judgments for all 20 cases. Stream A must not manufacture that
independence. Only after a digest-bound response exists may the deterministic
decision combine it with the separately held answer key. No automatic route,
repair authority, model promotion or provider decision follows from this run.
