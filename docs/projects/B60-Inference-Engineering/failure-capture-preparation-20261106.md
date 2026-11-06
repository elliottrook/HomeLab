# Failure capture after the actual R2 trial — November 6 preparation

Preparation-only heartbeat: no host/guest probe, model/GPU call, benchmark,
mount, download, service/timer/configuration change, credential read or lease.
The real35B R2 result remains FAILED_RESTORED with its original uncertainty.
The newly observed News-XPU post-release delta is preserved; its owner receipt
and consumer/scheduler integration remain an owned question already published.
No new peer response or inferred delivery is claimed.

The real R2 collector lost partial per-request metadata when a later request
raised. Added an undeployed capture core that preserves every attempted row,
including explicit length finish, HTTP/protocol errors, timeout, oversize,
transport failure and invalid/late clock cases. It retains earlier successful
metadata when a subsequent request fails. Planned versus actual call counts,
zero retries, missing token fields as unknown and fixed error enums are explicit.
No exception text, response body or hidden reasoning is returned. Metadata may
include counts, timing and a valid final-answer digest; hidden reasoning text
or its digest is never retained. Empty/truncated/unsupported finishes are not
accepted as usable answers, and late responses cannot become timing wins.

The exact R2 request-source SHA256dbc596c5b77a8ea9359868798d621ff951c331754b2b4968c177b80d079e3dca
is checked before interpreting its public fixed payload definitions. Its run(),
main() and key reader are never called. Drift is rejected before interpretation.
The two prompts,1024-token cap and60s bounds are unchanged; there is no model
or effort tuning. Transport and clock are mandatory injected dependencies, with
no endpoint/key/CLI/network default. This core grants no live authority.

Nine focused fake-backend tests cover second-request token limit with preserved
first row, timeout/no retry, HTTP/malformed/oversize/invalid types, exception and
finish-string sanitization, empty final, deadline overrun, invalid clock before/
after a call, genuine fixed payloads and pre-interpretation source drift denial.
All160 B60 tests pass against the exact controller root
/private/tmp/b60-resource-checkpoint-20261104/scripts/local-ai. No fake fixture
is treated as a model result, semantic review, human approval or qualification.

Next integrate a reviewed bounded source-local transport/key shim and durable
packet storage into a **new** source-bound adapter/card. Persist the packet
before turning failed outcomes into runner failure; otherwise the host's
nonzero-exit handling would still discard it. Do not modify deployed R2 sources,
replay spent bookings or widen output budgets from this preparation heartbeat.
Actual next trial still needs current News consumer/schedule reconciliation,
fresh entry/resource/backup admission and a real booked independent runner.
Fresh9B complete-useful-answer baseline and harder held-out contract precede
tuning; final capability/p50/p95 acceptance remains open. No new conversational
approval is missing for this safe source work. No background execution claim.

## Exact authoritative read receipts

| Commit | Path | SHA256 |
|---|---|---|
| 1f1489554e1d70688c6f777ee0ef68e19600cffc | docs/projects/AI Projects/evidence/Stream-A-24-hour-progress-report-2026-11-06.md | 7946d0cfbf83072ff347d5c08abfaa7cbf2853ae1286f79bb49be1a924b8500e |
| 55888a388ac6b2e1b3968c4a21509648711b346b | docs/projects/B60-Inference-Engineering/actual-35b-model-result-20261106.md | 974f0f1332bda693ab626be074cb2bbb45690ac96d9e2ca4121ba99f5780c19f |
| 6fb0207fec5190e0c34ed3bc72ea38e128f06127 | docs/runbooks/Local-AI-Lease.md | 064b56ee8fca8aad37e9ae627cf119c581c3f8d8ad7d9782ccfeb0fa23b31d4c |
