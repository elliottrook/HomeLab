# D4 tool-free development attempt 2 — 2026-10-24

## Result

The explicitly approved corrected run at digest
`d61be2b4165a19498808226e2b2118dddd1899b379d87997d0ff098232657d2e`
completed its fixed twelve-session schedule on the accepted Qwen3.5-9B
Q4_K_M / llama.cpp b11429 / SYCL service. It is a **model-contract NO-GO**.

- 12 sessions started and 12 finished.
- 12 first calls completed with `finish_reason=stop`; no retry ran.
- Every engine result was `invalid_answer`; zero responses reached an accepted
  terminal state and zero simulated checks were accepted.
- Completion latency was 2.367–2.791 seconds and total recorded engine time was
  30.987 seconds.
- No reasoning output or tool call was present. No effect was accepted.
- The service remained authenticated, idle and healthy; `aster-llama` stayed
  active/running with zero restarts and the lease returned `ready`.

The immutable owner-only journal remains at
`/root/aster-d4-development-evidence-20261024/attempt-2-ledger.jsonl` in
LXC104, mode 0600, SHA-256
`7ab864b7e96914a25aaf13651a3be65f86b2206683aba299d53582e93db7c28c`.
Temporary source packages were removed from LXC104 and Proxmox after capture.

## What the evidence proves

The observed-evidence enum correction prevented the prior
`unobserved_evidence_rejected` outcome, but every first response then failed
the answer-shape boundary. The retained journal deliberately discarded the
malformed body. It therefore proves the common phase and bounded status, but
cannot distinguish invalid JSON from a wrong object field or type. Reading
model text from service logs would bypass that retention boundary and was not
used.

This is not a model-quality score and does not support a routing, role, tool or
runtime promotion. It identifies an observability gap in the development
contract: rejected answer bodies need a closed, content-free parse/shape
classification so one malformed response can diagnose the request contract
without exposing or retaining model text.

## Corrective candidate

The offline candidate adds closed parse and answer-shape classifications to
the transport and journal validators. It also provides a one-case, one-call
diagnostic probe that retains only the classification, timing and existing
bounded metadata. It never retains model text, reasoning or credentials. The
complete evaluation suite passes 147/147.

The exact probe digest is
`04774564801ebc0f21347d44fbdec53cbca7555bb0b90b70dff7859eee779873`.
It subsequently ran once with separate approval and measured a duplicate
evidence-ID failure; see the
[probe result](D4-one-call-contract-probe-result-2026-10-24.md). That result
supports a specific contract correction, but cannot qualify D4 or authorize
another twelve-case run.
