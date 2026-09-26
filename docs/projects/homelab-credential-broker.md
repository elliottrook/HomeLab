# Project: AI Privileged Access Management (AI-PAM) and Credential Broker

> Status: active — Stream A; M0–M6 complete
>
> Owner: Jason
>
> Proposed: 2026-09-21
>
> Started: 2026-09-21
>
> Completed: —
>
> Stream: **A (Autonomous)** — Jason explicitly authorized Stream A on
> 2026-09-21 for the scope, exclusions, risk assessment, gates and
> no-secret-in-context rule recorded here. Non-waivable stops and the repository
> requirement for immediate confirmation before each remote push still apply.

## Purpose and desired outcome

Create a central, vendor-neutral privileged-access layer for AI-assisted HomeLab administration so Jason can start work from the Mac, continue steering it from an iPhone, and authorize narrowly scoped administrative access without copying passwords, API tokens or private keys into AI conversations.

ChatGPT/Aster, Claude Code, local Aster/Hermes and future AI clients will authenticate to one broker. The broker exposes capabilities rather than raw secrets, obtains credentials from OpenBao, and uses Authentik plus passkey/WebAuthn for human approval of sensitive actions.

The user-visible result is:

1. an AI can discover only the capabilities it is allowed to request;
2. low-risk read-only work can be pre-authorized where appropriate;
3. privileged changes create a clear approval request;
4. Jason can approve or deny from an iPhone with a passkey;
5. approval is bound to the exact agent, service, capability, resource and TTL;
6. the AI normally receives the result of an operation, not the credential;
7. any AI can be suspended or replaced without rotating unrelated service credentials;
8. active leases/sessions can be revoked centrally; and
9. every new HomeLab service must explicitly define its AI-administration posture before graduation.

This project supersedes the narrower 2026-09-15 SSH-only credential-broker proposal at this same path. The useful privilege-separation idea is retained, but the design expands to OpenBao secret custody, Authentik approval, a capability/MCP gateway, a management GUI, replaceable agent identities and service-wide onboarding rules.

## Current state and evidence

- Authentik is already an established HomeLab identity/authorization service and passkey/WebAuthn operation is proven through the normal HTTPS path.
- Aster is deliberately bounded: it has no arbitrary shell, arbitrary filesystem path, generic credential retrieval or unrestricted network-target tool.
- Existing Aster integrations already use sanitized readers and separately governed action paths.
- Forgejo remains the primary Git repository authority; GitHub is the synchronized off-site protection remote.
- NetBox remains authoritative for adopted device/IP/VLAN/service inventory facts.
- There is no central AI credential/capability control plane today.
- The previous credential-broker draft was SSH-only, deferred Authentik, used file-backed keys and had no management GUI or replaceable-AI lifecycle.
- M0 live discovery confirms Proxmox 9.2.10, Authentik 2026.8.0 in
  unprivileged LXC 106, Forgejo 15.0.7 in unprivileged LXC 108, and no existing
  OpenBao guest/service. Forgejo 15 supports repository-specific scoped tokens
  but not the Forgejo-16 Authorized Integration path.
- Proxmox has ample pilot capacity. The OpenBao placement was revised on
  2026-09-24 from VMID 116 to VMID 117 because the intervening Aster Speech
  project legitimately assigned 116. `192.168.50.24/24` was unassigned in
  NetBox and did not answer the live probe. LXC 117 is now deployed and NetBox
  records VM/interface/IP IDs 18/18/32 for `192.168.50.24/24`.
- The maintained Forgejo MCP is pinned for future evaluation at immutable tag
  `v3.2.0` (annotated tag object
  `931a525dc25dfef430c4bbee51728ad3795f7491`, peeled source commit
  `e30bb7e2e45c0e447506b5df1fe83ebce4b43944`). Its default catalogue
  includes mutation tools and has no documented runtime tool allowlist, so it
  must remain behind the broker's independent deny-by-default adapter.

## Scope and exclusions

### In scope

- Deploy **OpenBao** as the central machine-secret custody, policy and lease/revocation engine unless M0 discovers a material blocker.
- Deploy a separate **AI Access Broker** exposing a versioned internal API and MCP-compatible tool surface.
- Integrate the broker with **Authentik OIDC** and passkey-protected human approval.
- Build a private **AI-PAM Management GUI**.
- Give each AI client a distinct broker identity such as `agent-chatgpt`, `agent-claude`, `agent-aster` or `agent-hermes`.
- Give each target service a separate least-privilege AI identity where supported, such as `ai-proxmox`, `ai-opnsense`, `ai-truenas`, `ai-forgejo` and `ai-homeassistant`.
- Prefer broker/proxy execution so the AI never sees the credential.
- Support dynamic or temporary credentials where the target supports them.
- Permit wrapped static-secret delivery only as a documented exception.
- Create Green/Yellow/Red/Black capability classes.
- Create mandatory probationary onboarding and decommissioning for new AI clients.
- Add an AI Integration Gate to the HomeLab Project Creation Standard.
- Integrate backup, restore, monitoring, HomeLab Doctor, audit and emergency revocation.
- Add a supported Forgejo MCP path so AI clients can work with the authoritative Forgejo repository without sharing human Git credentials.

### Explicit exclusions

- No AI receives OpenBao root/recovery material.
- No AI receives Authentik recovery credentials or passkey private material.
- No universal HomeLab superuser credential is created.
- No requirement that every service expose a raw API key. “AI key” is operator shorthand; the real requirement is a documented AI service identity/capability path.
- No public OpenBao administration surface.
- No automatic promotion from probation.
- No destructive capability merely because the broker can technically invoke it.
- Core HomeLab operation must remain independent of AI-PAM.
- Existing human administrator credentials remain available as break-glass access during the pilot.

## Authority model

| Fact / control | Authority |
|---|---|
| Device/IP/VLAN/service inventory | NetBox where adopted |
| AI-PAM design and policy intent | HomeLab Git/Forgejo |
| AI client identities and capability roles | AI Access Broker |
| Human identity, passkeys and OIDC authentication | Authentik |
| Secret values, dynamic-secret configuration and leases | OpenBao |
| Target-service permissions | Target service native RBAC/API |
| Approval/audit history | Broker audit log correlated to Authentik identity |
| Aster/Hermes memory | Derived/non-authoritative only |

Git records metadata and procedures, never secret values.

## Architecture and data flows

```text
                         JASON
                    iPhone / Mac
                         |
                  Passkey / WebAuthn
                         |
                         v
                    +----------+
                    | Authentik|
                    +----+-----+
                         |
                         v
+-------------+     +----+-----------------------+
| ChatGPT     |---->|                            |
+-------------+     |                            |
                    |       AI ACCESS BROKER     |----> Proxmox
+-------------+     |       + MCP gateway        |----> OPNsense
| Claude Code |---->|       + policy engine      |----> TrueNAS
+-------------+     |       + approvals          |----> Forgejo
                    |       + audit service      |----> Home Assistant
+-------------+     |       + management API     |
| Aster/Hermes|---->|                            |
+-------------+     +-------------+--------------+
                                  |
                                  v
                             +----+-----+
                             | OpenBao  |
                             +----------+
```

The broker and OpenBao remain outside the AI-agent trust boundary.

### Execution modes

**Mode 1 — broker/proxy execution (default).** The AI calls a named capability such as `proxmox.vm.status`; the broker authenticates to the service and returns sanitized output. The credential never reaches the AI.

**Mode 2 — dynamic/temporary credential.** Where the target supports short-lived credentials, issue a scoped credential with a TTL and revocable lease.

**Mode 3 — wrapped static credential (exception).** Only when a client itself must present a static token. A broker TTL must never be represented as target-side revocation if the third-party service continues accepting the underlying token. The integration must proxy instead or include target credential rotation/revocation.

### M0 implementation findings

- Use a dedicated unprivileged OpenBao LXC with integrated Raft. For the
  single-node pilot, use Shamir human unseal rather than introducing an
  unowned external KMS/HSM lifecycle dependency. Initialization/recovery output
  must be encrypted directly to Jason-controlled PGP recipients and must never
  enter the AI session, Git or ordinary logs.
- During M1 recovery testing, bind OpenBao to TLS loopback only. Do not create
  DNS or firewall rules until the synthetic snapshot/restore and human-unseal
  gates pass. The exact non-secret candidate is recorded in
  `ops/credential-broker/openbao-pilot-manifest.yaml`.
- The maintained Forgejo MCP's credential-free OAuth resource-server mode
  requires Forgejo 16+ and a public HTTPS issuer. It is therefore unavailable
  on Forgejo 15.0.7 and conflicts with this project's no-public-OpenBao/control
  surface boundary. Phase 1 must use a repository-specific, minimum-read-scope
  service token held behind the broker, never supplied to the AI client.
- `ops/credential-broker/mcp_policy_adapter.py` is the initial synthetic
  enforcement prototype. It filters the MCP catalogue, requires an allowlisted
  repository, rejects credential/environment arguments and sensitive paths,
  and fails closed on secret-shaped or oversized output. It does not yet
  connect to OpenBao or Forgejo.
- The M2 broker is deployed on LXC 104 as a distinct `hlabroker` service
  identity. Its only agent-facing transport is a group-restricted Unix socket;
  Linux peer credentials bind UID `hlabagent` to probationary identity
  `agent-hermes`. M2 remains synthetic-only with no OpenBao connection or
  production credential.

## Risk classes

### Green — pre-authorized low-risk/read-only

Examples: health, metrics, inventory, sanitized logs, non-secret configuration, repository reads and status checks.

### Yellow — explicit mobile approval

Examples: restart a service/guest, modify bounded configuration, push an approved Git change, install/update a package, rotate a non-root service credential.

### Red — fresh high-assurance approval

Examples: firewall/routing changes, authorization-policy changes, destructive operations, backup-retention changes, OpenBao/Authenik administrative changes. Red requests require a fresh passkey assertion and a second explicit target/effect/rollback summary.

### Black — never delegated to AI

OpenBao root/recovery material, Authentik recovery credentials, passkey private keys, full root passwords, storage-encryption recovery keys and backup master-recovery secrets.

## Management GUI

The private management GUI is a required control surface, not an optional dashboard.

### AI Clients

Show identity, vendor/harness, lifecycle state, roles, allowed capabilities, last authentication, active leases and recent request status.

Actions: add, begin probation, promote/demote, suspend, rotate client authentication, revoke sessions/leases, disable and retire.

### Services and credentials

Show metadata only: service, AI service identity, credential type, secret-custody identifier, execution mode, scope, rotation age/due state, revocation method and health. Normal operation must not display secret values.

Actions: onboard service, test identity, rotate credential through a controlled workflow, disable AI access, revoke supported credentials and open the runbook.

### Approvals

Show requester, reason, service/resource, capability, risk class, duration, exact change summary and rollback.

Actions: approve once, approve for allowed TTL, deny, deny-and-suspend and open audit history.

### Emergency controls

Provide per-agent disable/revoke controls and a prominent **REVOKE ALL AI ACCESS** control. The global control must stop new broker issuance, revoke broker sessions, revoke revocable OpenBao leases, trigger supported target revocations, and leave human break-glass administration intact.

## Probationary onboarding and replaceable AI clients

Every new AI begins in **Probation**. No identity can be created directly as Operator or Orchestrator.

```text
Registered -> Probation -> Observer -> Operator -> Specialist / Orchestrator
                  |            |
                  +-------> Suspended / Retired
```

Probation may use selected health checks, sanitized inventory/logs, documentation lookup and capability discovery. It may not retrieve raw secrets, run arbitrary shell/network calls, make configuration changes, restart services, administer accounts, change network policy or rotate credentials.

Promotion requires recorded tests for identity attribution, denied-action handling, prompt-injection attempts, malformed arguments, scope expansion, expired approvals, live revocation and absence of secret material in AI-visible output.

Replacing one AI means registering the replacement in Probation, validating its workload, assigning only required roles, promoting explicitly, disabling the old identity, revoking its sessions/leases and proving the old identity is denied. Target-service credentials need not be rotated merely because the AI changes unless the old AI was allowed to see that credential directly.

## Forgejo MCP integration

### Goal

Give ChatGPT/Aster, Claude Code and local Aster/Hermes a common, revocable path to the authoritative Forgejo repository without sharing Jason's personal Git credentials or making GitHub the routine write authority.

### Phase 1 — repository-scoped Forgejo service identity

Use the maintained **Forgejo MCP Server** as the protocol adapter.

Deploy it in a dedicated unprivileged Proxmox guest/container or alongside the broker only if isolation remains equivalent. Run streamable HTTP for remote-capable clients and keep operator-token fallback disabled.

Create a dedicated Forgejo AI identity/token restricted to the HomeLab repository when the deployed Forgejo version supports repository-specific tokens. Store that token only in OpenBao. The AI client authenticates to the AI Access Broker; the broker supplies or proxies the narrow Forgejo credential.

Expose explicit capabilities such as:

- `forgejo.repo.read`
- `forgejo.file.read`
- `forgejo.history.read`
- `forgejo.commit.create`
- `forgejo.push.request`
- `forgejo.issue.create`
- `forgejo.pr.create`

Do **not** expose generic Forgejo token retrieval.

Repository reads are candidates for Green. Repository writes/pushes are Yellow initially and require the normal action-specific mobile approval.

The desired normal flow is:

```text
AI edits project
   -> creates local/candidate change
   -> requests forgejo.push
   -> AI-PAM creates approval
   -> Jason approves on iPhone with passkey
   -> broker/MCP performs the Forgejo write
   -> broker verifies Forgejo ref
   -> broker verifies GitHub mirror reached the same commit
```

### Phase 2 — Forgejo 16 Authorized Integrations / secret-less path

If the deployed Forgejo is version 16 or newer and the implementation tests cleanly, prefer the Forgejo MCP resource-server mode using Authentik-issued OIDC/JWT identity plus a Forgejo Authorized Integration.

In that model:

- the client does not carry a Forgejo PAT;
- the MCP endpoint validates the Authentik/OIDC access token;
- the MCP server signs a short-lived caller JWT;
- Forgejo validates that identity through the configured Authorized Integration; and
- no standing Forgejo token must be distributed to the AI client.

This is the preferred end state because it removes static Forgejo tokens from the normal path and aligns Forgejo access with AI-PAM's identity/lease/approval model.

### ChatGPT connectivity constraint

The Forgejo MCP service must be designed as a standards-compliant remote MCP endpoint rather than assuming direct LAN access from every AI. Claude Code and local AI can use LAN/stdio/HTTP paths as supported; ChatGPT access is enabled only through the MCP/plugin capability actually supported by the active ChatGPT account/environment. The broker remains the stable interface so an AI can be added, removed or replaced without redesigning Forgejo.

### Forgejo-specific revocation

The management GUI must support:

- disable one AI's Forgejo capabilities;
- revoke active Forgejo-related broker sessions/leases;
- disable/rotate the Phase-1 repository token;
- disable the Phase-2 Authorized Integration;
- emergency-disable all AI-originating Forgejo writes while retaining human Forgejo administration.

## Pre-start risk assessment

| Risk | Impact | Control |
|---|---|---|
| Broker compromise becomes privileged pivot | Critical | separate guest, deny-by-default capability API, narrow broker identity, no root secret, segmentation, audit, kill switch |
| OpenBao compromise exposes stored static secrets | Critical | restricted surface, protected storage/backups, minimal admins, recovery-key separation |
| Prompt injection requests dangerous capability | High | explicit capabilities, no generic secret/shell tool, risk classes, approval binding |
| Approval fatigue | High | concise action-specific prompts, short TTLs, no approval spam |
| Static target token outlives broker lease | High | proxy by default or rotate/revoke target credential |
| New AI inherits excessive privileges | High | mandatory Probation and explicit promotion |
| MCP endpoint becomes generic Forgejo admin path | High | repo-scoped identity, capability allowlist, no operator-token fallback, network restriction |
| Broker/Authentik/OpenBao outage blocks AI work | Medium | fail closed; human direct administration remains independent |

Initial implementation is **Stream A** under Jason's 2026-09-21 authorization,
but the credential trust boundary retains the project-specific and repository
non-waivable stops. Stream A does not authorize secret material in model
context, public exposure, a failed recovery gate or unbounded capabilities.

Stop immediately if a secret reaches model-visible output or Git, a denied capability succeeds, an approval can be replayed against a different payload/resource, revocation fails, or human break-glass access is lost.

## Persistence plan

Persist non-secret agent/service registries, roles, approval records, audit metadata, schema/version and project milestone state. Never persist secret values, passkey private material or reusable approval bearer tokens in Git/project logs.

On resume: re-read the project standard and this project, inspect Git/live health, verify the last evidence gate, ensure no stale lease remains, then continue from the recorded safe action.

## Milestones

### M0 — discovery, version lock and threat model

- [x] Confirm deployed Forgejo version and native token/Authorized Integration capabilities.
- [x] Confirm Authentik OIDC/passkey flow suitable for broker approval.
- [x] Confirm Proxmox placement/IP/VLAN capacity.
- [x] Evaluate current OpenBao release/deployment requirements.
- [x] Verify the maintained Forgejo MCP release and pin an immutable version
  for later isolated testing: `v3.2.0`, annotated tag object `931a525d`,
  peeled source commit `e30bb7e2`.
- [x] Select first Green and Yellow production-shaped integrations: bounded
  Forgejo repository reads (Green) and broker-performed approved safe-branch
  push (Yellow, not enabled during the read-only pilot).
- [x] Produce final data-flow/threat-model diagram.

**Gate passed 2026-09-21:** discovery used only read-only system/repository
queries. No production credential, identity, ingress, authorization or service
was created or changed. The 10-test synthetic MCP policy prototype also passes
locally; it contains no live client or credential.

### M1 — OpenBao foundation

- [x] Record exact non-secret candidate deployment/backup/abort/rollback
  manifest and validate its YAML structure.
- [x] Deploy dedicated OpenBao guest.
- [x] Establish human-only recovery ownership.
- [x] Configure minimal broker identity.
- [x] Configure protected backup and isolated restore.
- [x] Prove broker identity cannot perform root/admin operations.

**Gate passed 2026-09-24:** OpenBao 2.6.3 runs in dedicated unprivileged LXC
117 with Raft, TLS loopback-only, UI disabled and effective
`MemorySwapMax=0`. Human-held 2-of-3 PGP recovery passed initial, restart and
isolated-restore unseal tests. Audit and a synthetic secret round trip passed;
the `hlabroker` AppRole could read only the synthetic path and received HTTP
403 for administrative policy enumeration. The test token and initial root
token were revoked. The authenticated snapshot is off-guest, and disposable
restore LXC 118 was destroyed after validation.

### M2 — Broker, policy and audit

- [x] Deploy separate AI Access Broker.
- [x] Implement agent/service registries.
- [x] Implement explicit capabilities and risk classes.
- [x] Implement request IDs, payload binding, TTL and revocation.
- [x] Implement metadata-only audit.
- [x] Implement global emergency disable.

**Gate passed 2026-09-24:** the synthetic-only broker runs as `hlabroker` on
LXC 104 with `AF_UNIX` as its only permitted address family. Kernel peer
credentials bind `hlabagent` to `agent-hermes`, which starts in Probation and
discovers only the explicitly probation-safe Green health capability. All 23
tests pass. Live tests proved one-time payload-bound execution, probationary
Yellow/Black denial, global disable/re-enable, zero open requests and an audit
schema containing metadata/hashes but no payload column. No OpenBao or target
credential was created.

### M3 — Authentik mobile approval

- [x] Reuse the dedicated passkey-only Aster Companion application/provider;
  do not create a second identity stack.
- [x] Build and deploy the iPhone-friendly approval flow.
- [x] Require passkey at the defined risk class.
- [x] Test approve, deny, timeout, replay and changed-payload failure.

**Gate passed 2026-09-24:** the approval bridge is deployed on LXC 104. Aster validates
the signed Authentik token and derives a one-way actor identifier plus
`auth_time`; it never accepts those identity values from the browser. A
separate `AF_UNIX` approval service accepts only the kernel UID of `aster`.
Yellow and Red requests remain payload-hash-bound, one-use and TTL-bound; Red
also requires passkey assurance and authentication no more than 120 seconds
old. Companion shows only allowlisted, length-bounded non-secret summaries and
forces fresh OIDC authentication (`max_age=0`) before a Red approval.

The complete deployed-runtime suites pass (30 broker tests and 94 Aster tests).
Live checks proved unauthenticated HTTP rejection, denial of the agent UID at
the approval socket, changed-payload rejection, timeout rejection, a real
fresh-passkey Red approval followed by exact one-time consumption and replay
rejection, and a real human Yellow denial. The broker audit recorded only the
one-way actor identifier and request metadata. Zero requests remain open. No
production target is connected.

### M4 — Management GUI

- [x] AI client lifecycle.
- [x] roles/capabilities.
- [x] service/credential metadata.
- [x] approval inbox/history.
- [x] sessions/leases.
- [x] per-agent/per-service/global revocation.
- [x] audit search.
- [x] responsive iPhone layout.
- [x] secret rendering prohibited and tested.

**Gate passed 2026-09-24:** the synthetic-only management interface is deployed inside
Aster Companion. Read-only views cover lifecycle state, explicit capabilities,
service and non-secret credential metadata, active requests, approval history
and recent audit events. Mutations cover agent state, service access, individual
request revocation and the global kill switch. Every mutation requires a fresh
passkey-backed `auth_time` no older than 120 seconds at the broker boundary;
caller-supplied identity is rejected. Disabling an agent, service or the global
broker revokes matching open requests. History and snapshot tests prove request
payloads are absent. The live candidate passes 36 broker tests and 97 Aster
tests; three hardened services are active, the agent UID remains denied at the
approval socket and stale management authentication is rejected. Jason
accepted the iPhone layout and completed fresh-passkey agent suspend/restore
and global disable/re-enable. Live issuance failed while each control was off.
The service-level control separately denied issuance and restored cleanly.
Final state is global enabled, `agent-hermes` Operator, synthetic service
enabled and zero active requests.

### M5 — Probationary AI lifecycle

- [x] Mandatory Probation default.
- [x] promotion/demotion.
- [x] replacement/retirement workflow.
- [x] prompt-injection/scope-expansion tests.
- [x] live revocation proof.

**Gate passed 2026-09-24:** disposable Unix identity `hlabagent-m5` was bound
to `agent-replacement-m5`, which entered Probation regardless of its four
assigned synthetic capabilities. It discovered only the explicitly
probation-safe Green capability. Yellow, Red, Black, ungranted scope expansion,
malformed payload, arbitrary method and caller-supplied identity attempts were
denied. Prompt-injection-shaped payload text never entered audit output;
changed-payload consumption failed and the exact Green request consumed once.
After Jason's fresh-passkey promotion to Operator, a Yellow request became
pending. Fresh-passkey retirement revoked it and blocked further execution.
A live check then found retired identities could still enumerate their prior
catalogue; discovery was corrected to fail closed and the 36-test broker suite
plus live retired/active regression passed. The disposable Unix user was
removed, the retired audit identity remains, and zero requests are open.

### M6 — Forgejo MCP pilot

- [x] Deploy pinned Forgejo MCP.
- [x] Create repo-scoped Phase-1 AI identity/token if needed.
- [x] Store token only in OpenBao.
- [x] Register bounded Forgejo capabilities.
- [x] Green read-only tests.
- [x] Yellow approved write/push test on a safe branch/test file.
- [x] Verify Forgejo authoritative ref.
- [x] Verify GitHub mirror.
- [x] If Forgejo 16+, test Authorized Integration/resource-server mode and decide
  whether to retire the PAT path. **Not applicable on deployed Forgejo 15.0.7;**
  retain the restricted Phase-1 path until a separately reviewed upgrade.

**Gate passed 2026-09-25:** a distinct non-admin Forgejo service identity and
OpenBao AppRole expose only the `forgejo.write.safe-branch` Yellow capability.
The gateway permits only `create_file` in `jason/homelab`, from `main` to a new
`ai-pam/` branch, under `ai-pam-pilot/`, with bounded non-secret content and a
fixed commit-message prefix. Direct-main writes, other paths and destructive
tools were denied before forwarding. Jason approved the exact disposable
request in Aster; the broker consumed it once and created commit `2deacea` on
`ai-pam/m6-yellow-20260925` while `main` remained `35175c8`. Forgejo and GitHub
showed the same commit. Jason then separately authorized rollback: the branch
was removed from Forgejo and, after the mirror failed to prune it, removed
directly from GitHub as explicit mirror recovery. Both remotes retained the
unchanged `main` ref. No credential appeared in request, audit or Git output.

### M7 — additional production integrations

For each target service create least-privilege `ai-*` identity where supported, prefer broker proxy mode, implement revoke/rotate, test allowed and denied actions, and verify no credential appears in AI context/logs.

- [x] Doctor Green latest-result path: deployed; historic/new-result reads,
  wrong-peer denial, target-side revocation and restoration passed.
- [x] Doctor Yellow one-run path: deployed; two independently approved runs,
  one-use/idempotency, broker-side revocation and zero-job denial passed.

The first candidate reuses the existing Lab Operations worker without exposing
its bearer credential or any backup target. See
[M7 Doctor candidate](credential-broker-m7-doctor-candidate.md).

### M8 — charter/service-onboarding integration

- [x] Adopt AI Integration Gate in `docs/Project-Creation-Standard.md`.
- [x] Update service onboarding docs.
- [x] Add AI-PAM service-registry template.
- [ ] Update architecture/runbooks/NetBox/Homepage as authoritative.
- [ ] Add Doctor/drift checks.
- [ ] Bring the native macOS Aster Companion app to functional parity with
  the web AI-PAM surface. It must provide the approval inbox with approve/deny
  and fresh-passkey reauthentication; agent, service, capability, active
  request/session, history and audit views; agent/service/request lifecycle
  controls; and the global emergency revoke/restore control. Keep all existing
  broker-side freshness, payload-binding, identity and no-secret-rendering
  enforcement unchanged.
- [ ] Add native Swift coverage for AI-PAM response decoding, secret-free
  rendering, approval and management actions, reauthentication, denial/error
  states and emergency controls. Complete a real-Mac acceptance pass against
  the deployed broker, including an approved request, a denial, one lifecycle
  change and global disable/re-enable.

Native candidate status: the Mac source now implements the full approval and
management surface through the existing OIDC API, including `max_age=0` fresh
passkey continuation for Red and every management action. Typed models omit
credential values/raw payloads and Swift tests cover response shapes, action
encoding and fresh-auth URL construction. Source compiles with 23/23 tests;
bundle replacement and the real-Mac acceptance matrix remain gated.

The signed 0.2.0 (build 2) candidate was installed on the Mac after verifying
release binary SHA-256 `0336a91007be7f19663aa6ea88937e4211dd3c743be6fa668bda845bc92d840a`.
The preceding 0.1.0 bundle is retained intact at
`/Applications/AsterCompanion.pre-ai-pam-20260925.app` with its original binary
SHA-256 `2bdb6e7a5022efef3661c2aed1b98f75d9adfd7ebc41b1641141b7dc675a203c`.
The Mac locked before UI/passkey acceptance, so neither native-parity checkbox
is complete yet.

Initial visual acceptance found the AI-PAM button could fall beyond the visible
right edge at the operator's narrower window width. The button was moved beside
the Aster title, 23/23 tests passed again, and the signed bundle was replaced
without removing the 0.1.0 rollback copy. Approval acceptance remains pending.

Native approval and denial then passed, but the first management acceptance
correctly failed closed with HTTP 409: Authentik had immediately reused its
browser session and the new token retained stale `auth_time`. Version 0.2.1
(build 3) isolates every fresh privileged web-authentication session while
retaining the shared browser session for ordinary sign-in. This forces the
intended passkey ceremony before the action is submitted.
The regression test brings the native suite to 24/24 passing, and the signed
0.2.1 bundle builds successfully. The replacement candidate was installed with
release binary SHA-256
`d91cb232299c645f06c7d477f0a7f77ddd7c552bfb9fc35876ba5f2d5315351b`;
the separate 0.1.0 rollback bundle remains untouched.

### M9 — graduation

- [ ] global kill-switch test;
- [ ] per-agent/per-service revoke tests;
- [ ] Authentik/OpenBao/broker outage tests;
- [ ] reboot/restart tests;
- [ ] backup + isolated restore;
- [ ] two independent normal workflow passes;
- [ ] web and native macOS AI-PAM feature-parity acceptance;
- [ ] no temporary access remains;
- [ ] normal HomeLab administration still works with AI-PAM unavailable.

## Validation and evaluation

Test normal function, least privilege, malformed arguments, target/path injection, prompt-injection secret requests, approval replay, changed payload after approval, expired sessions, compromised-agent revocation and dependency outages. Safe failure is always closed without damaging human administration.

## Observability and maintenance

HomeLab Doctor should check broker/OpenBao/Authenik dependency health, sealed/unavailable state where safely observable, stale leases, overdue rotations, audit freshness, backup age, restore-test marker, global-disable state and service-integration drift.

Monitoring should track request counts/outcomes, approval latency, denied requests, failed authentication, active leases and service proxy errors without logging secret-bearing payloads.

## Backup, restore and rollback

Protect OpenBao state/recovery material separately, broker database/config/policies, Authentik integration configuration and source/runbooks in Forgejo.

Restore order: network/DNS -> OpenBao -> broker state/policy -> Authentik integration -> GUI/API -> target-service integrations -> agents.

Rollback must be able to disable broker issuance, revoke leases, disable `ai-*` identities and AI-PAM network paths while preserving human administration.

## Required integration impact checklist

- [ ] HomeLab Doctor
- [ ] Monitoring/alerting
- [x] Backup and isolated restore
- [x] NetBox
- [ ] Human wiki
- [ ] Aster mirror/snapshot (sanitized only)
- [ ] Operational reference/runbooks
- [ ] Repository architecture/portfolio docs
- [ ] Homepage private operator link
- [ ] Authentik/native target authorization
- [ ] DNS/certificates/firewall
- [ ] Automation/schedules
- [ ] Security inventory
- [ ] Forgejo MCP + mirror-verification runbook

## AI Integration Gate / “AI key” standard

Every newly deployed or materially replaced service must have its AI administration posture explicitly defined before graduation.

The shorthand may be “AI key”, but a raw API key is neither required nor preferred. The required deliverable is a documented AI service identity/capability path or an explicit `AI administration: not currently supported` decision with reason.

Where the service supports appropriate APIs/RBAC, create a dedicated `ai-*` identity with the minimum required permissions. Never share the human administrator/root identity.

Credentials belong in the central secrets system and should be reached through the AI Access Broker. Prefer proxy execution; dynamic credentials are second choice; static-secret release is an exception with documented rotation/revocation.

Each integration records service, AI identity, auth type, broker capabilities, risk/approval class, secret-custody identifier (not value), rotation, revocation, human break-glass path and status.

Never weaken a service merely to satisfy this gate.

## Graduation criteria

The project graduates only when OpenBao and broker are recoverable; root/recovery material is human-only; no generic arbitrary-shell/network/secret-dump tool exists; mobile passkey approval is proven; GUI lifecycle/revocation works; global kill switch works; probation cannot be bypassed; Forgejo read/write path and mirror verification pass; at least one additional Green and Yellow service path pass twice; backup/restore pass; documentation and monitoring are current; and human administration works with AI-PAM unavailable.

## Evidence log

| Date | Action | Evidence | Residual risk |
|---|---|---|---|
| 2026-09-15 | Initial SSH-only broker proposal | repository history | lacked central secrets, Authentik approval, GUI and AI lifecycle |
| 2026-09-21 | Reframed as AI-PAM | current charter/authorization/architecture reviewed | implementation not started |
| 2026-09-21 | Added replaceable-AI model, mandatory probation, GUI and kill switches | design | requires adversarial testing |
| 2026-09-21 | Added OpenBao + Authentik + broker/MCP architecture | design | exact deployed versions must be verified at M0 |
| 2026-09-21 | Added Forgejo MCP access plan | Forgejo MCP current README; Forgejo v15 repo tokens; Forgejo v16 Authorized Integrations | live compatibility resolved by the later M0 entry below |
| 2026-09-21 | Drafted AI Integration Gate | project design | charter amendment included in this commit |
| 2026-09-21 | Jason authorized the recorded project under Stream A | delegated instruction preserved by this project record | non-waivable stops and immediate per-push confirmation remain |
| 2026-09-21 | Completed live M0 discovery | read-only PVE/LXC/service/NetBox/backup queries: PVE 9.2.10, Authentik 2026.8.0, Forgejo 15.0.7, OpenBao absent, VMID 116 and `192.168.50.24` candidates | candidates are not reserved; no production mutation |
| 2026-09-21 | Pinned maintained Forgejo MCP candidate | upstream tag `v3.2.0`, annotated tag object `931a525dc25dfef430c4bbee51728ad3795f7491`, peeled source commit `e30bb7e2e45c0e447506b5df1fe83ebce4b43944`; upstream tool/auth review | release artifact signature/SBOM still must be verified before execution |
| 2026-09-21 | Added synthetic deny-by-default MCP adapter | `mcp_policy_adapter.py`; 10/10 tests cover catalogue filtering, repo scope, pre-forward write denial, credential/environment arguments, sensitive/traversal paths, secret-shaped/oversized output and non-tool methods | not connected to a live MCP, OpenBao or Forgejo identity |
| 2026-09-21 | Added exact non-secret M1 candidate manifest | `openbao-pilot-manifest.yaml`; YAML validated; loopback-only recovery phase, Raft/Shamir, backup, abort and rollback gates | human PGP recovery recipients are not available on this Mac; initialization must not proceed |
| 2026-09-24 | Jason confirmed all three private recovery-key backups decrypt successfully | human recovery test; public-only A/B/C files revalidated locally | private keys/passphrases remain human-held and were not inspected |
| 2026-09-24 | Revalidated M1 placement after resuming | VMID 116 is now production `aster-speech`; current LXC/VM inventory leaves 117 free; NetBox still has no `192.168.50.24`; address probe received no reply; daily all-guests backup remains enabled | manifest moved to VMID 117 before any mutation; address still must be checked immediately before creation |
| 2026-09-24 | Revalidated the OpenBao release pin before installation | upstream published 2.6.3 with security fixes on 2026-09-23; candidate manifest advanced from 2.6.2 to the maintained 2.6.x patch | artifact signature and checksum still must pass before installation |
| 2026-09-24 | Created the empty M1 guest and installed the verified OpenBao package | unprivileged LXC 117; Debian 13; exact CPU/memory/disk/VLAN/IP; official signing-key fingerprint, detached GPG signature and SHA-256 all passed for OpenBao 2.6.3 | guest required the established Debian 13 `nesting=1` compatibility feature; no initialization or credential material exists |
| 2026-09-24 | Hit the recorded mlock abort gate before first service start | OpenBao 2.6.3 refuses `disable_mlock=false` because mlock support was removed upstream; vendor unit supplies `MemorySwapMax=0`; service stopped, disabled and has no listener | Jason must explicitly accept replacing the obsolete mlock requirement with verified per-service no-swap enforcement before initialization |
| 2026-09-24 | Jason approved the OpenBao 2.6.3 swap-control update | explicit risk decision in the project task; obsolete mlock gate replaced by required and verified systemd `MemorySwapMax=0` | service must still prove its effective cgroup swap limit before initialization |
| 2026-09-24 | Started and initialized the loopback-only OpenBao foundation | effective `MemorySwapMax=0`; only `127.0.0.1:8200` listens; Raft storage; UI disabled; three public recipients and 2-of-3 encrypted initialization; encrypted root token; off-guest bundle in `Documents/OpenBao Recovery` | instance remains sealed pending two human-held private-key operations; no plaintext share/token entered the task or Git |
| 2026-09-24 | Completed human recovery, least-privilege and root-token lifecycle gates | Jason performed 2-of-3 unseal; file audit enabled declaratively; synthetic KV round trip passed; `hlabroker` AppRole read passed and admin policy listing returned HTTP 403; transient test token and initial root token revoked | later broker deployment must mint a fresh one-use SecretID through an approved administrative workflow |
| 2026-09-24 | Completed authenticated snapshot and isolated restore | SHA-256 recorded for off-guest snapshot on `backups`; disposable network-isolated LXC 118 restored the Raft snapshot, accepted the original human shares, and verified synthetic data/audit/policy/AppRole before destruction | recovery remains human-operated by design; encrypted shares must remain on their separate recovery devices |
| 2026-09-24 | Adopted the deployed placement in NetBox and repository references | NetBox VM/interface/IP IDs 18/18/32; `configs/devices.conf`, IP addressing and backup coverage updated | OpenBao remains loopback-only; no DNS, firewall, Authentik or production-secret integration exists yet |
| 2026-09-24 | Completed M2 synthetic broker foundation | `broker_core.py`, Unix-socket service/client/admin, hardened systemd unit, installer and 23 passing tests; live LXC 104 probation, payload-binding, one-time consumption, risk denial and global-disable checks | M3 must supply Authentik/passkey approval; M2 exposes no TCP endpoint and holds no OpenBao or production credential |
| 2026-09-24 | Deployed M3 mobile approval candidate | Existing passkey-only Aster Companion OIDC reused; separate approver-only Unix socket; kernel UID and signed-token identity boundary; sanitized approval inbox; 30 broker and 93 Aster tests; live changed-payload, replay and timeout failures passed | Real iPhone approve/deny gate deferred until Jason can sign in locally; M3 is not complete and no production target is connected |
| 2026-09-24 | Corrected silent approval-inbox behavior | Inbox/list and denial now require a valid signed Companion identity but not a fresh `auth_time`; the broker still fails Red approval closed unless fresh authentication supplies it. Companion now shows an immediate loading/result message and serves the page with `Cache-Control: no-store`; 94 Aster tests pass live | Real-device approve/deny remains pending; Red freshness enforcement is unchanged |
| 2026-09-24 | Corrected Authentik fresh-login compatibility | Real Safari test showed Authentik 2026.8.0 returned `Not Found` from a stale Companion page using `prompt=login&max_age=0`; retained standards-based `max_age=0`, removed the incompatible `prompt` value and disabled Companion HTML caching | Private Safari fetched the corrected page and completed the required fresh passkey; normal Safari no longer needs the stale page |
| 2026-09-24 | Completed M3 human mobile gate | Jason completed a real fresh-passkey Red approval; the exact synthetic request consumed once and replay failed. Jason separately denied a clearly labeled Yellow request; broker read-back shows `consumed` and `denied`, metadata-only actor attribution and zero open requests | M3 remains synthetic-only; M4 lifecycle GUI is next and no production target credential is connected |
| 2026-09-24 | Deployed M4 synthetic management candidate | Companion management view plus approver-only snapshot/history/audit and fresh-passkey lifecycle/revocation actions; 36 broker and 97 Aster tests; live services healthy, zero active requests and stale management auth denied | Human iPhone layout and representative revoke/restore acceptance pending; no production service or credential is connected |
| 2026-09-24 | Completed M4 management GUI | Jason accepted the responsive iPhone view, suspended/restored `agent-hermes` and disabled/re-enabled global AI access through fresh passkeys. Live requests were denied while disabled and succeeded after restoration. Synthetic service disable/restore also denied/re-enabled issuance; final snapshot is globally enabled, agent Operator, service enabled and zero active requests | M4 remains synthetic-only; M5 probation/replacement adversarial lifecycle is next |
| 2026-09-24 | Completed M5 probationary replacement lifecycle | Disposable kernel-bound identity started in Probation; allowed Green and denied Yellow/Red/Black/scope expansion/malformed/arbitrary-method/identity-spoof cases; prompt-shaped text stayed out of audit. Jason promoted then retired it through fresh passkeys; retirement revoked its pending request and execution. A retired-catalogue leak was found, fixed and live-regressed; Unix test account removed, retired record retained, zero requests open | M6 Forgejo MCP remains gated; no production credential or target was introduced |
| 2026-09-24 | Verified the pinned M6 Forgejo MCP release artifacts | Forgejo release API maps `v3.2.0` to source commit `e30bb7e2e45c0e447506b5df1fe83ebce4b43944`; the checksum bundle's P-256 signature verifies with the upstream public key pinned at GitOps commit `cd3715fa8283a2069a2e3e299744a7b55b1b0260`. The Linux amd64 archive SHA-256 is `bf8f744d53dd06c0e7830ee13a0507464b3ab301fcf01de4744db03d770039df`; its CycloneDX 1.7 SBOM SHA-256 is `5ae227404314345c48828b41a96f43f525b0501c0c4c9e5a856852732e8917d0`; both match the signed checksum list | Artifact execution and all Forgejo identity/token creation remain gated; the tag signature itself could not be independently validated because its OpenPGP public key was unavailable locally |
| 2026-09-24 | Began the authorized M6 read-only Forgejo pilot | Installed the checksum-verified `forgejo-mcp` 3.2.0 binary at `/opt/forgejo-mcp/bin/forgejo-mcp` on LXC 104 without starting it. Created restricted, non-admin Forgejo user `ai-pam-mcp` and granted only read collaborator mode on `jason/homelab`; no PAT exists yet | A one-use `jason` bootstrap token granted the collaborator permission but its intentionally narrow scope could not self-revoke through the API (HTTP 403); the exact token row was deleted locally and verified absent. Service-PAT creation is deferred until it can be transferred directly into OpenBao |
| 2026-09-24 | Recovered OpenBao administrative access after discovering the 2.6 authenticated-root-generation change | Proxmox snapshot `ai-pam-pre-m6-root-recovery` plus cold Raft/audit copy `/root/openbao-pre-m6-20260924T224849Z`; restored the authenticated M1 Raft snapshot and Jason supplied two encrypted recovery shares directly, returning the service to unsealed state | OpenBao 2.6 rejected both unauthenticated legacy root-generation calls and the authenticated CLI call without a token. The restored initial root token is temporarily valid again and remains PGP-encrypted under Recovery A; create/test a limited operator recovery path and revoke root before M6 completion |
| 2026-09-24 | Created and validated the Phase-1 Forgejo credential | Restricted non-admin `ai-pam-mcp`; sole collaboration `jason/homelab` in read mode; PAT `ai-pam-m6-read` has exactly `read:repository`; stored and round-trip verified only at OpenBao `secret/ai-pam/forgejo-mcp-read`. Live API validation returned pull=true, push=false, admin=false; `/api/v1/user` returned HTTP 403 because `read:user` was deliberately omitted | One-shot bootstrap helper removed after success. Broker/OpenBao private listener and MCP policy adapter are not connected yet; no Yellow write credential exists |
| 2026-09-24 | Opened the broker-only OpenBao service path | Added TLS listener `192.168.50.24:8200` while preserving loopback recovery; replacement certificate has SANs only for `127.0.0.1` and `192.168.50.24`. LXC 117 nftables and logged OPNsense rule `7d50a11f-0fe6-4546-bff6-572f14b6541b` permit only `192.168.70.10` TCP 8200; OPNsense checkpoint `/conf/backup/config-ai-pam-openbao-before-20260924.xml`; repository configs `openbao-m6-listener.hcl` and `openbao-m6-nftables.conf` | After human 2-of-3 unseal, broker path returns HTTP 200 with certificate validation; Forgejo LXC 108 times out. Existing loopback recovery remains healthy |
| 2026-09-24 | Connected the M6 Green Forgejo MCP path | CIDR-bound AppRole `hlabroker-forgejo-m6` can read only `secret/data/ai-pam/forgejo-mcp-read`; five-minute tokens, 30-minute maximum, no default policy. Broker-private gateway socket is mode 0600 and starts checksum-pinned MCP 3.2.0 per call, filtering its catalogue and requests through the independent allowlist. Registered Green `forgejo.read.repository` for `agent-hermes` | Real agent → broker → OpenBao → MCP → Forgejo `jason/homelab` read passed and consumed once. Another repo and `delete_repo` were denied before forwarding; policy administration and another secret path returned 403; all observed test tokens were revoked. The restored root token remains temporarily valid and encrypted pending a separately approved human-only operator recovery path |
| 2026-09-25 | Closed the temporary OpenBao root-recovery window | Created loopback/CIDR-bound `human-root-ceremony` AppRole with only authenticated root-ceremony start/status/cancel/update and self-revoke rights; its sole credential is PGP-encrypted to Recovery A in the human recovery bundle. Jason proved login, a zero-share 2-of-3 ceremony start, cancellation and token self-revocation, then revoked the temporarily restored root token. OpenBao remained healthy/unsealed and a fresh agent → broker → AppRole → Forgejo MCP read passed and consumed once after revocation | A future root token still requires this human-held AppRole credential plus two independent recovery shares; the legacy encrypted initial-root-token file is retained only as historical/recovery evidence and its contained token is revoked |
| 2026-09-25 | Made native macOS AI-PAM parity mandatory | M8 now requires the native Aster Companion app to match the web approval inbox, management views, lifecycle actions and emergency controls without weakening broker enforcement; Swift coverage and a real-Mac acceptance matrix are explicit | The web implementation remains the deployed reference until the native work and acceptance pass are complete; M9 cannot graduate without parity |
| 2026-09-25 | Completed the M6 Yellow Forgejo safe-branch pilot | Separate `ai-pam-mcp-write` identity, CIDR-bound AppRole, OpenBao secret path, Unix gateway and policy adapter limit the Yellow capability to one bounded `create_file` operation on a new `ai-pam/` branch under `ai-pam-pilot/`; direct-main, path expansion and destructive tools were denied. Jason approved request `572d03b6-a638-4686-b327-cabf39dfcfe3`; commit `2deacea` appeared identically on Forgejo and GitHub while `main` stayed `35175c8` | Jason separately approved deletion of the disposable branch. Forgejo deletion succeeded; the mirror did not prune, so Jason explicitly approved direct GitHub mirror recovery. The branch is absent from both remotes and `main` is unchanged. Forgejo 16 Authorized Integrations remain not applicable on deployed 15.0.7 |
| 2026-09-25 | Prepared the local-only M7 Doctor candidate | Green latest-result and Yellow one-run capabilities route through a dedicated peer-bound Unix gateway into the existing durable Lab Operations store; backup targets, worker credentials, shell, paths and raw logs remain unavailable. Review found and fixed a potential cross-target housekeeping effect: broker-initiated Doctor now fails closed on stale work rather than reconciling unrelated jobs | Synthetic broker and Aster suites pass; no capability, group, service, job, credential or production file was created. Exact deployment and two real approved passes remain gated |
| 2026-09-25 | Deployed the bounded M7 Doctor gateway | Jason authorized commit `2a81a78`; LXC 104 created a root-only recovery checkpoint, installed the peer-bound service, and registered Green latest-result plus Yellow one-run for `agent-hermes`. Green returned the sanitized historic result; wrong-peer denial passed; a pending Yellow validation created no job and was revoked | Both services are active and the Lab Operations queue has no active/uncertain job. Two human-approved Yellow runs plus revocation validation remain gated; the deployment source gained a bounded socket-readiness loop after observing a harmless startup race |
| 2026-09-25 | Completed both M7 approved Doctor runs | Jason independently approved two payload-bound Yellow requests. Each was consumed once, created one distinct durable Doctor job and completed `succeeded/checks_complete`; first-request replay was denied and Green latest returned the new sanitized record. Each result reported 72 passes, 4 warnings and 1 health failure in 32 bounded checks | Pre-revocation review added a structured timeout/unavailable denial for the private gateway. Deploying that hardening and proving live broker-side/target-side revocation remain before graduation |
| 2026-09-25 | Graduated the first M7 Doctor capability pair | Installed the bounded timeout/unavailable hardening, then proved target-side gateway stop/restart and broker-side service disable/enable. Denials created no Doctor job; Green recovered afterward. Final state: both services active, 9 historic Doctor records, 0 active/uncertain jobs and 0 pending approvals | Recovery checkpoint remains `/var/lib/homelab-broker/m7-doctor-rollback-20260925-191251`; the Doctor result still reports the underlying NetBox redirect failure and aging-backup warnings for operational follow-up, not automatic repair |

## Close-out

Not graduated. M0 through M6 are complete. OpenBao holds separate restricted
Forgejo read and safe-write credentials; the broker-only private listener,
CIDR-bound AppRoles and deny-by-default MCP gateways are live. The temporary
root tokens used during recovery/bootstrap are revoked, while the tested
human-only root-ceremony AppRole still requires two independent recovery
shares.

Next safe action: **M7 additional production integrations.** Select one
reversible Green path and one tightly bounded Yellow path, define target-side
revocation before enabling either, and repeat the allow/deny/no-secret tests.
