# Stream A two-phase evaluation adapter review — 2026-10-25

> Decision: **CORRECTED AND INSTALLED INACTIVE; live effects remain closed**

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
The platform owner integrated the correction at `bdf745aa` and committed the
corrected four-path card at metadata commit `dfeb1374` (card SHA-256
`5defe13576de09b0435265a99f4156a58c7acf8554a6c14d0af57d21379c1385`).

## Inactive installation result

Jason approved the exact inactive upgrade on October 25. The complete review
packet SHA-256 was
`19d5a7a9ba8865ccae358fac880668403558dba8a60b4c6ae2ef381d87b8995b`;
it includes the wrapper dependencies omitted from the first local review
archive and passes 39/39 clean-archive tests without bytecode.

The transaction revalidated all four old live hashes, created the root-only
checkpoint `/root/stream-a-evaluation-two-phase-20261025`, and atomically
installed the four card-pinned files. Target-Linux tests passed 39/39, installed
imports passed, and the existing wrapper returned the exact inert
`source-only` result without reading an intent. Independent postcheck matched
all four new hashes and root:root mode 0644. The five evaluation services and
timers remained disabled/inactive, all lease/lock/identity/intent/heartbeat/
status files remained absent, LXC104/110/116 and their production services
remained running, and pvescheduler/pvestatd remained active. The October 26 F2
exact-date timers remained enabled for 01:15 and 01:20 PDT.

This closes only the inactive two-phase adapter installation. It does not arm
F6, prepare a lease, quiesce consumers, call a model, or authorize D4/M3. The
next bounded gate is a reviewed prepare-only healthy-lease/recovery exercise
that proves watchdog observation and exact cleanup before any consumer effect.

## Prepared cancellation follow-up

Independent review of the platform owner's first prepare-only exercise card at
`568f8743` found that the installed `PREPARED` recovery path still issued the
eight normal consumer restore commands. That contradicted the proposed
pre-effect exercise's zero-consumer-command boundary. Requiring fresh F2–F5
evidence before proving this pre-effect behavior was also circular; those
fresh-cycle gates remain mandatory before quiescence, not before a disposable
prepare/cancel proof.

Stream A corrected the isolated source at commit
`440c62513e2fe41ba40066b391fe67a715b9c939`. Recovery-authorized cancellation
from exact `PREPARED` state now validates the unchanged baseline, backend,
authentication, idle state and accepted GPU holder, then clears the lease and
lock without invoking the runner. Invalid observations retain state and lock,
and a caller without recovery authority cannot cancel. The focused clean suite
passes 41/41 with no bytecode. The adapter SHA-256 is
`db9c368707f4203d96725a06012adba808d8c425d42b1c25d19e7837052ce7cc`;
the test SHA-256 is
`ea64876ebc4248768038074bba10293ade2f45b8b9c62f6b6872ddd310b91ff7`.
Nothing from this follow-up is installed. Platform integration, a corrected
hash-pinned inactive upgrade card and independent prestate review remain the
next steps.

### Prepared-cancel inactive installation

The platform owner integrated the correction as `2f59c2b0` and pinned the
one-file transaction in metadata commit `fcc40a37` (card SHA-256
`738a4920c2969c3f040c699a67237d4841bb3ad4258e1d625f7c4fd01fed26bc`).
Jason approved the exact inactive upgrade. The complete source/test packet
SHA-256 was
`446d1bb22a5b4a34be1b0f4e3f7161f32cc1a769493470ff9a1956e153dca6ee`.

The target transaction matched the old adapter prehash, retained a root-only
mode-0600 rollback file under
`/root/stream-a-evaluation-prepared-cancel-20261025`, installed only the new
adapter at root:root mode 0644, and passed 41/41 target-Linux tests plus
installed imports. Independent postcheck matched adapter SHA-256
`db9c368707f4203d96725a06012adba808d8c425d42b1c25d19e7837052ce7cc`.
All five F6 units/timers remained disabled/inactive; lease, lock, operation
lock, identity, intent, heartbeat, status and restore-intent paths remained
absent. Production guests/services, pvescheduler and pvestatd remained healthy,
and the October 26 F2 timers remained scheduled for 01:15/01:20 PDT.

This closes the prepared-cancel source/install dependency. Review of the first
live exercise card then found that every installed owner/heartbeat/watchdog
unit has `RefuseManualStart=yes`, while the exercise correctly forbids arming
its recurring timers. A direct owner-wrapper launch cannot pass the identity
binding because its process is not in the hard-coded owner service cgroup. The
exercise therefore remains NO-GO pending a bounded authentic owner-launch path
and a corrected exact card; no exercise state was created.

## Fixed transient exercise-owner candidate

The initial prepare-only card could not launch an authentic owner without
arming a recurring timer: all installed candidate units have
`RefuseManualStart=yes`, while direct wrapper execution is outside the expected
owner-service cgroup. Stream A closed the source gap in isolated commits
`7374a60b` and `af803abd`, integrated by the platform owner as `b971f2a6` and
`00046b25`.

The owner accepts only the fixed
`stream-a-evaluation-exercise-owner.service` transient identity, verifies its
PID/boot/start-time/cmdline/cgroup before writing identity, and rejects direct
SSH or caller-selected unit names. A new inert-by-default launcher pins the
fixed unit, root user, `NoNewPrivileges`, strict system/home/tmp protections,
exact two writable directories and all required owner flags. The clean packet
passes 41 lease tests plus 23 owner/watchdog/observer/launcher tests. Its
SHA-256 is
`7e5303f426f567f3ea70a66e61ab7c57b28ddf9f5d2588b9b8c4e0af6abc7fba`.

The corrected two-file inactive card is platform metadata commit `5a3f8fa6`,
SHA-256 `e6084fc68a322211a7b0d8cf8f4193bb36b385bd37999d385af993f8ae985099`.
The corrected later exercise card SHA-256 is
`30462aa3b49242fb18e718327e667223832c68884a75a831c06254125eaf5c44`.
Live prestate matched the pinned old owner hash and absent launcher; all runtime
state was absent before installation.

### Exercise-owner inactive installation

Jason approved the exact two-file inactive installation. The complete packet
SHA-256 was
`7e5303f426f567f3ea70a66e61ab7c57b28ddf9f5d2588b9b8c4e0af6abc7fba`
and the bounded installer SHA-256 was
`0165a21d300a4730f81677f382afee0846bf3738d25d2a02ea49c2744cdf6759`.
The transaction created root-only rollback checkpoint
`/root/stream-a-evaluation-exercise-owner-20261025`, installed the owner at
SHA-256 `74c8072793cbbcc68e40d0548065f55031c2b8e5bfeab3d9583069aa4c8a22a1`
with root:root mode 0644, and installed the fixed launcher at SHA-256
`0d84d35300202c5d9316cc38a853402f7c252aab0ec5069f0b759dd3f3157d22`
with root:root mode 0755.

Target Linux validation passed all 41 lease tests and all 23
owner/watchdog/observer/launcher tests. Installed imports passed. No evaluation
runtime state was created and no transient or persistent unit was activated.
All five F6 services and timers remained disabled/inactive, production guests
and services remained healthy, and the October 26 F2 timers remained unchanged
at 01:15 and 01:20 PDT.

This closes the inactive owner-launch dependency only. The live exercise is
still a distinct gate. Review of the exercise procedure found that the normal
production admission schema requires retained-receipt identifiers and the
production 75/90-minute deadline pair. A disposable pre-effect exercise must
not satisfy those fields with values that could be mistaken for real evidence.
The next source gate is therefore a dedicated exercise-only admission path that
cannot quiesce consumers, cannot start a workload and cannot be promoted into a
production lease.
