# Stream A work cadence

> Owner: Jason. Status: continuous lane active; no exclusive benchmark launcher admitted. The one-time October 15, 16 and 17 read-only checks are complete and paused. This cadence does not promote a model, deploy a service, grant a tool, or waive an approval gate.

## Operator approval and timed-test signal

When an explicit approval is the only remaining blocker, Stream A must send a
standalone notification whose first line is:

> 🚨 **ACTION REQUIRED — APPROVAL**

The notification must state the exact action being approved, its decision
deadline, expected effect, explicit exclusions and what will happen if approval
does not arrive. Do not bury this request in a progress report or wait for Jason
to ask what is next. One reminder may be sent at the card's recorded reminder
time; an expired request is retired and reported as NO-GO rather than silently
carried into another cycle.

Immediately after approval has been applied and the resulting installation,
activation or preflight has been checked, report exactly one of:

- **TIMED TEST: GO — SCHEDULED / CONDITIONAL**: the exact runner or timer is
  active, static hashes/custody and cleanup observation passed, and the next
  trigger time is stated. List any fresh runtime gates that must still pass at
  execution, such as the current backup chain, host load and absence of a
  competing lease. These conditions do not require another approval unless the
  reviewed action changes.
- **TIMED TEST: NO-GO**: the test is not safely runnable or scheduled. State the
  first failed dependency, practical effect and the exact next approval or
  corrective action. Present that approval request immediately when it is ready.

Routine status may follow this signal, but must not obscure it. This convention
changes operator communication only; it does not weaken repository, platform or
live-change approval boundaries.

**October 23/24 activation cadence correction:** the October 23 F2 packet was
technically ready about seventeen hours before its window, but its distinct
host-activation approval was not received before 01:15. No timer or scan ran.
The [measured review](evidence/F2-october-24-target-validation-and-missed-window-analysis.md)
records this as an approval-workflow miss, not an F2 or backup failure. Exact-
cycle cards must now be reviewed by noon where possible, raised immediately as
a timed blocking decision, reminded once at 18:00, and retired at 22:00 if
still unapproved. The replacement October 24 candidate has passed target-side
unit/calendar, installed-pin, custody and current absence checks, but remains
inactive pending its own explicit approval.
Jason subsequently approved that exact activation. The
[October 24 activation](evidence/F2-exact-cycle-activation-result-2026-10-24.md)
is now live: prepare is scheduled once at 01:15, final once at 01:20, and the
observation-only reconciliation once at 01:42 PDT. Recurring F2 timers remain
disabled. The future backup and TrueNAS completion gates remain mandatory; a
failed or uncertain gate means NO-GO without retry.
The [October 24 terminal result](evidence/F2-exact-cycle-no-go-2026-10-24.md)
is now **NO-GO**: preparation passed, final failed after one second with
`FINAL_GUARD_SUBCHECK_FAILED`, and there are no archive rows. The exact-date
timers were removed, recurring timers remain disabled, and production is
healthy. The installed wrapper does not retain which final-guard subcheck
failed; a per-subcheck diagnostic correction, offline/target proof and a fresh
reviewed and approved cycle are required before another attempt.
The bounded per-subcheck correction was subsequently
[installed inactive](evidence/F2-final-guard-subcheck-correction-inactive-install-2026-10-24.md)
with a fresh root-only rollback checkpoint. Installed hashes match the reviewed
platform commit and 24/24 target-Linux tests pass. All F2 timers remain absent
or inactive and production postchecks are healthy. A fresh date-specific card,
independent review and separate activation approval still precede another
timed attempt.
The platform owner's fresh October 25 exact-cycle candidate at `3b15f8c6` has
now passed [independent review](evidence/F2-exact-cycle-activation-review-2026-10-25.md):
both nonpersistent timer hashes match, target systemd/calendar checks resolve
to 01:15/01:20 PDT, installed diagnostic pins match and required cycle state is
absent. The timers remain uninstalled/inactive pending exact activation
approval. An observation-only reconciliation at 01:42 owns cleanup; runtime
backup, host and lease gates still fail closed.
Jason then approved the exact October 25 activation. The
[activation result](evidence/F2-exact-cycle-activation-result-2026-10-25.md)
records enabled/active one-shot timers for 01:15 and 01:20 PDT, unchanged
diagnostic pins and an active observation-only reconciliation at 01:42. The
timed test is GO — scheduled/conditional; fresh runtime gates still decide
whether the scanner starts, and any failure means NO-GO without retry.

**October 20 F2 result:** the two exact-date timers fired and are now disabled,
but preparation failed after five seconds and final failed immediately. No
archive row or scan result was produced. The exact preparation sub-gate is
unknown because the final generic state overwrote it while service output was
suppressed. Production remained healthy and no lease, receipt, drill, A1 run
or model call occurred. A platform diagnostic-preservation correction,
offline/target proof and a fresh approved cycle are required before another
F2 attempt; no F2 schedule is now active.
The bounded one-file diagnostic correction was subsequently installed with
Jason's approval. Its installed hash and root-only rollback match the reviewed
card, and 10/10 target-Linux focused tests pass. It preserves the first bounded
failure phase/class on a future attempt. All F2 timers remain disabled; the
failed helper-service status and terminal October 20 evidence remain intact.
This installation does not authorize or schedule another scan.
Jason then approved a fresh October 21 exact cycle. A fixed-window coordinator
with a root-only rollback is installed; two nonpersistent timers are active
for preparation at 01:15 and final/read-only scan at 01:20 PDT, with a 01:40
hard deadline. The recurring timers remain disabled. A one-occurrence 01:42
Stream A heartbeat may only reconcile the terminal state and remove/disable
the spent timers; it cannot retry or advance F3 automatically.
That October 21 attempt subsequently failed in prepare without a scan. The
superseding [four-file correction](evidence/F2-final-minute-consistency-inactive-install-2026-10-21.md)
is now installed inactive with root-only rollback and 33/33 target-Linux
tests. It removes F2's future 02:00 LXC110 mirror dependency and aligns the
final guard, observer and producer to the coordinator's 01:20 start and 01:40
deadline. Recurring F2 timers remain disabled; no scan, receipt or lease ran.
A fresh exact-cycle card and approval remain necessary before F2 can produce
qualifying evidence.
Jason subsequently approved the reviewed October 22 exact cycle. The two
[date-specific timers](evidence/F2-exact-cycle-activation-result-2026-10-22.md)
are enabled and active for 01:15 prepare and 01:20 final, with a 01:40 hard
deadline and one observation-only 01:42 reconciliation. Recurring F2 timers
remain disabled. No scan result is claimed before the terminal state is read;
failure or uncertainty means NO-GO without a same-cycle retry.
The [October 22 result](evidence/F2-exact-cycle-no-go-2026-10-22.md) is now
terminal NO-GO: prepare succeeded, final exited `1` after one second, and the
retained bounded class is `FINAL_FAILED` with no archive rows. The scanner did
not run. Exact-date timers were removed, recurring timers remain disabled and
production is healthy. Do not schedule another attempt until the platform
owner adds a bounded final subphase/code and proves the correction offline and
on target Linux; a fresh cycle still requires its own reviewed card and
approval.
The final-subcheck diagnostic correction was subsequently
[installed inactive](evidence/F2-final-subcheck-diagnostic-inactive-install-2026-10-22.md)
with the prior coordinator preserved in a root-only rollback checkpoint.
Target-Linux focused tests passed 14/14, all F2 timers remain disabled and
production is healthy. This permits a future failed attempt to identify its
bounded final subcheck; it does not authorize or schedule that attempt.

**October 18 daytime lab-hours path:** Jason accepted up to 90 minutes of
daytime Aster/voice unavailability for a first supervised, no-reboot pilot.
The [measured acceleration assessment](evidence/Lab-hours-acceleration-assessment-2026-10-18.md)
separates that outage budget from host-change approval. Jason approved the
combined 19-file Proxmox and one-wrapper LXC110 **disabled** packet at
`b43d4971`. Stream A verified all 20 installed hashes, target-Linux imports,
47 focused synthetic tests, unchanged production services and no lab listener.
The proposed first live run is 30 minutes of isolation plus a 15-minute
restore reserve between hourly News ingests. Jason then approved the exact
`dafc0332` four-file guardian/rescue upgrade: the inactive target matches all
four pins, 65 target-Linux tests passed, and production postchecks remained
normal. No one-shot guardian has been armed, no live drain has run, and no
lab-hours schedule is active.
The first October 18 read-only live-source preflight returned NO-GO: the
completed 00:30 backup had aged out of Proxmox's current task list, and the
UPID parser rejected its valid trailing colon. The platform owner repaired
that source in `c66b9ae8` using bounded `pvescheduler` journal proof. Jason
approved the separate inactive four-file install; all four installed hashes,
rollback hashes and 65 target-Linux tests passed, and the read-only current-
cycle local backup proof returned `True`. The one-shot guardian remains
unarmed, and no outage followed. A **fresh** backup and News timer check,
MacBook operator custody, accepted GPU holder and separate live approval
still gate a 30-minute pilot plus 15-minute restoration. The proposed
six-minute 18:05–18:11 slot is not a valid run window for that profile.
The fixed in-guest smoke does not prove MacBook handoff or continuous host-wide
GPU exclusivity. The old manual controller and F2/F3 full-stop drill remain
separate gates.

**October 17 evening schedule check:** the October 17 F2 guard returned NO-GO
without archive rows. Its daily heartbeat entry was explicitly set to
`PAUSED` and the saved status was verified; it is not a new nightly scan.
The separate four-hour continuous-work heartbeat remains active for
offline/shared work. The enabled normal backup chain remains 00:30 Proxmox
and 01:00/02:00/03:00 TrueNAS, subject to actual nightly completion. No
full-stop drill, A1 benchmark or B60 exclusive test is scheduled by this
cadence. A later F2 scan requires a new reviewed card and one-cycle approval.

**October 15 afternoon update:** The approved full-stop compatibility
candidate is installed inactive on Proxmox and passed synthetic installed-path
Linux checks. The old controller remains unchanged and no live lease or drill
is admitted. A new one-time **read-only** archive timing check is scheduled
for October 16 at 01:10 Vancouver, conditional on that cycle's completed
backup/task-1 chain, suitable load and no conflicting lease or job. This is a
new dated observation, not a reopening of the completed October 15 check.
It cannot persist the trusted retained admission receipt; the receipt-writing
CLI and acquisition effects remain disabled. The platform owner controls the
live run card and any future watchdog activation. Full-stop and A1 cannot
share one backup cycle.
Track every dependency and any failed gate in the
[full-stop recovery dependency tracker](Full-Stop-Recovery-Dependency-Tracker.md).

**October 16 reconciliation:** The 01:10 archive timing check did not retain a
complete three-archive result before its cutoff and is paused. No later scan
or live drill is implied by the old schedule text below. A source-only common
host-exclusion candidate and a corrected disabled-install card exist; the
first host preflight found a card mismatch, which was fixed locally. The
platform owner had not installed that candidate or enabled a timer at the
time of this reconciliation. Its next host change needed exact approval,
target-Linux proof and preserved
rollback; the old manual lease path and backup/TrueNAS conflict checks still
gate unattended observation. Continue M1/D4 and M3 work offline while these
dependencies are resolved.

The first approved six-path staging attempt subsequently failed the A1
controller import check and was [fully rolled back](evidence/Common-host-exclusion-disabled-install-rollback-2026-10-16.md).
Its one-root card is superseded by a seven-path, two-root review candidate.
No archive observation is admitted from that failed attempt; a separate exact
approval is needed for the corrected host change.

**October 16 evening F2 update:** A later, distinct three-path read-only F2
candidate was installed disabled on Proxmox after target-Linux synthetic tests
passed (23 focused tests plus four installer tests). The manual controller,
producer and one-shot guard match their pinned hashes; no archive scan, receipt,
lease or timer activation occurred. Jason approved one conditional, supervised
scan for the **October 17** backup cycle. The 01:05 preflight may start the
one-shot guard only between 01:10 and 01:19 if that cycle's backup and TrueNAS
task 1, exact archive identities, installed pins and quiet-host gates all pass.
The hard stop is the earlier of 20 minutes or 01:40. Any failed or uncertain
gate means NO-GO without a retry. This approval does not release a trusted
receipt or full-stop drill; see the dependency tracker for the current F2 gate.

Stream A has two work lanes. **Continuous lane:** documentation, code and fixture review, local tests, evidence reconciliation, read-only LAN/health checks and low-impact shared-service observation run whenever useful, including between lab windows. Continue this lane when an exclusive run is blocked. During an active whole-host lab lease, keep this lane offline and do not compete with maintenance. Companion session and Keychain behavior remain quiet reliability monitoring under the [D3 gate reassessment](evidence/D3-refresh-gate-reassessment-2026-10-12.md), not a reason to hold other Stream A work. A signed-in request after time has passed may support renewal, but sign-out/re-sign-in is not refresh evidence. Check only content-free observations; do not manufacture expiry or send repeated Codex questions.

**Exclusive lane:** deliberate model-call batches, latency/quality comparisons and any activity that occupies the single inference slot or requires lab isolation. Jason's newer [cross-project schedule decision](evidence/Stream-A-lab-window-coordination-2026-10-12.md) proposes a **whole-host `ai-lab` maintenance lease after the complete backup chain and ending by 04:15 America/Vancouver**, followed by a 04:15–06:15 local-AI analysis reservation and the 06:15 News digest. The lab lease can include guest/component restarts and host reboots under that project's checkpoint and recovery controls. Stream A may use the longer lease for its scoped tests, but it does not own the host scheduler or B60 backend promotion. The old 01:00–02:00 Aster slot is retired.

**2026-10-14 schedule reconciliation:** The earlier proposed paused 03:15
Stream A readiness check is superseded by the current automation file
`aster-stream-a-b60-window`: `status = ACTIVE`, daily 03:40 Vancouver. Its
prompt is a **read-only post-drill recovery check** for October 15 and directs
the task to pause itself after that first run. It is not a 03:15 drill or an
exclusive benchmark launcher. No 03:15 platform drill automation was found in
the local automation inventory; whether the platform owner will perform an
attended drill remains a separate live decision. The 03:40 check may inspect
actual backup, lease and recovery receipts only; it cannot infer completion,
acquire the host, invoke a model, or re-enable the obsolete runner from the
clock. The [A1 full-path card](benchmarks/A1-full-path-admission-run-card-2026-10-13.md)
records the blocking gates and minimum restoration reserve.
After a measured 43.585 GB archive check exceeded the 300-second adapter
limit, a one-time **01:10 October 15 read-only timing check** was added. It
must skip unless the 00:30 backup and 01:00 pull actually finished, no host
lease is active, it begins by 01:20 and it can finish before 01:40. This
observes new-archive integrity and timing only; it is not a trusted admission
producer or live-drill launcher. The 03:05 and 03:40 checks remain read-only.
An [evening readiness audit](evidence/A1-evening-readiness-audit-2026-10-14.md)
found that 03:40 is too late for a first A1 admission with 35 minutes of
reserve before 04:15. A separate one-time **03:05 read-only backup/source
preflight** was active in this chat; it must mark A1 NO-GO by 03:10 if task 2
or any source-bound gate remains unproved. It neither runs the platform drill
nor grants A1 model calls.

**2026-10-15 completion:** The 01:10 timing check and 03:05 backup/source
preflight have each run once and are now **paused**. The [current-cycle
record](evidence/A1-2026-10-15-read-only-preflight.md) found successful
scheduled backups and matching A1 subset data, but no complete current-cycle
archive integrity result, no trusted retained receipt and no live A1 admission.
Full-stop and A1 remain NO-GO this cycle. The separate 03:40 read-only
postcheck [ran once](evidence/A1-2026-10-15-post-window-recovery-check.md),
found no full-stop drill or restoration evidence, and is now paused too.
Do not reactivate these completed one-time checks merely because the next
daily clock boundary arrives.

**Current-state guard, reconciled 2026-10-12:** the platform owner's current,
uncommitted `docs/projects/Local-AI-Platform-Split.md` record in the main
checkout reports backup schedules moved to Proxmox 00:30 and TrueNAS
01:00/02:00/03:00. Stream A independently checked the enabled Proxmox job and
TrueNAS tasks 1/3/2 read-only on 2026-10-12; those configured schedules match.
This does not prove a later backup chain completed. The platform record also
reports one successful manually acquired and released **light** lease; the
controller remains disabled by default and unscheduled. Stream A has not
obtained a current lease receipt. The News 06:15 move and 04:15–06:15 analysis workload
remain proposed. The 03:40 recovery-check automation performed a read-only
inspection on October 15, made no model call, and is now paused.
Before any exclusive test, recheck the actual schedules, completed backup
chain, active lease/owner, scope of drain and restoration deadline. A clock
time, a prior light-lease success or earlier broad lab access alone does not
grant a new lease.

The longer window increases test capacity once those controls exist. It does not silently authorize a new production release, credential exposure, security-policy change, remote Git write, or a test outside Stream A's recorded scope. Aster testing must yield to the host maintenance owner and stop early enough for accepted production to be restored and verified by 04:15.

## Ready-queue contract

Each exclusive candidate has one dated, committed run card with:

1. Question and expected decision value; why shared/offline work cannot answer it.
2. Scope, synthetic/sanitized input, exact runner and version pins, output custody, and any credential-delivery method already authorized. Never print or store a credential.
3. Baseline and frozen score/latency method; maximum requests, tokens, concurrency, elapsed time, and one-attempt/no-retry rule.
4. Whole-host lease ownership, completed backup chain, service-occupancy, runtime-hash, health and conflicting-experiment preflight; explicit stop conditions, restoration budget and production postcheck.
5. Classification as **READY**, **BLOCKED** or **DONE**, with a specific reason. Only READY cards execute inside a verified lease. A failed preflight changes READY to BLOCKED and produces no model call.
6. Result and limits, raw evidence location/checksum where permitted, local commit, and the separate promotion decision. Never turn a development score into a qualification claim.

Preflight multiple candidates in one continuous-lane pass, but execute serially within the window. Recheck volatile health/occupancy/pins immediately before each candidate. Stop after the first unexpected failure and preserve its partial evidence. Do not rerun an uncertain request. Use existing B60 engineering controls for any backend-changing experiment; Stream A owns assistant-workload evaluation, not the runtime project's promotion decision.

## Current queue, reconciled 2026-10-16

The [next batched offline preflight](evidence/Stream-A-batched-next-lab-preflight-2026-10-12.md)
classifies five prospective cards and their missing gates. None is yet a
READY exclusive run. The continuous lane can prepare synthetic completed-
answer capture and bounded diagnostic evidence while those gates remain open.

| Item | Lane / state | Next action |
|---|---|---|
| Companion session and Keychain reliability | Continuous / monitoring | Watch natural ordinary use for renewal failures or repeated prompts; investigate only on a meaningful change. The finite flagged-UI/consent check, not another indefinite refresh wait, gates routine manual-Codex release. No B60 exclusivity. |
| Gateway and imported-module source reconciliation | Continuous / done locally | Gateway and eight imported modules match production; Lab Operations retains an uninstalled operator-only candidate. Local commits await the normal per-push approval. |
| M1/D4 authority and diagnostic usefulness | Continuous / inactive M1 installation passed | The independent M1 identity, modules, configuration and units are installed on LXC104 but have never run; no listener, route or grant exists. Prepare the real-token and zero-overlap cutover evidence while continuing D4 offline. No connected Codex tool or worker grant follows without its own gate. |
| M3 low-resource decision contract and replay | Continuous preparation complete; exclusive calibration pending | The independent 60-case calibration set, blind labels, content-free release, registered policy, preregistered binary score and journal-bound wall-deadline runner now pass the dependency-free 111-test NLU suite. A machine-readable minimal persistent LXC110 staging/return packet is pinned and its validator byte-checks exact regular non-symlink inputs, but the packet has not been applied. The exact live run still needs a compatible whole-host lease plus staging and bounded model-call approval. Automatic routing, holdout access and shadowing remain off. |
| New 9B/SYCL assistant-workload experiment | Exclusive / DONE, no routing promotion | The [v1 run](experiments/m3-9b-sycl-routing-compatibility/RESULT-2026-10-12.md) stopped at case 1; two distinct-case diagnostics identified a non-plan/capability mismatch. A [versioned v4 development run](experiments/m3-9b-sycl-routing-compatibility/RESULT-V4-2026-10-12.md) returned valid shape on 30/30 but agreed with only 18/30 expected routes, missing all calendar, mixed and private-context examples. Stop prompt tuning on these exposed cases; automatic routing remains off. The old 27B/Vulkan sysadmin scores remain historical. |
| B60 backend benchmarks | B60 engineering project / outside Stream A run queue | Coordinate with that project's own gates and window. Stream A reads accepted results; it does not run a competing benchmark automatically. |
| A1 completed-answer control | Shared-service development run / DONE; qualification / open | The six-case development run is done. The first 20-case holdout attempt lost its answer evidence to a local write failure, so v1 has no quality score and must not be replayed. The [fresh v2](benchmarks/answer-holdout-release-v2-2026-10-12.md) passed storage and live admission, then returned 20/20 responses; two blind AI reviews agreed on [14/20 full-rubric passes](experiments/a1-answer-holdout-v2/RESULT-2026-10-12.md). This is a frozen direct-backend regression baseline, not native Aster latency, human ground truth or a promotion bar. Next candidates need separate profiles, independent labels and a paired comparison; do not retune on v2. |

No exclusive benchmark automation is admitted until the platform owner proves
the shared lease, independent recovery and benchmark admission and Jason
approves a bounded live card. The separate 03:40 recovery check inspected
actual state once and was paused. The continuous-lane automation remains
active every four hours, works without exclusive B60/host access and stays
quiet on unchanged session state. Both lanes belong to this chat and worktree; a
remote push follows the repository's per-push rule except Jason's narrow
standing authorization for branch commits whose purpose is coordination with
the MacBook B60 agent.

## Continuation rule — 2026-10-13

Jason asked Stream A to keep working through the available queue instead of
ending each turn after one check. The active four-hour continuation prompt now
states this explicitly. Within a turn, completion of a test, note or local
commit is a checkpoint: select the next independent authorized item from the
delivery map and this queue. An app reliability observation or a held release
gate does not stop offline M1/D4, M3 or benchmark work. End only when every
remaining useful item requires a real approval, credential, external result,
exclusive lease or unavailable resource, and report the exact gate. This rule
does not waive any release, remote-write or security approval.
