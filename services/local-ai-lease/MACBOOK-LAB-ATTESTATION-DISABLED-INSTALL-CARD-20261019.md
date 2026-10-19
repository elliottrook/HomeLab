# MacBook lab attestation boundary — disabled-install card

Status: source-only candidate; not installed and not an authorization to add
SSH access, change `authorized_keys`, admit a workload, or start a lease.

## Exact candidate

| Source | SHA-256 | Future target path/mode |
|---|---|---|
| `lab_macbook_forced_command.py` | `76a4bc792c0fd06d3d8e32e5d6adabcd1387595c7947f72bce7a1d944a036b16` | `/usr/local/libexec/local-ai-lease/lab_macbook_forced_command.py`, root:root 0750 |
| `lab_macbook_admission_adapter.py` | `7d04042c4b80efbfc331a21bca2c7e1c6b39d6e459ff76384cfa273e531c3e26` | `/usr/local/libexec/local-ai-lease/lab_macbook_admission_adapter.py`, root:root 0644 |
| `lab_workload_admission.py` | `c128ab7825b525df97c4164f078750a52e1b15f39b4292e4bbcea756a43455fb` | `/usr/local/libexec/local-ai-lease/lab_workload_admission.py`, root:root 0644 |

The target config is a new root:root 0600 file at
`/etc/local-ai-lab/aster-lab-session.json`, containing only the reviewed
principal, client-key fingerprint and Proxmox host-key digest. Its parent must
already be root:root mode 0700; the installer must not create or chmod an
unverified parent. The fresh attestation path is a new root:root mode-0700
directory `/var/lib/local-ai-lab/macbook-attestation`; the writer refuses a
missing, symlinked, or insecure parent.

## Fixed forced-command shape

The future `authorized_keys` entry must be created only after the exact public
key and fingerprint are independently verified. Its shape is:

```text
command="/usr/bin/python3 /usr/local/libexec/local-ai-lease/lab_macbook_forced_command.py",restrict,no-port-forwarding,no-agent-forwarding,no-X11-forwarding ssh-ed25519 <reviewed-key>
```

The key material is intentionally not stored in this repository. The fixed
command reads only the root-custodied config and sshd-established
`SSH_ORIGINAL_COMMAND`/`SSH_CONNECTION`, creates a fresh nonce-bound session
with a 120-second expiry, writes the envelope atomically, and exits. The
consumer loads it through an `O_NOFOLLOW` descriptor, verifies current time
and connection binding, and consumes it once. Request JSON cannot provide a
principal, fingerprint, connection, nonce, or expiry.

## Rollback and gates

Prior state for all three modules, config, attestation directory and
authorized-key entry must be captured as absent or exact old bytes. Rollback
removes only newly added files and empty directories; it does not revoke other
SSH keys or alter the existing administration path. Target-Linux root-custody
positive tests, expired/static replay tests, config custody tests, and a
read-only authenticated-session proof are required before any admission
review. MacBook ingress remains HOLD until those gates and the persistent
supervisor/known-consumer boundary are separately approved.
