# D4 tool-free development attempt 1 — 2026-10-24

## Result

The exact production-compatible development run at digest
`6299c6b285a440607d5da31790ff7af4275a613c4fdaac97e4bea6a3a2999267`
completed its fixed twelve-session schedule on the accepted Qwen3.5-9B
Q4_K_M / llama.cpp b11429 / SYCL service. It is a **model-quality NO-GO**.

- 12 started and 12 finished journal sessions.
- 12 model calls; the 36-call ceiling was not approached.
- All requests returned `finish_reason=stop` in 2.303–3.391 seconds.
- All 12 engine results were `unobserved_evidence_rejected`.
- No simulated check was accepted, no final advisory answer was retained and no
  effect was claimed.
- Total recorded engine time was 33.370 seconds.
- The exact run digest is present in all 24 hash-chained journal rows.

The immutable owner-only journal remains at
`/root/aster-d4-development-evidence-20261024/attempt-1-ledger.jsonl` in LXC104,
mode 0600, SHA-256
`a6239704b73408845bf912d74cb1e27ee0b48cc25ef602b927b9eabbdaf93b7d`.
Temporary executable sources were removed after capture.

## Failure analysis

The request schema allowed any string in `evidence_ids`, while the engine
correctly accepted only identifiers already present in the current observation
set. Every first response crossed that boundary. The raw rejected answers were
deliberately discarded, so the evidence supports the error class and phase but
does not support a claim about the precise invented identifier text.

This is development evidence and may be used to correct the request contract.
It is not a reason to weaken the engine's observed-evidence check. The offline
candidate now enumerates only currently observed IDs in the constrained JSON
schema on every step; the independent runtime check remains as defense in
depth. Tests prove the enum grows only when simulated evidence is revealed.

## Recovery and next candidate

Postchecks found the accepted service active/running with zero restarts, the
lease state ready, Aster Agent and Speech active, and no temporary run package.
No service, runtime, model, key, lease, firewall or schedule changed.

The corrected candidate has exact run digest
`d61be2b4165a19498808226e2b2118dddd1899b379d87997d0ff098232657d2e`.
Its isolated-package import test and complete evaluation suite pass 142/142.
It remains dry-run only. A second model attempt requires new exact approval;
there is no automatic retry.
