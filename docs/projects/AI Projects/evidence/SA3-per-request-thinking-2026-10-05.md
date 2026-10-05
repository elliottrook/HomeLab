# Per-request thinking and workload separation

Status: source-verified mechanism; offline request candidate tested; no model calls.

## Evidence

Read-only invocation of the running LXC 110 executable's version command confirmed
build 11081, commit `161755f29`. The corresponding primary source
[server-common.cpp](https://github.com/ggml-org/llama.cpp/blob/161755f29/tools/server/server-common.cpp#L1336)
applies `chat_template_kwargs.enable_thinking` per request over the default.
At lines 1386–1399 it accepts `reasoning_budget_tokens` (or
`thinking_budget_tokens`) and uses the service budget only if the request value
is -1. A zero service default need not force every request to zero when a positive
request budget is supplied. Budget handling depends on recognized template thinking
end tags. The loaded template's behavior remains to be tested.

[Pinned server documentation](https://github.com/ggml-org/llama.cpp/blob/161755f29/tools/server/README.md#post-v1chatcompletions-openai-compatible-chat-completions-api)
also describes per-request template parameters and disabling reasoning with effort
none. Merely changing reasoning_format does not disable generation. The candidate
sets an explicit boolean and budget together and does not send a conflicting effort.

`sa3_fair_request.py` builds paired requests offline, with identical case, catalogue,
prompt and answer schema, and 1,024 answer-token headroom plus zero or 1,536 thinking
tokens. Combined limits are hypotheses about practical capacity, not measured
guarantees. It has no network client, secret handling or automatic routing.

## Proposed operating profiles

| Request | Preferred path | User experience |
|---|---|---|
| Turn lights on | Authorized deterministic Home Assistant action | Prompt response, independent of GPU |
| Weather | Approved current-data skill, concise formatting | Fast; report stale/unavailable data honestly |
| Run Lab Doctor | Fixed diagnostic job | Acknowledge quickly; deliver result when complete |
| Is SABnzbd up? | Registered read-only health check | Return precisely what was checked; deeper diagnosis only if needed |
| Fix ARR stack | Thinking-enabled investigation | Acknowledge, gather evidence, propose bounded repair; separate authority gate |
| Organise email overnight | Scheduled bounded workflow; reasoning where useful | Draft classification/proposals under approved data scope; mutations need their own authorization |

This is an architectural proposal, not evidence that these integrations are all
deployed. A fast acknowledgement is not task completion. Even Doctor can be slow
without any model reasoning. A simple recurring email rule may need no model at all.

## Independent controls

Choose capability, thinking budget, interactive/background priority, privacy and
permission scope separately. Overnight scheduling does not grant new permissions.
Do not let a model increase its own budget or privileges. Use bounded escalation,
deadlines, explicit cancellation and durable progress, with no blind action retries.

The current service has one inference slot. A queue priority cannot preempt a
generation already occupying it. Keep deterministic controls outside that queue;
split background model work into bounded requests and yield between them. Initially
schedule large jobs outside interactive windows. Verified cancellation or isolation
is required before promising immediate interactive LLM answers during background
inference. Do not add another server or hardware without evidence of need.

## Next bounded verification

Prepare one synthetic development incident and run a serial off/on smoke pair only
under the connected-run gate: same prompt, no tools/private corpus, positive bounded
thinking budget, service health/load precheck, hard timeout, no retries or config
change. Keep only final answer, latency, finish reason and aggregate reasoning-field
presence/length or trustworthy token metadata; discard reasoning content. Absence
of reasoning metadata is inconclusive unless parser/template behavior is verified.
If the override is ignored, stop and investigate; do not restart production or call
the candidate thinking-enabled. Confirm answer-schema compatibility and context
headroom before any held-out comparison. This smoke pair is not yet run.
