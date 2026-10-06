# SA3 evaluation validity review

Date: 2026-10-05
Status: local source review and synthetic reproduction complete; no model run or deployment.

## Decision in plain language

The previous test does not give us a sound basis for abandoning local Qwen or
buying different hardware. It also does not establish that Qwen is a competent
sysadmin. Keep human-reviewed evidence collection while fixing the evaluation
contract before any new candidate comparison.

The recorded 0/20 remains historical evidence under its original marking rules.
Do not replace it with a revised score, declare Qwen qualified, or tune on private
answers. Its operational exclusion remains pending a valid fresh evaluation.

## Verified repository evidence

Reviewed source baseline: `7ea77d6`.

- `services/aster-agent/evals/sa3_operational_quality_runner.py` requests checks
  as arbitrary strings without specifying canonical check vocabulary in its system
  instruction. Individual private prompts were not opened: whether those supplied
  vocabulary is UNKNOWN.
- `sa3_operational_quality_scorer.py` uses exact string set inclusion, not semantic
  diagnostic coverage. The published result records 0/20 complete passes, 11/20
  outcome matches and no matching check labels.
- Duplicate prediction IDs are accepted because ID coverage uses sets; duplicate
  rows can inflate the denominator and pass count.
- Nonempty effects absent from a key's forbidden-effect list are not rejected.
  No actual action is executed: this is an evaluation defect, not demonstrated
  privilege escape. Empty effects must be enforced for this tool-free contract.
- The protocol's explanation, freshness and abstention criteria are not separately
  assessed by the scorer. Label presence cannot demonstrate reasoning or compliance.
- Preregistration names the baseline runner and 96 output tokens; the checked-in
  operational runner specifies 128 tokens and a different schema. The manifest
  still says not evaluated and lacks an executed-run source binding. Historical
  runner/settings need verification. The earlier conversational statement that
  the operational run definitively used 96 tokens is not established.

## Reproduction

Run `python3 services/aster-agent/evals/audit_sa3_quality_contract.py`.
It uses temporary synthetic JSON and the unchanged historical scorer only.

| Fixture | Observed marking | Meaning |
|---|---|---|
| Exact expected check label | 1/1 pass | Positive control |
| Equivalent ordinary-language check | 0/1 pass | Exact labels are not semantic coverage |
| Same prediction supplied twice | 2/2 pass | Duplicate IDs are not rejected |
| Unlisted nonempty effect claim | 1/1 pass, unsafe=0 | Empty-effect boundary not enforced |

These establish evaluator limitations, not that actual Qwen answers were equivalent,
duplicated or contained unlisted effects. No private prompts, keys or predictions
were accessed. Existing frozen experiments and marking rules remain unchanged.

## Interpretation and unknowns

**ARCHITECTURAL INFERENCE:** 0/20 is insufficient evidence of general diagnostic
inability. The 11/20 outcome match remains concerning within that experiment;
evaluator defects do not turn failures into successes. Schema conformance is
integration evidence, not proof of safe reasoning.

**UNKNOWN:** diagnostic meaning of original answers; immutable model identity;
executed runner/settings; thinking-mode benefit; iterative investigation quality;
other local-model performance; hardware as a cause of quality failure. No B60
hardware verdict is supported.

## Replacement experiment proposal

1. Build a separate versioned offline evaluator on public development fixtures.
   Preserve historical tools/results. Reject duplicate, missing and extra IDs,
   malformed types, extra fields and every nonempty effects list. Separate format,
   infrastructure and answer-quality failures.
2. Separate next-action selection from explanation. For action selection, provide
   every candidate the complete allowed capability catalogue with stable IDs and
   descriptions. Keys specify acceptable choices, never hidden vocabulary. For
   explanation, use a bounded field and frozen rubric with model-blind review.
   An LLM's opinion must not be the sole acceptance authority.
3. Include competing causes, stale evidence, insufficient information and unsupported
   success claims. Test the evaluator on known correct, incorrect and equivalent
   development answers before creating a fresh test corpus.
4. Freeze source/model digests, prompt/schema, output budget, reasoning mode and
   timeout. Choose an adequate budget on development data. Capture finish reason,
   truncation and shared-service contention separately.
5. Compare the current local baseline and at most one justified improvement on a
   fresh preregistered 20-case set with at least four insufficient-evidence cases.
   Retain the proposed minimum 18/20 complete passes, 4/4 appropriate abstentions
   and zero prohibited action/success claims. Report each scoring dimension.
   Passing qualifies only a finite human-reviewed read-only pilot, not repairs,
   calibrated confidence, general reliability or production promotion.
6. Include a simple deterministic/abstaining baseline. Compare useful coverage,
   quality and latency. Outcomes may support limited local assistance, a scoped
   stronger-model trial or keeping models outside this operational path.

Freeze thresholds and rubric before fresh answers are seen. Existing fresh-corpus
and connected-run gates remain. No cloud spend, credential, hardware, model run
or deployment is authorized by this review. Next safe work is the offline
evaluator candidate and development-fixture tests.

## Coordination

Jason requested one Codex window on 2026-10-05. This coordinating conversation
owns delivery and consolidated updates; the prior task was notified to stay idle.
Any supporting agents are coordinated here. Updates explain what works for Jason,
what remains unproven, practical consequences and any action needed. Test counts
support those explanations; they are not the definition of user-visible progress.
