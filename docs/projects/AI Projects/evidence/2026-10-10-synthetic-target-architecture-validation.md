# Synthetic target-architecture validation

Date: 2026-10-10

Status: **engineering proxy complete; neither model configuration is qualified
for unattended personal analysis**

Follow-up: the model-owned routing conclusion in this record is superseded by
the code-owned, quote-grounded v2 architecture and results in
`2026-10-10-grounded-target-architecture-v2.md`. This file remains the evidence
for why that separation was required.

## Question and boundary

Real household timers, media providers, Home Assistant entities and a sufficient
corpus of private overnight records are not yet available for a representative
field test. This evaluation therefore synthesizes both layers proposed for the
target Aster architecture:

1. a side-effect-free deterministic household-intent contract; and
2. a 20-case synthetic personal/overnight analysis and routing corpus.

All content is invented. The results measure behavior under the recorded prompt
and schema, not real-world qualification. TTS is outside the test and unchanged.

## Deterministic household layer

`aster_household_contract.py` is a reference parser, not a deployed service. Its
ten unit cases cover an explicit fractional-minute timer, conflicting timer
durations, ambiguous alarm time, exact timer cancellation, media availability
and room selection, exact Home Assistant entity/state selection, unknown entity
handling and an unrelated request. Ambiguous or unavailable cases return no
effect. All ten cases pass as part of the 66-test local eval suite.

This supports separating timers/media/Home Assistant actions from model prose.
It does not prove integration with a real provider, device registry or execution
adapter.

## Frozen synthetic analysis corpus

The 20 cases cover inbox priorities, calendar conflicts, contradictory medicine
notes, school changes, photo and backup reports, possible duplicate expenses,
stale news, contradictory sources, missing evidence, retrieval injection,
family isolation, private/public joins, public knowledge, sysadmin escalation,
overnight safety ordering, timezone ambiguity and duplicate-photo candidates.

The initial 27B smoke run exposed two evaluator-contract problems before a 9B
arm saw the final contract: an artificial distinction between two local route
names and an unstated permission to analyze supplied private data locally. Those
diagnostic artifacts were retained but rejected. The final contract uses one
`local` route and explicitly permits local analysis while prohibiting external
disclosure and unconsented cross-family access.

## Results

| Arm | Strict pass | Median latency | Evidence SHA-256 |
|---|---:|---:|---|
| Accepted Qwen3.8-27B, reasoning off | 3/20 | 14.390 s | `242f792491623ea5da8b2093d7528ef13df76d01328651f0ca5e15977c68fb34` |
| Qwen3.5-9B Q4_K_M, reasoning off | 2/20 | 3.612 s | `8d260fa0317d6af54805ff4ce192f0be4ab49bb43cbe9ee567fac34443acc984` |
| Qwen3.5-9B Q4_K_M, thinking budget 256 | 9/20 | 9.114 s | `9e9afbd412ef87b980cacfc52af3d14eb3e4677b3975ab2de183ff6155373577` |

Raw immutable reports remain on LXC 114 under
`/var/lib/b60-inference/evidence/aster-analysis-v1-*.json`.

Strict scores include some taxonomy/string failures that a human would not call
wrong prose. For example, `local` instead of `none` on a refusal is not a data
leak, and the phrase “whether the job completed successfully” triggered a
forbidden-word assertion even though it correctly expressed uncertainty. The
scores are therefore not stand-alone quality percentages. The structured fields
are still operationally important: a downstream router cannot safely ignore an
incorrect `refuse`, `escalate` or sensitivity value merely because the prose is
good.

## Semantic review

Both reasoning-off arms repeatedly extracted the right facts but labelled safe
local summaries as `refuse`. The 27B also misclassified the ordinary overnight
status prompt as an injection. The 9B reasoning-off arm routed a private expense
anomaly to cloud sysadmin analysis. These configurations are unsuitable for an
unattended overnight pipeline without a stronger deterministic policy layer and
contract tuning.

Bounded thinking materially improved 9B: it passed inbox, calendar, medicine,
backup, expense, private/public join, public fact, sysadmin route and timezone
cases, while remaining faster than 27B. It is not safe to select yet. In the
deep-sysadmin case it invented disconnect events, restart cycles and missing
heartbeat tuning that were not present in the prompt. It also continued to
refuse several harmless summaries and produced inconsistent sensitivity labels.

## Decision

- Keep the accepted 27B production service for the current architecture; this
  synthetic run provides no basis for a production model promotion.
- Implement the deterministic household executor before changing models.
- Retain 9B with bounded thinking as the strongest efficiency candidate for the
  separated personal/overnight analysis role, but require prompt/contract repair
  and a new sealed corpus with a zero-unsupported-fact gate.
- Do not use 9B reasoning-off for private analysis or sysadmin routing in its
  tested form.
- Keep TTS evaluation as a separate project and do not infer anything about
  voice quality from these model results.

## Recovery evidence

The candidate ran only from tmpfs. The finalizer restored accepted production;
the candidate is inactive, accepted binary and unit hashes match, health is
`ok`, both news timers are enabled and active, `xe` and BMG G21 Vulkan
enumeration remain present, and no relevant recent kernel/GPU failure appeared.
Authenticated post-restore generation passed with evidence SHA-256
`09114da0a0ba573e06c398c15cc6848e0026358c2758233d83911312544b42ba`.
The staged evaluator, model and runtime were removed; 21 GiB root-disk headroom
and 13 GiB available guest RAM remained after cleanup.
