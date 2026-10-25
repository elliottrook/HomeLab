# M1 independent-ingress passkey installation result — 2026-10-25

> Result: **INSTALLATION PASS; LIVE CLAIM TRANSPORT CHECK PENDING**
>
> Candidate source: `38f4346c`
>
> Installation card: `85a684f6`

## Installed boundary

Jason approved the bounded installation. LXC104 now contains the two pinned
runtime files and the exact non-secret mapping
`ASTER_APPROVAL_PASSKEY_ACRS=urn:homelab:aster:webauthn:1`:

| Target | Installed SHA-256 |
| --- | --- |
| `/opt/aster-agent/approval_passkey_config.py` | `e99123190eadbc0d9b1ecd77dcaa000a5d5c185078743e358fa85e39cb11cb2f` |
| `/opt/aster-agent/approval_ingress_service.py` | `6596cdd2300ee0fc1848fda89e0c72fd9591a5c96b62a55fa4a086f6032db40a` |

Both files are root-owned mode 0644. The protected environment remains
root:`aster-approval` mode 0640. The prior service source and exact environment
bytes are held in the root-only rollback checkpoint
`/root/aster-approval-rollbacks/passkey-acr-20261025T103206`.

## Validation

- The first target test invocation used an invalid `unittest` path form and
  stopped before any live file changed. The corrected discovery command then
  passed the seven configuration/factory assertions before installation.
- The complete approval route, socket, broker, factory and passkey suite passed
  **31/31** against the target Python environment after installation.
- Only `aster-approval-ingress.service` restarted. It is active on port 9121;
  an unauthenticated session request returns 401.
- Aster Agent and the independent approval broker remained active. The ordinary
  Aster health endpoint passed and its process/listener were not restarted.
- The broker database SHA-256 remained
  `db583d652cc2ec152a0f730c136b8168b7e8ecdb4bf1cfb736a828f3f5486d9e`,
  with zero live pending or approved-unconsumed requests.
- No approval, management mutation, capability grant, model call or network
  change occurred.

## Remaining live check

Opening AI-PAM Approvals showed no pending items. Selecting Management made the
window unavailable to accessibility automation while the Companion process
remained alive and completed its four read-only HTTP refreshes successfully.
Source inspection then established that selecting this tab does **not** invoke
fresh authentication; only effect-bearing approval and management buttons do.
The observation is therefore neither a passkey attempt nor proof that the new
ingress observed `passkey_verified=true`.

The installation therefore remains a stable fail-closed candidate. Complete
one human passkey prompt and then read only the approval session result. The
installed Companion currently has no non-effecting control that performs those
two steps together, so a separately reviewed read-only UI candidate is required.
Do not
exercise a Red approval or management mutation. Until that observation passes,
claim transport is pending and no higher authority is released.
