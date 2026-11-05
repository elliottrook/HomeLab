# SA4 first target and key-custody owner review — 2026-11-05

## Recommendation

Use a purpose-built, inert canary adapter on LXC 104 as SA4's first genuine
target. Do not repair an existing production source, generated report,
credential, service file or rollback checkpoint.

Read-only inventory found no existing file that meets the whole first-effect
boundary. The live Aster source-report files are root:`aster` mode 0640 and
periodically regenerated, so a repair would race their declared producer.
Installed Python modules require a service restart to take effect. Existing
root-owned mode-0644 files under `/var/lib/aster` are retained rollback
checkpoints and must not become repair targets. The proposed SA4 directory,
target and checkpoint directory are all currently absent.

## Exact target candidate

| Field | Frozen proposal |
|---|---|
| target ID | `sa4-lxc104-canary-adapter-v1` |
| host | LXC 104 only |
| target | `/var/lib/aster/sa4/canary-adapter.json` |
| custody | root:root, regular file, one link, mode 0644 |
| classification | low-criticality read-only canary adapter |
| maximum bytes | 4096 |
| checkpoint parent | `/var/lib/aster/sa4/checkpoints`, root:root mode 0700 |
| temporary path | `/var/lib/aster/sa4/.canary-adapter.json.sa4-tmp` |
| service restart | forbidden and unnecessary |
| network/credential/model effect | none |
| automatic retry/routing | off |

The initially installed inert drift fixture is canonical 82-byte JSON with
SHA-256 `19b4e02d7f4edd9b38d9a0c3e9e3b49c4209473694fab39db0494c5fe523df1a`.
The exact proposed repair artifact is canonical 82-byte JSON with SHA-256
`4529dee5c9b58b607a9025b62aa3a4871660de98c4bafbb7fd69d7bc2a1e1065`.
Both exact files are retained under `scripts/aster-adaptive/fixtures/`.
Two focused tests verify canonical bytes, exact digests, size, distinct states
and that the production registry remains empty. The complete SA4 suite passes
**59/59**.

The consumer-health postcheck will be a fixed, content-free validator that
opens only the compiled path with `O_RDONLY|O_NOFOLLOW|O_CLOEXEC`, accepts only
the canonical `healthy` fixture, and exposes no general path or command input.
The canary is not read by normal Aster requests, so its initial drifted state
cannot degrade production. This proves the repair transaction and recovery
boundary without making an existing service the first write target.

## Three-way key custody

Only public RSA-2048 keys and their digests will be compiled after review.
Private keys must remain outside Git and outside model context:

1. **Owner approval key:** human-controlled Mac signing surface. Its private
   key is not exported or read by Codex; only a detached exact-plan approval
   crosses into the packet.
2. **AI-PAM grant key:** broker-controlled signing identity, separate from the
   owner device and operation owner. It signs only a one-use exact target/plan
   grant after policy checks.
3. **Independent observer key:** a dedicated observer identity on the Proxmox
   control plane, distinct from the LXC 104 operation owner. It signs only
   content-free postcheck/rollback receipts after its own measurements.

No role may nominate a runtime key or sign another role's payload. Key
creation, custody installation, rotation/revocation and public-key compilation
form a separate credential/change packet. This review does not authorize
reading Keychain, exporting private material, adding broker access or creating
those keys.

## Recovery and stop boundary

The transaction holds the shared operation lock, uses the one-use grant ledger
and retains the checkpoint. Any failed, stale, missing or uncertain postcheck
requires rollback observation and terminal reconciliation; it never retries.
The canary directory and files can later be removed under a separately reviewed
cleanup only after evidence retention is satisfied. Core Aster operation does
not depend on the canary.

## Owner decision requested

Approve or reject this exact canary target and three-way custody split as the
SA4 release-candidate design. Approval permits only the next source packet:
compiled target registration, fixed validator programs and public-key slots.
It does **not** authorize private-key access or installation, a live target,
grant, checkpoint, repair, restart, route, model change or deployment. Those
remain later exact gates, and the first repair effect still requires immediate
specific approval.
