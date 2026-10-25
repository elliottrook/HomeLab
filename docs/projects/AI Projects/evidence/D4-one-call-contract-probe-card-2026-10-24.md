# D4 one-call contract probe card — 2026-10-24

## Purpose

Diagnose the common `invalid_answer` phase from development attempt 2 without
spending another twelve-case run or retaining model-controlled text. The probe
uses the first reviewed synthetic case, the accepted production-compatible
local runtime and exactly one nonthinking request.

## Frozen candidate

- Probe digest:
  `04774564801ebc0f21347d44fbdec53cbca7555bb0b90b70dff7859eee779873`.
- Reviewed fixture SHA-256:
  `c3999bdd26d66290fb751519fc2439d28f45bc9fde4e13a76bc6a1afae4faf58`.
- Fixture review SHA-256:
  `59aee3a99826a75423327ab614676b31daa44f8879f4b602898ad101287ed07f`.
- Runtime: Qwen3.5-9B Q4_K_M, llama.cpp b11429, SYCL/Level Zero,
  reasoning off.
- Bound: one case, one call, 60-second request timeout, no retry.
- Test evidence: the complete evaluation suite passes 147/147.

## Retained result

The owner-only result contains the digest; a closed parse class
(`object`, `non_object` or `invalid_json`); a closed answer-shape class; a
closed semantic status; finish reason, latency, completion-token count,
reasoning-presence/count, tool-call count and postcheck health. It contains no
prompt, model answer, reasoning text, credential or fixture content.

## Fresh gates

Before the call, require the exact digest and source hashes, lease state
`ready`, LXC104/110/116 running, the exact accepted llama.cpp/SYCL unit active
with zero restarts, Aster and Speech active, authenticated health and an idle
processing gauge, and no competing backup, maintenance, News or lab work.

Stop without a call if any gate is uncertain. After the call, preserve the
0600 result, verify service health, zero restarts and ready lease state, and
remove temporary executable sources. Do not replay.

## Authority boundary

Execution needs exact approval for this digest. It authorizes one model call
and temporary hash-verified staging in LXC104. It does not authorize a second
call, twelve-case run, connected tool, effect, service/configuration change,
runtime promotion, route promotion, holdout access, deployment or Git push.
