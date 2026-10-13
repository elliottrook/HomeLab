# Post-policy personal and overnight analysis comparison

Date: 2026-10-10

Status: **comparison passed; 9B reasoning-off selected for this separated role**

## Question

After deterministic policy owns household execution, privacy refusal and
sysadmin escalation, can Qwen3.5-9B efficiently handle permitted personal
summaries and scheduled overnight analysis? Does a bounded thinking budget add
enough quality to justify its latency?

The frozen 20-case synthetic suite SHA-256 was
`ca1ecae58cd588b2251ff0c5ef10d36f0fe13ff3fec05e4f194d58b67c8767bd`.
Four refusal/escalation cases belong to deterministic policy and were not sent
to the summarizer. The remaining 16 prompts and content requirements were
unchanged across all model arms.

## Contract correction

The first 9B run incorrectly asked the model to re-decide outcome, privacy and
routing after policy had already selected the role. Reasoning-off scored 2/20
and thinking-256 scored 9/20, primarily because correct summaries were labelled
`refuse`. Those immutable reports are retained as contract-failure evidence,
not model-selection evidence:

- reasoning-off SHA-256
  `8d260fa0317d6af54805ff4ce192f0be4ab49bb43cbe9ee567fac34443acc984`;
- thinking-256 SHA-256
  `9e9afbd412ef87b980cacfc52af3d14eb3e4677b3975ab2de183ff6155373577`.

The corrected runner makes the model responsible only for `summary`, `facts`
and `uncertainties`. It does not let the model route, refuse, authorize, execute
or claim an action. Forbidden assertions are checked only in asserted summary
and fact fields, so wording such as “whether it was successful is unknown” is
not misclassified as a success claim. Three focused scorer tests cover this
boundary.

## Results

| Arm | Mechanical score | Human semantic review | Median request latency | Immutable SHA-256 |
|---|---:|---:|---:|---|
| Qwen3.5-9B reasoning-off | 12/16 | 16/16 | 2.488 s | `51ae6c2bc4188f61eb984fcfff3308eb8ea209ce73f71fc4ee59416b027736e8` |
| Qwen3.5-9B thinking-256 | 14/16 | 16/16 | 7.938 s | `a24bc36bd27a5aa376f39b0ccd6b924e6d96ad3f087d08fe280c2ba865fef7e4` |
| Accepted Qwen3.8-27B reasoning-off | 15/16 | 16/16 | 11.051 s | `4ed39ad62821e3f71449ccbe2e62bc85eb963031e5530fc5bbb5abbdbdca430c` |

All mechanical misses were reviewed. They were exact-word false negatives, not
semantic failures: stating a feed was generated 30 hours ago without the word
“stale”; preserving both observations and timestamps without repeating source
labels; saying no status/result was provided without the word “missing”;
omitting the word “local” from an otherwise correct private/public comparison;
quoting both conflicting medication notes without selecting a dose; and saying
two charges appeared identical while leaving duplication explicitly unclear.

Reasoning-off 9B was approximately 4.4 times faster than accepted 27B and 3.2
times faster than its own thinking arm. Thinking produced no semantic-quality
gain on this bounded role.

## Safety and restoration

The exact pinned 9B model and llama.cpp b11429 Vulkan runtime were reacquired in
LXC 110 tmpfs with their previously accepted hashes. The candidate used the
existing protected API-key file; no credential value entered output or evidence.
News workers were idle and their timers were stopped only during candidate
load. Every run used an exit trap. Final checks found accepted production
active and healthy with zero restarts, the candidate inactive, News timers
active, accepted hashes unchanged, B60 still on `xe`, BMG G21 enumerated, and
no matching reset/hang/device-loss/OOM kernel event. All transient model,
runtime and staging copies were removed; immutable mode-0600 reports remain in
the protected evidence root.

## Decision

Select Qwen3.5-9B reasoning-off for the separated post-policy local-summary and
scheduled-analysis role. Do not use its thinking mode by default. Keep 27B as
accepted production until a separately approved deployment defines model
residency, service isolation, fallback and monitoring. This result does not
authorize 9B to handle household effects, privacy decisions, consent,
authorization, or deep sysadmin diagnosis; those remain deterministic policy
or sanitized GPT-backend responsibilities.
