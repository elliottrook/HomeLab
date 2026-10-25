# Stream A endpoint-retaining evaluation lease — inactive install card

Status: **SOURCE-ONLY; NOT INSTALLED, ARMED OR RUN**

This packet defines the smallest compatible lease for the already approved D4
candidate-G followed by M3 NLU calibration sequence. It retains the exact
`lxc110:aster-llama.service` Qwen3.5-9B Q4_K_M llama.cpp b11429 SYCL/Level Zero
endpoint and quiesces only the registered Aster Agent, Speech and News timer
consumers. It does not use the A1 sidecar, temporary key, ingress, firewall or
full-stop controller.

## Source

- `scripts/local-ai/evaluation_lease.py`
- `scripts/local-ai/test_evaluation_lease.py`

The module is pure and has no live entry point. A future adapter must be
separately reviewed and approved before installation or effectful testing.

## Fixed sequence

1. Capture and bind fresh F2, F3 and backup receipts, exact runtime/model/unit
   identity, owner, generation and hard deadlines.
2. Capture the exact production unit/timer baseline.
3. Keep `lxc110:aster-llama.service` active, authenticated and idle, and prove
   it is the only GPU inference holder.
4. Quiesce only LXC104 Aster Agent, LXC116 Speech, and the two LXC114 News
   timers. Do not stop or mask the llama backend.
5. Recheck the exact post-quiescence target set, backend holder and endpoint
   idleness before any model request. Run D4 candidate-G once, retaining its
   separate journal/result, then run M3 calibration once with its own journal/result. Any transport, lease, source,
   endpoint or custody uncertainty skips the next workload and triggers restore.
6. Restore the exact baseline, prove production health/authentication and GPU
   idleness, then release the lock. Uncertain recovery retains the lock/state.

The fixed 90-minute window has a 75-minute effect deadline and reserves the
final 15 minutes for restoration. The fixed workload budgets are 36 minutes
for D4 and 20 minutes for M3, with a 10-minute setup budget; unused time is
not borrowable.

## Live gates that remain

- Install and effectful adapter/controller/watchdog/recovery implementation.
- Independent target-Linux review of the effectful adapter, including systemd,
  Proxmox and GPU-holder observations.
- Fresh source-bound F2 archive and F3 retained-receipt evidence for the same
  cycle. Historical or generic `ready` state is not sufficient.
- Exact D4 digest
  `03b0ad74a862ee04de75e012f52f6662c61192b69b279ea4d1d66c80d9ff9153` and M3
  manifest digest
  `357b4e3d5514fe32b1509ac27f9eac3940edb0635db3a5008b4f29fc4f124a00`.
- A separately approved live run, independent recovery path, post-restore
  production checks and custody verification.

Successful F2 and F3 evidence is therefore required before arming this lease;
this source-only commit does not claim either result and does not change target
state.
