# Stream A effectful entry point — deployment and recovery review card

Status: **SOURCE-ONLY; NOT INSTALLED, ACTIVATED OR AUTHORIZED**

This card is the next platform-owned review boundary after the accepted
inactive library candidate. It adds one manually invoked entry point and one
shell wrapper. It creates no systemd unit/timer and has no automatic activation
path.

## Pinned source

The complete source must be reviewed from the full local implementation commit
`SOURCE_COMMIT_TO_BE_RECORDED` and the metadata follow-up that records that
commit here. Verify every file hash from that clean commit:

| Source | Target | Mode | SHA-256 |
|---|---|---:|---|
| `scripts/local-ai/evaluation_lease.py` | `/usr/local/libexec/local-ai-lease/stream-a-evaluation/evaluation_lease.py` | 0644 | `38a986e9d868d04c7ee7814ae0fbd2f1a1709e7a464916195d594ca2bf286312` |
| `scripts/local-ai/evaluation_lease_adapter.py` | `/usr/local/libexec/local-ai-lease/stream-a-evaluation/evaluation_lease_adapter.py` | 0644 | `8fac397f96b88be5ccb042a2e3b3da6cbbccdc89e91e4afeacf029a13769c6a1` |
| `scripts/local-ai/evaluation_lease_watchdog.py` | `/usr/local/libexec/local-ai-lease/stream-a-evaluation/evaluation_lease_watchdog.py` | 0644 | `b6409e9f29d954033ebd2098fdbd983862d0d32eb5de04471f7b06f9aaf74725` |
| `scripts/local-ai/evaluation_lease_entrypoint.py` | `/usr/local/libexec/local-ai-lease/stream-a-evaluation/evaluation_lease_entrypoint.py` | 0644 | `d42963fb84730aa3a6f9a8206c1626b1b526ec2b9ee4ac5456716ed7b4be8b97` |
| `scripts/local-ai/host_exclusion.py` | `/usr/local/libexec/local-ai-lease/stream-a-evaluation/host_exclusion.py` | 0644 | `b39680d55d7203fe4e4a5f0ccbb7a3a708cc01616b02fd93d665585e467e3b61` |
| `services/local-ai-lease/stream-a-evaluation-lease` | `/usr/local/sbin/stream-a-evaluation-lease` | 0755 | `962100b591493b2ae8f62814fa6f66a1875463dd5ca613bb321169764c56c276` |

The entry point requires both an explicit phase and `--effect-authorized`.
Without that flag it does not read state or intent and returns
`effects=disabled`. It supports only `acquire`, `post-quiescence`, `heartbeat`,
`start`, `outcome` and `restore`; it cannot arm itself or start a timer.

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
   candidate's exact target state.
2. Require the destination root and all target files absent; existing paths are
   NO-GO. Create the root `root:root 0755`, copy only the five libraries, and
   copy the wrapper `root:root 0755`.
3. Recheck hashes, owner, mode, regular-file type and no symlinks. Run imports
   and the 28+ entry-point tests with bytecode disabled.
4. Invoke the wrapper only without `--effect-authorized` and verify the
   disabled response. Do not invoke an effectful phase.
5. Confirm no unit/timer, lease, operation lock, runtime state, consumer
   change, model request or F2 change.

## Rollback

The pre-install checkpoint is the exact absent-state manifest. If any copy or
post-copy check fails, stop and remove only the newly created wrapper and
destination root after confirming it contains only these candidate files. If
state is uncertain, retain the root mode `0700` for reconciliation and do not
retry automatically. Never touch existing lease code, F2 timers, production
services, credentials or the accepted backend.

This card does not authorize installation, activation, lease acquisition,
consumer stop/start, model calls, D4/M3 execution, F2 changes or Git push.
