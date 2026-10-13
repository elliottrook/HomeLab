# Cloud-agent Forgejo document publishing

> Status: Proposed — M0 read-only reconciliation complete; pre-start risk
> review and explicit Stream A acceptance required
>
> Owner: Jason / delegated Mac mini Codex specialist
>
> Proposed: 2026-10-13
>
> Authorization stream: **Stream A — proposed only.** M0 discovery, design and
> local synthetic analysis are in scope. No implementation, broker-policy
> change, runner-permission change or remote write is authorized by this record.

## Purpose and desired outcome

Provide a safe, reviewable way for a cloud agent to stage large or multi-file
HomeLab project documents for canonical publication in Forgejo without giving
the cloud agent a Forgejo credential, tailnet identity, OpenBao access, general
HomeLab network access or arbitrary execution authority.

The immediate need is document handoff, not general cloud-to-lab Git access.
The recommended M1 direction is a trusted local Mac import of a reviewed,
public GitHub staging branch into a new Forgejo branch. Forgejo remains the
authority and GitHub remains a temporary, explicitly approved transport for
this handoff. A broader signed multi-file pull-runner capability remains a
separate fallback design, not an implied implementation path.

This project produces no speech; the repository-wide Aster voice requirement
is not applicable.

## Current state and M0 evidence

- Live Forgejo is version 15.0.7 on LXC 108 (`192.168.20.30`) and its service
  is active. The canonical `jason/homelab` `main` ref is
  `da8b0fca9783fb72ca1ac9da9d31a97f971cfb93`.
- GitHub `main` was read-only verified at the same SHA. The staged branch
  `aster-home-eh001-feasibility` is public, at
  `1b5b5a52e7d2425bc4f2ed88052720f2e1cb1dac`, and is three unsigned,
  docs-only commits ahead of `main` with no commits behind it. Its changed
  files are exactly three added Markdown documents, including this project's
  staged charter.
- The requested `docs/Environment-and-Release-Lifecycle.md` does not exist in
  the local checkout or on live canonical `main`. This is a documentation gap,
  not an authorization to invent lifecycle rules.
- The completed pull-based runner remains intentionally canary-only. Its
  effective write boundary is one new UTF-8 text file, at most 4 KiB, under
  `ai-pam-pilot/`, on a new `ai-pam/*` branch from `main`, with a Yellow
  payload-bound Companion approval. The runner has no direct Forgejo or
  OpenBao credential and cannot update, delete, merge or write `main`.
- The broker source enforces kernel peer identity, canonical payload hashes,
  one-use requests, policy-digest reauthorization, bounded 1–900 second TTLs,
  lifecycle revocation and a global kill switch. The local full
  `ops/credential-broker` suite passed **112/112** on 2026-10-13.
- Live LXC 104 checks show `homelab-broker.service`, both Forgejo gateways and
  `homelab-bundle-health.timer` active. Live broker metadata reports
  `global_enabled=true` and 115 audit events. Live runner health is healthy,
  with an intact ledger and two consumed/two revoked records.
- A material drift requires resolution before using the runner for any new
  flow: the worker's live `base_revision` is `d7e49c4d4d6b7124a764208cc44e0ef9ed12797b`,
  while canonical Forgejo `main` is `da8b0fca…`. The worker must not silently
  rebase or treat its stale pin as current evidence.

See the independent [M0 evidence log](AI%20Projects/evidence/Cloud-Agent-Forgejo-Document-Publishing-M0.md)
for command-level evidence and provenance.

## Scope and exclusions

### In scope

- Read-only reconciliation of canonical Forgejo, GitHub staging provenance,
  the completed runner, broker policy and relevant repository tests.
- A trusted local import design for documentation-only, multi-file packages.
- Offline and synthetic tests for provenance, base drift, path/file-type limits,
  secret-like content, branch confusion, partial import and rollback.
- A future bounded implementation only after an accepted risk envelope,
  explicit source/path/size/count limits and a fresh gate.
- Operator documentation, audit receipts, rollback and evidence sufficient for
  a human to reproduce the import without the implementation agent.

### Explicit exclusions

- No change to AI-PAM policy, broker code, gateway code, runner code,
  OpenBao, Authentik, Forgejo permissions or protected-branch rules in M0.
- No public Forgejo ingress, inbound tunnel, webhook receiver, generic Git
  proxy, cloud-to-LAN connection or tailnet credential in the cloud.
- No direct GitHub push, Forgejo push, pull-request mutation, merge, tag,
  release, workflow trigger or branch deletion in this M0 record.
- No automatic GitHub-to-Forgejo promotion. GitHub is an untrusted staging
  transport and never becomes canonical.
- No confidential operational material, credentials, private keys, secret
  configuration or unreviewed private-address inventory may be placed on a
  public GitHub staging branch.
- No general repository write authority, arbitrary patch execution, package
  installation, workflow/configuration publication or production deployment.
- No attempt to “fix” the stale runner base pin as part of this project until
  its exact owner, desired target and validation/rollback are separately
  recorded.

## Authority model

| Fact or control | Authority |
|---|---|
| Project intent, scope and risk decision | This project in HomeLab Git/Forgejo |
| Canonical repository history and current base | Forgejo |
| Temporary staging artifact | GitHub branch, treated as untrusted input |
| Human identity and approval | Jason through the normal local Git/Forgejo workflow and existing Companion gates where applicable |
| Broker identity/capabilities | AI-PAM broker and its policy database |
| Service credentials | OpenBao behind the existing broker-private gateways |
| Runtime inventory | NetBox where adopted; live systems for current health |
| Derived mirror | GitHub after Forgejo promotion; never proof of canonical acceptance |

## Architecture and data flow

```text
cloud agent
  -> public GitHub staging branch (temporary, reviewed, no secret material)
  -> trusted Mac local checkout
  -> verify branch tip, merge-base, file/path policy, hashes and diff
  -> run local tests and secret/content checks
  -> human reviews exact documentation diff
  -> create/push a new non-main Forgejo branch through normal Git tooling
  -> read-only verify Forgejo commit/tree and later GitHub mirror
```

The local Mac is the trust boundary for import. The staging branch does not
receive any Forgejo credential and cannot cause a remote write by itself. The
importer must fetch a pinned branch tip, reject a changed tip during review,
and stop if Forgejo `main` advances before promotion. A future private or
automated path may reuse the runner only after a new capability design proves
that local import is insufficient.

## Privacy and security design

The preferred path adds no broker capability, service identity, network path,
credential or runner authority. Its unavoidable new exposure is that the
staging branch is public: a document package must therefore be classified as
safe for public GitHub visibility before staging. The local importer treats
all fetched content as untrusted and never executes repository-provided code,
hooks, workflows, binaries or dependencies.

Required controls for any implementation:

1. Pin and record the exact GitHub branch tip, Forgejo `main` base SHA, source
   commit list and resulting Forgejo commit; do not import a moving branch.
2. Allow only an explicit documentation path allowlist and Markdown/text file
   types, with file-count, per-file and total-size ceilings. Reject symlinks,
   submodules, binaries, executable/configuration paths and path traversal.
3. Scan the complete proposed diff for credentials, private keys, secret-like
   values and accidentally copied private operational data. A public-content
   failure is a hard stop.
4. Review the human-readable diff locally, run relevant tests, and verify the
   resulting Forgejo tree contains exactly the reviewed files. Do not replay
   the staging branch wholesale over newer canonical work.
5. Require Jason's immediate explicit confirmation before each Forgejo remote
   write. Push only Forgejo `origin`; observe the GitHub mirror afterward.
6. Retain a source-to-canonical receipt with hashes, review decision, base,
   destination branch and mirror observation. Never store credentials or raw
   approval material in the receipt.

## Before/after security-loss comparison

| Candidate | Security change | M0 decision |
|---|---|---|
| Trusted local GitHub-staging import | Adds public staging visibility and a manual trust/reconciliation step; adds no lab privilege or network reach | **Preferred and sufficient for the current docs-only need**, conditional on public-content review and exact import gates |
| Expand pull runner to signed multi-file docs | Increases payload/resource/path/atomicity exposure and requires new runner validation and write semantics; retains a stronger private transport story | Defer; only justify if local import cannot meet a concrete operational requirement |
| Network bridge, public Forgejo endpoint or generic credentialed Git proxy | Adds remote attack surface, credential/exfiltration risk and broader lateral-movement potential | Reject |

The local import is not “trusted because it came from GitHub.” It is trusted
only after the Mac operator verifies provenance, content policy, base ancestry,
tests and the exact proposed diff. The unsigned public commits and branch
visibility are residual risks that must be accepted for each staging package.

## Pre-start risk assessment

| Risk | Likelihood / impact | Control | Residual decision |
|---|---|---|---|
| Public staging exposes private HomeLab details | Medium / high | Public-content classification, secret scan, no private material, stop on uncertainty | Accept only per package; otherwise use a private human-carried artifact and new risk review |
| Staging branch is changed or substituted | Medium / high | Pin SHA, record commit list, verify branch and merge-base again before import | Low after exact receipt; mismatch stops |
| Canonical Forgejo advances during review | Medium / medium | Re-read Forgejo `main`; require exact base or regenerate/re-review | Stop and regenerate; never silently merge |
| Multi-file docs contain executable or policy-changing content | Medium / high | Documentation-only allowlist, file/count/size caps, no hooks/binaries/workflows, human diff review | Low for approved paths; new paths require fresh decision |
| Local importer makes wrong remote change | Low / high | New non-main branch, explicit immediate write confirmation, read-only post-write verification | Accept only with operator present |
| Stale runner base/policy is mistaken for current | High / medium | Do not use stale `base_revision`; reconcile/update under separate bounded task | Current blocker for runner-based implementation |
| GitHub mirror or staging is mistaken for authority | Medium / high | Forgejo-first receipt and separate mirror observation | Low if documented and enforced |

No irreversible operation is required for M0 or the recommended import design.
The recovery point is the unchanged Forgejo `main` commit plus the local
review receipt. A failed import leaves canonical history unchanged; discard
the unpushed local branch and evidence workspace. A remote branch cleanup, if
ever desired, requires its own explicit authorization.

## Persistence and resumability

Persist the source branch tip, merge-base, changed-file list, content hashes,
policy version, reviewer decision, destination branch, Forgejo commit and
mirror observation in a non-secret receipt. Never infer success from process
exit status alone. On resume, re-read this project, the standard, current
Forgejo `main`, the source tip and local Git status. Any source or canonical
drift invalidates the pending receipt and requires a fresh review.

## Milestones and gates

### M0 — read-only reconciliation and recommendation

- [x] Read repository governance, runner project/runbook, AI-PAM reference,
  broker source/tests and staged charter.
- [x] Verify live Forgejo version, canonical `main`, branch inventory and GitHub
  mirror/staging refs without writing remote state.
- [x] Verify live broker/gateway/runner health and record base/policy drift.
- [x] Run the local broker test suite and compare candidate architectures.
- [x] Record the local-import recommendation, exact blockers and approval gates.

Gate: no implementation may start until Jason accepts the pre-start risk
assessment and chooses the proposed Stream A envelope.

### M1 — local importer design and synthetic validation (not started)

Define the exact docs-only paths, file/count/size limits, public-content policy,
receipt format, import procedure and rollback. Validate with synthetic branches
covering stale base, changed tip, traversal, symlink, binary, secret-like,
oversized, partial and conflicting inputs. Gate: all denied cases fail closed
and the operator can reproduce a no-write dry run.

### M2 — reviewed local import canary (not authorized)

After M1 acceptance, import one public-safe synthetic or project-document
package into a new Forgejo branch. Obtain immediate confirmation before the
actual Forgejo push, verify the exact tree and observe GitHub's derived mirror.
No merge, direct `main` write or branch deletion.

### M3 — recovery, operations and graduation (not authorized)

Prove interrupted import recovery, receipt integrity, source/canonical drift
handling, documentation, Doctor/monitoring/backup impact and post-deployment
intent/efficiency review. Graduate only if the path remains supportable without
the implementation agent and residual public-staging risk is accepted.

## Validation and evaluation

Required tests include normal docs import, public-content review, exact base
ancestry, branch-tip substitution, stale Forgejo main, duplicate/conflicting
paths, Unicode/case path tricks, traversal, symlinks, submodules, binaries,
oversized files/total payloads, secret patterns, hooks/workflows/configuration,
partial import, interrupted review, remote rejection and recovery. Critical
behavior needs two independent production-shaped passes before graduation.

The runner's existing 112-test Linux baseline remains a regression gate. The
current local M0 run was 112/112; it is evidence of the existing boundary, not
evidence that a multi-file extension is safe.

## Observability, maintenance and recovery

M0 changes no host, service, guest, network path or monitoring inventory.
Beszel, NetBox, Doctor, backups, Homepage, DNS, certificates, firewall and
authentication are therefore unchanged and are recorded as N/A for M0. Any
future importer deployment must reassess each integration, including Beszel
coverage for an affected host/service, backup/restore of receipts and the
runner/policy state, and a human operator handover.

## AI administration posture

The recommended local importer uses the human operator's existing local Git
administration path and does not add an AI service identity. AI administration
for this project is therefore **not currently supported as a new capability**;
the reason is that adding an AI write capability is unnecessary for the current
docs-only need and would widen the established boundary. Human break-glass
Forgejo administration remains independent. Any future automated importer
must define a dedicated `ai-*` identity, broker capability, custody,
revocation, rotation and passkey approval before implementation.

## Integration impact checklist (M0)

| Integration | M0 result |
|---|---|
| HomeLab Doctor | N/A — no deployment or runtime change; future importer health needs a separate check |
| Monitoring/Beszel | N/A — no host/service change; reconcile if an importer service is deployed |
| Backup/recovery | N/A for M0; preserve canonical `main` and local receipts; future state needs restore proof |
| NetBox | N/A — no infrastructure object changed |
| Human wiki | Future operator handover; no M0 operational procedure yet |
| Aster mirror | No derived summary until a canonical project record is accepted |
| Operational reference/runbooks | This project records the M0 recommendation; future importer requires a runbook |
| Repository documentation | This charter, portfolio entry and evidence log added locally |
| Diagrams/rack records | N/A — no topology or physical change |
| Homepage/service discovery | N/A — no new service or UI |
| Authentication/authorization | No change; existing human Git/Forgejo and AI-PAM boundaries retained |
| DNS/certificates/firewall | N/A — no network change |
| Automation/schedules | N/A — no importer automation deployed |
| Security inventory | No credential, key, account or permission added |
| AI administration | Explicitly not currently supported as a new capability; see above |

## Graduation criteria

Graduate only after Jason accepts the Stream A envelope, the chosen import
method has passing synthetic denial/recovery tests, exact source-to-Forgejo
receipts exist for two independent passes, public-staging residual risk is
accepted, operational documentation is complete, and the post-deployment
intent/efficiency review and user handover are done. A broader runner
permission change requires a new risk decision even if this project graduates.

## Close-out

M0 recommends trusted local GitHub-staging import as the least-relaxing method
that is sufficient for the current large/multi-file documentation handoff.
The main blockers are explicit Stream A acceptance, package public-safety
classification, exact import limits/procedure, and resolution or deliberate
non-use of the stale runner base pin. No live implementation has started.
