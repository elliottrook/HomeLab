# Stream A work cadence

> Owner: Jason. Status: active operating procedure, 2026-10-12. This schedules work; it does not promote a model, deploy a service, grant a tool, or waive an approval gate.

Stream A has two work lanes. **Continuous lane:** documentation, code and fixture review, local tests, evidence reconciliation, read-only LAN/health checks and low-impact shared-service observation run whenever useful, including between B60 windows. Continue this lane when an exclusive run is blocked. The Companion natural-session observation belongs here: a signed-in request after time has passed can show refresh, but sign-out/re-sign-in is not refresh evidence. Check only content-free event codes; do not manufacture expiry or send repeated Codex questions.

**Exclusive lane:** deliberate model-call batches, latency/quality comparisons, backend experiments and any activity that occupies the single inference slot or could disturb another B60 experiment. The Aster window begins at **01:00 America/Vancouver**. A candidate must be preflighted beforehand and must finish, including postchecks, by **02:00**; aim to stop new calls by 01:45. This respects the B60 engineering project's 00:30–02:00 disturbance envelope and leaves margin before the 02:30 backup. An Aster test does not displace another active B60 experiment. If occupancy, service health, backup timing, source pins or rollback cannot be confirmed, skip that candidate and continue the continuous lane. No queued test runs merely because the clock reached 01:00.

## Ready-queue contract

Each exclusive candidate has one dated, committed run card with:

1. Question and expected decision value; why shared/offline work cannot answer it.
2. Scope, synthetic/sanitized input, exact runner and version pins, output custody, and any credential-delivery method already authorized. Never print or store a credential.
3. Baseline and frozen score/latency method; maximum requests, tokens, concurrency, elapsed time, and one-attempt/no-retry rule.
4. Service-occupancy, runtime-hash, health, backup and conflicting-experiment preflight; explicit stop conditions and unchanged-production postcheck.
5. Classification as **READY**, **BLOCKED** or **DONE**, with a specific reason. Only READY cards execute at 01:00. A failed preflight changes READY to BLOCKED and produces no model call.
6. Result and limits, raw evidence location/checksum where permitted, local commit, and the separate promotion decision. Never turn a development score into a qualification claim.

Preflight multiple candidates in one continuous-lane pass, but execute serially within the window. Recheck volatile health/occupancy/pins immediately before each candidate. Stop after the first unexpected failure and preserve its partial evidence. Do not rerun an uncertain request. Use existing B60 engineering controls for any backend-changing experiment; Stream A owns assistant-workload evaluation, not the runtime project's promotion decision.

## Current queue, 2026-10-12

| Item | Lane / state | Next action |
|---|---|---|
| Companion natural refresh | Continuous / observing | Quiet four-hour observation; a real refresh plus ordinary-use check can close only this D3 gate. It does not use B60 exclusivity. |
| Gateway and imported-module source reconciliation | Continuous / done locally | Gateway and eight imported modules match production; Lab Operations retains an uninstalled operator-only candidate. Local commits await the normal per-push approval. |
| M1/D4 authority and diagnostic usefulness | Continuous / open | Continue offline/read-only work. No connected Codex tool or worker grant follows without its own gate. |
| M3 low-resource decision contract and replay | Continuous / offline probe rechecked | The [first batched preflight](evidence/Stream-A-cadence-first-preflight-2026-10-12.md) accepted the reconciled gateway source; 30 tests passed. Representative labels and live shadow gates remain open. |
| New 9B/SYCL assistant-workload experiment | Exclusive / BLOCKED | The [first batched preflight](evidence/Stream-A-cadence-first-preflight-2026-10-12.md) found no current run card with a frozen representative corpus, current runner pin, credential-safe execution path and decision threshold. The old 27B/Vulkan sysadmin scores are historical; rerunning them at 01:00 would not answer the next architecture question. Prepare a specific card before scheduling inference. |
| B60 backend benchmarks | B60 engineering project / outside Stream A run queue | Coordinate with that project's own gates and window. Stream A reads accepted results; it does not run a competing benchmark automatically. |

The 01:00 automation checks this queue and performs only READY, bounded tests after live preflight. If none are READY, it records no false test result and uses the window for non-inference Stream A work if useful. The continuous-lane automation resumes work every four hours and stays quiet on unchanged session state. Both operate in this chat and this worktree; neither pushes to Forgejo without immediately current approval.
