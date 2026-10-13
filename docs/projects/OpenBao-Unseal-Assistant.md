# OpenBao Unseal Assistant

> **Status:** Deployed V1 — native recovery fixes accepted; full ceremony and integration gates remain open
> **Project owner:** Jason
> **Authorization stream:** Stream M setup and deployment completed; acceptance
>   and graduation remain open
> **Service identity:** `openbao-recovery` (a human-only Companion capability)
> **Current release:** V1 deployed 2026-10-12

## Purpose and desired outcome

Provide a small, passkey-protected recovery panel reachable from Homepage so
Jason can complete the existing human OpenBao unseal ceremony without asking
Codex to format shell commands. OpenBao requires two tokens for this ceremony;
the panel submits them one at a time, shows only sanitized seal progress,
clears the input after each submission, and stops when OpenBao is unsealed.
The same panel also provides an explicitly confirmed **Seal OpenBao** action
for planned maintenance or emergency isolation.

This is an operator convenience layer over the existing human ceremony. It is
not a secret browser, token generator, root console, AI capability or direct
OpenBao UI.

## Security boundary

- The tile deep-links to the authenticated Aster Companion panel; it does not
  expose `192.168.50.24:8200` or create a new OpenBao listener.
- Authentik Companion JWT validation and a separate owner-hash allowlist are
  required. A recent passkey-authenticated session is required by default.
- The backend accepts one token/share per request, sends it directly to
  `/v1/sys/unseal`, never persists or echoes it, and returns only allowlisted
  seal metadata. The UI never combines the two tokens in one request.
- No OpenBao token, KV path, policy, root operation or secret read is exposed.
- Rate limiting serializes submissions and prevents accidental rapid repeats.
- Sealing is a separate authenticated action with a browser confirmation and
  no token input; it intentionally interrupts OpenBao-dependent services until
  the two-token ceremony is completed again.
- Recovery shares remain human-held and outside Git, Aster knowledge, logs and
  the browser's persistent storage.

## Current state and authority

OpenBao LXC 117 remains the credential authority at `192.168.50.24`. Existing
TLS, firewall and human recovery controls remain authoritative. Aster LXC 104
already has the narrow network path used by the broker and will host the
authenticated Companion endpoint. Homepage remains the dashboard authority;
the provisioning script adds only a deep-link to Companion.

## Milestones

### 0. Design and pre-start safety review

- [x] Confirm the existing human unseal ceremony, network path and recovery
  boundary.
- [x] Define the endpoint allowlist, owner allowlist, recent-authentication
  requirement, no-storage rule and sanitized response shape.
- [x] Jason authorised the bounded deployment and subsequently accepted the
  repaired recovery UI; remaining graduation checks are listed below.

### 1. Local implementation and synthetic tests

- [x] Add authenticated status and one-token-at-a-time submission endpoints.
- [x] Add the responsive style-guide panel to Aster Companion.
- [x] Add the native SwiftUI Mac Companion panel and API client methods.
- [x] Add an idempotent Homepage deep-link provisioner.
- [x] Add tests for response sanitization, request strictness and operator auth.
- [x] Add a separately confirmed seal action that returns sanitized status.
- [ ] Run the complete Aster test suite and a mocked OpenBao HTTP test.

### 2. Controlled deployment preparation

- [ ] Capture an LXC 104 checkpoint and record the exact source/configuration
  manifest.
- [x] Configure the OpenBao CA path and dedicated owner-hash allowlist without
  exposing credentials in Git.
- [ ] Validate service startup, direct endpoint denial, TLS verification and
  logs contain no share material.

### 3. Live operator acceptance

- [x] Add the Homepage tile and validate the backup copy/YAML before restart.
- [ ] Test sealed status, first token, incomplete quorum, second token/final
  unseal, already-unsealed state, invalid token, explicit seal confirmation,
  OpenBao outage and expired authentication.
- [ ] Confirm the tile works on LAN and through the existing Tailscale path.

### Deployment evidence — 2026-10-12

- Aster LXC 104 source checkpoint: `/opt/aster-agent/rollback-openbao-20261012.py`.
- Aster environment checkpoint: `/etc/aster/aster.env.rollback-openbao-20261012`.
- Homepage configuration checkpoint:
  `/opt/homepage/config/services.yaml.rollback-openbao-20261012`.
- Native Mac rollback bundle: `/Applications/AsterCompanion.pre-openbao-20261012.app`.
- Aster syntax validation, service restart, health check and unauthenticated
  endpoint denial passed. Homepage loaded the new tile and returned healthy.
- Native Swift build and all 24 existing tests passed; the installed app now
  contains the OpenBao recovery and confirmed seal controls.
- The seal action was not invoked during deployment. Jason must perform the
  authenticated acceptance test deliberately; sealing interrupts dependent
  services until two tokens are supplied again.

### 4. Documentation adequacy reflection — mandatory

- [ ] Re-read the Project Creation Standard, lifecycle standard, architecture,
  network, IP, AI-PAM operational reference, Aster operations, Companion guide,
  backup runbook, Homepage operations and this project.
- [ ] Confirm the documentation distinguishes the safe Companion panel from
  direct OpenBao administration and states exactly where unseal shares may and
  may not exist.
- [ ] Update stale “no OpenBao tile” wording to describe the safe deep-link,
  while retaining the prohibition on direct OpenBao/broker/secret links.
- [ ] Record any remaining recovery or handover gap as follow-up work.

### 5. Graduation

Graduation requires Jason's real acceptance, authenticated failure-closed
behaviour, no secret-bearing logs or browser storage, backup/recovery evidence,
Homepage and operational-reference reconciliation, and an explicit rollback to
the existing Aster Companion behaviour.

## Integration checklist

### Native passkey freshness correction — 2026-10-12

Follow-on live acceptance identified HTTP 500 after successful passkey login.
The traceback showed `PermissionError` reading the public CA under the broker's
restricted directory. Copied only that public CA to `/etc/aster/openbao-ca.crt`
and changed the live recovery default; broker permissions were preserved.
Backup: `/opt/aster-agent/aster_agent.py.before-openbao-ca-20261012`.
After restart, `/health` passed and `_openbao_json` ran as `aster`, returning
initialized/unsealed status with the two-share threshold. Local source also
places CA filesystem checks inside the sanitized error handler; this additional
error-handling change has not yet been deployed.

Both native bundles were subsequently signed with the existing
`Aster Companion Local Signing 2026` certificate; the designated requirement
pins certificate `10b67a3b122fafcdb2bb55124caf327115a4e6fa` rather than a build
hash. The build script now selects this identity for future updates. No signing
private key or Keychain session was transferred. The transition from ad-hoc
signing can require one final user approval per Mac; subsequent same-certificate
builds retain the requirement. Jason confirmed the resulting UI works after
this update; full recovery-ceremony acceptance remains a separate gate.

Jason confirmed MacBook native login succeeded but OpenBao status returned
401 requiring a recent passkey sign-in. Normal OIDC login reused the existing
Authentik session, so its authentication age did not satisfy the recovery gate.
The native client now offers **Verify passkey** and explicitly enters
`/if/flow/aster-companion-reauthentication/`, matching the existing web client,
then resumes the native PKCE authorization and reloads status. Share inputs
are cleared before reauthentication; no share submission is replayed.

All 25 Swift tests passed, including authorization URL/PKCE preservation.
The tested bundle was installed on both mini and MacBook with executable
SHA-256 `8781e1defd4bb953544b93a65cefbf115d20ca41e707dabb34de1750795e3eb4`.
The MacBook's prior bundle remains at
`/Applications/AsterCompanion.before-openbao-passkey-20261012.app`; the mini's
at `/Applications/AsterCompanion.pre-openbao-passkey-20261012.app`.
Live passkey verification and status display were accepted by Jason; human
two-share ceremony acceptance remains pending.
The backend freshness requirement and owner allowlist remain unchanged.

- [ ] HomeLab Doctor: check endpoint/service dependency and sanitized OpenBao
  seal status without reading shares or secrets.
- [ ] Beszel: reconcile LXC 104 coverage; no duplicate monitoring required.
- [ ] Backup/restore: protect Aster source/configuration and preserve existing
  OpenBao recovery material separately.
- [ ] NetBox: no new guest or IP; document only if the capability becomes a
  separately addressable service.
- [ ] Homepage, Aster Companion guide, AI-PAM reference and human wiki.
- [ ] NPM/Auth/Tailscale: retain the existing private Companion route only.

## Close-out

Jason confirmed the repaired native recovery UI works on 2026-10-12 after
passkey reauthentication, CA access repair and stable signing installation on
both Macs. This accepts those fixes. It does not establish that the full
seal/two-share/unseal ceremony, outage cases, Tailscale acceptance or all
integration/graduation gates were exercised; the remaining unchecked gates
above remain open. The mini-to-MacBook SSH key remains enrolled at Jason's
explicit request. No private key or session was copied between machines.

No live deployment, OpenBao configuration change, firewall change, credential
change or remote Git operation is authorised by this document alone.
