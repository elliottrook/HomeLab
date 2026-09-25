# B60 inference engineering

> Status: Active — Stream M
>
> Owner: Jason
>
> Proposed: 2026-09-25
>
> Started: 2026-09-25
>
> Completed: not applicable

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
  is `ok`. It runs llama.cpp b11081 (`161755f29`) with all layers offloaded,
  one 8,192-token slot, batch 256, microbatch 128, Q8 K/V cache, flash
  attention, Jinja templates and reasoning disabled.
- Mesa Vulkan 26.1.6 identifies the B60 as a discrete BMG G21 device. No Intel
  OpenCL or Level Zero package is installed in production.
- The unit SHA-256 is
  `7e3e2d9a4c7d861b18ad2c9c83dc294893ea81f295a25918f76fcf3e0f9c9013`;
  the accepted server binary SHA-256 is
  `47692a3806ad5615c218e347f3bd55870436f07117c041cea7bf880b3b978693`.
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

Potentially disruptive experiments may run only from 00:30 through 02:00
America/Vancouver and must restore and validate production before 02:00. They
must not overlap the 02:30 backup or approximately 04:20 mirror jobs. Firmware,
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
| Production Aster interruption | Medium / high | Side-by-side builds, one variable per test, fixed window, hard timeout, finalizer and health/generation validation | Stream M approval per operational change |
| GPU reset, device loss or host instability | Medium / high | Baseline kernel log, live health/telemetry, immediate abort, no automatic retry, restore accepted binary/unit | Accept only for an explicitly bounded test |
| Firmware/boot failure without console | Low-to-medium / critical | Do not attempt remotely; require attended console and verified recovery; retain normal boot path | Separate immediate approval is mandatory |
| Incorrect or misleading output | Medium / high | Fixed correctness assertions, two real-workflow passes, independent evidence audit, control rerun | No promotion with regression |
| Secret/private-data capture | Low / high | Synthetic fixtures, schema-limited collection, secret scan, no raw service environment | Stop and quarantine on any exposure |
| Benchmark contamination or cherry-picking | Medium / medium | Warm-up plus five repetitions, medians/spread/raw samples, cold-cache control, pre/post controls | Auditor signs causal conclusions |
| Backup/mirror collision | Medium / high | 00:30–02:00 only, verify schedules/checkpoints immediately before run, skip if completion/rollback cannot fit | No overlap accepted |
| Storage or memory exhaustion | Medium / high | Preflight disk/RAM/VRAM headroom, bounded artifacts, no host spill, cleanup only after evidence acceptance | Stop before unsafe headroom |
| Upstream experimental regressions | Medium / high | Record exact revision, applicability, known defects and rollback; tiny-model enumeration before target model | Experimental work remains isolated |

No irreversible operation is required for Phase 0 or Phase 1. The project adds
no authentication, firewall, DNS, public exposure or external data service.
Expected users affected by later tests are Aster users and dependent local
services; interruption is detected by service health, authenticated synthetic
generation and dependent-workflow checks.

## Proposed Stream M authorization envelope

Pre-agreed now under the repository standard: non-secret read-only LAN checks,
primary-source research, local documentation, synthetic fixtures, harness code,
local tests and local commits.

Every state-changing host/guest command or external write requires Jason's
immediate approval with exact target, change, effect, validation and rollback.
This includes installing packages, starting/stopping services, executing a
production GPU benchmark that materially loads the shared service, creating a
scheduler on a lab system, changing firmware/BIOS/boot state and pushing Git.

An optional future Stream A envelope may cover only enumerated non-firmware,
reversible Vulkan experiments after the Phase 1 harness and rollback have been
reviewed. Firmware, BIOS, bootloader, reboot, GPU reset, production promotion
and remote Git writes remain immediate-approval operations even under that
envelope.

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
- [ ] Capture a fresh immutable control with the Phase 1 harness.

Gate: an independent reader can reproduce the control and restore the accepted
production service.

### M1 — Baseline and instrumentation

- [x] Implement schema-validated environment and result capture.
- [x] Add synthetic pp512, pp4096 and tg128 tests at context positions 0, 4K
  and 8K where supported, with warm-up, five repetitions and pre/post controls.
- [ ] Add cold-prefill isolation, prompt-cache state and CPU-fallback checks.
- [ ] Add GPU frequency, temperature, power, VRAM/RAM, CPU/affinity and bounded
  sanitized kernel-log capture where supported.
- [x] Add real Aster conversation, persona, read-only tool, grounded retrieval,
  2K and 8K fixtures with TTFT, completion and correctness assertions.
- [ ] Characterize variance and quantitatively explain the synthetic/real gap.

Gate: a repeatable baseline, known variance, verified GPU residency and a tested
rollback invocation.

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
- [ ] Analyze SR-IOV/VF reservations and current `xe` BAR-resize behavior.
- [ ] Build a safe decision record for `pci=realloc=on`, Dell A34 and attended
  recovery; do not deploy from the analysis alone.
- [ ] If a stable larger BAR is separately approved and proven, enumerate Level
  Zero with a tiny workload before SYCL/OpenVINO or the target model.
- [ ] Recheck current B60/Qwen correctness, OOM and reset defects before trials.

Gate: a larger stable BAR with proven recovery, or defensible evidence that safe
software/configuration methods cannot provide one.

### M4 — Alternative runtime and model interface

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

- [ ] Promote atomically with accepted and last-known-good artifacts.
- [ ] Run Doctor, B60 validation, Aster curricula and dependent regressions.
- [ ] Prove rollback and observe the defined reset/OOM/device-loss soak.
- [ ] Add quiet drift/research monitoring and operator-grade runbook updates.
- [ ] Complete integration impacts and terminal close-out or durable waiting state.

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
or approach to the 02:00 restoration deadline. Do not auto-retry a potentially
destabilizing failure class.

### M0 accepted and rollback artifact inventory

Read-only inventory on 2026-09-25 established the following immutable anchors:

| Role | Path / version | SHA-256 or evidence |
|---|---|---|
| Accepted server | `/opt/llama.cpp-b11081/llama-server` | `47692a3806ad5615c218e347f3bd55870436f07117c041cea7bf880b3b978693` |
| Accepted server implementation | `/opt/llama.cpp-b11081/libllama-server-impl.so` | `b89200852d6f1cbf4c2f4764b19ce86bc316c41280798cab3dc0b2afded1985d` |
| Accepted Vulkan backend | `/opt/llama.cpp-b11081/libggml-vulkan.so` | `dfbfe66354e7b9f7a0236194d665874152983284315d6c4f76a36aaff96b0dc5` |
| Accepted unit | `/etc/systemd/system/aster-llama.service` | `7e3e2d9a4c7d861b18ad2c9c83dc294893ea81f295a25918f76fcf3e0f9c9013` |
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

## Close-out

Not started. The project is active for read-only discovery and local development
under Stream M. Production load, host/guest changes, scheduler deployment and
remote Git writes remain individually gated.
