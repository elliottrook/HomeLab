# M1 Stage2 — authorized availability and passkey repair

Status: deployed; real iPhone signed-session and workflow acceptance pending.
Owner: Jason. Authorization: on 2026-09-27 Jason explicitly said **“Authorize full
repair”**, following the recommendation to complete identity/passkey checks and
restore the previously accepted AI-PAM approvals and management. This is a bounded
Stream A corrective amendment to Adaptive Computing M1 Stage2, linked to AI-PAM.
It supersedes the proposed limited interim recovery for this incident.

## Scope and risk assessment

Targets: existing Authentik Companion provider 26 on LXC 106; Aster approval bridge
and approval daemon on LXC 104; corresponding local source, tests and operational
records. Permit an application-specific claim mapping, exact existing-owner
allowlists at both entrypoints, compatible approval daemon/configuration updates,
protected checkpoints and isolated restore checks, bounded service restarts,
synthetic approval/management tests and real iPhone acceptance. No general broker
grants, production target operations, core/transport replacement, authentication
weakening, credential rotation, public ingress, firewall, DNS, guest or storage
changes. Git pushes remain separately gated. Drift-baseline acceptance is not
implied by this repair authorization.

Existing versions: Authentik 2026.8.0; Aster and broker active. The dedicated login
flow requires WebAuthn with user verification, zero reuse threshold and denial
for unconfigured users; provider is owner-only and includes claims in tokens.
Existing bridge configuration is empty; old approval daemon lacks subject
allowlists. No pending/approved broker request or active lab job at investigation.
Reverify immediately before activation.

Primary risks: incorrect assurance could admit a non-passkey login; inconsistent
components could prolong the outage; backups/logs could expose credentials.
Controls: trusted token-session login-event evidence, exact provider/subject
binding, negative tests for ordinary/generic/stale/refreshed/cross-user claims,
matching allowlists, protected local-to-host checkpoints, no raw token/session
output, staged activation and actual signed-session test. No production request
is approved as a test. Existing Aster process remains in the approval trust base;
this repair does not claim independent cryptographic verification at the Unix
socket. Human SSH recovery remains available.

Planned authentication change: add one provider-specific `openid` scope mapping
that emits a dedicated ACR only when the token's own successful login event proves
WebAuthn use through the dedicated validated flow. Do not alter existing shared
scope mappings, login flow, device registrations, token lifetimes or provider key.
Do not infer assurance from user/device enrollment, a constant flow policy, generic
MFA or the current wall clock. Refresh retains the original authentication time.
Fail closed if event/session provenance is absent, malformed or inconsistent.

Availability: brief Aster/approval interruption during coordinated restart;
Authentik mapping changes require no Authentik restart. Capture provider mapping
membership/expression recovery and verified protected DB backup; preserve existing
Aster/approval source/drop-ins and SQLite backup/restore proof. On failure remove
only the new mapping/drop-ins as appropriate, leave privileged approval disabled,
retain failed evidence, restore chat availability. Never restore an old broker DB
over subsequent actions or remove entitlement/assurance checks to reopen access.

## Gates and resumability

- [x] Exact source-backed claim design and local negative tests.
- [x] Installed Authentik evaluator tests and source-local provenance checks.
- [x] Protected checkpoint and isolated restore checks.
- [x] Coordinated provider mapping, exact-owner configurations and matching daemon.
- [x] Denial regressions, readiness/health and unchanged neighboring service hashes.
- [ ] Fresh real iPhone session proves signed passkey claim; approval/deny and
      management workflow accepted without performing production target actions.
- [x] Monitoring readiness, documentation/evidence and local commit.

Current safe resume: do not redeploy. Read this record, Git status and live hashes;
ask Jason to sign out and sign in with his passkey, open AI-PAM management and
confirm the new “Passkey verified” message. Then create clearly labelled,
short-lived synthetic Red/Yellow requests for his approve/deny checks and a
fixture-only management action. Use a new broker fixture with no Unix account,
credential or execution adapter. Retire it and disable its service afterward;
preserve audit history. No such fixture has been created yet. Do not substitute
fabricated claims for signed-session acceptance or claim M1 graduation.

## Deployment evidence — 2026-09-27

Installed a coordinated release on LXC104 and one provider-specific mapping on
LXC106. The release manifest is [retained here](M1-stage2-repair-manifest.json).
Archive SHA-256: `d4c527a7082df061b34efd43155293afdb6bb6dbb9f1d2e7c9be8004f37a77af`.
The deployed Aster candidate preserved two existing live AI-PAM retrieval boosts;
only the management assurance message changed in that file. Broker core and
transport hashes stayed unchanged. No existing grants or production requests
were modified. Both owner allowlists derive from the existing verified lab owner.

Authentik mapping: `Aster Companion verified WebAuthn v1`, UUID
`740d36ad-72cd-4a3b-ad3d-1fb91d72bf74`, fixed activation epoch `1790543081`.
Expression SHA-256:
`843035b7321bf48ad4e0c0430e808d8264d7302cf315f1503af42537ed31bced`.
The four previous mappings and dedicated passkey flow remain unchanged. Build
the exact expression with `build_companion_passkey_mapping.py --policy-epoch
1790543081`. Only fresh sessions after activation can receive the dedicated ACR;
refresh never advances original authentication time. The `/session` bridge route
returns only authorized/passkey/fresh booleans from the verified JWT.

Validation: 14 pure evidence tests, installed Authentik evaluator positive and
14 negative mutations, 11 bridge tests and 164 gateway tests pass. Ten strict
approval-daemon tests against copies of the live core/transport pass. Installed
services are active; Aster health passes; unauthenticated inbox, session and
management routes return 401. Readiness verifies matching process configuration
and socket existence; missing configuration and stopped-service failure paths
were tested. This is not yet proof of a fresh human signed-token workflow.

Protected LXC104 checkpoint:
`/var/lib/homelab-broker/rollback/approval-full-repair-20260927` (prior source,
configuration, metadata, online broker DB backup and verified restored copy).
Protected LXC106 checkpoint: `/root/aster-passkey-repair-20260927` (custom-format
Authentik dump and verification metadata). The full dump restored into an isolated
temporary database; source/restored user counts matched, and the test database
was removed. No recovery material or credentials were exported to Git.

On LXC104 the staged release remains under
`/root/aster-full-repair-release-20260927`. On recovery, stop approval mutations,
inspect checkpoint metadata, and restore source/configuration as a coordinated
set if necessary. Do not overwrite current broker state with the old DB. On
LXC106 detach only the new mapping from provider26 if assurance is suspect;
retain the original four mappings. Privileged actions must remain denied until
the coordinated configuration and signed-session gate pass again.

## Integration and remaining work

- Doctor: repository and pinned Mac toolkit include approval readiness; the
  live check passes. Toolkit rollback copy is
  `~/Library/Application Support/AsterLab/rollback-doctor-20260927T204514Z/doctor-before-approval-readiness.sh`.
  Existing scheduled/worker checks inherit this check; no duplicate schedule.
- Backup/security: protected checkpoints and isolated restores above; new owner
  environment is root-owned mode0600. Existing SSH recovery remains independent.
- Authentication/AI administration: exact owner at both approval entrypoints;
  signed session-specific ACR with unchanged 120-second fresh-action gate.
  No production target credential, broker capability or agent grant added.
- NetBox, DNS, certificates, firewall, Homepage and diagrams: no topology,
  address, service endpoint or physical change; no updates applicable.
- Operational reference: incident runbook and canonical programme link this
  evidence. Human wiki/Aster mirror contain no new target or capability to
  advertise; publish accepted workflow guidance only after human acceptance.
- Implementation, monitoring and evidence are locally committed. No push or
  drift-baseline acceptance; Forgejo synchronization is pending separate push
  authorization. Final human acceptance must be recorded at close-out.

## Source evidence

Installed `/authentik/stages/authenticator_validate/stage.py` appends the actual
successfully validated device object to `auth_method_args.mfa_devices`;
`events.utils.model_to_dict` records server-owned app/model identity. Login signal
binds that evidence to the session's login event. `get_login_event(token.session)`
retrieves the correct grant session. OAuth2 `IDToken.new` and `UserInfoView.get_claims`
pass the grant token into the mapping; refresh copies the original grant
`auth_time` and session. Read-only projection of recent real owner login events
shows `auth_mfa`, typed WebAuthn devices and the dedicated Companion executor path.
No token, session key, authenticator identifier or raw event was exported.

Official reference: [property mapping expressions](https://docs.goauthentik.io/add-secure-apps/providers/property-mappings/expression)
and [OAuth2 provider](https://docs.goauthentik.io/add-secure-apps/providers/oauth2).
Installed source, not generic documentation, determines the claim semantics here.
