# Fixed-hardware capability research watch — 2026-10-12

Research-only Monday review, America/Vancouver. No model/runtime download,
execution, GPU load, host/service/schedule change or Git push. Full checkout
currently read-only; this local record is in the focused writable checkout.
No numerical Aster quality/latency budget or new compatibility proof is invented.

## Important deduplication: do not upgrade for features already present

[MTP PR 22673](https://github.com/ggml-org/llama.cpp/pull/22673) merged
2026-05-16, commit `255582687b8dd211fdbc582e43ab842491554e94`.
[SYCL quantized-KV TILE PR 26689](https://github.com/ggml-org/llama.cpp/pull/26689)
merged 2026-08-28, commit `d077b4c21466cfad678b07b05b557599f4db3974`.
Public GitHub compare metadata against b11429 reports ahead, behind_by=0,
and merge-base equal to each PR merge commit:
[MTP ancestry](https://api.github.com/repos/ggml-org/llama.cpp/compare/255582687b8dd211fdbc582e43ab842491554e94...b11429),
[TILE ancestry](https://api.github.com/repos/ggml-org/llama.cpp/compare/d077b4c21466cfad678b07b05b557599f4db3974...b11429).
Both source changes are therefore already ancestors of accepted b11429.
This resolves their older PR-status ambiguity, not exact artifact/kernel
dispatch, MTP weight presence, safe residency or correctness. The published
TILE gains are external workload reports, not transferable Aster gains.

GitHub latest llama.cpp release metadata gives v0.6.0, published 2026-10-05,
target `8345f333951c661d166b00e6f9362e553768f292`. Do not infer that the latest
semver-labelled release is newer or faster than the accepted b11429 build
solely from its label. A broad rebuild is not the next experiment.

## Source register and implications

1. [Qwen3.6-35B-A3B official card](https://huggingface.co/Qwen/Qwen3.6-35B-A3B),
   Apache-2.0; previously frozen source revision
   `995ad96eacd98c81ed38be0c5b274b04031597b0`. Released model, not a new discovery.
   Thinking defaults on in the documented template; historical-thinking
   preservation is a separate setting. Runtime and conversion must implement
   the exact mode. The pinned maintainer Q4_K_M is 20,419,565,568 bytes: roughly
   19.02 GiB, not 3B-sized residency. KV/workspace and optional MTP heads still
   need measured fit. Existing guest RAM/root constraints are unchanged.
2. [GLM-4.7-Flash official card](https://huggingface.co/zai-org/GLM-4.7-Flash),
   MIT; retained source pin `7dd20894a642a0aa287e9827cb1a1f7f91386b67`.
   Released cross-family 30B-A3B challenger already queued. Maintainer Q4_K
   artifact is 18,244,193,920 bytes, about 16.99 GiB. Vendor reasoning/agent
   scores do not measure Aster or B60 latency. Keep distinct prompts, tokenizers,
   reasoning semantics and tool-policy controls visible in comparisons.
3. [OpenVINO 2026.4 release notes](https://docs.openvino.ai/2026/about-openvino/release-notes-openvino.html),
   released 2026-09-16, not merely nightly. GenAI lists Qwen3.5/3.6 MTP on CPU
   and GPU; DFlash is flagged preview. These are worthwhile later backend
   leads, not proof of the exact B60/INT4 model/runtime stack. Existing private
   trial already pins 2026.4, so this is not an upgrade discovery. Conversion,
   tokenizer, cache, graph/residency and compiler-memory effects must be reported.
4. [Intel compute-runtime 26.35.39758.10](https://github.com/intel/compute-runtime/releases/tag/26.35.39758.10),
   latest release API result, published 2026-09-17, prerelease=false,
   target `dfa6faf3d866ea6a22b70df5a7bd2a507aa457bd`. Repository already records
   this exact private runtime. [Supported platforms](https://github.com/intel/compute-runtime)
   lists Battlemage, but not validation of this Proxmox kernel/guest/loader
   combination. No newer verified runtime fix found here warrants installation.
5. [vLLM Intel XPU installation](https://docs.vllm.ai/en/latest/getting_started/installation/gpu/)
   lists Intel Arc support and Python 3.12-specific custom-kernel wheels.
   This is a generic support path, not a demonstrated B60/Qwen35B/quant result.
   It adds an isolated dependency/runtime footprint and is lower priority than
   ordinary inference in the installed stack. No new wheel was downloaded.
6. [llama.cpp speculation documentation](https://github.com/ggml-org/llama.cpp/blob/master/docs/speculative.md)
   lists MTP, model-based and draftless approaches. Current master is mutable,
   not a claim every option exists in the accepted binary. External drafts
   consume additional RAM/VRAM and verification time. Draftless ngram-mod is
   documented around 16 MB but shares its hash pool across slots: evaluate
   request/custody isolation, not just speed. Repetition-heavy results need
   separate short-assistant controls. Synthetic-acceptance options bypass
   real target verification and produce invalid model output; never use them
   for answer quality, useful-answer latency or a production recommendation.
7. [Qwen-Agent guidance in the Qwen card](https://huggingface.co/Qwen/Qwen3.6-35B-A3B#agentic-usage)
   is a framework recommendation, not an Aster permissions contract. Preserved
   thinking/context packing may affect calls/tokens; record them as new
   profiles and retain local custody. Do not adopt example filesystem/MCP
   grants, cloud endpoints or hidden-thought logging. TTS remains unchanged.

No newly verified B60-specific Linux xe/oneAPI fix was established by this
review. Absence of a credible finding is not proof none exists. The accepted
BAR/kernel remain fixed controls; no BIOS, reset, boot or global-driver proposal.

## Correctness hazards: distinguish report, fix and hardware applicability

- [SYCL MTP issue 23149](https://github.com/ggml-org/llama.cpp/issues/23149)
  opened 2026-05-16 on device e211 with old b9181: truncated thinking, OOM or
  garbled later answers. It closed completed 2026-05-22; the reporter says a PR
  resolved it. Do NOT describe that historical failure as an unpatched current
  bug. It motivates first/second-request and memory/correctness gates, not a
  declaration that MTP cannot work on B60.
- [Second-prompt TILE crash 21396](https://github.com/ggml-org/llama.cpp/issues/21396)
  remains the already-recorded old B50/B60 report, closed stale/not planned.
  Closure is not proof of a fix or of current reproduction. Exact isolated
  multi-request tests are required before trusting a new architecture/profile.
- [MTP hard-lock report 28252](https://github.com/ggml-org/llama.cpp/issues/28252)
  is open and concerns CUDA multi-GPU/tensor-split with very long contexts.
  It is NOT a demonstrated single-B60/SYCL fault. Do not reproduce its unsafe
  setup; retain bounded single-device/8K testing and independent recovery.

## Ranked next bounded experiment — after actual lease and staging admission

First screen the already-pinned Qwen3.6-35B-A3B Q4_K_M on accepted FP16 SYCL,
reasoning genuinely enabled and speculation disabled. Prefer a single-model
ordinary-inference screen over mixing an engine/driver upgrade and MTP at once.
This is a proposed experiment, not a READY run card or a latency prediction.

- Verify manifest/license/template, artifact integrity and reviewed read-only
  host-backed guest path. Required model bytes plus workspace/cache/residency
  remain measured gates; no guest-root copy/tmpfs assumption or silent disk growth.
- Reserve one slot, 8K maximum context and a bounded EOS-respecting output/time
  profile agreed with Adaptive. A truncated reasoning/final answer is failure,
  not a fast thinking-on pass. No hidden reasoning text in shared telemetry.
- Begin with two sequential synthetic correctness requests and resource/health
  inspection; stop on device, OOM, restart, malformed/truncated answer or drift,
  without retry. Only then use the Mini-custodied paired development corpus,
  pre/post accepted controls and exact independent restoration.
- Keep a 30-minute experiment ceiling with recovery margin and restoration by
  04:15. Full useful-answer median/p95 qualification waits for the actual
  Aster-path/case/review/sample contract; direct backend throughput cannot fill it.
- If ordinary fit/correctness passes, a separate later MTP-on diagnostic may
  verify included NextN tensors, draft overhead/acceptance and exact backend
  support. Never enable synthetic acceptance. GLM is next if Qwen is eliminated;
  OpenVINO remains a later controlled backend comparator, not default promotion.

## Coordination and persistence

Fetched Adaptive `dc7531ca` (News close-out changes), B60 `779af42f` and platform
`fc60e5a2`. No inference of acknowledgment/adoption from a branch tip. The
shared runner/lease and current tunnel endpoint/access remain unresolved by
this research; no remote execution or claimed background experiment.
Exact receipts, SHA-256 over Git file bytes:

- Adaptive `dc7531ca093a80c3f62be561c0ef53361d7abf00`,
  `docs/projects/AI Projects/benchmarks/B60-coordination-interface-2026-10-12.md`,
  `783e7598c914b2480149d9bc1616d0fd754b119eaddd7bed063ed793fb40469a`.
- B60 `779af42fe067d9332a82036b91cccb3530d59ca6`,
  `docs/projects/B60-Inference-Engineering/full-path-and-lease-recovery-handoff-20261012.md`,
  `8c676d428dd1e3f5f88870cb201b2cfaa0d87fee01177e9a5a3a0ab072d3ded7`.
- Platform `fc60e5a2c9eac8f311ce8e6c0a83b901fe55600b`,
  `docs/projects/Local-AI-Platform-Split.md`,
  `358f1176d792c0e88b32ad65903a2384fa8de44904e3f839f27a2978b9f4c7be`.

This record is a local-only commit for later writable-checkout integration.
The watch explicitly prohibits Git push even though separate liaison runs have
standing branch-only authority. No automatic pause: 27B+ reasoning-on target
and iterative capability programme remain open.
