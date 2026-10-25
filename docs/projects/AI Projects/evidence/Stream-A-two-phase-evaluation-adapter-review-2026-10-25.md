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

## Failed boundaries

`quiesce()` executes every mask/stop command while the durable lease remains in
`PREPARED`, then writes `QUIESCING` only after the entire loop succeeds. A
process or host failure during that loop may therefore leave some consumers
stopped while the durable state still represents the no-effect phase. The
focused suite has no partial-quiescence failure/recovery test and no clean
prepared-state recovery test.

The companion watchdog decoder also still accepts only `QUIESCING`, `RUNNING`
and `RESTORING`. It rejects the newly introduced `PREPARED` state before the
deadline decision. A prepared lease therefore cannot pass the intended
healthy-lease check and cannot reach deadline- or owner-loss recovery.

The correction must atomically persist `QUIESCING` with the exact lease,
generation and fresh heartbeat before the first consumer command. A synthetic
mid-loop failure must retain that recoverable phase, and recovery must restore
the exact four-consumer baseline and clear state/lock only after the existing
post-restore validation succeeds. A separate prepared-state recovery/cancel
test must also preserve production state and remove the lease safely. The
watchdog input contract must accept exact-identity `PREPARED` state under the
same fixed deadline constraints, remain inert while its heartbeat/owner are
healthy, and recover it on owner loss or deadline expiry.

Nothing from this candidate was installed or invoked. The currently installed
inactive contract/adapter/entrypoint and watchdog packet are unchanged. F6
arming, lease preparation, consumer quiescence and D4/M3 remain NO-GO; the
October 26 F2 test remains independent.

## Corrected source candidate

Stream A implemented the bounded correction in an isolated worktree at commit
`d2e296eefaf4ea0ab6abe22ef0b65a0b41b59faa`, based directly on the platform
owner's `2f790b63` split. It:

- persists `QUIESCING` before the first mask/stop command;
- retains that phase after a synthetic mid-loop failure;
- proves recovery restores the four-target baseline and clears state/lock only
  after validation;
- covers clean `PREPARED` recovery;
- admits exact `PREPARED` state to the bound watchdog; and
- proves healthy prepared state is inert while owner loss and the hard deadline
  invoke recovery.

A second clean-archive run passes 39/39 focused tests with no bytecode. The
runtime hashes are contract
`e79c74035acf22222105b4a8cdcc00f75608bf2289732b4cba9a625252fe45b2`,
adapter `304edaf3c2f247ac874b333331ee0098ac41d2776877c3ee51431152c294c877`,
watchdog `68f261c65f48443a7d7c2115ad0017a5de6f5866f9693143a53375e10d7a585f`
and entrypoint
`7425ffe9bd6c8b70c41fe3856343a0454d726e54d0f0531cd7ce7225118a332c`.
The platform owner has been given the local commit for integration and a
hash-pinned inactive upgrade card. Nothing is installed from this correction;
the install gate remains closed until that card is committed and independently
checked against the live prestate.
