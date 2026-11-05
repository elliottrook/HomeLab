# SA4 receipt/ledger reconciliation boundary — 2026-11-05

## Result

SA4 now has a source-only reconciler that cross-binds the exact plan,
source-preflight admission, exclusive checkpoint result, already-claimed
one-use ledger record, operation-owner terminal assertion, independently
authenticated postcheck receipt and, when required, independent rollback
receipt.

The operation owner's statement can never establish success. The reconciler
requires the receipt's operation, plan, admission, claim, terminal, target
registration, lock owner and compiled check programs to match byte-for-byte.
Passing postchecks must observe the exact candidate digest and may not carry a
rollback receipt. Any failed or uncertain postcheck requires a separately
authenticated rollback receipt bound to the triggering receipt, retained
checkpoint and compiled rollback program. Missing, stale, duplicated,
misordered or mismatched evidence fails before the ledger is changed.

The committed owner, AI-PAM and observer trust registries remain empty, and
the production target registry remains empty. Even a complete synthetic
postcheck is deliberately not accepted as an effect: its already-used grant is
burned `uncertain`. A failed postcheck with complete independently observed
rollback is burned `failed`; incomplete rollback is burned `uncertain`. No
path reaches `consumed`, success, reuse or retry. Every returned result keeps
`effect_outcome_accepted=false`, `manual_reconciliation_required=true`,
`maximum_effects=0`, `preflight_eligible=false`, automatic routing off and
automatic retry false.

The expanded SA4 suite passes **57/57**. No production target, trust key,
checkpoint, grant claim, repair, rollback, service restart, deployment or route
was created.

## Source identities

- receipt/ledger reconciler:
  `873fa76409bdf819bf9bfc32fa13aec4996929eed658c07d595baf1e464bd820`
- adversarial and cross-binding tests:
  `6bb6a2fdb4479632fe97f0fe90e4c263c2f1950dff0d1e1142fb420ba7f6c166`

## Remaining gate

The generic source-control chain is complete at its deliberately ineligible
boundary. The next work is an evidence-only review of one genuine
low-criticality, no-restart target and the custody design for three separately
controlled real keys. Adding any target or trust anchor is a reviewed source
change. Installing the inactive owners and proposing the first repair are later
gates; the first effect still requires Jason's exact immediate approval.
