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
- The transition and every workload gate recheck the fixed hard deadline,
  heartbeat freshness and the remaining budget for that exact workload; late,
  future, stale or under-budget requests fail before a first model call.
- Durable state starts with `next_workload=d4-candidate-g`; each workload must
  be atomically marked in-flight before its first request and may write only
  one lease/generation-bound terminal receipt. Only a valid terminal D4 receipt
  enables M3, and only a valid terminal M3 receipt enables normal restoration.
  In-flight or uncertain work remains non-replayable; recovery may restore
  services without pretending the evaluation completed.
- The state reader accepts only the exact empty, D4-only, or D4-plus-M3
  progression shapes and checks 64-character journal/result digests. A
  descriptor-adjacent operation guard serializes competing start attempts.
- The baseline is exactly four `enabled+active` service/timer records. Missing,
  duplicate, unexpected or differently enabled targets fail before effects.
- `evaluation_lease_watchdog.py` reports disabled unless a future deployment
  explicitly supplies effect authority and a recovery callback. Its future
  state reader must validate owner/mode/symlink custody and bind lease ID,
  generation, heartbeat and fixed deadlines before recovery. The public
  unbound watchdog function can never invoke recovery, even if a caller passes
  an authorization flag; only the validated durable-state path may do so.
  The effect-capable path reads that state through the adapter's descriptor
  reader, including duplicate-key and exact-schema rejection.

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
| `scripts/local-ai/evaluation_lease_adapter.py` | `fdc3c12383ecc80d53fd706fdeb8b51eac5c152444276539cd620e03a8ddb1f7` |
| `scripts/local-ai/evaluation_lease_watchdog.py` | `b6409e9f29d954033ebd2098fdbd983862d0d32eb5de04471f7b06f9aaf74725` |
| `scripts/local-ai/host_exclusion.py` | `b39680d55d7203fe4e4a5f0ccbb7a3a708cc01616b02fd93d665585e467e3b61` |
| `scripts/local-ai/test_evaluation_lease_adapter.py` | `dd0cef180bc1ff359e8bd1f7a799d9f08a5998e7ecc74b7cef62175facb3ba74` |

No pin authorizes installation or live effects. Fresh F2/F3 evidence, target-
Linux review, an independent recovery path, exact source verification, and a
separate live-run approval remain mandatory.
