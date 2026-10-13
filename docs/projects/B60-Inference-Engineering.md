# B60 inference engineering

> Status: Active — full BAR persistently deployed; repeat boot and production recovery validated
>
> Owner: Jason
>
> Proposed: 2026-09-25
>
> Started: 2026-09-25
>
> Completed: 2026-10-10

> Reopened: 2026-10-10 for the separately gated M3 BAR work

## Purpose and desired outcome

Establish the fastest safe, stable and repeatable local-LLM configuration that
the fixed Dell Precision T5810, Xeon E5-2698 v4, 80 GB ECC RAM and ASRock Intel
Arc Pro B60 24 GB can sustain for Aster. Separate platform/BAR, driver/runtime,
model-interface and application-workload effects with reproducible evidence.
Promote a candidate only when it materially improves real Aster latency without
correctness, tool-use, recovery or stability regression.

The initial promotion threshold is at least 15% median decode improvement or a
clearly valuable real-workflow latency improvement, reproduced in two sessions
with a post-series control rerun. Phase 1 may refine this threshold before it is
used as a gate.

## Current state and evidence

### Owner-approved SYCL promotion and subsequent OpenVINO evaluation — 2026-10-11

Jason approved permanent SYCL deployment after the remaining tests pass:
verify a fresh LXC 110 backup and mirror, grow only its root disk from 64 to
72 GiB (not shrinkable in place), persist the pinned b11429 FP16 runtime,
private loader 1.33.1 and oneAPI dependencies under `/opt/aster-sycl-b11429`,
atomically update `aster-llama.service` with bounded readiness while preserving
model, API, inference settings and exact Vulkan rollback, then validate
regression and soak. No global driver, system package, firmware, reboot,
GPU reset, credential or Git push change is included. Other B60 consumers stay
paused. Jason subsequently confirmed the order: deploy this configuration
first, then test native OpenVINO as a llama.cpp replacement, not merely its
OpenVINO backend. Keep that later trial isolated, private and reversible;
record exact prerequisites and checkpoint before executing it. No permanent
OpenVINO promotion is implied.

Two independent FP16/fusion-1 workflow sessions completed with correct 2,060
token grounded retrieval and 8,012-token marker recall, five measured repeats
per fixture and Vulkan pre/post controls. Session 1's reported server decode
improvements are 21.3378% and 20.9313%; its create-once report SHA-256 is
`3dfdf49e2fc89597cedff704cf52f1021a53aa590aaeb425caefdc19f3f9f0dd`.
Outputs are short (18 grounded tokens; 70 candidate versus 85 control tokens
for 8K), so do not present this as sustained 128-token throughput. Session 2
completed at 00:12:55 PDT with all correctness and recovery gates passing;
its exact pre-request mapped-runtime proof SHA-256 is
`0dc1ca1dbc410e28c4d0e2c2a881bce786bd27050ce0af94e7275c06ea281bff`.
Accepted Vulkan is healthy, candidate stopped and both watchdogs disarmed.
Final fixed-length decode confirmation uses new identity
`20261011-fp16-decode-1`, unchanged FP16/fusion-1 runtime, calibrated cold/warm
fixtures, at least 120 output tokens, five repetitions, fresh preflight and
the independent rolling restoration watchdog. No persistent mutation has
occurred at this record point. The previously completed M6 checkboxes refer
to the earlier Q4/Vulkan promotion, not this new SYCL deployment.

Session 2 report SHA-256:
`200143b8ad3ad5b761e4d9914e8149fda123e551dfc09ba6d4feb054153e6a56`.
Grounded decode improvement 21.4546%, request latency reduction 17.0590%;
8K decode improvement 21.2937%, latency reduction 37.3191% (63 candidate
versus 85 control tokens, so the latter is not a pure speed gain).

Final fixed-length comparison passed: every measured output is exactly 128
tokens, candidate warm/cold server decode medians 57.8879/57.8249 tok/s,
approximately 48.6 tok/s Vulkan controls. Decode gains are 19.1536% warm and
18.9557% cold, with request latency reductions 15.5278% and 13.4914%.
Immutable complete report on LXC 114:
`matched-sycl-exclusive-20261011-fp16-decode-1-workflow-report.json`, SHA-256
`9d6b1a9854dc76959d1c064e7d61293fd6410877adb6d39c9da74e9dff7eecb1`.
All pre/post controls, recovery/authentication and fault gates passed; watchdog
disarmed. Thus promotion has two independent correct real-workflow sessions
plus sustained-output confirmation, not merely a three-token health probe.

Deployment lifecycle decision: replace the existing warmup helper only for
the SYCL unit with a 300-second health-readiness loop, systemd startup limit
330 seconds, and `Restart=no` to prevent repeated GPU execution after an
initialization/device failure. Preserve all existing inference, API, identity
and hardening settings. Automatic service retry is deliberately traded for
fail-closed operation and an exact independently invocable Vulkan rollback.
The existing scheduled TrueNAS mirror is deletion-enabled, so this checkpoint
uses a single create-once SSH-stream copy with SHA-256 verification and no
existing archive deletion or scheduler mutation. The archive is never saved
on the workstation or displayed in the conversation. Checkpoint, 64-to-72 GiB
growth, persistent runtime and atomic unit validation must precede activation.

Jason explicitly approved the later native OpenVINO trial's prerequisite:
revision-pinned `OpenVINO/Qwen3.5-9B-int4-ov` download (up to 6.28 GB), matching
runtime/OpenCL libraries in isolated trial storage, hashes, synthetic tests
and exact SYCL recovery. No system packages/global driver or permanent
OpenVINO deployment. The native GenAI GGUF reader's Qwen3.5 hybrid architecture
limitation is distinct from llama.cpp's OpenVINO backend; use vendor IR rather
than pretending the existing GGUF is directly supported. Sources:
[native GGUF limitation](https://github.com/openvinotoolkit/openvino.genai/issues/4137),
[vendor IR model](https://huggingface.co/OpenVINO/Qwen3.5-9B-int4-ov).
This trial changes quantization/model artifact as well as runtime and must be
reported as a quality-gated deployment comparison, not a backend-only causal
benchmark. No OpenVINO GPU execution precedes accepted SYCL deployment and
regression validation. Model storage, bounded context/cache, reasoning-off,
private endpoint/authentication compatibility and mapped B60 execution need
explicit verification; do not accept CPU fallback or automatic failure retry.

Fresh pre-promotion checkpoint completed at 00:32:36 PDT without pruning:
`/mnt/backups/dump/vzdump-lxc-110-2026_10_11-00_28_16.tar.zst`,
38,516,046,359 bytes, SHA-256
`62ace1cd8ab7412031b99a7b9f378f98d5aec5f31ee0831742b00b8e1804e205`.
Single-pass verification at 00:38:52 proved compressed frame integrity and the
exact accepted unit, binary and model bytes inside the archive, without
displaying or extracting secret contents. Host immutable proof:
`/var/lib/b60-inference/evidence/sycl-prepromotion-checkpoint-20261011.json`.
The initial verifier was intentionally stopped before any proof or mutation,
replacing its redundant triple read with one equally strict sequential scan.
The backup executable was resolved from `/usr/sbin` to installed `/usr/bin`
before the backup started; no failed/partial backup was represented as success.
TrueNAS create-once copy completed at 01:15:31 PDT, matching every byte and
the same archive SHA-256. Fresh verification at 01:16 preceded the passing full
preflight and approved root-disk growth to 72 GiB. Actual root free space after
growth: 30,016,192,512 bytes; after verified persistent runtime copy:
27,197,358,080 bytes. Thin-pool data/metadata usage 23.71%/1.09%; pre-existing
thin overprovisioning warnings did not indicate actual pool exhaustion.
The later direct-copy approval arrived when the existing relay was already
86% complete; it was faster to finish that relay. No temporary TrueNAS task
was created, and no existing schedule, credential or archive was altered.

First persistent activation passed at 01:21:04 PDT: exact unit SHA-256
`a4c75169673a1a230682b73d362a05c1bdd30f7a5c41cfb9c77463204dfd4cb3`,
33/33 B60 layers, all selected runtime mappings under `/opt/aster-sycl-b11429`,
authenticated correctness, healthy services, zero restarts and no kernel fault.
Activation proof SHA-256
`97055185bfc04e002e1325d4031ce15ac2156f59c73577ec83edc4a177a8d2b8`.
Post-deployment regression completed at 01:22:39: 12/16, same four known
baseline scoring failures, no new failure. Short-suite evidence SHA-256
`77fd4aaf38431588a035578a47f051be3212d457e822a2b1ca1bff521b6add7c`;
production validation proof
`50833c514d03aa85fb2e7ba1da6f584d28b9fd6f41fa04bcf02de4a5b56754cb`.
Exact Vulkan rollback was then exercised successfully at 01:23:49, including
accepted hashes and protected synthetic correctness. Second clean SYCL start
passed at 01:27:05; immutable activation SHA-256
`3bdc3dcc49c2e4a240a04dc990912a421c6c2f8e5a2f8c226ac307751f4a873f`.
The ten-minute soak began at 01:27:50 with exact hashes, health, kernel,
resource, xe/Vulkan and reservation checks. During it, five correct exactly
128-token cold outputs measured 57.7846 tok/s and 2.47559-second median request
latency (evidence SHA-256
`923b603124b610680f92c004e433bc96dfde9c821786e5575492fd879e3a852b`).
The persistent 8K workflow passed all repetitions at 8,012 prompt tokens,
85 output tokens, 49.4821 tok/s, median request 1.83973 seconds (SHA-256
`6550cd919d245178592f81a8f073ab190575396aa0a0aab6a4bdb6f71c28e39a`).
This output length differs from earlier volatile SYCL sessions, so retain the
earlier length-related latency caveats; the decode rate is consistent.
Persistent grounded retrieval also passed every repetition at 2,060 input and
18 output tokens, 54.9140 tok/s; evidence SHA-256
`4e4e79099ed251bdacc8bed9f509900281eee0ef968d4b4496e18f0175564f3b`.
The ten-minute exercised soak passed at 01:38:13, SHA-256
`d121856bcf8f739cf1178f6fea3c6809c4f101e41fb000369f50cc7a62dd2702`.
Final authenticated correctness passed at 01:38:27. SYCL accepted at 01:39:08;
host create-once acceptance record SHA-256
`058bee09f7fdfb8023445fc9880563bf8c8901e466ae49504011b2c64f9aceec`.
Promotion rollback timer disarmed after those proofs. Default guard now pins
accepted SYCL; native staging/execution also require this acceptance marker.
No permanent OpenVINO deployment or Git push. The repository now retains an
exact-hash SYCL unit template; legacy Vulkan recovery uses an explicit profile
so later default acceptance cannot silently change its restoration target.

Native preparation completed at 00:48:38 PDT: 27 publisher-verified artifacts,
6,347,862,877 bytes, model revision
`ee5a3761d4524966dd6c1f1037694ebc581cb196`. Host isolated publisher manifest
SHA-256 `360266b625445ca62ef752ce549295648a56e4184df44c543c4c2f896b38cb24`.
Pinned CPython 3.13 GenAI/tokenizers 2026.4.0.0 and runtime 2026.4.0;
matching Intel OpenCL 26.35.39758.10, Debian private ICD loader 2.3.3-1,
NumPy 2.4.4 and telemetry 2025.2.0 downloads completed at 00:56:01, hashes
verified. Guest staging passed at 01:41:30: 31 verified artifacts, 22,379,098,112
bytes disk free, 11,775,365 KiB available RAM; staging proof SHA-256
`db9d6379f6d7929cb81e842b7046ed38a58bdb753e6f041678aa2a66730dfc05`.
No package installation. Fresh guarded preflight at 01:47:50 passed accepted
SYCL hashes, verified checkpoint/mirror, health, xe/Vulkan, resources and kernel
gates. The bounded native comparison began at 01:48:05 with an independent
30-minute exact-SYCL recovery watchdog and preservation of the 02:30 backup
boundary. Temporary telemetry now follows the explicitly selected accepted or
candidate unit, rejects PID zero and missing temperatures, and requires positive
native GPU residency before generation. The added fail-closed collector tests
pass. Native GPU startup passed at 01:50:19 in 20.413 seconds, explicit B60
selection and private OpenCL/GPU-plugin mappings, proof SHA-256
`c4d783c99f8a9250f0ff6e07bb0339495cb1e0fbfef5a7a6a21cfa2f7811a47f`.
Authenticated correctness passed, then regression scored 14/16 with no new
failures (remaining stale-news/private-public-join), SHA-256
`2959f7b7118323668d0d7381cd580e28c738d29fc0e758b00c806c893d6d1520`.
The sustained-output warmup stopped naturally at 101 tokens, below the unchanged
120-token minimum. Its sanitized report SHA-256
`148304452d73e3fb4486d7e0f0d3f114d91635135e85a90cb8dbc75699aa3655`
contains only that failing warmup; do not treat its 51.300 reported tok/s as a
measured speed result. Native execution stopped immediately without retry.
Exact SYCL hashes, private mappings, 33/33 GPU layers, health and authenticated
generation were restored at 01:52:35; recovery proof SHA-256
`5c591238a687776eb8bd7a562307098adc86fadd82739bbad829f2380f6eb656`.
Independent read-only final validation passed at 01:54:07, SHA-256
`a950231241b4b22b2dce9723497a2912ea7bec1c94269cba40c03edd74b482db`.
No device/kernel failure or permanent OpenVINO deployment. Comparison remains
incomplete: grounded/8K native runs and post-controls were not executed after
the failed gate, and no native speed improvement is established.

Next bounded comparison uses explicit ignore-EOS only for the synthetic
128-token throughput fixture, identically on SYCL pre/post and OpenVINO. The
installed GenAI binding documents `GenerationConfig.ignore_eos`; default
personal/regression generation remains EOS-respecting. Runner records the
generation policy, native adapter rejects unbounded/non-throughput use, and
report requires exact 128-token outputs and identical fixed-length policy.
This correction is locally tested, not yet executed. No second trial can start
after 01:55 under the existing 35-minute reserve before the 02:30 backup. Fresh
preflight and no active backup I/O remain prerequisites for the next run.
Trial staging reserves the 20-GiB disk floor, including filesystem overhead,
by keeping the vendor text-embedding/vision-merger blobs and private runtime
in RAM; guest staging is gated on accepted
SYCL deployment. Native adapter is synthetic-only: greedy/reasoning-off,
8K total tokens, at most 256 output tokens, one sequence, no MTP or prefix
cache. It does not claim streaming/tool/media API parity. Native TTFT is not
misreported as prefill time, and cache reuse is not invented. Telemetry checker
is redirected process-locally to private declined consent, not home/global
configuration. Sources: [GenAI API/installation](https://openvinotoolkit.github.io/openvino.genai/docs/getting-started/installation/),
[telemetry implementation](https://github.com/openvinotoolkit/telemetry).

### Latest owner priority override — 2026-10-10 22:49 PDT

Jason reserved the B60 for these tests until he explicitly resumes other work.
This supersedes earlier automatic News restoration instructions. LXC 114's
ingest/digest timers are stopped and disabled (previously enabled); their
workers are inactive. The News UI remains unchanged. The 23:45
`restore-news-timers-after-b60` heartbeat is paused with an explicit no-resume
instruction. Re-enable/start these two timers only when Jason resumes other
work, without replaying missed briefings. Preserve backups, health monitoring,
and unrelated A380/TrueNAS GPU work. This priority reservation does not extend
experiment deadlines or authorize automatic retries after compute failures.

At 23:00 PDT Jason clarified: these tests take priority over all other B60
activity and are approved under Stream A until the objective is reached.
This supersedes per-test conversational approvals for bounded isolated backend
tests, including the instrumented loader/fusion-off run and its fresh preflight
after the old 22:55 conservative stop. For tonight, retain the previously
presented 23:20 experiment stop and 23:40 accepted-restoration deadline.
Each run still needs complete fresh backup/mirror, hashes, health, resource,
kernel, device, correctness and rollback gates. Never automatically retry a
GPU/device failure; no package installation, global loader change, driver,
boot, firmware, GPU reset, production promotion or Git push is implied.
Other B60 consumers remain paused until Jason resumes them. Test safety gates
are not dependent on a human being available overnight.

At 23:03 PDT Jason explicitly removed the 23:20 stop and directed continued
testing until he instructs resumption of regular GPU activity. This supersedes
both absolute 23:20/23:40 calendar limits during the exclusive reservation.
Retain per-experiment bounds: fresh preflight, at most 30 minutes of an
experiment and accepted recovery within the next five minutes, independent
transient rollback watchdog, no candidate automatic restart, no production
promotion, and immediate stop on failed gates or GPU/device faults. Each
subsequent experiment refreshes evidence and keeps a new immutable run identity;
never treat a prior preflight as indefinitely valid. Cancelled the obsolete
calendar-limited controller while it was still running accepted Vulkan
controls: no candidate had started. Cancelled only its source-local synthetic
runner processes and verified accepted health before resuming an exclusive
comparison. Preserve its completed warmup evidence; do not overwrite it.

### Exclusive SYCL session 1 — complete, 2026-10-10 23:21 PDT

Fresh 23:05:43 preflight passed; completed Vulkan warmup + five measurements,
one corrected candidate start, protected generation, SYCL warmup + five
measurements, validated accepted restoration and Vulkan warmup + five
post-controls. All 18 suites scored 12/16 with exactly the four documented
baseline failures, no new scoring/runtime failure. The sole candidate
`2ab1b68b4be9497483fc62ca39f1ff9f` selected B60 SYCL0 and offloaded 33/33
layers. Actual maps proved private loader 1.33.1, oneAPI libsycl 9.0.0 and
Intel Compute Runtime 26.35.39758.10. CPU-mapped model buffer 545.62 MiB and
small SYCL host buffers remain; all-layer offload is not zero CPU participation.
Immutable host proof SHA-256
`a12864c15ed43c31369a1dc0244e1d544331d1ca560ed5846ec9258c52e40b70`.

SYCL fusion-off suite medians: 2.2626915, 2.2331075, 2.2154860, 2.2520945,
2.1868760 seconds. Median 2.2331075, compared with 2.41432425 for the ten
Vulkan pre/post medians: **7.5059% lower end-to-end request latency / 1.08115x
request speed**. Six cases with identical completion-token lengths show
7.9210% median latency reduction; other outputs vary in length. This is not
isolated decode/TTFT or proof of the 15% promotion threshold. The slight
Vulkan pre/post drift is preserved in the report, not hidden. Candidate backend
INFO logging uses verbosity 4 for proof; accepted Vulkan uses default verbosity
3, so observed diagnostic overhead is included rather than claiming peak speed.

Complete immutable LXC 114 report:
`/var/lib/b60-inference/evidence/matched-sycl-exclusive-20261010-report.json`,
SHA-256 `bbbaf807ff72ef90704c6d537a417ff1dd2835e4bd9e51af7d2baa6aedc6bef2`.
It contains 15 measured-file hashes, per-case lengths/latencies and limitations.
The controller finished successfully at 23:21:19, after the revoked calendar
stop. Accepted production is restored and candidate stopped; the rolling
watchdog is disarmed only after validation. News remains intentionally disabled.

#### Trial-storage margin correction and next one-variable test

After all measured controls finished, moved only the extracted, task-derived
private driver/IGC tree from `/opt/b60-level-zero-trial-20261010/root` into
`/dev/shm/b60-driver-assets-20261010/root`, preserving the original namespace
with a symlink. Verified every file/link, byte digest, mode, uid and gid before
and after. 63 entries / 440,191,320 derived bytes; aggregate content/metadata
digest `187c14dd162626abb13fc2c5f4eea182c95d820ec771f63f90d8b4e095e89ea9`.
Free root space improved from 21,477,978,112 to 21,918,326,784 bytes. Migration
proof SHA-256 `7163286fd215295e345375f65e16fdfeac3aa3a3ba052b1de4f7c5dfbf69e981`.
No accepted binary/unit/model, installed package or backup moved/deleted.
Private trial artifacts are volatile and must be restaged after reboot;
accepted Vulkan production is independent of them.

Under standing Stream A authorization, next compare fusion **1** against the
working loader-1.33.1/fusion-0 result. Preserve model, precision build, GPU,
context, batch, threads, KV, flash-attention, reasoning and scoring. The storage
placement changes startup staging only; exclude warmups, preserve byte hashes
and record placement. Use new identity `20261010-fusion-on`, new full preflight,
five measurements per phase, rolling watchdog, exact invocation/offload proof
and unchanged correctness/fault stops. Do not automatically retry a failure.

### Exclusive fusion-on session — complete, 2026-10-10 23:39 PDT

Controller `b60-exclusive-trial-fusion-on` completed successfully at 23:39:54.
Candidate invocation `61536172b00f4968bbe1add80598b4bb` loaded private 1.33.1
and offloaded 33/33 layers to B60 SYCL0. Exact mapped-runtime proof SHA-256:
`bd7e36945fe73dfead2b14b56a087ec2dc7519abcf12db983d6d68ff88311b66`.
All five measured SYCL suites had no new correctness failure (12,12,12,12,13
passes; the fifth also passed stale-news). Vulkan controls remained 12/16.
Median SYCL request latency was 2.1440585 seconds: **11.6519% lower latency /
1.13189x request speed** against the ten contemporaneous Vulkan control medians.
Seven identical-completion-length cases show 10.3060% median reduction.
This does not yet establish isolated decode improvement or general quality.
Accepted hashes, health, authenticated generation, xe/Vulkan and clean kernel
scan passed; candidate stopped and watchdog disarmed. News stays disabled.
Immutable complete report on LXC 114:
`matched-sycl-exclusive-20261010-fusion-on-report.json`, SHA-256
`f8a0e1f4df0dbf00abbc1223b93595cdc3ae3cb440ae7c0d52da20d62d3b2560`.

#### Next one-variable precision comparison

Official b11429 releases provide an FP16 SYCL build alongside FP32; the pinned
[release workflow](https://github.com/ggml-org/llama.cpp/blob/b11429/.github/workflows/release.yml)
uses `GGML_SYCL_F16=ON`. The
[backend guide](https://github.com/ggml-org/llama.cpp/blob/b11429/docs/backend/SYCL.md)
recommends measuring both precisions for the actual workload. Downloaded and
publisher-digest verified only the runtime archive (not a model): 54,298,316
bytes, SHA-256 `dbbf6e0d767b3da3b4f13c7fa8bb49582cdd427b800e060d0958568c8c4fc973`.
Extracted 174,018,614 bytes into a new private RAM-backed namespace after all
fusion-on controls finished. Same server SHA as FP32; FP16 backend SHA-256
`58757946256db139bab7ddab56dbe6e8d5503bb41518eb25bfc734c175c68591`.
No system installation or production change. Dependency inspection resolves
private loader 1.33.1 and all libraries; staging proof SHA-256
`bc29dfafdce6d9069b2c35ad173cc25b867b3c7c47542527848632871b5af3c5`.

Fresh full preflight at 23:41:57 passes with 21,918,326,784 bytes disk,
10,836,482,048 bytes RAM and 20,379,389,952 bytes VRAM headroom, today's exact
backup and freshly checked successful mirror. Started new immutable identity
`20261010-fp16-fusion-on`; change only compiled backend precision, retaining
fusion 1 and all inference flags. Five measurements per phase, independent
30-minute watchdog and validated accepted restoration remain mandatory.
No FP16 speed or correctness result is claimed before measurement completes.
Local tests include tar traversal/link/device refusal, precision scoping,
single-start restoration and midnight/calendar-cutoff bypass with the rolling
deadline still enforced (15 B60 BAR tests and 32 inference tests pass).

### Exclusive FP16 session — complete, 2026-10-10 23:58 PDT

The single FP16 candidate invocation `542904b564074298b07c15af63c3d8d6`
started at 23:47:49 and became ready at 23:49:18; this first precision-specific
warmup is excluded from performance claims. Actual mappings, backend SHA,
fusion=1, private loader 1.33.1 and 33/33 B60 offload are recorded in host proof
SHA-256 `b8d30741fec508973f90986027a597321be50255bd84eeaafce6df0f04fb9bed`.
Every measured candidate/control suite scored 12/16, with the same four baseline
limitations and no new scoring, runtime or GPU/kernel failure. FP16 medians:
2.0357545, 2.029335, 2.0354085, 2.034541, 2.028128 seconds. Combined control
comparison: **15.5912% lower request latency / 1.18471x request speed**;
five identical-completion-length cases show 16.1867% median reduction.
This is one session of short synthetic requests, not yet two-session workflow
reproducibility or an isolated decode-speed claim.

Validated accepted restoration, protected generation, xe/Vulkan and all five
post-controls; completed successfully at 23:58:29 and disarmed its watchdog.
News remains disabled under the exclusive reservation. Complete immutable
LXC 114 report `matched-sycl-exclusive-20261010-fp16-fusion-on-report.json`,
SHA-256 `9faacdbc77717e05d7ba46bc9468cead4ebabd1f917f620ad84ca53590202f49`.
Private staging proof is also preserved durably on the host, mode 0600, at
`/var/lib/b60-inference/evidence/fp16-stage-proof-20261010.json`.

Prepared the next same-configuration comparison using the existing calibrated
`aster-grounded-retrieval` (2K) and `aster-context-8k` fixtures: warmup plus
five measured runs per fixture in Vulkan pre, candidate, Vulkan post phases.
New identity `20261011-fp16-workflow-1`; no simultaneous short-suite load.
The source-local runner stops on a failed correctness assertion, persists that
sample privately, and distinguishes actual server decode rate from the
completion-tokens/request-time fallback. Summary refuses mismatched prompts,
token counts, missing repetitions or new correctness failures. Both positive
and negative paths are tested locally (22 BAR/report tests, 35 inference tests).
No longer-workflow result is claimed yet. Fresh preflight and rolling watchdog
remain required; no promotion or Git push has been performed.

Read-only discovery on 2026-09-25 reconciled the documented baseline:

- Proxmox 9.2.20, kernel `7.0.14-19-pve`, Dell BIOS A31 dated 2019-06-05.
- Xeon E5-2698 v4 host with 78 GiB visible RAM and 46 GiB available at the
  observation point.
- ASRock B60 `8086:e211` at `04:00.0`, bound to `xe`. BAR2 remains 256 MiB.
- The endpoint's x1 report is local to the card topology. Root port `00:02.0`
  negotiated PCIe 3.0 x8 and exposes an approximately 49 GiB 64-bit
  prefetchable bridge window.
- Unprivileged LXC 110 is running with 4 vCPU and 16 GiB RAM. VM 105 is stopped
  and has no persistent B60 passthrough mapping.
- `aster-llama.service` is active and health at `192.168.70.12:11435/health`
  is `ok`. Following the separately approved Aster architecture decision, it
  now runs Qwen3.5-9B Q4_K_M on llama.cpp b11429 (`d81235049`) with all layers offloaded,
  one 8,192-token slot, batch 256, microbatch 128, promoted Q4 K/V cache,
  flash attention, Jinja templates and reasoning disabled. The exact former
  27B Q4 unit and earlier Q8 unit are retained for immediate rollback.
- Mesa Vulkan 26.1.6 identifies the B60 as a discrete BMG G21 device. No Intel
  OpenCL or Level Zero package is installed in production.
- The current 9B Q4 K/V unit SHA-256 is
  `6b09f4580ef49b1c61532d22f48cc5091ec95a0e823f73893db7a83f5c1a461e`;
  the immediate former-27B rollback unit is
  `e2019cac74dc23deb4bc92efc38cf3a31a9af1b34d43d651c15e507c392fb184`;
  the retained Q8 rollback unit is
  `7e3e2d9a4c7d861b18ad2c9c83dc294893ea81f295a25918f76fcf3e0f9c9013`;
  the accepted server binary SHA-256 is
  `5faf410bbbc00a1b94b09ee01623699f255365628dfa73b1ee552d9e52a2231d`.
- The active 02:30 snapshot backup completed for LXC 110 on 2026-09-25 at
  02:39. The documented approximately 04:20 TrueNAS mirror remains a scheduling
  constraint and requires live reconfirmation before an overnight test.
- The last seven days of host kernel log showed no B60 reset, device loss or
  kernel OOM. The only matching line was a benign 2026-09-23 VGA arbitration
  message.
- Accepted documented control after the prior llama.cpp/Mesa work is about
  193.3 prompt tok/s at pp4096 and 11.85 tok/s at tg128. Recent production
  responses have sometimes been about 7 tok/s. This project must establish a
  fresh immutable control rather than treating either figure as current truth.
- Prior isolated testing proved that Intel Compute Runtime rejects the current
  256 MiB physical BAR. It did not prove that a safely enlarged BAR is
  impossible on this platform.
- The bounded TrueNAS pull task for LXC 110 is enabled at 04:20 daily. Its
  2026-09-25 run completed successfully from 04:20:01 to 04:24:36 PDT, and the
  mirrored `2026_09_25-02_39_12` archive is present at 38,433,987,658 bytes.
- A credential-bearing GitHub mirror URL was exposed during an earlier local
  bare-repository configuration inspection. The credential value is not
  retained here. Treat it as compromised and revoke/rotate it only through a
  separately authorized security workflow; this project must not use it.

Current upstream research adds a credible performance lead, not proof: current
llama.cpp material reports Intel B60 results and ongoing SYCL/Vulkan work,
including materially higher decode on some Qwen 27B formats. Comparability is
not established because the reported quant, OS and backend differ. The same
upstream record also retains Qwen3.5 SYCL correctness/crash reports and labels
Vulkan I-quant performance as slow. These are candidates for bounded tests only.

## Hypothesis tree

1. **Platform/BAR:** firmware/MMIO allocation prevents a sufficiently large
   physical BAR and blocks Level Zero/SYCL/OpenVINO.
2. **Runtime/kernel:** `xe`, Mesa ANV, llama.cpp revisions, kernels or build
   choices leave Vulkan performance unused.
3. **Model interface:** architecture, quant, KV type, flash attention, context,
   batches or speculative/MTP behavior restrict performance.
4. **Workload/harness:** prompt composition, tool schemas, context position and
   cache behavior explain the synthetic-to-production gap.
5. **Secondary host:** CPU, RAM and PCIe affect load/prefill but may not be the
   main resident-model decode restriction.

## Scope and exclusions

In scope after the applicable gate: read-only inventory and research; local
documentation, harness and fixture development; side-by-side runtime builds;
bounded Vulkan tests; model/quant and application-path comparisons; and a
carefully designed, attended BAR/compute-path decision tree.

Excluded unless separately and immediately approved are BIOS or firmware
changes, bootloader/kernel-parameter deployment, host reboot, GPU reset,
production-service stop/restart, production package/configuration promotion,
credential access, firewall or network changes, backup deletion, destructive
storage work and every remote Git write. Replacing the Dell, moving the B60 or
buying another GPU is not a project solution.

Potentially disruptive experiments may run only from 22:15 through 23:40
America/Vancouver and must restore and validate production before 23:40. They
must not overlap the midnight NAS work, 01:30 media job, 02:30 backup or
approximately 04:20 mirror jobs. Firmware,
BIOS, bootloader, reboot and recovery-dependent work is always attended.

## Authority model

| Fact | Authority |
|---|---|
| Live host, guest, driver and service state | Proxmox/LXC runtime |
| Device, guest and physical inventory | NetBox, reconciled with live state |
| Accepted configuration and procedure | Git documentation and deployed unit/package state |
| Benchmark result | Versioned raw result plus sanitized ledger entry |
| Upstream capability or defect | Primary vendor/source repository at a recorded revision/date |
| Aster-derived knowledge | Non-authoritative mirror with provenance |

Conflicts are recorded and reconciled; they are never silently resolved.

## Architecture and data flows

The Proxmox host owns the B60 through `xe` and maps DRM devices into
unprivileged LXC 110. Mesa ANV/Vulkan and llama.cpp serve a private
OpenAI-compatible endpoint on `192.168.70.12:11435`; Aster in LXC 104 consumes
it over Lab VLAN 70. API keys remain in root-owned service files and are never
captured by this project's fixtures, logs or ledger.

Candidate binaries and configurations remain side by side until promotion.
Raw benchmark evidence is immutable per run. Sanitized summaries reference the
raw path, configuration hashes and source revisions. The accepted service is
restored by a bounded finalizer after every scheduled experiment.

## Privacy and security design

- Use synthetic, non-secret prompts and tool results.
- Never capture API keys, private messages, personal retrieval content or raw
  secret-bearing configuration.
- Keep inference private; add no public ingress, firewall rule or new standing
  credential.
- Run candidates with the existing least-privilege device boundary where
  possible; explicitly record any exception.
- Treat runtime output as untrusted and sanitize kernel/service excerpts before
  Git persistence.
- Reject silent CPU fallback, host-memory spill or an unexplained device path.

## Pre-start risk assessment

| Risk | Likelihood / impact | Control and rollback | Residual decision |
|---|---|---|---|
| Production Aster interruption | Medium / high | Side-by-side builds, one variable per test, fixed window, hard timeout, finalizer and health/generation validation | Covered only by the bounded Stream A envelope after all M1 preflight gates pass |
| GPU reset, device loss or host instability | Medium / high | Baseline kernel log, live health/telemetry, immediate abort, no automatic retry, restore accepted binary/unit | Accept only for an explicitly bounded test |
| Firmware/boot failure without console | Low-to-medium / critical | Do not attempt remotely; require attended console and verified recovery; retain normal boot path | Separate immediate approval is mandatory |
| Incorrect or misleading output | Medium / high | Fixed correctness assertions, two real-workflow passes, independent evidence audit, control rerun | No promotion with regression |
| Secret/private-data capture | Low / high | Synthetic fixtures, schema-limited collection, secret scan, no raw service environment | Stop and quarantine on any exposure |
| Benchmark contamination or cherry-picking | Medium / medium | Warm-up plus five repetitions, medians/spread/raw samples, cold-cache control, pre/post controls | Auditor signs causal conclusions |
| Backup/mirror collision | Medium / high | 22:15–23:40 only, verify schedules/checkpoints immediately before run, skip if completion/rollback cannot fit | No overlap accepted |
| Storage or memory exhaustion | Medium / high | Preflight disk/RAM/VRAM headroom, bounded artifacts, no host spill, cleanup only after evidence acceptance | Stop before unsafe headroom |
| Upstream experimental regressions | Medium / high | Record exact revision, applicability, known defects and rollback; tiny-model enumeration before target model | Experimental work remains isolated |

No irreversible operation is required for Phase 0 or Phase 1. The project adds
no authentication, firewall, DNS, public exposure or external data service.
Expected users affected by later tests are Aster users and dependent local
services; interruption is detected by service health, authenticated synthetic
generation and dependent-workflow checks.

## Accepted bounded Stream A authorization envelope

Jason changed the project to Stream A on 2026-09-26. Autonomous work covers
non-secret read-only LAN checks, primary-source research, local documentation,
synthetic fixtures, harness code, local tests and local commits. After the M1
harness, immutable control, checkpoint, time-window and tested-finalizer gates
all pass, it also covers the enumerated reversible non-firmware Vulkan
experiments in M2: side-by-side llama.cpp candidates and one-variable tests of
batch/microbatch, threads/affinity, flash attention, supported KV types,
context, prompt/graph cache reuse and memory headroom. Each experiment must run
only from 22:15–23:40 America/Vancouver, retain the accepted b11081 artifacts,
use synthetic data, stop on the documented abort conditions and restore and
validate production before 23:40. This authorization does not waive a platform
approval prompt.

The following remain outside Stream A and require Jason's immediate approval:
every Git push; firmware, BIOS, bootloader or kernel-parameter change; reboot or
GPU reset; package installation/removal; persistent service/unit/configuration
change or production promotion; scheduler deployment; credential access or
rotation; firewall/network/public-exposure change; destructive storage work;
backup deletion; and any experiment whose rollback or checkpoint cannot be
verified. SYCL/Level Zero/OpenVINO, model downloads and BAR changes remain
outside this envelope until separately reviewed because their prerequisites and
blast radius differ from the bounded Vulkan work.

## Persistence plan

- Ledger schema: `docs/projects/B60-Inference-Engineering/ledger.schema.json`.
- Candidate register:
  `docs/projects/B60-Inference-Engineering/candidate-fixes.md`.
- Sanitized ledger: `docs/projects/B60-Inference-Engineering/experiments.jsonl`
  (created when the first fully specified experiment is recorded).
- Raw artifacts: one immutable directory per run under a protected non-secret
  evidence root, referenced by path and checksums rather than committed when
  large.
- Candidate-fix records include URL, date, revision/version, applicability,
  prerequisites, known regressions, rollback and released/experimental state.
- Resume by reading `AGENTS.md`, the project standard, this project, Git status,
  the last ledger record and current live health before any action.

## Milestones

### M0 — Reconcile state and preserve a control

- [x] Confirm clean authoritative repository state before project drafting.
- [x] Reconcile host/kernel/BIOS, GPU driver/BAR/topology, guest allocation,
  runtime/Mesa version, service flags and current health read-only.
- [x] Confirm active 02:30 backup schedule and a fresh LXC 110 archive.
- [x] Confirm the approximately 04:20 mirror schedule and last success live.
- [x] Record model shard SHA-256 values without disrupting production.
- [x] Inventory exact last-known-good binary, unit, packages and rollback paths.
- [x] Capture a fresh immutable control with the Phase 1 harness.

Gate: an independent reader can reproduce the control and restore the accepted
production service.

### M1 — Baseline and instrumentation

- [x] Implement schema-validated environment and result capture.
- [x] Add synthetic pp512, pp4096 and tg128 tests at context positions 0, 4K
  and 8K where supported, with warm-up, five repetitions and pre/post controls.
- [x] Add cold-prefill isolation, prompt-cache state and CPU-fallback checks.
- [x] Add GPU frequency, temperature, power, VRAM/RAM, CPU/affinity and bounded
  sanitized kernel-log capture where supported.
- [x] Add real Aster conversation, persona, read-only tool, grounded retrieval,
  2K and 8K fixtures with TTFT, completion and correctness assertions.
- [x] Characterize variance and quantitatively explain the synthetic/real gap.

Gate: a repeatable baseline, known variance, verified GPU residency and a tested
rollback invocation.

### M1 preflight and finalizer timing

The guarded invocation is `python3 scripts/b60-inference/guard.py preflight
PREFLIGHT.json --estimated-minutes N`. Its evidence must be collected from
22:00 through 22:14 America/Vancouver and be no more than five minutes old. It
fails closed unless the latest LXC 110 backup and TrueNAS mirror are no more
than 26 hours old, the mirror job state is `SUCCESS`, accepted binary/unit
hashes match, service health is `ok`, the B60 is on `xe`, Vulkan reports BMG
G21, and disk/RAM/VRAM headroom is at least 20 GiB/4 GiB/2 GiB.

No experiment starts before 22:15. The experiment hard-stops at 23:20, reserving
20 minutes for `python3 scripts/b60-inference/guard.py finalize --execute
--allow-production`. The absolute restoration deadline is 23:40. The finalizer
stops `aster-b60-candidate.service`, explicitly stops the accepted
`aster-llama.service`, allows GPU/process state to quiesce for 30 seconds, then
requests one non-blocking clean start. It polls active state and health for up
to five minutes before requiring accepted binary/unit hashes, host `xe` binding
and BMG G21 Vulkan enumeration. Candidate absence is acceptable; failure of any
restoration or validation step is not.
Authenticated synthetic generation remains an additional required validation
before a live control can close. The 2026-10-07 standing authorization permits
only the established protected credential path; the value must never enter
logs, evidence or the conversation.

### Nightly scheduling audit — 2026-10-10

The original 00:30–02:00 window was selected only to precede the 02:30 Proxmox
backup. Live scheduler reconciliation shows that it is not otherwise quiet:

| Scheduled work | Live schedule | B60 impact |
|---|---|---|
| Synology Drive backup | Daily 00:00; integrity check Monday 04:00 | Storage activity at the start of the old window |
| TrueNAS Media and Recovery scrubs | Sunday 00:00, historically to about 02:46 | Directly conflicts with the entire old Sunday window |
| Video archiver | Monday–Saturday 01:30–07:30 | Overlaps the last 30 minutes of the old window |
| Proxmox all-guest snapshot backup | Daily 02:30 | Hard boundary; supplies the next recovery point |
| TrueNAS guest, Mac and B60 pulls | Daily 04:00, 04:15 and 04:20 | B60 mirror normally completes around 04:25 |
| TrueNAS family/config/retention jobs | Daily 04:30, 05:00 and 06:00 | Dense storage-maintenance period |
| Playlist bridge / ARR report | Every six hours at :15 / every five minutes | Small; ARR report is read-only and negligible |
| Archive compaction | Daily 08:00–13:30 | Avoid for uncontended storage operation |

The replacement window is 22:15–23:40 daily. Preparation begins at 21:40 and
fresh evidence is collected at 22:00–22:14. This uses the same day's completed
02:30 backup and 04:20 mirror, avoids both Sunday scrubs and all nightly heavy
jobs, and retains 20 minutes for restoration before any midnight work. The
heartbeat is an orchestration and notification layer, not the timing authority:
the checked-in guard owns the clock, rejects late starts and prevents a delayed
heartbeat from shifting production work into another job's window.

### M2 — Non-disruptive Vulkan optimization

- [ ] Compare the accepted runtime with selected upstream llama.cpp revisions.
- [ ] Test one variable at a time: batch/microbatch, threads/affinity, flash
  attention, supported KV types, context, cache/graph reuse and memory headroom.
- [ ] Compare IQ4_XS with quality-gated Q4_K and Q4_0 candidates where storage
  and model availability permit.
- [ ] Evaluate Mesa/ANV changes and documented environment controls in isolation.
- [ ] Consider MTP/speculative decoding only after ordinary decode is controlled.

Gate: repeated synthetic improvement, two independent real-workflow passes,
health checks and rollback proof.

### M3 — BAR and Intel compute path

- [ ] Reconfirm observable BIOS settings and all bridge apertures without change.
- [x] Analyze SR-IOV/VF reservations and current `xe` BAR-resize behavior.
- [x] Build a safe decision record for `pci=realloc=on`, Dell A34 and attended
  recovery; do not deploy from the analysis alone.
- [x] If a stable larger BAR is separately approved and proven, enumerate Level
  Zero with a tiny workload before SYCL/OpenVINO or the target model.
- [ ] Recheck current B60/Qwen correctness, OOM and reset defects before trials.

Gate: a larger stable BAR with proven recovery, or defensible evidence that safe
software/configuration methods cannot provide one.

#### M3 allocation diagnosis and decision — 2026-10-10

Fresh read-only inspection makes the allocation failure more precise than the
older “no ReBAR” shorthand:

- the B60 physical BAR2 advertises 256 MiB through 32 GiB and is currently
  256 MiB;
- its SR-IOV VF BAR2 is programmed to 2 GiB per VF and the device advertises
  24 VFs, so PCI core reserves 48 GiB before `xe` probes even though no VF is
  enabled;
- the upstream root-port path has an approximately 49 GiB prefetchable window;
- `xe` then releases the PF resources and requests a 32 GiB PF BAR2, making the
  combined bridge requirement approximately 80 GiB; the request therefore
  fails with `-ENOSPC` and the original allocations are restored; and
- `xe.max_vfs=0` suppresses driver-exposed VFs but runs too late to prevent the
  generic PCI core's initial 48 GiB VF reservation.

This proves that the immediate failure is an aperture-allocation conflict, not
absence of a physical Resizable BAR capability. The large above-4G allocation
also strongly suggests that Dell's Above-4G/Large-MMIO path is active, although
the exact setup values still require an attended BIOS-console check.

Linux commit `72207463f7a4a6818a88f4ef57802b42da534301`, merged for 7.3-rc6,
is titled `drm/xe/pf: Keep VF LMEM BAR size low if no VFs enabled`. Inspection
of the exact three-line change shows that it restores the VF template after an
SR-IOV enable failure or disable. It does not shrink an already-programmed
2 GiB-per-VF template during initial PCI enumeration. It is therefore relevant
preventive work but is not, by itself, a remedy for this host's boot-time
48 GiB reservation.

The newest package visible in the configured Proxmox repository is
`proxmox-kernel-7.0.14-23-pve-signed` (package SHA-256
`f4cc4a95b76fb86fdcadb28a835d0ebd8897f6e325570f33ea44fd4f186dbb31`).
Offline extraction of its `xe.ko` found the old `Failed to set VF LMEM BAR`
path and no new reduce/restore path. Upgrading from the running 7.0.14-20 only
to obtain this fix is therefore rejected.

The leading software remedy is now a narrowly reviewed pre-`xe` helper that,
when SR-IOV is administratively disabled, reduces VF LMEM BAR2 to the minimum
supported size before `xe` asks PCI core to enlarge PF BAR2. The helper can use
the stock kernel's existing exported GPL PCI APIs and avoids replacing the
whole kernel. On this device,
256 MiB per VF would reduce the aggregate VF reservation from 48 GiB to 6 GiB,
which has enough aggregate capacity beside a 32 GiB PF BAR within the observed
49 GiB aperture, but still requires suitable alignment and bridge relocation.
That arithmetic is necessary but not sufficient: a source-applicability review,
offline build and package inspection must precede any install. The first host
trial requires a fresh backup and mirror, retained current kernel, verified
boot-menu rollback, local console or equivalent recovery, an attended reboot,
and post-boot validation of BARs, bridge windows, `xe`, Vulkan, LXC 110 and
accepted Aster production. No kernel, firmware, boot or BAR mutation is
authorized by this analysis.

Current ordering:

1. compile and inspect the helper against matching Proxmox headers in an
   isolated builder;
2. prefer an official Proxmox kernel only if its extracted module proves it
   contains an effective initial-probe fix;
3. otherwise present the exact pre-driver helper and attended recovery plan
   for immediate approval, with deployment isolated to a second kernel so the
   current kernel and initramfs remain the rollback path;
4. keep Dell A34 plus explicit Above-4G/Large-MMIO verification as secondary
   platform hygiene, not the first experimental variable; and
5. do not use `pci=realloc=on` as a blind first step: it cannot manufacture
   enough space while the 48 GiB VF reservation remains.

#### Attended BAR trial result — 2026-10-10

Jason explicitly approved the fourth test's v3 install, exact kernel arguments,
dedicated GRUB entry and console-attended reboot. Boot ID
`70bca49a-5e1c-4910-be7b-034daac7b732` on `7.0.14-23-pve` obtained physical
BAR2 at `0x31000000000`, size **32 GiB**, and restored BAR0 to 16 MiB at
`0x30800000000`. The disabled VF LMEM BAR is 256 MiB per VF, with a **6 GiB**
aggregate reservation. `xe` reports CPU-accessible VRAM `0x5fa000000`, equal
to usable VRAM, with no Small BAR message. The B60 remains bound to `xe` and
Vulkan enumerates BMG G21. Accepted production binary/unit hashes match and
endpoint health is `ok` after normal LXC 110 autostart.

The prerequisite discovered by the third trial was **alignment**, not merely
capacity: the 48.65 GiB root-port window at `0x30080000000` contained no
32 GiB-aligned span, and a sibling device prevented its release during `xe`
probe. The fourth trial used `pci=realloc=on` plus
`pci=resource_alignment=35@0000:04:00.0` to reserve aligned PF resources during
initial PCI assignment, then used the verified v3 helper before udev to set the
hardware ReBAR and shrink the oversized GTT/VF reservations.

The tested module SHA-256 is
`7d040a5d709161376a171b32258e37ac4804b051dea2e34f44730ec08a7b5894`;
the separate test initramfs SHA-256 is
`5c844425a4d5c124334b6f7cea0bc1f20f4b619c65edb0536937d0c77965d308`.
The test entry and GRUB `next_entry` were removed after boot. Normal
7.0.14-23 initramfs SHA-256 remains
`3d514d6c0f2c4724b84b205adc9c0bebe4fb828dd76f1677d4e5a40d55963450`,
and retained 7.0.14-20 initramfs remains
`9ea827de6a9fd0bfde7ce6636ca2cd583ebe7c2a3521791d4f1e669ba3bca22a`.
Jason subsequently approved persistent boot promotion and a final attended
reboot. `/etc/grub.d/41_b60_bar` and
`/etc/default/grub.d/zz-b60-bar.cfg` select the pinned
`b60-bar-aligned-7.0.14-23` entry and the same verified image. Repeat boot ID
`0b822e46-9f9e-469b-8927-38782b20dcc5` reproduced 32 GiB BAR2, 16 MiB BAR0,
6 GiB VF reservation and fully CPU-accessible usable VRAM. Normal 23 and
retained 20 recovery entries remain unchanged. Kernel upgrades require explicit
rebuild/validation; no automatic helper migration is installed. Any
Level Zero/SYCL package/backend trial remains a separate decision.
This result proves full BAR access, not faster inference.

Source, build method, host-specific GRUB candidate and recovery details are in
`scripts/b60-bar/README.md`. The unsigned module's kernel taint is expected and
recorded; no firmware or BIOS change was needed.

Persistent repeat-boot recovery passed: accepted binary and unit hashes match,
`scripts/check-aster-b60.sh` passes, and inference/Aster health is `ok` from
LXC 114's established client path. Authenticated synthetic 7+5 generation
returned the correct answer in 0.458 seconds (three completion tokens; not a
performance benchmark). Host evidence:
`/var/lib/b60-inference/evidence/2026-10-10-bar-persistent-generation.json`,
SHA-256 `970e93c387a817c0f445da06768f140ebef2587979a921b8251c12dd57a764f6`.
All expected guests and news timers recovered. Host-management-source HTTP
checks time out while same-VLAN client checks pass; no firewall change was made.
The source-report startup race was handled by a normal refresh after readiness.

#### BAR performance follow-up — 2026-10-10

Owner acceptance: Jason accepts the observed gain and full-BAR configuration
and directs moving forward rather than reverting to the old BAR profile for
further causal benchmarking. No small-BAR comparison boots are planned.
Retained small-BAR entries remain emergency recovery only. The next objective
is isolated Intel Level Zero enumeration and then a same-model SYCL comparison,
not an immediate removal of the working Vulkan production backend. Read-only
inventory found no `sycl-ls`, `clinfo`, `ze_info` or queried Level Zero runtime
packages/libraries in LXC 110. Runtime installation and non-Vulkan compute
execution remain separately approval-gated; production is unchanged.

Owner requested push and immediate before/after testing. Restored this checkout's
origin to the documented Forgejo SSH primary after finding unexpected local
checkout indirection; merged four concurrent main commits without rewriting
history and pushed `124e228`. GitHub mirror matched. A credential-bearing URL
was encountered in the unrelated local mirror configuration; its value is not
recorded here. Owner should revoke/rotate that exposed credential through the
normal protected process; no credential mutation was inferred or performed.

Fresh archive/mirror size 38,852,679,165 and task 3 SUCCESS were verified,
along with model/binary/unit hashes, headroom, health and clean kernel evidence.
Ran the exact historical production summary suite on unchanged accepted 9B:
one warm-up plus five measured suites. Median latency fell from historical
3.070279 to 2.403453 seconds (**21.7% lower observed latency**); measured suite
medians span 2.399258–2.407435. All completion-token counts match. The same four
assertions fail: 12/16 before and in every repeat, with no new correctness
failure. These failures remain limitations, not a clean suite pass.

The historical first eight cases were disproportionately slow, only one baseline
suite exists, and the kernel changed with the BAR fix. Consequently this is
not a BAR-only causal speed claim. A same-kernel small/full/small repeated control
would need separate attended boot authorization. Sanitized results and hashes:
`bar-performance-20261010.json`. Production remains healthy, service restart
count is zero, news timers restored, no relevant kernel/GPU fault observed.

### M4 — Alternative runtime and model interface

#### Approved isolated Level Zero trial — 2026-10-10

Jason approved isolated runtime setup, device enumeration and a tiny workload
before a same-model SYCL comparison, without host driver replacement, reboot or
production promotion. LXC 110 is Debian 13 with glibc 2.41 and GCC 14 libraries.
Official Intel Compute Runtime 26.35.39758.10, IGC 2.41.5 and gmmlib 22.10.0,
plus Debian loader/headers 1.20.6, were SHA-256 verified and extracted only under
`/opt/b60-level-zero-trial-20261010`. No dpkg installation, global linker change,
production unit change or service stop occurred. GitHub API rate limiting was
worked around using publisher release-page hashes and authenticated APT index
metadata, not credentials. Dependency versions and `ldd` resolved successfully.

The first bounded execution of the compiled 4 KiB device-memory roundtrip
aborted in Intel's `command_stream_receiver.cpp` line 1205. Direct inspection
of the exact 26.35.39758.10 source identifies the condition as
`UNRECOVERABLE_IF(preemptionSurfaceSize == 0)`. The generic Battlemage hardware
defaults declare a nonzero page-sized preemption surface; the cause of the
effective zero is not yet established. No enumeration output was flushed, so
neither enumeration nor the roundtrip is claimed as passed. No SYCL/model load
or automatic GPU retry followed. Relevant kernel fault scan stayed empty;
accepted binary/unit hashes, inference/Aster health, zero restarts and active
news timers were confirmed. Evidence: `level-zero-trial-20261010.json`.

Next: separately approve one instrumented diagnostic execution (call-stage
logging and debugger/trace if available) to locate the failing initialization
path. Do not disable preemption or set arbitrary runtime overrides as a blind
workaround. Retained isolated files have no boot or production consumers;
Vulkan remains accepted. This phase changes no speech, UI, address, identity,
firewall, scheduling or monitoring ownership and does not graduate a new service.

Jason then approved exactly one instrumented diagnostic retry. Call-boundary
logging plus SIGABRT backtrace capture showed exit 134 inside the initial
`zeInit(ZE_INIT_FLAG_GPU_ONLY)`, before `zeDriverGet` or any test memory/command
operation. Immutable log in LXC 110:
`/opt/b60-level-zero-trial-20261010/diagnostic-attempt-1.log`, SHA-256
`a7b00943e049f6cc541611d286644860e5826c10ce10127962c3144c5cb89e3e`.
No further GPU execution followed; production health remains `ok`, zero restarts,
news timers active and relevant kernel-fault scan empty.

Offline exact source revision `dfa6faf3d866ea6a22b70df5a7bd2a507aa457bd`
explicitly supports B60 device E211. Kernel debugfs GT0 hwconfig lacks CSR-size
key 62; GT1 reports no hwconfig. Source `system_info.h/.cpp` defaults absent
CSR size to zero, `drm_neo.cpp` copies that to `CsrSizeInMb`, and
`product_helper.cpp` replaces the generic page-sized default with that size
times one MiB. `command_stream_receiver.cpp:1205` rejects the resulting zero.
This is a strongly supported metadata/runtime initialization diagnosis, not a
confirmed live debugger inspection of the intermediate value. Full BAR is not
rolled back. Next safe work is offline selection/review of a compatible runtime
or a validated metadata fallback. Another compute attempt or preemption override
requires a new specific risk decision; do not automatically retry this binary.

Further offline analysis found an implementation error in the trial's isolated
loader path, superseding the missing-metadata-only diagnosis. IGC packages
extract their compiler libraries under `root/usr/local/lib`, whereas both smoke
attempts set only `root/usr/lib/x86_64-linux-gnu`. A non-GPU `ctypes.CDLL`
check fails to find `libigdfcl.so.2` under the original environment and loads
both that library and `libigc.so.2` with both directories included.
`Device::isStateSipRequired()` requires a compiler interface;
`initializeCommonResources()` skips SIP initialization if it is absent.
The CSR SIP initialization normally supplies the preemption surface size from
its state-save header. Thus missing key 62 alone was an incomplete diagnosis;
missing compiler discovery is the concrete trial-setup defect to correct first.

Prepared `scripts/b60-bar/run-level-zero-smoke.sh` with the corrected
process-local library path and load-only compiler checks. It applies no runtime
preemption override, global linker mutation, host change or service change.
The corrected GPU attempt has not run: prior GPU-abort no-retry gating remains,
and a newly explicit single-attempt approval is required. No runtime version
change or arbitrary CSR-size workaround is justified before this validation.

Jason approved the single corrected-library-path smoke attempt. It exited zero:
Level Zero initializes, enumerates Intel Arc Pro B60 (`8086:e211`), creates its
context/compute queue, allocates 4 KiB device memory, submits a roundtrip and
verifies all bytes. All cleanup API calls passed. Log SHA-256:
`c55befa2f8240ca482c853b363647e51aa278c57265b54760ab34047ddadf1b5`
at `corrected-library-attempt-1.log` in the isolated directory. Production
health remained `ok`, zero restarts and no relevant kernel fault. This validates
the compiler-discovery correction without any preemption override or BAR rollback.

Continued the original approved isolated SYCL trial by staging official b11429
FP32 archive, SHA-256
`5e6c382f8ae19d906a6aa0c806faa7184ed1cef872e60fff15373f3162416b08`.
Its dependencies require private oneAPI compiler/math libraries; staging uses
bounded `/dev/shm/b60-oneapi-trial-20261010`, not dpkg/global linker installation.
No production backend switch is authorized or performed by this preparation.

OneAPI runtime-only packages were extracted to disposable tmpfs (2.20 GB
extracted, 408 MB archives): compiler/shared/OpenMP 2026.1.1, TBB 2023.1,
UMF 1.1, oneDNN 2026.0.2 and MKL core/SYCL BLAS 2026.1. SHA-256 values were
verified against Intel's HTTPS package index and retained in the local manifest;
no system installation was performed. Main executable linkage resolved, but
first bounded SYCL enumeration exited 134 with “No device of requested type
available.” Its log SHA-256 is
`ca45fc397f3a2a422d754924f1bde7f37d5ef9835edb8f4f1738f46782edb115`.
No model load or automatic GPU retry followed. Production remains healthy.

Read-only recursive adapter inspection found `libhwloc.so.15` unresolved in
both Unified Runtime Level Zero adapters, although main executable `ldd`
had passed. Added Debian libhwloc15 2.12.0-4 privately, verified against the
APT index SHA-256 `aa53c4a1878475e7309f2c265c54d9a8a4602dec95564cf84d471d7376ff616c`.
Load-only ctypes checks now load both adapters successfully without invoking
GPU initialization. One corrected-dependency SYCL enumeration attempt requires
explicit approval after the failure. Model performance/correctness remains
untested. Guest disk availability after candidate staging is 21,161,783,296
bytes, below the documented 20 GiB floor (21,474,836,480); recover scratch
archive headroom safely before any model-load gate. Tmpfs dependencies are
disposable and need restaging after reboot. No speech, UI, host driver, global
linker, scheduler, credential or production configuration change occurred.

Jason approved one corrected-dependency SYCL enumeration attempt. It exited
zero, listing `Intel Arc Pro B60 Graphics`, `level_zero:gpu:0`, 160 compute
units, 25,669 MB global memory and driver `1.17.39758+10`. Immutable log
`sycl-enumeration-corrected-1.log` SHA-256:
`3df320bffb38faffe406356f6349f3f654aadac17eb505ddacd8159a9eb4f382`.
Production health is `ok`, zero restarts, relevant kernel-fault scan empty.

Fresh backup and mirror were verified again at 22:01; both contain the same
38,852,679,165-byte archive, task 3 enabled and SUCCESS. Recovered the 20 GiB
disk floor by moving only candidate package archives, candidate tarball and
SYCL binaries to `/dev/shm/b60-sycl-assets-20261010`; a trial-only link preserves
the SYCL path. Disk availability is now 21,503,397,888 bytes. No files deleted
or production paths changed. These reproducible trial assets disappear on
reboot and must be restaged; logs and manifest remain on disk.

The preflight/finalizer guard still contained retired 27B binary/unit hashes.
Updated the local guard to accepted b11429/9B hashes and binary path, retaining
all freshness, timing, headroom and finalizer controls, with a regression test
that rejects retired hashes. No production stop or model load occurred in this
enumeration milestone. Next is the originally approved same-model SYCL trial,
gated by a fresh current-hash preflight and tested restoration. Vulkan remains
production; no speed or correctness advantage for SYCL has yet been established.

#### Matched 9B backend trial — 2026-10-10 (failed closed)

Jason explicitly requested pushing the enumeration milestone and continuing
matched 9B SYCL performance/correctness tests. Forgejo and its GitHub mirror
both reached `1866594`. This trial retains Vulkan production and uses the same
b11429 release, exact model, 8K context, Q4 K/V, flash attention on, reasoning
off and synthetic 16-case post-policy suite. Five measured repetitions per
backend plus excluded warmups and Vulkan pre/post controls are planned.
Baseline's four known scoring failures are not counted as new regressions.
Any runtime error, new scoring failure, incomplete GPU offload or relevant
kernel event aborts; no automatic candidate retry is allowed.

The host harness is `/run/b60-matched-sycl/matched-sycl.py`, with current guard
and source-local credential runner staged separately. Only a transient
`aster-b60-candidate.service` is allowed, `Restart=no`, runtime capped at 900
seconds. A separate transient host restoration watchdog must be armed before
the trial starts. The harness also restores accepted production in `finally`,
validates authenticated synthetic generation and restores both news timers.
It uses a conservative 22:55 load cutoff inside the normal experiment envelope.
Evidence goes to LXC 114 `/var/lib/b60-inference/evidence/matched-sycl-20261010-*`;
never to the almost-floor LXC 110 disk. Interrupted continuation must inspect
candidate/accepted state, watchdog and existing immutable evidence first;
do not replay a partial candidate run or overwrite evidence.

Fresh 22:12 preflight passed all gates, with model hash matching, mirrored
38,852,679,165-byte backup, clean kernel scan and both dependent workers idle.
The trial started at 22:15 with the independent 30-minute restoration watchdog.
Vulkan warmup plus five measured suites completed: measured medians
2.413183, 2.4183145, 2.406876, 2.402978 and 2.411537 seconds; aggregate median
2.411537 seconds. Each scored 12/16 with exactly the four known failures.

The single SYCL candidate started at 22:20:33 and aborted at 22:20:37 during
startup compute warmup, before serving any synthetic evaluation request.
Trace identifies `ggml_sycl_op_rms_norm_fused` submitting through the SYCL
queue/handler and error 44 `UR_RESULT_ERROR_UNSUPPORTED_FEATURE`. Candidate
invocation is `5e4a34e8ebac4a0fbe1a64baf284a687`. No candidate retry or post-failure
benchmark ran; SYCL measured repetitions and valid speed/correctness results
are zero. No kernel/device fault was detected. This is a backend/runtime
unsupported operation, not evidence that full BAR has regressed.

The `finally` finalizer restored production and validated accepted hashes,
active state, `xe`, BMG G21 Vulkan, protected authenticated generation and
news timers by 22:21:32; accepted service has zero restarts and Aster health
is `ok`. Disarmed the independent watchdog only after restoration checks.
Host immutable sanitized trace SHA-256 is
`d38c4f6b5bf4df2157dc50cb52bfdc0a1f6c553fd5b954b6da2c4b9bf1ffa637`;
failure record `matched-sycl-failure-20261010.json` SHA-256 is
`de3d22654d46ec590d9e9665ec8ef00ded3ec3c925435101db09b38a335bb194`.

Offline official b11429 source review verified that
[`GGML_SYCL_ENABLE_FUSION`](https://github.com/ggml-org/llama.cpp/blob/b11429/ggml/src/ggml-sycl/ggml-sycl.cpp)
defaults to 1 and that
[`fusion.cpp`](https://github.com/ggml-org/llama.cpp/blob/b11429/ggml/src/ggml-sycl/fusion.cpp)
returns false from `ggml_sycl_can_fuse` when it is 0, bypassing the fused RMS
dispatch. A single candidate-only `GGML_SYCL_ENABLE_FUSION=0` trial is the
narrow next diagnostic; it changes no host driver, preemption or production
configuration. It is **not a confirmed remedy**: the unfused normalization
kernel shares launch characteristics, and runtime/compiler compatibility
remains a possible cause. Requires explicit post-failure retry approval and
a valid fresh/timing envelope; do not silently reuse stale preflight or retry.

Harness review also replaced POSIX whitespace syntax with Python `\s` in its
kernel regex, and limited startup/offload evidence to the exact invocation
instead of all historical candidate-unit logs. During this run, the independent
grep-based live kernel checks covered IOMMU faults despite the initial Python
regex warning. Regression tests prove candidate startup failure restores
without retry and the corrected fault pattern catches IOMMU faults without
matching “default.” New milestone remains locally committed pending another
specifically approved push. Production promotion is not authorized.

#### Explicit fusion-disabled retry and one-time preflight exception

On 2026-10-10 Jason approved one diagnostic compute retry changing only the
candidate's `GGML_SYCL_ENABLE_FUSION` to 0. After being explicitly told the
ordinary fresh-preflight collection window had closed, he separately approved
collecting a new full preflight now. This exception is confined to this one
retry on 2026-10-10 before the conservative 22:55 load cutoff; all freshness,
backup/mirror, hashes, headroom, health, correctness, kernel, rollback and
23:20/23:40 deadlines remain unchanged. It does not change the recurring
schedule, authorize another failure retry or permit promotion/push.

The guard's opt-in `--approved-fusion-retry-20261010` is date-expiring and
leaves default timing unchanged. New immutable outputs use prefix
`matched-sycl-fusion-off-20261010`, preserving the failed attempt's evidence.
One candidate process is allowed with no restart, 900-second runtime limit,
core dumps disabled and independent `b60-fusion-restore` transient watchdog.
If startup/correctness passes, continue the originally requested matched
five-repetition performance comparison and Vulkan post-control. Any compute
failure aborts and restores production without an automatic candidate retry.

The fresh 22:27:56 collection passed all unchanged gates. Five new Vulkan
controls scored 12/16 with only the known four failures: medians 2.417553,
2.407410, 2.4058685, 2.4137595 and 2.4069545 seconds (aggregate 2.407410).
The sole fusion-disabled candidate failed at 22:33:59 during startup warmup:
`Error OP RMS_NORM`, error 44 `UR_RESULT_ERROR_UNSUPPORTED_FEATURE`, exit 1.
Invocation `10ef71a32e4e4edfaf0a776a55e532bb`. This rejects a fusion-only
explanation; no SYCL measured repetition or post-failure benchmark ran.
Finalizer verified production and authenticated generation by 22:34:54,
with accepted hashes, active health, zero restarts, news timers and Aster
health passing. No relevant kernel/device fault. Watchdog disarmed only after
successful restoration; archived failure record SHA-256
`0025dcc8070fc8406886056173e47286dddfede16f897c134724c99ad8df8011`,
sanitized trace SHA-256
`9ab18e76cba9069c199ab1cd5850933d135f7e676e3a9048a21fcd5c27054223`.

Offline review found a concrete trial packaging mismatch: the exact
[b11429 Ubuntu SYCL release workflow](https://github.com/ggml-org/llama.cpp/blob/b11429/.github/workflows/release.yml)
pins oneAPI 2026.1 and **Level Zero 1.33.1**; the isolated trial uses matching
oneAPI 2026.1.1 but Debian loader **1.20.6**. This is a candidate cause, not
proof of the failing underlying API. Official
[SYCL backend guidance](https://github.com/ggml-org/llama.cpp/blob/b11429/docs/backend/SYCL.md)
requires matching package versions. Locally downloaded and inspected the
publisher's `libze1_1.33.1+u24.04_amd64.deb` (1,089,826 bytes), matching GitHub
asset digest `298d6d3656a13f112497f557be2cb557efb67374bc7d069aa77a9115db909e1d`.
Its libc >=2.38 and libstdc++ >=13.1 requirements fit the documented Debian
13 trial. **Not installed, not staged on the lab, and no new GPU execution.**

Decision then pending: approve one attempt replacing only the candidate's private
loader with 1.33.1 (retain fusion off and everything else), including a new
full fresh preflight if attempted tonight. Source-supported `SYCL_UR_TRACE=2`
can record UR call diagnostics during startup without credentials/private
requests, if necessary. Do not blindly switch adapters: current Intel runtime
documentation describes V2 as default on Xe2/Battlemage, and availability of
a legacy-switch symbol was not demonstrated in the staged library. No driver,
firmware, preemption, package-install or global-linker change is proposed.

#### Approved private 1.33.1 loader attempt — guarded observability abort

Jason approved private extraction and one loader-only retry, including fresh
preflight tonight with unchanged cutoffs. Extracted the checksum-verified
package in `/dev/shm/b60-loader-1331-trial-20261010/root`, leaving installed
packages, global linker configuration, older private loader and production
unit unchanged. Actual process maps confirmed `libze_loader.so.1.33.1`;
library SHA-256 is
`a4859c17183add6412c48d44d0f356f8ef5d7b43ae35ed253074f670a6879d23`.
Fusion remained disabled. Full fresh preflight passed at 22:46:09 PDT:
backup/matching successful mirror, accepted binary/unit/model and candidate
hashes, inference/Aster health, xe, Vulkan, disk/RAM/VRAM, temperature and a
nonempty clean kernel-log scan. Disk free was 21,503,164,416 bytes: keep trial
staging in tmpfs because this is only about 28 MB above the 20 GiB floor.

A fresh Vulkan confirmation scored 12/16 with the same four known limitations;
median request latency 2.4922815 seconds. Immutable LXC 114 evidence:
`matched-sycl-loader-1331-20261010-vulkan-confirmation-warmup.json`, SHA-256
`e2086fd83e9c76b7efaf83876265935d9787763ca48a54f1ff9672fc0daf97fa`.
This single confirmation is not a five-repetition matched speed comparison.

The sole candidate started at 22:48:03, loaded its model and listened at
22:49:29. Invocation `1cfae5fc97f045fba5f67f6059481671`. No previous
unsupported-feature exception appeared. The harness then aborted because its
mandatory full-GPU-offload log proof was absent. No candidate authenticated
generation or 16-case test request was sent; no speed gain is established.
The process was intentionally stopped, not observed to crash.

Offline source review identified the observability defect in the exact
[b11429 logging implementation](https://github.com/ggml-org/llama.cpp/blob/b11429/common/log.cpp#L498):
backend INFO/CONT callbacks map to verbosity **4**, above the server's default
**3**. Added `--log-verbosity 4` to future isolated candidate controllers;
kept the exact-invocation/all-layers-offloaded gate, rather than weakening it.
This correction was tested locally, **not rerun on the B60**. Another model
start requires a newly scoped approval/window; the one approved start was used.

Finalizer restored accepted production and protected synthetic correctness by
22:50:30 PDT, with accepted hashes, active health, xe/Vulkan and zero automatic
service restarts. No relevant kernel failure. The independent 22:55 watchdog
was disarmed only after validated restoration; competing News schedules were
then held per Jason's new priority override. Sanitized immutable host record
`/var/lib/b60-inference/evidence/loader-1331-outcome-20261010.json` SHA-256
`f826baea16cf55c36b7fffcaa8e7a9e3afe315bc5b96139543ccebbc62781a45`;
startup trace SHA-256
`d517ab271a544e2e1f3b2c939e0d1f3a0eeb345e6a691fc4cb03e89e0d8bcbc6`.
No Git push or production promotion. Next live test is the same corrected
loader/fusion-off candidate with verbosity 4, authenticated correctness, then
five matched repetitions and fresh post-control if every gate passes and the
approved window can contain the complete study. Do not repeat five full
pre-controls merely to establish startup viability.

- [ ] Evaluate only exact-B60/Linux candidates that can be isolated.
- [ ] Require tiny-model enumeration, target-architecture correctness, explicit
  fallback/transfer accounting and like-for-like quality comparisons.
- [ ] Separate ordinary decode, speculative accepted-token throughput and
  maximum stable context.

Gate: select on correct, recoverable end-to-end operation rather than headline
throughput.

### M5 — Aster workload engineering

- [ ] Attribute prompt components by tokens and processing time.
- [ ] Test lazy tool/retrieval schemas, cache reuse/invalidation and deliberate
  context policy without losing personality, safety or source attribution.
- [ ] Report fewer-token gains separately from runtime/GPU gains.

Gate: real Aster workflows meet accepted latency/correctness targets with safe
headroom.

### M6 — Promotion, monitoring and handoff

- [x] Promote atomically with accepted and last-known-good artifacts.
- [x] Run Doctor, B60 validation, Aster curricula and dependent regressions.
- [x] Prove rollback and observe the defined reset/OOM/device-loss soak.
- [x] Add quiet drift/research monitoring and operator-grade runbook updates.
- [x] Complete integration impacts and terminal close-out or durable waiting state.

## Validation and evaluation

Every benchmark group uses an idle sample, warm-up, five measured repetitions,
median and spread, then an accepted-control rerun. Results record exact model
and shard hashes, runtime source/build flags, kernel/driver/Mesa/firmware,
configuration hash, BAR/topology, cache/context state, resource telemetry,
errors and correctness. Unlike models, quants, contexts, cache types,
speculative modes or concurrency are never presented as like-for-like.

Promotion additionally requires two independent real-workflow sessions,
authenticated health, tool-schema validity, grounded-source expectations,
dependent regression checks, no new GPU reset/OOM/device loss during the
defined soak and tested automatic restoration of the accepted service.

## Observability and maintenance

Extend existing B60/Doctor coverage only where it adds actionable signal:
accepted runtime/config drift, benchmark drift, service health, GPU residency,
recent `xe` reset/device-loss/OOM and evidence/schedule freshness. Avoid a
duplicate alert when existing Doctor or Beszel coverage owns the condition.

A weekly primary-source research review should deduplicate against the
candidate register and remain quiet on no change. Notify only for a credible
remedy, merged/released relevant fix, newly documented hazard, test-ready
candidate, blocked decision or meaningful conclusion. The recurring automation
is designed here but will not be created until separately approved.

## Backup, restore and rollback

Before any operational test, verify the latest LXC 110 archive and its mirror,
the accepted binary/unit/package inventory, free disk/RAM/VRAM, current service
health and a bounded rollback command sequence. Retain the accepted server
binary and unit beside candidates. The experiment finalizer restores the
accepted service and proves B60 `xe` binding, discrete Vulkan enumeration,
health, authenticated synthetic generation and dependent Aster health.

Abort immediately on a new `xe` reset, device loss, kernel OOM, host/guest
impact, unexpected CPU fallback/spill, unsafe telemetry, invalid output,
unverifiable rollback/checkpoint, material topology surprise, secret exposure
or approach to the 23:40 restoration deadline. Do not auto-retry a potentially
destabilizing failure class.

### M0 accepted and rollback artifact inventory

Read-only inventory on 2026-09-25 established the following immutable anchors:

| Role | Path / version | SHA-256 or evidence |
|---|---|---|
| Accepted server | `/opt/llama.cpp-b11081/llama-server` | `47692a3806ad5615c218e347f3bd55870436f07117c041cea7bf880b3b978693` |
| Accepted server implementation | `/opt/llama.cpp-b11081/libllama-server-impl.so` | `b89200852d6f1cbf4c2f4764b19ce86bc316c41280798cab3dc0b2afded1985d` |
| Accepted Vulkan backend | `/opt/llama.cpp-b11081/libggml-vulkan.so` | `dfbfe66354e7b9f7a0236194d665874152983284315d6c4f76a36aaff96b0dc5` |
| Accepted Q4 K/V unit | `/etc/systemd/system/aster-llama.service` | `e2019cac74dc23deb4bc92efc38cf3a31a9af1b34d43d651c15e507c392fb184` |
| Immediate Q8 rollback unit | `/etc/systemd/system/aster-llama.service.pre-q4-20261010` | `7e3e2d9a4c7d861b18ad2c9c83dc294893ea81f295a25918f76fcf3e0f9c9013` |
| Prior runtime | `/opt/llama.cpp-b10507/llama-server` | `c5aabbf808bab4029ac7fcdb382fe3ab0806a1abe1b036ad2bf160e8742320f5` |
| Prior server implementation | `/opt/llama.cpp-b10507/libllama-server-impl.so` | `e50ee38d96dc769c9e9cfbee020e4f968cfc76f4b9d6e20e251bb915054a31d4` |
| Prior Vulkan backend | `/opt/llama.cpp-b10507/libggml-vulkan.so` | `f448536ac8a7b95d3d05448f0317e835b91bff0f2a4a62576a31d98028abd701` |
| Prior unit copy | `/etc/systemd/system/aster-llama.service.bak-b10507` | `2850809f20608af7b4ffe76cc4166cfda52e48caaedcf39b9ca59f9b3bc7a105` |
| Older unit copy | `/etc/systemd/system/aster-llama.service.backup-20260901-aster-fix` | `83960f7dc8476980b955fab40fc879aa72bdc461fa99956d1986528106301651` |

The guest package inventory records `mesa-vulkan-drivers` 26.1.6-1~bpo13+1,
`libvulkan1` 1.4.309.0-1 and `vulkan-tools` 1.4.304.0+dfsg1-1. The accepted
IQ4_XS shards hash to
`40fac4050e940397dbf13087afd50f4734a11805bf9d65ef8ddd7483470e6199`
and `83ee4f4f205fa514161778c41df1ea14144faa0f713510893b63c2395f5c2d53`.
The resident Q4_K_S alternative hashes to
`75bc9c8adba2842e72f0ab5201aaa07133c5010b566305c09187fcbdcd364017`
and `83ee4f4f205fa514161778c41df1ea14144faa0f713510893b63c2395f5c2d53`.
The identical second-shard hash is expected from the observed files but is not
yet a quality or compatibility conclusion. Checksums were calculated with idle
I/O and lowest CPU scheduling priority; the production service was not changed.

The accepted rollback target for any future candidate experiment is b11081 plus
the accepted unit above, not b10507. The b10507 pair is retained as an older
known runtime comparison. Exact restoration commands and an actual rollback
proof remain gated operational work and must be reviewed before the first load
test.

## Documentation and systems-of-record updates

- [ ] **HomeLab Doctor** — add only actionable runtime/config/health/drift checks
  not already covered; test failure behavior.
- [ ] **Monitoring/alerting** — define GPU health/performance history and quiet,
  owned thresholds without duplicates.
- [ ] **Backup and recovery** — verify candidate/accepted configuration and raw
  evidence protection plus isolated rollback.
- [ ] **NetBox** — no topology change currently; update only if live inventory
  authority changes.
- [ ] **Human wiki** — add operator guidance and recovery links at promotion.
- [ ] **Aster mirror/snapshot** — publish only accepted, sourced conclusions.
- [ ] **Operational reference and runbooks** — update accepted service,
  benchmark and recovery procedures.
- [ ] **Repository documentation** — maintain this project, portfolio,
  hardware/operations references and changelog.
- [ ] **Diagrams/rack records** — not currently applicable; no physical change.
- [ ] **Homepage/service discovery** — not currently applicable; no new service.
- [ ] **Authentication/authorization** — no new identity; preserve existing
  service-key custody and least privilege.
- [ ] **DNS, certificates and firewall** — not applicable unless architecture
  changes; none is proposed.
- [ ] **Automation and schedules** — gated scheduler and weekly monitor require
  lock, timeout, missed-run semantics, durable status and quiet no-change policy.
- [ ] **Security inventory** — no secrets in Git/evidence; record ownership,
  modes, update responsibility and temporary-access removal.
- [ ] **AI administration integration** — not a new service; existing Aster
  administration boundary remains authoritative and no wider capability is added.

## Graduation criteria

The project graduates when a materially better stable configuration passes all
synthetic, real-workflow, health, soak, rollback and integration gates, or when
every credible current remedy is safely tested or ruled out and the fixed
hardware ceiling is documented reproducibly. If progress requires attended
recovery capability, a non-waivable decision or an upstream fix, status becomes
waiting rather than falsely complete, with the weekly research monitor retained.

## Evidence log

| Date | Role | Action and evidence | Result / next safe action |
|---|---|---|---|
| 2026-09-25 | Principal investigator | Read `AGENTS.md`, project standard, portfolio, completed Local AI record, Aster operations, hardware/network baselines, changelog and relevant Git history; authoritative tree was clean at `e50b670` | Proposed Stream M project drafted; no production or remote Git state changed |
| 2026-09-25 | Platform/runtime engineer | Read-only Proxmox/LXC inventory captured BIOS, kernel, root-link width, BAR, `xe`, guest allocation, Mesa, llama.cpp, unit flags, hashes and health | Starting facts reconciled; model hashes, mirror success and exact rollback inventory remain M0 gaps |
| 2026-09-25 | SRE reviewer | Confirmed active 02:30 snapshot job, fresh LXC 110 archive and seven-day kernel-log absence of resets/OOM/device loss | Keep 00:30–02:00 disruptive window and verify the 04:20 mirror before tests |
| 2026-09-25 | Research monitor | Reviewed current official llama.cpp documentation/issues/discussion and Dell documentation | B60 performance lead warrants controlled research; SYCL correctness risk and small-BAR gate remain; candidate register expansion is next |
| 2026-09-25 | Inference engineer | Re-read governing instructions; verified TrueNAS task 3 is the enabled bounded 04:20 LXC 110 pull, last state `SUCCESS` at 04:24:36 PDT, and confirmed the newest mirrored archive | M0 mirror gap closed without changing TrueNAS or Proxmox |
| 2026-09-25 | Inference engineer | Inventoried and hashed accepted b11081, prior b10507, unit backups, Vulkan packages and four resident model shards; shard hashing used idle I/O and lowest CPU priority | Exact accepted rollback artifacts and model identities are recorded; no service, package or configuration state changed |
| 2026-09-25 | Harness engineer | Added an offline schema validator, deterministic planner, 13 synthetic fixture cases and unit tests under `scripts/b60-inference/`; all five tests, fixture validation, plan generation and bytecode compilation pass | Local M1 foundation is ready; it cannot execute production load, and the runner/production control remain separately gated |
| 2026-09-25 | Security reviewer | Recorded that an earlier bare-repository inspection exposed a credential-bearing GitHub mirror URL, without copying the value | Jason must revoke/rotate the credential through a separately authorized security workflow; do not use it |
| 2026-09-25 | Harness engineer | Added a guarded OpenAI-compatible runner: dry-run by default, explicit execution interlock, a second non-loopback interlock, pre/post health checks, one warm-up and five measurements; fake transport tests make no network request | Nine combined harness/runner tests pass; production execution, telemetry integration and correctness evaluators remain pending |
| 2026-09-25 | Repository operator | Attempted the approved push through this checkout's `origin`; Git rejected it because `origin` is an unrelated checked-out local repository. A corrected credential-free Forgejo URL push was blocked by the platform pending exact destination approval | No remote changed; do not alter the other checkout or reuse the exposed mirror credential |
| 2026-09-25 | Repository operator | Merged concurrent Aster Adaptive Computing work, preserved both changelog histories, and pushed integrated commit `aaf775b`; Forgejo and the GitHub protection mirror both resolved `main` to `aaf775b64a969c97fef39b6c59119baf2b8e34dd` | Remote synchronization complete; this checkout's local-path `origin` remains stale and must not be treated as authoritative |
| 2026-09-25 | Harness engineer | Added executable correctness evaluators for all fixture assertions, separate prefill/decode samples, conservative server-reported cache-hit detection and create-once mode-0600 raw evidence with fsync and SHA-256 | Twelve local tests pass, including incorrect tool/source rejection and overwrite refusal; CPU-fallback and live telemetry collectors remain incomplete |
| 2026-09-25 | Telemetry engineer | Read-only LXC 110 discovery found `xe` hwmon package/VRAM/channel temperatures, per-process DRM fdinfo with 13,762,772 KiB resident VRAM and 1,017,304 KiB resident GTT at idle, 16 GiB guest RAM with 7,547,627 KiB available, and llama-server CPU affinity `3,9,19,20` | Temperature, VRAM/GTT, RAM and affinity can be captured without new packages; frequency and power counters were not exposed and must be recorded unavailable rather than inferred. Only `vulkaninfo` is installed; no `intel_gpu_top`, `xpu-smi` or `sensors` |
| 2026-09-26 | Telemetry engineer | Added a read-only LXC collector plus strict parser for `xe` temperatures, process VRAM/GTT residency, guest RAM and CPU affinity. Unknown, duplicate, impossible and credential-like fields are rejected; unsupported frequency, power and CPU-fallback values remain explicit nulls. Ran the collector live through stdin without installing or writing it; it returned the expected strict fields for PID 441 | Fifteen local tests pass and the live read-only format is proven. This is partial M1 telemetry: bounded host kernel-log capture and positive CPU-fallback detection remain before the checkbox can close |
| 2026-09-26 | Telemetry engineer | Added bounded Proxmox kernel-log collection plus strict sanitization/classification for reset, device loss, hang and OOM. Added affirmative CPU-fallback classification: explicit CPU fallback is failure; full Vulkan layer offload plus material VRAM residency is pass; insufficient evidence remains unknown. A live read-only last-hour collection returned no relevant failure lines | Nineteen local tests pass. The M1 telemetry-capture checkbox closes; orchestration into complete ledger records remains next |
| 2026-09-26 | Owner authorization | Jason directed the project to continue as Stream A | Bounded autonomous envelope accepted as recorded above. M1 gates still prohibit production load; firmware/boot/reboot, packages, persistent promotion, schedulers, credentials, destructive work and every Git push remain immediate-approval operations |
| 2026-09-26 | Harness engineer | Added complete experiment-record assembly binding deterministic fixture identity, raw artifact hash, environment hashes, telemetry, kernel findings, health, correctness and affirmative fallback evidence. Measured-only median/MAD is calculated, incomplete samples are rejected and the validated record is written create-once mode 0600 | Twenty-one local tests pass. Cold-prefill/cache/fallback and record-assembly gates close; fresh immutable production control and finalizer rollback proof remain before production load |
| 2026-09-26 | Reliability engineer | Added fail-closed preflight and finalizer orchestration with accepted hashes, exact candidate/accepted units, headroom/freshness gates and 00:20/00:30/01:40/02:00 timing. Fake execution verifies exact rollback order and failure handling; dry-run emits the command plan without mutation | Twenty-five local tests pass. Current time was 13:29 PDT, so immediately-before-window backup/mirror verification was correctly deferred; live finalizer execution and authenticated generation remain unproven and no production benchmark ran |
| 2026-09-29 | Automated preflight | At 00:20–00:23 PDT fast-forwarded the clean checkout to authoritative Forgejo `4f5d281` without pushing, then verified the 2026-09-28 02:39 LXC 110 archive, bounded TrueNAS task 3 `SUCCESS` at 04:25, matching accepted binary/unit hashes, healthy service, `xe`, BMG G21 Vulkan, 23.3 GB free disk, 7.9 GB available RAM, about 11.7 GB VRAM headroom and no relevant 24-hour kernel failure line. `guard.py` accepted a 60-minute plan with 01:40/02:00 deadlines | Preflight passed, but the immutable control did not run: authenticated generation needs the existing service credential and credential access remains outside the bounded Stream A envelope; live finalizer execution is also unproven. No production load or service mutation occurred; Jason approval is required for the credential-bound test path |
| 2026-10-06 | Resume and mirror reconciliation | Rebased the unpublished B60 evidence commit onto authoritative Forgejo `2de4595` without pushing. Read-only inspection confirmed TrueNAS task 3 moved to `/mnt/Recovery/guests/aster-lxc110`, remains the enabled bounded 04:20 pull, completed `SUCCESS` at 04:24, and contains the 2026-10-06 02:39 archive (38,439,311,784 bytes). All 25 B60 tests pass | The earlier missing-task result was an obsolete path query, not a failed mirror. Current backup documentation was corrected locally. A fresh in-window preflight, credential-bound authenticated control and live finalizer proof remain required before production load |
| 2026-10-07 | Owner authorization | Jason explicitly approved both previously blocking operations for the next eligible bounded B60 run: use of the existing service credential solely for authenticated synthetic generation, and live invocation of the documented finalizer/rollback that stops only the candidate service, restarts the accepted `aster-llama.service`, and validates restoration | Credential values must not be exposed or persisted. This approval does not authorize scheduler deployment, Git push, broader credential access, persistent production changes, or any other excluded action. All normal preflight, time-window, abort and restoration gates remain mandatory |
| 2026-10-07 | Standing owner authorization and scheduler | Jason authorized recurring nightly testing until a reproducible fix is found and the project completes. Created active thread heartbeat `b60-nightly-validation-loop` for 00:20 America/Vancouver daily. Standing authorization covers the existing credential only through the protected path for authenticated synthetic generation, the documented live finalizer/rollback, and the already enumerated bounded Stream A Vulkan experiments | Each run remains fail-closed and limited to the 00:20 preflight, 00:30–01:40 experiment window and restoration before 02:00. The automation must pause on failed or surprising gates and when the project completes. Git pushes, firmware/BIOS/boot/reboot/GPU reset, packages, persistent production changes or promotion, network changes, destructive storage, backup deletion, SYCL/Level Zero/OpenVINO, BAR changes and model downloads remain excluded and separately gated |
| 2026-10-08 | Nightly automation timing guard | The first recurring heartbeat began at 00:35 PDT, after the mandatory 00:20–00:29 preflight window. It failed closed: no preflight was represented as valid and no production load or service mutation ran. Moved the heartbeat trigger from 00:20 to 00:05 and made early preparation plus the exact in-window evidence requirement explicit | Tonight was skipped safely. The earlier trigger allows checkout reconciliation and read-only preparation before the next 00:20–00:29 gate while retaining the 01:40/02:00 deadlines and all standing exclusions |
| 2026-10-09 | Live finalizer proof | Rebased the five unpublished B60 commits onto authoritative Forgejo `2f92914` without pushing. At 00:20 PDT the exact preflight passed: fresh 2026-10-08 LXC 110 backup and successful bounded mirror, accepted hashes, healthy service, `xe`, BMG G21 Vulkan, 21.9 GB disk, 8.8 GB RAM, 11.6 GB VRAM headroom and no relevant 24-hour kernel failure. At 00:30 invoked the standing-authorized live finalizer. The accepted service restart did not become healthy within its start-post window; repeated warmup health checks returned 503 and systemd entered auto-restart. No benchmark or candidate load ran | Production restoration is not yet proven and accepted service remains in an unhealthy restart cycle. The safe next recovery step is an explicit stop, quiesce and single clean start, but the platform rejected that mutation because it exceeds the recorded finalizer sequence. Immediate owner approval is required; do not run further experiments |
| 2026-10-10 | Recovery and owner continuation | Jason authorized continuing the requested stop/quiesce/clean-start recovery. Before mutation, read-only validation found the accepted service had recovered automatically after 36 restarts: active, health `ok`, accepted binary/unit hashes, `xe`, BMG G21 Vulkan and no relevant kernel failure since the finalizer. No healthy service was stopped and no benchmark ran outside the window. Revised the local finalizer to stop accepted production explicitly, wait 30 seconds, request a non-blocking clean start, poll active plus health for up to five minutes, and only then validate hashes, driver and Vulkan; all 25 B60 tests pass | The original immediate restart validation is rejected as unsafe. Updated and resumed `b60-nightly-validation-loop`; its next operational action is one successful live proof of the revised sequence in a fresh overnight window before any benchmark |
| 2026-10-10 | Automation efficiency audit | Reconciled durable evidence, Codex schedules and live Proxmox/TrueNAS schedules. Since recurring nightly testing was created, both eligible nights fired, but neither produced a benchmark: 2026-10-08 missed the narrow preflight window and 2026-10-09 stopped at the failed finalizer. The separate 2026-09-29 one-time run passed preflight but stopped at then-unapproved credential/finalizer gates. No experiment ledger or raw benchmark result exists, so automated experimental throughput is 0/3 attempts despite substantial harness, safety and recovery engineering | Moved the guarded lab window to the demonstrably quieter 22:15–23:40 period, scheduled preparation at 21:40, moved weekly research to Monday 20:30, retained fail-closed clock enforcement in code, and muted routine unchanged notifications. The next run must prove the revised finalizer and then capture the fresh immutable control; a failed proof pauses the loop and names required owner action explicitly |
| 2026-10-10 | Owner-authorized exclusive window | Live schedule reconciliation found two remote scheduled B60 consumers omitted from the initial infrastructure-only audit: LXC 114's hourly news pipeline (up to five minutes randomized delay) and 05:15/17:15 digest synthesis; Paperless is also demand-driven every five minutes but Jason confirmed it is not currently in use. At Jason's request, stopped only `news-aggregator-ingest.timer` and `news-aggregator-digest.timer`; both worker services are inactive and the news UI remains active | B60 has an exclusive scheduled-work window through tonight's run. The nightly automation must restore and verify both news timers after accepted production validation or any abort. A separate one-time 23:45 restoration heartbeat provides a second recovery path and must not replay the missed briefing |
| 2026-10-10 | Control-run preparation | Reconfirmed accepted service health, `xe`, BMG G21 Vulkan, stopped news timers and 25/25 local tests. Packaged the tested runner as SHA-256 `3bff21d1d7ed17d7a33ed31100049715276708fdb7b06d0216eea6d611203825` and staged it source-locally on LXC 114 at `/run/b60-runner.pyz`; staged synthetic fixtures at `/run/b60-synthetic-fixtures.json` (SHA-256 `c0b72c8e554c7384e63d3183f0bfe83e8f7e8548cb938d72e2aeea11a3a7f190`). Confirmed the protected `/root/.news-aggregator-llama-key` exists without reading it, and the non-loopback dry run refused execution as designed | Tonight's first control is fully specified: fixture `pp512-cold-pos0`, endpoint `http://192.168.70.12:11435`, existing source-local key file, and create-once mode-0600 output `/var/lib/b60-inference/evidence/2026-10-10-control-pp512-cold-pos0.json`. The evidence directory is root-only mode 0700 and the output path does not yet exist |
| 2026-10-10 | Owner-authorized daytime execution | Jason clarified that the cleared B60 schedule was intended for immediate work through the day. Re-ran every safety gate against today's 02:39 backup and successful 04:24 mirror, clean kernel evidence, accepted hashes, health, `xe`, BMG G21, 21.9 GB disk, 8.3 GB RAM and adequate VRAM. The revised live stop/quiesce/clean-start finalizer passed. Authenticated source-local controls then passed correctness and health: API warm-cache tg128 median was 6.713 tok/s; cold-cache tg128 was 9.072 tok/s, a 35.1% improvement. Raw `llama-bench` comparison showed b11081 at 193.29 pp4096 / 11.863 tg128 and installed b11429 at 200.24 / 11.970, only +3.6% / +0.9%. A 2/4/8-thread sweep was flat at about 193.2 / 11.85. All raw outputs are mode 0600 beneath `/var/lib/b60-inference/evidence`; accepted production was restored healthy after every stop | Newer installed runtime and thread count are rejected as primary fixes. Prompt-cache reuse is the first material lead and exceeds the 15% threshold on synthetic decode, but requires repeated real Aster workflow/correctness comparison before any persistent client change or promotion. News timers remain intentionally stopped for the owner-authorized daytime window |
| 2026-10-10 | Aster-workflow cache comparison | Added and validated an identical warm-cache twin of the synthetic Aster conversation fixture. Five measured cold and warm runs all passed the fictional-scope, nonempty-response and no-tool-call assertions. Cold-cache decode median was 5.793 tok/s; warm-cache was 5.778 tok/s, so the apparent 35.1% short-prompt cache gain did not transfer to the longer Aster-style prompt. The harness's 512-token construction target produced about 3,600 actual model tokens, while the 64-token construction target produced 475, exposing a systematic fixture-token calibration defect. Production remained active and healthy | Do not promote `cache_prompt=false` as a general fix. The strongest current explanation is context-length sensitivity in the server path. Next work is tokenizer-calibrated context-length profiling, followed by a repeated real Aster latency/correctness comparison at matched actual token counts |
| 2026-10-10 | Tokenizer calibration and Q4 KV candidate | Replaced word-count estimation with live `/tokenize` calibration and added the previously omitted OpenAI tool schema to tool-call fixtures; 27 local tests pass. At an actual 524-token prompt, matched Q8 cold/warm controls were 5.943/5.948 tok/s, rejecting prompt cache as the remedy. Two clean transient server sessions changing only K/V cache from Q8_0 to Q4_0 produced 11.047 and 11.008 tok/s; the required accepted-Q8 post-control was 6.689 tok/s. This is a reproducible 64.6% improvement against the stronger control and 85.9% against the pre-control. All 30 measured Q4 workflow runs passed: conversation, persona, real tool-schema selection, 2,060-token grounded retrieval and 8,012-token marker recall. Decode remained 10.44–11.76 tok/s across those contexts. Immutable evidence hashes include Q4 sessions `ec80e2b65ee10f04c7541c55ad0aa0d37482408698616097f3991c6136737ff9` and `bf449a79e950193de8797ae7a03b8cd44482e93c1a5991be85cc341f9ad0a377`, post-control `15bdd314152506062caca2cf41e60b73b8a8d372705b59464ad1a37ef4edf95e`, tool `9f4c81472786cac0f8d0f853d22981939d423cc8cc568f99f1004e17c9144d1e`, grounded `72ff66c964ddb1b58aa24aac93e0fae4bfaafd21bf222870f7fa85e77ec01b69` and 8K `c24de46e4219016e2f46716d956c9dd03e4a8983d4a556075d1b4862e9ea7c76`. Every transient candidate was removed and accepted binary/unit hashes plus health were revalidated | Q8 KV traffic in the API server path is the reproduced bottleneck; Q4 K/V is the promotion candidate and exceeds the 15% threshold with no tested correctness regression. Persistent unit change remains explicitly outside standing Stream A authorization. Next action is owner-approved atomic promotion of only `-ctk/-ctv q8_0` to `q4_0`, followed by Doctor/dependent regression checks, soak and rollback proof; do not repeat exploratory nightly benchmarks while awaiting that decision |
| 2026-10-10 | Owner-approved Q4 K/V promotion | After explicit approval, revalidated the accepted hashes, health, `xe`, BMG G21 Vulkan and headroom. Preserved the exact Q8 unit at `/etc/systemd/system/aster-llama.service.pre-q4-20261010`, atomically promoted only `-ctk/-ctv` to Q4_0, daemon-reloaded, quiesced for 30 seconds and clean-started production. The promoted unit hash is `e2019cac74dc23deb4bc92efc38cf3a31a9af1b34d43d651c15e507c392fb184`. Authenticated post-promotion workflow evidence `8465a95e1e85be45bf2203ae4c408f7ecb9fd24aa52297091adadeabaa4fbecc` passed correctness at 10.987 tok/s median. B60 binding/Vulkan/rollback-VM checks and Aster agent health passed; service is active with zero restarts and the immediate kernel failure scan was empty | Q4 K/V is now accepted production. Retain the exact Q8 unit for immediate rollback. Complete the longer reset/OOM/device-loss observation, then update operational guidance and close or narrow the nightly automation |
| 2026-10-10 | Exercised soak and close-out | Continued immediately rather than deferring to the scheduled window. At 9 minutes 50 seconds after the promoted clean start, ran a fresh authenticated 2,060-token grounded-retrieval series. All six runs passed source attribution and unsupported-source assertions at 10.724 tok/s median; immutable evidence SHA-256 is `0e5683c468373128e06806340499432171279611244a94e6fddc55f5a60c5376`. After load, the service remained active with zero restarts, both inference and Aster agent health were `ok`, binary/promoted-unit/rollback-unit hashes matched, news timers were active and the kernel scan remained empty for reset, hang, fault, OOM and device loss | Graduation gates pass. Existing B60/Doctor health monitoring remains authoritative; no duplicate recurring benchmark is needed. Pause the project automation, retain Q8 rollback, and reopen only on health/correctness/performance regression or an explicitly scoped new optimization project |
| 2026-10-10 | Subsequent Aster 9B role promotion | The separate Aster architecture programme selected Qwen3.5-9B reasoning-off for post-policy summaries and Jason explicitly approved production promotion. Revalidated today's backup/mirror and every B60 gate, then installed pinned b11429 and the exact 9B model while preserving the accepted 27B and Q8 rollback units/models. The first attempt failed closed before mutation on staged RAM; corrected sequencing quiesced 27B before the RAM gate. Final 9B unit/runtime/model hashes match, disk headroom increased, protected-path Aster generation passed, service restarts remain zero and the kernel scan is clean | B60 engineering remains complete; accepted production is now the Aster programme's 9B configuration. Retain the former 27B unit/runtime/model as immediate rollback and retarget the finite post-promotion observation to the new accepted hashes |
| 2026-10-10 | M3 BAR diagnosis and source review | Live read-only PCI evidence proved that the 24 × 2 GiB VF LMEM template consumes 48 GiB of the approximately 49 GiB bridge aperture before `xe` requests a 32 GiB PF BAR. Extracted official Proxmox 7.0.14-23 offline and confirmed its `xe.ko` lacks the 2026-10-03 upstream VF restore fix. Reviewed that exact upstream change and found it does not alter initial enumeration. Added a narrow one-shot pre-driver helper. It matches only `0000:04:00.0` plus `8086:e211`, refuses enabled VFs, selects the device's minimum advertised VF BAR and uses existing exported GPL PCI APIs. The source passes strict kernel checkpatch and its APIs are exported by Linux v7.0 | No host state changed. The helper is the preferred proof candidate because it retains the stock kernel. Next safe work was an isolated matching-header build and binary inspection; any package install, initramfs/boot change or reboot still requires immediate owner approval and attended recovery |
| 2026-10-10 | M3 isolated helper build | With explicit owner approval, downloaded but did not install official `proxmox-headers-7.0.14-23-pve`, verified package SHA-256 `4a65d1279907ca20e9c8d8a2facd86f2d94082142c19be20419a03e5594d79c4`, and compiled in temporary LXC 114 storage using its existing toolchain. `MODPOST` resolved every expected versioned PCI symbol. The module SHA-256 was `16feed7a34c9d80941ceb27f6d8e1981c18b719332a57865d11f3092bf3ea7d4`; vermagic was exactly `7.0.14-23-pve SMP preempt mod_unload modversions`; it declared no module dependency. Host and guest `/sys/module/b60_vfbar` were absent and live PF/VF BARs remained 256 MiB/2 GiB | Compile gate passes. The module was not installed, loaded or persisted, and both temporary build directories were removed. The remaining operation is deliberately disruptive: install the second official kernel and matching headers, rebuild/install the helper only for it, create and inspect only its initramfs ordering, then perform one console-attended boot after fresh backup/mirror checks. That entire operation requires immediate owner approval |

| 2026-10-10 | M3 attended full-BAR proof | Four separately approved boots isolated ordering, VF resource bookkeeping and PF alignment. Fourth boot on 7.0.14-23 obtained 32 GiB physical BAR2, correct 16 MiB BAR0 and a 6 GiB VF reservation. `xe` exposes all usable VRAM; Vulkan enumerates BMG G21. Accepted 9B binary/unit hashes, inference and Aster health, authenticated synthetic correctness, guest autostart and news timers pass. No relevant kernel/GPU failure appeared. The source-report job initially ran before LXC 104 started; an ordinary rerun succeeded and the host has zero failed units. Immutable generation evidence on the host is `/var/lib/b60-inference/evidence/2026-10-10-bar-v3-generation.json`, SHA-256 `3aa01c1f531fba9d8888960deba6a84f690a26802f7b468e4759bf8177e928d8`; sanitized PCI/recovery facts are in `bar-v3-trial-20261010.json` | Full-BAR trial passes without a BIOS change. Temporary test GRUB entry and next_entry removed, builder headers and temporary files cleaned, normal 7.0.14-23 image and retained 7.0.14-20 unchanged. Persistent deployment and repeat boot validation remain pending; no BAR-derived speed gain is claimed. No Git push performed |

## Close-out

Completed 2026-10-10. Q4 K/V is promoted and validated at 10.724–10.987 tok/s
in post-promotion authenticated workflows, compared with 5.943–6.689 tok/s for
the matched Q8 controls. Tool use, grounding, persona, conversation and 8K
recall passed; the exercised soak ended with zero restarts and no relevant
kernel event. The exact Q8 unit remains available for immediate rollback.
Existing B60/Doctor monitoring owns ongoing health; the project automation is
paused and no recurring synthetic load remains.
