# Aster Ask completed-answer qualification — proposed protocol v0

**Status:** Design proposal, 2026-10-12. No corpus, latency budget, release
threshold, cloud batch or production route is authorized by this draft. Aster
Adaptive owns this task bar; B60 may supply runtime candidates and measured
results after the protocol and lab lease are frozen together.

## Question to answer

For which *specific Aster request classes* does a candidate local stack produce
a correct, useful and policy-compliant result at an acceptable user-facing
latency and resource cost, compared with the current local control and an
eligible Codex fallback? The answer may differ by class and reasoning mode.
The published [30-case routing regression](ask-routing-development-v1/README.md)
answers a narrower question and cannot fill this role.

## Unit of evaluation and boundaries

One case consists of a user-style request, declared capability availability,
permitted context fixture, expected observable outcome, privacy/locality class,
maximum permitted tool scope and an adjudication rubric. A case has a stable
opaque ID and a provenance record. Raw private prompts, secret values and
hidden reasoning do not belong in Git. Synthetic context is preferred for
development. Any real-interaction case requires a separate retention and
consent decision, source-local redaction, restricted custody and an exportable
content-free result.

The test distinguishes **route selection**, **completed answer quality**,
**grounded reasoning**, **tool authorization/execution** and **latency**. A
candidate may be judged for answer quality with read-only fixture tools; this
never grants access to live systems. Identity and policy decide whether any
real tool call is allowed. A model's own claim of safety or confidence cannot
override a deterministic deny.

## Candidate profiles

Pin each candidate's model/quant, runtime revision and binary/unit hashes,
prompt and adapter hashes, reasoning mode, context length, cache type, tool
mode, egress boundary and hardware allocation. Reasoning-on and reasoning-off
are separate profiles. A change to any pinned element is a new candidate;
do not combine its samples with the prior profile. Record token and call counts,
subscription/provider limits and costs where observable; mark unavailable
fields `UNKNOWN`, never zero.

The comparison set contains the accepted current local control, one or more
B60 candidates and, only after exact reviewed consent and an equivalent
subscription-compatible adapter, a Codex fallback. The existing D3 manual
answers cannot be retrofitted into this corpus. Deterministic timer/light
paths remain their own control and outage requirement; a model is not a
candidate replacement merely because it can describe the intended action.

## Request classes and outcomes

| Class | Observable pass condition | High-cost error to count separately |
|---|---|---|
| Timers, lights, media | Correct entity, action and confirmation in a fixture; local deterministic path remains available. | Wrong household target or invented completion. |
| Stable public facts | Correct answer or justified abstention under a frozen reference. | Confident false fact. |
| Live web | Correct dated answer with valid cited source in a frozen or replayed retrieval fixture. | Stale or fabricated source. |
| Calendar and private context | Correct answer from permitted synthetic context, no unnecessary export. | Disclosure or omission of required private context. |
| Mixed public/private reasoning | Correct composition with explicit uncertainty and local join when policy requires it. | Private-context egress or failure to combine required sources. |
| HomeLab status/diagnosis | Correct reading of fresh, named, sanitized evidence; uncertainty and next check fit the evidence. | Invented state, stale evidence treated as current, or an unauthorized fix. |
| Ambiguous/unsafe | Appropriate clarification, abstention or policy denial. | Action or false certainty when the target is unresolved. |

For each class, freeze a rubric covering factual correctness, completeness,
source/evidence freshness, policy conformance, calibration or abstention and
useful completion. Keep human adjudication blind to backend where practical.
Record disagreement and adjudication rather than silently rewriting labels.
Rare high-impact errors need explicit negative cases and independent boundary
tests; a small zero-failure sample cannot certify their absence.

## Latency and load measurement

Measure from Aster's accepted request to a **completed useful answer** or
terminal failure. Also record first response, route decision, retrieval/tool
time and inference time separately when observable. Include unsuccessful and
abstained cases; do not improve p95 by dropping failures. Report per-class
sample count, p50, p95, spread, timeouts, retries and censored runs. With few
independent cases, label p95 descriptive and disclose its uncertainty.

Freeze at least these profiles before a finalist comparison: warm resident
model at idle, cold/reload where applicable, and representative shared load.
Declare cache reuse, case order/random seed, concurrency, prompt/context
lengths and warmups. Alternate candidate/control order where practical, run
the current control before and after the series, and repeat finalists in
separate sessions. Do not compare Mac rule microseconds, B60 route-request
milliseconds and cloud completed-answer seconds as if they share a boundary.
The B60 target of 27B+ reasoning-on at current 9B useful-answer latency is a
testable engineering hypothesis; per-class acceptable budgets must be set
from current Aster workflows and Jason's expectations **before** looking at
finalist scores.

## Evidence and promotion sequence

1. **Development:** use public synthetic cases for adapter and regression
   debugging. Preserve all attempts and failed configurations.
2. **Qualification preregistration:** freeze class definitions, independent
   cases, labels, scorer/policy versions, safety floors, latency/load profiles,
   acceptable risk and rollback. Keep keys outside candidate prompts/training.
   The old S1 set is closed incomplete and is not a qualifying holdout.
3. **Blind comparison:** run each eligible backend on equivalent inputs and
   allowed capabilities. Save sanitized records plus dataset/scorer/policy,
   candidate, runtime and manifest digests; retain timeouts and disagreements.
4. **Review:** reject a candidate that violates a mandatory boundary even if
   its average score or speed is better. A proposed promotion packet names
   earned classes, remaining GPT fallback, quality/latency tradeoffs, resource
   impact, recovery/soak and owner decision. Two sessions support engineering
   repeatability but do not alone establish rare-event safety or p95 certainty.
5. **Shadow, canary, continue monitoring:** effect-free shadow first; then a
   separately approved reversible class-specific canary. Roll back on a
   preregistered regression or boundary failure. New production becomes the
   next control without erasing the previous limits or evidence.

## Work still required

No independent answer-quality cases, adjudicators, privacy retention decision,
per-class current-control latency distributions or release floors are frozen
yet. Build those before asking B60 to optimize against a numeric bar. Aster
can first run a *small synthetic feasibility set* to prove capture and scoring,
clearly marked development-only; it must not be used to claim a release pass.
