# Stream A watchdog and recovery activation boundary

Status: **SOURCE-ONLY; PREPARED, NOT ARMED OR RUN**

This is the next independent review boundary after the successful inactive
entrypoint installation. It defines what must be verified before any watchdog
or owner-heartbeat timer is enabled. It authorizes no timer change, lease,
service stop/start, recovery action, model request, schedule change, or push.

## Current verified boundary

- The inactive entrypoint install passed its exact five-file, owner, mode,
  import, disabled-wrapper, and no-bytecode checks.
- Automatic rollback was confirmed for two failed preliminary package attempts;
  the final hierarchy-preserving package is the installed candidate.
- No lease state or operation lock exists.
- `lxc104:aster-agent.service`, `lxc110:aster-llama.service`,
  `lxc116:aster-speech.service`, Proxmox `pvescheduler` and `pvestatd` are
  healthy; the four F2 timers remain enabled/active for the scheduled cycle.
- No effect phase has run. The accepted backend remains Qwen3.5-9B Q4_K_M via
  llama.cpp b11429 SYCL/Level Zero at the pinned endpoint.

These facts are a receipt for the inactive install, not authorization to arm
the recovery boundary.

## Pinned source

The watchdog and adapter must be reviewed from the installed source pins:

| Source | SHA-256 |
|---|---|
| `scripts/local-ai/evaluation_lease.py` | `675ebb566de298334f7c612cae9af2637067930f40c0ad2c23a22e1b7e248f1b` |
| `scripts/local-ai/evaluation_lease_adapter.py` | `8fac397f96b88be5ccb042a2e3b3da6cbbccdc89e91e4afeacf029a13769c6a1` |
| `scripts/local-ai/evaluation_lease_watchdog.py` | `b6409e9f29d954033ebd2098fdbd983862d0d32eb5de04471f7b06f9aaf74725` |
| `scripts/local-ai/host_exclusion.py` | `b39680d55d7203fe4e4a5f0ccbb7a3a708cc01616b02fd93d665585e467e3b61` |
| `scripts/local-ai/test_evaluation_lease_adapter.py` | `ce328723dc62d753ec7ab16aeb1bdc254eff6bc7ab851a851f2c77e13fc2e35d` |

The entrypoint and wrapper remain pinned by the effectful deployment card.
Any source drift, flattened package layout, missing dependency, or hash/mode/
owner mismatch is an immediate NO-GO.

## Conditional F5 read-only preflight

After a fresh same-cycle backup, F2 and F3 evidence envelope is independently
reread, then verify all of the following without mutation:

1. The exact F2/F3/backup receipts are fresh and mutually consistent.
2. The accepted backend, binary, model, endpoint authentication, GPU holder,
   API-key custody and `aster-llama.service` identities match the pinned
   baseline.
3. The production baseline is exactly four `enabled+active` records:
   Aster Agent, Speech, and the two News timers. No extra consumer, backup,
   maintenance, lease, lock, or recovery process is present.
4. The watchdog and owner-heartbeat identities are installed but inactive;
   their state files, lease, lock, heartbeat and watchdog status are absent.
5. The post-backup window contains the full 90-minute lease plus the reserved
   15-minute restore interval and does not overlap the next scheduled backup.

F5 records only a bounded non-secret observation. It does not create state,
write a receipt, arm a timer, or call the model.

## Separate F6 activation review

F6 requires a new explicit approval after F5 is reviewed complete. The
platform operator must then checkpoint the exact inactive state and verify:

- watchdog and owner-heartbeat unit/timer paths, hashes, root custody and
  modes;
- exact durable-state schema compatibility with the installed adapter;
- owner-liveness identity and the constrained recovery callback;
- `--effect-authorized` is present only in the pinned timer command and not in
  diagnostic/default paths;
- enablement is limited to the watchdog and owner-heartbeat timers, with no
  manual service start and no lease acquisition.

F6 must stop and roll back its own timer changes on any mismatch. It must not
clear historical failures or state, touch F2 schedules, stop a consumer, start
the backend, invoke recovery, or call a model. Loss of watchdog or owner
liveness is NO-GO. Human approval remains mandatory before any effect phase.

## Recovery behavior that must remain true

The watchdog reads the fixed durable lease descriptor through the adapter,
binds lease ID, generation and the 75/90-minute deadlines, and only considers
recovery from `quiescing`, `running` or `restoring`. Unbound or in-memory
diagnostics remain effect-disabled. An uncertain or incomplete workload is
never reported as successful; recovery restores the exact baseline or leaves
the durable state and lock for reconciliation.

This card is a prepared activation boundary, not an activation instruction.
