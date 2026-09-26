# M1 Stage2 candidate — explicit approver and assurance boundary

Status: offline candidate and threat review; **not deployment-ready**.
Owner: Jason. Implementation owner: shared AI-PAM/Aster work, coordinated with
AI-PAM before overlapping code edits. Stage1 is deployed; this does not graduate M1.

## Smallest useful change

Retain the already tested local candidate in `broker_approval_service.py` and
`services/aster-agent/broker_approvals.py`: require the explicit hashed subject
allowlist at both entrypoints, require actor metadata on every approval-socket
read/write, and recognize passkey assurance only through an operator-configured
verified claim mapping. No new model, router, credential broker or authority
framework is needed. Empty allowlists fail closed. Yellow may continue for an
explicitly entitled authenticated subject; Red and management mutations require
fresh, verified passkey assurance. Existing app binding is defense in depth,
not an entitlement substitute.

This proposed change is **not** a complete separation of intelligence from
authority: the allowed Aster process still supplies actor/assurance metadata to
the approval socket. A compromised Aster process can assert an allowed actor.
Do not call a subject-hash allowlist a cryptographic proof of approver presence.
A separate minimal approval ingress/verification process is the next architecture
option if this trust assumption is unacceptable. That requires its own UID,
network/API and client compatibility review; it is not silently included here.

## Evidence and unresolved dependency

Verified source-local inspection of installed Authentik2026.8 found generic ACR
and generic MFA classification. The selected flow requires WebAuthn, but flow
selection, a device flag, generic `mfa`, or a recent `auth_time` does not establish
a signed, session-derived passkey-specific claim for the actual Companion token.
The candidate's passkey-ACR allowlist therefore remains empty. No mapping is
invented and no raw bearer token or session database is requested.

Stage1 deployment record and M1 deployment-plan Stage2 section retain the exact
observations and official references. These observations are time-specific; a
future candidate must reverify installed behavior and actual claim projection.

The smallest **safe experimental step** is a source-local claim-verification
probe in a separately approved authentication test flow, using a fresh real
Jason session. Retain only booleans/claim names, issuer/audience-match outcomes,
assurance category and age checks. Never export tokens, cookies, private keys,
credential identifiers or raw session contents. Actual fresh login requires human
participation; offline fixtures cannot establish it. No provider mapping or flow
is authorized by this design.

## Acceptance matrix before any Stage2 rollout

| Input / condition | Required result |
|---|---|
| Missing/unknown subject or empty entitlement config | Deny reads and mutations before broker call |
| Valid signature but wrong issuer/audience | Deny at ingress |
| Forged client actor/assurance fields | Reject schema; derive only from validated claims |
| Generic ACR, generic MFA, password/TOTP or absent claim | Never label passkey; Red/management deny |
| Proven approved passkey category + entitled owner | Yellow allowed; Red/management only with fresh integer auth_time |
| Boolean/string/future/stale auth_time | Red/management deny |
| Token refresh without fresh proof | Must not manufacture fresh authentication |
| Provider/JWKS outage, invalid signature, missing key | Fail closed; no fallback to API key for approval |
| Cross-owner access and removed entitlement | Deny; invalidate relevant cached authorization |
| Broker/Companion version mismatch | Stop rollout; compatibility test before enabling requests |
| Deny/revoke/emergency path during assurance outage | Human SSH remains; validate no unsafe automatic reenable |
| Compromised Aster allowed UID | Residual trust risk explicitly accepted or isolated ingress required |

Offline tests already cover entitlement/assurance/default deny and broker fresh
actor behavior. They are necessary, not evidence that the installed issuer emits
the required claim. Do not reuse the generic provider ACR as the positive fixture
for a claimed production passkey test.

## Exact intended deployment boundary (must be finalized later)

Candidate files: approval service, Companion approval bridge and the narrow
`aster_agent.py` configuration wiring already present locally. Operator config:
explicit approver subject hash at both services and **only a verified** provider
assurance mapping. Unit/drop-in changes must be enumerated and pinned after the
claim experiment; no secrets in Git. Restart only affected approval/Aster services,
with broker/gateway maintenance coordination and bounded socket/HTTP readiness.
No broker core change, new grant, credential rotation, firewall or provider-flow
change may be hidden in this release. The approved Stage1 install is not authority
for this deployment.

Do not request deployment approval yet: the exact verified mapping, endpoint
compatibility result and availability impact are not established. Deliberately
disabling Red/management with an empty mapping is an alternative risk decision,
not an accidental outcome of deploying the candidate. Jason must choose that
tradeoff explicitly if used.

## Recovery and stop conditions

Capture source/config hashes and protected DB checkpoint after coordination,
verify backup/restore, and run synthetic compatibility/denial tests first. Unit
readiness must be application-level, not only `systemctl is-active`. Retain a
human SSH path that does not depend on the new assurance mapping.

On failed identity/assurance/integrity checks, keep approval mutations disabled;
stop the affected approval ingress and approval service. Leave the Stage1 core
and read/write gateway files unchanged. Do not restore an older DB, resurrect
approvals, remove entitlement checks or reenable broad old approval behavior as
an automatic rollback. A corrected restrictive configuration or separately
reviewed isolated ingress is the recovery path. Aster chat interruption and
Companion management availability must be measured/accepted in the final plan.

No automatic permission expansion, auto-promotion or model-written safety policy.
Proposal, token verification, authorization, effect execution and audit remain
separate responsibilities even where current process isolation is incomplete.
