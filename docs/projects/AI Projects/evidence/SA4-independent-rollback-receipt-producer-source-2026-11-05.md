# SA4 independent rollback receipt producer source — 2026-11-05

The independent rollback observer is now source-complete with an intentionally
`unconfigured` host binding. It accepts only the compiled target and validates
the signed failed-or-uncertain postcheck, plan, admission, claimed one-use
grant, retained checkpoint and one-shot rollback-owner terminal before reading
the restored target and checkpoint through stable no-follow descriptors.

This work found and closed a lineage gap in the existing receipt contract: the
signed rollback receipt now includes the exact rollback terminal digest, and
the ledger reconciler requires that digest before it can burn the claim as a
completed rollback. A receipt from a different rollback attempt can no longer
be substituted even if its other target and checkpoint fields match.

The producer reports complete only when the target exactly matches the retained
checkpoint, both files retain their fixed custody, no temporary file remains,
and the compiled inert canary consumer boundary is healthy. It signs nothing
itself and never accepts an effect. Three focused tests cover complete
restoration and validator acceptance, a retained failed observation, and the
inactive host/terminal-drift boundaries. The full SA4 suite passes **118/118**.

No source was installed and no live target, signer, claim, checkpoint, repair
or rollback was used. Next is a joined disposable success-plus-failure
transaction rehearsal across the already frozen components.
