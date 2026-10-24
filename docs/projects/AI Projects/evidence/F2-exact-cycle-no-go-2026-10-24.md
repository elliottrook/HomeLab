# F2 October 24 exact-cycle result — NO-GO

**Observed:** 2026-10-24 at 01:42 America/Vancouver. **Gate:** F2.  
**Decision:** NO-GO; no retry in this cycle.

## Terminal evidence

The root-owned mode-0600 cycle state is schema
`aster-f2-scheduled.v1`, cycle `2026-10-24`, state `no_go`, with
`first_failure_phase=final` and
`failure_class=FINAL_GUARD_SUBCHECK_FAILED`. It contains no result object and
therefore no archive rows.

The 01:15 preparation service completed successfully with exit status 0 at
01:15:05 PDT. The 01:20 final service exited 1 at 01:20:01. The observer and
`zstd` scanner did not remain running. No cooperative lease state or lock,
application lease lock, F2 receipt, retained archive receipt or source receipt
was present.

The retained class proves that the failure occurred inside the final guard,
before the archive observer produced a result. It does not identify the failed
subcheck. Source inspection at platform commit
`054ada0698d4b35cf99217b1d6fe7bac97ff1cb3` confirms that
`run_fixed_final_guard` exceptions are currently collapsed into the single
`FINAL_GUARD_SUBCHECK_FAILED` class. Naming the clock/window, absence,
exclusion, lease, quiet-process, load, installed-pin or snapshot/freshness
check as the cause would be unsupported.

## Cleanup and postcheck

Under the approved activation rollback, both October 24 exact-date timers were
stopped, disabled and removed, followed by a systemd daemon reload. They now
report not-found/inactive. The recurring F2 timers remain disabled/inactive.

LXC104, LXC110 and LXC116 remained running. Aster Agent, Aster Speech and the
accepted `aster-llama.service` were active; the llama unit hash remained
`a4c75169673a1a230682b73d362a05c1bdd30f7a5c41cfb9c77463204dfd4cb3`.
The News ingest/digest timers and UI, `pvescheduler` and `pvestatd` were also
healthy. Production recovery was not required.

## Consequence and next action

F2 remains open, so F3 and the full-stop drill cannot advance. The platform
owner was notified to prepare a source-only correction that preserves a
bounded code for each final-guard subcheck, then prove it offline and on target
Linux. Do not schedule or rerun F2 from this result. A corrected inactive
installation, fresh exact-cycle card, independent review and new explicit
activation approval are required before another attempt.
