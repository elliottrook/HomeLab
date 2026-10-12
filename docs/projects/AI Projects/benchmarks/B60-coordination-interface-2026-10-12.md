# Aster Adaptive / B60 benchmark coordination interface

**Status:** Local coordination proposal, 2026-10-12. No production, policy,
tool or GPU-lease change is authorized by this note. The B60 request delivered
by Jason is a proposal; its named successor programme files were not available
in this checkout at review time, so the new lease window and 04:15 restoration
deadline require reconciliation with B60's authoritative project record.

## Ownership and integration

- **Aster Adaptive owns the task bar:** request classes, capability vocabulary,
  safety and privacy constraints, scoring protocol, outcome measures and the
  route/role promotion decision. It supplies fixed inputs and receives
  content-free results plus pinned provenance. It does not dictate B60 runtime
  engineering choices.
- **B60 owns candidate stacks and measurements:** exact model, quantization,
  runtime, reasoning mode, hardware, load/cache state, repeated latency and
  stability observations. A candidate stack is evaluated against Aster's
  versioned bar. B60 performance does not grant Aster tools or alter policy.
- **The shared lab lease owns exclusive GPU access:** neither project infers an
  exclusive slot from a benchmark request. Production restoration is checked
  against the current lease record before and after tests.

## Existing reproducible route-development contract

The current interface is the [Aster Ask development benchmark](ask-routing-development-v1/README.md).
It uses `aster-ask-backend-manifest.v1` and the independent
`aster-ask-route-score.v1` scorer in
`scripts/aster-adaptive/ask_route_benchmark.py`. The immutable synthetic fixture
SHA-256 is `c797533494119e44c9c927d5b9b274ccd6426cacd50ca7cd93391861c0663cec`;
the first local 9B/SYCL run SHA-256 is
`20d75242c9057008eeaa99ca2749eb17845334424debbe6cc65673c8ddf47303`.
The scorer source SHA-256 at this checkpoint is
`d8d5641dde28bf8e3b94ed180ef4e994d516a7644d459d6adb6c0cd3b7f41f6a`.
The model artifact, runtime unit, prompt and adapter hashes are pinned in the
[local baseline manifest](ask-routing-development-v1/local-9b-sycl-2026-10-12.manifest.json).
The benchmark's first implementation commit is `872117f`; label-blind backend
compatibility was fixed in `d913043`. Forgejo and its GitHub mirror both
reached coordination commit `828c683` on 2026-10-12.

The current run is **one warm, lightly loaded, serial attempt per case** with
no retries: 30/30 valid, 18/30 exact status-plus-capability matches; inside-
container request latency p50 0.634 s and p95 0.705 s. It does not report a
completed useful answer, cold-cache behavior, load sensitivity, or a stable
population p95. These values must not become an automatic budget for a 27B+
reasoning-on stack or an assertion about production answer quality. They are
the first fixed regression observation.

The ten route families are timer, Home Assistant, media, stable facts,
calendar, live web, calendar-plus-web, HomeLab read, ambiguous and private
context. The test uses no tools, no real personal context and no infrastructure
action. Its capability proposal is subordinate to deterministic privacy,
identity, approval and tool policy. The exposed fixture can detect regressions,
but cannot qualify a model for automatic routing. Its answer key is already
public in the repository; no hidden answer key exists for this 30-case set.
The existing lexical rules also have a pinned [30/30 development run](ask-routing-development-v1/README.md)
on this fixture. The rules and cases were authored together and ran on a
different host; this is a cheap control, not an independent model comparison
or an equivalent latency measurement.

## Separate qualification lanes

The [completed-answer protocol draft](completed-answer-qualification-protocol-v0.md)
develops these lanes into a proposed common test boundary; its datasets,
budgets and release floors remain unapproved and unmeasured.

1. **Route proposal:** same versioned request text, capability vocabulary,
   output contract and tool-free scope across eligible backends. Measure
   status/capability agreement, unnecessary clarification/abstention, missing
   and extra capabilities, validity and latency by class.
2. **Completed answer quality:** define new class-specific observable success
   conditions, evidence freshness and appropriate abstention. For a B60 stack
   this must measure *completed useful answers*, including prompt, generation
   and any allowed retrieval; a route proposal alone is insufficient.
3. **Grounded reasoning, privacy and tools:** use separate cases for personal
   context locality, source quality, tool-call shape and denial behavior.
   Tool execution and authority remain outside the benchmark unless a later
   approved, bounded operational test explicitly includes them.
4. **Operational shadow and canary:** after fresh qualification, compare a
   challenger without changing execution, then make only a reversible,
   class-specific release decision under the normal Aster gates.

For a future candidate, freeze the dataset, scorer and policy versions before
running it; record their hashes along with model, quant, runtime, prompt,
adapter, reasoning setting, tool mode, egress, hardware, cache state, load,
sampling count, failures and cost. Keep development examples visible for
debugging and new qualification keys in restricted custody. The old S1 corpus
closed incomplete and is not a qualifying holdout. No new holdout is asserted
to exist here.

## Gaps to close before a joint release bar

| Requested item | Current answer | Required next evidence |
|---|---|---|
| Per-class quality floors | **UNKNOWN / not frozen.** Three published cases per family are too few. | Fresh, independently labelled cases with adverse privacy/locality examples; preregistered hard safety floors and error costs. |
| Per-class p50/p95 completed-answer limits | **UNKNOWN / not frozen.** Only route request latency is measured. | Measure accepted Aster workflows on the current control under declared cold/warm cache and shared-load profiles; set user-facing budgets before finalists. |
| 27B+ reasoning-on at 9B latency | **Experimental hypothesis**, not a release requirement proven feasible. | B60 measures exact finalist stacks on equivalent useful-answer workloads, with uncertainty and resource cost. |
| Codex comparison | **PENDING.** D3 manual pilot used different questions and emitted no Decision record. | Reviewed consent and a subscription-compatible no-tool adapter; pin model/effort when exposed. Do not treat this Codex chat as an Aster backend result. |
| Two finalist sessions | Useful engineering replication, **insufficient by itself** for rare safety failures or a defensible p95. | Report sample size and uncertainty; require zero observed mandatory-boundary violations plus independent checks, then shadow/soak before class-specific promotion. |
| Shared lease and 04:15 restore | **REQUIRES VERIFICATION.** Current checkout still contains older B60 timing. | Reconcile the newer B60/platform lease documents and live schedule before any exclusive test. |

The eventual promotion packet should name the exact stack and *earned request
classes*, control comparator, qualifying dataset and scorer versions, quality
and latency distributions, safety exceptions, GPT fallback, resource impact,
recovery/soak observation, rollback and Jason's decision. A new control must
retain the original budget as a recorded comparator; it must not silently
weaken it. Automatic local routing remains off until its own gate passes.
