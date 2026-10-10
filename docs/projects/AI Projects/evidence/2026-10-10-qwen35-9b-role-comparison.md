# Qwen3.5-9B local-role comparison

Date: 2026-10-10

Status: **9B rejected as an immediate drop-in replacement; retained as a
summary-only challenger behind deterministic routing**

## Question

Can reasoning-disabled Qwen3.5-9B replace the accepted reasoning-disabled
Qwen3.8-27B for Aster's local household, personal-summary, privacy-routing and
sysadmin-escalation decisions while materially reducing latency?

The comparison used only synthetic data. Both arms received the same explicit
decision contract, JSON schema, 20 cases, temperature zero, seed one and
256-token output limit. The accepted arm used the production Qwen3.8-27B
service. The challenger used the transient Qwen3.5-9B Q4_K_M and official
llama.cpp b11429 Vulkan runtime recorded in the companion B60 screening.

## Invalid first control

The initial control scored 1/20 because the scorer required canonical argument
names and routing labels that the prompt did not define. Review of the 27B
answers exposed this contract defect before 9B saw any case. That run is
preserved at
`/var/lib/b60-inference/evidence/aster-local-role-27b-20261010.json` on LXC 114
with SHA-256
`0ba1dc25aedd76908eb04d1981eae58a0c9917fd9952a82c7435bb9a25841327`.
It is not model-quality evidence.

The corrected v2 contract explicitly defined every decision, capability,
privacy class and executable argument name, and accepted limited predeclared
equivalents for safe clarification/refusal behavior. Runner SHA-256 was
`15db3db86f7ac42cc444386b35fb1b62b60d4eda12ab2710f0bab62ed0902a1b`;
corpus SHA-256 was
`f16974de558a62321c4d439f504aa6805659381b3b43320d59afbc526dca40b2`.
It was frozen before the 9B arm.

## Fixed-contract result

| Arm | Exact cases | Median request latency | Immutable result SHA-256 |
|---|---:|---:|---|
| Accepted Qwen3.8-27B | 16/20 | 7.710 s | `290bb9d27d895d61ee394ab440e17638f231210f1b9a9fa64081811c2be48c3f` |
| Qwen3.5-9B Q4_K_M | 11/20 | 3.059 s | `ea4adb143f0c7251815eece001dfb45a2284d24fd4a5c3362a3b342e21062a40` |

The 9B arm reduced median end-to-end latency by about 60%. This agrees with the
separate raw/API screening that measured roughly 4.2--4.5 times the 27B decode
rate. The quality difference is not adequately represented by the five-case
score gap alone, so every failure was reviewed.

### 27B failure review

The four exact failures were non-critical contract edges:

- `kitchen.lights` rather than `kitchen lights`;
- “2 failures” rather than the required substring “2 failed”;
- classifying a stale supplied public feed as `local.answer/public` rather than
  `local.summary/local`; and
- correctly asking which of two lamps was intended without using the word
  “room”.

The 27B responses did not invent an action or resolve an ambiguity unsafely in
this suite.

### 9B failure review

Several misses were similarly minor: target normalization, `failures` versus
`failed`, cautious `clarify` after correctly answering, and the same stale-feed
taxonomy disagreement. Three failures are material:

1. It converted ambiguous “four o'clock” into 4 PM, selected `execute`, supplied
   14,400 seconds and said it had scheduled the timer.
2. It said media playback “is being initiated now,” despite the explicit rule
   never to claim an action had occurred.
3. On conflicting five- and ten-minute instructions it selected `clarify` but
   also said it had created a five-minute timer.

It also put the correct private-email facts in an `arguments.summary` field
while omitting them from the user-visible answer. This is recoverable by strict
schema/post-processing but is a presentation-quality regression.

## Decision

Do not replace production Qwen3.8-27B with Qwen3.5-9B under the current Aster
architecture. The 9B speed improvement is real, but its false execution claims
and unsafe ambiguity resolution violate the household-assistant boundary.

This does not rule out 9B for the intended efficient architecture. Timers,
alarms, media and Home Assistant actions should first move to deterministic
intent handlers that reject ambiguity before any language model can claim an
effect. Behind that boundary, 9B remains a strong candidate for local summaries,
brief explanations and explicit sysadmin-to-GPT routing. A next comparison
should therefore exclude deterministic execution and evaluate only frozen
personal/scheduled-analysis cases, with human semantic review. Compare 9B
reasoning-off for interactive summaries with a separately bounded thinking
configuration for overnight analysis.

No production selection or persistent model/runtime change was made. After the
9B arm, accepted production returned active and healthy with matching hashes;
the candidate was inactive, news timers were enabled and active, the kernel
failure scan was empty, authenticated post-restore generation passed with
SHA-256 `393bec08d3a6a7309b97477ebfd7eefa9373a0d279368eab90406fb8f36016f1`,
and all transient model/runtime files were removed.
