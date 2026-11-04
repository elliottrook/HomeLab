# Stream A standing authority and agent limits — 2026-11-04

## Why continuation repeatedly stopped

The agent incorrectly treated project run cards and internal effect decisions
as repeated conversational permission gates even after Stream A was approved.
It also treated scheduling or committing one checkpoint as an end condition
instead of selecting the next independent ready item. Four-hour heartbeats
made that error visible: once a turn ended, the chat agent did not continue
until another user message or heartbeat, although host timers continued.

Sandbox prompts added confusion. A managed sandbox may require an escalation
for linked-worktree Git metadata, private evidence directories, remote pushes
or host mutations even when Jason has already granted project authority. Those
are product-enforced execution checks, not new project decisions, and must not
be presented as uncertainty about Stream A.

## Standing authority now recorded

Within the recorded Stream A scope, Jason authorizes routine read-only checks,
local source/evidence work, tests and commits; candidate registration, Lab Hours
booking and bounded candidate execution; fixed stop/restoration of declared
production consumers; reversible inactive corrections after spent attempts;
and a Forgejo push at each completed milestone after remote-head fast-forward
precheck and followed by read-only GitHub mirror verification.

These actions proceed without another conversational approval. Internal cards
are technical proof and rollback boundaries, not owner prompts.

## Controls that still cannot be waived

The agent must still stop or use the platform's required approval mechanism for
destructive or irreversible loss, credential exposure/rotation, public ingress,
weakened authentication/encryption/backup/isolation, materially different
scope, production model/backend replacement, new access, unrelated deployment,
security/trust expansion, force push, history rewrite, remote deletion,
tag/release/PR/workflow changes, direct GitHub push, or an unsafe failed
recovery prerequisite. A platform/sandbox escalation prompt also remains a
technical control even where project authority already exists.

Lab Hours rules remain mandatory: query the authoritative ledger before every
schedule, use only registered hash-pinned workloads, and require the atomic
booking claim, whole-host lease and shared operation lock. Runtime drift fails
closed without retry, but should lead directly to evidence, deterministic
correction and the next independent task.

## Product limitation

The chat agent is not a continuously running daemon. Work happens during an
active turn and resumes on user input or a configured heartbeat. Host-side
dispatchers/timers can continue independently and retain terminal evidence.
Every turn must therefore advance multiple ready items, persist state, and
leave timed work with an authoritative host owner rather than relying on the
chat remaining open.
