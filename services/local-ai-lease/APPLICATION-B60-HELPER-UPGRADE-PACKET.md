# Application B60 helper upgrade/install packet

Status: reviewable, not executed. This packet is separate from the later
effectful application drill. It performs only a disabled helper upgrade and
installs the bounded controller/heartbeat entrypoints. It must not create a
lease, key, ingress rule, sidecar process, model request, or enabled timer.

## Exact destinations and hashes

All Proxmox files below are root-owned. Python/helper files are mode 0644;
shell wrappers are mode 0755; service/timer files are mode 0644.

| Host | Destination | Source SHA-256 |
|---|---|---|
| Proxmox | `/usr/local/libexec/aster-a1/application_b60_controller.py` | `3daa4204b1e9515e397680dc51bb2ed96994d2a273e0c2c3ef87f728ce6a41af` |
| Proxmox | `/usr/local/libexec/aster-a1/application_b60_lease.py` | `deaf278c8bc3234f3150f1c3ee696b3cc0cdb55e97c575fec6efb65d6ef9c95d` |
| Proxmox | `/usr/local/libexec/aster-a1/application_b60_watchdog.py` | `3447d490ec396dee45191a5294537f2132deac6578e3e30376f6f6980a98e8d2` |
| Proxmox | `/usr/local/libexec/aster-a1/application_b60_lease_recovery.py` | `b70779a816915ec0fa8cfb66d122ea47e96a607a68bf056d26cda75e237b9311` |
| Proxmox | `/usr/local/libexec/aster-a1/application_receipt_boundary.py` | `1b61d3cc5fdbf3bae538a4a49864a57cca2c360fec37d2408e70a8f1e95ca0da` |
| Proxmox | `/usr/local/libexec/aster-a1/application_b60_lease_heartbeat.py` | `8b77bb099ed78293d3c779b225ea347a686587388b2ffcbaba7a435e61da63ca` |
| Proxmox | `/usr/local/libexec/aster-a1/application_admission_cli.py` | `3702f50d8425227d435fbfe6044622d1fcca5c78c93bfdbe1047e29f32e0e655` |
| Proxmox | `/usr/local/libexec/aster-a1/application_b60_drill_entrypoint.py` | `5eb774f4f5eb7f09e8cefcb30d9eff95bc0f4c1da89d6d113d54b89a2f0a5eb2` |
| Proxmox | `/usr/local/libexec/aster-a1/lease_effect_runner.py` | `e4fb2f9657534d83b3581e82ee52c6ee3aeecf613df54c3f6f4916b8d34d84f5` |
| Proxmox | `/usr/local/sbin/application-b60-lease-recovery` | `309774dca1f0b5b37a9159b00fe6eed7b46f123f866c98e5d996e2c9fdc46499` |
| Proxmox | `/usr/local/sbin/application-b60-heartbeat` | `867f17d5472e7fa62e1ade7159ad08918438aa669272cb90871f5779ce53849b` |
| Proxmox | `/usr/local/sbin/application-b60-drill` | `4386211d9c951c7591dcf1619a19f161334be6826bc4d1b51e20ff0ec1c5a967` |
| Proxmox | `/etc/systemd/system/application-b60-watchdog.service` | `f7434db1f18afa4418f1217801152e35a2ae24388c20e04e47e3db8c3288cec7` |
| Proxmox | `/etc/systemd/system/application-b60-watchdog.timer` | `3e0be0830d60e586e53a1c3035abef7df802ecd156214ddc558f60677111d45a` |
| Proxmox | `/etc/systemd/system/application-b60-heartbeat.service` | `8a3c1698bedad471e0cc4434570bbe0e6c6a9f0700e58b7cf1d8a8a2a3621741` |
| Proxmox | `/etc/systemd/system/application-b60-heartbeat.timer` | `ee3f390bd520b51d8b426de635bf781693ad872766e58d0cd0f8a98e4cc56a6b` |
| LXC110 | `/usr/local/libexec/aster-a1/a1_key_file.py` | `25f2c82cb09b051f3307341571b3a27c6b2c4f6002c70b5a1a256ed4e8292b36` |
| LXC110 | `/usr/local/libexec/aster-a1/a1_ingress_policy.py` | `07be9c42650f74edbcb080d4b338bb01cc43a6ac18a847d86839c07a0ad65d1d` |
| LXC110 | `/usr/local/sbin/aster-llama-test-key-add` | `10292b91e79ebe30892ef3ce0f9af70a4ecf52b523878d7fd4c1cc8099cca156` |
| LXC110 | `/usr/local/sbin/aster-llama-test-key-status` | `9fa646d7db2974389cbea18a68edd82a868b849fcfdd435578e28d729403c9cf` |
| LXC110 | `/usr/local/sbin/aster-llama-test-key-remove` | `0c294198d2e60b5ed07654c92025713ca6a812bdd065720f3d8183ae6ef357d6` |
| LXC110 | `/usr/local/sbin/aster-llama-ingress-apply` | `41b96f560261a198c09fd85d8ba7150478241fbe6a38f28befad9dc4fa40020b` |
| LXC110 | `/usr/local/sbin/aster-llama-ingress-restore` | `9bf3c3cb1e04081f41584f9dc742d86e9e7ead3a1806a243a6ce3478572ff347` |
| LXC110 | `/usr/local/sbin/aster-llama-production-auth-probe` | `aac604de1f35c048791c5f1cfc21e25d9eb3e679fb7d799f74671307463313ac` |

The Mini-side client remains source-controlled rather than installed by this
packet: `a1_admitted_batch.py` is
`c8913e854f358e1a4753cd4637d036edfa1e19730d1abab0321df724ce748574`,
`a1_headless_client.py` is
`3d9c84735a7338860648215467996ff0f820aff8778acd7f7f42d6325dad6494`, and
`a1_full_path_capture.py` is
`a7bbb2b8fc98dd18c5d748a808e0e838b9c17dd80e84121e2d1e23ad006f9c86`.

## Preflight and sequence

1. Read and record each current destination hash/absence, ownership and mode;
   abort on unexpected files. Record full-stop watchdog unit hashes and states.
2. Copy the Proxmox set atomically, then the LXC110 helper set atomically.
   Preserve the current LXC110 key-file owner/group/mode; do not read or print
   its contents. Do not install credentials.
3. Run `systemd-analyze verify` on all four candidate units, reload systemd,
   run the entrypoint's `--phase plan` as root, and run target-Linux import
   checks for `application_b60_drill_entrypoint`, `application_b60_controller`,
   `application_b60_lease`, `application_b60_watchdog`,
   `application_receipt_boundary`, and `lease_effect_runner` with bytecode
   writes disabled. In LXC110, import-check `a1_ingress_policy` from its
   installed path before accepting the wrapper hashes.
4. Disable both candidate timers and services. Do not enable, start, unmask or
   trigger them. No lease state, lock, receipt, checkpoint or key may exist.
5. Verify all destination hashes, root ownership/modes, inactive/no-PID state,
   unchanged full-stop units, unchanged LXC104/LXC110/LXC116 services, and no
   listener on `192.168.70.10:19104`.

The heartbeat timer is intentionally installed disabled. It is only enabled
inside the later drill after the lease is admitted, and is disabled again in
the release/rollback path.

## Transport and identity

The admission CLI emits one JSON object and accepts only the pinned profile.
The later live packet must expose it through a dedicated forced-command SSH
identity or equivalent restricted local transport. It must not use root SSH,
permit a shell, accept arbitrary arguments, forward agents/ports, or expose
credentials. The forced command may invoke only
`application_admission_cli.py --profile <pinned-profile>` and must use the
already pinned Proxmox host key from the platform transport policy.

## Later drill entrypoint

The only effectful controller path is `/usr/local/sbin/application-b60-drill`.
Its phases are `plan`, `acquire`, `mark-effect`, and `admit`; it accepts only
the fixed root-owned mode-0600 producer paths
`/var/lib/local-ai-lab/application-b60/prelease.json` and
`/var/lib/local-ai-lab/application-b60/sidecar-receipt.json`, and validates
their producer schemas, source-bound backup marker, lease identity and exact
sidecar observation fields. It uses the self-contained allowlisted effect
runner and has no arbitrary command path. The heartbeat timer is enabled only
after `admit`, then runs once per minute. The separate recovery watchdog
remains the rollback authority. A manually created root JSON lacking those
producer schemas is rejected and does not authorize admission.

## Rollback and independent checks

For this disabled packet, disable both candidate timers/services, verify no
candidate process/state/lock, remove only files whose preflight state was
absent, reload systemd, and confirm the full-stop units are byte-identical.
Retain any unexpected state for reconciliation; do not delete ambiguity.

Independent checks must verify every listed hash, root custody, unit syntax,
disabled/inactive state, no listener, unchanged production services, and the
absence of key/ingress/checkpoint/receipt data. This packet does not authorize
the restricted transport identity, timer enablement, key/ACL effects, sidecar
start, model calls, recovery drill, or Git push.
