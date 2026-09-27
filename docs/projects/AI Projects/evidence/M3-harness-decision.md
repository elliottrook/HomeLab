# M3 harness decision — retain the bounded Aster runtime

Date: 2026-09-26

Status: **ACCEPTED FOR THE FOUNDATION BASELINE; M3 OVERALL REMAINS OPEN**

Decision owner: Jason

Scope: serving/orchestration harness only. This decision grants no tool, model,
credential, deployment or production-change authority.

## Decision

Retain the existing bounded Python Aster runtime as the foundation serving
harness. Keep Hermes as an optional user-facing/workflow harness, not Aster's
operational brain or a required platform dependency. Do not migrate the baseline
to PydanticAI, LangGraph, Pi or another agent framework on the available evidence.

PydanticAI slim remains a **probationary specialist challenger** for a future use
case that can state what custom validation, retry, structured-output or provider
code it would replace. LangGraph remains conditional on a demonstrated need for
durable graph execution, pause/resume or branching that the current bounded loop
cannot express clearly. Pi remains an unbenchmarked integration option where a
TypeScript boundary is independently justified. Hermes may be selected by a user
for an interactive workflow when its measured prompt and call overhead is an
accepted trade, but it is not placed in the deterministic household or authority
path.

This is a retain-baseline decision, not a declaration that the current Aster
harness is permanent. The stable contracts are the long-lived architecture;
harness implementations remain replaceable behind them.

## Evidence classification

### VERIFIED CURRENT STATE

- Read-only checks on 2026-09-26 found `aster-agent.service` in LXC 104 and
  `aster-llama.service` in LXC 110 active with zero systemd restarts. Current
  memory was approximately 44.6 MiB and 9.55 GiB respectively. The authenticated
  llama.cpp health endpoint returned `{"status":"ok"}`. No service was changed.
- LXC 110 exposes one llama.cpp listener on `192.168.70.12:11435`. The repository
  unit describes one 8,192-token slot and Qwen3.8-27B UD-IQ4_XS on Vulkan.
- The deployed Aster source SHA-256 was
  `f3d460fbf0af81befc1e296a6f518fdc6b7e5cb11c3eb189d1c905b7c695bddb`.
  The current worktree source SHA-256 was
  `62a8b3410856d218ad57aeac8c233d3e70a21354995b88a25dd064ce2a40a407`.
  They are not byte-identical. Follow-up read-only comparison proved the deployed
  bytes exactly match commit `2c71d6b12abcf3ed4d71aa9f9ea2af60a2fcfae2`
  and the current local `origin/main` tree. That commit adds ten lines of narrowly
  scoped AI-PAM knowledge ranking/anchoring over this worktree's Aster source. The
  Stream A branch and local `origin/main` are otherwise divergent histories, so no
  merge was attempted as part of this evidence decision. The earlier synthetic
  measurements are not presented as a fresh benchmark of today's deployed file.
- The isolated PydanticAI comparison used Aster source slice SHA-256
  `8777687ce97055d2db3254aa6b30ddf37fc61e73dac2bd18008cbea3fef1a8b6`,
  `pydantic-ai-slim==2.51.0`, Pydantic 2.13.4 and a 17-wheel, 5.45 MB locked
  dependency set. The disposable environment occupied about 46,000 KiB.
- In two controlled preload repeats, PydanticAI stayed within the preregistered
  guardrails but used about 69 MiB peak RSS versus 47.1 MiB for Aster and added
  about 1 ms p95 per simple case. In explicit tool loops, both candidates passed
  all eight conformance cases twice; ordinary PydanticAI loop p95 was about
  1.66–2.25 ms versus 0.026–0.033 ms for Aster.
- PydanticAI rejected malformed arguments earlier. The independent deterministic
  validator and authorization checks were still required, so the candidate did
  not remove a security boundary or establish a maintenance saving.
- Historical recorded Hermes configurations were materially heavier: direct
  warm Ollama was 1.47 seconds while stock Hermes was 96.6 seconds with 19,422
  prompt tokens; a stripped Hermes profile still recorded a 12.2-second warm
  conversation and 45.6-second two-call terminal loop. Current Hermes Desktop
  compatibility tests recorded about 65–69 seconds while reevaluating an
  approximately 4,900-token startup prompt. These are configuration-specific
  lab measurements, not claims about every Hermes release.
- Existing production Aster evidence demonstrates real local-model usefulness,
  but not a challenger comparison: the sysadmin graduation passed 28/28 across
  two runs with worst latency 47.5 seconds; Home Assistant passed 20/20 with
  worst latency 46.798 seconds; the later mirror graduation accepted 60/60 with
  mean 48.436 and maximum 71.447 seconds after one bounded evaluator correction.
- The accepted S0 descriptive routing run used ten exposed development families.
  It is sufficient to retain abstain, keyword and fixed-nearest baselines for
  future comparison, but insufficient to select a production router or calibrate
  confidence. Its approximately 135-second disposable-VM lifecycle for 0.118
  seconds of evaluator work also rules that VM mechanism out as a serving harness.

### REPOSITORY INTENT

The canonical programme requires harnesses and decision engines to propose,
deterministic policy to authorize, narrow adapters to execute and independent
evidence to verify. Its fast household path must survive GPU, cloud, Hermes and
experimental-router failure. Harness replacement is optional and must preserve
the Decision, Harness Run, Outcome, Capability and authority contracts.

### ARCHITECTURAL INFERENCE

The dominant cost is model-visible context and model round trips, rather than the
Python framework's sub-millisecond loop time. Reducing exposed schemas, prompt
material and unnecessary reasoning calls is therefore likely to yield more value
than replacing Aster with a general agent framework. This inference should be
tested when a concrete workflow is proposed; it is not a universal framework
benchmark.

### UNKNOWN / REQUIRES VERIFICATION

- No equivalent live local-model workload has compared current Aster with
  PydanticAI, LangGraph, Pi or a current stripped Hermes configuration.
- Maintenance effort has qualitative records and dependency counts, but no long
  observation window with measured engineer hours for competing implementations.
- The current deployed file has verified Git lineage, but the Stream A branch and
  local `origin/main` each contain 43 commits absent from the other at this
  checkpoint. Integration must preserve both histories and is outside this ADR.
  A future byte-specific comparison must begin from the reconciled intended tree.
- Pi and LangGraph have not been installed or benchmarked in this lab.

## Alternatives and disposition

| Alternative | Evidence-backed value | Cost or unresolved issue | Disposition |
|---|---|---|---|
| Bounded Aster Python runtime | Proven local model path, small process, explicit deterministic boundaries, no added migration | Custom code remains owned locally; current source lineage needs reconciliation | **Retain foundation baseline** |
| PydanticAI slim | Typed responses, earlier argument rejection, provider/test abstractions | 17-package footprint, about 22 MiB added peak RSS, added loop overhead, no removed boundary or measured maintenance gain | **Reject baseline migration; retain probationary challenger** |
| Hermes | Existing desktop compatibility and broad interactive workflow UX | Large prompt/schema and repeated-call overhead in measured configurations | **Optional client/workflow harness only** |
| LangGraph | Potential durable state, branching and human pause/resume | No demonstrated requirement; would add a second orchestration abstraction | **Defer until a graph-shaped requirement exists** |
| Pi agent core | Potentially lean general agent loop | No lab benchmark; TypeScript integration and duplicated authority adapters | **Keep as conditional research option** |
| New custom generic agent framework | Full local control | Recreates framework maintenance without a proven requirement | **Do not build** |
| No agent harness in deterministic path | Minimal dependencies and graceful degradation | Cannot answer open-ended reasoning tasks alone | **Required architecture rule** |

## Why no live challenger run now

The preregistered rule says that merely passing overhead guardrails is not a reason
to migrate. The offline candidate established no correctness or maintenance benefit.
A live run would require a provider integration, safe handling of an inference
credential, additional load on the single-slot production model and careful
current-source reconciliation. Those costs cannot answer a hypothesis stronger
than “the added layer can call the same model.” The experiment is therefore
rejected at this stage rather than performed for completeness.

A future live comparison becomes justified only when all of these are true:

1. a concrete workflow names the baseline limitation and the code expected to be
   removed or simplified;
2. current Aster and candidate source, dependencies, model, prompts, schemas and
   inference settings are pinned;
3. a representative frozen corpus and task-quality rubric exist;
4. the candidate runs with no broader permissions, tools or private context;
5. prompt/output tokens, calls, retries, p50/p95, queue/prefill/decode, RSS/CPU,
   quality and maintenance effort are measured; and
6. rollback is removal of the isolated candidate with no production-path change.

## Consequences and M3 status

The harness subdecision is complete: **retain Aster, reject migration, preserve
replaceability**. No new serving framework is added and no production service is
changed. Hermes overhead remains a workload/configuration metric that must be
included whenever Hermes is proposed for a path.

M3 overall remains open. The milestone combines harness and routing acceptance.
The ten-family S0 corpus is exposed descriptive evidence, not an independently
reviewed holdout, and no production router or calibrated confidence exists. The
missing evidence is therefore narrowed to representative routing evaluation and,
only if a concrete harness benefit appears, a preregistered live challenger test.
Missing candidate evidence cannot be converted into an adoption claim.

## Reversal

This documentation decision requires no runtime rollback. Supersede it with a new
ADR only after the trigger conditions above and a reviewed comparison show a
material benefit without weaker authority, privacy, reliability or degradation
behavior. Retain this negative result and its source digests as prior evidence.

## Evidence links

- [Harness alternatives and source review](../HARNESS-ALTERNATIVES.md)
- [Preregistered comparison](M3-comparison-plan.md)
- [Preload results](M3-preload-results.md)
- [Tool-loop and earlier routing smoke](M3-tool-loop-results.md)
- [Accepted S0 descriptive result](../experiments/s0-routing-descriptive-v1/run-v5b-corpus/README.md)
- [Accepted S0 decision](../experiments/s0-routing-descriptive-v1/run-v5b-corpus/DECISION.md)
- [Aster operations](../../../reference/Aster-Operations.md)
- [Local AI history](../../../projects/completed%20projects/Local-AI.md)
- [Sysadmin graduation](../../../projects/completed%20projects/Aster-Sysadmin-Second-Brain.md)
- [Home Assistant graduation](../../../projects/completed%20projects/Aster-Home-Assistant.md)
- [Mirror graduation](../../../projects/completed%20projects/Aster-Mirror-Directory-Retrieval.md)
