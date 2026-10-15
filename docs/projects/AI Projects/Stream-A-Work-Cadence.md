# Stream A work cadence

> Owner: Jason. Status: continuous lane active; no exclusive benchmark launcher admitted. A separate 03:40 read-only recovery check is active. This schedules work; it does not promote a model, deploy a service, grant a tool, or waive an approval gate.

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
preflight** is active in this chat; it must mark A1 NO-GO by 03:10 if task 2
or any source-bound gate remains unproved. It neither runs the platform drill
nor grants A1 model calls.

**Current-state guard, reconciled 2026-10-12:** the platform owner's current,
uncommitted `docs/projects/Local-AI-Platform-Split.md` record in the main
checkout reports backup schedules moved to Proxmox 00:30 and TrueNAS
01:00/02:00/03:00. Stream A independently checked the enabled Proxmox job and
TrueNAS tasks 1/3/2 read-only on 2026-10-12; those configured schedules match.
This does not prove a later backup chain completed. The platform record also
reports one successful manually acquired and released **light** lease; the
controller remains disabled by default and unscheduled. Stream A has not
obtained a current lease receipt. The News 06:15 move and 04:15–06:15 analysis workload
remain proposed. The 03:40 recovery-check automation is active for a read-only
inspection; it performs no model test.
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

## Current queue, 2026-10-12

The [next batched offline preflight](evidence/Stream-A-batched-next-lab-preflight-2026-10-12.md)
classifies five prospective cards and their missing gates. None is yet a
READY exclusive run. The continuous lane can prepare synthetic completed-
answer capture and bounded diagnostic evidence while those gates remain open.

| Item | Lane / state | Next action |
|---|---|---|
| Companion session and Keychain reliability | Continuous / monitoring | Watch natural ordinary use for renewal failures or repeated prompts; investigate only on a meaningful change. The finite flagged-UI/consent check, not another indefinite refresh wait, gates routine manual-Codex release. No B60 exclusivity. |
| Gateway and imported-module source reconciliation | Continuous / done locally | Gateway and eight imported modules match production; Lab Operations retains an uninstalled operator-only candidate. Local commits await the normal per-push approval. |
| M1/D4 authority and diagnostic usefulness | Continuous / open | Continue offline/read-only work. No connected Codex tool or worker grant follows without its own gate. |
| M3 low-resource decision contract and replay | Continuous / offline probe rechecked | The [first batched preflight](evidence/Stream-A-cadence-first-preflight-2026-10-12.md) accepted the reconciled gateway source; 30 tests passed. Representative labels and live shadow gates remain open. |
| New 9B/SYCL assistant-workload experiment | Exclusive / DONE, no routing promotion | The [v1 run](experiments/m3-9b-sycl-routing-compatibility/RESULT-2026-10-12.md) stopped at case 1; two distinct-case diagnostics identified a non-plan/capability mismatch. A [versioned v4 development run](experiments/m3-9b-sycl-routing-compatibility/RESULT-V4-2026-10-12.md) returned valid shape on 30/30 but agreed with only 18/30 expected routes, missing all calendar, mixed and private-context examples. Stop prompt tuning on these exposed cases; automatic routing remains off. The old 27B/Vulkan sysadmin scores remain historical. |
| B60 backend benchmarks | B60 engineering project / outside Stream A run queue | Coordinate with that project's own gates and window. Stream A reads accepted results; it does not run a competing benchmark automatically. |
| A1 completed-answer control | Shared-service development run / DONE; qualification / open | The six-case development run is done. The first 20-case holdout attempt lost its answer evidence to a local write failure, so v1 has no quality score and must not be replayed. The [fresh v2](benchmarks/answer-holdout-release-v2-2026-10-12.md) passed storage and live admission, then returned 20/20 responses; two blind AI reviews agreed on [14/20 full-rubric passes](experiments/a1-answer-holdout-v2/RESULT-2026-10-12.md). This is a frozen direct-backend regression baseline, not native Aster latency, human ground truth or a promotion bar. Next candidates need separate profiles, independent labels and a paired comparison; do not retune on v2. |

No exclusive benchmark automation is admitted until the platform owner proves
the shared lease, independent recovery and benchmark admission and Jason
approves a bounded live card. The separate 03:40 recovery check only inspects
actual state and should pause after its first run. The continuous-lane automation remains
active every four hours, works without exclusive B60/host access and stays
quiet on unchanged session state. Both belong to this chat and worktree; a
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
