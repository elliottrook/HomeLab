# November 6 nightly reconciliation and candidate recovery composition

The delayed heartbeat arrived at 08:28 Vancouver, outside the booked overnight
window. No experiment was started or replayed. R3 normal, R4 independent
owner-loss and R5 bounded synthetic-resource recovery remain qualified and
spent, as recorded in the November 5 immutable results. Their passes do not
qualify the staged 35B model, its persistent mapping or its VRAM needs.

## Current observations and authority

Fetched and read both liaison branches and the platform registry. No new peer
reply appeared. The existing coordination publication ee955ce1466d748eed7f0527a4e618aed3b045cd
matches the GitHub protection ref over verified HTTPS. This nightly commit is
local only; publication does not establish peer reading. Registry/manual-light
lease prose predates the B60 live passes; do not describe all recovery work as
undeployed. The accepted no-model profile still refuses model experiments.

Minimal Proxmox control-plane metadata at epoch 1793979051 found lease.json,
lease.lock, full-inference-drain.json, full-inference-drain.lock and the shared
operation marker absent. This is marker evidence only, not an authenticated
same-cycle backup, resource, GPU, health, consumer-drain or admission proof.
No guest, GPU, model or production-service probe followed that metadata check.

## Implementation advanced, with live boundary retained

Added an undeployed candidate recovery composition core under scripts/b60-inference.
It binds exact candidate command bytes, booking, production entry and private
custody checkpoint digests. Owner and guardian must share that binding and a
durable source-local journal. Every cleanup intent must be persisted before its
effect. Re-entry observes current state; an absent candidate mount after a crash
is handled without repeating its removal. Unknown mounts are retained.

The enforced order is recovery admission, candidate whole-scope fence, empty
scope verification, exact declared mount removal/absence, checkpointed staging
custody restoration and verification, then base entry restoration and verification.
The base production mount identity check is retained. Failure prevents later
steps; the core never releases shared exclusion or claims a model result.
Even a completed re-entry fences and verifies again. It contains no production
backend, subprocess/network endpoint, installer, activation or deployment.

Nine synthetic tests cover the ordering, each pre-restore failure, foreign mount,
intent-write failures, crash after removal before phase write, completed re-entry,
four binding drifts, base restoration/verification failure and invalid identities.
All 133 B60 tests pass using the exact pinned controller dependency root
/private/tmp/b60-resource-checkpoint-20261104/scripts/local-ai. This is offline
failure-path evidence, not a live guardian, mount or resource qualification.

## Next concrete action

Implement the fixed source-local model/mount/custody/resource backend and bind
this composition to both the qualified owner adapter and its independent guardian.
Review guest stop/start and mount lifecycle against all five entry checkpoints;
unknown or partial custody must retain the exclusion for exact recovery. Complete
artifact license/revision/hash/headroom observers, bounded capture and strict
activation schema before installing a candidate release. The deployed
experiment=null guard remains untouched. No new conversational approval is missing.

Rank 1 remains the staged Qwen3.6-35B-A3B reasoning-on two-request compatibility
screen on accepted SYCL, one 8K slot, speculation off, 60 seconds per request,
no retries, within a fresh booked admitted lab window. It is not the 24-case
private packet or final quality/p50/p95 acceptance. Graph/runtime diagnostics
remain later. Freeze fresh accepted 9B complete-useful-answer baseline and harder
held-out contract before tuning. The published sampling/session question does
not prevent this independent implementation work or justify inventing budgets.

No model run, download, mount, service/timer/configuration change, lease,
credential operation, driver/package/boot change or Git push occurred. No new
qualification or promotion is claimed. The expanded programme remains active;
no sleeping/background execution is implied.

## Exact read receipts

| Commit | Path | SHA256 |
|---|---|---|
| 70832267c59b1e9a6b809ec08ff1af1157c0c8e1 | docs/projects/AI Projects/evidence/B60-first-screen-enforcement-source-reconciliation-2026-10-26.md | 9c47499ffa6fb283f92f4c45aaa2d81212544b6b121b4e32e00948225fa6e45f |
| ee955ce1466d748eed7f0527a4e618aed3b045cd | docs/projects/B60-Inference-Engineering/fixed-candidate-command-preparation-20261106.md | d05c6e430ddd1f293c101d928412e302f3dec9f0a39060323de197fa97324d83 |
| 6fb0207fec5190e0c34ed3bc72ea38e128f06127 | docs/projects/Local-AI-Platform-Split.md | 6bd3106078315a80046a6f917646410698df6a73f6e34c219b32272ce9f935d7 |
| 6fb0207fec5190e0c34ed3bc72ea38e128f06127 | docs/service-release-registry.md | d93de63ad79e3980568335b485b0713041f43bdf7e36f3f46f584de9c5b060d8 |
