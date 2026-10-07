# Aster Codex worker — credential registry candidate

Integration status: **candidate, not registered or issued**. Owner/operator:
Jason. Review: 2026-10-06. Programme: Aster Adaptive Computing D3. This follows
the existing AI-PAM service-registry template and conveys no new authority.

## AI authority

Posture: production integration not yet supported. Proposed identity:
`aster-codex-worker-mac`, initially probationary, no target-system credentials.
Authentik M2M authentication identifies the worker; it is not human approval or
AI-PAM delegation. Proposed broker execution mode: none for workload transport;
future infrastructure tools must separately use existing broker capabilities.
Human break-glass remains direct human administration and the existing vault
recovery procedure, independent of Aster.

| Capability | Scope | Risk/approval | Explicit denials |
|---|---|---|---|
| Workload authentication | Assigned worker offers, receipts, controls, final result and numeric usage only | Identity configuration is a reviewed security change; no automatic privilege promotion | No user impersonation, queue-wide enumeration, job creation or approval |
| Fictional model pilot | One immutable pre-approved payload, model and scope | Explicit connected-test approval | No tools, real personal/lab context, API fallback or replay |
| Infrastructure operation | Not granted | Separate future capability and human approval | No SSH/root/general shell or target credentials |

## Credential custody proposal and unresolved facts

Update: [custody adapters and a manual connected-worker candidate](D3-custody-and-worker-preparation-2026-10-06.md)
are implemented locally with 163 passing tests. Exact proposed role/policy inputs
and pilot TTLs are recorded there. Provisioning, runtime delivery and Keychain
access checks remain incomplete; neither secret has been issued or accessed.

Two independent credentials are required:

1. Mac worker's Authentik service-account credential. Proposed authoritative
   custody record `secret/ai-pam/aster-codex-worker`; consumer only the worker's
   protected source-local credential mechanism. Existing signed Companion
   Keychain storage proves an available platform primitive, not permission to
   reuse the human login item. A distinct item/access policy and supported
   provisioning/rotation path must be established before any issuance.
2. Gateway's Authentik confidential-provider introspection credential. Proposed
   custody record `secret/ai-pam/aster-worker-introspection`; consumer only the
   LXC 104 verifier through a dedicated least-privilege vault retrieval identity.
   Never add this secret to the model context, user token or Mac worker identity.

Both vault paths and retrieval roles are **proposals, not verified existing
state**. Exact role/policy creation authority, bootstrap path, source-local
consumer identity, rotation interval and revocation runbook remain to be
prepared. No approved static-file exception exists. Do not install permanent
credentials until these facts are resolved and the change is approved.

Repository evidence records restricted existing OpenBao service AppRoles and a
human-only root ceremony requiring independent recovery shares. Do not infer
that current Forgejo roles can administer the vault. Do not retrieve recovery
shares or request them in chat. Human participation may be needed if no narrower
supported administrative mechanism is available; verify before asking.

Revocation design: disable issuance/service identity and revoke issued tokens;
gateway performs online introspection on every request, with no positive cache.
Global AI-PAM disable additionally denies worker access once the status callback
is deployed/wired. Gateway/issuer/vault/control outages must deny new dispatch;
in-flight stopping is best effort until a provider terminal event confirms it.
Exact live propagation and recovery behavior need deployment evidence.

## Network and data

Mac initiates TLS to private `aster.elliottrook.com` and `auth.elliottrook.com`.
No inbound Mac listener or new public ingress. Mac-to-Authentik TLS and temporary
token revocation passed; authenticated Mac-to-production-Aster worker routes are
not deployed. Existing gateway-to-vault route and permitted identity for this new
integration require verification. Models receive only approved request content;
bearer tokens, app passwords, provider secrets, AppRole material and recovery
information must never enter prompts, Git, audit payloads or routine logs.

## Validation/lifecycle checklist status

Passed: temporary identity issuance/revocation; Mac TLS identity path; fixture
wrong-owner/worker/scope denial; duplicate admission protection; local global
switch status/peer-denial tests; real fictional answer/usage; one confirmed stop.
Retained failure: first live stop reporting returned unknown despite later saved
provider interruption. Cause not established.

Outstanding: production identity probation/revocation controls, cross-client
credential misuse denial, actual custody/bootstrap/rotation, vault outage,
restore/recovery, global switch wired end-to-end, native UI observation, gateway
deployment and post-change monitoring. All temporary identity objects from both
approved tests were independently verified absent. No permanent credential exists
as a result of this programme's tests.

## Integration ownership

Doctor/monitoring: add non-secret worker availability and dependency status with
deployment, not a new monitoring stack. Backups: include approved non-secret
configuration and durable duplicate-protection state; treat credential backup
through approved vault/Keychain recovery separately. NetBox/DNS/firewall/Homepage:
no new resource proposed. Wiki/mirror/runbooks: update only with proven deployment
facts after approval. Repository retains candidate configuration and evidence;
Jason retains security-change and promotion authority.
