# Full-stop recovery drill — dependency tracker

**Owner:** Stream A for evidence and coordination; Local AI platform owner for
host release, lease and recovery. **Last reconciled:** 2026-10-27
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

The [October 27 terminal result](evidence/F2-exact-cycle-no-go-2026-10-27.md)
is NO-GO. Preparation completed successfully, but the final observer exited
nonzero with bounded class `OBSERVER_EXIT_NONZERO`; the terminal state contains
zero archive rows. No F2 result can be accepted and F3 must skip without
writing a receipt. Both spent exact-date timers were removed after observation,
recurring F2 timers remain disabled, no scanner, lease, lock or receipt exists,
and production postchecks passed. The platform owner must diagnose the
observer's nonzero exit from the preserved content-free state and bounded
logs, add a more specific failure subphase if the existing evidence cannot
distinguish the cause, prove the correction offline and on target Linux, and
present a fresh reviewed cycle. October 27 must not be retried.

The platform source candidate at `be6cafa47d77668a69181a80018a755d6f740840`
now preserves the observer child's already bounded `preflight`, `observer` or
`result` phase instead of collapsing every nonzero child exit. Stream A's
[source review](evidence/F2-observer-exit-diagnostic-source-review-2026-10-27.md)
accepts the one-file correction and its conservative malformed-output fallback.
Jason approved the [inactive installation](evidence/F2-observer-exit-diagnostic-inactive-install-result-2026-10-27.md),
which now matches candidate `efe8bc99…87ec` under exact root custody. The first
incomplete test packet triggered verified rollback; the corrected packet then
passed 31/31 focused, 56/56 broader target-Linux and 4/4 direct installed-path
checks. This improves the next failure evidence but cannot recover the discarded
October 27 child phase. A fresh date-specific card and independent review are
the next gates; no timed cycle is scheduled.

The fresh October 28 candidate is committed at platform tip
`581c5ba93d65c4af3a143e845485ded44f6b654d`. Stream A's
[independent activation review](evidence/F2-exact-cycle-activation-review-2026-10-28.md)
matched both timer hashes and the installed diagnostic baseline, resolved the
calendars to 01:15/01:20 PDT, accepted only the two exact disabled historical
October 20 timer files, and found the new-cycle state, lease, locks and receipt
absent. Card tests passed 3/3 and the complete F2 suite passed 58 tests with one
expected non-root custody skip. Activation is now **HOLD**, rather than the
next action. The [repeated-failure analysis](evidence/F2-repeated-overnight-failure-analysis-and-daytime-mitigation-2026-10-27.md)
shows that successive overnight cycles have been exposing deterministic
installed-path integration defects one layer at a time. The new platform
daytime no-scan rehearsal initially passed 57/57 local tests, then reproduced
the real failure on target: the isolated child omitted `/usr/sbin` from PATH,
so Proxmox's `/usr/sbin/pvesm` could not resolve the first archive. Platform
commit `18c7198e` corrects that fixed path, updates the observer pin and passes
60 focused tests. The corrected staged rehearsal passed twice against all three
current archives without scanning them or writing a receipt. Card `07cedd0a`
freezes the three-file inactive replacement and rollback; successful install
and target proof are the next gate before another exact-date activation.
Runtime backup, pull, identity, load and quiet-host gates remain fresh and fail
closed.

The [installed correction and daytime real scan](evidence/F2-Proxmox-path-install-and-daytime-real-scan-2026-10-27.md)
now close the reproduced defect and expensive-probe uncertainty. The corrected
three-file baseline passed 60/60 target tests and two identical no-scan
rehearsals. A supervised real scan then verified VMIDs 104/110/116 at
19.312/337.578/42.015 seconds, all exit zero, with no receipt written. The
relay and narration workload were restored afterward and Aster Speech remained
active. The remaining F2 proof is only the actual 01:15/01:20 clock/timer path
against a fresh cycle; runtime gates remain fail closed.

The conditional [October 27 F3 conversion](evidence/F3-from-F2-no-go-2026-10-27.md)
then failed closed at its first mandatory gate. The reconciled F2 state is
`no_go` with zero archive rows rather than three independently validated
exit-zero rows, so the converter was not invoked and no retained receipt was
written. F3 and every later effect gate remain closed until a fresh F2 cycle
completes successfully.

The [October 26 terminal result](evidence/F2-exact-cycle-no-go-2026-10-26.md)
is NO-GO. The bounded state reached phase `final` with failure class
`OBSERVER_COMMUNICATION_FAILED` and no archive rows. Both date-specific timers
were removed after observation, recurring F2 timers remain disabled, no
scanner, lease, lock or receipt exists, and production postchecks passed. F3
must skip and write no receipt. The platform owner must diagnose the observer
communication path, preserve a more specific bounded failure, prove the
correction offline and on target Linux, and present a fresh reviewed cycle.

The subsequent [root-cause analysis](evidence/F2-observer-communication-root-cause-2026-10-26.md)
found a deterministic launcher API mismatch: `final()` defaulted to
`subprocess.run` but then called the Popen-only `communicate()` method on its
`CompletedProcess`. The observer child launched, but its result could not be
accepted. Synthetic success tests injected a Popen-like fake and therefore
missed the installed entrypoint. The correction needs a default-launcher
regression plus offline and target-Linux proof before a fresh cycle.

The platform owner has now committed the source-only correction as `d00073e5`.
Stream A's [independent review](evidence/F2-observer-launcher-source-fix-review-2026-10-26.md)
confirmed the real default `subprocess.Popen` path, retained deadline/process-
group behavior, the missing installed-entrypoint regression, 15/15 focused
tests and 50 passes with one expected skip across the 51-test broader F2 suite.
The source gap is closed; inactive installation and target-Linux proof remain
required before a fresh cycle.

The exact one-file inactive-install card is now committed at full platform
commit `a46b004f94fc7d4a3fd4038125615266b8c8b564`. Stream A's
[independent review](evidence/F2-observer-launcher-inactive-install-review-2026-10-26.md)
accepts its predecessor/candidate/state pins, target-Linux default-entrypoint
test, rollback and exclusions. One explicit host-change approval is now the
only gate to this inactive installation; no timer or retry is included.

Jason approved the card and the [inactive installation result](evidence/F2-observer-launcher-inactive-install-result-2026-10-26.md)
passed. One incomplete test archive triggered and verified rollback; the
corrected clean archive then passed the installed 15/15 and broader 50-pass,
one-expected-skip target-Linux suites. Installed hash/custody and the October
26 state digest match, timers remain disabled/inactive and production is
healthy. The next gate is a fresh date-specific card and separate activation
approval; no timed test is currently scheduled.

The fresh October 27 candidate is now committed at platform commit `9550e53a`.
Stream A's [independent activation review](evidence/F2-exact-cycle-activation-review-2026-10-27.md)
matched all source/timer pins, resolved the target calendars to 01:15/01:20
PDT, confirmed the new-cycle state absent and recurring timers disabled, and
passed 3/3 focused plus 53-pass/one-expected-skip broader tests. Exact activation
was approved and the [activation result](evidence/F2-exact-cycle-activation-result-2026-10-27.md)
passed: both one-shot timers are enabled, active and waiting, the installed
launcher assertion plus 15/15 focused and 50-pass/one-expected-skip broader
target tests passed, and production stayed healthy. The 01:42 one-occurrence
reconciliation is active. Runtime backup, pull, identity, quiet-host and
absence checks remain fresh fail-closed gates.

The conditional [October 26 F3 conversion](evidence/F3-from-F2-no-go-2026-10-26.md)
then failed closed at its first gate. Because F2 was not complete and contained
no accepted archive rows, the converter was not invoked and no retained receipt
was written. This is the required outcome; it grants no F4 or later authority.

The fresh [October 27 F3 effect review](evidence/F3-from-F2-exact-cycle-effect-review-2026-10-27.md)
accepts platform commit `35b5f61d` as an approval-ready conditional conversion
card. It binds the corrected installed coordinator, exact cycle state and
one-invocation/no-retry boundary; 14/14 F3 tests and target hash/custody checks
pass. The effect remains unapproved and may run only after the 01:42
reconciliation accepts exactly three complete F2 rows.

The [October 22 exact-cycle attempt](evidence/F2-exact-cycle-no-go-2026-10-22.md)
passed preparation at 01:15 but the final service exited `1` after one second
at 01:20. The bounded terminal state is `no_go`, first failure phase `final`,
failure class `FINAL_FAILED`, with no archive rows. The scanner did not run.
The coarse final class and suppressed service output do not identify the
failed final-guard subcheck, so a more specific cause would be speculation.
The spent date-specific timers were removed, recurring timers remain disabled,
and production postchecks passed. F2 remains open and F3 cannot advance. The
platform owner must preserve a bounded final subphase/code and prove the
correction offline and on target Linux before a fresh card and approval.

The platform owner supplied that source-only correction at
`1ca66cee2953c50563da90fe2071a70b62372c2c`. Stream A's
[independent review](evidence/F2-final-subcheck-diagnostic-independent-review-2026-10-22.md)
first rejected a missing observer-communication test, then verified the
corrected pin and 14/14 focused local tests after the gap was fixed. The
platform owner reports 14/14 target-Linux focused tests and 361 local passes
with eight expected skips. This is ready only for a separately approved
inactive one-file installation; it does not diagnose the October 22 failure
retroactively or authorize another scan.

Jason approved that inactive installation. The
[installed-path result](evidence/F2-final-subcheck-diagnostic-inactive-install-2026-10-22.md)
records the corrected coordinator at its pinned hash, the former bytes in a
root-only rollback checkpoint, 14/14 target-Linux focused tests, disabled F2
timers and healthy production postchecks. No scan, lease, receipt or F3 action
ran. The platform owner may now prepare a fresh exact-cycle candidate, but a
separate reviewed activation approval is still required.

The platform owner prepared the October 23 exact-cycle candidate at corrected
commit `58edf4e1`. Stream A's
[independent review](evidence/F2-exact-cycle-activation-review-2026-10-23.md)
verified both timer hashes, exact dates, nonpersistent scheduling, preservation
of October 19–22 evidence and the observation-only cleanup owner. The candidate
did not receive its separate activation approval before the fixed window and
is now expired. The [04:00 reconciliation](evidence/F2-window-not-activated-2026-10-23.md)
confirmed both exact-date units absent, recurring F2 timers disabled/inactive,
and no cycle state, lease, lock or scanner. No scan ran. F2 remains open; the
platform owner must prepare a fresh-date card before another activation
decision.

The platform owner then prepared a fresh October 24 candidate at full commit
`054ada0698d4b35cf99217b1d6fe7bac97ff1cb3`. Stream A's
[independent review](evidence/F2-exact-cycle-activation-review-2026-10-24.md)
recomputed both timer hashes, verified the 01:15/01:20 exact-date,
nonpersistent schedules, confirmed that historical evidence is preserved, and
confirmed the observation-only cleanup boundary. The candidate is ready for a
separate activation decision; no timer is installed or enabled and no scan is
authorized yet.
The subsequent [target-side validation](evidence/F2-october-24-target-validation-and-missed-window-analysis.md)
matched both candidate and all five installed source hashes, passed systemd
unit/calendar checks, found the required live absence gates and healthy core
guests/Proxmox daemons, then removed its temporary files. This closes the
pre-activation validation step only. The future backup/task-1 gates remain
volatile, and activation still requires explicit approval.
Jason then explicitly approved activation. The
[activation result](evidence/F2-exact-cycle-activation-result-2026-10-24.md)
records matching installed hashes, enabled/active one-shot timers for 01:15
and 01:20 PDT, disabled/inactive recurring timers, healthy Proxmox/guest
postchecks, and an active one-occurrence 01:42 observation-only reconciliation.
No service was manually started and no scan, lease, receipt or F3 action has
yet occurred. F2 remains open until terminal evidence is reconciled.

The [October 25 terminal result](evidence/F2-exact-cycle-no-go-2026-10-25.md)
is NO-GO. Preparation completed successfully, but the final service exited 1
with bounded phase `final` and class `FINAL_GUARD_INSTALLED_PIN`; no scanner or
archive row was produced. The spent exact-date timers were removed, recurring
timers remain disabled, no lease/lock/receipt exists and production postchecks
passed. F2 and F3 remain blocked. The platform owner must identify the exact
installed path/hash mismatch, prove any correction offline and on target Linux,
and present a fresh reviewed exact-cycle candidate before another approval.

That diagnosis and bounded correction are now complete. The platform owner
identified stale `host_exclusion.py` pins in the wrapper and observer, then
installed only the two corrected files after Jason's approval. Stream A's
[independent installation and October 26 review](evidence/F2-host-exclusion-pin-correction-and-october-26-review-2026-10-25.md)
re-read all three installed hashes, confirmed 17/17 target-Linux validation,
matched the fresh exact-date timer hashes, and found the new-cycle state,
lease, lock and receipt absent with recurring timers disabled. Static review
passes. Jason then approved the exact activation. Platform commit
`7d74e6cf9cd2dae057b8ed3b10e3515606f3989e` records both one-shot timers
enabled, active and waiting for 01:15/01:20 PDT, with recurring timers still
disabled and no manual service start. Stream A independently confirmed those
states and created the one-occurrence 01:42 observation/cleanup heartbeat. F2
is still open until runtime produces three bounded exit-zero rows. A later
[10:18 PDT static recheck](evidence/F2-october-26-static-recheck-2026-10-25.md)
again matched both timer and all five installed source hashes, found both
timers active at their exact times, and confirmed the new-cycle state, lease,
lock and receipt absent. This does not replace the fresh runtime gates.

The replacement [F3-from-F2 path](evidence/F3-from-F2-inactive-install-result-2026-10-25.md)
is now installed inactive and target-tested. Its exact October 26
[effect-card review](evidence/F3-from-F2-exact-cycle-effect-review-2026-10-25.md)
is GO at the design boundary: one conversion, no retry, no second archive scan,
independent receipt verification and F4 deferred to a subsequent cycle. The
effect remains unapproved and may not run unless F2 is independently reconciled
as a complete three-row success.

The [October 24 terminal result](evidence/F2-exact-cycle-no-go-2026-10-24.md)
is NO-GO. Preparation succeeded, but the final service exited 1 with bounded
phase `final` and class `FINAL_GUARD_SUBCHECK_FAILED`; no archive rows were
produced and no scan result exists. The spent exact-date timers were removed,
recurring timers remain disabled, and production postchecks passed. The
installed coordinator collapses every exception from the final guard into this
one class, so the failed clock/window, absence, exclusion, lease,
quiet-process, load, installed-pin or snapshot/freshness subcheck remains
unknown. F2 and F3 stay blocked pending a per-subcheck diagnostic correction,
offline and target-Linux proof, and a fresh reviewed cycle.

The platform owner supplied the per-subcheck correction at full commit
`770107dfe5a7f0473f99be98675752fa7fa86b14`. Stream A's
[independent review](evidence/F2-final-guard-subcheck-correction-independent-review-2026-10-24.md)
matched both candidate and installed baseline hashes and passed 24 focused
tests from a clean commit archive with one expected macOS custody skip. The
platform owner reports 24/24 target-Linux and 362 full-suite passes with eight
expected skips. The two-file candidate is ready for a separately approved
inactive installation; it does not authorize a timer, rerun or F3 action.

Jason approved that inactive installation. The
[installed-path result](evidence/F2-final-guard-subcheck-correction-inactive-install-2026-10-24.md)
records matching candidate hashes, a fresh root-only rollback checkpoint,
24/24 target-Linux focused tests, absent/inactive F2 timers and healthy
production postchecks. No scan, schedule, lease, receipt, service stop, model
call or F3 action ran. The correction is ready for a future failure to identify
the exact final subcheck, but F2 remains open until a fresh exact-cycle card is
prepared, reviewed, approved and produces three exit-zero archive rows.

The platform owner then prepared the fresh October 25 candidate at full commit
`3b15f8c6412180bf2340c89e293c2e23f82d9912`. Stream A's
[independent review](evidence/F2-exact-cycle-activation-review-2026-10-25.md)
matched both timer hashes, passed target systemd unit and exact-calendar checks,
re-read the installed diagnostic pins and verified the required current-cycle
absence gates. Temporary validation files were removed. The two timers remain
uninstalled and inactive pending one exact activation decision; no scan or
other effect is authorized yet.

Jason explicitly approved that exact activation. The
[activation result](evidence/F2-exact-cycle-activation-result-2026-10-25.md)
records matching installed unit and diagnostic hashes, enabled/active one-shot
timers for 01:15 and 01:20 PDT, absent current-cycle state/lease/receipt and an
active 01:42 observation-only cleanup automation. Neither service was manually
started. F2 is scheduled conditionally and remains open until the fresh runtime
gates and terminal evidence are reconciled.

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

The [October 20 exact-cycle attempt](evidence/F2-exact-cycle-no-go-2026-10-20.md)
fired both date-specific timers at 01:09 and 01:10 PDT. Preparation exited 1
after five seconds, final exited 1 immediately, and the terminal state is
`no_go` with no archive rows. The final generic error overwrote the earlier
content-free preparation cause while both unit streams were suppressed, so
the individual failed preparation sub-gate is **UNKNOWN**. Naming a backup,
TrueNAS, pin, load or archive cause would be unsupported. Production stayed
healthy, no scanner/lease/receipt remained, the spent exact-date timers were
disabled, and the daily timers remain disabled. F2 is FAILED/UNMEASURED for
this cycle and cannot be retried; the one-occurrence Codex observer is paused.
The platform owner must first preserve a
bounded first-failure phase/code and pass offline plus target-Linux tests;
another cycle needs a fresh card and approval.

The platform owner's source-only correction is pinned at
`183e7cfcc6d5de9c6e1da0d7f86c0cc8269f80c9`. Stream A's
[independent review](evidence/F2-first-failure-correction-independent-review-2026-10-20.md)
verified both frozen hashes, the first-failure preservation logic and a 10/10
isolated focused pass. The platform owner reports 344 local passes with eight
expected skips and 10/10 target-Linux focused tests. This advances only the
source-review gate. Jason subsequently approved its one-file inactive
installation. The platform [installation record](../../../services/local-ai-lease/F2-FAILURE-PHASE-INSTALL-RESULT-20261020.md)
at commit `8a747eccc837d6c71d615dfb589562d32a6cb419` records the corrected
`aef623af…5cd23` coordinator at root:root `0644`, the old
`67510f7b…f28f3d` bytes in a root-only rollback checkpoint, 10/10 focused
target-Linux tests, disabled/inactive F2 timers and no scan, receipt, lease,
service restart, backup or model call. The failed helper-service state and
October 20 terminal evidence were deliberately preserved. No F2 schedule is
active and no new scan is authorized.

**October 21 fresh-cycle result:** Jason approved the subsequent fixed-window
correction and one-cycle activation. The platform
[activation record](../../../services/local-ai-lease/F2-EXACT-CYCLE-ACTIVATION-RESULT-20261020.md)
at commit `13303e3359649b19b4ad0bf7eb7e46b9de931ad6` records coordinator
hash `fd711a4c…2356`, a verified root-only rollback to `aef623af…5cd23`,
and two nonpersistent exact-date timers: prepare at 01:15 PDT and final/read-
only scan at 01:20 PDT on October 21, with the existing 01:40 hard deadline.
Recurring and October 20 timers remained disabled. The prepare phase recorded
`PREFLIGHT_FAILED` and no scan followed. Reconciliation proved that task 1
does not copy LXC110 before the preflight and that the separate final windows
were inconsistent. The exact-date timers were stopped, disabled and removed;
production remained healthy. See the
[dated result](evidence/F2-exact-cycle-no-go-2026-10-21.md). F2 remains open
and F3 cannot advance.

The platform owner has also prepared the conditional post-F2 F3/F4 sequence
at `29018e69ce893f970d899c5b30631624d8f5d7cf`. Stream A's
[independent review](evidence/F3-F4-conditional-sequence-independent-review-2026-10-20.md)
verified the card digest and its isolated 2/2 pin/contract tests. F3 and F4
remain distinct future approvals: F3 may write one durable archive receipt
only after complete F2 evidence; F4 later binds that receipt to a fresh live
observation. Neither effect is currently authorized.

The downstream conditional F5/F6 card is pinned at platform commit `5106efc0`.
Stream A's [independent review](evidence/F5-F6-conditional-gates-independent-review-2026-10-20.md)
passed its isolated 2/2 contract tests and corrected two false/ambiguous
preflight findings: the model path is a symlink to a restricted pinned blob,
and the Aster/Speech/News observer namespaces are now explicit. F5 still needs
fresh read-only observation after F4; F6 remains inactive and separately
approval-gated. No lease or service stop is prepared as an automatic effect.

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
| F2 | **New-cycle read-only archive timing**, after successful 00:30 Proxmox job and 01:00 TrueNAS task 1 | Exact current-cycle 104/110/116 identities; three bounded `zstd -t` exit-0 results before the deadline, without competing work. Failure/unknown/partial is NO-GO. | [ ] **OCTOBER 27 SCHEDULED / CONDITIONAL** — corrected one-shot timers are active for 01:15/01:20 PDT with observation/cleanup at 01:42. Static installed-path checks pass; fresh backup, task-1, identity, load and exclusion gates remain runtime conditions. |
| F3 | **Trusted retained-receipt release**, after F0/F1 and timing review | A separately reviewed, hash-pinned producer can write a root-owned mode-0600 receipt in a mode-0700 directory only after all fixed source, whole-job, task-1, archive identity/integrity and deadline checks pass. Partial/late scans leave no success receipt. Test the actual installed path and rollback; obtain bounded host-change approval. | [ ] **OCTOBER 27 APPROVED / SCHEDULED CONDITIONAL** — the installed converter and corrected dependency pins match, the 14-test F3 suite passes and the [one-time 01:50 activation](evidence/F3-from-F2-exact-cycle-activation-2026-10-27.md) is active. Conversion must skip unless 01:42 reconciliation accepts exactly three complete F2 rows and all postchecks; no receipt exists before the run. |
| F4 | **Fresh trusted pre-acquire receipt for the drill cycle**, after F3 and that cycle's backup/task 1 | Complete current-cycle pre-acquire envelope exists, is independently re-read and bound to the same archive identities, backup digest, proposed lease identity and still-running production observation; stale, replaced or incomplete files fail closed. It grants no authority to stop services. | [ ] **WRITER INSTALLED INACTIVE / LIVE INVOCATION OPEN** — the new pre-acquire boundary and corrected controller consumer remain installed inactive. The [same-cycle correction](evidence/F4-same-cycle-and-watchdog-sequencing-correction-2026-10-26.md) requires F4 to bind the same local-date accepted F2/F3 set after the 03:00 pull. The pure builder binds exact predecessor bytes without effects, and the [fixed-source writer installation](evidence/F4-F5-root-writer-inactive-install-review-2026-10-26.md) now passes 9/9 target tests with exact custody, ready lease and absent evidence. One same-cycle writer invocation remains separately unapproved; F5–F7 must pass before F8 can consume it. |
| F5 | **03:05 full preflight**, after F4 and 02:00/03:00 TrueNAS tasks | Fixed schedules and same-cycle job completions; exact LXC110 mirror; three consumers still running; no conflicting lease/job; pinned Qwen3.5-9B Q4_K_M, llama.cpp b11429 SYCL/Level Zero, GPU, unit and authentication state; News timer active/enabled and job idle. Save non-secret baseline for restoration. | [ ] **AUTH PATH AND WRITER INSTALLED / FRESH INVOCATION OPEN** — the metadata-only authentication upgrade requires no-auth and invalid-key rejection before accepting the real key and exact model; 13/13 target tests passed without inference. The fixed writer now collects this observation and publishes admission last, but it has not been invoked. F5 still requires the successful same-cycle F2/F3 chain and 03:00 pull plus separate live approval. |
| F6 | **Independent recovery armed**, after F5 and approved live card | Compatible watchdog and owner-liveness paths are verified active/enabled before any stop; exact state schema and constrained recovery executor match pins; the manual `acquire --light` remains legacy-schema and cannot be used with this watchdog even after its F2 lock update. Loss of watchdog/owner closes acquisition. | [ ] **PRE-EFFECT EXERCISE PASSED / V3 COMPOSITION AND FINAL M3 PACKET INSTALLED INACTIVE / CURRENT-PACKET SOURCE CARD VALIDATED** — the exact receipt-free exercise reached healthy durable `PREPARED`, proved the healthy watchdog path inert, detected owner loss and recovered with nested `cancelled-prepared`. It issued zero consumer commands, left F2/F6 unchanged and passed independent cleanup/production checks. Receipt SHA-256 is `d5cad1d3…be13`. The inactive auth-pin upgrade and [owner-before-heartbeat correction](evidence/Stream-A-F6-owner-heartbeat-ordering-inactive-install-2026-10-25.md) are installed inactive. The first two [composition](evidence/Stream-A-evaluation-composition-source-review-2026-10-25.md) packets were prevented or rolled back on dependency-boundary defects. The corrected [V3 installation](evidence/Stream-A-evaluation-composition-inactive-install-v3-2026-10-25.md) passed 96/96 target-Linux tests, installed all 13 pinned paths, imported through the two fixed module roots and returned the exact inert guest result in both guests. The final [M3 packet receipt](evidence/Stream-A-F6-current-M3-packet-coordination-2026-10-25.md) pins runner `88af8eb7…`, scorer `7bce041e…`, journal validator `966786f8…` and complete eleven-file manifest `7b547d9b…`; its dependency-free suite passes 119/119 and target scorer tests pass 9/9. The [post-V3 card reconciliation](evidence/Stream-A-F6-post-V3-activation-card-reconciliation-2026-10-25.md) found the candidate-H card's restore-observer pin stale and all V3 composition pins absent. F6 remains disabled/inactive with no state or lock. The [current-packet source card](evidence/Stream-A-F6-current-packet-card-review-2026-10-26.md) at platform commit `107626c6` now passes its 5/5 contract suite and Stream A independent validation against every required V3/M3 and guest binding. Production arming still requires fresh same-cycle F3–F5 evidence, a cycle-specific effect transaction/rollback and later approval. |
| F7 | **Human live-drill approval**, after reviewable F3–F6 evidence and revised platform card | Jason approves one exact bounded drill, target services, stop condition, 03:30 hard release cutoff, 04:15 reconciliation reserve and rollback. No automatic approval from this tracker or scheduler. | [ ] NOT REQUESTED — platform run card remains NO-GO. |
| F8 | **Bounded full-stop acquisition/drill**, after F4–F7 in the same cycle | New source-bound controller persists watchdog-compatible state and lock before stopping only Aster Agent (104), llama.cpp (110) and Speech (116); records each effect and stable isolation. No model call, unrelated host change or News timer stop. | [ ] NOT SCHEDULED. |
| F9 | **Exact recovery and release**, after F8 | Independent recovery/restore proves original services plus exact model/backend, GPU, auth, unit, schedules, backup points, News and control plane. Release by 03:30 only on a complete match; otherwise retain lock, mark FAILED/UNKNOWN and use 03:30–04:15 for reconciliation. | [ ] NOT STARTED. |
| F10 | **Evidence close-out**, after F8/F9 | Keep immutable observations, unexpected effects, rollback result and decision record; update run card and this tracker; no A1 promotion inferred. | [ ] NOT STARTED. |
| A1 | **Aster full-path benchmark**, only on a later separate backup cycle | Its own application-only lease, source-bound A1 admission, sidecar/ingress/auth and recovery gates, frozen workload and independent scoring. A full-stop attempt makes A1 NO-GO for that same cycle even if recovery succeeds. | [ ] SEPARATE BLOCKED LANE — not part of F8/F9 approval. The [October 18 interface review](evidence/A1-admission-platform-interface-review-2026-10-18.md) records the corrected offline trigger/deadline contract and matched v2 client. Trusted source-specific host adapters, measured recovery/lag, installed-path proof and live drill remain open. |

## Critical path and failure reporting

The October 27 F2 and conditional F3 actions are scheduled for 01:15–01:50 PDT. The [F4 sequencing correction](evidence/F4-same-cycle-and-watchdog-sequencing-correction-2026-10-26.md) proves that any later F4/F5 must use that same local date after the 03:00 pull; waiting until the next calendar day would invalidate the accepted archive set. The fixed-source writer is now installed inactive and target-tested, separating non-effect evidence production from the still-mandatory F6 watchdog gate. No F4/F5 invocation is yet authorized or scheduled.

F2 can be measured while the later gates are engineered, but a successful
read-only F2 result is not itself a trusted F4 pre-acquire envelope. The
installed F3 converter could retain a future unchanged F2 result only after
independent reconciliation accepts exactly three bounded exit-zero rows and
the separate effect gate remains valid. October 26 F2 failed with no rows, so
its 01:50 conversion must skip without writing. F4 and F5 then require fresh
same-cycle observations; F5–F9 are
serial and cannot be inferred from the clock.

The October 26 sequence ended at F2 without a scan result. The next conditional
sequence starts only after the observer communication defect is diagnosed,
corrected, proven offline and on target Linux, and represented by a fresh
reviewed exact-cycle card. A later successful F3 result would not arm recovery
or stop a consumer. F4/F5 must be produced and independently accepted, the
platform owner must replace the stale F6 card with one pinning the installed V3
and final M3 packet, and Jason must approve the exact live drill before F6–F9.
This failed cycle cannot be retried and leaves production running; it does not
block offline Stream A work.

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
