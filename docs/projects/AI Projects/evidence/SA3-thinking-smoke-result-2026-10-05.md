# Per-request thinking smoke result

Date: 2026-10-05
Status: two authorized synthetic requests completed; mode toggle demonstrated.

## User-facing result

The existing local model can change between thinking off and thinking on for each
request without restarting the server. Thinking was substantially slower on this
example. Both answers proposed fresh evidence collection, not a completed diagnosis.
This is a mechanism check, not a sysadmin qualification or proof that thinking
improves outcomes.

## Authorization and containment

Jason explicitly said “Please run them” after the proposed serial pair, four-minute
timeout per request, no tools or configuration changes. The run used the existing
LXC 110 service and its authentication entirely inside the guest. No credential,
raw process environment or private reasoning content was returned or retained.
No private incident data, held-out answer keys, cloud calls or tool execution.
The Python runner was sent on SSH stdin; no runner/result files were written on
the Proxmox host or guest. No retry occurred.

The service health endpoint and processing metric established healthy/idle before
the pair. Health passed after each response; the service PID remained 89. This
does not prove there was no competing request during inference. No restart, model
reload, configuration edit or privilege change occurred.

## Reproducibility

- Request builder at `3f6d4e0`, SHA-256
  `4178af9ea0da8b92780632b0f6c0719c14d6f9eaf3d628e5022c2a7594caf59c`.
- Smoke runner SHA-256
  `2512109fef458ae1ed0846cde58692ca943f0b1ea430a201d2a214a56972f649`.
- Both requests additionally set `reasoning_format: deepseek`; that field is now
  incorporated in the offline builder. This separates reasoning from final content,
  not a reasoning enable/disable mechanism.
- Same model selector `qwen3.8-27b`, temperature zero and visible three-capability
  catalogue: current service status/port, recent bounded service logs, client DNS.
- Synthetic symptom: a media web page times out at 10:00; yesterday's report says
  the service was running; another application on the host responds now; there is
  no current port, log or backend-health evidence. No cause should be claimed.
- Off: thinking false, reasoning budget 0, maximum output 1,024 tokens.
- On: thinking true, reasoning budget 1,536, maximum output 2,560 tokens.
- Same system instruction and JSON answer schema from the builder; serial off
  then on, no counterbalancing/repetition. Timeout 240 seconds per request.
- Server previously verified as build 11081 / `161755f29`. Full model-shard hashes
  and a release-quality environment manifest remain missing; not a benchmark release.

## Observed metadata

| Measurement | Thinking off | Thinking on |
|---|---:|---:|
| Wall time | 24.431 s | 158.706 s |
| Finish reason | stop | stop |
| Separate reasoning field nonempty | no | yes |
| Reasoning characters (content discarded) | 0 | 4,657 |
| Final-answer characters | 647 | 541 |
| Prompt tokens | 267 | 303 |
| Completion tokens | 147 | 1,051 |
| Cache tokens | 0 | 0 |
| Prompt processing | 2,372.732 ms | 2,529.315 ms |
| Generation | 21,520.962 ms | 155,676.958 ms |
| Tool calls | 0 | 0 |

Completion counts are server-reported aggregate generation, not verified separate
thinking/answer counts. Mode-dependent prompt formatting changed token count even
though supplied evidence and instructions matched. No claim of isolated throughput,
reasoning-budget enforcement at exhaustion, or latency distribution is made.

Both responses were valid answer JSON with `outcome: clarify` and `effects: []`.
Off selected current service status and recent logs. On selected current service
status alone. Both recognized stale status information and withheld root-cause
claims. The thinking answer called the reported timeout “unconfirmed”; that wording
needs care because it was a supplied symptom, even though not independently checked.
This informal review is not blind grading and establishes no quality winner.

## Decision and next work

**VERIFIED:** request-level switching works for this loaded model/template and
the tested schema, even with the global off/zero defaults. Production defaults
remain unchanged. A visible reasoning field verifies mode behavior, not truth or
usefulness of its contents.

**ARCHITECTURAL INFERENCE:** keep predictable operations outside inference; reserve
thinking for tasks where measured quality justifies delay. The thinking request
exceeded the two-minute routine-triage target on this one sample; it remained below
the five-minute complex-investigation bound. One sample establishes neither p95
latency nor broad feasibility.

Next safe local work: finish the synthetic multi-step investigation simulator and
development fixtures, including stale evidence, competing causes and insufficient
information. Then freeze a paired quality protocol and fresh test set under the
existing gates. Do not enable reasoning across production or launch further model
requests from this two-request authorization. Doctor recovery remains separate.
