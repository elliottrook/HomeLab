# M1 independent-ingress passkey configuration candidate — 2026-10-25

> Result: **OFFLINE CANDIDATE PASS; NOT INSTALLED OR ENABLED**

## Purpose

The permanent independent approval ingress deliberately runs Yellow-only. Its
factory passes an empty passkey-ACR set, so Red approvals and management
mutations fail closed even after a fresh Companion passkey ceremony. The older
verified Authentik mapping already emits the dedicated claim
`urn:homelab:aster:webauthn:1`; generic MFA and ordinary login claims are not
equivalent.

This candidate adds a narrow operator configuration boundary. Missing or blank
configuration preserves Yellow-only mode. The factory accepts exactly the
reviewed Aster WebAuthn ACR and rejects generic, alternate, repeated or
multi-value mappings before the listener binds.

## Candidate pins

| File | SHA-256 |
| --- | --- |
| `services/aster-agent/approval_passkey_config.py` | `e99123190eadbc0d9b1ecd77dcaa000a5d5c185078743e358fa85e39cb11cb2f` |
| `services/aster-agent/approval_ingress_service.py` | `6596cdd2300ee0fc1848fda89e0c72fd9591a5c96b62a55fa4a086f6032db40a` |
| `services/aster-agent/test_approval_passkey_config.py` | `de9217ac873388f16cc2fad14d248a1f2319f3b88c7e02e44eaf5d1d16b3414c` |
| `services/aster-agent/test_approval_ingress_service.py` | `9cce9fd1ea410679bd253b64adf87b7e025490046b98bb8f852acc8e35cbf126` |

## Validation

- dependency-free configuration tests: 3/3 passed on the Mac;
- candidate factory plus approval route/socket/broker tests: 31/31 passed in
  LXC104's existing Python environment using an in-memory source bundle;
- the adjacent live `approval_ingress.py` and `broker_approvals.py` hashes
  exactly match the reviewed branch source; and
- no file was copied to LXC104, no service or environment changed, no passkey
  token or credential was read, and no approval or management action ran.

The target emitted an existing Starlette deprecation warning about its TestClient
dependency. It did not affect the 31 passing assertions and is not a release
claim about a dependency upgrade.

## Separate live gate

A future exact installation must checkpoint the current ingress source and
owner-only environment, install only the two runtime files above, add exactly
`ASTER_APPROVAL_PASSKEY_ACRS=urn:homelab:aster:webauthn:1`, and restart only
`aster-approval-ingress.service`. Before any Red or management mutation, verify:

1. blank configuration still yields `passkey_verified=false` in an isolated
   target-side test;
2. ordinary signed-in tokens and generic MFA remain non-passkey;
3. one fresh Companion passkey ceremony yields `passkey_verified=true` with
   a current integer authentication time;
4. stale/future/missing authentication time still denies Red and management;
5. Yellow approval, wrong-caller denial, duplicate-consumption denial and
   broker restart recovery remain unchanged; and
6. rollback restores the prior source and environment and returns the service
   to its current Yellow-only state.

That installation and ceremony need a separate reviewed approval. This offline
candidate does not enable Red, management, a capability grant or a tool.
