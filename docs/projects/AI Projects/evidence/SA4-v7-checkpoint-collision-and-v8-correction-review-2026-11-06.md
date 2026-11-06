# SA4 v7 checkpoint collision and v8 correction review — 2026-11-06

**Result: NO-GO for v7; source correction PASS. No repair effect occurred.**

The v7 transaction stopped during preparation with
`SA4 checkpoint path is not unused`. The target remained exactly
`a9831e62…4da0`, the v4 ledger remained `ready` with `use_count=0`, the v4
evidence directory and observer exchange were empty, and no SA4 process
remained. The exact plan-bound operation lock and emergency-stop files were
retained, as required for an uncertain preparation exception. The whole-host
lease remained `ready`.

The cause is deterministic: v7 correctly used fresh v4 input, evidence and
ledger paths but reused plan ID `sa4-canary-v2-first-repair-v1`. Checkpoints
are named by plan ID, and the retained root-owned mode-0600 original from the
earlier transaction already occupied that exact path. The checkpoint owner
therefore failed closed before creating a checkpoint, claiming the grant,
requesting an observer signature or changing the target.

The source correction adds:

- a narrow pre-claim reconciler that accepts only this exact retained attempt,
  requires the target and retained checkpoint to be byte-identical, requires
  the ledger to remain ready/use-zero and both evidence directories empty,
  proves the exact controls are unheld, writes one content-free receipt, and
  releases only those matching runtime-control files;
- plan v2 with unique plan/checkpoint ID
  `sa4-canary-v2-second-repair-v1`;
- a fourth fresh unsigned authority identity; and
- runner v8 with fresh v5 input/evidence/ledger paths and operation identity.

Focused tests pass 8/8 and the complete SA4 suite passes 322/322. The two-file
create-exclusive inactive-install packet installs only the reconciler and v8
runner. It invokes neither. After exact installation, the next bounded action
is one reconciliation of the retained v7 pre-claim failure, followed by a
fresh v8 release packet. No retry may reuse v7, its plan, grant or state.
