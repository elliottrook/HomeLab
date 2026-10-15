# Full-stop recovery drill — dependency tracker

**Owner:** Stream A for evidence and coordination; Local AI platform owner for
host release, lease and recovery. **Last reconciled:** 2026-10-15, 15:40
America/Vancouver. **Overall decision: NO-GO.** This tracker is the human
status page. The platform-owned
`services/local-ai-lease/FULL-STOP-RECOVERY-DRILL-RUN-CARD.md` is the executable
run card. Neither a checked box nor a calendar time authorizes production
effects; the separately approved live card and deterministic host gates do.

## What will happen automatically

The existing `aster-archive-integrity-timing-check` heartbeat is active for
**October 16 at 01:10 Vancouver**. It is a conditional, read-only scan of
that cycle's 104/110/116 backup archives. It must skip if the backup/task-1
chain, host load or lease checks fail, and must end by its bounded deadline.
It cannot save the trusted root-owned admission receipt. It cannot activate
the watchdog, stop a service, acquire a lease, run A1 or launch this drill.
There is **no scheduled 03:10 live drill**; the old 03:05 and 03:40 one-time
checks are paused. A schedule entry is not evidence that its preconditions
passed or that a scan finished.

## Dependency chain and live status

`[x]` means the named evidence was observed. `[ ]` means open. If an attempted
gate fails, replace its status with `FAILED` and record the reason, cycle,
evidence location, consequence and recovery action. Do not mark a later gate
complete from an earlier day's observation. Each fresh-cycle gate expires at
the end of that backup cycle.

| ID | Gate and dependency | Required evidence / pass condition | Status at checkpoint |
|---|---|---|---|
| F0 | **Pinned inactive compatibility source** | Source pins, seven-file rollback checkpoint, 12 installed modules and two heartbeat units match reviewed bytes; no lease/lock or production change. | [x] DONE — `services/local-ai-lease/FULL-STOP-COMPATIBILITY-DISABLED-INSTALL-RESULT-20261015.md` on platform branch; separate local `codex/aster-lease-compat` branch. |
| F1 | **Target-Linux synthetic compatibility**, after F0 | Installed-path imports, admission-record round-trip, old-dependency compatibility, watchdog/recovery and archive tests; timers stay inactive. | [x] DONE — same result; synthetic tests only. |
| F2 | **New-cycle read-only archive timing**, after successful 00:30 Proxmox job and 01:00 TrueNAS task 1 | Exact current-cycle 104/110/116 identities; three bounded `zstd -t` exit-0 results before the deadline, without competing work. Failure/unknown/partial is NO-GO. | [ ] WAITING — conditional October 16 01:10 check scheduled. October 15 was partial; 110 exit unknown and 116 untested. |
| F3 | **Trusted retained-receipt release**, after F0/F1 and timing review | A separately reviewed, hash-pinned producer can write a root-owned mode-0600 receipt in a mode-0700 directory only after all fixed source, whole-job, task-1, archive identity/integrity and deadline checks pass. Partial/late scans leave no success receipt. Test the actual installed path and rollback; obtain bounded host-change approval. | [ ] BLOCKED — installed producer CLI remains hard-disabled. F2 alone cannot satisfy F3. |
| F4 | **Fresh trusted receipt for the drill cycle**, after F3 and that cycle's backup/task 1 | Complete current-cycle receipt exists, is independently re-read and bound to the same archive identities; stale, replaced or incomplete files fail closed. | [ ] BLOCKED by F3 and next eligible backup cycle. No October 15 receipt exists. |
| F5 | **03:05 full preflight**, after F4 and 02:00/03:00 TrueNAS tasks | Fixed schedules and same-cycle job completions; exact LXC110 mirror; three consumers still running; no conflicting lease/job; pinned Qwen3.5-9B Q4_K_M, llama.cpp b11429 SYCL/Level Zero, GPU, unit and authentication state; News timer active/enabled and job idle. Save non-secret baseline for restoration. | [ ] BLOCKED by F4; must be observed afresh in the chosen cycle. |
| F6 | **Independent recovery armed**, after F5 and approved live card | Compatible watchdog and owner-liveness paths are verified active/enabled before any stop; exact state schema and constrained recovery executor match pins; old manual `acquire --light` cannot be used with this watchdog. Loss of watchdog/owner closes acquisition. | [ ] BLOCKED — both candidate timers inactive and live arming unapproved. Synthetic tests do not close this gate. |
| F7 | **Human live-drill approval**, after reviewable F3–F6 evidence and revised platform card | Jason approves one exact bounded drill, target services, stop condition, 03:30 hard release cutoff, 04:15 reconciliation reserve and rollback. No automatic approval from this tracker or scheduler. | [ ] NOT REQUESTED — platform run card remains NO-GO. |
| F8 | **Bounded full-stop acquisition/drill**, after F4–F7 in the same cycle | New source-bound controller persists watchdog-compatible state and lock before stopping only Aster Agent (104), llama.cpp (110) and Speech (116); records each effect and stable isolation. No model call, unrelated host change or News timer stop. | [ ] NOT SCHEDULED. |
| F9 | **Exact recovery and release**, after F8 | Independent recovery/restore proves original services plus exact model/backend, GPU, auth, unit, schedules, backup points, News and control plane. Release by 03:30 only on a complete match; otherwise retain lock, mark FAILED/UNKNOWN and use 03:30–04:15 for reconciliation. | [ ] NOT STARTED. |
| F10 | **Evidence close-out**, after F8/F9 | Keep immutable observations, unexpected effects, rollback result and decision record; update run card and this tracker; no A1 promotion inferred. | [ ] NOT STARTED. |
| A1 | **Aster full-path benchmark**, only on a later separate backup cycle | Its own application-only lease, source-bound A1 admission, sidecar/ingress/auth and recovery gates, frozen workload and independent scoring. A full-stop attempt makes A1 NO-GO for that same cycle even if recovery succeeds. | [ ] SEPARATE BLOCKED LANE — not part of F8/F9 approval. |

## Critical path and failure reporting

F2 can be measured while F3 is engineered, but a read-only F2 result is not
retroactively a trusted F4 receipt. F3 must exist and be approved **before**
the backup cycle from which F4 is produced. F5–F9 are serial: they cannot be
compressed into the 03:10 window merely because the clock reaches it. The
earliest credible drill cycle is therefore **not October 16 under the current
configuration**. A later date depends on F3, fresh-cycle success and approval;
the prior 2–4 calendar-day estimate is conditional, not a reservation.

For any failed or uncertain dependency, the observing Stream A or platform
agent must promptly tell Jason in this chat, in ordinary language:

1. **What failed or is unknown** (gate ID and cycle), without secrets or raw
   private logs.
2. **What will not run** as a result (scan, drill, A1), and whether production
   remains normal or recovery is in progress.
3. **What evidence was retained**, the safe next action, owner and revised
   earliest eligible cycle. Never silently retry an uncertain effect.

Update the checkbox and a dated evidence link in this file only after direct
observation or a pinned source/test result. A scheduler `SUCCESS`, file
presence, synthetic test or another agent's proposal cannot substitute for a
fresh receipt or actual post-recovery checks. Commit scoped status changes
locally; remote publication follows the repository's per-push approval rule.
The read-only October 16 automation must record and report any failed scan
prerequisite or incomplete result and pause after that one run. The platform
owner must report any F3–F9 failure during its own reviewed release/drill.
