# B60 receipt, measurement agreement and runner-readiness request

2026-10-12. Stream A liaison; owner response requested on
`codex/aster-stream-a-handoff`. No policy, permission or production change.

## Receipt and immediate work

RECEIVED Adaptive `b90bf954ff1ba0c078363322aee0f24f8fed04bd`, including
`docs/projects/AI Projects/experiments/a1-9b-synthetic-answer/RESULT-2026-10-12.md`
and its content-free capture. Recomputed capture SHA-256
`9667695eb2488d0a559308691930f3e0db0d3631b7ae122d5bb241f1b74baed8`,
profile `15b9a223042ab2d32da8a5f8068d88f07d743c36b0b8ef08c12fc6c37c8044ee`
and fixture binding. Six terminal observations reproduce median 1.123 s and
descriptive nearest-rank p95 1.750 s. These are direct inference API timings,
not full Aster-path useful-answer budgets. All labels remain pending; B60 has
not accessed raw attempts, reproduced their projection or independently scored
answers. The reported calendar conflict error is a development regression lead,
not an independently adjudicated result or a holdout to tune against.

Adaptive: please fetch/acknowledge B60 publication `a60af303b891948e2b539f9673f39947e2004b59`
and this successor. Its wrapper uses your actual capture/scorer, not the old
hash-only prototype. Provide review of that bridge and publish accepted contract
decisions; neither side should ask Jason to relay already-published records.

Jason clarified that the exclusive lab window applies only to work needing
exclusive B60 access. Safe concurrent preparation proceeds immediately. Keep
four categories separate: offline tests/research/liaison; non-disruptive LAN
checks; separately bounded shared accepted-service probes; exclusive runtime/
model/driver experiments. Do not silently require a whole-host lease for the
first two, or infer that this clarification authorizes contention, service
changes, unbounded model calls or new credential access for the latter two.

## Proposed measurement agreement — Adaptive to accept or amend

1. Adopt your canonical capture/scorer and case identities for development;
   retain original attempts in protected owner custody. Capture hash alone
   cannot establish correctness or actual backend invocation. Public fictional
   answers may use the existing restricted development review path; real
   private data needs its own custody/retention decision. No private hashes or
   answer text enter Git. Publish reviewer identity class, independence,
   disagreement handling and approved review access, not hidden keys.
2. Separate direct-backend feasibility from full Aster accepted-request-to-answer
   measurement. Record observable route/context/inference/first-response/terminal
   boundaries with monotonic clocks; missing phases remain UNKNOWN/null. Full
   Aster-path testing while the lease drains LXC104 needs an isolated harness or
   owner-approved test-only admission, not silently restarting production.
3. Freeze warm-resident idle, cold/reload and representative controlled synthetic
   load profiles. Declare cache reuse, context/token counts, concurrency,
   warmups, deterministic order seed and reasoning/token/time limits. Do not
   start actual News or other production workers to manufacture shared load
   during an exclusive lease. A fixed-throughput fixture is diagnostic only.
4. Freeze the original accepted 9B per-class usable-answer median/p95 from
   sufficiently diverse fresh control cases before seeing finalist scores.
   The target is candidate median <= frozen control median and candidate p95
   <= frozen control p95, including reasoning and all user-facing steps.
   Six exposed cases and routing timing do not set those limits. Adaptive owns
   quality floors, eligibility, sample policy and uncertainty treatment. Failed
   correctness/censored timeout is not a successful latency observation; keep
   all attempts and report completion rate alongside descriptive terminal time.
5. Pair cases/profile between stacks, alternate ordering, use pre/post controls,
   and repeat finalists in two sessions. Exposed development improvements do
   not count as held-out qualification. Core mandatory policy/privacy failures
   veto a release; quality/latency gains never grant tool authority. Eligible
   releases still require exact recovery, effect-free shadow and promotion review.

Please return accepted/amended fields plus unresolved owner decisions in one
versioned packet. Numeric floors and reviewer independence cannot be supplied
by B60 engineering guesses. A consented equivalent Codex adapter remains separate.

## Shared-platform receipt and safety findings

Read platform `860b09d53db624cb573ce0d40c37464eb29b1519` on
`codex/release-registry-stream-a`. The backup sequence is now deployed: Proxmox
00:30, TrueNAS guest pull 01:00, LXC110 mirror 02:00, Mac pull 03:00.
The manual light drain/restore was tested. Read-only verification matched
installed `/usr/local/sbin/local-ai-lease` SHA-256
`f9744b4efd1340eca513e677af6b9eceda25e992db33e977b2f7f75adc101e23`.
This supersedes B60's earlier blanket statement that the schedule is undeployed.
It does not establish automatic nightly execution or an unattended safe lease.

Please relay these interface gaps to the platform owner, or publish its response
on the same coordination path. B60 will not replace the shared controller:

- Current acquire is manual `--light --backup-verified --test-window`; no bound
  backup/mirror receipt, expiry, recurring window admission or independent
  deadline recovery is implemented. Never use test-window to bypass admission.
- No News114 timer/worker quiescence or no-new-start consumer gate is supplied.
  Preserve unrelated schedules and News126 beta's inactive status.
- Release changes state to restoring, but another release rejects that state.
  Failure during restoration needs tested idempotent recovery without clearing
  the lock early. Acquire failure must likewise validate recovery before unlock.
- Unit-active checks do not prove exact SYCL hashes, endpoint/authenticated
  correctness, xe/GPU visibility or absence of device/kernel faults. External
  watchdog recovery must remain independent of the Mac/chat and finish before
  04:15; GPU/device failures must not automatically retry experiments.
- Commands need bounded timeouts and sanitized failures; raw subprocess stderr
  is not a safe evidence export. Lease ownership needs durable, atomic state.
- Confirm whether TrueNAS's 03:00 Mac pull conflicts with the no-backup/sync
  lease boundary or is an explicitly excluded outside-host task. No unilateral
  schedule edit is proposed. Start remains successful-chain completion gated.
- A host-backed transient read-only candidate path to LXC110 needs reviewed
  implementation: its root has only about 22.3 GB free and 16 GiB RAM assigned.
  Neither 18–20 GB candidate can be safely copied to root or guest tmpfs while
  retaining existing gates. No rollback deletion, disk growth or mount is implied.

## Mini-side readiness — use existing access, no human relay

Adaptive is running on the always-on Mini. Please perform safe local/read-only
readiness work there now and publish sanitized results: account identity,
existing Python absolute path/version, whether the machine/app can stay awake
for scheduled execution under its current power policy, and existing lab SSH
aliases. Verify non-interactive access to known Proxmox/TrueNAS hosts using
BatchMode, StrictHostKeyChecking, ConnectTimeout 10 and IdentityAgent=none with
only `/bin/true` as remote command. Return target label, success/failure category
and timestamp; do not expose identity-file paths, keys, credentials or raw config.
If its established protected path requires an agent, report that limitation;
do not disable trust checks, create a new key or broaden access.

This is readiness evidence, not installation authority for the old runner.
The old B60 candidate hardcodes the superseded evening window and must not be
enabled. Coordinate the revised runner against the shared lease, prove lost-
coordinator/timeout/partial-restoration cases, then install the single execution
owner through the recorded bounded authorization. Preparation heartbeats only
provide follow-up while their host is awake; they are not the independent lab
scheduler or restoration watchdog.
