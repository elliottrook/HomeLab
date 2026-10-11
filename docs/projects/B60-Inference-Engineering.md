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
- [ ] If a stable larger BAR is separately approved and proven, enumerate Level
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
