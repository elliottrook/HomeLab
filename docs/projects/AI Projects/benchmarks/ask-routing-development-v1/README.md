# Aster Ask routing benchmark — development baseline v1

**Purpose:** preserve a reproducible starting point as Aster's local and Codex
backends change. This is a **synthetic regression suite**, not a test of general
intelligence, real-user success, calibrated confidence or authority to act.

The frozen 30-case source is
[`routing-families-v1.json`](../../../../../scripts/aster-adaptive/fixtures/routing-families-v1.json)
at SHA-256
`c797533494119e44c9c927d5b9b274ccd6426cacd50ca7cd93391861c0663cec`.
It covers timer, household, media, stable facts, calendar, web, mixed
calendar/web, HomeLab status, ambiguity and personal context, three synthetic
examples each. Those requests and labels were exposed to implementation and
prompt iteration. Keep this exact file immutable and version a successor;
do not relabel or silently add cases to make a model pass.

The first baseline is the [9B/SYCL manifest](local-9b-sycl-2026-10-12.manifest.json),
[raw content-free route record](../../experiments/m3-9b-sycl-routing-compatibility/run-v4-2026-10-12.json)
and [independently recomputed score](local-9b-sycl-2026-10-12.score.json).
The source experiment and its v1 failure/diagnostics are retained under
[`experiments/m3-9b-sycl-routing-compatibility`](../../experiments/m3-9b-sycl-routing-compatibility).
The [existing lexical-rule run](rules-macos-2026-10-12.run.json),
[manifest](rules-macos-2026-10-12.manifest.json) and
[score](rules-macos-2026-10-12.score.json) give a cheap, tool-free control on
the **same exposed fixture**: 30/30 exact. The rules and examples were authored
together, so this is an especially favourable development check for the rules,
not an independent rules-versus-model quality comparison. The rule run was
measured on a Mac with Python 3.9.6, not the B60; its rounded `0.0`-second
latency fields mean **below the scorer's millisecond precision**, not zero
execution time or a directly comparable household response time.
The scorer ignores a runner's claimed matches when deriving the result and
rejects disagreement, changed input digests, duplicate/missing identities,
unregistered capabilities and unexpected raw-text fields. No new dependency
or service is required.

**2026-10-15 percentile correction:** The original scorer selected index
`floor(0.95 × (n − 1))`, which is not the nearest-rank p95 used by the A1
client-clock summary. With 30 requests, it selected the 28th ordered sample
rather than the 29th. The frozen 9B/SYCL raw run is unchanged; its corrected
nearest-rank request p95 is **0.708 s**, versus the originally published
**0.705 s**. The rule baseline remains rounded to **0.0 s**. The new
[9B score](local-9b-sycl-2026-10-15-nearest-rank.score.json) and
[rule score](rules-macos-2026-10-15-nearest-rank.score.json) retain the original
scores alongside them. Exact route agreement stays 18/30 and 30/30
respectively; the qualification decision remains unchanged. The source runner
uses nearest rank for future frozen runs; its historical source hash and raw
output are preserved in the original manifest rather than repinned.
The 2026-10-13 offline scorer check also rejects a record marked valid while
it carries a transport failure, error code or non-success HTTP status; HTTP
and error fields must have bounded code shapes. The retained local 9B and
lexical-rule runs still score unchanged. This is evidence-integrity hardening,
not a new route or a promotion result.
The current scorer also fixes the v1 suite ID and fixture digest in code, so
changing both the fixture and its manifest cannot produce a score under the
same suite identity. The retained baseline score files keep their original
evaluator digest; a later run records the revised evaluator digest and does
not rewrite those historical files. This integrity check changes no route,
label or promotion decision.

**2026-10-17 content-free failure check:** An invalid attempt may now retain
only its bounded failure metadata and latency, not status, capabilities or
runner-claimed agreement fields. Optional run-level timings must be finite,
non-negative numbers. The focused scorer suite passed 16 tests. Re-scoring the
unchanged retained runs still gives 18/30 for 9B/SYCL and 30/30 for the
lexical rules, with nearest-rank p95 values 0.708 s and rounded 0.0 s.
This closes a raw-text channel in future run artifacts; it does not improve
the router or supply independent labels. Historical manifests and scores keep
their original evaluator identity.
The later October 17 manifest check also requires bounded, single-line ASCII
backend/model/runtime/reasoning/schema identifiers, because the backend ID is
copied into the score. The focused suite passes 17 tests and retains the same
two baseline results. It does not verify that an asserted backend identity is
true; release provenance and model attestation remain separate evidence.

## What a comparable backend run must provide

Each backend—deterministic, newer local stack or subscription-backed Codex—gets
the **same request text, capability vocabulary, output contract and tool-free
scope**. The model never receives gold labels. Each result has one record per
case with ID, validity, status, selected capability IDs and request latency;
raw answers, prompts, account identifiers, tokens and hidden reasoning are
excluded. A label-blind backend may omit `exact_match`, `extra` and `missing`;
the independent scorer derives them after the run. The manifest binds fixture
bytes, result bytes, adapter/prompt code,
model artifact where available, runtime, backend class, reasoning setting,
local/cloud boundary and disabled tool mode. A different prompt, quantization,
reasoning mode, harness or model is a new run identity, never a relabelled old
score. Missing model/runtime identity is `UNKNOWN`, never silently filled from
the current configuration.

For a new stack, run the exact frozen suite once after offline adapter tests.
Score with:

```sh
python3 scripts/aster-adaptive/ask_route_benchmark.py \
  --fixture scripts/aster-adaptive/fixtures/routing-families-v1.json \
  --run PATH_TO_CONTENT_FREE_RUN.json \
  --manifest PATH_TO_PINNED_BACKEND_MANIFEST.json \
  --output PATH_TO_SCORE.json
```

Compare **per family** as well as overall: exact status+capability agreement,
missing/extra capabilities, inappropriate clarification/abstention, invalid
outputs and request latency. Do not average 30 near-related examples into an
assumed population accuracy or merge timing from different hardware/backend
loads. Cloud token cost and subscription impact must be measured or marked
unknown; subscription access must not be labelled zero cost. Reasoning-on and
reasoning-off are separate profiles. A low-latency deterministic timer route
does not need a model simply because a new model can answer it.

**Codex baseline is pending.** The native Companion
[D3 manual pilot](../../evidence/D3-native-v16-installation-2026-10-11.md) tested
different fictional questions and did not emit this Decision schema, so its
answers cannot be backfilled as a 30-case Codex routing result. A future
subscription-compatible adapter must keep the same no-tool contract, obtain
Jason's reviewed cloud consent for the exact synthetic batch, cap calls and
retention, record the selected Codex model/effort when exposed, and return only
content-free route fields. The existing one-question bridge is not silently
turned into a 30-question unattended runner. Do not substitute this Codex chat
session for the actual Aster-to-Codex backend.

## Promotion is a separate evidence lane

This suite is the **development/regression lane**: it detects a change in a
known set and identifies families worth investigating. The
[closed S1 human-labelled corpus](../../experiments/s1-routing-holdout-v1/CLOSEOUT-2026-10-03.md)
contains 45 accepted families but missed its own frozen
sampling and adverse-case quotas; it remains incomplete collection evidence,
not a qualifying holdout. Before any automatic router promotion, create a
new protocol and independent, engine-blind labels for realistic asks and
adverse privacy/locality cases. Keep labels away from candidate prompts and
training. Then compare candidate and incumbent on the same cases, with
predeclared per-family safety floors, abstention rules, latency/reliability
budgets and an explicit reject/rollback option. Shadow mode and a small
reversible canary follow; the Decision Plane never grants permissions.

No single score should qualify all of Aster. Maintain separate outcome suites
for: (1) *route selection*; (2) answer correctness and evidence freshness for
facts, web and private knowledge; (3) deterministic household execution and
outage survival; and (4) HomeLab diagnosis/repair with source provenance and
independent postchecks. The
[completed-answer qualification proposal](../completed-answer-qualification-protocol-v0.md)
specifies the next distinct measurement boundary for iterative B60 and Codex
comparisons; it is not a frozen release protocol or an existing corpus. The
current 30-case suite measures only item 1's
status/capability proposal. It does not measure privacy classification,
authorisation, tool effects, final answer quality, voice recognition or
infrastructure remediation. Register each new case family and metric before
using it as a promotion gate.

| Aster ask | First useful outcome measure | Boundary that cannot be inferred from a route score |
|---|---|---|
| Timer, alarm, lights, media | Correct target/action, completion time and offline availability | A model proposal does not prove the action occurred. |
| Stable fact or live web | Correct answer, source/date when needed, abstention on uncertainty | Fast routing does not prove answer truth or fresh evidence. |
| Calendar, personal context, mixed web/personal | Correct composition, privacy locality and unnecessary cloud use | No personal content enters a benchmark by default; a route cannot override policy. |
| HomeLab status and diagnosis | Fresh named evidence, correct uncertainty and safe next check | Diagnosing a fault does not grant repair authority. |
| Ambiguous or unsafe request | Correct clarification, denial or abstention | More model confidence is not permission to act. |

For each row, freeze realistic cases and the *observable* success condition
before testing a new backend. Where confidence is emitted, check calibration
on independent cases; the present runner emits no probability, so none can
be inferred from its 18/30 agreement. Give higher weight to false cloud
egress, unsafe tool suggestions and missed required context than to harmless
extra clarification, but freeze that weighting before a promotion comparison.

The practical promotion unit is **a role or request class**, not “the local
model is now smart enough.” A new local stack may earn media or public-facts
routing while calendar, personal-context or sysadmin requests still escalate.
Retain the prior run, manifest, score, decision and rollback target so later
versions can be compared without rewriting history.
