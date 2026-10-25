# Stream A two-phase lease adapter — inactive upgrade card

Status: **SOURCE-ONLY; NOT INSTALLED OR AUTHORIZED**

This card upgrades the already inactive evaluation packet so durable lease
preparation is separate from consumer quiescence. It authorizes no install,
lease, lock, identity, consumer stop/start, model call, timer change or push.

## Contract change

- `acquire` is no longer an effectful shortcut. Its compatibility method is
  prepare-only and cannot mask or stop a consumer.
- `prepare` validates the exact admission and writes only the root-owned
  durable `lease.json` and `lease.lock` in phase `prepared`; the operation
  lock is a transient serialized guard, not additional durable lease custody.
  It performs no systemd command and no model work.
- `quiesce` is a separate effect-authorized phase. It requires the same
  lease/generation, fixed deadline and fresh controller heartbeat, durably
  promotes the lease to `quiescing` before the first consumer command, then
  masks and stops only the four registered consumers. Any mid-loop failure
  retains `quiescing` for recovery rather than misrepresenting partial effects
  as `prepared`.
- `post-quiescence` remains a separate read-only observation gate and promotes
  `quiescing` to `running` only after exact four-consumer, backend, auth, idle
  and GPU checks pass.
- Recovery accepts `prepared`, `quiescing`, `running` and `restoring`; a
  prepared crash can restore the exact baseline without claiming a workload.
- Workload `start`, `outcome` and normal `restore` remain blocked until the
  same lease/generation reaches the appropriate later phase.

## Pinned inactive upgrade

Implementation commits: `2f790b6310981d31358a60fb2a7a3f98f7a26633`,
`bdf745aa` (`d2e296eefaf4ea0ab6abe22ef0b65a0b41b59faa`).

| Source | Target | Pre-upgrade SHA-256 | New SHA-256 | Mode |
|---|---|---|---|---:|
| `scripts/local-ai/evaluation_lease.py` | `/usr/local/libexec/local-ai-lease/stream-a-evaluation/evaluation_lease.py` | `675ebb566de298334f7c612cae9af2637067930f40c0ad2c23a22e1b7e248f1b` | `e79c74035acf22222105b4a8cdcc00f75608bf2289732b4cba9a625252fe45b2` | 0644 |
| `scripts/local-ai/evaluation_lease_adapter.py` | `/usr/local/libexec/local-ai-lease/stream-a-evaluation/evaluation_lease_adapter.py` | `8fac397f96b88be5ccb042a2e3b3da6cbbccdc89e91e4afeacf029a13769c6a1` | `304edaf3c2f247ac874b333331ee0098ac41d2776877c3ee51431152c294c877` | 0644 |
| `scripts/local-ai/evaluation_lease_entrypoint.py` | `/usr/local/libexec/local-ai-lease/stream-a-evaluation/evaluation_lease_entrypoint.py` | `e4efd62036b8d26b0eb972a03f53f2cfdf6fbb6fa8a00f1c652b5803c23b5ce7` | `7425ffe9bd6c8b70c41fe3856343a0454d726e54d0f0531cd7ce7225118a332c` | 0644 |
| `scripts/local-ai/evaluation_lease_watchdog.py` | `/usr/local/libexec/local-ai-lease/stream-a-evaluation/evaluation_lease_watchdog.py` | `b6409e9f29d954033ebd2098fdbd983862d0d32eb5de04471f7b06f9aaf74725` | `68f261c65f48443a7d7c2115ad0017a5de6f5866f9693143a53375e10d7a585f` | 0644 |

The watchdog is included only to admit healthy `prepared` state and to retain
the same exact lease/generation/deadline recovery gates. The host exclusion,
wrapper, units/timers and other installed artifacts are not changed by this
upgrade. The new entrypoint phase is `quiesce`; no unit or timer is added or
enabled.

## Inactive upgrade sequence

1. Capture root-owned pre-upgrade checkpoint of the four old hashes, modes,
   owners, regular-file/no-symlink properties and the existing four-library
   root. Refuse the transaction on any drift.
2. Replace only the four listed files atomically, preserving root custody and
   mode `0644`. The already-installed `stream_a_evaluation_watchdog.py`
   packet and its wrappers, units, timers, host exclusion, state, lock,
   identity, owner intent, heartbeat and status are unchanged.
3. Run the full focused lease/entrypoint suite with Python `-B`, imports and
   static hash/mode checks. Confirm `prepare` produces no consumer commands,
   the legacy compatibility call cannot quiesce, a mid-loop failure leaves a
   durable `quiescing` phase that recovers the exact baseline, and a healthy
   `prepared` lease remains inert while an owner-loss/deadline case recovers.
4. Keep all services/timers disabled and inactive. Do not invoke `prepare`,
   `quiesce`, `post-quiescence`, `start`, `outcome` or `restore` on the target.

## Rollback

If any replacement or postcheck fails, restore all four checkpointed old files
atomically and rehash them. Preserve the already-installed watchdog packet,
host exclusion, wrappers, units, timers and all runtime custody. If state is
uncertain, retain the checkpoint and stop for manual reconciliation; never
retry automatically.

This upgrade is a prerequisite for the read-only healthy-lease gate, but it
does not authorize that gate, F6 activation, identity/state creation, consumer
quiescence, D4/M3 execution or recovery.
