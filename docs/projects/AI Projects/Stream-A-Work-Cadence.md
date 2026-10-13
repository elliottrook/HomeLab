# Stream A work cadence

> Owner: Jason. Status: continuous lane active; exclusive automation paused at Jason's request on 2026-10-12. This schedules work; it does not promote a model, deploy a service, grant a tool, or waive an approval gate.

Stream A has two work lanes. **Continuous lane:** documentation, code and fixture review, local tests, evidence reconciliation, read-only LAN/health checks and low-impact shared-service observation run whenever useful, including between lab windows. Continue this lane when an exclusive run is blocked. During an active whole-host lab lease, keep this lane offline and do not compete with maintenance. Companion session and Keychain behavior remain quiet reliability monitoring under the [D3 gate reassessment](evidence/D3-refresh-gate-reassessment-2026-10-12.md), not a reason to hold other Stream A work. A signed-in request after time has passed may support renewal, but sign-out/re-sign-in is not refresh evidence. Check only content-free observations; do not manufacture expiry or send repeated Codex questions.

**Exclusive lane:** deliberate model-call batches, latency/quality comparisons and any activity that occupies the single inference slot or requires lab isolation. Jason's newer [cross-project schedule decision](evidence/Stream-A-lab-window-coordination-2026-10-12.md) proposes a **whole-host `ai-lab` maintenance lease after the complete backup chain and ending by 04:15 America/Vancouver**, followed by a 04:15–06:15 local-AI analysis reservation and the 06:15 News digest. The lab lease can include guest/component restarts and host reboots under that project's checkpoint and recovery controls. Stream A may use the longer lease for its scoped tests, but it does not own the host scheduler or B60 backend promotion. The old 01:00–02:00 Aster slot is retired.

**Current-state guard, reconciled 2026-10-12:** the platform owner's current,
uncommitted `docs/projects/Local-AI-Platform-Split.md` record in the main
checkout reports backup schedules moved to Proxmox 00:30 and TrueNAS
01:00/02:00/03:00. Stream A independently checked the enabled Proxmox job and
TrueNAS tasks 1/3/2 read-only on 2026-10-12; those configured schedules match.
This does not prove a later backup chain completed. The platform record also
reports one successful manually acquired and released **light** lease; the
controller remains disabled by default and unscheduled. Stream A has not
obtained a current lease receipt. The News 06:15 move and 04:15–06:15 analysis workload
remain proposed. Jason will assign new exclusive time later. The former
01:30 exclusive automation is **paused**; it performs no wake-up or test.
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

The exclusive automation remains paused until Jason assigns a new lab window.
Then it may inspect the actual backup/lease state and execute only READY,
bounded tests inside a verified lease. The continuous-lane automation remains
active every four hours, works without exclusive B60/host access and stays
quiet on unchanged session state. Both belong to this chat and worktree; a
remote push follows the repository's per-push rule except Jason's narrow
standing authorization for branch commits whose purpose is coordination with
the MacBook B60 agent.
