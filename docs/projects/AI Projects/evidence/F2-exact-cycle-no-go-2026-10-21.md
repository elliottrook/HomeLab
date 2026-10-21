# F2 exact-cycle NO-GO — 2026-10-21

## Classification

- **VERIFIED CURRENT STATE:** the one-shot prepare phase started at 01:15 PDT
  and recorded `state=no_go`, `first_failure_phase=prepare`,
  `failure_class=PREFLIGHT_FAILED`. The final phase failed closed at 01:20.
  No archive-result rows, scan process, lease, lock or F2 receipt existed.
- **VERIFIED CURRENT STATE:** the current-cycle 104/110/116 Proxmox archives
  exist. TrueNAS task 1 completed successfully at 01:06 PDT, but its fixed
  include list excludes LXC110. LXC110 is copied by task 3 at 02:00, and the
  October 21 LXC110 archive was therefore absent from the fixed mirror at the
  01:15 preflight.
- **VERIFIED SOURCE MISMATCH:** the installed source pinned by commit
  `16e24548fc3dde996d2744a97ee37836ff7ecf51` required that future 02:00
  LXC110 mirror during the 01:15 preflight. Its coordinator also invoked the
  final path at 01:20 while the pinned final guard, observer and producer
  accepted starts only from 01:10 through 01:19.
- **ARCHITECTURAL INFERENCE:** the mirror dependency is sufficient to explain
  the prepare failure. Even with that dependency removed, the independent
  01:20/start-window mismatch would have made this exact release fail closed
  before archive scanning.

## Bounded result

The result is **F2 NO-GO**. No integrity timing result was produced and F3
cannot advance. Production remained normal: Aster Agent, accepted llama.cpp,
Speech, News, `pvescheduler` and `pvestatd` were active; the lease controller
reported ready.

The approved rollback was completed after observation. The two October 21
timer units were stopped, disabled and removed, systemd was reloaded, and the
daily F2 timers remain disabled/inactive. The terminal state and failed helper
service evidence were retained. There was no retry.

## Required correction

Do not merely schedule the same source again. A replacement must use one
internally consistent dependency/window design and test all cooperating
components at their actual installed paths. At minimum it must:

1. make the preflight's backup dependencies match the fixed TrueNAS schedule;
2. align coordinator, final guard, observer, producer and hard deadline to one
   exact window;
3. preserve single-attempt and first-failure evidence;
4. pass target-Linux synthetic tests and a no-effect inactive install; and
5. receive a new exact one-cycle activation approval.

The platform owner was notified with the bounded failure and asked to prepare
the smallest tested correction. No deployment, new schedule, F3 receipt,
lease, service stop, model call or automatic retry is authorized by this note.

## Superseding inactive candidate

The platform owner produced a combined source-only candidate at commit
`223d4a18855e1085dce180a2c842fef926d1d1b8`. Stream A rejected its first
three-file draft because the wrapper and observer still pinned the old
transitive hashes. The superseding four-file card closes that dependency
chain: snapshot, fixed wrapper, observer and disabled producer now agree on
the 01:15/01:20/01:40 window and on one another's hashes. The platform suite
passed 357 tests with eight expected platform skips. The reviewed card is
`services/local-ai-lease/F2-FINAL-MINUTE-CONSISTENCY-INACTIVE-INSTALL-CARD-20261021.md`
with SHA-256 `4d76d247f27d91eefd258d7fc783c73228fb1d501e0fa4bf130f36fab861b672`.

This is still source-only. A bounded four-file inactive installation and
target-Linux dependency-closure check require the next approval; a future
timer activation remains a separate decision.
