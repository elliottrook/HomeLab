# M3 K2 sealed-evaluation scorer boundary — 2026-11-06

## Outcome

The conditional K2 sealed-evaluation scorer is source-ready without opening
the retained R5 evaluation. It accepts only the exact accepted evaluation
SHA-256, fixed preregistration metadata, exactly 32 unique cases, all 16 frozen
labels exactly twice, exactly 32 model requests, zero retries/errors and a
proven restored production state.

It independently reapplies the frozen K2 consensus policy to every result.
The release floor is at least 31/32 exact with zero unsafe false routes and
zero routed privacy underclassifications. A lower-quality complete transaction
produces `reject`; changed identity/counts, malformed results, duplicate cases,
response errors or failed restoration fail closed.

The local scorer first emits content-free metrics without claiming restoration.
A separate reconciliation function converts those metrics into the M6 score
contract only when an exact registered workload terminal record proves 32
requests, zero retry/error, matching result digest and production restored.
Request text, per-case predictions and private key material never enter the
shared score. Five focused tests pass. No model or sealed case was accessed by
this source-only work.
