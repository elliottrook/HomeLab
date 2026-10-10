# Project proposal: Secure cloud-agent access to private Forgejo

**Status:** Design only; no production changes, credentials, tunnels, runners, gateways, tokens, commits, pushes, or network-policy changes were made.  
**Prepared:** 2026-10-10  
**Source request:** `Brand-Design-Unification-Handoff/codex/TAILSCALE_FORGEJO_SPECIALIST_PROMPT.md`  
**Canonical constraint:** Forgejo remains the source of truth and remains reachable only through the private/Tailscale network. GitHub is a mirror, not a reverse write path.

## 1. Executive decision

Adopt **Option A: a dedicated, Tailscale-joined local execution runner that applies reviewed, immutable change bundles** as the default architecture. It minimizes attack surface because the cloud agent never receives Forgejo or tailnet credentials and no inbound service is exposed. Keep the runner pull-based, isolated, deny-by-default, repository-scoped, and unable to promote without a human approval record.

Use **Option C: gated mirror plus trusted local promotion** only as an interim workflow or disaster-recovery input channel. A trusted local promoter must verify provenance, base commit, signatures/checksums, policy, and tests before creating the Forgejo commit. Never let GitHub mirror changes flow automatically into canonical Forgejo.

Defer **Option B: authenticated broker/tunnel** unless interactive cloud access becomes a proven requirement that A cannot satisfy. A broker substantially expands the remotely reachable attack surface and token-handling burden. If approved later, expose only a narrow change-request API—not Forgejo itself—through an authenticated private path, with mTLS/workload identity, short-lived capability tokens, rate limits, request signing, human gates, and complete audit logs.

## 2. Known facts, assumptions, and discovery gates

Known from the supplied handoff:

- Forgejo is canonical; GitHub mirrors it.
- Forgejo is private behind Tailscale.
- Cloud agents cannot assume tailnet reachability.
- Public Forgejo ingress, credentials in chat, or deployment without authorization are forbidden.

Not available in this workspace and therefore **not assumed**:

- The HomeLab repository, its `AGENTS.md`, project standard, authorization matrix, Forgejo version/configuration, mirror direction/config, tailnet ACL/grants, identity-provider topology, AI-PAM product/API, Authentik flows, secrets manager, runner platform, cloud-agent network/runtime capabilities, or current backup/restore runbooks.

Before implementation, an authorized operator must inventory those items and record versions, owners, data classifications, repository identifiers, protected-branch rules, allowed egress, and retention requirements. This proposal is an actionable plan for a repository-connected agent or operator to reconcile with those policies and commit only after approval.

## 3. Threat model

### Protected assets

- Forgejo repositories, issues, releases, packages, webhooks, users, and administrative settings.
- Tailnet membership, ACL/grants, device keys, OAuth clients, auth keys, node identities, and DNS/service discovery.
- Signing keys, repo-scoped tokens, Authentik/AI-PAM approvals, audit logs, artifact storage, and mirror credentials.
- Confidential source, generated patches, build logs, prompts, test artifacts, and provenance records.

### Trust boundaries

1. Untrusted or partially trusted cloud-agent runtime.
2. Artifact/change-request exchange.
3. Dedicated local runner/worker identity on the tailnet.
4. Forgejo repository and protected-branch boundary.
5. Human approver, Authentik, AI-PAM, and secrets manager.
6. GitHub mirror and any external CI/artifact systems.

### Principal threats and required responses

| Threat | Required control | Failure behavior |
|---|---|---|
| Cloud agent compromise or prompt injection | No tailnet/Forgejo secret in cloud; content treated as untrusted; signed immutable request; sandboxed validation | Reject request; revoke request identity; preserve evidence |
| Malicious patch or dependency change | Path allowlist; diff-size and binary limits; policy tests; isolated build; human review; protected branch | Quarantine, never auto-promote |
| Runner compromise | Single-purpose node/tag; least-privilege service account; read-only base checkout; ephemeral job workspace; no admin token; egress allowlist | Disable node and credentials; rebuild from known image |
| Credential theft/replay | Short-lived, audience/repo/action-scoped credentials; mTLS/workload identity; nonce and expiry; secret manager delivery | Revoke/rotate; replay detection; fail closed |
| Broker abuse/DoS | Narrow schema; body/patch limits; concurrency/rate limits; per-identity quotas; no arbitrary proxying | 429/deny; circuit-breaker; alert |
| Tailnet lateral movement | Tagged non-human device identity; explicit grants only to required Forgejo endpoint/port; no subnet-router wildcard access | Network denial; alert on unexpected destination |
| Forgejo API privilege escalation | Non-admin bot; exact repository permission; protected branches; no token management/org administration/webhooks unless separately approved | API deny; incident review |
| Mirror poisoning or synchronization inversion | Forgejo-only promotion; base SHA and ancestry verification; explicit mirror-lag check; no automated GitHub-to-Forgejo push | Stop promotion and reconcile manually |
| Audit tampering | Append-only/remote log sink; correlated request/job/approval/commit IDs; restricted deletion; clock synchronization | Promotion blocked if audit sink unavailable, except documented break-glass |
| Sensitive data in logs/artifacts | Secret scanning and redaction; minimal logs; retention policy; encrypted storage | Quarantine and incident workflow |
| Approver/session compromise | Authentik MFA; AI-PAM just-in-time approval; separation of duties for high-risk actions; short approval TTL | Expire approval; revoke session; require re-approval |
| Supply-chain compromise | Pinned runner image/toolchain; verified downloads; SBOM where applicable; isolated/no-network tests by default | Block and rebuild |

Remote compromise must never yield a general tailnet foothold, a Forgejo administrative credential, direct protected-branch write, arbitrary network proxy, or automatic public publication.

## 4. Ranked alternatives

### Rank 1 — A. Pull-based Tailscale-joined local runner

**Flow:** Cloud agent produces an immutable change bundle (patch or Git bundle, manifest, base SHA, requested actions, tests, expiry, checksum/signature). A local runner fetches it outbound or receives it through an approved artifact queue, validates it in an ephemeral sandbox, and publishes a preview/result. A human approves promotion through AI-PAM/Authentik. The runner then uses a short-lived repository-scoped identity to create a branch/commit or merge through the approved Forgejo workflow.

**Why first:** No public ingress; no tailnet credentials in cloud; simplest least-privilege story; clear human gate; easiest containment and rollback.

**Runtime feasibility:** Works with any cloud agent able to emit a patch/bundle and manifest to an approved exchange. It does not require the agent to run Tailscale, accept inbound connections, or preserve a stable workload identity. The local runner must support Tailscale and isolated job execution; exact OS/container/VM implementation is a discovery decision.

**Controls:**

- Dedicated non-human tailnet node with a service tag and no reusable human login.
- Tailnet policy permits only the Forgejo host and required port/DNS, plus explicitly approved artifact/audit/identity endpoints. No broad LAN/subnet access.
- Per-repository worker configuration; allowed operations and paths; maximum patch/artifact size; binary and submodule deny rules by default.
- Two identities: a validation identity with read access and a separate JIT promotion identity with minimal write scope.
- Promotion credential minted/released only after an approval whose subject binds request hash, repository, base SHA, branch, action, actor, and expiry.
- Protected branch remains enforced. Prefer pull request/review over direct pushes. Direct protected-branch write requires an explicit separate exception.
- Network disabled for build/test unless a reviewed job profile grants destination-specific egress.
- Runner cannot alter its own image, tailnet policy, AI-PAM policy, or Forgejo permissions.

**Cost/operations:** Low cloud egress (compressed bundle and logs); moderate local compute and patching; moderate initial engineering. Capacity is bounded by the local runner pool and test workload.

### Rank 2 — C. Gated mirror/input repository plus trusted local promotion

**Flow:** Cloud agent writes to a separate, explicitly non-canonical staging repository or uploads a signed bundle. A local promoter fetches outbound, verifies the canonical Forgejo base SHA, rebases/applies in isolation, runs policy/tests, and opens a Forgejo change for review. The existing GitHub mirror must remain one-way from Forgejo; do not repurpose it as canonical input without an approved architecture change.

**Strength:** Fastest interim PoC and compatible with most agent runtimes. Cloud has no tailnet access.

**Risk:** Reviewers may confuse staging with canonical state; history and review metadata can diverge; malicious staging content remains untrusted; bidirectional automation can create loops or overwrite canonical work.

**Correctness controls:** Distinct repository naming/banner; no force-push promotion; exact base SHA; ancestry check; deterministic patch generation; content checksum; compare resulting tree hash; mirror-direction invariant test; promotion receipt maps source artifact to Forgejo commit. On mismatch or canonical advancement, stop and regenerate—never silently merge.

**Cost/operations:** Low-to-moderate egress; lower initial engineering; moderate ongoing reconciliation and user-training burden.

### Rank 3 — B. Narrow authenticated remote broker/private tunnel

**Flow:** A broker accepts a constrained change-request schema and queues local execution. It must not be a TCP proxy, shell gateway, generic Git transport, or Forgejo API passthrough. Prefer an outbound-established/private overlay connection where the cloud runtime supports a stable attested identity. The broker calls the same local validation/promotion engine as A.

**Use only when:** Interactive status/cancellation or latency requirements cannot be met through the queue/artifact model, and the specific cloud runtime can present a stable, verifiable workload identity.

**Identity and access:**

- mTLS for machine authentication with short-lived certificates and audience binding.
- OAuth/OIDC authorization where supported, using Authentik as the policy-facing IdP only after validating exact flows and token claims in the installed versions.
- AI-PAM issues/approves a short-lived capability bound to repository, action, request hash, expiry, and maximum uses; it must not hand a Forgejo token to the cloud agent.
- Broker-to-Forgejo credential remains local, repo-scoped, short-lived where the installed Forgejo/identity stack supports it; otherwise retrieve a tightly scoped token just in time, minimize TTL/exposure, and rotate/revoke through a documented compensating control.
- Deny unknown routes, methods, repositories, branches, content types, oversized payloads, stale requests, replayed nonces, and missing approvals.

**Remote compromise scenario:** Assume the remote caller's identity is stolen. The attacker may submit only bounded requests; cannot choose arbitrary upstream URLs, commands, destinations, or Forgejo API methods; cannot view secrets; cannot bypass approval; and is throttled and revocable. If any of those properties cannot be demonstrated, do not deploy B.

**Cost/operations:** Potential persistent tunnel and logging egress; highest certificate, gateway, patching, monitoring, and incident-response burden.

### Safer supporting alternatives

- **Human-carried signed bundle:** Lowest automation and attack surface; suitable for bootstrap/break-glass and low-frequency changes.
- **Local interactive agent:** Run the agent entirely on a trusted tailnet host under the same runner restrictions. Strong security, but reduced elasticity and potentially different data-governance implications.
- **Read-only cloud mirror plus local write workflow:** Good for analysis, never promotion. Ensure mirror latency and confidentiality are acceptable.

## 5. Reference architecture for the recommended path

1. Cloud agent emits `request.json`, patch/Git bundle, checksums, test intent, tool/version provenance, and expiry. No secrets.
2. Exchange stores the request immutably and returns a request ID. Encryption and retention follow repository classification.
3. Local scheduler pulls the request, verifies checksum/signature/schema/expiry/replay state, and maps the repository through a static allowlist.
4. Validator checks out the exact Forgejo base commit using read-only access into an ephemeral workspace; applies the bundle; scans content; enforces path/size/binary/submodule/LFS policies; tests with network off by default.
5. Results and normalized diff are published with immutable artifact hashes. No promotion happens yet.
6. Human reviews diff/results. Authentik enforces MFA/session policy; AI-PAM records authorization and grants a short-lived, request-bound promotion capability. Exact integration depends on locally installed products and must be discovered.
7. Promoter re-verifies base SHA and all hashes, obtains a local repo-scoped credential, creates a uniquely named branch, and opens the normal Forgejo review. Protected-branch rules remain authoritative.
8. Forgejo commit/PR ID and resulting tree hash are written to the audit receipt. Downstream GitHub mirror status is observed separately; it is not proof of Forgejo promotion.

### Audit record (minimum)

Record request ID, repository, base SHA, source artifact URI and hashes, signer/workload identity, cloud-agent/runtime declaration, validation worker/image digest, policy version, commands/tests and exit states, normalized diff hash, approval identity/method/time/expiry, capability ID, promotion identity, Forgejo branch/PR/commit, resulting tree hash, mirror observation, rejection reason, revocations, and rollback event. Logs must redact secrets and go to a retention-controlled sink the runner cannot erase.

## 6. Phased non-destructive PoC

### Phase 0 — discovery and design approval

Authorized operator:

1. Reads current HomeLab `AGENTS.md`, project standard, auth rules, network policy, Forgejo and mirror docs.
2. Records actual cloud runtimes and whether each supports artifact upload, stable OIDC identity, Tailscale, inbound service, and persistent storage. Do not generalize between hosted Codex, CI runners, and locally hosted agents.
3. Inventories Forgejo version/API token scopes, protected branches, Authentik protocols/claims, AI-PAM approval/JIT interfaces, tailnet grants, secrets manager, audit sink, backups, and restore test.
4. Produces data-flow diagram, repository allowlist, RACI, retention values, SLOs, and cost ceiling.
5. Obtains architecture/security/privacy approval before any account, key, runner, or policy is created.

### Phase 1 — offline validator, no network/write

- Use a synthetic repository and benign/malicious fixture bundles.
- Implement request schema, checksum/signature verification, expiry/nonces, allowlists, limits, secret scan, deterministic apply, network-disabled tests, result receipt, and cleanup.
- Runner has no Tailscale, Forgejo, GitHub, Authentik, or AI-PAM credentials.
- Demonstrate rejection cases and that untrusted content cannot escape the sandbox.

### Phase 2 — tailnet read-only canary

- Create a dedicated canary node identity/tag after approval.
- Grant only canary Forgejo read access and required audit/artifact endpoints.
- Clone a dedicated non-sensitive test repository at an exact SHA; no write token exists.
- Verify network denials, device revocation, node expiry/rebuild, logging, and egress measurements.

### Phase 3 — gated write to a non-production repository

- Integrate Authentik MFA and AI-PAM approval, validated against installed capabilities.
- Release a short-lived, repository/action-scoped promotion credential locally only after approval.
- Open a branch/PR in a disposable repository; no direct default-branch write.
- Exercise expiration, revocation, duplicate/replay, stale-base, approver denial, credential leak simulation, audit outage, and rollback.

### Phase 4 — limited production canary

- Owner selects one low-risk repository and approved paths.
- Require human approval for every promotion; low concurrency and strict rate limit.
- Run for a defined observation window and review incidents, false rejects, latency, costs, and operator burden.
- Expansion to additional repositories/actions is a new recorded approval, not an implicit rollout.

## 7. Acceptance matrix

| Area | Test | Pass criterion |
|---|---|---|
| Isolation | Malicious build attempts filesystem/container escape | No host or sibling access; job terminated and evidence retained |
| Network | Job probes LAN, metadata, internet, and tailnet | All denied except exact profile destinations; denies logged |
| Identity | Missing/invalid/expired/replayed signature or OIDC/mTLS identity | Request rejected before checkout or execution |
| Authorization | Valid identity requests unlisted repo/path/action | Denied with no Forgejo credential minted |
| Approval | Promotion without approval, after TTL, or after diff change | Denied; any content/hash change requires new approval |
| Secrets | Job prints env/config and scans process space | No Forgejo/tailnet/promotion secret accessible; output redacted |
| Forgejo scope | Credential tries admin, other repo, token/webhook management, protected direct push | All denied; intended canary branch/PR only succeeds |
| Tailnet | Runner tries any non-approved host/port | Denied by tailnet and host egress policies |
| Rate limits | Burst, oversized bundle, excessive concurrency | Enforced per identity/repo/global; service remains available |
| Content policy | Binary, symlink escape, submodule, external SVG/script, secret, huge diff | Rejected unless an explicit reviewed profile permits it |
| Base correctness | Canonical branch advances after validation | Promotion halts; revalidation and reapproval required |
| Tree correctness | Apply same approved bundle twice from same base | Identical tree hash; second promotion prevented as replay |
| Mirror direction | GitHub staging/mirror changes independently | No automatic write to Forgejo; discrepancy alerted |
| Audit | Correlate request through commit; audit sink unavailable | Complete immutable receipt; fail closed on sink failure |
| Revocation | Revoke caller, node, capability, and repo credential during job | New actions cease within defined SLO; incomplete job cannot promote |
| Recovery | Disable runner and rebuild from trusted image | Clean rebuild succeeds without persistent job secrets |
| Rollback | Revert canary change through normal Forgejo review | Canonical history preserved; revert SHA and mirror observation recorded |
| Cost | Measure bundle, logs, tunnel/queue, clone/test traffic | Within approved per-job/month ceiling; alert before overrun |
| Operations | Patch, rotate, expire, and restore components | Runbooks exercised by someone other than implementer |

Numeric TTLs, rate limits, retention periods, revocation SLOs, and cost ceilings must be selected during Phase 0 based on actual risk and operations; inventing them here would create false assurance.

## 8. Explicit approvals required

Approval is required before each of the following:

1. Selecting the architecture and processing/data residency for cloud artifacts.
2. Creating a tailnet node, service tag, OAuth client/auth key, or changing ACL/grants/DNS/routes.
3. Creating Forgejo users/tokens/SSH keys/apps, changing repository permissions or protected-branch rules, or configuring webhooks/mirrors.
4. Creating Authentik providers/applications/flows/claims or changing MFA/session policy.
5. Integrating AI-PAM, defining approval roles, or enabling JIT credential release.
6. Deploying a runner, broker, tunnel, queue, artifact store, audit sink, or monitoring integration.
7. Allowing any inbound listener, external endpoint, or new egress destination.
8. Executing untrusted content, even in the offline PoC, on owner-controlled infrastructure.
9. Moving from offline to read-only tailnet, from read-only to write canary, and from canary to production.
10. Issuing a production write credential, promoting any real change, publishing externally, or changing mirror direction.

High-risk exceptions—direct protected-branch writes, administration, new public ingress, generic proxying, reusable credentials, wildcard tailnet access—require a separate security decision and are outside this proposal.

## 9. Rollback and incident response

### Service rollback order

1. Pause request intake and promotion queue; retain evidence.
2. Revoke current promotion capabilities and Forgejo credentials.
3. Disable/revoke runner node identity and broker certificate/client identity if applicable.
4. Revert tailnet grants, host firewall/egress rules, Authentik/AI-PAM application grants, and new endpoints using versioned prior configurations.
5. Rebuild compromised runners from a trusted image; do not reuse persistent workspaces or cached secrets.
6. Review audit correlations, rotate affected credentials, scan affected repositories, and notify owners per incident policy.

### Repository rollback

- Prefer a reviewed revert commit/PR that preserves canonical history.
- Never force-push or rewrite protected history as an automated rollback.
- If the promoted commit contained secrets, revoke/rotate first, then follow the repository's approved history-remediation procedure.
- Verify the Forgejo rollback SHA first; verify the GitHub mirror separately and record lag/discrepancy.

### Fail-closed triggers

Stop promotion on identity/approval/audit unavailability, stale base, hash/signature mismatch, policy version mismatch, unexpected egress, credential issuance failure, mirror-direction ambiguity, runner integrity alert, or incomplete tests. Read-only status may remain available if it cannot reveal sensitive data or weaken containment.

## 10. Deliverables for the authorized repository-connected implementation task

- Reconciled HomeLab-format project record and architecture decision record.
- Current-state inventory with versions and owners; data-flow/threat-model diagram.
- Request/receipt schemas and signed sample bundles.
- Versioned tailnet, host firewall, identity, Forgejo, rate-limit, retention, and approval policies.
- Offline validator fixtures and acceptance-test evidence.
- Canary deployment/runbooks, credential rotation/revocation, backup/restore, rollback, and incident procedures.
- Evidence index: approvals, configuration diffs, image/tool digests, test results, audit samples, cost/egress observations, Forgejo commits, and separately verified mirror status.

## 11. Recommendation checkpoint

Proceed only to **Phase 0 discovery** after owner authorization. The first implementation decision should be whether an approved immutable artifact exchange already exists. If yes, build A directly. If not, bootstrap with a human-carried signed bundle or isolated staging store, then add automation. Do not create a public Forgejo endpoint, install a gateway, join a cloud runtime to the tailnet, or issue credentials merely to accelerate the Brand Design task.
