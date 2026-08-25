# Local AI Enhancement Project

> Status: Pilot complete; hardware-backed expansion proposed
>
> Project owner: Jason
>
> Last updated: 2026-08-24

## Purpose

Develop a private, locally operated assistant platform without making the
production HomeLab dependent on experimental AI workloads. Hermes Agent is the
assistant/orchestration layer and Ollama is the local inference backend.

## Inherited baseline

- [x] Hermes Agent runs in unprivileged LXC 104 at `192.168.70.10`.
- [x] Ollama runs in VM 105 at `192.168.70.11` and is normally stopped when its
  memory allocation would interfere with production guests.
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
- [ ] Confirm host/kernel, IOMMU, VM firmware and Linux driver compatibility.
- [ ] Record the proposed PCI address, IOMMU group and passthrough design.
- [ ] Create a current VM 105 recovery checkpoint and written rollback plan.
- [ ] Make an explicit purchase/install or reject/defer decision.
- [ ] If approved, install the GPU, validate host isolation and pass it through
  only to VM 105.

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
