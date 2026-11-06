# SA4 distinct-registry call-graph correction review — 2026-11-06

**Decision: source-complete; inactive installation is the next gate. No repair is authorized.**

Reviewing the fresh distinct-target release before creating authority found a
deterministic fail-closed defect. The installed v3 owner changed only its direct
registry resolver. The shared plan validator and downstream measurement,
checkpoint, admission, repair, postcheck, rollback and reconciliation modules
remained pinned to registry v1, so a v2-target plan would be rejected before an
effect. No authority, signature, ledger, checkpoint or repair was attempted.

The source-only correction binds every registry consumer as one context for
exactly `sa4-lxc104-canary-adapter-v2`, validates the complete plan while bound,
and restores every predecessor module to registry v1 in `finally`. A v4 owner
wraps every target-sensitive phase; a no-argument v4 runner wraps the installed
v3 entry point with that owner. Other targets fail closed.

Focused regression proves that v1 rejects the distinct plan, the complete v2
binding accepts it, all globals restore to v1 afterward, the owner reaches the
candidate digest gate, and the final runner rejects arguments. The complete SA4
suite passes 266/266. The reviewed three-file create-exclusive inactive-install
plan binds 16 exact installed dependencies, the predecessor install result and
the unchanged drifted canary. It excludes signing, authority, a ledger claim,
checkpoint, repair, service action, routing and promotion.

