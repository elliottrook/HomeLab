# D3 protected controller and vault patch prerequisite

## Controller preparation — LOCAL CANDIDATE

`provision_controller.py`, `provision_node.py` and `provision_journal.py` now join
inactive identity creation, vault writes, encrypted gateway delivery and Mac
Keychain receipt over owned SSH subprocess pipes. Remote sources must match local
manifest hashes before import. Secret frames are consumed inside the controller,
not printed as command results. No model starts and no identity activates.

The private SQLite journal records recognized stages and allowlisted object IDs
only. It commits write intent before the corresponding source-side operation.
An existing run directory cannot be reused. Lost acknowledgements retain uncertainty
and do not trigger issuance retries or name-based cleanup. Vault administrative
material remains source-local in a root-only runtime handoff file, is never sent
to the Mac, and must be revoked after vault operations; a missing revocation ACK
remains uncertainty. Root/recovery material is not ordinary controller input.

184 local tests pass, including successful fixture handoff, lost gateway ACK,
Keychain failure, forged early completion, absent approval and secret-shaped
journal rejection. The node/controller syntax compiles. These are fixture tests,
not end-to-end proof with real credentials or deployed services. Source-local
administrative handoff, staging, crash cleanup and human ceremony still need
integration validation. The temporary admin token must be specific to this
approved operation, not a reused standing administrator token. No helper has
been installed remotely; no administrator material was read.

## Verified prerequisite problem

LXC 117 runs OpenBao **2.6.3**. The official October 1 advisory
[GHSA-7m59-mp95-w6ph](https://github.com/openbao/openbao/security/advisories/GHSA-7m59-mp95-w6ph)
reports that AppRole SecretIDs can be accepted after expiry until periodic cleanup;
the fix is in 2.6.4/2.7.1. Maintainer severity is low (2.1), and cleanup normally
runs every minute. This finding is not evidence of compromise or indefinite
credential validity. No exploit test was performed.

The new 24-hour SecretID proposal must not claim strict expiry on this installed
version. Recommendation: patch within the existing 2.6 series before new issuance.
The candidate vault endpoint now requires exactly reviewed 2.6.4 health before
opening administrative custody. Successful storage tests do not override this
prerequisite. Existing service policy/expiry mechanisms were not modified.

## Artifact verified locally

- Release: [OpenBao v2.6.4](https://github.com/openbao/openbao/releases/tag/v2.6.4).
- Package: `openbao_2.6.4_linux_amd64.deb`, ordinary non-HSM amd64 package.
- SHA-256: `09e0b4ced4cfa2f04a3573c5ec05c94ecd4f858d580d76c7422c51b99b74cce1`.
- Primary signing key: `66D15FDD87287219C8E15478D200CD702853E6D0`, independently
  matched to the [official installation documentation](https://openbao.org/docs/install/).
- Both package and checksum-file detached GPG signatures passed; package hash
  matches the signed checksum file. Isolated temporary GPG home; no human keyring.
- Local staging: `/private/tmp/aster-openbao-2.6.4-review`.
- Package metadata and maintainer scripts inspected locally. Dependency is
  `openssl`; preinstall creates its system user only if absent. Postinstall exits
  without replacing TLS material if the existing certificate/key are present;
  both were confirmed present by metadata-only checks. No install has occurred.

## Live read-only recovery baseline

LXC 117 is the existing unprivileged Debian 13 amd64 container, 16 GiB local-lvm
root disk, two cores and 2 GiB RAM. Its existing snapshot is
`ai-pam-pre-m6-root-recovery`; do not overwrite or remove it. Proposed new snapshot
name `aster-pre-openbao-264-20261006` is absent. OpenBao is active as its dedicated
service user and effective `MemorySwapMax=0`. Installed apt metadata offers only
2.6.3, so a pinned verified package is needed; no apt repository alteration.

Backup storage `backups` is active with about 2.6 TiB available. Latest listed
LXC 117 archive is `backups:backup/vzdump-lxc-117-2026_10_06-02_46_36.tar.zst`
(380,161,288 bytes). Listing proves existence, not integrity or current restore
success. A fresh cold-service checkpoint/archive is required before the update.

## Exact requested maintenance approval

Approve updating **only OpenBao on LXC 117 from 2.6.3 to verified 2.6.4**, including:

1. Recheck baseline/version, public TLS/config hashes, archive space, package
   hash, destination absence and human availability with the recovery shares.
   Abort on drift. No recovery keys are entered in chat or agent tool input.
2. Copy the verified package to fresh root-owned staging
   `/var/tmp/aster-openbao-264-20261006`, verify it again, and record package/unit
   metadata. Do not install other packages or change repositories.
3. Stop only `openbao.service`. With the vault stopped, create the new Proxmox
   snapshot `aster-pre-openbao-264-20261006` and a fresh LXC 117 archive on
   `backups` (`vzdump`, snapshot mode, zstd, no removal/pruning). Confirm archive
   completion and compressed-stream integrity before package installation.
   Do not expose archive contents. If checkpoint/backup fails, do not update.
4. Install the exact package, preserving existing configuration/TLS/data and
   systemd overrides. Reload systemd and start only OpenBao. Confirm 2.6.4,
   expected seal state, listeners, service identity and no-swap setting.
5. Jason supplies the two shares through the existing human-only terminal path
   to unseal. A direct terminal `bao operator unseal` prompt hides its input;
   never put a share in arguments, chat, scripts, environment or recorded output.
   No new root token or administrator ceremony is needed just to unseal.
6. Verify unsealed health from the existing broker network path, unchanged TLS/
   configuration, broker/approval/Aster health and sanitized Doctor result.
   Do not issue delegation credentials or a privileged test request.
7. Retain the new snapshot/archive and metadata; remove only this package staging
   after successful validation. Do not delete existing backups or recovery copies.

Impact: vault-dependent AI-PAM operations are unavailable from stop until human
unseal. No automatic time guarantee: backup duration and human interaction govern
the maintenance window. Ordinary applications are not being restarted. Jason's
keys are available but must be ready before stopping the vault. No push included.

Rollback: before new vault administrative changes, if package/start validation
fails, stop the vault and restore the newly created complete LXC checkpoint,
then start and human-unseal the old version. Preserve the failed-state evidence.
Do not merely downgrade the binary against possibly changed state. If new vault
writes have been accepted or checkpoint recovery is uncertain, pause for review
instead of rolling state backwards blindly. Rollback restores the known expiry
limitation, so keep new delegation provisioning blocked.

This is a new production/security maintenance action; repository AGENTS.md
requires explicit confirmation. No maintenance has begun. All prior custody
check approvals are consumed and do not authorize this update.

## Resume after maintenance

### Approved preflight paused — 2026-10-06

Jason approved the bounded update in chat. Read-only preflight reconfirmed the
package hash, version 2.6.3, staging/snapshot absence and backup space. However,
the vault is already sealed: health and seal-status both report `sealed=true`,
Shamir threshold 2 of 3, progress 0, Raft storage. Service/container start times
are October 5 at 16:29:22/16:29:20 UTC; service restart count is zero. A container
start is consistent with the sealed state, but does not prove its cause or explain
why it remained sealed. Broker, approval and Aster services are active; that alone
does not prove their vault-dependent operations work.

No production mutation was performed. Per the approved abort-on-drift gate,
establish an unsealed healthy baseline through Jason's private terminal before
stopping, backing up or installing. The bounded patch approval remains recorded;
no additional approval is needed for the same scope once the baseline is healthy.
Do not treat the existing sealed state as an update result. Recovery shares must
never enter chat/tool input. Config SHA-256 before maintenance:
`331bd87de4e6226deafdb872f92b7877ce905b0db8fdb62fadd24c694834ec9a`;
public TLS certificate SHA-256:
`86fa3b74acf9aff4df1cefd2aef54763d70d431fa0ee289ac9f3642ec3c5bf74`.

Finish protected staging and the complete human administrator ceremony instructions,
then review one inactive-identity/credential provisioning deployment. Keep gateway
delegation disabled. The no-tools pilot and later sysadmin tool authority remain
separate gates. The controller is prepared locally, not production-qualified.
