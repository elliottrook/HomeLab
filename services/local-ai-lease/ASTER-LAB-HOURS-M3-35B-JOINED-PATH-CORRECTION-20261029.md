# M3 35B joined-path correction — 2026-10-29

## Observed result

Corrected booking `aster-stream-a-m3-35b-20261029-1915` passed registration,
claim, manifest validation, static preflight and guardian arming. The owner
then failed before the first drain effect because it requested a 3,600-second
lab interval while the shared full-drain contract has an explicit 2,700-second
maximum. The bounded owner traceback identifies
`full-drain budget is outside its bound`.

The outer failure record reported `COMPETING_PROCESS:m3_joint_semantic_35b`
and `production_restored=false`. Those fields were conservative but imprecise:
the owner had already exited before effects, while its expected guardian still
matched the generic quiet-host process marker during failure reconciliation.
Independent postchecks found no drain state, lock, lease, mount or 35B process,
and all production services healthy.

## Correction

- The M3 transaction, runtime preflight and registered workload now share the
  full-drain maximum of 2,700 seconds.
- The minimum booking becomes 3,600 seconds, retaining the separate 900-second
  restoration reserve. Twenty-four 90-second request ceilings plus the bounded
  startup period remain within the transaction deadline.
- After an owner process exits and durable drain state is absent, the reserved
  runner stops and resets its own expected guardian before running the generic
  quiet-host postcheck. It never removes the guardian while durable recovery
  state or lock exists.
- Tests bind the registry, runtime preflight, transaction, guardian deadline
  and safe guardian-settlement behavior through one consistent budget.

The correction changes no model, prompt, threshold, public fixture, result
criteria, recovery commands or automatic-routing state. Installation is an
inactive five-file replacement with exact rollback. It creates no booking and
performs no service stop, mount, restart or model request.
