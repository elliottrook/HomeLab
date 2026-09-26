# M2 offline contracts and baseline adapter — 2026-09-25

Status: local candidate, not deployed. No M1 graduation or connected-pilot claim.

## Implemented slice

`services/aster-adaptive` implements strict DecisionRequest, Decision, Capability,
Catalogue, HarnessRun, Outcome and Experiment models with exported candidate-v1
JSON Schemas under `schemas/aster`. Schemas plus explicit semantic invariants form
the proposed wire contract. The only adapter extracts the reviewed current Aster
selector's literal regex declarations and pure function without importing the
application. Source is digest-checked and evidence pins the exact source, candidate,
fixtures and evaluator. There is no live executor, broker client, model client,
collector, dataset of real interactions or network deployment.

The catalogue is synthetic, execution-disabled and scoped to current hinted
tools. It carries actual input-schema digests and explicit opaque output-schema
digests; this does not pretend all Aster outputs already have stable schemas.
Unknown capabilities or source/registry drift deny proposals. Policy and registry
snapshots, proposal expiry, steps and DAG order are checked. No plan grants access.
An adapter cannot return a made-up confidence probability; it remains null.

Outcome records never label the absence of tool execution as a successful action.
They omit prompts, results, hidden reasoning, actor IDs, credentials and arbitrary
error text. This allowlist is not a universal secret detector: syntactically valid
IDs can carry sensitive information if a future producer misuses them. Only the
reviewed synthetic runner is authorized here. Production ingestion remains gated.

## Evidence

- 25 conformance/adversarial tests pass, including socket/subprocess denial during
 evaluation, unknown versions/fields/capabilities, source drift, cross-baseline
 catalogues, policy/registry mismatch, expired proposals, cycles, step/deadline
 bounds, empty scope and false authority/execution claims.
- 12 synthetic fixtures cover timers, lights, media, knowledge, calendar, web,
 mixed calendar/web, personal context, sysadmin, ambiguity, an existing HA report
 and scope denial. 100 repetitions each; baseline selection matches exactly.
- Local warm selector p50/p95: 8.875/18.667 microseconds.
- Adapter plus semantic validation p50/p95: 46.875/56.208 microseconds.
- Existing environment: Python3.12.14, Pydantic2.13.4 on the Mac; no installation.
- The current Stage2 approval candidate still passes10 bridge and 10 approval-service
 tests. No overlapping broker/approval source was edited.

Exact results and source digests are in [the experiment record](M2-offline-baseline.json).
Rerun commands are in [the package README](../../../../services/aster-adaptive/README.md).
These are local timing samples, not significance estimates or production SLOs.
The fixture clock is synthetic; no emitted proposal is a live authorization.

## Findings and falsifiable limits

The hypothesis tested was **preserving baseline tool selection**, not improving
routing quality. It passed on this small corpus. Desired future capabilities are
separate design labels, not human gold or existing tools. No held-out accuracy,
calibration, local-resolution percentage or cloud-savings claim is justified.

The baseline selects no tools for timers, media, fact, web and mixed-calendar/web
examples; `today` selects the time tool, not a calendar reader. A lights request
selects knowledge search rather than device control. These are observed selector
gaps on fixtures, not proof that the entire runtime cannot answer a question.
A no-tool selection can still invoke the runtime's model-only fallback. The
candidate's `abstain` means only "no tool proposal from this selector".

Contract validation adds roughly 38 microseconds at the median in this run, which
is small in absolute terms but not a deployment resource/cost result. It neither
measures nor fixes Hermes/harness prompt overhead. M3 needs separately controlled
full harness/model experiments before any framework adoption decision.

## Threat and failure review

| Failure / attack | Local guard | Remaining gate |
|---|---|---|
| Model invents capability or authority | Known-catalogue validation; authorization fixed not_granted; no executor | Real authorization must remain in AI-PAM |
| Drifted/stale catalogue or policy | Source/digest binding; cross-record checks; expiry | Trusted live projection/revocation design |
| Untrusted file presented as baseline | Caller-pinned digest; only trusted reviewed repo file | AST extraction is not an arbitrary-code sandbox |
| Prompt/tool-output or secret retention | No free-text telemetry; strict unknown-field rejection | Source-local privacy review for real collection |
| Classifier claims calibrated probability | Probability fixed null | Disjoint labeled calibration dataset |
| Graph cycle/fanout/budget abuse | Ordered earlier-step dependencies; at most 8 steps; bounded input | No DAG executor or composition/data-flow enforcement yet |
| Timeout or missing tool match | Degraded/abstain, zero execution | Household fallback remains outside this unused package |
| Evaluator marks itself successful | Only synthetic selection agreement; no action-success label | Independent human gold/locked holdout for M3/M4 |
| Broken schemas or rollback | No production consumer; remove candidate binding/files | Version/deprecation policy before external consumers |
| Existing host/GPU/cloud outage | Offline CPU-only package adds no runtime dependency | Live household availability remains untested here |

## Acceptance and rollback

Local slice acceptance: schemas exist, 25 tests pass, fixture selection preserved,
no network/process/tool/model execution, reproducible source manifest and measured
CPU overhead. M2's full connected adapter/authorized catalogue gate remains open
behind M1 Stage2 and explicit pilot approval. The current fixture projection is
not that authoritative integration.

Rollback: discard the unused local adapter/schema binding and retain historical
experiment evidence. No service, policy, DB, identity, endpoint or infrastructure
needs restoration. No production or Git remote action is authorized by this work.

Next work: human review of the candidate contracts and required/optional/prohibited
capability labels; a controlled M3 harness baseline can use synthetic dependencies.
No connected pilot, private interaction collection or expanded authority may start
from a passing fixture result. Stage2 remains blocked on actual verified assurance
provenance and a bounded, separately reviewed deployment choice.
