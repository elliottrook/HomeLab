# D3 encrypted custody host check — result

**VERIFIED CURRENT STATE:** approved check completed once on LXC 104.
Jason approved the [exact gate](D3-encrypted-custody-gate-2026-10-06.md).
That approval is consumed; it is not authorization for real provisioning.

## Execution and observations

Preflight independently reconfirmed both staging/fixture paths absent, the
transient unit not found, the host key absent and both Aster/approval services
active/running. Staged only the two approved sources, compiled and verified the
combined fingerprint before running:
`fbac03972fc66376bbda43b516cc138c802c2f4f604eec92a186b49a8c7a4b93`.

The exact helper returned:

```json
{
  "runtime_delivery_passed": true,
  "encrypted_source_denied": true,
  "host_key_preexisted": false,
  "real_credentials_used": false,
  "aster_restarted": false
}
```

This establishes a real systemd encrypt/decrypt round trip and delivery through
`LoadCredentialEncrypted` to a temporary process with User=aster. The process
verified only fixed fictional values. Ordinary Aster-UID access to the stored
encrypted source was denied. It does not establish protection against root or
all processes sharing the same UID, nor validate the full Aster deployment.

Independent post-checks found:

- `aster-worker-custody-check-20261006.service`: not found/inactive/dead.
- `/run/aster-worker-custody-check-20261006`: absent.
- Approved staged files rehashed, removed, and
  `/var/tmp/aster-custody-tools-20261006` independently verified absent.
- `/var/lib/systemd/credential.secret`: now exists, UID 0, mode 0400.
  Only metadata was inspected. The key was not printed, copied or deleted.
- `aster-agent.service` and `homelab-broker-approval.service`: active/running.
- Companion page HTTP 200; page reachability only, not a user-login test.

Source: direct SSH/pct execution and separate metadata/systemd/HTTP observations
in this task. No real vault/Authentik credential, human recovery material or
model was used. No permanent unit, identity/group change, Aster restart or push.
The persistent host-key creation was expressly included in the approval.

## Recovery and remaining work

No rollback was needed. Retain the host encryption key; do not treat deleting it
as cleanup, because future credentials may depend on it. Existing LXC backup
scope covers its location; this check did not run or verify a backup/restore.

The delivery primitive is now supported by host evidence. Real provisioning,
protected controller transport, Authentik access binding, Mac Keychain access
validation and the gateway mount still require completion and their deployment
approval. The proposed credential drop-in remains uninstalled; delegation stays
disabled. Do not reopen the human recovery ceremony until those preparations
are ready. Jason's recovery keys remain human-held and available.
