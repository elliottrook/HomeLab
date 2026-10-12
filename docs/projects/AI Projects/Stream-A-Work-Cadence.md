# Stream A work cadence

> Owner: Jason. Status: continuous lane active; exclusive automation paused at Jason's request on 2026-10-12. This schedules work; it does not promote a model, deploy a service, grant a tool, or waive an approval gate.

Stream A has two work lanes. **Continuous lane:** documentation, code and fixture review, local tests, evidence reconciliation, read-only LAN/health checks and low-impact shared-service observation run whenever useful, including between lab windows. Continue this lane when an exclusive run is blocked. During an active whole-host lab lease, keep this lane offline and do not compete with maintenance. The Companion natural-session observation belongs here: a signed-in request after time has passed can show refresh, but sign-out/re-sign-in is not refresh evidence. Check only content-free event codes; do not manufacture expiry or send repeated Codex questions.

**Exclusive lane:** deliberate model-call batches, latency/quality comparisons and any activity that occupies the single inference slot or requires lab isolation. Jason's newer [cross-project schedule decision](evidence/Stream-A-lab-window-coordination-2026-10-12.md) proposes a **whole-host `ai-lab` maintenance lease after the complete backup chain and ending by 04:15 America/Vancouver**, followed by a 04:15–06:15 local-AI analysis reservation and the 06:15 News digest. The lab lease can include guest/component restarts and host reboots under that project's checkpoint and recovery controls. Stream A may use the longer lease for its scoped tests, but it does not own the host scheduler or B60 backend promotion. The old 01:00–02:00 Aster slot is retired.

**Current-state guard:** the backup moves, News timer, lab controller and host-level lease are still proposals, not verified live changes. Jason changed priorities and will provide exclusive lab time later. The former 01:30 exclusive automation is **paused**; it performs no wake-up or test. Existing 02:30/04:00/04:20 backup tasks remain potential conflicts until independently verified moved. When Jason gives a new window, recheck the real schedule, completed backup chain, active lease/owner and restoration deadline before resuming any exclusive test. A clock time or earlier broad lab access alone does not prove those conditions.

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

| Item | Lane / state | Next action |
|---|---|---|
| Companion natural refresh | Continuous / observing | Quiet four-hour observation; a real refresh plus ordinary-use check can close only this D3 gate. It does not use B60 exclusivity. |
| Gateway and imported-module source reconciliation | Continuous / done locally | Gateway and eight imported modules match production; Lab Operations retains an uninstalled operator-only candidate. Local commits await the normal per-push approval. |
| M1/D4 authority and diagnostic usefulness | Continuous / open | Continue offline/read-only work. No connected Codex tool or worker grant follows without its own gate. |
| M3 low-resource decision contract and replay | Continuous / offline probe rechecked | The [first batched preflight](evidence/Stream-A-cadence-first-preflight-2026-10-12.md) accepted the reconciled gateway source; 30 tests passed. Representative labels and live shadow gates remain open. |
| New 9B/SYCL assistant-workload experiment | Exclusive / BLOCKED | The [first batched preflight](evidence/Stream-A-cadence-first-preflight-2026-10-12.md) found no current run card with a frozen representative corpus, current runner pin, credential-safe execution path and decision threshold. The old 27B/Vulkan sysadmin scores are historical; rerunning them overnight would not answer the next architecture question. Prepare a specific card before scheduling inference. |
| B60 backend benchmarks | B60 engineering project / outside Stream A run queue | Coordinate with that project's own gates and window. Stream A reads accepted results; it does not run a competing benchmark automatically. |

The exclusive automation remains paused until Jason assigns a new lab window. Then it may inspect the actual backup/lease state and execute only READY, bounded tests inside a verified lease. The continuous-lane automation remains active every four hours, works without exclusive B60/host access and stays quiet on unchanged session state. Both belong to this chat and worktree; neither pushes to Forgejo without immediately current approval.
