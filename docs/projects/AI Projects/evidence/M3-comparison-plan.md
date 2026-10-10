# M3 — preregistered minimal harness comparison

Date: 2026-09-25. Status: **prepared, not run**. No candidate performance results
were observed before these criteria. Owner: Jason. This is a local synthetic
comparison envelope, not adoption/deployment authority.

## Question and alternatives

Does minimal PydanticAI improve contract handling or maintenance enough to justify
its dependencies and overhead for the existing bounded Aster use case?

Baseline: current Aster at source SHA-256
`8777687ce97055d2db3254aa6b30ddf37fc61e73dac2bd18008cbea3fef1a8b6`.
First challenger: `pydantic-ai-slim==2.51.0`, with Pydantic 2.13.4 held constant.
No provider extras, hosted tracing, coding harness, shell, MCP, persistent memory,
CLI, service or production credentials. LangGraph remains conditional on a
workflow need not served by the baseline; it is not installed for completeness.

Official sources checked 2026-09-25:

- [Installation](https://pydantic.dev/docs/ai/overview/install/) distinguishes the
  broad default package from the selectively installed slim package.
- [Testing](https://pydantic.dev/docs/ai/guides/testing/) documents scripted
  `FunctionModel` responses and `ALLOW_MODEL_REQUESTS=False` for non-test models.
- [Slim package metadata](https://raw.githubusercontent.com/pydantic/pydantic-ai/main/pydantic_ai_slim/pyproject.toml)
  shows base graph, HTTP and telemetry API dependencies. The retained PyPI
  resolution pins released artifacts; current main documentation alone does not.

The metadata dry run resolved 17 packages without optional extras. It includes
pydantic-graph, httpx2/httpcore2, pricing metadata and telemetry API packages even
without a provider. This is a real dependency cost, not “just a tiny decorator.”
The complete versions/hashes are retained under M2-integration. An isolated
candidate must not update any shared or production Python environment.

## Separate comparisons

1. **Equivalent preload profile:** same synthetic prompts and read results,
   deterministic capability filtering before the model, one scripted response,
   same system instruction and output semantics. Measures integration overhead
   without giving one candidate extra reasoning rounds.
2. **Explicit tool-loop profile:** fixed scripted proposals and responses for
   one/two reads, invalid arguments, denied tool and bounded retries. Report the
   additional round trips separately; do not average them into the preload case.
3. **Later local-model profile:** only after runtime/resource compatibility gate;
   identical model/version/settings and permitted tools, no production writes.
   Must measure actual prompt/output tokens, quality and queue/prefill/decode.
   Offline scripted responses cannot select a production winner.

The initial four M2 corpus cases retain their digest and serve as a smoke/control
set. Add separately versioned adverse fixtures for malformed schema, unknown tool,
principal/policy mismatch, expired projection, cancellation and budget exhaustion.
Freeze both fixture manifests before challenger timing. No real private data.

## Bounds and method

- At most 8 fixture tool attempts, 4 scripted response steps, 10 seconds per case,
  one active case, 64 KiB result envelope; no network model or tool request.
- No persistent traces containing prompts, results or identities. Store aggregates,
  explicit synthetic labels, source/package/schema/evaluator/dataset digests.
- Ten warmups and 200 paired samples per ordinary fixture, alternating order;
  independent repeats from a fresh process twice. Report p50/p95, per-case spread,
  calls, retries, serialized prompt/schema bytes and unknown token counts as null.
- Report cold process import and whole-process peak RSS separately. Existing slice
  timing excludes app startup and is not interchangeable with full-path timing.
- Keep fixed response scripts independent of candidate output. A harness validates
  structure; the script is not evidence of semantic intelligence or answer quality.
- Record implementation/review effort and dependency count. Equal maximum tuning
  budget: two local tuning iterations per candidate after conformance passes;
  retain failures and do not change fixtures to favor a candidate.

## Decision rules

All denial/isolation/cancellation/budget conformance tests must pass with no
unauthorized fixture execution. Failure means reject or fix within the tuning
budget, never loosen authority or evaluator requirements.

For the equivalent preload profile, a challenger must keep the same scripted
response count and stay within an added 5 ms p95 construction overhead per case
and 100 MiB incremental isolated-process peak memory versus the same baseline
measurement method. These are local experiment guardrails, not household SLOs.
Passing alone is not a reason to migrate: also require a demonstrable correctness
or maintenance benefit (e.g. removal of a tested custom validation/retry component
without weaker guarantees), documented for review. No claimed benefit means retain
Aster. A graph/tool-loop result is reported separately rather than used to disguise
preload overhead. Any live adoption still requires local-model quality evidence
and human review. Inconclusive and retain-baseline outcomes are valid results.

## Installation and stop boundary

No dependency installation has occurred for this preregistration. Before proceeding,
review the resolved 17-package footprint. If judged within the approved minimal
local experiment, use a fresh temporary venv, wheel-only pinned artifacts and no
extras; record disk size and environment manifest. Otherwise defer the challenger
and continue independent evidence-loop work. Do not install major dependencies
merely to produce a comparison, modify production runtimes, fetch personal sources,
or enable external telemetry. Model/production tests and expanded collection remain
outside this offline comparison step.


## Subsequent execution record

The bounded dependency footprint was assessed and the preload profile ran after
this plan. See [results and deviations](M3-preload-results.md). The plan above
remains the preregistration; later measurements do not retroactively change it.
