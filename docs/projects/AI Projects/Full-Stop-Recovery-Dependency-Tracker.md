# Full-stop recovery drill — dependency tracker

**Owner:** Stream A for evidence and coordination; Local AI platform owner for
host release, lease and recovery. **Last reconciled:** 2026-10-18
America/Vancouver. **Overall decision: NO-GO.** This tracker is the human
status page. The platform-owned
`services/local-ai-lease/FULL-STOP-RECOVERY-DRILL-RUN-CARD.md` is the executable
run card. Neither a checked box nor a calendar time authorizes production
effects; the separately approved live card and deterministic host gates do.

The [October 15 23:29 pre-cycle read-only check](evidence/Full-stop-precycle-read-only-2026-10-15.md)
found a ready lease state, disabled/inactive independent watchdog and the
unchanged disabled producer pin. It does not change any gate status.

The platform owner corrected the stale pre-install wording in the execution
card in local commit `8f598f7b`. It now distinguishes the installed inactive
controller and retained adapter from the still-uninstalled receipt CLI, while
keeping the old manual controller separate. The documentation mismatch is
resolved; this is not an F3/F6/F7 pass or live approval. The owner also
integrated the missed-window record and the uninstalled read-only observer
source in local commits `11764480` and `b254bd02`.

## Current next action and historical sequence

The one-time October 17 supervised F2 guard was invoked once after the
current-cycle backup and task-1 pull passed preflight. It returned `F2NoGo`
without per-archive results; the [dated record](evidence/F2-archive-guard-no-go-2026-10-17.md)
marks this cycle FAILED/UNKNOWN and prohibits a retry under the consumed
approval. Production and schedules remained normal in the postcheck. No
receipt or drill is scheduled. The [bounded diagnostic plan](evidence/F2-no-go-diagnostic-plan-2026-10-17.md)
separates offline reproduction from any later one-cycle scan approval; it does
not change F2 status. A [reviewed disabled diagnostic candidate](evidence/F2-diagnostic-candidate-independent-review-2026-10-18.md)
now has matching source hashes and 14 passing focused synthetic tests. It is
not installed and reports only a content-free failure phase. It cannot recover
the missing October 17 archive results; a bounded target-Linux installation
and a later one-cycle scan each need their own authorization. The paragraphs
below preserve the earlier failed and corrected
paths as provenance; their earlier “uninstalled” descriptions are historical,
not the current installed state.

A source-only follow-up candidate at local `b9094cc6` adds a fixed,
content-free failure phase (`preflight`, `observer`, or `result`) for a future
review. It is not installed and was not used to retry October 17. The current
checkout passes 208 local tests with four expected macOS root-custody skips;
target-Linux proof, a new pinned card and fresh approvals remain required.

A later source-only projection review at local `588be180` binds future
complete results to the cycle date and fixed archive names, and rejects
impossible size, ctime and elapsed-time values. The current checkout passes
209 tests with four expected macOS root-custody skips. This candidate remains
uninstalled and does not explain the October 17 failure.

Later read-only [post-event observations](evidence/F2-post-event-observations-2026-10-17.md)
confirmed the lease remained ready, the installed producer matched all three
fixed guest-log final lines, and the fixed scheduler filter showed one backup
start and one success with no task error. They narrow source-shape concerns
but do not reconstruct the failed 01:10 instant or prove a scan ran.

The October 16 01:10 read-only archive heartbeat triggered, but no complete
three-archive result was retained by the time Stream A resumed after the
start cutoff. It is now **paused**; see the [dated F2 record](evidence/Full-stop-archive-window-missed-2026-10-16.md).
An uninstalled, source-only read-only observer candidate on
`codex/aster-lease-compat` at `c32db365` passed offline tests and now refuses
both whole-host and application-B60 lease state/locks at startup. The platform
owner integrated the guard locally at `26ab170b`; it does not
retroactively supply F2 evidence or authorize a new host schedule.
It cannot save the trusted root-owned admission receipt. No evidence was
retained of a watchdog activation, service stop, lease, A1 run or drill.
The source guard does not prevent a competing lease or backup from starting
mid-scan; a reviewed host-side exclusion, load/competing-job check and outer
process deadline still gate unattended use.

An October 16 read-only Proxmox installation preflight found that the first
common-exclusion card misclassified the installed files: three modules exist
and three are absent. The platform owner retained the failed preflight in
local commit `7e039c6d` without changing the host. Stream A corrected the
source card at `a0438d81`; the platform owner integrated it locally at
`574d7bde`. It now pins three observed replacement hashes and three add-only
absences. This resolves the **card discrepancy only**; a fresh check and
separate disabled-install authorization are still required, and F2/F3/F6
remain open.

Jason approved that six-path disabled install, but the [target-Linux import
failed and the install was rolled back](evidence/Common-host-exclusion-disabled-install-rollback-2026-10-16.md).
The application controller's real root is `/usr/local/libexec/aster-a1`, not
the whole-host lease directory. Pre-install hashes, production service state,
timers and backup schedule were restored/verified. Jason subsequently approved
the corrected two-root, seven-path card. Its [target-Linux result](evidence/Common-host-exclusion-disabled-install-v2-2026-10-16.md)
at local `codex/aster-lease-compat` commit `048adc01` records matching
installed hashes, both module-root imports, cross-process exclusion, 51/51
synthetic host tests with one repository-unit-file test excluded, and unchanged
inactive timers, services and schedules. This is a **disabled installation**;
it does not admit an unattended F2 scan or advance F3/F6. The October 17 F2
scan remains unadmitted pending the [separately reviewed timing/schedule
guard](evidence/F2-archive-timing-admission-gap-2026-10-16.md).
The source-only F2 guard packet was revised at local
`codex/aster-lease-compat` commit `339b554e`. A read-only TrueNAS query
confirmed that task 1/2/3 `enabled` values are booleans and schedule
hour/minute values are strings. The disabled installed producer expected
numbers, so it cannot admit the observed live configuration. The packet now
pins a corrected producer as a **third** proposed host path, alongside the
lock-compatible old manual controller and one-shot read-only guard. It also
pins all observer imports, rejects bool-as-zero scan exits and handles the
Linux 15-byte process name for the Proxmox backup client. The full local suite
passed 206 tests with two macOS root-custody skips. The first scan is planned
as a **supervised one-cycle** action because backup and pull jobs do not share
the advisory lease lock. The platform owner integrated the source and Jason
separately approved the bounded stage/test/conditional disabled installation.
The result on `codex/aster-lease-compat` at
`services/local-ai-lease/F2-DISABLED-INSTALL-RESULT-20261016.md` records 23/23
F2 and 4/4 installer synthetic tests on target Linux, three exact installed
hashes, two old-file checkpoints, inactive timers, running guests/News timers,
and no lease, receipt or scan. Jason separately approved **one conditional,
supervised F2 read-only scan for the October 17 backup cycle**. The active
one-time Stream A heartbeat will perform a 01:05 preflight; a scan may start
only before 01:20 if the actual 00:30/01:00 jobs succeeded, the exact
104/110/116 identities and installed pins match, the host is quiet, and no
manual backup/pull/lease competes. It must stop by the earlier of 20 minutes
or 01:40 Vancouver and skip on any failed, late or uncertain gate. This is no
F2 timing result yet: F2 remains NO-GO until all three tests exit 0 within
the bound. It grants no receipt, full-stop drill, model call or service stop.
The source checkpoint and live schedule-type assertions were clarified in
`62125a65`; the conditional stage/test/install wording is in `9f9ae8a9`.
The platform owner integrated the matching source locally at `1829271d`,
with its own full suite passing. Those source facts preceded the target-Linux
result above; none is an F2 timing result.
The disabled F3 producer received the same pre-start lease guard in local
source commit `4e16b964`, integrated by the platform owner as `f4b9da31`.
Its full local suite passed 177 tests with two macOS root-custody skips. The
F3 receipt CLI is still uninstalled/disabled; the F2-installed producer is
effect-disabled and cannot write a receipt through the read-only observer.
F3 remains open.

The subsequent source-only F3 custody-test update is integrated locally in
`511123a4`. It adds explicit opened-file symlink, hardlink, wrong-mode,
oversize and unsafe-parent checks; the complete local suite now passes 207
tests with four expected macOS root-only skips. This strengthens the
preflight candidate but is not target-Linux root proof and does not authorize
installation or receipt production.

Review of the corrected install's recovery helper found that its first
version could not roll back an interruption partway through the seven atomic
file writes. The source-only replacement at local lease-compatibility commit
`22d80549` now accepts exactly the pinned old/new states or an absent add
path. Disposable-directory tests pass for all eight interruption points,
reject symlinks and drift, and restore all four originals. The platform owner
has the commit for independent review. This improves the rollback candidate;
it does **not** prove target-Linux behavior, authorize the seven-path install,
or advance F2/F3/F6.

A later source-only common-exclusion candidate is documented at
`services/local-ai-lease/COMMON-HOST-EXCLUSION-OFFLINE-CANDIDATE-20261016.md`
on local `codex/aster-lease-compat` commit `a38da489`, integrated by the
platform owner locally as `6fe98336`, holds one advisory
directory lock through an archive scan or receipt write and through either
candidate lease's state creation. Its full offline suite passed 188 tests
with two macOS root-custody skips. It is **not installed** and does not
advance F2 or F3. Target-Linux proof, backup/load exclusion, outer process
deadline and the old manual controller's bypass were review blockers at that
checkpoint; the later disabled F2 install above addresses those source paths
without arming the F3/F6 release.
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
| F2 | **New-cycle read-only archive timing**, after successful 00:30 Proxmox job and 01:00 TrueNAS task 1 | Exact current-cycle 104/110/116 identities; three bounded `zstd -t` exit-0 results before the deadline, without competing work. Failure/unknown/partial is NO-GO. | [ ] **FAILED/UNKNOWN, October 17** — [one approved guard attempt](evidence/F2-archive-guard-no-go-2026-10-17.md) returned `F2NoGo` without archive rows despite passing observable backup/task-1 preflight. No retry this cycle. October 16 was UNKNOWN/NO-GO after the [missed window](evidence/Full-stop-archive-window-missed-2026-10-16.md); October 15 was partial. A future attempt needs a revised card and approval. |
| F3 | **Trusted retained-receipt release**, after F0/F1 and timing review | A separately reviewed, hash-pinned producer can write a root-owned mode-0600 receipt in a mode-0700 directory only after all fixed source, whole-job, task-1, archive identity/integrity and deadline checks pass. Partial/late scans leave no success receipt. Test the actual installed path and rollback; obtain bounded host-change approval. | [ ] BLOCKED — the receipt CLI entrypoint and an older receipt-boundary file exist on Proxmox, but the F3 path is not released or invoked. The writer/reader candidate through `a8d0f380` needs target-Linux root proof and a complete effect-enabled release review. The later source-only writer hardening and custody tests remain local-only. The corrected archive producer is installed only for read-only F2 observation; no trusted receipt was produced. F2 alone cannot satisfy F3. |
| F4 | **Fresh trusted receipt for the drill cycle**, after F3 and that cycle's backup/task 1 | Complete current-cycle receipt exists, is independently re-read and bound to the same archive identities; stale, replaced or incomplete files fail closed. | [ ] BLOCKED by F3 and next eligible backup cycle. No October 15 receipt exists. |
| F5 | **03:05 full preflight**, after F4 and 02:00/03:00 TrueNAS tasks | Fixed schedules and same-cycle job completions; exact LXC110 mirror; three consumers still running; no conflicting lease/job; pinned Qwen3.5-9B Q4_K_M, llama.cpp b11429 SYCL/Level Zero, GPU, unit and authentication state; News timer active/enabled and job idle. Save non-secret baseline for restoration. | [ ] BLOCKED by F4; must be observed afresh in the chosen cycle. |
| F6 | **Independent recovery armed**, after F5 and approved live card | Compatible watchdog and owner-liveness paths are verified active/enabled before any stop; exact state schema and constrained recovery executor match pins; the manual `acquire --light` remains legacy-schema and cannot be used with this watchdog even after its F2 lock update. Loss of watchdog/owner closes acquisition. | [ ] BLOCKED — both candidate timers inactive and live arming unapproved. Synthetic tests do not close this gate. |
| F7 | **Human live-drill approval**, after reviewable F3–F6 evidence and revised platform card | Jason approves one exact bounded drill, target services, stop condition, 03:30 hard release cutoff, 04:15 reconciliation reserve and rollback. No automatic approval from this tracker or scheduler. | [ ] NOT REQUESTED — platform run card remains NO-GO. |
| F8 | **Bounded full-stop acquisition/drill**, after F4–F7 in the same cycle | New source-bound controller persists watchdog-compatible state and lock before stopping only Aster Agent (104), llama.cpp (110) and Speech (116); records each effect and stable isolation. No model call, unrelated host change or News timer stop. | [ ] NOT SCHEDULED. |
| F9 | **Exact recovery and release**, after F8 | Independent recovery/restore proves original services plus exact model/backend, GPU, auth, unit, schedules, backup points, News and control plane. Release by 03:30 only on a complete match; otherwise retain lock, mark FAILED/UNKNOWN and use 03:30–04:15 for reconciliation. | [ ] NOT STARTED. |
| F10 | **Evidence close-out**, after F8/F9 | Keep immutable observations, unexpected effects, rollback result and decision record; update run card and this tracker; no A1 promotion inferred. | [ ] NOT STARTED. |
| A1 | **Aster full-path benchmark**, only on a later separate backup cycle | Its own application-only lease, source-bound A1 admission, sidecar/ingress/auth and recovery gates, frozen workload and independent scoring. A full-stop attempt makes A1 NO-GO for that same cycle even if recovery succeeds. | [ ] SEPARATE BLOCKED LANE — not part of F8/F9 approval. The [October 18 interface review](evidence/A1-admission-platform-interface-review-2026-10-18.md) identifies a trigger-versus-hard-deadline naming mismatch and missing source-bound/measurement proof. |

The B60 peer's offline watchdog timing proposal requires at least 15 minutes
for restoration plus a one-minute trigger-lag floor before 04:15. It is a
necessary refusal condition, not a measured recovery budget or live admission.
The corresponding A1 source/tests are present on the separate Stream A
lineage (`d5510733` through `ede3c268`) but are not integrated into this
platform branch. The candidate was therefore not cherry-picked blindly;
platform-owned measured restoration/lag evidence and an agreed authoritative
source-bound admission interface remain required.

The platform-side offline contract is now recorded in
`evidence/A1-source-bound-window-contract-2026-10-18.md`: the receipt and
admission projection keep `restore_start_epoch` (trigger) distinct from
`restore_deadline_epoch` (hard completion). The complete local suite passes
212 tests with four expected root-custody skips. A follow-up boundary review
also rejects admission at or after the recovery trigger. This closes only the
naming ambiguity and trigger-boundary gap; it does not provide live source authentication, measured recovery
budgets, target-Linux proof, or A1 authorization.

The next offline platform gate is the uninstalled source-bound pre-lease
candidate in `evidence/A1-source-bound-prelease-candidate-2026-10-18.md`.
It binds backup, TrueNAS, Mac-subset and runtime observations to one cycle and
rejects fabricated, stale, future or partial inputs. Its adapter interfaces
still require fixed root-owned host implementations and independent custody
proof before any entrypoint wiring or host approval.

The following custody boundary is recorded in
`evidence/A1-fixed-host-source-adapter-candidate-2026-10-18.md`: a future
producer must read fixed root-owned envelopes, validate private parent/file
custody, exact source/cycle/time and a pinned payload digest before setting
`verified=True`. The candidate is not wired or installed; synthetic
`verified` flags remain non-authoritative.

The next F2 diagnostic candidate is documented in
`services/local-ai-lease/F2-DIAGNOSTIC-DISABLED-RELEASE-CARD-20261018.md`.
It is source-only and HOLD: 14 focused synthetic tests pass, including one
denial per preflight gate with no child launch. Any target-Linux staging or
future scan requires new bounded approvals; the October 17 approval remains
consumed.

The approved disabled target-Linux replacement completed on the Proxmox host
root and is recorded in
`services/local-ai-lease/F2-DIAGNOSTIC-DISABLED-INSTALL-RESULT-20261018.md`.
The old guard is checkpointed for rollback, the new guard and all dependencies
match their pins, and the 14/14 synthetic suite passes. No scan was invoked;
F2 remains FAILED/UNKNOWN.

The approved bounded recurring daily scan protocol is documented in
`services/local-ai-lease/F2-FRESH-CYCLE-SUPERVISED-SCAN-CARD-20261018.md`.
It allows at most one supervised attempt per completed cycle, with fresh
gates every time, and pauses after the first complete three-row pass or any
drift/safety/review condition. It does not authorize automatic promotion or
any host action beyond the separately controlled read-only invocation.

The separate cooperative daytime lab-hours candidate and bounded first-pilot card
are documented in
`services/local-ai-lease/COOPERATIVE-LAB-HOURS-RUN-CARD-20261018.md`. It
preserves the accepted backend, quiesces only the fixed Aster/Speech/News
consumer set with runtime deny-new-start masks, and remains offline pending
source-bound host wiring and a separate daytime pilot approval. The offline
review is recorded in
`services/local-ai-lease/COOPERATIVE-LAB-HOURS-OFFLINE-REVIEW-20261018.md`.
The disabled source producer, exact Linux observer and rollback card are local
in Stream A commit `71d91314`; direct-client exclusivity remains an explicit
NO-GO until a reviewed MacBook identity and exact established-peer proof are
available.
The 30+15 isolation/recovery pilot is a prerequisite only; it does not close
the usable MacBook B60 workload milestone. That milestone remains blocked until
an actual client-admission enforcement boundary is independently verified. The
read-only path inventory is Mac/Companion → `aster.elliottrook.com` → LXC104
gateway → internal LXC110 backend; no static MacBook identity or direct-backend
ACL is established, and the pilot stops LXC104.
An alternative full-inference drain assessment and smaller 30+15 run card are
recorded in
`services/local-ai-lease/COOPERATIVE-FULL-INFERENCE-DRAIN-ASSESSMENT-20261018.md`
and `services/local-ai-lease/COOPERATIVE-FULL-INFERENCE-DRAIN-RUN-CARD-20261018.md`.
They use the historically verified MacBook→Proxmox administration path but
leave the first workload and fresh baseline checkpoint as explicit gates.
The fixed five-effect implementation and complete source/validator packet are
local in `3d976dd4`, with its
self-contained disabled-install card at
`services/local-ai-lease/COOPERATIVE-FULL-INFERENCE-DRAIN-DISABLED-INSTALL-CARD-20261018.md`.
The approved outage ceiling is up to 90 minutes, but the first pilot remains
the stricter 45-minute reservation (30 minutes lab plus 15 minutes restore),
and must fit before the next hourly News ingest with a five-minute margin as
well as before the 17:15 News run.

## Critical path and failure reporting

F2 can be measured while F3 is engineered, but a read-only F2 result is not
retroactively a trusted F4 receipt. F3 must exist and be approved **before**
the backup cycle from which F4 is produced. F5–F9 are serial: they cannot be
compressed into the 03:10 window merely because the clock reaches it. The
earliest credible drill cycle is therefore **not October 16 under the current
configuration**. A later date depends on F3, fresh-cycle success and approval;
the prior 2–4 calendar-day estimate is conditional, not a reservation.

With the October 16 timing result missing, the earliest *conditional* sequence
is: complete the source review, target-Linux synthetic proof and separate
three-path disabled installation before an eligible backup cycle; supervise
one approved F2 scan in that cycle; review and release
F3 only after that measurement; produce a fresh F4 receipt from a later
backup cycle; then consider F5–F9 on that cycle only if the run card
and Jason's live approval are ready. This is a dependency order, **not a booked
drill**. A failed scan, late F3 release, backup mismatch or absent approval
pushes it later. It cannot honestly be marked complete merely because a source
candidate or calendar slot exists.

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
