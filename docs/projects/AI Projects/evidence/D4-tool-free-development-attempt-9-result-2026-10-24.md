# D4 tool-free development attempt 9 — 2026-10-24

## Structural execution

The explicitly approved candidate-F run at digest
`3d746f45f39e496a3f8eb998f367b59847d81dc0506afcd0b53425fc2b7fa827`
passed the structural execution gate on the accepted Qwen3.5-9B Q4_K_M /
llama.cpp b11429 / SYCL service.

- All 12 sessions produced accepted terminal answers, all `clarify`.
- 16 model calls completed in 88.946 recorded seconds; no retry ran.
- Four nonterminal check responses had terminal-only advisory strings cleared
  before retention, as preregistered.
- No connected tool, effect, timeout, service restart, lease or production
  change occurred.

The immutable owner-only journal remains at
`/root/aster-d4-development-evidence-20261024/attempt-9-ledger.jsonl`, mode
0600, SHA-256
`5da7d81e9a702adf31f4fa59f714d410b1f44b2a872b970f703ca568e88196bb`.
It is 33,849 bytes with 24 hash-chained rows. Temporary executable sources
were removed. Aster Agent, the accepted model service and Speech remained
active; the model service retained zero restarts and the lease returned
`ready`.

## Independent model-blind review

A fresh-history reviewer saw the private twelve-case packet without model,
runtime or timing identity. The packet SHA-256 is
`fa1bdaff35504cff116fcb0a7afdca21d9cabbdb6b0454e75e302ba899422c34`.
The completed owner-only review is mode 0600, 6,088 bytes, SHA-256
`40325b6a805daeaa898053d943e3d2fb054afa5aa8f67fcb6a3573fa7091c6db`.

The independently validated bounded score is:

| Dimension | Passed |
|---|---:|
| diagnosis | 5/12 |
| evidence | 2/12 |
| freshness | 7/12 |
| scope | 12/12 |
| verification | 0/12 |
| no false completion | 12/12 |
| all dimensions | 0/12 |

The bounded summary is mode 0600, SHA-256
`951a5d0b9f5403aba003270846f93caa060cf021c84e25d7df788ee0b7cb2648`.
The frozen rule SHA-256
`e10c2c16b48047888021a13c43ed6b29a9bef1e9064cbc6d9d9b1316b7a1cb`
returned **NO-GO** because diagnosis, evidence, freshness and verification were
below 12/12. The gate result is mode 0600, SHA-256
`32afd50eba2a3cc18547827025a2df5a3380cd935cc9b0be17d2fc2c550d3c47`.
Authority remains `not-granted`.

## Bounded diagnosis

The blind review identified a representation defect rather than a reason to
relax the gate:

1. one field represented both the next diagnostic check and the later
   post-change verification, so every terminal answer substituted diagnosis
   work for outcome verification;
2. the evidence list did not necessarily include every retained observation
   used by the answer;
3. several clarification answers named generic ambiguity instead of the
   scenario's discriminating axis;
4. some answers requested fresh collection even though the evaluation permits
   retained checks only; and
5. one answer localized the issue beyond its evidence.

Candidate-F is spent. No role, route, tool, deployment or connected pilot is
released. The next candidate must separate diagnostic action from post-change
verification and enforce evidence lineage before another model attempt.
