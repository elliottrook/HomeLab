# D4 tool-free development attempt 8 — 2026-10-24

## Structural execution

The explicitly approved candidate-E run at digest
`0e6b324a5e779b00744f9258431280016116df75e1f7cccd67d0e383545104d6`
passed the structural execution gate on the accepted Qwen3.5-9B Q4_K_M /
llama.cpp b11429 / SYCL service.

- All 12 sessions produced accepted terminal answers: 4 `clarify` and 8
  `conclude`.
- 31 model calls completed in 166.388 recorded seconds; no retry ran.
- Nineteen nonterminal check responses had terminal-only advisory strings
  cleared before retention, as preregistered.
- No connected tool, effect, timeout, service restart, lease or production
  change occurred.

The immutable owner-only journal remains at
`/root/aster-d4-development-evidence-20261024/attempt-8-ledger.jsonl`, mode
0600, SHA-256
`4ee7ed74dbd290d893c490f86e601bd646e50d870f42eae60082cd44ce764515`.
It is 52,005 bytes with 24 hash-chained rows. Temporary executable sources
were removed. Aster Agent, the accepted model service and Speech remained
active; the model service retained zero restarts and the lease returned
`ready`.

## Independent model-blind review

A fresh-history reviewer saw the private twelve-case packet without model,
runtime or timing identity. The packet SHA-256 is
`6fa2f23e8d3ec0e9357802109dccbe4d8bf3560d0fe292fd416668ca65113b20`.
The completed owner-only review is mode 0600, 4,675 bytes, SHA-256
`7b373770fbe243336bb8e361162f6bcc83b8020adc3974e09a20a7005639643b`.

The independently validated bounded score is:

| Dimension | Passed |
|---|---:|
| diagnosis | 10/12 |
| evidence | 10/12 |
| freshness | 11/12 |
| scope | 12/12 |
| verification | 7/12 |
| no false completion | 12/12 |
| all dimensions | 6/12 |

Failed review IDs were D4R-02, D4R-04, D4R-07, D4R-08, D4R-09 and D4R-10.
The bounded summary is mode 0600, SHA-256
`c79bef2f92d47df876def6ae8fab9a3f6a277ab37cad8de03ca1903ae0c70f2b`.

The frozen rule SHA-256
`a41dbb8c45e9771650a39f58746e9698ec64a64aaee4dcf9301af5bb0b2f4d1c`
returned **NO-GO** because diagnosis, evidence, freshness and verification were
below 12/12. The gate result is mode 0600, SHA-256
`9887eb08f1260d2ecbc7aa802a2b7ae270c489e81a0e0f42537ecf004861bf59`.
Authority remains `not-granted`.

Candidate-E is spent. No role, route, tool, deployment or connected pilot is
released. The next work is offline prompt/contract correction based only on
the failed development dimensions; there is no automatic rerun.
