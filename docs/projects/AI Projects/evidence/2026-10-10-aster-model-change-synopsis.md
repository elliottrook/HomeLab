# Aster model change synopsis

Date: 2026-10-10

Audience: Codex or engineer continuing Aster development

Status: Qwen3.5-9B promoted to production and validated

## Executive summary

Aster's local inference model changed from Qwen3.8-27B reasoning-off to
Qwen3.5-9B Q4_K_M reasoning-off. The change applies to permitted local
summaries, explanations, scheduled personal-information analysis and the local
side of sysadmin-to-GPT routing. It does not give the model control over
household effects, privacy decisions, authorization or deep sysadmin analysis.
Those responsibilities remain with deterministic policy or the GPT backend.

The controlled 16-case comparison found the 9B model semantically equivalent
to the former 27B model for this bounded role while reducing median request
latency from 11.051 seconds to 2.488 seconds. This is a 4.44 times speedup, a
77.5% latency reduction and an 8.563-second median saving per request.

The production rerun measured 3.070 seconds median on the same post-policy
suite. Compared with the former 11.051-second 27B baseline, that is still about
3.60 times faster, or a 72.2% latency reduction. The controlled comparison is
the primary model-selection result; the production number includes live-service
conditions and is reported separately.

## Why the architecture changed

Early testing exposed a contract problem rather than a model-quality problem.
The summarizer was initially asked to reconsider routing, refusal and privacy
after deterministic policy had already made those decisions. This caused valid
summaries to be scored as failures.

The corrected architecture gives the local model only three outputs:

- summary;
- facts;
- uncertainties.

Deterministic code retains routing, refusal, consent, authorization and
household execution. Deep or sensitive sysadmin work continues to be packaged
for the GPT backend. This separation made it possible to evaluate model size
against the work Aster will actually ask the local model to perform.

Text-to-speech is a separate service and was not changed. The model promotion
therefore does not address the previously observed TTS voice artifacts.

## Controlled evaluation

The frozen synthetic suite contained 20 cases and has SHA-256
`ca1ecae58cd588b2251ff0c5ef10d36f0fe13ff3fec05e4f194d58b67c8767bd`.
Four refusal or escalation cases were handled entirely by deterministic policy
and were not sent to the model. The remaining 16 prompts and their content
requirements were identical for every model arm.

| Model arm | Mechanical score | Human semantic review | Median latency | Relative result |
|---|---:|---:|---:|---:|
| Qwen3.5-9B, reasoning off | 12/16 | 16/16 | 2.488 s | Selected |
| Qwen3.5-9B, thinking budget 256 | 14/16 | 16/16 | 7.938 s | 3.19 times slower than 9B reasoning-off |
| Qwen3.8-27B, reasoning off | 15/16 | 16/16 | 11.051 s | 4.44 times slower than selected 9B |

All mechanical misses were manually reviewed. They were exact-word or
presentation mismatches rather than semantic failures. Examples included
describing 30-hour-old data without using the exact word `stale`, reporting
that no result was supplied without using `missing`, and correctly preserving
conflicting medication notes without selecting a dose. All three arms passed
human semantic review 16/16.

Thinking mode produced no semantic-quality improvement and raised median
latency from 2.488 to 7.938 seconds. Reasoning-off is therefore the accepted
default.

Immutable controlled-run reports:

- 9B reasoning-off:
  `51ae6c2bc4188f61eb984fcfff3308eb8ea209ce73f71fc4ee59416b027736e8`;
- 9B thinking-256:
  `a24bc36bd27a5aa376f39b0ccd6b924e6d96ad3f087d08fe280c2ba865fef7e4`;
- 27B reasoning-off:
  `4ed39ad62821e3f71449ccbe2e62bc85eb963031e5530fc5bbb5abbdbdca430c`.

The retained reports from the invalid pre-correction role contract must not be
used for model selection. Their hashes are
`8d260fa0317d6af54805ff4ce192f0be4ab49bb43cbe9ee567fac34443acc984`
and
`9e9afbd412ef87b980cacfc52af3d14eb3e4677b3975ab2de183ff6155373577`.

## Production promotion

The exact promoted configuration is:

- model: Qwen3.5-9B Q4_K_M;
- model SHA-256:
  `cd76ec205963b3b33350093e6904d9de16c4e666fd104e1f632d25c7f15f2a13`;
- runtime: llama.cpp b11429, fingerprint `d81235049`;
- server binary SHA-256:
  `5faf410bbbc00a1b94b09ee01623699f255365628dfa73b1ee552d9e52a2231d`;
- systemd unit SHA-256:
  `6b09f4580ef49b1c61532d22f48cc5091ec95a0e823f73893db7a83f5c1a461e`;
- Vulkan with all model layers offloaded to the Intel Arc Pro B60;
- 8,192-token context, one slot, batch 256 and microbatch 128;
- flash attention and Q4 key/value cache;
- reasoning disabled.

The first promotion attempt failed closed before mutation. Staging in tmpfs
temporarily reduced reported available memory below the 4 GiB safety gate while
27B was still resident. The sequence was corrected to preserve and arm
rollback, stop 27B, wait 30 seconds and then evaluate available memory.

The successful attempt removed only an inactive, uniquely referenced and
redownloadable legacy Ollama 9B blob. It installed the pinned model and runtime,
preserved all 27B rollback artifacts and increased root-disk availability from
21,066,375,168 to 21,943,648,256 bytes, a gain of 877,273,088 bytes.

## Production validation outcome

The production post-policy run passed human semantic review 16/16 with a
3.070-second median. Its immutable mode-0600 report SHA-256 is
`79b9f25da1b078b957f0ec15095276e0ffd24532ad0c2caf4a20348d3b9efb02`.

Additional validation established that:

- authenticated `/v1/models` reports `aster-qwen3.5-9b`;
- an authenticated identity request correctly reports Qwen3.5-9B through
  llama.cpp on the B60 Vulkan path in LXC 110;
- the identity request generated at 46.7 output tokens per second, although
  this short request is not a like-for-like replacement for suite latency;
- the Aster agent and inference services are active with zero restarts;
- the B60 remains bound to `xe` and enumerates as BMG G21 through Vulkan;
- News timers are active;
- the relevant kernel reset, hang, device-loss, fault and OOM scan is clean;
- 75 Aster evaluator tests and 27 B60 harness tests pass;
- the deployed Aster source, API metadata, prompt and UI all identify the new
  model consistently.

The final deployed Aster agent source SHA-256 is
`a311a020ccf4965e7d1efee43bcbaacfc7b6f95379bba87daaf082eec5ea4b66`.

## Rollback and follow-up

The exact former Qwen3.8-27B unit is retained at
`/etc/systemd/system/aster-llama.service.pre-9b-20261010` with SHA-256
`e2019cac74dc23deb4bc92efc38cf3a31a9af1b34d43d651c15e507c392fb184`.
Its runtime, model shards and earlier Q8 unit remain available. GPU or device
failures must not be retried automatically.

A finite read-only post-promotion observation is scheduled for 21:40
America/Vancouver on 2026-10-10. It checks the accepted hashes, service state,
model identity, authenticated generation, GPU binding, headroom, News timers
and kernel logs. If healthy, it records closeout and pauses itself; it does not
run further experiments or mutate production.

Repository implementation and evidence are recorded in local commit
`ce84b28` (`Promote Aster 9B production runtime`). That commit was not pushed at
the time of this synopsis.

## Final decision

Qwen3.5-9B reasoning-off is the better production fit for Aster's bounded local
analysis role. It preserved semantic quality in the tested workload while
delivering a controlled 4.44 times speedup and materially reducing live
latency. Qwen3.8-27B is retained as rollback rather than the active default.
The result depends on keeping deterministic policy and GPT-backend escalation
separate from the local summarizer; it should not be interpreted as evidence
that 9B can safely replace those components.
