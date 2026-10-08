# D3 approved vault maintenance — 2026-10-08

Jason unlocked the vault privately and approved continuation on October 8.
Preflight confirms 2.6.3 initialized/unsealed, active broker/approval/Aster,
unchanged config and public certificate hashes from the October 6 gate, and
available backup space. No recovery secrets were read by the agent.

The Doctor catalogue warning corresponds to intentionally retained September 27
repair-test metadata, documented in `M1-stage2-repair-2026-09-27.md`: service
disabled, agent retired, no execution adapter. Preserve this history; reconcile
the checker narrowly rather than deleting records or ignoring arbitrary drift.

The expired local download was fetched again from the same official 2.6.4 release.
Detached signature passed against primary fingerprint
`66D15FDD87287219C8E15478D200CD702853E6D0`; package SHA-256 remains
`09e0b4ced4cfa2f04a3573c5ec05c94ecd4f858d580d76c7422c51b99b74cce1`.

Authorized operation retains the exact approved remote names:
`/var/tmp/aster-openbao-264-20261006` and
`aster-pre-openbao-264-20261006`. Their date denotes the reviewed plan, not the
execution date. A fresh archive will have the actual October 8 timestamp.

## Installed; awaiting human unseal

Stopped only OpenBao, created the approved snapshot, and completed fresh archive
`/mnt/backups/dump/vzdump-lxc-117-2026_10_08-14_23_45.tar.zst` on Proxmox.
The timestamp is the host-generated filename. Complete `zstd -t` passed;
archive SHA-256 is
`9575162f57fa9285ac53838fa5b922fd12815c9b9d4ef875d3a74e89a85d62d5`.
This is archive integrity evidence, not a new isolated restore test.
No old backups or snapshots were removed.

Installed the exact verified package with existing configuration retained.
Package postinstall confirmed the existing TLS key/certificate were preserved.
Reloaded systemd and started only OpenBao. CLI and TLS health both confirm 2.6.4;
vault is initialized and sealed, as expected after restart. Configuration and
public certificate hashes match preflight. User/group remain `openbao`, effective
`MemorySwapMax=0`, API listeners remain loopback and `192.168.50.24:8200`.
Broker, approval and Aster services remain active. No delegation credentials
were issued, no policy changed and no privileged target request executed.

NEXT: Jason privately unseals with two different decrypted shares. Verify health
from broker, retained metadata/agent retirement and sanitized Doctor result;
reconcile the exact retired fixture in the checker without accepting arbitrary
extra entries. Remove only approved package staging after complete validation.
Staging remains intentionally present until then. No push authorized/performed.

Resume carefully: verify live service, snapshot/archive and package state before
repeating any operation. Maintenance is not complete until private human unseal
and post-update validation. Never read recovery-share or private-key contents.
