# B60 inference engineering

> Status: Active — Stream A; overnight llama.cpp v0.6.0 A/B armed for 2026-10-09 00:30 PDT
>
> Owner: Jason
>
> Started: 2026-10-08
>
> Authorization: Jason explicitly directed “run stream A and approve” on
> 2026-10-08 after receiving the exact 00:30–02:00 outage, test and rollback
> plan.

## Purpose and desired outcome

Find the fastest correct, stable and recoverable inference configuration for
the fixed Dell Precision T5810 and Intel Arc Pro B60 24 GB. Quantify the value
of software/runtime changes separately from the known 256 MB physical BAR
restriction. The first bounded experiment compares production llama.cpp b11081
with upstream v0.6.0 on the unchanged Vulkan/Mesa/model path.

## Current state and evidence

- Dell Precision T5810, Xeon E5-2698 v4, 80 GB ECC RAM.
- Arc Pro B60 is exposed by the host `xe` driver to unprivileged LXC 110.
- Physical BAR2 is 256 MB; Level Zero/SYCL/OpenVINO previously refused this
  device, while Vulkan works.
- Production is llama.cpp b11081 (`161755f29`), Mesa Vulkan 26.1.2,
  Qwen3.8-27B UD-IQ4_XS, all layers offloaded, 8,192 context, Q8 KV and flash
  attention.
- Accepted controlled result: pp4096 about 193.3 tok/s and tg128 about 11.85
  tok/s. Production was healthy when revalidated on 2026-10-08.
- LXC 110 had 22 GB free before staging. The accepted b11081 directory and
  systemd unit are retained as rollback.

## Scope and exclusions

Stream A permits side-by-side source/build staging, bounded benchmark scripts
and schedules, temporary interruption of only `aster-llama.service` between
00:30 and 02:00 America/Vancouver, synthetic tests, evidence capture and
automatic restoration/validation. Later low-risk Vulkan experiments require
the same one-variable, reversible pattern.

Excluded without a new explicit decision: BIOS/firmware flashing, boot or
kernel parameters, host reboot, BAR manipulation, Mesa/driver/package changes,
model replacement, VM/LXC topology changes, public/network/authentication
changes, destructive data operations and production promotion. Remote Git
push remains separately gated by `AGENTS.md`.

## Authority model and architecture

Live Proxmox/LXC state owns deployed facts. This repository owns the project,
test harness and accepted operational record. Upstream llama.cpp commits and
release tags own source provenance. LXC 110 remains the sole inference guest;
no new listener, credential or trust path is introduced.

## Privacy and security design

Tests use synthetic prompts and the existing local model only. Logs contain no
API key or private prompt. Evidence is root-owned in LXC 110 until sanitized.
The experiment does not read secret files; systemd performs the existing
warm-up using its existing protected environment.

## Pre-start risk assessment

The expected impact is a temporary loss of Aster inference during the window.
The main risks are a GPU reset, candidate crash/OOM, missed rollback, collision
with backup, or a misleading faster-but-incorrect result. Controls are a
single-GPU lock, hard deadline, shell trap that always restarts production,
matched flags/model, five repetitions, pre/post kernel-log checks, GPU
residency validation and final service health. Any reset, device loss, OOM,
CPU fallback, invalid result or approach to the deadline aborts promotion and
restores b11081. The test ends before the 02:30 Proxmox backup and 04:20 mirror.
No irreversible operation is required.

## Persistence and resume

The tracked runner is `scripts/b60-llama-v060-experiment.sh`. The installed
timer/service and root-only result directory in LXC 110 record scheduled,
running, complete or failed state. Resume by inspecting those records and this
evidence log; never infer success merely from timer execution.

## Milestones

- [x] M0 — reconcile repository/live state, authorization, rollback and window.
- [x] M1 — stage and identify the v0.6.0 candidate without changing production.
- [ ] M2 — run matched overnight synthetic A/B and restore production.
- [ ] M3 — analyze variance, correctness, GPU errors and real-workload value.
- [ ] M4 — promote only if repeated synthetic and real-workload gates pass.

## Validation and evaluation

Each binary runs pp512, pp4096 and tg128 with the identical model, `-ngl 999`,
four threads, batch 256, microbatch 128, flash attention on and Q8 KV. Each
test uses llama-bench warm-up plus five repetitions and JSON output. Record
binary version, SHA-256, model targets, kernel/Mesa identity, start/end time,
service state and relevant kernel errors. A result is not promotable until two
independent real Aster workflow passes also retain correctness.

## Observability and maintenance

Existing HomeLab Doctor `xe` reset monitoring remains authoritative. The
weekly `b60-inference-fix-watch` research monitor continues to identify new
test-ready fixes. An experiment failure is actionable; an unchanged research
poll is quiet.

## Backup, restore and rollback

The accepted b11081 binary directory and unit remain untouched. The runner's
EXIT trap restarts `aster-llama.service`; that unit's existing post-start
warm-up is the rollback validation. LXC 110 is covered by the established
02:30 archive and 04:20 mirror chain; the experiment finishes first and does
not modify model data.

## Integration impact

- HomeLab Doctor/monitoring: existing service and `xe` reset checks apply.
- Backup/recovery: existing LXC 110 coverage; no new authoritative data.
- NetBox, DNS, firewall, authentication, Homepage, diagrams: not applicable;
  topology and endpoints do not change.
- Wiki/Aster mirror: update only if a configuration is accepted.
- Operational reference: update after any production promotion.
- Repository/changelog: this project and its evidence are authoritative.
- Schedule: temporary bounded timer only; remove after evidence collection.
- Security inventory: no credential or permission changes.

## Graduation criteria

A candidate must produce a repeatable material gain, correct output, full GPU
residency, no new reset/OOM/device loss, safe memory headroom, two independent
real-workload passes, proven rollback and updated operational documentation.
Otherwise retain b11081 and record the negative result.

## Evidence log

| Date | Evidence | Result |
|---|---|---|
| 2026-10-08 | Read-only live check: LXC 110 running; `aster-llama.service` active on b11081 commit `161755f29`; B60 detected through Vulkan; 22 GB free; 02:30 backup schedule confirmed | Control and rollback path available |
| 2026-10-08 | Jason approved the presented 00:30–02:00 test as Stream A | Bounded implementation authorized |
| 2026-10-08 | Fetched annotated tag `v0.6.0` (tag object `69ecae9`, commit `d81235049384534c167caea52b85a694f6103d14`, upstream build 11429); built Vulkan candidate side-by-side with GCC 14.2; candidate enumerated the B60 and production remained active | M1 passed; exact source/build identity preserved |
| 2026-10-08 | Installed locked guest runner plus host kernel-log wrapper; transient timer normalized to 2026-10-09 00:30 PDT / 07:30 UTC with an 80-minute hard runtime and production restoration traps | M2 armed; expected finish before 02:00 and 02:30 backup |

## Close-out

Open. Do not promote v0.6.0 merely because the synthetic result is faster.
