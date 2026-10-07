# D3 live stop result — reporting failure, diagnostic retest gate

## What the approved test established

Jason approved manifest `7fcad97583ef0092c76de9c101b9182d7eff7fb8cb47fee407c8b5b1362182c3`.
Ran once from `96306cf`. The [worker result](D3-stop-result-2026-10-06.json)
reported `unknown` after 0.075 seconds, stop requested, stop unconfirmed, no
answer and no usage. The process exited normally because the worker deliberately
returns an uncertain result on exceptions; exit zero is not a passed experiment.

A fresh restricted app-server connection read the exact saved thread/turn with
no new inference. [Recovery evidence](D3-stop-recovery-2026-10-06.json) confirms
one dispatch, one matching turn, provider state **interrupted**, only a userMessage
item, and no final answer. The original worker ledger and owner view remained
unknown. Preserve that original failure rather than replacing it with a pass.

Conclusion: remote interruption is verified by later inspection, but the live
confirmation/reporting path **failed acceptance**. The evidence does not establish
whether the interruption followed the requested RPC or subsequent app-server
shutdown, nor which operation raised the swallowed exception. No invented root
cause, model rerun or production change is justified by this record.

## Offline investigation and local change

Two local reproductions used the installed Codex app-server against an explicitly
verified loopback fake Responses provider with `requires_openai_auth=false`,
zero retries and disabled tools. They involved no real model inference. The
basic Session/interrupt flow and the assembled owner-route worker flow both
reported interrupted successfully. The latter completed in 0.182 seconds with
no observed worker exception other than normal coroutine StopIteration events.
This does not reproduce the native-provider failure and is not proof of a fix.

Added only bounded diagnostic output to the worker failure result: a fixed
operation-stage label, allowlisted exception class and whether the interrupt RPC
returned normally. A typed RPC rejection retains its integer protocol error code,
never the provider error text. No prompt, credential or hidden reasoning is logged.
143 Python tests and five renderer scenarios pass, including secret-text exclusion
and protocol-code retention. There is no claimed root-cause repair yet.

## Exact next approval — one instrumented stop test

Approve one repetition with diagnostics, not an automatic retry under the consumed
approval. Same fictional Orion prompt, ChatGPT subscription, `gpt-5.6-luna`, medium
reasoning, owner stop immediately after running acknowledgement, no tools and no
real lab context. One turn maximum. Gateway/owner remain local test fixtures.

[Prepared manifest](D3-stop-diagnostic-manifest-2026-10-06.json):
`341df1d732973b5cbdb6842108c7f4feb0e03ed6c91493934aa831c653b07b11`

```text
/private/tmp/aster-delegation-gateway-py311-20261006/bin/python services/aster-agent/delegation/assembled_pilot.py --cancel-after-ack --run --approved-sha256 341df1d732973b5cbdb6842108c7f4feb0e03ed6c91493934aa831c653b07b11 --output-dir /private/tmp/aster-d3-stop-diagnostic-20261006
```

Fingerprint and fresh output directory are mandatory. All previous scope and
deadline bounds apply: one turn, no tools or paid API fallback, 180-second target
plus bounded RPC/stop grace, no production deployment, credentials or Git push.
After the run, inspect the existing saved turn without creating another one.
No automatic repeat whether this passes, fails or races normal completion.

Passing requires a provider-confirmed interrupted state delivered by the worker,
no final answer and exactly one turn. A repeat failure is useful only if it
identifies the failing stage/category; retain that evidence and investigate
locally. A successful repetition alone does not explain the first failure or
establish a reliability rate. Provider completion before interruption remains
inconclusive, and lost confirmation remains unknown.

This approval is needed because it creates a new cloud turn. The previous
approval is consumed. Await this specific decision; no production credential or
service change is requested, and no additional authentication canary is needed.
