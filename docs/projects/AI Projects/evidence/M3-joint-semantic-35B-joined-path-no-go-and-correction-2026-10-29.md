# M3 joint-semantic 35B joined-path NO-GO and correction — 2026-10-29

## Measured result

Booking `aster-stream-a-m3-35b-20261029-1915` passed claim, exact installed
manifest validation, static preflight and guardian arming. The owner exited
before its first drain command because the M3 transaction requested 3,600
seconds while the shared full-drain contract permits at most 2,700 seconds.
The owner traceback records `full-drain budget is outside its bound`.

The outer terminal then reported phase `owner-transaction`, code
`COMPETING_PROCESS:m3_joint_semantic_35b` and
`production_restored=false`. This was conservative but imprecise: the expected
M3 guardian matched the generic process marker during failure reconciliation.
Independent postchecks prove no drain state or lock, lease, model mount, 35B
process or changed production service. No public case ran and no score exists.

## Corrected installed baseline

Platform commit `309ce983` makes the registry, runtime preflight, transaction
and guardian use one 2,700-second budget, with a 3,600-second minimum booking
and separate 900-second recovery reserve. The reserved runner now removes its
own expected guardian from the quiet-host postcheck only after durable drain
state and lock are absent. Joined-path regressions cover both defects.

The five-file correction is installed inactive. All 32 release pins, joined
imports and budget assertions pass; Lab Hours Doctor and production services
are healthy; rollback is retained at
`/var/lib/local-ai-lab/checkpoints/m3-joined-309ce983`. The spent booking was
not retried or rescheduled. Automatic routing remains off and holdout custody
is unchanged.
