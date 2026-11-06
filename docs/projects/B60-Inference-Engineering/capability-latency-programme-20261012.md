> Recovery receipt, November6: this programme file was present in the existing full checkout but absent from authoritative main and the focused B60 coordination branch. Its complete historical source bytes had SHA256 `27f416c32d2cc1b895effc438c80a55e6616282c9597434a0fe8f747e078acaf`. Restored here as a durable dependency, without claiming that missing upstream provenance was verified. Jason’s explicit expanded objective and approval remain the governing task authority.
>
> Current operational state supersedes the historical “runner/shared lease remain undeployed” paragraph below: normal restore-only, independent owner-loss and bounded resource/private-mount gates actually passed November5. A separate post-Xe accepted-SYCL correctness qualification is armed for November6 16:20; no post-Xe inference pass,27B+ capability/latency acceptance or promotion is inferred. See the [current project](../B60-Inference-Engineering.md) and [actual qualification plan](post-xe-qualification-plan-20261106.md). Historical model/runtime research remains dated leads, not fresh support claims.

# Fixed-hardware Aster capability/latency programme

Date: 2026-10-12, America/Vancouver. Status: owner-requested expanded scope;
evaluation contract being defined, no new GPU result or deployment claimed.

## Objective and first deliverable

Deploy the most capable measured local Aster stack within the agreed latency
on the existing Dell T5810 / Xeon E5-2698 v4 / 80 GB ECC / Arc Pro B60 24 GB.
No new inference hardware, remote accelerator or cloud-model substitution may
be used to claim this local milestone. The Mac mini remains execution/control,
not additional inference capacity.

First deliverable: a 27B+ model with reasoning enabled, integrated with Aster,
matching current Qwen3.5-9B reasoning-off response latency and improving useful
capability. Jason confirmed on 2026-10-12 that 27B+ total-parameter MoE models
qualify and that both median and p95 time to a complete usable answer, including
reasoning, must match the fresh 9B baseline. No slower allowance is approved.
Report uncertainty and dense/MoE distinctions. Neither a smaller model nor a
reasoning-off large model silently satisfies the first deliverable.

## Evidence, not a feasibility promise

Current accepted production is 9B, not 8B: FP16 SYCL b11429, Q4_K_M model,
8K context and one slot. The historical post-policy suite gave 2.488 s for 9B
reasoning-off, 7.938 s for 9B thinking-256 and 11.051 s for old 27B reasoning-off;
all passed semantic review 16/16. Those model comparisons predate accepted SYCL
and are not the new latency thresholds. Current fixed 128-token SYCL controls
record about 57.8 tokens/s and 2.476 s request latency, on that fixture only.
See the project and `AI Projects/evidence/2026-10-10-aster-model-change-synopsis.md`.

The 16-case semantic ceiling cannot establish which stack is smartest. Expand
the evaluation rather than claiming that more parameters or thinking guarantees
better answers. Earlier architecture tests showed unsupported observations in
thinking mode; grounded correctness and authority isolation remain mandatory.

Illustrative capacity calculation, **not a throughput prediction or hard bound
for all algorithms**: 27 billion weights at exactly 4 bits require 13.5 GB before
quantization metadata, buffers and cache. If a conventional dense decode step
streams all these weights, Intel's advertised 456 GB/s divided by 13.5 GB is
about 33.8 steps/s before overhead. Speculation, weight reuse and architecture
changes can change that model. At 2.476 s, generating 256 reasoning plus 128
answer tokens would require about 155 generated tokens/s even ignoring prefill.
Do not promise dense 27B long-thinking at current short-answer latency on that
basis. Short useful reasoning, MoE, MTP/speculation and avoiding extra agent calls
are testable ways to change the work required, not proof of success.

## Freeze the acceptance contract before tuning

- Refresh accepted 9B baseline in the valid shared lab window. Measure complete
  Aster-path latency, separately per task class: median and p95 usable-answer
  completion; first usable content; prefill; decode; queue/retrieval/tool time;
  reasoning and final-answer token counts where available. Acknowledgments and
  hidden thought tokens are not usable answers. STT/TTS are unchanged controls;
  report their contribution for voice workflows separately.
- Owner-accepted strict target: candidate median and p95 no
  worse than the fresh 9B baseline per interactive task class. Use identical
  task semantics, completeness requirements, load, context and cache policy.
  Account for uncertainty; five repeats are screening, not adequate p95 proof.
  Collect at least 100 observations per acceptance class across two sessions,
  reporting spread and uncertainty without pretending independence when correlated.
- Keep fixed-token runtime fixtures separate: equal generated-token counts help
  diagnose engines; end-to-end model tasks may have different tokenizers and
  reasoning lengths, which must be disclosed rather than forced into fake matches.
- Reasoning enabled means the runtime applies the model's documented thinking
  template/mode. Verify mode metadata and representative synthetic behavior;
  record counts/timings, not private chains of thought. Test bounded effort and
  budgets including a reasoning-off diagnostic, but do not count off/zero-budget
  or prematurely truncated malformed answers as thinking-on success.
- Retain all existing safety/regression cases. Add hard held-out multi-step
  grounded analysis, calendar conflicts/time zones, source contradictions,
  uncertainty/abstention, tool-schema selection, multi-turn state and 8K recall.
  Test timer/media/Home Assistant paths with recording adapters, not household
  effects. Deep sysadmin still routes to GPT under existing policy; local task
  quality cannot be credited to a cloud answer.
- Use frozen rubrics, development versus held-out splits, blind semantic review
  where possible and repeatable automated checks. Report quality and latency
  by class; no aggregate hiding a safety failure. Require zero observed unsafe
  effects/privacy violations and no regression on must-pass correctness cases.
  Require improvement on harder capability cases with paired uncertainty; no
  claim of universal correctness or statistically proven superiority from 16 cases.

## Ranked experiment sequence and source-backed candidates

1. Reuse retained Qwen3.8-27B for a dense thinking-on diagnostic after fresh
   checkpoint/resource gates. Its current official card documents thinking,
   effort control and MTP. Verify that the actual pinned local runtime supports
   each feature; a model card's recommended engine is not B60 compatibility proof.
2. Screen Qwen3.6-35B-A3B (and compare 3.5 only if compatibility or evidence
   warrants it). The 3.5 official card lists 35B total / 3B activated and MTP.
   MoE reduces active computation but still needs weights/state resident or
   explicitly accounted offloading; it is not a 3 GB model or guaranteed speedup.
3. Cross-family eligible challenger: GLM-4.7-Flash, officially 30B-A3B with
   thinking guidance. Treat vendor benchmark claims as selection leads, not
   Aster evaluation results. Verify pinned quantization, tools and GPU kernels.
4. Dense cross-family candidate: Gemma 4 31B. Its 26B-A4B alternative does not
   meet a strict 27B floor (official total 25.2B). Current OpenVINO notes flag
   Gemma long-prompt/agentic GPU accuracy and conversion/template issues: gate
   exact versions, do not promote from a speed result alone. Smaller models
   (e.g. Magistral 24B) may be diagnostic comparators, never qualifying milestones.
5. Compare existing llama.cpp SYCL with compatible pinned newer SYCL builds,
   native OpenVINO/GenAI or Model Server, and vLLM XPU if exact B60/model/quant
   support and storage fit are demonstrated. vLLM lists Intel Arc support but
   that is not proof of this whole combination. SGLang/other servers enter only
   after primary-source Intel compatibility screening, not CUDA assumptions.
6. Tune measured bottlenecks: thinking effort, quantization/KV precision,
   supported MTP or speculative draft decoding, graph/kernel choices, context
   packing, retrieval relevance and call count. Test agent/harness alternatives
   behind Aster's typed tool contract with bounded steps; preserve deterministic
   timer/media/HA execution, authorization, privacy and GPT-routing boundaries.
   A new wrapper that calls the same model more often is not inherently smarter.

Use staged elimination, not a Cartesian product. First prove load/resource fit,
then safety/correctness, then capability/latency; invest in finalists only.
One variable per diagnostic; label joint stack changes and attribute gains only
when supported by controls. The 9B OpenVINO run may establish an engine gate,
but may be bypassed if a direct eligible-model test is more informative.

## Authorization, resources and recovery

Jason explicitly requested broader model/family/agent/runtime/driver trials,
resource allocation and downloads as needed. This extends prior download-only
restrictions for relevant **isolated lab artifacts**, not arbitrary remote
execution, credential/export/public exposure or destructive storage. Pin source
revision, license and artifact hashes; prefer official weights or a traceable
conversion. Do not blindly execute remote model code. Inventory available disk,
RAM and VRAM before acquisition; derive each download cap from exact artifact
bytes plus extraction/conversion/cache needs and required free headroom. One
candidate resident/staged at a time; never delete accepted/last recovery copies
or expand a disk silently. Record GPU/CPU offload and draft-model overhead.

Private user-space runtime/driver libraries and local builds are staged trials.
Global kernel/driver/package/boot changes need a specific risk/checkpoint plan
and the tested owning host-maintenance procedure; do not infer those privileges
from a generic agent loop. Hardware stays unchanged. Production promotion uses
an exact finalist manifest and rollback plan presented for acceptance, not an
open-ended instruction to install whatever a benchmark ranks highest.

Use the shared backup-completion-gated host lease; restoration before 04:15.
No overlapping backup/mirror, 04:15–06:15 analysis or another lab owner. Keep
independent watchdogs, exact accepted SYCL recovery, protected credentials,
fresh gates, no automatic retry after device failures and sanitized immutable
evidence. The runner/shared lease remain undeployed; do not claim the clock
change itself solved unattended execution.

## Research cadence and programme stop rules

Expand the existing Monday 20:30 America/Vancouver watch, not a duplicate, to
official model releases/cards, Intel/xe/compute runtimes, OpenVINO, llama.cpp,
XPU serving engines, speculation/MTP, retrieval and agent/harness developments.
Record version/date/source, released versus preview/PR status, exact hardware
applicability, known hazards and a ranked next test. Quiet on duplicates/no change.
Do not download or execute every release. Review the queue before each lab run.
Success of a 9B OpenVINO comparison no longer pauses the overall programme.
Completion requires the expanded acceptance criteria; infeasibility requires
an explicit measured report and owner decision, not an invented guarantee.

## Primary sources consulted 2026-10-12

- [Intel B60 datasheet](https://www.intel.com/content/dam/www/central-libraries/us/en/documents/2026-03/datasheet-b60-gpu.pdf): 24 GB, 456 GB/s advertised maximum.
- [Qwen3.8-27B official card](https://huggingface.co/Qwen/Qwen3.8-27B): architecture, MTP, thinking/effort and serving guidance.
- [Qwen3.5-35B-A3B official card](https://huggingface.co/Qwen/Qwen3.5-35B-A3B): total/active parameters and thinking/MTP.
- [Qwen3.6-35B-A3B official card](https://huggingface.co/Qwen/Qwen3.6-35B-A3B): current next-generation candidate; not tested here.
- [GLM-4.7-Flash official card](https://huggingface.co/zai-org/GLM-4.7-Flash): 30B-A3B and thinking guidance.
- [Gemma 4 official card](https://ai.google.dev/gemma/docs/core/model_card_4): dense/MoE sizes and total/active distinction.
- [OpenVINO release notes](https://docs.openvino.ai/nightly/about-openvino/release-notes-openvino.html): version-dependent hybrid/MoE support, speculation and known accuracy issues. Nightly content is not proof an installed stable build has a feature.
- [llama.cpp SYCL](https://github.com/ggml-org/llama.cpp/blob/master/docs/backend/SYCL.md) and [speculative decoding](https://github.com/ggml-org/llama.cpp/blob/master/docs/speculative.md): supported paths; exact candidate build still requires validation.
- [SYCL quantized-KV dispatch PR 26689](https://github.com/ggml-org/llama.cpp/pull/26689): specific kernel tuning lead, not evidence of a local improvement or automatic production approval.
- [vLLM GPU installation](https://docs.vllm.ai/en/latest/getting_started/installation/gpu/): Intel XPU/Arc path and dependencies, not a B60 benchmark.
