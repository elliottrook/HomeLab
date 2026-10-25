# Stream A F6 activation and healthy-lease read-only preflight boundary

Status: **SOURCE-ONLY; PREPARED, NOT AUTHORIZED OR RUN**

This boundary follows the accepted inactive installation. It defines the
read-only checks required before any future F6 activation. It does not create
identity/state, start the owner, enable or arm timers, acquire a lease, stop
consumers, run recovery, call the observer/model, or change schedules.

## Gate order

1. Obtain a fresh same-cycle backup/F2/F3 evidence envelope and independently
   reread the retained digests. Confirm the post-backup window contains the
   complete 90-minute evaluation lease plus the 15-minute restoration reserve.
2. Confirm the inactive install result remains intact: all 13 artifact hashes,
   modes, owners and regular-file/no-symlink properties match the accepted
   card; all five candidate units/timers remain disabled/inactive.
3. Confirm no lease, operation lock, identity, owner intent, heartbeat, status,
   restore intent, observer output, bytecode, evaluation process, backup,
   maintenance job or model request is present.
4. Recheck the accepted backend and current GPU-holder identity read-only:
   exact llama-server executable, exact `/lxc/110/ns/system.slice/aster-llama.service`
   cgroup, PID/starttime consistency and no foreign holder.
5. Confirm LXC104/110/116, Aster, accepted llama/SYCL, Speech,
   `pvescheduler` and `pvestatd` health, plus unchanged F2 timers and backup
   schedules.

Any stale, missing, foreign, ambiguous or drifted evidence is a NO-GO. The
preflight writes no receipt and creates no runtime file.

## Future healthy-lease read-only check

Only after a separately approved activation creates the fixed root-owned
identity/state files may this check run. It reads, without mutation:

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

F6 activation remains a distinct approval after this read-only preflight. That
approval must name the exact cycle and permit only the owner identity/intent
creation and enabling of the pinned owner/watchdog/heartbeat units in the
documented order. A later approval is still required before any lease effect
phase. Loss of controller heartbeat, owner identity, backend health,
accepted-GPU identity or backup/F2/F3 continuity is an immediate recovery/NO-GO
condition; no automatic retry is permitted.
