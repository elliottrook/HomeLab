# S0 descriptive routing comparison — proposed experiment

Status: **completed under later exact approvals; no production promotion**. Owner:
Jason. Baseline95f4258. Result:
[`run-v5b-corpus/`](run-v5b-corpus/README.md).
Scope: exposed, accepted synthetic train/dev data only. No new collection, service,
model, cloud provider, GPU, real requests, credentials, tool execution or deployment.

## Question and falsifiable hypotheses

Does a small existing router recover Jason-approved capability/status labels on
this exposed development set, and where does it fail? This is an integration and
error-analysis exercise, not a test of generalization or permission to adopt a route.

H1: keyword rules recover more complete development labels than always-abstain.
H2: a fixed nearest-example router recovers more complete development labels than
keyword rules when fit only on20 train families. A tie or lower count fails the
corresponding descriptive hypothesis. Neither outcome selects a production model.
H3: verbatim synthetic context changes predictions relative to request-only input.
Report disagreements and gains/losses, not just a favorable aggregate.

No confidence intervals, significance test, calibration claim, production target,
privacy-safety guarantee or adoption threshold is justified by these10 exposed dev
families. A one-case difference is10 percentage points. These hypotheses describe
this finite corpus only. All failures and negative results must be retained.

## Verified existing pieces and missing implementation

`scripts/aster-adaptive/routing_smoke.py` has stdlib `rules`, `Nearest`, `tokens`
and `proposal` functions. Its normal `evaluate()` reads a different fixture corpus
and tunes a threshold on a calibration split: **do not call that entry point** for
this experiment. No calibration split exists here. `plan.json` pins this source
and the pilot summary; the latter pins all nine reviewed artifacts.

The existing S0 validator is deliberately fixture-only; do not relax it or present
it as a human-record authenticator. A separate bounded read-only manual-record
adapter, evaluator and test suite are still required. No implementation was added
or run in preparing this plan. `runner_sha256`, `adapter_sha256` and environment
manifest are null until reviewed implementation exists; null must block a run.

## Corpus, provenance and splits

Use exactly30 accepted families:20 train/10 dev, three per stratum and exactly one
dev per stratum. Preserve accepted labels and train/dev assignments. Read the
original pending proposal plus the later acceptance receipt together; the receipt
must match full artifact and per-case hashes. No guessed acceptance from filenames.

Adapter acceptance requires exact version/field/type/size checks, unique family
IDs, integer revisions, content and label accept for every included record, matching
receipt/source hashes, consistent split and no unsupported schema, capability or
status. Verify30/20/10 counts and all registry vocabulary. Reject cross-split exact
request duplicates; report semantic overlap manually without silently dropping
cases or changing families. Check disjoint required/optional/prohibited sets,
mandatory forbidden capabilities and sensitivity inheritance. Human authenticity
remains the recorded conversational approval, not cryptographic proof.

Prepare engine input separately from scoring references. Engines must never see
dev labels, stratum, split, family ID, review decisions, effort or receipt metadata.
Nearest training rows may see only permitted text and approved training targets.
No train/dev resplit, additional variants, relabeling or tuning after output.

## Engines and fixed operating points

1. Always-abstain: returns abstain, empty capabilities, no authority, null confidence.
2. Existing keyword rules: reuse pinned source unchanged. Any missing vocabulary,
   overbroad matching or failure to honor negation is an observed limitation.
3. Existing TF-IDF nearest example: fit separately per input profile on the20
   train rows only. Keep source tokenization/IDF and deterministic ties; sort train
   rows by family ID before fitting. Fixed cosine threshold0.2, chosen as an
   engineering probe, not calibrated or optimized. Do not fit on dev or try a grid.
   For multiple acceptable training statuses choose lexical first after sorting
   (`deny` before `unsupported`); log this rule rather than pretending unique gold.

Nearest's required labels are copied only for a plan target. Non-plan predictions
must contain no capabilities. Similarity is not probability; confidence stays null.
No Jev, semantic embedding package, Ollama, Hermes or frontier adapter is necessary
for this first bounded comparison. Do not install dependencies.

## Input profiles and interpretation

A. Request-only: exact `request`. Context-dependent errors must be tagged as such;
this profile intentionally lacks some reference assumptions and does not measure
complete assistant behavior.

B. Context-assisted: exact request, then literal separator `\nSynthetic context:\n`,
then exact `synthetic_context`. No labels or additional annotation. Fit nearest on
the same profile used to query it. This context is oracle-like scenario framing,
not context retrieved by a deployed assistant. It may include routing hints or
explicit clarification/denial cues. Higher agreement is not evidence that the
engine discovered those facts or safely retrieved context.

Show profiles separately. Never blend them into one headline accuracy value.
Treat the request-only/context-assisted delta as diagnostic sensitivity to the
provided context. Do not edit away awkward hints after seeing results.

## Scoring (proposal, no results yet)

Denominator is all10 development families per engine/profile. A missing output,
exception, timeout or malformed output stays in that denominator as a failure.
Preserve the raw prediction and the validation/error status.

Complete agreement: predicted status belongs to the accepted status set. For plan,
required capabilities are a subset of predicted capabilities, predicted capabilities
are a subset of required union optional, and none are prohibited. For non-plan,
capability list is empty. Clarify/deny/unsupported count as correct when accepted;
abstain is correct only if explicitly accepted by that case. Do not silently score
abstention as correctness. Sorted-set comparison, not list ordering.

Report counts and fractions for complete agreement, status agreement, missing/extra
capabilities, prohibited-capability predictions, invalid outputs, abstention,
non-abstaining valid-decision coverage and error fraction among covered cases.
Zero coverage => conditional error N/A, not0. Count clarify/deny as covered decisions.
Pairwise disagreement compares status plus sorted capability set on valid outputs;
report valid-pair denominator and missing/error pairs separately. Include one
per-case table with input profile, target, raw prediction and failure classification.

These engines have no independent sensitivity/egress output. Report privacy-routing
quality **not measured**, rather than synthesizing a correct privacy score from the
gold labels. No model selection exists: cloud-required percentage and production
local-resolution percentage are **not measured**. Actual experiment cloud calls and
tool executions must both be0. Those zeroes do not prove household reliability.

## Measurement and execution bounds

One semantic pass per profile/engine over10 dev families (60 decisions total).
Thirty warm repeats of those same decisions solely for latency; repetitions are
not new independent examples. Log construction time separately from routing time.
Use monotonic nanosecond timing; report per-engine/profile median and nearest-rank
p95 warm latency over300 observations, plus10 individual first-pass timings.
Do not call first-pass measurements a cold-process distribution. Record Python,
OS/architecture and CPU descriptor, execution order and input/source digests.

Peak RSS is process-wide high water, not allocation attributable to one route.
Normalize OS units and report that limitation. Budget:60 seconds total,256MiB peak
RSS,2MiB output; stop cleanly on exceeded or unavailable enforcement. No loop retries
for a favorable score. Abort/errors preserve known counts and identify unprocessed
cases. Timing and resource limits are not asserted tested by this document.

Network and subprocess access must be denied for the actual runner before loading
engines. Use reviewed local stdlib code only, no arbitrary plugin import or dynamic
adapter discovery. A documented OS-level network/process restriction must be verified
available; otherwise stop at readiness. Python monkeypatch tests are defense in depth,
not a sandbox for adversarial code. No secret/environment export in output. Restrict
reads to pinned data/source plus required runtime files; writes only to a bounded
fresh scratch run directory. No Git staging, SSH, HTTP, MCP, production services,
local model sockets or shell/tool calls from the runner. Starting the runner through
the approved local shell is distinct from the runner launching subprocesses.

## Future validation requirements

Before any corpus execution, use disposable fixture tests for: missing acceptance,
changed content/hash, duplicated IDs/JSON fields, bad revision/split, malformed
status, non-plan capabilities, missing mandatory prohibitions, sensitive optional
capability downgrade, changed source/runtime pins, empty training set, deterministic
ties, missing/timeout outputs, zero coverage, paired-disagreement denominator,
and context/label separation. Fail if dev labels enter a fit or prediction input.
Test deny/clarify accepted outcomes, no-network/process enforcement, read-only inputs,
write/output budgets and interrupted partial output handling. Do not rewrite the
accepted pilot corpus to satisfy a test or route.

## Evidence, review and rollback

Before a run, freeze this plan, adapter/runner hashes, runtime manifest, exact input
manifest and validated safeguards. Technical review must check those concrete
artifacts. Authorized execution, if later granted, is one bounded run with these
settings. Any change invalidates the frozen run identity and needs a new record.

Retain per-case predictions, failures, descriptive aggregates, timings, resource
observations, source/adapter/runtime pins and a decision note. M4-compatible export
may be proposed later; do not fabricate independent M4 acceptance or custody.
Publication still needs explicit push approval. Failed runs remain evidence, not
silently overwritten. Duplicate launch must detect the existing run and stop.

Rollback: no production state changes; disable/discard unused candidate runner and
retain approved experiment history. Exclude defective results explicitly without
rewriting accepted labels. No engine/model/policy promotion follows a successful run.

## Next authorization

Approve **local adapter/evaluator implementation and fixture tests only**, using
this plan. No execution against the30 accepted cases yet. After implementation,
verified isolation and technical review, present one concrete bounded run for
separate execution approval. This sequencing implements the existing collection
approval's explicit exclusion of router/model evaluation; “continue” was not treated
as authority to run one. No further collection, model calls, deployment or push.

## Completed outcome

After the intervening implementation, isolation and approval gates, corrected run
`corpus-descriptive-002` completed in fresh offline VM123. Strict framing and result
validation passed. H1, H2 and H3 passed only as finite-corpus descriptive
hypotheses: keyword rules beat abstention; fixed nearest beat keyword rules in both
profiles; and context changed predictions but did not uniformly improve them.

The result retains all three engines as baselines and explicitly rejects production
selection or threshold tuning from ten exposed development families. See the
[result](run-v5b-corpus/README.md), [evidence](run-v5b-corpus/evidence.json) and
[decision](run-v5b-corpus/DECISION.md). M3 and production/shadow gates remain open.
