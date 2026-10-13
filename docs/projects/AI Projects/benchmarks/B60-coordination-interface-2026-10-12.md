# Aster Adaptive / B60 benchmark coordination interface

**Status:** Published interface; bidirectional B60 receipt confirmed on
2026-10-12. No production, policy, tool or GPU-lease change is authorized by
this note. The proposed recurring window and 04:15 restoration deadline still
require reconciliation with the live platform lease.

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
closed incomplete and is not a qualifying holdout. At this interface
checkpoint no new holdout existed; the later A1 v2 development baseline is
recorded below and still does not qualify a route.

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

## B60 response receipt and Aster acknowledgement — 2026-10-12

**RECEIVED:** Forgejo branch `codex/b60-adaptive-coordination` at full commit
`9b007602eeb5087fe759a52bc0f5e7d27b2264c2`, file
`docs/projects/B60-Inference-Engineering/coordination-response-20261012.md`,
SHA-256 `09a35c30fbcd2841058ed6da255e59600d31aea5e7a6ae3acb4b7ca63c6983cf`.
The file was read from a fresh single-branch clone pinned to that commit, not
inferred from Jason's summary or from a successful push alone.

**ACCEPTED:** B60's ownership boundary and four separate test lanes match this
interface. Its independent recomputation of the exposed routing development
baseline confirms 30 valid and 18 exact matches against the same fixture, run
and scorer digests. This is useful reproduction, not independent qualification.
The reported 0.634 s p50 / 0.705 s p95 is route-request timing under one warm
serial development run, not completed-answer latency. The 27B+ reasoning-on
at current-9B completed-answer speed target remains an experiment. B60's
accepted recovery stack is 9B/SYCL; no old Vulkan or 27B state is inferred.

**OPEN / no disagreement:** Aster still owes preregistered class-specific
answer rubrics, quality floors and latency budgets measured from accepted
current workflows; independently labelled qualification cases; a comparable,
consented Codex backend measurement; and verification of the shared host-level
lease. The [completed-answer protocol v0](completed-answer-qualification-protocol-v0.md)
is already a versioned draft with these decisions explicitly open. B60's
provisional offline gate is not adopted as Aster's release bar. The backup-
completion-to-04:15 window is agreed in principle only; neither team may
start an exclusive batch from clock time alone.

**NEXT HANDOFF:** Aster will keep the development key exposed and qualifying
keys separate, develop the completed-answer capture/scorer against synthetic
fixtures, and preregister the current-control measurement method before any
candidate comparison. B60 may integrate the published routing scorer for
engineering regression and return an exact current-stack measurement plan.
Both teams should inspect the other's named branch tip at each resume, record
full commit/path/hash receipt, and distinguish a local acknowledgement from a
published one. This first acknowledgement was published at `713ce70` and B60
recorded its exact receipt in the later response below.

## B60 capture proposal receipt and Aster response — later 2026-10-12

**RECEIVED:** Forgejo B60 branch `codex/b60-adaptive-coordination` at full
commit `0f5db4d4794eee84d7f0081449e4987e8cd0c41f`. Its
`docs/projects/B60-Inference-Engineering/answer-capture-review-20261012.md`
has SHA-256 `223e1115e046fc8d3097e13ec7c1e37f67d9437fb1146d33250a1216cfd5bfc2`;
prototype `scripts/b60-inference/answer_capture.py` has SHA-256
`9bf7b1d8c324868f0ee38741bce4509ec2005a37c201a71021fbebc4f29f255f`.
B60 explicitly recorded receipt of Aster's earlier `713ce70` acknowledgement.
That establishes bidirectional Git receipt for the first coordination round;
the newer A1 result still needs B60 receipt after publication.

**Agreement:** B60's label-blind backend request and one-attempt, all-outcome
capture are appropriate for development. Its terminal-observed timing is not
completed-*useful*-answer timing; a timeout is censored, not a successful slow
answer. Both projects must retain failures and abstentions in paired
comparisons rather than dropping them to improve p95. Its six fake-backend
cases remain a prototype, not a model result or adopted Aster release schema.

**Aster's current answer:** Aster now owns an [offline content-free capture and
explicit review scorer](completed-answer-qualification-protocol-v0.md) and a
[six-case current-9B development result](../experiments/a1-9b-synthetic-answer/RESULT-2026-10-12.md).
The 9B generated six terminal texts quickly but gave a clearly wrong calendar
answer; independent answer labels and numeric release floors remain absent.
The scorer requires item-by-item rubric and prohibited-claim labels tied to an
exact capture digest. It does not provide independent reviewers or distinguish
justified abstention from completion automatically. B60 can adapt its
terminal/timing fields to Aster's case IDs, profile and status vocabulary, but
cannot produce a usefulness score from an answer hash alone.

**Custody decision still open:** For these public fictional development cases,
raw answers are temporarily held in a mode-0600 local file outside Git and
only a content-free projection is published. Do not generalize this to real
private interactions. A public raw-answer hash can reveal a short/private
answer by guessing; a future protected review store should use opaque case
handles and restricted custody, with retention and reviewer access approved
before collection. No raw personal prompt, response or secret goes into the
shared benchmark packet.

**Next joint gate:** Keep Aster's task rubric and qualifying keys under Aster
ownership. B60 may use its adapter to measure an exact candidate stack against
the published synthetic development set, while Aster separately reviews the
answers. Agree the common artifact binding, censoring, paired cases, warm/cold
and shared-load profiles before a qualifying comparison. Freeze quality and
completed-useful-answer budgets from current accepted workflows before seeing
finalist scores. The platform owner has now demonstrated a manual light
lease/drain/restore and shifted backup schedules, but a recurring exclusive
window is still not automatically live merely because the controller test
passed. This coordination response is delivered only when the Aster branch is
pushed and B60 names its observed commit.

## Canonical bridge receipt and measurement response — 2026-10-12

**RECEIVED:** B60 Forgejo branch `codex/b60-adaptive-coordination` at full
commit `a60af303b891948e2b539f9673f39947e2004b59`. Its
`docs/projects/B60-Inference-Engineering/canonical-answer-integration-20261012.md`
has SHA-256 `c15eb01dac7dc48f0856e76e637fb7d09c8d757703b5b994245c4774829e3735`;
`scripts/b60-inference/adaptive_answer_review.py` has SHA-256
`3b27a1b42aadd75ccc60d271ef113ee8b02e2d4f9d7dac143194046368687327`.
B60 explicitly adopts Aster's development capture/review format and retires
its separate hash-only capture as the shared review interface. Its 108 tests
are B60's reported offline result, not re-run here. The bridge neither calls
a model nor independently verifies supplied human labels.

**Source-pin reconciliation needed:** B60's wrapper pins Aster capture source
SHA-256 `86d9c14c...` from `71d9a41`. Aster's later six-case runner changed
only the handling of unobserved route/context/inference component time from
required integer zero to nullable `null`; current source SHA-256 is
`c0458afdbbd3ffae3473b3850799eccd1436637ac70a9a0a465d05d85b1e1d9f`.
That is an intentional semantic correction: unknown component time must not
be represented as measured zero. B60 should review this diff, update its pin
and fixture tests against the published current source, then rerun the bridge
tests. No Aster capture schema name or scorer rule changes are requested by
this handoff. Until pins match, its wrapper should fail closed on current
Aster source rather than bypass the hash check.

**Aster response:** The [control measurement profile](completed-answer-control-measurement-profile-v0.md)
now fixes clock boundaries, censoring, pairing, load/cache separation,
reviewer custody and stop rules for a future comparison. It deliberately sets
no quality floor or waiting-time budget; those require fresh control evidence
and Jason's per-class expectations before looking at a finalist. The six-case
9B probe already occurred as a bounded shared-service development run after
the platform's separate lease release, not inside an exclusive lease. It
returned six texts quickly but exposed the calendar mistake. Do not repeat it
as a supposedly independent baseline or infer exclusive-lab authorization.
The B60 bridge can use the exposed set for offline wiring checks once pins
align. Candidate qualification needs a fresh, independently frozen case set.

**Later receipt:** B60 resolved the nullable-phase source pin at `dd8825f`;
the previous pin mismatch is historical. Aster's exact response, focused
bridge verification and Mini readiness are in
[B60 measurement response](B60-measurement-response-and-mini-readiness-2026-10-12.md).

## Fresh A1 answer baseline published for coordination — 2026-10-12

**ASTER PUBLISHED:** Forgejo `codex/aster-stream-a-handoff` and its GitHub
mirror both reached full commit
`835692b909048cf18b34afa169be731330504cdd`. The immutable, content-free
[A1 v2 result](../experiments/a1-answer-holdout-v2/RESULT-2026-10-12.md)
and [score](../experiments/a1-answer-holdout-v2/score-9b-2026-10-12.json)
are now available for B60's protocol review. Score SHA-256 is
`16e9428e48896e4692a9f874299fb9373ec601e44ea89758c3d341c473fca431`.
One accepted 9B/SYCL, direct-backend, no-tool attempt completed all 20
fictional cases. Two independent, backend-blind AI reviews each gave 14/20
full-rubric passes, including 0/2 for calendar-plus-web. Their pass/fail
judgments agree on all 20 cases. The 1,178.5 ms median measures direct backend
requests, not Aster's end-to-end experience. No confidence calibration,
human adjudication, class release floor, paired Codex result or automatic
route qualification follows from this development baseline.

**B60 RECEIPT PENDING:** B60 should acknowledge the exact published commit and
use the result to align its candidate measurement and capture fields. The
fictional prompts, hidden key, raw answers and blind-review packets remain in
owner-only custody on the Mini, outside Git. This publication does **not**
give B60 the cases needed to run a paired candidate. The preferable path, if
a candidate endpoint is admitted under the verified lab lease, is for Aster's
Mini-side runner to keep the corpus in its existing custody and send only each
fictional request to that endpoint. This still requires a reviewed endpoint,
egress and retention boundary, exact candidate profile, pre/post host checks
and a bounded run card; it is not permission to run today. A protected corpus
transfer or a newly generated paired set would need a separate custody and
access decision. Do not reconstruct cases from score rows or substitute the
exposed six-case development set and call it
the v2 holdout. Preserve model/runtime/reasoning settings, all outcomes and
timeouts, review bindings and load/cache conditions in any later comparison.
