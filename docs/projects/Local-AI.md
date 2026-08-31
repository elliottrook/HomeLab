# Local AI Enhancement Project

> Status: B60 operational through GPU LXC 110; Hermes integration validated
>
> Project owner: Jason
>
> Last updated: 2026-08-30

## Purpose

Develop a private, locally operated assistant platform without making the
production HomeLab dependent on experimental AI workloads. Hermes Agent is the
assistant/orchestration layer and Ollama is the local inference backend.

## Inherited baseline

- [x] Hermes Agent runs in unprivileged LXC 104 at `192.168.70.10`.
- [x] Ollama runs with B60 Vulkan acceleration in unprivileged LXC 110 at
  `192.168.70.12`; VM 105 at `192.168.70.11` is retained stopped as rollback.
- [x] Both workloads are isolated on Lab VLAN 70 with narrowly scoped access.
- [x] Hermes reached Ollama through its OpenAI-compatible `/v1` API.
- [x] The `qwen3-64k:8b` profile ran with a 65,536-token context window.
- [x] Proxmox archives, checksum-verified Synology mirrors, encrypted off-site
  coverage and isolated restore tests exist for both guests.
- [x] Beszel monitors Hermes; Ollama's intended stopped state is represented by
  HomeLab Doctor.

## Scope

- Complete the planned CPU/RAM maintenance and re-establish a safe production
  capacity baseline.
- Evaluate and, only if suitable, install a dedicated Intel Arc Pro B60-class
  GPU for local inference.
- Measure useful model quality, latency, memory use and production impact.
- Implement the Hermes second-brain design with controlled source ingestion,
  provenance and recovery.
- Establish secure operations, monitoring and credential hygiene.

## Out of scope

- Making HomeLab operation dependent on Hermes or Ollama.
- Moving Frigate object detection away from its dedicated Coral TPU.
- Exposing the Ollama API publicly or placing it behind a browser authentication
  proxy.
- Purchasing a GPU before exact SKU, power, cooling and physical-fit checks pass.
- Treating generated answers as authoritative live infrastructure state.

## Milestone 1 — Host capacity and maintenance baseline

- [ ] Record the current Proxmox CPU, RAM, storage, PCIe/IOMMU and guest
  allocation baseline immediately before maintenance.
- [ ] Install the remaining approved CPU/RAM hardware and run firmware,
  `memtester`, EDAC and sustained-load validation.
- [ ] Reconfirm Frigate VM memory and all production guest allocations.
- [ ] Prove all production guests can run with acceptable memory headroom while
  Ollama remains stopped.
- [ ] Define the maximum safe Ollama allocation and the policy for starting it.
- [ ] Update hardware inventory, architecture, baseline and recovery notes.

Completion gate: the production estate is stable and adequately resourced before
GPU or model experiments resume.

## Milestone 2 — GPU selection and installation decision

- [ ] Confirm the exact Intel Arc Pro B60 product, VRAM and physical dimensions.
- [ ] Verify Dell Precision T5810 slot clearance, lane availability, airflow,
  PSU capacity and required power connectors.
- [x] Confirm host/kernel, IOMMU, VM firmware and Linux passthrough compatibility.
- [x] Record the PCI address, IOMMU group and passthrough design.
- [x] Create a current VM 105 recovery checkpoint and written rollback plan.
- [x] Make an explicit purchase/install decision.
- [x] Install the GPU, validate host isolation and pass it through
  only to VM 105.

Installed baseline (2026-08-30): ASRock Arc Pro B60 24 GB at `04:00.0`
(`8086:e211`, IOMMU group 56), with its unused audio function at `05:00.0`
(group 57). VM 105 uses OVMF/Q35 and `hostpci0: 04:00.0,pcie=1,rombar=0`.
Snapshot `pre-b60-passthrough` is the rollback point. The board-facing link is
PCIe 3.0 x8. The host could not enlarge the physical BAR beyond 256 MB; this is
an accepted diagnostic constraint until guest acceleration is measured.

Completion gate: the selected hardware is either safely operational in VM 105
or rejected with the reason recorded; production workloads remain unaffected.

## Milestone 3 — Accelerated inference validation

- [ ] Install the supported guest driver/runtime and verify Ollama uses the GPU.
- [ ] Capture idle and loaded power, temperature, VRAM, RAM and CPU use.
- [ ] Benchmark time-to-first-token and generation speed for the existing model.
- [ ] Test the required context size without OOM or guest instability.
- [ ] Test Hermes-to-Ollama operation and one concurrent production-load window.
- [ ] Select a bounded default model and retain CPU fallback instructions.
- [ ] Add useful health checks without duplicating Beszel or HomeLab Doctor.

Completion gate: the chosen model is repeatably useful, measured and safe to run
within the documented capacity envelope.

Current diagnostic result (2026-08-30): Ollama 0.32.14 starts with the passed
through device. Ubuntu was upgraded from the 6.8 GA kernel to the 7.0 HWE
kernel and the `xe` driver now binds `8086:e211`; current firmware and Mesa
Vulkan packages are installed, and Ollama already belongs to the `video` and
`render` groups. The remaining 256 MB physical BAR is not sufficient for this
configuration: `vulkaninfo` blocks in uninterruptible I/O and Ollama's GPU
discovery watchdog times out, then reports `size_vram: 0`. The custom 64K
profile also exhausted the temporary 8 GB guest allocation during its initial
CPU fallback, while the same model at a 2K context completed successfully.
Resolve host BAR allocation before selecting or pulling the replacement Hermes
model.

Host BAR remediation attempt (2026-08-30): Proxmox was configured with
`xe.max_vfs=0` and rebooted successfully. The driver switched out of SR-IOV PF
mode, but PCI firmware still reserved the B60's virtual-function BAR window and
the physical BAR remained 256 MB; the attempted 32 GB resize continued to fail
with `-ENOSPC`. The host reports a 46-bit DMAR address width, so the limiting
factor is the firmware-created PCI bridge aperture rather than IOMMU address
width. Full-device VFIO passthrough is blocked unless a suitable B60 AIB/IFWI
firmware makes the maximum physical BAR available. The production workaround
is unprivileged LXC 110, which receives only the host `xe` DRM devices.

LXC workaround validation (2026-08-30): Debian 13 LXC 110
(`ollama-gpu-pilot`, `192.168.70.12`) maps `/dev/dri/card0` and
`/dev/dri/renderD128`. Mesa Vulkan identifies the B60, and Ollama 0.33.2 reports
23.9 GiB total GPU memory. `gemma4:12b` is installed for multimodal testing.
Hermes uses `qwen3.5:9b`, whose native 262K context, tool calling, thinking and
vision capabilities satisfy Hermes's requirements; Ollama and Hermes are set
to a 65,536-token operating context. A real Hermes one-shot returned
`HERMES_GPU_OK`; the cold full-tool prompt took 88 seconds, including 48.7
seconds to prefill about 19K tokens at roughly 392 tokens/second. LXC 110 starts
automatically and snapshot `post-b60-hermes-20260830` is the recovery point.

Qwen3.8:27b quant evaluation (2026-08-30): tested whether a larger model could
replace `qwen3.5:9b` as the Hermes default. The registry build
`qwen3.8:27b` (Q4_K_M, 17 GB) ran 100% GPU at a reduced 32,768-token context
but spilled 18%/82% CPU/GPU at Hermes's actual 65,536-token context, dropping
generation to roughly 0.7 tokens/second — not viable at the context Hermes
needs. Pulling a smaller quant to reclaim VRAM headroom
(`bartowski/Qwen3.8-27B-GGUF:IQ4_XS`, 15.6 GB) failed repeatedly: Ollama's
registry client timed out fetching one specific blob from
`huggingface.co` (`context deadline exceeded` on every retry over several
minutes), which read as a stuck file on HF's side rather than a local network
or disk issue. `qwen3.8:27b` and `gemma4:12b` (unused since the multimodal
pilot) were removed along with the orphaned partial-pull blobs, taking LXC
110's disk from 81% to 16% used.

A second source, `unsloth/Qwen3.8-27B-GGUF`, avoided the stuck-blob problem
(different blobs, same underlying model) and surfaced a real distinction
between quant *format* and quant *size*: `UD-IQ4_XS` (14.3 GB) loaded 100% GPU
at 65,536 context but generated at only ~4 tokens/second regardless of prompt
size — consistent with llama.cpp's Vulkan backend lacking efficient compute
kernels for IQ-format quants, so the weights sit in VRAM without being
computed efficiently. `UD-Q4_K_S` (16 GB, a standard K-quant with mature
Vulkan support) also loaded 100% GPU at the full 65,536 context and performed
normally: 22.3 tokens/second prefill / 6.0 tokens/second decode on a short
prompt, scaling to 96.9 tokens/second prefill on a realistic ~15K-token
prompt (192.6 seconds wall time end-to-end). Measured against the same
short-prompt baseline, `qwen3.5:9b` does 38.6 tokens/second prefill / 16.7
tokens/second decode; against the real ~19K-token Hermes benchmark above
(392 tokens/second prefill, 88 seconds total), `UD-Q4_K_S` is roughly 4x
slower on the realistic workload that matters. Not fast enough to become the
default, but confirmed genuinely usable rather than broken.

`hf.co/unsloth/Qwen3.8-27B-GGUF:UD-Q4_K_S` was added to Hermes's `Local`
provider as a selectable model (`/home/hermes/.hermes/config.yaml`, backed up
before editing); `model.default` stays `qwen3.5:9b` and the stale
`gemma4:12b` entry was removed from the selectable list. `hermes-gateway`
was restarted to load the change. Unrelated to this work, that restart's log
surfaced two pre-existing issues worth a separate look: the gateway's API
server is network-accessible (`0.0.0.0`) with the unsandboxed local terminal
backend, and the BlueBubbles integration's Cloudflare tunnel hostname is no
longer resolving.

Sandbox note: `192.168.70.10` (Hermes), `192.168.70.12` (Ollama LXC 110) and
`192.168.50.10` (Proxmox, the only reachable path to `pct exec` into LXC 110)
were added to Claude Code's sandbox network allowlist
(`.claude/settings.json`) to support this work and were kept in place
afterward at Jason's direction.

## Milestone 4 — Hermes second brain

The detailed design and task list live in
[`docs/AI-Hermes-Second-Brain.md`](../AI-Hermes-Second-Brain.md).

- [ ] Confirm the installed Hermes version and exact Wiki paths/configuration.
- [ ] Define authoritative read-only sources and the initial Wiki taxonomy.
- [ ] Define the boundary between memory, Wiki knowledge, skills, `SOUL.md` and
  Git documentation.
- [ ] Pilot ingestion using non-sensitive HomeLab reference material.
- [ ] Validate answers against a fixed question set and require source/provenance
  visibility.
- [ ] Add Wiki/source data to the protected Hermes recovery set.
- [ ] Restore the knowledge set into an isolated validation guest.

Completion gate: Hermes provides demonstrably better, verifiable answers from
curated local sources and the knowledge set survives restore.

## Milestone 5 — Security, operations and hand-back

- [ ] Remove unused Hermes cloud-provider authentication remnants.
- [ ] Confirm tokens, provider state, conversations and private sources remain
  outside Git.
- [ ] Document start/stop, upgrade, failure and rollback procedures.
- [ ] Confirm backup, mirror, encrypted off-site and restore coverage after the
  final configuration changes.
- [ ] Run HomeLab Doctor and review Beszel during a bounded observation period.
- [ ] Update the dashboard only with links or metrics that are genuinely usable.
- [ ] Record final resource limits, accepted risks and the operational owner.

## Definition of done

The Local AI project is complete when the hardware decision is resolved, the
selected inference path is stable and measured, Hermes has a recoverable curated
knowledge system, secrets remain protected, monitoring and rollback are proven,
and production HomeLab operation remains independent of the AI stack.

## Evidence log

| Date | Milestone | Evidence | Result |
|---|---|---|---|
| 2026-08-20 | Pilot recovery | Isolated LXC 972 and VM 973 restores | Passed |
| 2026-08-24 | Project split | Initial-build tasks moved to this enhancement document | Complete |
| 2026-08-30 | B60 installation | Proxmox detected `8086:e211`; functions isolated in IOMMU groups 56/57; VM 105 snapshot created and GPU-only passthrough booted | Passthrough passed; guest Vulkan pending |
| 2026-08-30 | B60 BAR remediation | Disabled unused `xe` SR-IOV PF mode and rebooted; physical BAR remained 256 MB and Vulkan still requires a different deployment path or AIB firmware | VFIO path blocked by firmware aperture |
| 2026-08-30 | B60 LXC production path | LXC 110 mapped host DRM devices; Ollama Vulkan detected 23.9 GiB; Hermes returned `HERMES_GPU_OK` using `qwen3.5:9b` at 64K context | Passed |
| 2026-08-30 | Qwen3.8:27b quant evaluation | `qwen3.8:27b` (Q4_K_M) CPU-spilled at 65,536 context; `bartowski` IQ4_XS blocked by a stuck HF blob; `unsloth` UD-IQ4_XS loaded 100% GPU but ran ~4 tok/s (Vulkan IQ-kernel limitation); `unsloth` UD-Q4_K_S loaded 100% GPU and ran correctly, ~4x slower than `qwen3.5:9b` on a realistic ~15K-token prompt | UD-Q4_K_S added to Hermes as a selectable model; `qwen3.5:9b` stays default |
