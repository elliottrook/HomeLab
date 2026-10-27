# Fixed-hardware capability research watch — 2026-10-12

## October 26 Monday review

Research execution receipt: 2026-10-27 UTC, Monday evening America/Vancouver.
Current ranking remains the staged Qwen3.6-35B-A3B ordinary-inference screen
on accepted b11429/SYCL, not an unqualified runtime upgrade. New upstream
memory and correctness changes warrant a later isolated comparison. A new
cross-family Muse Glimmer candidate enters behind the existing queue.
This review changes documentation only; no push, download or live effect.

### New runtime leads and hazards

- [SYCL reorder memory PR 31062](https://github.com/ggml-org/llama.cpp/pull/31062)
  merged October 26 at
  `5320c87ff0d994845b44ce7976f10055ec697447`. It bounds the per-operation
  temporary reorder buffer to 32 MiB. The motivating test used four B70s and
  a much larger MoE, not a single B60 or our Qwen candidate. This is a credible
  residency/OOM-risk lead, not a throughput gain: the contributor reports no
  same-layout speed effect. Aggregate peak allocations are not capped to
  32 MiB. [b11901](https://github.com/ggml-org/llama.cpp/releases/tag/b11901)
  includes the change but is labelled **pre-release** on its release page.
  Do not replace accepted recovery or trust auto-fit to budget every workspace.
- [SYCL F16 corruption issue 30892](https://github.com/ggml-org/llama.cpp/issues/30892),
  opened October 20 and still open, reports Qwen3.8-27B Q4_K_M garbage from
  short prompts on B70/Linux, with a reported first bad b11636 / `529ac89`
  after b11635. The reporter's backend-op tests passed despite bad model
  output. A second B70 configuration reproduces it. Reported fused-GEMM
  masking/F32 workarounds are diagnostic leads, not accepted production fixes.
  This is particularly relevant to a newer FP16 SYCL challenger, but does not
  establish a fault in accepted b11429, B60 G21 or Qwen3.6 MoE. Require model
  correctness gates before interpreting speed; never upgrade for memory alone.
- [Sparse-FA report 30624](https://github.com/ggml-org/llama.cpp/issues/30624)
  concerns B70/Windows with sparse FA enabled and roughly 40–60K-plus context,
  not the current one-slot 8K B60 profile. Its [ordering fix PR 30812](https://github.com/ggml-org/llama.cpp/pull/30812)
  merged October 20 at
  `8115b4c31faeab22954383202e0c26c4e55944e4`. Preserve the distinction between
  an open issue label, a merged source fix and tested artifact behavior. Keep
  sparse FA out of the first screen; the fix is not a reason to expand context.
- [Intel Vulkan FA-prefill PR 29357](https://github.com/ggml-org/llama.cpp/pull/29357)
  remains **open**, originating September 24. It includes B70 Linux prefill
  reports, including Qwen 27B/MoE. Intel Xe2 makes it relevant as a later
  hypothesis; G31 results do not validate G21, decode or useful-answer p95.
  Shader/compiler compatibility and correctness remain gates. No preview
  patch or Vulkan engine switch is proposed for the first challenger.

### Models and resource implications

Qwen3.8-27B, Qwen3.6-35B-A3B and GLM-4.7-Flash remain existing released
candidates, not new discoveries. Retain their prior pinned source/license
records below; smaller active-parameter counts do not remove resident weights.
The exact Qwen3.6 artifact is now owner-reported staged at 20,419,565,568 bytes,
SHA-256 `671e47e0ec53c665d048b98c3ecbfd5236b5ca9c3e02ed19fc8f81f7b85140c7`.
Guest mounting, loading and residency remain untested, separately gated effects.

[Muse Glimmer 30B official GGUF card](https://huggingface.co/meta-models/Muse-Glimmer-30B-GGUF)
adds a cross-family lead absent from the October 12 queue: Apache-2.0,
released August 2026; repository revision
`b44f1072cf75e918a1b82a3a17b45c4389b076e7`. The text Q4_K_M is listed as
16.8 GB, optional DFlash draft 1.63 GB and vision encoder 1.4 GB. Text artifact
[published SHA-256](https://huggingface.co/meta-models/Muse-Glimmer-30B-GGUF/blob/main/Muse-Glimmer-30B-KQuant-17GB-Q4_K_M.gguf)
is `4cc57c0f51040a226e5a72cc47b7613f7772950e460a665f7083de89f183f60e`;
exact byte count must be pinned before acquisition. The card reports about
29.6B including a roughly 1.8B vision encoder; a text-only eligibility audit
must confirm actual retained parameters. Thinking is template-enabled with
effort controls; early templates had effort-normalization issues and wrong
end-of-message stops can truncate turns. Card support starts at b10353,
but exact B60 kernels, quant quality and draft verification are unproved.
Vendor Apple/NVIDIA draft speedups are not Intel results. Budget weights,
KV, workspace and draft residency separately; no second candidate download
while Qwen remains staged. No example installer or agent tool grant is adopted.

### Engines drivers and harness review

[OpenVINO 2026.4 notes](https://docs.openvino.ai/2026/about-openvino/release-notes-openvino.html)
(September 16) remain the prior stable lead: CPU/GPU Qwen/Gemma MTP and
MoE support, DFlash preview, Gemma GPU accuracy/template caveats. No newly
verified stable backend change replaces the existing pinned trial. GenAI
support is not an exact B60 conversion or correctness result; Model Server
deployment adds no inherent capability or tool authority.

[vLLM XPU instructions](https://docs.vllm.ai/en/latest/getting_started/installation/gpu/)
still list Arc generically, Python 3.12 and XPU-specific kernels. Current
mutable guidance includes PyTorch 2.14 graph dependencies/oneAPI 2026.1.1
and a Triton XPU shim. These need one coherent isolated dependency pin, not
mixed CUDA wheels. Exact B60/model/quant validation remains open. No verified
SGLang/B60 combination was established in this search; keep it below supported
engine paths rather than assuming CUDA instructions apply.

[Compute runtime 26.35.39758.10](https://github.com/intel/compute-runtime/releases/tag/26.35.39758.10)
is the same September 17 release already recorded, not a new fix. The
[SYCL build guide](https://github.com/ggml-org/llama.cpp/blob/master/docs/backend/SYCL.md)
has a September oneAPI 2026.1 build-performance note measured on B570, not a
B60 result; check accepted build metadata before treating it as an upgrade.
No new source-pinned Linux DRM xe/BMG fix was established by this review.
Do not infer safety from a newer kernel/compiler or alter the global stack.

MTP and quantized-KV PR ancestry already in b11429 remains deduplicated below.
Agent/retrieval optimization should use the frozen retrieval snapshot and
identical typed no-effect boundary, measuring total calls and wall time.
Additional agent calls, hidden-thought retention, shared draft caches or
external search can change privacy and latency, not just answer quality.

### Authoritative owner receipt and next experiment

Fetched all three named Forgejo branches; read their current records, not just
main. Read-only GitHub protection refs matched:

- Adaptive `38b366e80987e0adeb57501034895d2e8cb70864`;
- B60 `64d909bb494473a068b61a49e1e3a493251feb48`;
- platform `6fb0207fec5190e0c34ed3bc72ea38e128f06127`.

Adaptive now explicitly acknowledges B60 commit `11febf1` and exact document
hash `106ab591f4a855f515d7c9bfbebaade4dc6ad7c9406d35e9444664f616b554ae`.
At Adaptive's full commit above, SHA-256 over Git file bytes under
`docs/projects/AI Projects/`:

- `evidence/B60-full-Aster-baseline-interface-reconciliation-2026-10-26.md`:
  `60be6a3686f07ed232c1e5d0ee4564780ea6890f7d9ced51614d3fa59fc03d69`;
- `evidence/Full-Aster-owner-freeze-result-2026-10-26.md`:
  `34274bdbf01dbc4b0c9a7274a3b201a4418b0988f607e0e4d491a988beea14b6`;
- `benchmarks/full-aster-benchmark-contract-v1.json`:
  `023939fd25e61e47af9418387ee6fe82163fac394511472a8bf64eaaab40382c`;
- `evidence/Full-Aster-challenger-artifact-staging-result-2026-10-26.md`:
  `c9804eac4a9d68b5314839ce17cf008c0032ab841a21e626a1b6ed16e87507df`.

The platform `docs/projects/Local-AI-Platform-Split.md` at its commit above is
`6bd3106078315a80046a6f917646410698df6a73f6e34c219b32272ce9f935d7`.
Its published ancestry still does not supply the newer recovery composition.
Native chat access is working as recorded October 26; older unavailability
claims are historical. This research run sends no new coordination message.

The frozen fictional packet has 24 cases across six families, two reviewers,
overall quality floor 87.5%, each family 75%, zero specified safety violations,
zero retries/timeouts, absolute p50/p95 ceilings 5/15 seconds and challenger
minus fresh baseline p50/p95 at most zero. These are **owner-reported accepted
screening constraints**, not measured latency or qualification. Forty-eight
calls provide one paired screen, not the programme's two independent sessions
and at least 100 observations per acceptance class. The absolute ceilings do
not relax the zero-delta requirement; minimum quality floors alone also do
not demonstrate improvement on harder cases. No private cases/labels were read.

Rank 1 remains exactly two sequential synthetic Qwen3.6 requests on unchanged
b11429/SYCL, genuine reasoning on, speculation off, one 8K slot, 60 seconds
per request, only after approved same-cycle F2–F5/F6 and independent recovery.
Measure actual weights/KV/workspace, no spill, health and complete output;
abort without retry on any device, OOM, truncation or custody failure. Keep
the B60 30-minute ceiling and restore before 04:15 even if the platform's
outer transaction budget is longer. This run card is still LIVE BLOCKED.
If ordinary fit fails from reorder memory, rank the exact newer-SYCL memory
fix as a separate diagnostic, with the F16 corruption gate first; do not mix
driver, quant, draft and runtime changes. Muse Glimmer is a later alternative,
not permission to acquire every release or claim the target feasible.

All changes remain local in the independent disposable liaison checkout;
the full implementation checkout is read-only in this execution environment.
Next preparation continuation should integrate these exact owner formats and
source/test dependencies, reconcile screening versus final qualification,
and receive fetchable recovery source before proposing effects.

## October 12 retained review

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
