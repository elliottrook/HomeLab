# F5/F6 conditional preflight and recovery card — inactive

Status: offline/read-only preparation; HOLD. F5 begins only after separately
approved F3 success and a fresh, independently reread F4 envelope. F6 remains
behind its own later approval. This card authorizes no install, timer arming,
receipt, lease, service stop, model call, drill, state clear, or push.

## Readiness and discrepancies

The installed F5/F6 source and unit files were reconciled read-only on
2026-10-20. LXC110's accepted Qwen3.5 9B Q4_K_M, llama.cpp b11429
SYCL/Level Zero, GPU devices, pinned binary, model, and `aster-llama.service`
identities match the manifest. The API-key file is root-readable only.

The model file is currently `root:root 0777`; this security discrepancy must
be accepted or corrected by separate review before F5 can report READY. No
correction is authorized here. The watchdog and owner-heartbeat units are
installed but inactive/disabled, and their state files, lease, lock, watchdog
status, and owner heartbeat are absent. The recovery candidate is installed
but cannot be armed by this card.

The retained producer remains `EFFECTS_ENABLED = False`; F5/F6 cannot promote
that producer or infer F3 success.

The LXC110 namespace does not expose the Aster Agent, Speech, or News unit
names queried during reconciliation; the production llama process is active
and the News renderer process is present on the host. F5 must use the fixed
observer ownership/probe paths and record the actual service identity before
acceptance. This is an evidence discrepancy, not permission to rename,
restart, or repair services.

## F5 read-only contract

After separately approved F3 success and fresh F4 success, reread F4 and
require its retained digest to match the F3 receipt and same-cycle backup
identity. F5 then records, without mutation:

- unchanged F2 terminal state and exact 104/110/116 archive rows;
- Proxmox 00:30, TrueNAS guest 01:00, LXC110 02:00, Mac 03:00, and News
  06:15/17:15 schedule identities enabled and current;
- same-cycle whole-job, guest, task-1, LXC110 mirror, and Mac completion facts;
- no competing backup, pull, maintenance, lease, lock, or F2/F3 process;
- LXC110 model, binary, unit, GPU, API-key custody, and authenticated runtime
  identities matching the pinned baseline;
- Aster Agent, llama, and Speech still running, with News active and idle;
- watchdog and owner-liveness identities present but not active.

F5 writes only a bounded non-secret observation matching F4. Missing, stale,
drifted, ambiguous, or security-discrepant evidence is NO-GO. F5 never
creates a lease, changes a schedule, stops a service, or calls a model.

## F6 independent recovery arming — later approval only

After F5 is independently reviewed complete, obtain a separate F6 approval.
Verify the exact candidate recovery and watchdog paths, create fresh root-owned
checkpoints, and arm only the pinned watchdog and owner-heartbeat timers.
Require active/enabled state, exact `aster-admission` schema compatibility,
owner-liveness, and the constrained recovery executor's explicit
`--effect-authorized` boundary.

F6 arming must not acquire a lease or lock, start a production service, invoke
recovery, call a model, or schedule a drill. Loss of watchdog/owner liveness
is NO-GO. F7 human approval remains mandatory before F8 can acquire the lease
or stop only the allowlisted services.

## Pinned source and runtime identities

| Path or identity | SHA-256 |
|---|---|
| `scripts/local-ai/full_inference_lab_sources.py` | `233459b80bf927a53b32d11563bf2e0b264ab25ad55091293e6f40995747e054` |
| `scripts/local-ai/test_full_inference_lab_sources.py` | `9a1c3abf5179c9f2933fce6936c0e8c23c839275ffb7e4d718a81359268257ae` |
| `scripts/local-ai/trusted_observer.py` | `de6d2da913a1dab4f5e371739a6a3eada79b99d8e11e2d3b64cf0f825274074e` |
| `scripts/local-ai/lease_watchdog.py` | `3146d292dd42a6a3f305b67cccf5518e7c0585c9c6de2e195d1a00686003d1fc` |
| `scripts/local-ai/lease_recovery_executor.py` | `d75ddfae4ccb3de4bd059aca75d41f4cdac6c60f4951d0ea6ab11a13b9f98e4d` |
| `scripts/local-ai/lease_contract.py` | `420ce2ecc44bde3d17ad25218462618d150a4ec37c4a597067ebb45f8e2f780b` |
| `scripts/local-ai/lease_controller_candidate.py` | `f46509e49227cf7ba78ce662184722192059277202e7315616d12456f0385217` |
| `services/local-ai-lease/local-ai-lease-recovery` | `46ddd8a031ecdeb2f227fadb18f5bc76ee9ad6042bf59d7056522c13ffe5b81c` |
| `services/local-ai-lease/local-ai-lease-watchdog.service` | `3041ed62efadcb1bcffe0c66e9c311933fc90c0cb101ea08f24b546fc9bc656d` |
| `services/local-ai-lease/local-ai-lease-watchdog.timer` | `9f09de46e3ee55d8f765e1f279d34632ea914c8c6506416f0455853ef538b744` |
| `services/local-ai-lease/local-ai-lease-owner-heartbeat.service` | `261ded21db209512be1b258613de4813063ae68d8057b475216e9af6e7911739` |
| `services/local-ai-lease/local-ai-lease-owner-heartbeat.timer` | `275e93ab7ab4a2ec5730feea8e8485126680837575f7d2a5756786a1e0a30b38` |
| `LXC110 /opt/aster-sycl-b11429/.../llama-server` | `0404f751814391544c86469fa71a893c0f3858e7c7aeb2cb0982909c1c0de6c5` |
| `LXC110 /opt/models/.../Qwen3.5-9B-Q4_K_M.gguf` | `cd76ec205963b3b33350093e6904d9de16c4e666fd104e1f632d25c7f15f2a13` |
| `LXC110 /etc/systemd/system/aster-llama.service` | `a4c75169673a1a230682b73d362a05c1bdd30f7a5c41cfb9c77463204dfd4cb3` |

The watchdog's content-free status schema carries lease ID, generation,
state, expiry, accepted model/backend identities, health, GPU, schedule and
failure fields. The recovery executor is effect-permitted only for a live
leased/restoring state with a healthy control plane and explicit authorization;
F6 does not supply those conditions.

## Rollback and approval points

F5 rollback is deletion of its temporary observation only; preserve F2/F3/F4
evidence. F6 rollback disables/stops only its candidate timers, restores fresh
checkpoints, and verifies no lease, lock, service stop, or recovery action.
It must not clear failed historical F2 services or state. F7 is the next
approval point for a human-bounded drill; F8/F9 remain separate execution and
restoration gates.

This card records conditional readiness only. It does not install or arm
watchdog/heartbeat timers, create receipts, acquire a lease, stop production,
call a model, schedule a drill, clear state, or push remotely.
