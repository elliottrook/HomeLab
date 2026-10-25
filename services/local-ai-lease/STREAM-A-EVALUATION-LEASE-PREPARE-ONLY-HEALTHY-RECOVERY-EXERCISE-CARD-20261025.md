# Stream A prepare-only healthy-lease and recovery exercise

Status: **SOURCE-ONLY; EXERCISE NOT AUTHORIZED OR RUN**

This card defines the next bounded validation after the inactive two-phase
adapter upgrade. It may create a temporary, exact-bound lease and identity
only when separately authorized for execution. It must not quiesce consumers,
arm recurring timers, call a model, alter F2/F3/F4/F5 schedules, or interfere
with the October 26 F2 window.

## Scope and non-goals

- Use a uniquely identified, bounded exercise lease with a fixed short
  deadline and a disposable exercise root; never reuse a production lease ID,
  generation, identity, heartbeat or status file.
- Create and validate only the root-owned identity, owner intent, heartbeat and
  `prepared` lease/lock required to exercise the binding and read-only gates.
- Run the healthy watchdog observation path and prove it is inert: no recovery,
  systemd command, consumer command, timer arm, backend call or model call.
- Force one bounded owner-loss or explicit cancel/recovery path after the
  healthy observation. Recovery must restore the exact four-consumer baseline,
  remove only the exercise state and lock, and leave production unchanged.
- Do not invoke `quiesce`, `post-quiescence`, `start`, `outcome`, model code or
  any workload path. The exercise ends before consumer effects.

## Preconditions — all required, otherwise NO-GO

1. Fresh same-cycle backup/F2/F3/F4/F5 evidence is complete, independently
   reread and outside the exercise's bounded window. The October 26 F2 timers
   and their next-run times are unchanged.
2. The inactive packet and two-phase source pins match the accepted cards:
   implementation commits `2f790b6310981d31358a60fb2a7a3f98f7a26633` and
   `bdf745aa`; corrected card commit `dfeb1374` with card hash
   `5defe13576de09b0435265a99f4156a58c7acf8554a6c14d0af57d21379c1385`.
3. All five F6 units and timers remain disabled/inactive; no runtime lease,
   lock, identity, owner intent, heartbeat or watchdog status is present.
4. Production health, accepted backend/GPU identity and the exact four-consumer
   baseline are independently healthy. No competing evaluation operation or
   lab-exclusive window is active.
5. The exercise host has a pre-created rollback checkpoint and a read-only
   receipt destination. The receipt records hashes, custody, commands and
   results, but contains no secret, recovery share, token or credential.

## Bounded execution sequence — future approval only

1. Capture the prestate: F2 timer identities/next runs, five F6 unit states,
   production health, four-consumer baseline, host GPU holder and absence of
   runtime state. Refuse to proceed on drift.
2. Create the disposable exercise identity and owner intent with a short fixed
   deadline. Do not enable or start recurring units or timers.
3. Invoke the bound prepare-only path with effect authorization. Prove the
   resulting lease has the exact exercise identity/generation, fixed deadlines,
   root custody, `prepared` phase and baseline, while the runner observed zero
   consumer/systemd/model commands.
4. Run the healthy watchdog observation using the exact lease/generation.
   Require `not-attempted`, no recovery callback, unchanged consumer baseline,
   unchanged F2 timers and no model/backend call.
5. Force exactly one bounded recovery case: owner-loss is preferred; an
   explicitly bounded cancel is acceptable only if it exercises the same
   recovery contract. The exercise may not wait into the October 26 F2 window.
6. Require recovery to restore the exact four-consumer baseline, clear only
   the exercise lease/lock and temporary identity/intent, and report success
   only after custody and absence checks pass.
7. Recheck production health, GPU holder, all five F6 unit/timer states and F2
   timer identities/next runs. Write the receipt and stop; never auto-retry.

## Pass/fail evidence

Pass requires all of the following:

- prepare-only created exactly one bound `prepared` lease and no consumer or
  systemd commands;
- healthy watchdog observation was inert;
- owner-loss/cancel recovery restored the exact baseline and cleared the
  exercise state, lock, identity and intent only after validation;
- no consumer, backend, model, timer or schedule changed;
- the October 26 F2 schedule and all F6 units/timers are byte-for-byte/state-
  for-state unchanged.

Any missing, foreign, stale, ambiguous or drifted identity/state is an
immediate NO-GO. A recovery or cleanup error retains the durable evidence and
stops for manual reconciliation; it must not retry or broaden scope.

This card authorizes no execution by itself, no production lease, no consumer
quiescence, no recurring timer arm, no model call and no remote Git operation.
