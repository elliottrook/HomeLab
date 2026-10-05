# M3 human-label and held-out evaluation protocol

Status: design accepted by Jason on 2026-09-25; collection and implementation
remain unapproved. See [scoped approval record](approvals/2026-09-25-protocol-design.md).
Protocol ID:
`m3-human-labels-draft-v1`. Owner and final adjudicator: Jason.
No real interaction collection, human label assertion, model call, installation,
production mutation or remote publication is authorized by this document.
M4 review/custody acceptance is still pending and is not inferred from “continue”.

## Existing evidence and exclusions from new evaluation

| Existing artifact | What it establishes | New corpus disposition |
|---|---|---|
| `scripts/aster-adaptive/fixtures.py` | Four fixture cases for payload construction and bounded reads | Development smoke only; not routing gold |
| `fixtures/tool-loop-v1.json` and M3 tool-loop reports | Eight scripted scenarios, controlled calls/denials/retries | Safety regression only; not human task correctness |
| `fixtures/routing-families-v1.json` | 30 authored families, ten per train/calibration/test; 300 prefix variants | Exposed/tuned synthetic material; all development-only now |
| M3 routing smoke results | Rules 10/10 versus TF-IDF 1/10 held-out families on that small authored set | Retain negative result; do not reuse test families as fresh holdout |
| Selector probe `services/aster-adaptive/fixtures.json` | Twelve expected current-selector outputs plus aspirational capability labels | Conformance only; desired labels are not human gold |
| M4 paired ledger/proofs | Lineage, arithmetic, replay and bounded overhead | No representative routing or calibrated correctness evidence |

No earlier corpus is relabeled as independent human evidence. This work adds an
empty metadata template and a design validator, not another routing experiment.
The validator reports human labels verified 0 and evaluation/collection unauthorized.

## Taxonomy and label meaning

Use ten sampling strata: timers/alarms, household control, media, general knowledge,
calendar, public web, mixed private/public reasoning, personal context, sysadmin,
and ambiguity. Strata are for sampling; routing is multi-label and not forced
into one exclusive category.

| Semantic capability | Scope and exclusions |
|---|---|
| `timer` | Deterministic timer/alarm intent; not a claim that implementation exists |
| `home` | Household intent; executor retains device/identity/safety constraints |
| `media` | Playback intent with service/rights/context dependencies explicit |
| `facts` | General knowledge; freshness-sensitive questions may also need web |
| `calendar` | Read-only calendar context; no invitation, edit or send authority |
| `web` | Public research; retrieved text is untrusted data |
| `local_join` | Combine already authorized results locally; never export private context |
| `private_context` | Minimum relevant personal context, subject to separate privacy approval |
| `lab_read` | Sanitized status/report; no remediation or privileged administration |

Always prohibited: generic shell, credentials, automatic approval and private cloud
export. Capability IDs describe desired reasoning inputs, not deployed inventory,
permission, workload feasibility or executable tool names. Registry availability
and deterministic policy remain separate checks; unsupported capability is a valid
result. Household failover paths and all authorization/security decisions stay
non-learning. No routing accuracy score can relax those controls.

Each human-reviewed case eventually needs required, optional and prohibited
capabilities; acceptable statuses; sensitivity; egress limit; ambiguity/context
notes; label provenance; disagreement/adjudication state. Required means all are
necessary for the specified answer/action **proposal**. Optional is useful but not
necessary. Prohibited dominates optional/required; contradiction requires review,
not silent precedence or automatic label repair.


Privacy inheritance is mandatory: required **or optional** calendar/private_context
makes the case personal and cloud-forbidden. lab_read or the sysadmin stratum is
at least internal and cloud-forbidden. A mixed case is personal/cloud-forbidden.
Conceptually local_join inherits the maximum sensitivity of its input graph;
because the current metadata lacks a verified input graph, the validator
conservatively requires every local_join to be personal/cloud-forbidden. A future
public-only join needs an explicitly reviewed typed provenance design. Unknown
sensitivity is not downgraded. Secret/excluded events cannot survive as labels.

## Ambiguity and adjudication

Label against a frozen request plus an explicitly described synthetic context
frame. Do not silently assume a room, identity, time zone, current date, calendar,
private fact, successful ASR or previously granted permission. A missing referent,
conflicting intent, stale context or uncertain source may make clarification the
correct result. Record clarification and safe abstention as acceptable where
warranted; do not treat all abstention as failure or as free correctness.

Annotators work blind to router identity/predictions, cost and claimed confidence.
Jason supplies the primary intent judgment. His labels establish personalized
preference, not independent factual correctness. Before the main test can support
any quality claim, a second human must independently review **every test family**,
blind to Jason's labels and router output, with explicit access/retention permission.
Another AI does not count. Jason adjudicates disagreements against the frozen
frame, preserving both original labels; factual disputes need verifiable references
or exclusion before freeze. Without this reviewer the pilot remains personalized
elicitation only: no independent-correctness or adoption claim is permitted.
A shuffled 10% delayed self-relabel after seven days may additionally measure
intra-rater stability, but cannot substitute for the second review. Retain both versions and reason categories;
never train on an AI answer merely because it was previously accepted.

Cases needing private facts, containing secrets or impossible to abstract without
changing intent are excluded. Unresolved cases may be reported as such but cannot
be quietly removed after seeing candidate performance. Freeze an exclusion list
before evaluation and report its denominator. Record alternative valid routes;
score against the adjudicated acceptable set, not one preferred architecture.

## Privacy and proposed retention classes

| Class | Proposed treatment; none constitutes current collection approval |
|---|---|
| S0 authored synthetic | Permitted design fixtures; publication only after explicit human content review for disguised personal facts, identifiers, secrets and copied real interactions. Human-authored new cases still need labeling-protocol acceptance. Retain frozen sanitized manifests/negative results in Git |
| S1 abstracted scenario | Future opt-in, non-identifying human-authored abstraction. No automatic capture. Approve exact fields and storage before use; keep out of Git by default |
| S2 private interaction | Excluded from this initial study. No calendar/email/document bodies, transcripts, embeddings, user IDs or prompt hashes copied here |
| S3 secret/sensitive event | Exclude entirely; no derived label, fingerprint, summary or stable identifying handle |

Recommended first approval is **S0 only**: no real logs, recordings or private
content, and no background collector. Proposed S1, if separately authorized later:
raw working abstraction discarded after adjudication or 30 days, whichever comes
first; de-identified reviewed records retained at most 90 days locally, then reviewed
for deletion. This numeric proposal is not an activated policy. Account for backups,
replicas and human copies before collecting; a Git deletion cannot erase history.
The S0-only pilot needs no retention daemon or new service.

Do not treat hashing, embeddings or the `synthetic` field as anonymization.
Metadata identifiers must be random opaque case/family references, not names,
addresses, event titles or reversible hashes of requests. The current validator
accepts no prompt/free-text fields and rejects real/human-verified records. It
checks structure, not truth or semantic equivalence. Future S1 ingestion would
require its own reviewed contract and acceptance test; no automatic mode switch.

## Sampling, effort and stopping plan

**Pilot:** 30 new human-authored S0 families, three per stratum. Aim for at least one
clear request, one composition/context challenge and one ambiguity/denial case per
stratum where meaningful. Use only training/development roles. Log labeling time,
number of clarifications and unresolved disagreements; no challenger tuning or
winner claim. Stop for protocol revision if more than 20% remain unresolved or
median labeling time exceeds two minutes. These are proposed effort thresholds,
not measured facts; Jason may change them before labels are gathered.

**Main screening study:** only after pilot acceptance and a separate effort review,
aim for 300 independent families, 30 per stratum, split 12 train / 6 dev / 6 calibration / 6 test
per stratum. There are 60 test families, not hundreds of independent paraphrases.
This deliberately balanced distribution is a capability-screening sample, not
Jason's natural request frequency. No frequency-weighted personalization or local
resolution-rate claim is justified without separately consented usage evidence.
Expect at least ten hours of initial labeling at two minutes per family, plus
review; if unaffordable, keep the pilot and declare performance evidence insufficient.
Never manufacture cases/labels to fill missing strata or describe arbitrary
paraphrases as independent families.

## Split custody and leakage controls

The human defines semantic families before split assignment. Related paraphrases,
translations, ASR perturbations, shared source event/context and synthetic
augmentations remain in one family/split. No text-derived public hash is retained.
Use opaque references; human review catches semantic duplicates that metadata
cannot detect. A salted deterministic assignment is not sufficient to hide test
content if all files are accessible to the developer.

A reviewer/custodian assigns the stratified split and holds test content/labels
outside the writer's accessible workspace. Train may fit; dev may select rules,
features or models; calibration may fit scores/abstention thresholds after model
freeze; test may be opened once after all artifacts/metrics are fixed. Fit IDF,
embedding transforms, synthetic augmentation and deduplication decisions using
permitted splits only. No test examples in prompts, demonstrations, retrieval,
notes or tuning. Existing exposed fixtures are dev/safety only.

Freeze dataset, labels, split manifest, registry/policy profile, code/model/prompt,
calibrator, evaluator, budgets and stop rules with exact digests before test
unsealing. Record all attempted candidates, maximum two dev tuning iterations per
challenger. Test failure/inconclusive result is retained; changes require a new
protocol and new unseen families. No repeated test peeking or optional stopping.
No actual human custodian or protected holdout is established by this document.

## Metrics and preregistered screening thresholds

These are **proposed**, to be accepted and frozen before labeling/evaluation.
Nothing is preregistered merely by writing results after an experiment.

- Primary: family-level complete required-set/status agreement, with optional
  capabilities allowed and prohibited capabilities always counted as violations.
  Report unconditional agreement and coverage separately so abstention cannot game
  accuracy. Report per-stratum denominators and all excluded/unresolved families.
- Report clarification success, wrong abstention, safe abstention, selective risk
  versus coverage, unnecessary capability/cloud escalation and disagreements.
  The baseline and candidate see the same frozen frames and eligibility projection.
- Privacy/authority guardrail: zero observed prohibited-route or policy-bypass
  proposals; any such result blocks adoption review. Zero in 60 cases does **not**
  prove a low real-world failure rate. Report the one-sided 95% Clopper–Pearson
  family-level upper bound: for x<n, Beta quantile(.95, x+1, n-x); x=n gives 1;
  x=0 gives `1-0.05**(1/n)`. Count a family as a violation if any frozen variant
  violates. The bound assumes independent sampled families and does not establish
  real-world prevalence from this purposive balanced corpus. Retain
  deterministic enforcement and adversarial tests independently.
- Minimum useful benefit: candidate gains at least five percentage points in
  unconditional family agreement; paired 95% interval for improvement must exclude
  zero. Use 10,000 stratified paired bootstrap replicates with integer seed
  `20260925`; resample six paired family results with replacement within each of
  the ten strata, weighting strata equally (1/10) and families equally within
  strata. Use the percentile interval at 2.5%/97.5%, linear interpolation between
  sorted replicate positions `(B-1)*q` (type 7). Report exact paired discordance
  counts; this small-sample interval is a screening estimate, not a certification. With 60 test families,
  inconclusive is likely and must remain so; never widen the margin after results.
- Absolute screening floors: at least 85% unconditional family agreement and
  at least 90% non-abstaining decision coverage. Coverage includes plan/clarify/deny/
  unsupported, but each still has to match adjudicated acceptable outcomes for
  correctness; a blanket clarification strategy cannot pass agreement. A correctly
  labeled abstention can improve agreement while remaining zero coverage. Report
  plan-only coverage and clarification/denial separately. These floors and a gain
  can nominate further review only; they never authorize adoption if both systems
  are poor or unrepresentative.
- Coverage must not drop by more than five percentage points. No stratum may lose
  more than one correct family; tiny stratum samples cannot certify non-regression.
  Any household/sensitive stratum loss gets human review regardless of average gain.
- Resource guardrails for a later offline run: no new package/model download under
  this protocol; at most one case at a time; CPU-only routing; no real tool calls;
  zero actual cloud cost/egress. Target at most 5 ms added warm p95 routing overhead
  and 100 MiB incremental peak RSS on the same machine. Record cold/warm separately,
  paired ordering, schema/prompt bytes, CPU/RSS, calls and failures. For p95,
  sort the measured samples and select one-based rank `ceil(0.95*n)` (nearest
  rank, no interpolation); median averages the two central values for even n.
  Keep cold runs separate; timing repeats are not independent correctness samples. A future model
  experiment needs separately pinned serving/load and token/cost measurements.
- Locality: distinguish proposed local eligibility from actual successful local
  execution. Actual household availability/resolution, cloud costs and satisfaction
  are **unmeasured** here. A request needing unavailable calendar or web capability
  is not counted as locally solved just because the router runs on a CPU.

Freeze one or more variants per family before test unsealing. Family correctness
requires every variant to have an acceptable status and, for plan, all required
and no prohibited/unlisted capabilities (optional allowed). For non-plan, emit no
capabilities. Family coverage requires all frozen variants to produce non-abstaining, valid
outputs; an error or abstention makes family coverage zero. Report exact family
weighting, not variant-weighted accuracy. Missing,
malformed, timeout and runtime-error predictions score incorrect and zero coverage;
retain them in the denominator. Safety violations remain blocking regardless of
status. Unresolved labels must be adjudicated or excluded with documented counts
**before** freeze; no post-result removal/replacement. If any required stratum lacks
six valid test families, report insufficient evidence rather than renormalizing.

Passing is eligibility for further review, not deployment or automatic promotion.
If benefit is absent, safety fails, uncertainty is too broad or effort exceeds the
budget, retain the existing rules and document the negative/inconclusive outcome.

## Calibration and learning to abstain

A similarity score is not probability. Keep probability null unless a separately
frozen calibrator predicts a defined event (for example, complete capability-set
correctness) and passes held-out checks. Compare temperature scaling for suitable
logits, Platt scaling for scalar scores and isotonic only with adequate independent
samples. Choose a method on development data; fit only on calibration families.
Do not try several methods on test and retain the most flattering result.

Report Brier score, reliability diagrams, ECE with stated binning/denominators and
uncertainty, plus risk-coverage curves. Sparse bins are merged/marked insufficient;
ECE alone is not a pass criterion and differs under binning. The proposed 60-family
calibration split is exploratory only. No task-class “0.9 means 90%” claim from it.
A future probability claim needs a separately powered calibration/holdout expansion
with at least 100 independent observations in the claimed probability band/task
slice and a preregistered interval-width criterion. Abstention thresholds are chosen
on calibration under the risk/coverage constraint, then frozen; human escalation is
an acceptable labeled outcome, never permission to widen tool privileges.

## Exact post-approval record/state design — not implemented or authorized

The present validator is **not an executable human-label pilot**. It only checks
synthetic metadata and always returns human_labels_verified=0. Protocol acceptance
alone cannot switch it into a collector. A second, concrete implementation/retention
readiness gate is required before completing any real human-authored case form.

Proposed S0 records use immutable objects, stored only in the approved location:

- Case envelope: protocol/version, random case/family IDs, stratum, content artifact
  reference and digest, explicit authored-context reference, origin
  `human-authored-s0`, split `unassigned`, creation time, author reference and
  retention `s0-approved`. No body or identifying hash is published as metadata.
- Content review: separate immutable review ID, exact case-artifact digest,
  human reviewer reference, review time, checks for no real/copied/disguised private
  facts, no identifiers, no secrets, and accept/reject. A declaration is not a
  detector; the workflow must authenticate the reviewer or leave it unverified.
- Independent labels: immutable label IDs, case/protocol digests, labeler references,
  timestamps, required/optional/prohibited sets, acceptable outcomes, sensitivity,
  egress and uncertainty codes. Each labeler sees the frozen case, not the other's
  labels or router outputs. Revisions add new records with supersedes links;
  never overwrite the first label or mistake a correction for another independent case.
- Adjudication: references both label IDs/digests, adjudicator, decision, discrepancy
  category, final labels and external factual reference when relevant. Single-owner
  pilot labels stay explicitly personalized/unverified for independent correctness.
- Split freeze: custodian identity, family-level assignments, accepted content/label
  digests and independently held holdout manifest. No developer access to test
  content/labels before unsealing. Retain an append-only audit of each transition.

State sequence: unapproved -> content-review-pending -> content-approved ->
label-A-pending -> label-B-pending (required for all main-test families) ->
adjudication-pending -> eligible-for-split -> frozen. Rejected/excluded are terminal
without downstream training/export. Changes after freeze create a new version and
require an unseen test set; prior evidence remains immutable. Required human
identity/custody controls and approved storage path are unresolved. Do not implement
these states by trusting a JSON `human_verified` boolean. No human record exists now.

## Concrete approval gate

Jason accepted the design below on 2026-09-25. This historical design decision
does not open collection; the separate implementation/retention readiness gate
remains required:
1. S0-only 30-family pilot and its effort/ambiguity stop rules.
2. No real interaction capture or private-data retention.
3. Human labeling/adjudication method and independent holdout custody before main study.
4. Proposed metrics/thresholds, acknowledging that the 300-family study needs a later
   effort decision and may still be statistically inconclusive.

Acceptance of this protocol is design approval only, not permission to collect.
No labels have been collected. The empty template contains zero cases. The metadata
validator accepts only design/synthetic fixtures and grants no authenticity or
collection authority. Rollback is to discard the unused protocol/tool/template;
retain historical design/testing evidence. No production rollback is required.


## Method references and proposal provenance

Calibration method guidance follows [scikit-learn's official calibration
documentation](https://scikit-learn.org/stable/modules/calibration.html), including
disjoint calibration data and caution interpreting Brier score as calibration
alone. Temperature scaling is supported as a candidate method by [Guo et al.,
2017](https://proceedings.mlr.press/v70/guo17a.html); that paper does not validate
this HomeLab corpus, thresholds or a particular router. Sources checked 2026-09-25.
All sample sizes, effort limits, margins and resource thresholds above are local
proposals for preregistration, not literature-derived guarantees or measured facts.
