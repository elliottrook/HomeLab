# Aster Lab Hours

> Authorization stream: **Stream A — Autonomous**
>
> Owner: Jason
>
> State: Exact-cycle night test passed; recurring operating release remains open
>
> Opened: 2026-10-28

## Objective

Provide a dependable, bounded handoff of the B60 AI stack to lab work and then
return it to the exact accepted Aster production configuration. Success is the
complete transaction: isolate every declared consumer, grant lab ownership,
run the fixed qualification workload, end lab ownership, restore the accepted
model/backend, restart production and scheduled workloads, and prove the
result.

This is operationally separate from the Full-Stop Recovery F2/F3/F4/F5
archive-evidence chain. A fresh completed Proxmox backup remains a recovery
prerequisite. Lab Hours does not require or create an F2 result, F3 retained
receipt, or F4/F5 admission record.

## Scope, authorization and exclusions

Jason approved Stream A execution, disruptive daytime qualification, and use
of the AI stack without repeated conversational approval except for a model
change or system restart. In scope are Proxmox and LXC 104/110/114/116; Aster
Agent and Speech; the accepted Qwen3.5-9B Q4_K_M llama.cpp/SYCL service; News
ingest/digest; EPUB narration worker/timer; the shared exclusion, owner scope,
guardian, fixed lab workload, exact restoration and bounded evidence.

Excluded are model/backend/credential/GPU-binding/firewall changes, VM105 use,
host or guest reboot, PCI rebind, fault injection, F2–F5 creation or promotion,
development-data promotion, deletion of attempt evidence/checkpoints, and
remote Git writes without immediate push approval. The project produces no
spoken output; restored consumers retain their existing voice contracts.

## Pre-start risk assessment

The expected interruption is deliberate: Aster, Speech, llama, News and EPUB
are unavailable during lab ownership. The main risk is incomplete restoration;
other risks are restoring a changed backend and colliding with backup/evidence
work or the long-running EPUB worker.

Controls are exact hashes before effects, a shared exclusion and durable
root-owned state, a separately armed guardian, fixed consumer inventory,
process-level quiescence checks, a fixed tool-free lab wrapper, exact model/
binary/unit/authentication restoration, direct current-cycle Proxmox backup
proof, no-retry exact-cycle runners, content-free failure evidence, and root
rollback checkpoints.

The EPUB queue is resumable. Lab Hours masks its timer, stops its static worker,
then restores the timer and restarts the worker without blocking production
recovery. Interrupted staging is recovered on the next attempt; the existing
ready generation is preserved.

Abort on installed drift, any lease/lock, competing backup/evidence work,
unknown B60 holder, failed isolation/workload, uncertain lab-process absence,
restoration/authentication failure, or owner/guardian uncertainty. Retain state
and evidence on uncertainty.

## Milestones

| Milestone | Gate | State |
|---|---|---|
| LH1 — direct transaction | Known production consumers isolate, fixed lab work runs, exact production restores. | Done twice, 2026-10-27. |
| LH2 — complete inventory | EPUB joins the drain and resumes without losing its durable queue. | Done twice with unchanged RC1c, 2026-10-28. |
| LH3 — host-owned night test | Date-specific runner completes independently of F2–F5 and retains actionable failure evidence. | **Done, 2026-10-29.** Complete in 220 seconds with three requests and production restored. |
| LH4 — recurring service | Reviewed schedule grants an actual reservation to the lab worker and restores production. | Open after LH3. |
| LH5 — graduation | Doctor/monitoring, runbook, owner-loss exercise and two scheduled passes. | Open. |

## Release candidate and evidence

RC1c is the October 27 full-inference candidate plus EPUB isolation. Two
October 28 attempts failed closed and restored production. The first proved a
static oneshot must be stopped rather than runtime-masked. The second showed
that an interrupted oneshot can enter `failed` after its process has gone.
RC1c accepts quiescence only with `MainPID=0` and zero/unset tasks and rejects
a failed EPUB worker after restoration.

The unchanged RC1c passed at 09:08 and 09:11 PDT. Both returned
`pilot-complete`, three requests and exit zero. Final checks found no lease,
state, lock, listener, lab process or guardian; production authentication
passed; Aster, llama, Speech and News were active; and EPUB resumed.

- [October 27 two-pass qualification](evidence/Full-inference-daytime-two-pass-qualification-2026-10-27.md)
- [October 28 RC1c qualification](evidence/Lab-Hours-RC1c-daytime-qualification-2026-10-28.md)
- [October 29 exact-cycle result](evidence/Lab-Hours-RC1c-exact-cycle-result-2026-10-29.md)

## Integration, recovery and resumability

- Backups: direct current-cycle Proxmox job/artifact proof is required; F2/F3
  are neither read nor written.
- News: Jason accepted catch-up; both timers are isolated and restored.
- EPUB: timer and worker are isolated/resumed; queue and ready generations are
  never deleted.
- Monitoring: graduation adds a Doctor check for retained lab state/lock,
  production restoration and stale attempts.
- NetBox/wiki: no topology change; publish the operating contract after LH3.
- Rollback: restore only pinned files from root checkpoints. Never delete state
  to report success; invoke exact rescue when ownership remains.

Platform source branch: `codex/aster-lab-hours-release-candidate`, based on
platform commit `200640648eca0d3485eae8e2cbfd2707a0e3c296`. Installed candidate:
`/usr/local/libexec/local-ai-lease/full-inference-pilot/`. Root evidence:
`/var/lib/local-ai-lab/lab-hours-attempts/`.

On resume, require no drain state/lock, operation lock, owner scope, listener
or guardian; verify production authentication, services/timers and EPUB. Never
reuse a spent exact-cycle evidence directory or retry a failed scheduled run.

## Immediate next action

Define LH4 as a reviewed recurring operating release: choose the reservation
cadence, retain the same collision and restoration checks, add a Doctor signal
for stale state or failed restoration, and require another complete scheduled
pass before graduation. The successful exact-cycle packet must not be rerun or
silently converted into a recurring timer.
