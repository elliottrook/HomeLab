# M3 — minimal preload comparison, first result

Date: 2026-09-25. **Controlled preload experiment complete; retain Aster for now.
M3 as a whole remains open.** No production migration, live inference or remote
publication occurred. This is not a quality comparison.

## Bounded dependency decision

After preregistration, HEAD metadata checks showed the 17 pinned wheels total
**5,446,375 bytes**. This was assessed as the explicitly requested minimal local
PydanticAI experiment, not a major platform installation: one disposable temporary
venv, no optional extras, no provider SDK, no service, no credentials, no change
to any existing or production environment. Hash-checked wheel-only installation
used the public PyPI index with isolated pip configuration and `--no-deps` against
the complete resolved lock. The resulting environment occupies 46,000 KiB on disk.

Environment: `/private/tmp/aster-adaptive-pydanticai`, Python 3.12.14,
PydanticAI slim 2.51.0, Pydantic 2.13.4. See the retained
[hashed lock](M3-preload/requirements.lock). It can be discarded without production
effect and rebuilt from that lock. No permanent framework dependency was added.
Telemetry is off, no optional capabilities/tools are registered in the preload
profile, non-test model requests are disabled, and socket connections are blocked.

## Method and compatibility correction

Both paths use the same Aster source-slice preload and the exact same system and
user text. Aster awaits a fixed async response; PydanticAI constructs a minimal
Agent with FunctionModel and awaits the same fixed response. Both have one scripted
response and zero real model calls. No function tools are exposed to the candidate.
The candidate callback asserts exact instruction/user-context equality.

Each process ran ten warmups and 200 retained samples for each of four fixed cases.
Independent fresh processes ran in Aster → PydanticAI → PydanticAI → Aster order.
This ABBA block order differs from the preregistered within-case alternation so
whole-process RSS can be compared without candidate imports contaminating Aster.
The difference is explicit; do not infer small timing differences statistically.
No performance tuning was applied. Creating an Agent per request is included.

The first candidate smoke invocation rejected an outdated `instrument=False`
constructor argument. Inspection of the installed 2.51.0 signature led to explicit
`capabilities=[]`; the package reported observability off. This API compatibility
correction happened before any successful candidate timing. The incomplete initial
baseline was rerun with the corrected evaluator. No failed candidate result was
silently counted as a pass. The second repeat suppressed only the optional startup
banner through `PYDANTIC_AI_NO_BANNER=1`; warmup excluded it in the first run.

## Results

| Case | Aster p95 ms, runs 1 / 2 | PydanticAI p95 ms, runs 1 / 2 |
|---|---:|---:|
| No tool | 0.008 / 0.008 | 1.008 / 0.977 |
| One read | 0.008 / 0.009 | 0.966 / 0.965 |
| Two reads | 0.012 / 0.015 | 0.965 / 1.002 |
| HA read | 0.013 / 0.013 | 1.078 / 0.969 |

Whole-process peak RSS: Aster **47.11 / 47.08 MiB**, PydanticAI
**69.00 / 69.06 MiB**. The incremental peak was approximately **22 MiB**.
Raw aggregate records, source/dataset/evaluator hashes, import time and context
bytes are retained in [M3-preload](M3-preload/pydanticai-1.json). Actual token counts
remain null; FunctionModel's synthetic usage is not a tokenizer measurement.

Four additional PydanticAI checks pass: no exposed tools/one response; unknown
shell tool denial; malformed unavailable tool denial; deadline cancellation of a
pending scripted response. The 26 adaptive contracts/HTTP tests and 89 existing
Aster tests also passed before comparison. These checks do not replace all planned
M3 conformance, tool-loop and recovery cases.

## Decision and remaining work

The preload candidate stays within the preregistered +5 ms p95 and +100 MiB
controlled-overhead guardrails. **Passing guardrails does not establish a benefit.**
It retains Aster's preparation logic and adds a dependency/loop layer without a
measured correctness or maintenance gain on these simple fixtures. Retain the
existing Aster runtime; do not migrate based on this experiment.

Next M3 work: test the explicit tool-loop profile only if it can demonstrate a
concrete validation/retry/structured-result maintenance benefit; keep its extra
round trips separate. Complete adverse conformance, cancellation/restart, resource
and provider compatibility coverage before any live comparison. A routing challenger
and frozen routing corpus remain separate unfinished M3 requirements. LangGraph
still has no demonstrated need and remains uninstalled.

M1 review and deployment remain open. M2 is complete for its offline contract/
baseline scope, not live behavior. The retained baseline and candidate comparison
are local checkpoints; pushing these newer commits requires a new explicit push
instruction. No B60 Stream M operation was undertaken.
