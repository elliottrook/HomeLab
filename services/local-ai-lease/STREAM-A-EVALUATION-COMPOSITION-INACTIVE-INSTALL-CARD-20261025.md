# Stream A evaluation composition — inactive install card

Status: **REVISED SOURCE AND TARGET PREFLIGHT PASS; INACTIVE INSTALL REQUIRES FRESH EXPLICIT APPROVAL**

Source identity: independently reviewed platform branch through `85c30e44`,
with the dependency-closure correction at `37452660` after target inventory
proved that neither guest carries `evaluation_lease.py`.
This card stages code only. It does not
produce F3/F4/F5/admission evidence, enable or start a unit, arm F6, acquire a
lease, stop a consumer, start D4 or M3, read a completed private result, call a
model, change F2, or invoke `EvaluationRuntime.run()`.

## Measured prestate

The read-only target inventory on October 25 found:

- the eight new Proxmox composition files absent;
- the installed restore observer present as root:root mode `0644`, one link,
  SHA-256 `70748eb15c50ff7008cadd85fe9affaf62c9ad3eb388ef962270f9f9389fc1d3`;
- both guest verifier files absent in LXC104 and LXC110;
- all five F6 units disabled and inactive;
- whole-host lease exactly `{"state":"ready"}` and no evaluation lease or
  lock.

## Exact target packet

All Proxmox Python files go below
`/usr/local/libexec/local-ai-lease/stream-a-evaluation/` as root:root regular
mode `0644` files:

| File | SHA-256 |
|---|---|
| `stream_a_evaluation_live_plan.py` | `0f8d7e558bff48d6be9f86da62041ccaa20aa6b18780b738756d1118f0bf0ef2` |
| `stream_a_evaluation_sequence.py` | `63eedd771d3cca25183e7f551b076c19d84e9c2855d9c7985e8cce445239aef1` |
| `stream_a_evaluation_effect_driver.py` | `06318de809a22321b254713a9af9b87aecfa150c1cfd298c164fcab16d961f0e` |
| `stream_a_evaluation_handlers.py` | `6977af891af538989de49c6cc67f13fe7d6953b68a9bd9d44bc9edadbbeed4a4` |
| `stream_a_evaluation_evidence_loader.py` | `836f627cd2702dffd59c77b77adab2aded01805ee43553a11471cfddfeb80a01` |
| `stream_a_evaluation_host_outcome.py` | `6b986fb71dca8657aa56b9fe8ef904223445e64b4122a827324adaf300c64321` |
| `stream_a_evaluation_restored_verifier.py` | `a83de6bcdf0b275b9f238acda1a35e7518eae12f47eb220faf8f822d9a5e0d93` |
| `stream_a_evaluation_runtime.py` | `7cda2842afa25bfca9cb47e30f433474c440ccf18123c80e7c55b54c66eb7210` |
| `stream_a_evaluation_restore_observer.py` | `20d977681452eb89cbda7b0417de02b4caed279f234e7b568a072638bb736fb2` |

Both LXC104 and LXC110 receive these exact root:root files:

| Target | Mode | SHA-256 |
|---|---:|---|
| `/usr/local/libexec/stream-a-evaluation-guest-outcome` | `0755` | `027183c9f10923cc4aa3053934b5f090d8e01f86aa81c9730d93abc143e6dcb9` |
| `/usr/local/libexec/stream_a_evaluation_outcome_verifier.py` | `0644` | `9408623489d52f7923c8dcca246159bb13a7926aa0a820c765fc8f3a339b58e1` |

## Bounded transaction

1. Recheck source hashes, target custody, ready lease, absent state/locks and
   all five F6 units disabled/inactive. Create a new root-only mode-`0700`
   checkpoint. Copy the installed restore observer into it as root:root mode
   `0600`, one link, and record every currently absent target.
2. Stage the reviewed source and tests in a new root-only temporary directory
   on Proxmox. Run `python3 -B` imports and the complete
   `test_stream_a_evaluation*.py` suite; require 95/95.
3. Install the nine Proxmox files atomically at the exact hashes and modes.
   Copy the two guest files into each guest atomically at the exact hashes and
   modes. Do not install a runtime wrapper or systemd unit for the composition
   root.
4. Re-run Proxmox imports. In each guest, run only the guest verifier with no
   arguments and require the canonical content-free `state=disabled` result;
   do not supply `--verify-authorized` and do not read a workload artifact.
   The guest pair must import and run with an empty `PYTHONPATH`; it may not
   depend on the host-only `evaluation_lease.py` module.
5. Recheck all thirteen target paths, all five F6 units disabled/inactive,
   ready whole-host lease, absent evaluation state/locks, healthy production,
   and unchanged F2 schedule. No daemon reload is needed because no unit file
   changes.

## Rollback

On any mismatch, restore only the checkpointed observer, remove only the
twelve targets proven absent in prestate, and re-run imports/inert checks and
the full postcheck. Preserve the checkpoint and diagnostic result. An unknown
target, active unit, runtime artifact, lease, process or schedule drift is a
stop condition; do not delete or infer recovery.

Successful inactive installation closes code placement and target-Linux
compatibility only. Fresh F2/F3/F4/F5/admission production, F6 arming, the
effectful 90-minute run and model calls remain separate gates.

## Revised target preflight

A clean archive from `37452660` (SHA-256
`f7bb5e658cdb2504c4b896fdf53fd187e7e35dacd05cdf82f5a078f6d006ae5c`)
passed 95/95 tests on Proxmox. The two-file guest packet was then copied only
to a fresh temporary directory in each of LXC104 and LXC110. With an empty
`PYTHONPATH`, both returned the exact canonical disabled result and created no
bytecode. Those temporary directories and the archive were removed. No target
installation, runtime state, lease, service action or model call occurred.
