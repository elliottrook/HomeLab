# Full-stop recovery drill — dependency tracker

**Owner:** Stream A for evidence and coordination; Local AI platform owner for
host release, lease and recovery. **Last reconciled:** 2026-10-19
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
now has matching source hashes and 14 passing focused synthetic tests. It
reports only a content-free failure phase and cannot recover the missing
October 17 archive results. Its later disabled installation is recorded below;
a new scan required separate authorization at that point. The paragraphs
below preserve the earlier failed and corrected
paths as provenance; their earlier “uninstalled” descriptions are historical,
not the current installed state.

**October 18 disabled diagnostic installation:** Jason approved the bounded
one-file replacement. The platform owner recorded the [host result](../../../services/local-ai-lease/F2-DIAGNOSTIC-DISABLED-INSTALL-RESULT-20261018.md)
at commit `5e049e0a`: the old guard is checkpointed, the installed diagnostic
guard and seven dependencies match pinned hashes and custody, and 14 target-Linux
synthetic tests pass. Stream A independently read the installed guard hash,
root:root `0644` mode, inactive/disabled timers and absence of lease/receipt.
No scan was invoked. This closes only the disabled diagnostic installation;
F2 is still FAILED/UNKNOWN.

Jason first approved one conditional October 19 scan, then explicitly approved
an **active daily schedule** for the bounded F2 read-only protocol. The
platform owner revised the [daily card](../../../services/local-ai-lease/F2-FRESH-CYCLE-SUPERVISED-SCAN-CARD-20261018.md)
at commit `42fa1308`. The existing Codex heartbeat is verified `ACTIVE` at
01:05 Vancouver daily. Each cycle requires fresh backup, TrueNAS, host,
lease, installed-hash and operator gates before at most one 01:10–01:19
invocation. The automation must pause after a complete three-row exit-zero
result or a drift, safety failure, uncertain postcheck or other review
condition. A scheduled wake-up does not prove the gates passed or that a scan
ran. The October 17 approval remains consumed. No F3 receipt, full-stop
drill or A1 action is included.

The [October 19 heartbeat](evidence/F2-window-missed-2026-10-19.md) arrived
at 01:06, but a complete preflight was not retained before the 01:20 start
cutoff. The next observed host clock was 03:45. No guard or archive scan ran;
the lease was `ready` and no scanner or F2 receipt remained. This cycle is
NO-GO/UNMEASURED, not an F2 pass or an archive failure. The daily protocol
still requires a fresh, supervised gate for each later cycle; it does not
authorize replay of October 19.

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
supervised F2 read-only scan for the October 17 backup cycle**. That approval
was consumed by the single guarded attempt described above. The guard returned
NO-GO without archive results; F2 remains open. The source-only fixed-phase
diagnostic at `codex/aster-lease-compat` commit `e5963762` passed 212 local
tests (four Mac root-custody skips) but is not installed and cannot diagnose
the October 17 failure after the fact. It grants no receipt, full-stop drill,
model call or service stop.
A later source-only projection correction on that branch at `1dd38c76`
rejects a child result labelled complete when its cycle, fixed archive name,
size, ctime or elapsed bound is inconsistent. The local suite passed 213
tests with four Mac root-custody skips. It is uninstalled, cannot explain the
October 17 NO-GO, and needs target-Linux review and a new exact release card
before any future host change.
The source checkpoint and live schedule-type assertions were clarified in
`62125a65`; the conditional stage/test/install wording is in `9f9ae8a9`.
The platform owner integrated the matching source locally at `1829271d`,
with its own full suite passing. Those source facts preceded the target-Linux
result above; none is an F2 timing result.
The disabled F3 producer received the same pre-start lease guard in local
source commit `4e16b964`, integrated by the platform owner as `f4b9da31`.
Its full local suite passed 177 tests with two macOS root-custody skips. The
F3 receipt CLI entrypoint exists on Proxmox but is not released or invoked;
the F2-installed archive producer is effect-disabled and cannot write a
receipt through the read-only observer. Read-only inventory found no current
archive-integrity or source-receipt file.
F3 remains open.
An offline F3 writer review at local `codex/aster-lease-compat` commit
`68ffacb7` (`services/local-ai-lease/F3-RECEIPT-WRITER-OFFLINE-REVIEW-20261016.md`)
found that the candidate
checked parent custody after writing through a predictable temporary name.
Its source-only correction checks custody before opening a unique temporary
file and passed 17 focused Mac tests with two root-custody skips. The platform
owner has the exact hashes for independent review. No target-Linux root proof,
effect-enabled release, receipt or F3 authorization follows from this change.
A subsequent source-only reader correction at `a8d0f380` bounds the opened
file and rejects malformed receipt shapes before candidate admission. Its
full offline suite passed 209 tests with two Mac root-custody skips; the
platform owner has the exact hashes for review. The later file hash supersedes
the writer-only hash as a future release candidate, but F3 remains HOLD.
The source-only target-Linux preflight card at lease-compatibility commit
`ca28466a` pins the observed installed and candidate hashes, rollback target,
and root-only test requirements. It identified two *known older* installed
source dependencies; neither is evidence of a host fault, but both must be
included in the actual installed-path compatibility proof. The card makes no
host change and does not authorize F3 release.

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
| F2 | **New-cycle read-only archive timing**, after successful 00:30 Proxmox job and 01:00 TrueNAS task 1 | Exact current-cycle 104/110/116 identities; three bounded `zstd -t` exit-0 results before the deadline, without competing work. Failure/unknown/partial is NO-GO. | [ ] **ARMED / OPEN** — the [October 20 exact-cycle activation](evidence/F2-exact-cycle-activation-2026-10-19.md) is installed: fixed non-recurring timers are enabled for 01:09 preparation and 01:10 final gate, while the old daily timers remain disabled. A one-occurrence 01:42 Codex observer can reconcile and clean up but cannot start or retry the scan. No scan result exists yet. October 19 was [missed without a scan](evidence/F2-window-missed-2026-10-19.md); October 17's [one approved guard attempt](evidence/F2-archive-guard-no-go-2026-10-17.md) returned `F2NoGo` without archive rows. Only three valid exit-zero rows and a clean October 20 postcheck can mark this gate done. |
| F3 | **Trusted retained-receipt release**, after F0/F1 and timing review | A separately reviewed, hash-pinned producer can write a root-owned mode-0600 receipt in a mode-0700 directory only after all fixed source, whole-job, task-1, archive identity/integrity and deadline checks pass. Partial/late scans leave no success receipt. Test the actual installed path and rollback; obtain bounded host-change approval. | [ ] **INSTALLED INACTIVE / BLOCKED** — the [12-file disabled installation](evidence/F3-disabled-receipt-writer-install-2026-10-19.md) is provenance-clean after an independent hash check caught and corrected a stale 11-file report. All clean committed source hashes equal the live files; 46 target-Linux tests and 336 local tests pass. Rollback is retained. The producer remains uncalled and no receipt exists. Effect-enabled use still requires a successful F2 result, fresh current-cycle evidence and separate approval. |
| F4 | **Fresh trusted receipt for the drill cycle**, after F3 and that cycle's backup/task 1 | Complete current-cycle receipt exists, is independently re-read and bound to the same archive identities; stale, replaced or incomplete files fail closed. | [ ] BLOCKED by F3 and next eligible backup cycle. No October 15 receipt exists. |
| F5 | **03:05 full preflight**, after F4 and 02:00/03:00 TrueNAS tasks | Fixed schedules and same-cycle job completions; exact LXC110 mirror; three consumers still running; no conflicting lease/job; pinned Qwen3.5-9B Q4_K_M, llama.cpp b11429 SYCL/Level Zero, GPU, unit and authentication state; News timer active/enabled and job idle. Save non-secret baseline for restoration. | [ ] BLOCKED by F4; must be observed afresh in the chosen cycle. |
| F6 | **Independent recovery armed**, after F5 and approved live card | Compatible watchdog and owner-liveness paths are verified active/enabled before any stop; exact state schema and constrained recovery executor match pins; the manual `acquire --light` remains legacy-schema and cannot be used with this watchdog even after its F2 lock update. Loss of watchdog/owner closes acquisition. | [ ] BLOCKED — both candidate timers inactive and live arming unapproved. Synthetic tests do not close this gate. |
| F7 | **Human live-drill approval**, after reviewable F3–F6 evidence and revised platform card | Jason approves one exact bounded drill, target services, stop condition, 03:30 hard release cutoff, 04:15 reconciliation reserve and rollback. No automatic approval from this tracker or scheduler. | [ ] NOT REQUESTED — platform run card remains NO-GO. |
| F8 | **Bounded full-stop acquisition/drill**, after F4–F7 in the same cycle | New source-bound controller persists watchdog-compatible state and lock before stopping only Aster Agent (104), llama.cpp (110) and Speech (116); records each effect and stable isolation. No model call, unrelated host change or News timer stop. | [ ] NOT SCHEDULED. |
| F9 | **Exact recovery and release**, after F8 | Independent recovery/restore proves original services plus exact model/backend, GPU, auth, unit, schedules, backup points, News and control plane. Release by 03:30 only on a complete match; otherwise retain lock, mark FAILED/UNKNOWN and use 03:30–04:15 for reconciliation. | [ ] NOT STARTED. |
| F10 | **Evidence close-out**, after F8/F9 | Keep immutable observations, unexpected effects, rollback result and decision record; update run card and this tracker; no A1 promotion inferred. | [ ] NOT STARTED. |
| A1 | **Aster full-path benchmark**, only on a later separate backup cycle | Its own application-only lease, source-bound A1 admission, sidecar/ingress/auth and recovery gates, frozen workload and independent scoring. A full-stop attempt makes A1 NO-GO for that same cycle even if recovery succeeds. | [ ] SEPARATE BLOCKED LANE — not part of F8/F9 approval. The [October 18 interface review](evidence/A1-admission-platform-interface-review-2026-10-18.md) records the corrected offline trigger/deadline contract and matched v2 client. Trusted source-specific host adapters, measured recovery/lag, installed-path proof and live drill remain open. |

## Critical path and failure reporting

F2 can be measured while F3 is engineered, but a read-only F2 result is not
retroactively a trusted F4 receipt. F3 must exist and be approved **before**
the backup cycle from which F4 is produced. F5–F9 are serial: they cannot be
compressed into the 03:10 window merely because the clock reaches it. The
October 17 guard failed without archive results, so **no October 17 drill or
A1 benchmark can follow from this cycle**. A later date depends on a diagnosed
and separately approved F2 attempt, F3 release, fresh-cycle evidence and live
approval; the prior 2–4 calendar-day estimate is not a reservation.

The earliest *conditional* sequence is: review the October 17 failure and any
source-only diagnostics, validate a revised guard on target Linux, and obtain
separate approval for a later one-cycle F2 scan. Only a complete bounded
three-archive result can advance F2. Review and release F3 after that timing
evidence, then produce a fresh F4 receipt from a **subsequent** backup cycle.
Consider F5–F9 in that same subsequent cycle only if their own run card and
Jason's live approval are ready. This is a dependency order, **not a booked
drill**. Another failed scan, late F3 release, backup mismatch or absent
approval pushes it later. Source code and a calendar slot are insufficient.

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
The October 17 one-shot scan result has been recorded and reported. Its
automation should be paused after that run; no repeat scan is authorized. The
platform owner must report any F3–F9 failure during its own reviewed
release/drill.
