# November 2 Monday research watch

Trigger2026-11-03T03:44:31.308Z, Monday20:44 Vancouver. Research/local records
only: no download, model/GPU call, installation, host probe, schedule change,
credential operation or Git push. Read the expanded programme before research.
The existing restore-only qualification and source-migration gates remain open.

## New source-backed additions to the queue

**SYCL graphs, later diagnostic:** [PR28725](https://github.com/ggml-org/llama.cpp/pull/28725)
merged October23, commit
[`7377bada8c22bce1b234f4b435ee69012f0300a9`](https://github.com/ggml-org/llama.cpp/commit/7377bada8c22bce1b234f4b435ee69012f0300a9).
This is merged source, not an accepted local artifact. It reduces launch
overhead using graph recording/replay. Published B70 comparisons are modest;
an initial long-context regression report was subsequently withdrawn October28.
Neither report measures this B60 or Aster useful-answer latency. The current
[SYCL guide](https://github.com/ggml-org/llama.cpp/blob/master/docs/backend/SYCL.md)
limits graph support to eligible single-device workloads; prefill/decode may
differ. Verify actual graph selection/reuse rather than assuming a build flag
enabled it. Extra graph memory/compile overhead is unmeasured here. Later use
one exact correctness-qualified newer binary, graphs off/on, fixed model and
context; keep compiler/driver/quant/speculation constant. Do not replace b11429.

**Server-path regression hazard:** [issue31262](https://github.com/ggml-org/llama.cpp/issues/31262),
opened October27 and still open, reports slower prompt processing in b11804
(`c7fc509`) versus b11046 (`60081bb`) with CPU-offloaded MoE experts, while
llama-bench suggests the opposite. Hardware is two B65s/32GB each and a122B
model on a different Xeon. This is not a demonstrated single-B60 fault and
does not implicate accepted b11429. It reinforces using the actual server /
Aster request path, not backend throughput, to admit a runtime candidate.
Retain host/GPU memory, cache policy, prompt shape and CPU offload observations.

**B60-specific but different topology:** [issue31510](https://github.com/ggml-org/llama.cpp/issues/31510),
opened November1 and open, reports severe stalls at master `0ec4027` with two
B60s, layer splitting and all experts in CPU RAM. Its102GB GLM5.3 quant and
EPYC topology exceed this project's80GB host and fixed one-GPU configuration.
Root cause remains a reporter hypothesis. Do not download that model or
reproduce the multi-card workload. Treat offload/cache behavior as a separate
measured variable; “B60” in the title is not proof our full-resident35B screen
is affected or that adding an A380 is appropriate.

## Deduplicated release/model/engine review

- [Qwen3.6-35B-A3B card](https://huggingface.co/Qwen/Qwen3.6-35B-A3B)
  still lists Apache-2.0; [GLM4.7-Flash](https://huggingface.co/zai-org/GLM-4.7-Flash)
  lists MIT. Both are existing released queue entries, not new discoveries.
  Retain frozen revisions/artifact hashes from the October26 register; mutable
  cards are not a new artifact pin. Qwen's staged20,419,565,568-byte quant is
  about19.02GiB before KV/workspace; GLM's retained18,244,193,920-byte quant
  about16.99GiB. Actual free RAM/VRAM/disk remains a live admission gate.
- [Muse Glimmer official GGUF card](https://huggingface.co/meta-models/Muse-Glimmer-30B-GGUF)
  remains the previously recorded cross-family lead. No second acquisition.
  Text-only parameter eligibility, thinking template, exact quant bytes and
  B60 support remain unproved; prior license/revision receipt is retained.
- [OpenVINO2026.4](https://docs.openvino.ai/2026/about-openvino/release-notes-openvino.html),
  September16 release, still advertises Qwen/Gemma MTP on CPU/GPU and labels
  DFlash preview. This is already in the queue. GenAI/Model Server serving
  support does not prove B60 conversion, numerical accuracy, memory fit or
  useful-answer improvement. Keep template/accuracy caveats and conversion
  temporary disk/RAM separate from compressed weight size.
- [vLLM XPU guide](https://docs.vllm.ai/en/latest/getting_started/installation/gpu/)
  still lists Arc and Python3.12-specific kernels. Mutable documentation has
  no immutable package pin here; exact Xeon ISA/model/quant/library closure
  must qualify before acquisition. No source-verified new SGLang/B60 stack.
- [Intel compute-runtime releases](https://github.com/intel/compute-runtime/releases)
  still identify26.35.39758.10, September17, as latest in the observed listing;
  exact retained target `dfa6faf3d866ea6a22b70df5a7bd2a507aa457bd` is unchanged.
  No newly pinned Linux DRM xe/Battlemage fix was established by this search.
  Search absence is not proof none exists. No global driver/kernel proposal.
- [Vulkan prefill PR29357](https://github.com/ggml-org/llama.cpp/pull/29357)
  remains open, with B70/G31 examples, not a merged B60/G21 qualification.
  [F16 corruption30892](https://github.com/ggml-org/llama.cpp/issues/30892)
  remains open; existing correctness gate precedes any newer-SYCL speed claim.
  Reorder-memory31062 remains the earlier merged lead, not a second discovery.

## Speculation, retrieval and evaluation

Current [speculation guidance](https://github.com/ggml-org/llama.cpp/blob/master/docs/speculative.md)
does not change the first screen: speculation off, genuine reasoning on.
Account for draft weights, KV, verification work and acceptance; no speculative
speed claim from synthetic acceptance or truncated thoughts. Accepted-source
ancestry of MTP/quantized-KV is already recorded; no upgrade just for those names.

A search index described Qwen-Agent PR1020 as a retrieval change, but the
[actual primary PR](https://github.com/QwenLM/Qwen-Agent/pull/1020) is an open
October30 attraction-duration scoring correction (head `f6e0e72`, base
`31a4d36d123688581a9e9744427272b33ce940e0`). It uses integer minutes to avoid
truncating valid durations. Do not adopt the index's mismatched title or claim
a released retrieval improvement. No Aster dependency on that evaluator is
established. Keep independent scoring, exact query bytes, frozen retrieval
snapshots and typed no-effect tools; agent call-count/latency/privacy remain
measured costs, not new tool permissions. TTS/GPT routing remain unchanged.

## Ranked bounded experiment and current blockers

Rank1 remains two sequential synthetic requests on the staged Qwen3.6 quant,
accepted b11429/SYCL, one8K slot, reasoning on and speculation off, only after
normal restore-only, independent owner-loss and candidate/resource recovery
qualification. Each request bounded60s; total trial≤30minutes with validated
restoration before04:15. Fail closed without device retry on OOM, drift,
malformed/truncated output or health failure. No feasibility guarantee.
After fit/correctness, freeze fresh9B control and harder held-out full-Aster
contract, then qualify capability and per-class p50/p95 across two sessions
with sufficient observations. Graph-off/on is a later diagnostic, not tonight's
replacement workload. No model result or arming is claimed by this watch.

## Exact coordination receipt

Fetched/read both liaison branches plus registry and booking-owner records.
No new peer reply or inferred reading. Current exact commit/path/hash receipts
are unchanged from `/private/tmp/b60-prelab-audit-20261103T014310Z.json`:

- Adaptive `d88f8239b6771836c3e56c59229db81a8c18ddd6`,
  `docs/projects/AI Projects/evidence/SA3-expanded-source-quality-inactive-install-preflight-2026-10-29.md`,
  `f4f72df5d792f17ce11ec87aae69e856f83865cac5b31b08146c65c32e8ac94a`.
- B60 `590341234b0e85612ec1009dfa26e24e4ffb5c92`,
  `docs/projects/B60-Inference-Engineering/nightly-reconciliation-20261102.md`,
  `0f94f994d29f1d1bfe31c0bdd933f7e6ecf370f5895104959a6299607d5fe871`.
- Registry `6fb0207fec5190e0c34ed3bc72ea38e128f06127`,
  `docs/projects/Local-AI-Platform-Split.md`,
  `6bd3106078315a80046a6f917646410698df6a73f6e34c219b32272ce9f935d7`.
- Booking owner `5a9c3471398cfeecc0c6db35bfb264f87d8318f9`,
  `services/local-ai-lease/ASTER-LAB-HOURS-RESERVATION-RUNBOOK.md`,
  `ed990e68fe04e4c238c192ff94fc81b275cf6cf622c0004e55afb26edda047ba`.

Read-only GitHub protection check matches590341234. This research commit stays
local. The current source migration/future activation next action remains in
[November2 reconciliation](nightly-reconciliation-20261102.md), not a new
approval wait, background execution claim or completed programme.
