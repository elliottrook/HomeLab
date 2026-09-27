# M1 Stage2 — authorized availability and passkey repair

Status: repair complete and accepted September 27. Jason confirmed repeated
iPhone passkey sign-in and all three synthetic approve/deny/management actions.
Broker read-back independently verified the results; test access is disabled.
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
- [x] Jason confirmed the requested repeated iPhone login/management check works.
- [x] Synthetic approval/deny and management-action workflow accepted without
      performing production target actions.
- [x] Monitoring readiness, documentation/evidence and local commit.

Current safe resume: repair acceptance is complete; do not redeploy or reactivate
the fixture. Jason answered “Works” to repeated sign-in/Passkey-verified checks,
then “All three worked” to the synthetic action checklist. Exact evidence:

- RED `089aeae7-6267-46e2-bff0-81382564e690`: approved by the verified owner with
  `passkey` assurance and authentication age within120 seconds at approval.
- YELLOW `37df2816-d3a7-4b6b-aae8-a85db4bdcad0`: denied by the verified owner.
- Agent `repair-test-20260927`: Jason suspended it through management. The broker
  owner-attributed audit and suspended state agree; suspension revoked the
  previously approved RED request. No request was executed against a target.
- Cleanup: fixture agent retired, fixture service disabled, new fixture requests
  denied, zero active fixture requests. No Unix account, credential or execution
  adapter ever existed for UID65027. Retired metadata and audit are retained.
- Final live approval-readiness check passes. The broader Adaptive Computing
  programme and its other gates remain open; this repair does not graduate them.

Historical pending statements below describe intermediate checkpoints and are
superseded by this acceptance record. Remote Git synchronization remains pending
separate authorization; no drift baseline was accepted.

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

### Fresh-login correction after iPhone feedback

**Latest correction, superseding `prompt=login` below:** Jason observed one
passkey prompt followed by silent subsequent sign-ins. Installed Authentik keeps
`SESSION_KEY_LAST_LOGIN_UID` after the first successful reauthentication, so its
prompt handler skips later requests whose login event differs from that marker.
Explicit fresh operations now navigate directly to
`/if/flow/aster-companion-reauthentication/`, with a relative same-origin `next`
URL containing the normal OAuth authorize request and fresh PKCE/state. No
`prompt` or `max_age` workaround is used. The required flow runs before OAuth
authorization; issuer/audience/signature and broker freshness checks remain.
Completed Authentik flows clear their active plan, so the next explicit attempt
plans the required stages again. Existing shared flow/stages remain unchanged.

Current live Aster SHA-256:
`60d67f007f5f21be32fbc77138e04ac866eaf96ea6dd5344b1cf5d9457376e18`.
Recovery source: `aster-before-direct-flow.py` within the LXC104 checkpoint.
JavaScript regression executes two sign-ins and a privileged action, checking
the mandatory flow URL, relative OAuth continuation, PKCE and preserved pending
action. Live health and served no-cache HTML pass. Two real consecutive iPhone
attempts are explicitly pending; do not infer acceptance from the first prompt.

**Current deployed correction:** provider26 now uses dedicated flow
`aster-companion-reauthentication` (`30ccaa43-c15e-4b8d-a30f-f5b4a1819740`). The
original shared flow and every other provider are unchanged. Both anonymous and
authenticated installed FlowPlanner tests produce all three mandatory stages
(identification, required WebAuthn, login). Fresh Companion sign-ins, Red approvals
and management changes now send `prompt=login`, not the ignored `max_age=0`.
The installed authorize-handler test checks initial, repeated-same-event and
new-event behavior without creating sessions or tokens. Live readiness/health and
the served no-cache page pass. Real iPhone acceptance still governs completion.

Current Aster SHA-256:
`dcd2ec2b373602abb13e6ae9c3adc625e79363c41039b1b4747ed4160550aaa4`.
Current mapping expression SHA-256:
`d085bbab7f0c91d21690f54e4969329f4b8bc85bd88174a834fa77b95eca561a`.
The original release manifest above is historical; these two hashes supersede
its Aster/expression entries. Expression source and builder now require the new
exact flow path with the same policy epoch. Protected LXC106 rollback metadata:
`/opt/authentik/data/aster-reauth-checkpoint-20260927.json`; restore its provider
flow and mapping expression together if needed. Prior Aster source is
`aster-before-prompt-login.py` in the LXC104 checkpoint. No shared stage changed,
no session was deleted and no device enrollment changed. The old named blueprint
instances have no embedded contents and their files were absent on the inspected
server; the repository blueprint now records the dedicated flow and reference.

Second feedback (“Same”) exposed two installed-source defects in the proposed
path: Authentik2026.8 evaluates `if self.params.max_age`, so zero skips the age
check, and the old flow rejects already-authenticated users. It is referenced by
31 providers, despite its Companion-specific name. Scope the correction to a new
Companion-only flow admitting both initial and repeat authentication into the
same mandatory stages; switch provider26 alone and bind its claim mapping to
that exact new path. Keep the other30 providers and original flow unchanged.
Change fresh requests to `prompt=login`; no global logout/session deletion.
This is within the authorized full repair, with no passkey requirement removed.
Installed-source tests confirm old/same login events require reauthentication,
a new event advances, and candidate flow entry supports both session states.
Capture prior provider/claim configuration before activation; restore those two
fields together if needed, retaining the original flow and denying privileged
actions on missing assurance. The earlier correction below was insufficient and
must not be considered human acceptance.

Jason reported that sign-out/sign-in reused the Authentik session without a new
passkey challenge. Companion sign-out clears app tokens, not the Authentik SSO
cookie; its explicit sign-in button called `login(false)`. Changed that button
to `login(true)`, which requests `max_age=0` using the existing fresh-approval
path. No sessions or devices were deleted and no other application was signed
out. A JavaScript execution check verified fresh-login parameters, PKCE and no
queued approval action. The exact one-line patch was applied to the current live
source, preserving unrelated live changes, and Aster alone restarted.

Current live Aster SHA-256:
`e208cf3515d01eddfe79befc2393fdf8bf6499808d5bd982d212d84dd2e98912`.
Pre-change source is `aster-before-fresh-login.py` inside the LXC104 checkpoint.
The initial probe incorrectly used loopback while Aster binds its guest IP;
corrected read-only checks on `192.168.70.10:9120` verified health and the served
fresh-login handler with `Cache-Control: no-store`. Service remained active with
zero automatic restarts. Jason must reload the page before using Sign in so
the already-open page does not retain the old handler. Real acceptance remains open.

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
