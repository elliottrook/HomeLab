# Stream A evaluation lease adapter — inactive target-Linux card

Status: **SOURCE-ONLY; NOT INSTALLED, ARMED OR RUN**

This is the smallest effectful adapter for the accepted endpoint-retaining
contract. Both the adapter and independent watchdog are hard-disabled by
default. The target-Linux test uses a synthetic command runner only; it does
not contact Proxmox, LXC110, systemd, the GPU, F2 timers or the model.

## Boundaries

- `evaluation_lease_adapter.py` may target only LXC104 Aster Agent, LXC116
  Speech, and the two registered LXC114 News timers.
- `lxc110:aster-llama.service` is never a command target. The accepted backend
  must remain the exact GPU holder and endpoint idleness is checked separately.
- Acquisition is ordered as mask/stop, post-quiescence verification, D4 then
  M3, and exact unmask/start restoration.
- Any restore exception leaves the durable state and lock in place for
  reconciliation; it never claims success.
- Recovery is idempotent from `quiescing`, `running` and `restoring`; a crash
  in any of those phases can retry exact-baseline restoration without losing
  the lock.
- Acquisition remains `quiescing` until a separate observed-state check proves
  every registered target is masked and inactive. Workloads are refused until
  that check atomically promotes the durable state to `running`.
- The baseline is exactly four `enabled+active` service/timer records. Missing,
  duplicate, unexpected or differently enabled targets fail before effects.
- `evaluation_lease_watchdog.py` reports disabled unless a future deployment
  explicitly supplies effect authority and a recovery callback. Its future
  state reader must validate owner/mode/symlink custody and bind lease ID,
  generation, heartbeat and fixed deadlines before recovery. The public
  unbound watchdog function can never invoke recovery, even if a caller passes
  an authorization flag; only the validated durable-state path may do so.

The controller binds the accepted contract's 90-minute total window, 75-minute
effect deadline, 15-minute restore reserve, and 10+36+20-minute fixed budgets
through the imported pure contract. Workload receipts remain separate and
lease/generation-bound.

## Source pins

The future inactive-install manifest must pin the exact SHA-256 values of:

- `scripts/local-ai/evaluation_lease.py`
- `scripts/local-ai/evaluation_lease_adapter.py`
- `scripts/local-ai/evaluation_lease_watchdog.py`
- `scripts/local-ai/host_exclusion.py`
- `scripts/local-ai/test_evaluation_lease_adapter.py`

Current source hashes:

| Path | SHA-256 |
|---|---|
| `scripts/local-ai/evaluation_lease.py` | `38a986e9d868d04c7ee7814ae0fbd2f1a1709e7a464916195d594ca2bf286312` |
| `scripts/local-ai/evaluation_lease_adapter.py` | `e015286f21e116c2215d9668bbadbf0d9e6a5399cb7bd5ddb87823035cad6f31` |
| `scripts/local-ai/evaluation_lease_watchdog.py` | `13cbfb89db55a20d1812379f3f3de8fcbcbf4b95b2d2f73af963cdbe5cb68ff3` |
| `scripts/local-ai/host_exclusion.py` | `b39680d55d7203fe4e4a5f0ccbb7a3a708cc01616b02fd93d665585e467e3b61` |
| `scripts/local-ai/test_evaluation_lease_adapter.py` | `59dafc3fbbf06f2655e7b76999b3eec44bf25c5e39b3a41bbb12e797a21bb703` |

No pin authorizes installation or live effects. Fresh F2/F3 evidence, target-
Linux review, an independent recovery path, exact source verification, and a
separate live-run approval remain mandatory.
