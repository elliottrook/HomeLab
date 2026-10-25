# Stream A prepare-only healthy-lease and recovery exercise

Status: **SOURCE-ONLY; EXERCISE NOT AUTHORIZED OR RUN**

This card defines the next bounded validation after the inactive two-phase
adapter and exercise-admission upgrades. It may create a temporary,
exact-bound exercise lease and identity
only when separately authorized for execution. It must not quiesce consumers,
arm recurring timers, call a model, alter F2/F3/F4/F5 schedules, or interfere
with the October 26 F2 window.

## Scope and non-goals

- Use a uniquely identified, bounded exercise lease with a fixed short
  deadline and a disposable exercise root; never reuse a production lease ID,
  generation, identity, heartbeat or status file.
- Create and validate only the root-owned exercise identity, owner intent,
  heartbeat and receipt-free `prepared` lease/lock required to exercise the
  binding and read-only gates. The lease carries the explicit
  `stream-a-prepare-only-exercise-v1` mode and
  `PRE-EFFECT-EXERCISE-NOT-PRODUCTION-EVIDENCE` marker.
- Run the healthy watchdog observation path and prove it is inert: no recovery,
  consumer-systemd command, timer arm, backend call or model call. The only
  permitted systemd control is the fixed exercise-owner transient unit below.
- Force one bounded owner-loss or explicit cancel/recovery path after the
  healthy observation. Because the lease is still `prepared`, recovery must
  validate the exact unchanged four-consumer baseline, issue zero consumer or
  systemd commands, and remove only the exercise state and lock.
- Do not invoke `quiesce`, `post-quiescence`, `start`, `outcome`, model code or
  any workload path. The exercise ends before consumer effects.

## Preconditions — all required, otherwise NO-GO

1. The exercise is scheduled outside the October 26 F2 execution window. Read
   the F2 timer identities and next-run times before and after the exercise;
   no same-cycle F2/F3/F4/F5 evidence is required for this pre-effect proof.
   Fresh backup evidence becomes mandatory before any later quiescence or
   effectful evaluation phase.
2. The inactive packet, two-phase source and exercise-admission pins match the
   accepted cards: implementation commits
   `2f790b6310981d31358a60fb2a7a3f98f7a26633`, `bdf745aa`, `2f59c2b0`,
   `7fbbc017630dc7ab87b212fc3a92ba92bb48663b` and
   `26dd2a0e90095a787d75353138393b71b3dbd6a4`; the installed watchdog must
   match `19606f6b398dd6f43a461704081e66f09e292c434f73f4aaee46327f9cc02f53`,
   the metadata-only auth-probe repair must be installed and verified, and
   the installed runner must match `610b963bccacc028401e6656df071e86dfa8c4066028b3e46291d5f3c9e2ec8a`
   before this exercise.
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
3. Invoke the bound `exercise-prepare` path with effect authorization. Prove
   the resulting lease has the exact exercise identity/generation, explicit
   exercise mode/marker, two-minute hard deadline, five-minute restore
   deadline, root custody, `prepared` phase, no receipt claims, no workload
   pointer and the exact baseline, while the runner observed zero
   consumer/systemd/model commands.
4. Launch the owner only through the fixed inert-by-default wrapper
   `/usr/local/sbin/stream-a-evaluation-exercise-owner-start`. It pins
   `systemd-run --unit=stream-a-evaluation-exercise-owner.service --collect
   --service-type=simple --property=User=root --property=NoNewPrivileges=yes
   --property=ProtectSystem=strict --property=ProtectHome=yes
   --property=PrivateTmp=yes
   --property=ReadWritePaths=/etc/local-ai-lab/stream-a-evaluation
   --property=ReadWritePaths=/var/lib/local-ai-lab/stream-a-evaluation`
   followed by `/usr/local/sbin/stream-a-evaluation-owner --run
   --effect-authorized --exercise-transient`. The owner must pass PID, boot
   ID, start-time, command-line and exact cgroup identity checks before writing
   its identity. Arbitrary unit names and direct SSH launches fail closed. Run
   heartbeat and watchdog once through their direct one-shot wrappers, not
   their recurring timers, using the exact lease and generation. The transient
   owner is the only allowed systemd control; no consumer systemd command is
   permitted.
5. Run the healthy watchdog observation using the exact lease/generation.
   Require `not-attempted`, no recovery callback, unchanged consumer baseline,
   unchanged F2 timers and no model/backend call.
6. Force exactly one bounded recovery case: owner-loss is preferred; an
   explicitly bounded cancel is acceptable only if it exercises the same
   recovery contract. The exercise may not wait into the October 26 F2 window.
7. Stop and collect only the fixed transient exercise owner, then clear its
   failed state if necessary. Do not stop or restart any production unit and
   do not enable or arm a recurring timer.
8. Require prepared-state recovery to validate the exact four-consumer
   baseline/backend/auth/idle/GPU evidence, issue zero runner commands, clear
   only the exercise lease/lock and temporary identity/intent, and report
   success only after custody and absence checks pass, including explicit
   absence of the durable lease, lease lock, transient operation lock and
   exercise identity/intent. If validation fails, retain `prepared` state and
   the lock for manual reconciliation.
9. Recheck production health, GPU holder, all five F6 unit/timer states and F2
   timer identities/next runs. Write the receipt and stop; never auto-retry.

## Pass/fail evidence

Pass requires all of the following:

- prepare-only created exactly one bound `prepared` lease and no consumer
  systemd commands; the only systemd activity was the fixed transient owner;
- the exercise marker/mode, short deadlines, receipt-free schema and absent
  workload progression were exact, and every production promotion path was
  rejected;
- healthy watchdog observation was inert;
- owner-loss/cancel recovery validated the exact baseline and cleared the
  exercise state, lock, identity and intent with zero consumer/systemd
  commands, and the transient operation lock was absent;
- no consumer, backend, model, timer or schedule changed;
- the October 26 F2 schedule and all F6 units/timers are byte-for-byte/state-
  for-state unchanged.

Any missing, foreign, stale, ambiguous or drifted identity/state is an
immediate NO-GO. A recovery or cleanup error retains the durable evidence and
stops for manual reconciliation; it must not retry or broaden scope.

This card authorizes no execution by itself, no production lease, no consumer
quiescence, no recurring timer arm, no model call and no remote Git operation.
