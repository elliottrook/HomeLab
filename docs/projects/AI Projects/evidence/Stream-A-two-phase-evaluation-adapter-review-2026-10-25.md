# Stream A two-phase evaluation adapter review — 2026-10-25

> Decision: **NO-GO; durable quiescence ordering correction required**

Platform source commit `2f790b6310981d31358a60fb2a7a3f98f7a26633`
separates durable lease preparation from consumer quiescence. Independent
clean-archive execution passed 36/36 focused evaluation-lease tests and left no
bytecode. The reviewed source hashes are:

- `evaluation_lease.py`:
  `e79c74035acf22222105b4a8cdcc00f75608bf2289732b4cba9a625252fe45b2`;
- `evaluation_lease_adapter.py`:
  `8f3c4f54015d5c7606f0ec82d48a09a8463f0aba358a11b7347d498f3195a5ec`;
- `evaluation_lease_entrypoint.py`:
  `7425ffe9bd6c8b70c41fe3856343a0454d726e54d0f0531cd7ce7225118a332c`.

The compatibility `acquire` API and entrypoint phase now perform prepare only,
with no consumer command. The explicit `quiesce` phase is required before
post-quiescence, so the legacy acquire→post sequence cannot bypass the new
boundary.

## First failed boundary

`quiesce()` executes every mask/stop command while the durable lease remains in
`PREPARED`, then writes `QUIESCING` only after the entire loop succeeds. A
process or host failure during that loop may therefore leave some consumers
stopped while the durable state still represents the no-effect phase. The
focused suite has no partial-quiescence failure/recovery test and no clean
prepared-state recovery test.

The correction must atomically persist `QUIESCING` with the exact lease,
generation and fresh heartbeat before the first consumer command. A synthetic
mid-loop failure must retain that recoverable phase, and recovery must restore
the exact four-consumer baseline and clear state/lock only after the existing
post-restore validation succeeds. A separate prepared-state recovery/cancel
test must also preserve production state and remove the lease safely.

Nothing from this candidate was installed or invoked. The currently installed
inactive contract/adapter/entrypoint and watchdog packet are unchanged. F6
arming, lease preparation, consumer quiescence and D4/M3 remain NO-GO; the
October 26 F2 test remains independent.
