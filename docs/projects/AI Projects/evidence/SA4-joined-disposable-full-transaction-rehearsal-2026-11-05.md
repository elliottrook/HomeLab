# SA4 joined disposable full-transaction rehearsal — 2026-11-05

The complete SA4 repair chain has now run in a disposable filesystem on both
terminal branches using the actual frozen components rather than isolated
shape fixtures. Each transaction performs read-only measurement, exclusive
checkpoint creation, durable one-use grant initialization and claim, one
atomic replacement, independent postcheck production and signature, and
terminal ledger reconciliation. The failure branch additionally performs one
atomic checkpoint restoration, an independent signed rollback observation and
a failed terminal burn. Neither branch retries.

The rehearsal exposed a deterministic integration defect before any live
effect: the reconciler treated the earlier zero-effect source preflight and
the final one-effect admission as if they were the same record. They are
deliberately different. The reconciler now accepts and independently validates
both, binds the operation/postcheck/rollback lineage to the final effect
admission, and retains the source preflight as a separate digest in terminal
evidence.

Measured results:

- success branch: one replacement, three independent postchecks passed, no
  rollback, the exact healthy candidate remained, and the one-use claim was
  terminally burned uncertain for manual reconciliation;
- failure branch: one replacement produced bounded failed postchecks, one
  rollback restored the exact checkpoint, independent rollback evidence
  completed, and the one-use claim was terminally burned failed;
- both branches retained evidence, accepted no effect outcome, performed zero
  retries and left no temporary file.

The full SA4 suite passes **120/120**. All host bindings exercised by the
rehearsal were temporary test patches; the committed repair, rollback and
observer producers remain `unconfigured`. No source was installed and no live
target, key, grant, checkpoint, repair or rollback was used.

The source chain is now ready for a reviewed inactive installation packet and
live dry preflight. The first real repair effect remains an exact immediate
approval gate.
