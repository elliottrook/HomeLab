# Stream A prepared-cancel adapter — inactive upgrade card

Status: **SOURCE-ONLY; NOT INSTALLED OR AUTHORIZED**

This card replaces only the installed evaluation-lease adapter so cancellation
of a genuinely pre-effect `prepared` lease validates and clears its own state
without issuing consumer or systemd commands. It authorizes no lease creation,
identity creation, consumer stop/start, model call, timer change, schedule
change, or remote Git operation.

## Exact one-file transaction

| Source | Target | Pre-upgrade SHA-256 | New SHA-256 | Mode |
|---|---|---|---|---:|
| `scripts/local-ai/evaluation_lease_adapter.py` | `/usr/local/libexec/local-ai-lease/stream-a-evaluation/evaluation_lease_adapter.py` | `304edaf3c2f247ac874b333331ee0098ac41d2776877c3ee51431152c294c877` | `db9c368707f4203d96725a06012adba808d8c425d42b1c25d19e7837052ce7cc` | 0644 |

The adapter change is the prepared-cancel source commit
`440c62513e2fe41ba40066b391fe67a715b9c939` (integrated locally as
`2f59c2b0`). The existing evaluation contract, entrypoint, watchdog,
host-exclusion packet, wrappers, units, timers, identity, state and lock
custody are not changed by this transaction.

## Required inactive sequence

1. Capture a root-owned checkpoint of the target's exact prehash, mode, owner,
   regular-file/no-symlink property and containing directory. Refuse on any
   drift or missing prestate.
2. Replace only the one listed adapter file atomically, retaining root custody
   and mode `0644`. Do not create or remove runtime state, identity, intent,
   heartbeat, status, lock, unit or timer files.
3. Run the target-local evaluation-lease suite with Python `-B`; require all
   41 tests to pass, including prepared cancellation with zero runner calls,
   validation-failure retention of PREPARED state, and normal effectful
   quiescing/recovery behavior. Run imports, static hash/mode checks and
   `git diff --check`.
4. Confirm all five F6 units/timers remain disabled/inactive and all runtime
   state remains absent. Do not invoke prepare, cancel, quiesce, restore,
   start, outcome, the watchdog effect path or any model/backend path on the
   target.

## Rollback

If replacement or any postcheck fails, atomically restore only the checkpointed
old adapter file, rehash it and verify root custody/mode. Preserve every other
packet and all runtime custody. If the target state is uncertain, retain the
checkpoint and stop for manual reconciliation; never retry automatically.

This card is a prerequisite for the prepare-only healthy-lease/recovery
exercise. It does not authorize that exercise or any effectful evaluation.
