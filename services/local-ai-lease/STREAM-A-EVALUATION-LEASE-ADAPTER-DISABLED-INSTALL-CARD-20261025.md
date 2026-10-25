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
- `evaluation_lease_watchdog.py` reports disabled unless a future deployment
  explicitly supplies effect authority and a recovery callback.

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
| `scripts/local-ai/evaluation_lease.py` | `c521ff753e92d290efe2a2cc6d8d78e8b10b1be86e2a1703f7304783cd3522ca` |
| `scripts/local-ai/evaluation_lease_adapter.py` | `d7273cbc532cc2708eeec5f9199c0de20d5ce37d1ed1acf64c9828a18e569cf5` |
| `scripts/local-ai/evaluation_lease_watchdog.py` | `74aa4524980e53d65f46f062842ba27d396071443e95a6dfff7eb3cdc0521a8c` |
| `scripts/local-ai/host_exclusion.py` | `b39680d55d7203fe4e4a5f0ccbb7a3a708cc01616b02fd93d665585e467e3b61` |
| `scripts/local-ai/test_evaluation_lease_adapter.py` | `9680a8127873bf6d114252d70ecacc3e0a7afbc00d09cfb7122722df6f9697f5` |

No pin authorizes installation or live effects. Fresh F2/F3 evidence, target-
Linux review, an independent recovery path, exact source verification, and a
separate live-run approval remain mandatory.
