# S1 representative routing holdout — proposed plan

Date: 2026-09-26

Status: **PROPOSED; NO COLLECTION OR EXECUTION AUTHORIZED**

Owner and gold-label authority: Jason

Purpose: supply the smallest credible independent evidence for the remaining M3
routing gate. This plan does not authorize a router, model, service, shadow pilot,
production route, permission, context source or retention change.

## Why S0 cannot be reused as the holdout

The S0 pilot contains 30 AI-proposed synthetic families. Jason reviewed proposed
cases and labels, and its ten development families were exposed to implementation
and result review. It is useful personalized development evidence, but suggestion
anchoring, author/evaluator correlation and test exposure prevent an independent
generalization claim. No resplit, relabel, paraphrase or renamed S0 record may enter
S1. S0 remains training/development evidence for the fixed nearest baseline.

## Decision question

On new, engine-blind requests representative of Jason's intended use, do any of
the retained routing baselines produce capability/status plans reliable enough to
justify a later read-only shadow proposal?

The permitted outcome is **advance one candidate to a separately approved shadow
plan**, **retain for more evidence**, or **reject**. S1 cannot promote a router into
the production path.

## Corpus and burden

Collect exactly **50 families**, five in each stratum:

1. timer/alarm;
2. Home Assistant/household control;
3. media;
4. general knowledge;
5. calendar;
6. public web research;
7. mixed calendar/web/personal-context composition;
8. personal knowledge/context;
9. HomeLab/sysadmin; and
10. ambiguous, deny, unsupported or clarification-required requests.

At least 15 families must require more than one capability or an explicit
clarify/deny/unsupported decision. At least ten must contain negation, changed
intent, an unavailable dependency, a privacy/locality constraint or a misleading
surface keyword. These quotas overlap and are fixed before collection. Do not add
near-duplicate paraphrases to satisfy them.

The target is roughly 30–60 minutes of human work based on S0's 13-minute
AI-assisted review, with additional allowance because S1 forbids label suggestions
and asks Jason to supply the request. Stop and retain partial effort evidence if
active work reaches 90 minutes or if ten label decisions remain unresolved. A
partial corpus is feasibility evidence and does not run.

## Human workflow and label independence

For each family Jason supplies, without seeing an engine prediction or AI-proposed
label:

- a sanitized request he might realistically make;
- accepted status set: `plan`, `clarify`, `deny`, `unsupported` or explicit
  `abstain` where that is truly acceptable;
- required, optional and prohibited capabilities from the frozen registry;
- sensitivity and required locality class;
- a one-sentence observable reason; and
- whether an unavailable dependency should clarify, degrade or fail closed.

No assistant pre-fills, recommends or ranks labels. A local form may validate
syntax and registry membership, but it must not call a model, show predictions or
infer missing values. Jason may revise a record before acceptance; every revision
gets a new hash and invalidates the prior acceptance.

This creates **personalized human gold**, not inter-annotator agreement. Jason is
both author and label authority, so annotator independence and population-level
validity remain unclaimed. Independence here means the cases are new, labels are
human supplied without engine/AI suggestion, and engines cannot inspect gold fields.

## Privacy and custody

- Use placeholders for people, events, locations, sites and systems. No secrets,
  tokens, account identifiers, private URLs, exact calendar contents, IP addresses,
  health data or copied conversation logs.
- Default retention is sanitized accepted records plus provenance. Drafts expire
  after seven days. Rejected or sensitive drafts are deleted locally after a
  retained count/reason record that contains no prompt text.
- Before collection, select and test one local custody path. Git may contain only
  content Jason explicitly accepts as sanitized and durable. A private scratch
  path must be excluded from Git, indexing, Aster knowledge snapshots and backups
  unless separately approved.
- Freeze accepted content and labels before any engine receives request text. The
  scoring reference is passed only to the evaluator, never to a router input,
  training path, prompt or diagnostic context.
- Publication and mirror synchronization remain a separate push decision.

## Frozen engines and inputs

Evaluate only these retained baselines:

1. always abstain;
2. the existing keyword rules; and
3. fixed-threshold TF-IDF nearest, trained only on the 20 S0 train families with
   threshold 0.2 and the existing deterministic tie rule.

Use request text only. S1 supplies no oracle-like synthetic context. Confidence is
null for every engine: similarity and rule matches are not calibrated probability.
Do not tune rules, threshold, tokenization, training rows, status order or capability
registry after collection begins. Pin exact source, registry, S0 training, adapter,
evaluator and runtime hashes before execution. If intended-source reconciliation
changes an engine, freeze a new experiment version rather than editing S1 in place.

No semantic router, embedding model, local LLM, Jev or cloud model is added to this
holdout. A new engine needs a separate preregistered challenger version and cannot
learn from S1 labels.

## Metrics and preregistered decision rules

Primary units are 50 independent families, never presentation variants. Report:

- complete plan agreement and Wilson 95% interval;
- status agreement;
- missing, extra and prohibited capability cases;
- abstention, valid-decision coverage and error among covered cases;
- clarify/deny/unsupported results separately;
- per-stratum counts with explicit small-denominator warning;
- pairwise engine disagreement and human error classification;
- invalid/missing outputs, latency p50/p95, peak RSS and actual calls/retries; and
- local/cloud/model use as execution facts, not inferred production percentages.

A candidate may be proposed for a later read-only shadow only if it has all of:

- at least 45/50 complete agreements;
- zero prohibited-capability predictions;
- zero invalid outputs;
- at least 12/15 complete agreements on the compositional/constraint quota;
- at least 8/10 complete agreements in the ambiguity/deny/unsupported stratum;
- no hard privacy/locality violation; and
- deterministic rerun identity with p95 routing latency below 25 ms on the chosen
  CPU-only execution host.

These are programme guardrails, not a claim of statistical production readiness.
Failure retains the result and blocks shadow advancement. If multiple candidates
pass, prefer the one with fewer extra capabilities and then higher abstention on
errors; latency breaks only a remaining tie. Do not tune against S1.

## Execution boundary

One frozen evaluation is permitted only after separate approval of the complete
50-family manifest and release hashes. The runner must be CPU-only, offline,
dependency-pinned, unable to invoke tools or subprocesses, and capped at 60 seconds,
256 MiB peak RSS and 2 MiB output. It consumes an engine-input projection separate
from the evaluator's gold projection. Duplicate run identity fails closed.

The disposable VM mechanism proven by S0 is an acceptable offline evidence boundary,
but its roughly 135-second lifecycle is overhead, not router latency. Reuse is
optional; a simpler local sandbox is acceptable only if its no-network/no-process
and read/write bounds are verified before corpus access. No production guest,
credential, model service or GPU is required.

## Evidence lifecycle and separation

1. **Observe:** retain only sanitized intended requests and explicit human labels.
2. **Measure:** validate provenance, corpus quotas, isolation and frozen hashes.
3. **Hypothesize:** the three fixed baselines have no post-collection changes.
4. **Review:** Jason accepts exact records; technical review accepts the frozen
   adapter/evaluator/release without seeing predictions.
5. **Experiment:** execute once inside the approved boundary.
6. **Evaluate:** score all families, retain failures and classify disagreements.
7. **Decide:** advance to a shadow proposal, retain, or reject; no direct promotion.
8. **Document:** store result, hashes, limits and decision; continue monitoring only
   if a later shadow is separately approved.

Proposal, label acceptance, runner implementation, evaluation and shadow authority
are separate records. An engine cannot change the evaluator, registry, labels,
thresholds or acceptance rules.

## Acceptance before collection

Collection must not begin until Jason approves one concrete packet containing:

- this plan hash;
- blank no-suggestion form/schema and syntax-only validator hashes;
- frozen capability/status/privacy registry hash;
- chosen local custody and tested exclusion/restore behavior;
- exact 50-family/quota and 90-minute stop bounds;
- retention and day-30/day-90 review dates; and
- an explicit statement that collection does not authorize evaluation.

After collection, a second packet freezes the accepted corpus and evaluation
release. Evaluation requires a separate exact approval. No further case generation,
tool installation, service, deployment, production access or Git push is implied.

## Rollback and stop conditions

Before acceptance, discard drafts and the unused helper. After acceptance, stop
new collection, preserve provenance and mark any withdrawn record excluded without
rewriting history. Stop immediately on secret/private-data entry, label suggestion,
engine output exposure, custody leakage, quota ambiguity, hash mismatch or unresolved
registry term. No production rollback exists because this plan changes no runtime.

## Current next action

Prepare the blank form/schema, syntax-only validator, fixture tests, custody choice
and immutable collection packet. Use invented fixtures only. Then present the exact
collection gate; do not create any S1 family before approval.
