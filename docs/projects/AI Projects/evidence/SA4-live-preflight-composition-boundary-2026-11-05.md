# SA4 live-preflight composition boundary — 2026-11-05

## Outcome

The SA4 preflight now has a separate production composition path. It accepts
only fresh authenticated owner and AI-PAM authority, a registered production
target, a stable live measurement, the matching exclusive checkpoint-owner
record, a ready unused one-use ledger entry, the held shared operation lock,
and an armed emergency stop.

The older synthetic composition remains available only for isolated schema
and contract tests. Its `source-complete-pending-real-trust-and-live-measurement`
status is no longer accepted by the final effect-admission or receipt/ledger
reconciliation boundaries. Only the new
`live-measurement-checkpoint-complete` status can flow toward a one-effect
admission.

## Fail-closed bindings

- plan, approval, approval proof, grant and grant proof;
- registered production target and expected pre-repair digest;
- exact live-measurement digest and target snapshot;
- exact checkpoint-owner digest, checkpoint digest and same-filesystem proof;
- ready, unused and unexpired one-use ledger record;
- held shared-operation lock owned by the plan;
- armed emergency stop owned by the plan;
- automatic retry disabled and automatic routing off.

The live composition still authorizes zero effects. It reports
`preflight_eligible=false`, `maximum_effects=0`, and requires the later exact
owner effect approval and final effect-admission record.

## Verification

- focused live-composition tests: 7/7 pass;
- effect-admission tests: 3/3 pass;
- receipt/ledger reconciler tests: 6/6 pass;
- joined full-transaction rehearsal tests: 2/2 pass;
- complete SA4 suite: 134/134 pass;
- whitespace/error check: pass.

No host mutation, key access, signature, ledger claim, checkpoint creation,
target write, service action, booking, schedule, model call or routing change
occurred. The already-installed transaction files remain at their recorded
installation hashes; this source milestone does not claim they were upgraded.

## Next gate

Build and rehearse a single fail-closed root transaction owner that sequences
the already-separated authority, measurement, checkpoint, ledger,
effect-admission, repair, independent receipt, rollback and terminal
reconciliation components. The first real repair remains an immediate exact
approval gate.
