# SA3 connected synthetic development run — 2026-10-12

Status: **development evidence only; not a holdout result or promotion gate**.

Jason approved this bounded run after the Local AI lease was released. It used
the existing authenticated Qwen endpoint with two public synthetic incident
fixtures, no private data, no tool execution, no effectful adapter and no
runtime/configuration change. Each session retained the existing three-call
and 300-second limit and the runner stopped on contract or transport failure.

| Session | Result | Calls | Elapsed |
|---|---|---:|---:|
| `dev-service-stopped`, non-thinking | Rejected: cited an observation before it had been returned | 2 | 5.314 s |
| `dev-service-stopped`, thinking | Concluded from the simulated parser error and current stopped state | 3 | 88.600 s |
| `dev-evidence-unavailable`, thinking | Correctly clarified that cause and current state were indeterminate | 3 | 89.421 s |
| `dev-evidence-unavailable`, non-thinking | Rejected: cited an observation before it had been returned | 1 | 2.722 s |

The run made nine model calls in total. No tool calls, effects, restarts or
production changes occurred. The post-run idle check passed, and the Aster,
llama.cpp and speech health checks all returned healthy. Temporary runner and
fixture files were removed from the host and LXC 104 afterward.

Interpretation: the thinking configuration completed both synthetic cases but
was slow, while non-thinking violated the evidence-order contract in both
cases. This is useful development evidence only; it does not qualify Qwen for
sysadmin operation, establish held-out quality, or authorize promotion.
