# Stream A effectful entry point — deployment and recovery review card

Status: **SOURCE-ONLY; NOT INSTALLED, ACTIVATED OR AUTHORIZED**

This card is the next platform-owned review boundary after the accepted
inactive library candidate. It adds one manually invoked entry point and one
shell wrapper. It creates no systemd unit/timer and has no automatic activation
path.

## Pinned source

The complete source must be reviewed from the full local implementation commit
`e55e9eff` and the metadata follow-up that records that
commit here. Verify every file hash from that clean commit:

| Source | Target | Mode | SHA-256 |
|---|---|---:|---|
| `scripts/local-ai/evaluation_lease.py` | `/usr/local/libexec/local-ai-lease/stream-a-evaluation/evaluation_lease.py` | 0644 | `38a986e9d868d04c7ee7814ae0fbd2f1a1709e7a464916195d594ca2bf286312` |
| `scripts/local-ai/evaluation_lease_adapter.py` | `/usr/local/libexec/local-ai-lease/stream-a-evaluation/evaluation_lease_adapter.py` | 0644 | `8fac397f96b88be5ccb042a2e3b3da6cbbccdc89e91e4afeacf029a13769c6a1` |
| `scripts/local-ai/evaluation_lease_watchdog.py` | `/usr/local/libexec/local-ai-lease/stream-a-evaluation/evaluation_lease_watchdog.py` | 0644 | `b6409e9f29d954033ebd2098fdbd983862d0d32eb5de04471f7b06f9aaf74725` |
| `scripts/local-ai/evaluation_lease_entrypoint.py` | `/usr/local/libexec/local-ai-lease/stream-a-evaluation/evaluation_lease_entrypoint.py` | 0644 | `932bd999c6e16ab646a406936b3dccac2773f6953bd69c0c6205e3ca7a3efcda` |
| `scripts/local-ai/host_exclusion.py` | `/usr/local/libexec/local-ai-lease/stream-a-evaluation/host_exclusion.py` | 0644 | `b39680d55d7203fe4e4a5f0ccbb7a3a708cc01616b02fd93d665585e467e3b61` |
| `services/local-ai-lease/stream-a-evaluation-lease` | `/usr/local/sbin/stream-a-evaluation-lease` | 0755 | `962100b591493b2ae8f62814fa6f66a1875463dd5ca613bb321169764c56c276` |

The accepted D4 packet digest is
`03b0ad74a862ee04de75e012f52f6662c61192b69b279ea4d1d66c80d9ff9153` and the
accepted installed M3 staging manifest digest is
`69ffc58928ebd2f2f64e0600b8c4a7d73ce5f5356c485e1df8c2265741972165`.

The entry point requires both an explicit phase and `--effect-authorized`.
Without that flag it does not read state or intent and returns
`effects=disabled`. It supports only `acquire`, `post-quiescence`, `heartbeat`,
`start`, `outcome` and `restore`; it cannot arm itself or start a timer.
Effectful mode accepts only the fixed state path
`/var/lib/local-ai-lab/stream-a-evaluation/lease.json`; arbitrary state paths
are rejected before intent is read. Intent files are root-owned mode `0600`,
with exact per-phase keys, typed fields and literal booleans.

## Effect and recovery contract

- Acquire is bound to fresh F2/F3/backup receipts and the accepted Qwen3.5-9B
  llama.cpp/SYCL endpoint.
- The accepted backend remains active; only the registered consumers are
  quiesced.
- The fixed window is 90 minutes, with a 75-minute effect deadline and a
  15-minute restoration reserve.
- D4 is persisted in-flight before its first request; terminal D4 then enables
  M3; terminal M3 is required before normal restoration/completion.
- Any foreign, uncertain, duplicate, stale, malformed or replayed intent fails
  closed. Recovery may restore from every durable recovery phase without
  claiming an incomplete evaluation succeeded.
- The watchdog remains an independent, manually reviewed recovery boundary;
  no unit or timer is deployed by this card.

## Inactive deployment sequence

1. Verify `SOURCE_COMMIT`, all hashes, clean source, and the prior inactive
   candidate's exact target state. The existing root must be `root:root 0755`
   and contain the four already-installed libraries with the pinned hashes
   above, each `0644`.
2. Require only the new entrypoint under that existing root and the wrapper
   `/usr/local/sbin/stream-a-evaluation-lease` to be absent. Add exactly those
   two files; do not remove, replace or rewrite the existing root or four
   libraries. The entrypoint is `root:root 0644`; the wrapper is `root:root 0755`.
3. Recheck hashes, owner, mode, regular-file type and no symlinks. Run imports
   and the 28+ entry-point tests with bytecode disabled.
4. Invoke the wrapper only without `--effect-authorized` and verify the
   disabled response. Do not invoke an effectful phase.
5. Confirm no unit/timer, lease, operation lock, runtime state, consumer
   change, model request or F2 change.

## Rollback

The pre-install checkpoint is the exact existing-root/four-library manifest,
plus absence of the new entrypoint and wrapper. If any copy or post-copy check
fails, stop and remove only the newly added entrypoint and wrapper after
confirming their identities. Preserve the existing root and four libraries. If
state is uncertain, retain the new files for reconciliation and do not retry
automatically. Never touch existing lease code, F2 timers, production
services, credentials or the accepted backend.

This card does not authorize installation, activation, lease acquisition,
consumer stop/start, model calls, D4/M3 execution, F2 changes or Git push.
