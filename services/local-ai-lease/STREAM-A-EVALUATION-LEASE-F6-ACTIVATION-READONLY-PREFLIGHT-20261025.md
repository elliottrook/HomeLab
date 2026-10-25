# Stream A F6 activation and healthy-lease read-only preflight boundary

Status: **SOURCE-ONLY; PREPARED, NOT AUTHORIZED OR RUN**

This boundary follows the accepted inactive installation. It defines the
read-only checks required before any future F6 activation. It does not create
identity/state, start the owner, enable or arm timers, acquire a lease, stop
consumers, run recovery, call the observer/model, or change schedules.

## Gate order

The phases are deliberately separate. No later phase is implied by an earlier
one:

1. **F2/F3/F4/F5 preflight:** obtain a fresh same-cycle backup/F2/F3/F4/F5
   evidence envelope and independently reread the retained digests. Confirm
   the post-backup window contains the complete 90-minute evaluation lease
   plus the 15-minute restoration reserve. Recheck the inactive install,
   absence state, accepted backend/GPU identity, production health, schedules
   and unchanged F2 timers.
2. **F6 arm, separately approved:** create only the proposed root-owned lease
   identity and owner intent, then arm the owner/watchdog/heartbeat units.
   Prove owner/watchdog readiness with **no lease**, no consumer mutation and
   no model work. This phase is not currently authorized or prepared to run.
3. **Acquire-only, separately approved:** a future adapter revision must create
   the exact durable lease and lock without masking/stopping consumers and
   without model work. The current `EvaluationLeaseAdapter.acquire()` does not
   satisfy this requirement: with effects enabled it creates state and then
   immediately masks/stops the four consumers. Therefore the acquire-only
   phase is presently **NO-GO** and requires a separately reviewed source
   change before F6 activation can proceed.
4. **Healthy-lease read-only check:** only after a valid acquire-only phase has
   produced `lease.json`, read and validate lease/heartbeat/lock custody,
   lease/generation identity, fixed deadlines, backend/authentication/idle/GPU
   evidence and the exact four-consumer baseline. This check must not mutate
   state or call any effect phase.
5. **D4→M3 effect phase, separately approved:** only after the healthy-lease
   check may a later approval invoke the effectful quiescence/start sequence,
   stop the four registered consumers and call the model. Restoration remains
   separately verified and retains the 15-minute reserve.

Any stale, missing, foreign, ambiguous or drifted evidence is a NO-GO. The
preflight writes no receipt and creates no runtime file.

## Future healthy-lease read-only check

Only after a separately approved acquire-only phase creates the fixed
root-owned lease/state files may this check run. F6 arm alone cannot satisfy
this precondition; it creates no lease. The check reads, without mutation:

- exact `watchdog-identity.json` lease ID, generation, owner process identity
  and heartbeat timeout;
- exact `lease.json` schema, fixed 75/90-minute deadlines, baseline,
  D4→M3 progression and lease/generation match;
- exact root-owned 0600 owner heartbeat and controller heartbeat freshness;
- operation-lock custody and absence of competing evaluation operations;
- candidate unit/timer enabled/active state and owner process identity;
- accepted backend/authentication/idle/GPU evidence from the fixed observer;
- exact four-consumer production baseline and no consumer mutation.

The healthy-lease check must not call `acquire`, `start`, `outcome`, `restore`,
the model, or any consumer command. It reports only whether the state is safe
for a later human-approved activation/drill.

## Separate activation boundary

F6 arm remains a distinct approval after the F2/F3/F4/F5 preflight. That
approval may permit only owner identity/intent creation and enabling of the
pinned owner/watchdog/heartbeat units. Acquire-only, healthy-lease inspection
and D4→M3 effects each require their own subsequent approval. Until the
adapter is revised to separate acquire-only from consumer quiescence, F6 arm
and all downstream phases remain NO-GO. Loss of controller heartbeat, owner
identity, backend health, accepted-GPU identity or backup/F2/F3 continuity is
an immediate recovery/NO-GO condition; no automatic retry is permitted.
