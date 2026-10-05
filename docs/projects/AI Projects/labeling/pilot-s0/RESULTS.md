# S0 manual pilot — collection cap reached

## Observed evidence

Thirty AI-proposed cases and labels were accepted by Jason in three ten-case
batches. Ten strata have three families each. Twenty train/ten development,
zero calibration/test. Exact source artifacts and hash-bound acceptance records
are retained; `summary.json` pins all nine proposal/acceptance/effort artifacts.
All30 case hashes, family uniqueness, counts and splits were checked locally.

Reported active review: **5 + 5 + 3 = 13 minutes**, an approximate **26 seconds per
case average**. No per-case timing, actual median, setup effort or AI drafting cost
was measured. Batch-specific conditional median bounds50/50/30 seconds are below
the120-second stop rule; these bounds depend on approximate aggregate self-report.
All30 case/label decisions accepted; zero unresolved annotation decisions. That is
not 100% router accuracy: no router or model was evaluated. Clarify/deny labels
are successful proposed outcomes, not executed results.

## Interpretation and limitations

**Supported:** reviewing this small set of AI-proposed synthetic examples was
manageable for Jason, with no reported unresolved case/label decisions.

**Not established:** independent labeling effort, correctness, real workload
coverage, calibration, routing improvement, privacy in operation, or suitability
of any model/harness. Jason saw proposed labels and accepted batches; suggestion
anchoring and correlated acceptance remain material risks. These are personalized
human-reviewed examples, not blind human-authored labels or independent gold.
Names/semantic similarity and cross-family overlap have not received an independent
leakage audit; nominal family IDs and train/dev splits alone do not prove statistical
independence. No calibration or held-out test claims are justified.

The original protocol's independent/blind labeling aims were not demonstrated by
this explicitly approved proposal-review workflow. Report the observed13 minutes
as review effort, never as a measured cost for independent annotation or an estimate
for the future300-family study. All examples have empty optional-capability sets;
composition/negation/adversarial diversity is limited. Accepted labels may still
contain errors. Do not change or silently relabel them without a new revision and
human review.

## Decision and next bounded step

Collection is closed at the authorized30-family cap. The evidence supports a
manageable review workflow; it does not graduate the Decision/Learning Plane or
authorize evaluation. Do not generate more cases under this approval.

Recommend a separately reviewed offline experiment plan using these exposed
train/dev examples for integration and descriptive error analysis only. Specify
baselines, data adapter validation, metrics, no-network safeguards and negative
results before requesting evaluation authority. Do not use this corpus to claim
unbiased generalization or tune and test on the same data. A subsequent independent
or blind labeling study needs its own scope, evidence and approval; the300-family
study remains excluded. M4 human checkpoint acceptance/custody remains unresolved.

Durable sanitized Git retention follows pilot approval; continued-use review is
still due at the original day30/day90 points (26October and25December2026). No
scheduler is created here. Draft copies retain their original seven-day expiry;
accepted repository copies have different, durable retention. No push authorized.
