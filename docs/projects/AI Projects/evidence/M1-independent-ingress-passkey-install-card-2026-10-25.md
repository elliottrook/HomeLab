# M1 independent-ingress passkey installation card — 2026-10-25

> State: **READY FOR ONE BOUNDED LIVE APPROVAL**
>
> Source: Stream A commit `38f4346c`

## Intended change

Move the already released independent approval ingress from Yellow-only to a
strictly configured passkey-aware candidate. Install two pinned runtime files
on LXC104 and add one fixed, non-secret environment setting:

```text
ASTER_APPROVAL_PASSKEY_ACRS=urn:homelab:aster:webauthn:1
```

This exact ACR is the dedicated claim emitted by the previously accepted
Authentik Aster Companion WebAuthn mapping. The candidate rejects generic MFA,
alternate ACRs and lists before opening its listener.

| Target | Candidate SHA-256 |
| --- | --- |
| `/opt/aster-agent/approval_passkey_config.py` | `e99123190eadbc0d9b1ecd77dcaa000a5d5c185078743e358fa85e39cb11cb2f` |
| `/opt/aster-agent/approval_ingress_service.py` | `6596cdd2300ee0fc1848fda89e0c72fd9591a5c96b62a55fa4a086f6032db40a` |

The source tests are pinned in the companion offline evidence. The candidate
passed 31/31 approval factory, HTTP, socket and broker assertions in LXC104's
existing Python environment without writing a target file.

## Precondition and checkpoint

1. Require both `aster-approval-ingress.service` and
   `homelab-broker-approval-independent.service` active and enabled, ordinary
   Aster healthy, and no pending or approved-unconsumed request.
2. Require `/opt/aster-agent/approval_passkey_config.py` absent and the live
   `approval_ingress_service.py` hash equal the current Yellow-only baseline
   `e613587f8fb2bd82c4f92b4d1135ac15aa5acc4982feaf8f1b82428feb62eff8`.
3. Require `/etc/aster/approval-ingress.env` root:`aster-approval`, mode 0640,
   with no existing `ASTER_APPROVAL_PASSKEY_ACRS` line. Do not print the file.
4. Create a fresh root-only mode-0700 rollback directory containing the old
   service source, the exact environment bytes and metadata. Hash the copies
   without displaying environment contents.

Any mismatch means stop before installation.

## Bounded installation and validation

1. Stage only the two pinned runtime files, verify their hashes, then install
   them root-owned mode 0644.
2. Append the exact fixed environment line using a root-only temporary file,
   preserve owner/mode and atomically replace the environment file. Never
   print it.
3. Run target-Python import and the same 31-test in-memory candidate suite.
4. Restart only `aster-approval-ingress.service`; do not restart the broker,
   Aster Agent, Authentik, OpenBao or llama.cpp.
5. Verify the new process, listener, unauthenticated denial, ordinary signed-in
   Yellow path, wrong-caller denial and unchanged broker database checkpoint.
6. Perform one fresh Companion passkey ceremony and require `/session` to show
   authorized, passkey verified and fresh. Exercise no Red approval or
   management mutation in this installation check.
7. Verify an isolated generic-MFA token remains non-passkey and stale,
   future, missing or Boolean authentication time cannot authorize Red or
   management.

The human fresh-passkey observation proves claim transport only. A later Red
or management ceremony remains its own capability/effect decision.

## Rollback

On any failed or uncertain check, stop the ingress, restore the exact prior
service source and environment bytes from the new checkpoint, remove only the
new config module, restart the ingress and verify Yellow approval plus
Red/management denial. Preserve the failed candidate and bounded diagnostics
outside the live path. Do not alter the broker database.

## Explicit exclusions

This card does not approve or consume a Red request, perform a management
mutation, create/revoke a grant, change Authentik, change NPM/OPNsense, expose
the management network path, call a model, deploy NLU, or push Git. Those
effects remain separate gates.
