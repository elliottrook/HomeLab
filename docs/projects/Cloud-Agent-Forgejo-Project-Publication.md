# Cloud-agent Forgejo project publication

> Status: Proposed — Stream M; M0 design and risk acceptance required
>
> Owner: Jason
>
> Proposed: 2026-10-13
>
> Authorization stream: **Stream M — Monitored**. This project document records
> a proposed narrow capability. It does not authorize a live deployment, a
> remote write or a merge. Each remote Forgejo write still requires Jason's
> immediate confirmation under the repository rules.

## Terminology and intent

For this project, **git means Forgejo**. Forgejo is the authoritative source of
truth and publication target. GitHub is only Forgejo's derived protection mirror;
it is never an input source, promotion source or direct write target.

The desired operator experience is:

> “Cloud agent, commit and push to git.”

That means a cloud agent may prepare a project package and submit it to the
approved local publication path. After the normal privacy, policy and human
approval checks pass, the local path may create a new non-main branch in
Forgejo. A later human merge remains separate. Forgejo's existing mirror then
publishes the accepted Forgejo commit to GitHub, where the ref is checked
read-only.

The project is intentionally an access expansion, not a change in authority:
the cloud agent receives no Forgejo credential, tailnet identity, OpenBao access,
direct LAN route, GitHub credential or ability to merge, delete, force-push or
trigger workflows.

This project produces no speech; the repository-wide Aster voice requirement is
not applicable.

## Desired outcome and boundary

Enable a cloud agent to submit a multi-file, larger project-document package
through the existing AI-PAM approval and bounded Forgejo write path while
preserving the following boundary:

- the package is prepared in the cloud, but is not accepted as authoritative
  until it passes local validation and Jason approves the exact content;
- the only publication target is Forgejo, on a newly created `ai-pam/` branch
  from an exact current Forgejo `main` revision;
- the initial allowlist is limited to text project records under
  `docs/projects/` and `docs/handovers/`;
- the automatic GitHub mirror is a derived output and is verified read-only;
- the package cannot execute code, install dependencies, alter CI/workflows,
  change credentials, modify infrastructure configuration or write `main`.

The existing single-file 4 KiB AI-PAM canary is not silently widened. This
project must introduce a separately versioned capability or runner policy for
the multi-file document package, with its own tests, policy digest and rollback.

## Current verified baseline

- Forgejo `origin` is canonical. GitHub is the automatic mirror and is not a
  promotion path.
- The current canonical Forgejo `main` observed for this project is
  `da8b0fca9783fb72ca1ac9da9d31a97f971cfb93`. This must be rechecked at M0 and
  again immediately before any publication.
- AI-PAM already provides approval-bound payload hashes, policy-digest
  reauthorization, one-use consumption, expiry, revocation, a global disable,
  OpenBao-held Forgejo credentials and separate read/write gateways.
- The existing safe-write capability is deliberately narrower: one new file,
  at most 4 KiB, below `ai-pam-pilot/`, from `main` to a new `ai-pam/` branch.
- Existing local policy adapters already reject secret-shaped content and
  enforce path, size and output limits, but they are not proof that every
  operational detail is safe to publish to a public mirror. The new document
  policy must make that check explicit before the Forgejo write.
- The earlier GitHub-first process has been rescinded. Its Forgejo branch was
  deleted, its local branch was retired, and its staging design is not an
  input or dependency of this project.

## Scope

### In scope

- A versioned, signed, immutable package manifest containing repository,
  exact base revision, destination branch, file paths, content digests, sizes,
  expiry, nonce and policy digest.
- A local pull-based or broker-mediated publication path that has no inbound
  cloud-to-LAN listener and gives the cloud agent no HomeLab credential.
- UTF-8 text documents only, initially limited to `docs/projects/` and
  `docs/handovers/`.
- A conservative package cap of at most 32 files, 256 KiB per file and 2 MiB
  total until measured evidence justifies a smaller or larger value.
- Rejection of deletes, renames, symlinks, submodules, binaries, LFS objects,
  hidden/traversal paths, case-colliding paths and executable content.
- Explicit privacy checks for credentials, tokens, private keys, secret-shaped
  values, private network/service details and other content that would be
  inappropriate for the automatic GitHub mirror.
- Jason's review of the exact file list, base, branch, content digest, policy
  result, expected effect and rollback before each Forgejo write.
- A new non-main branch only; merge, release, tag, workflow and branch cleanup
  remain separate human operations.
- Read-only verification of the accepted Forgejo ref and its automatic GitHub
  mirror.
- Recovery, revocation, monitoring, audit receipt and operator documentation.

### Explicit exclusions

- No GitHub-first staging, GitHub-to-Forgejo promotion or direct GitHub push.
- No cloud-held Forgejo, GitHub, OpenBao, Authentik, tailnet or HomeLab
  credentials.
- No arbitrary repository push, patch application, code execution, test run,
  dependency installation, hook execution or submodule fetch.
- No writes outside the project-document allowlist; no service code,
  infrastructure, secrets, workflows, CI configuration or repository policy.
- No direct write to Forgejo `main`, protected refs, tags or releases.
- No merge, force-push, branch deletion, workflow trigger or remote cleanup as
  part of the agent publication action.
- No new public ingress, firewall rule, DNS record, tailnet route or listener.
- No claim that a successful secret-pattern scan makes arbitrary documents
  safe. A package that cannot be classified as safe for the automatic GitHub
  mirror is rejected or held for a separately designed private publication
  path.

## Authority model

| Fact or control | Authority |
|---|---|
| Project scope, risk decision and publication policy | HomeLab project record in Forgejo |
| Canonical repository state and base revision | Forgejo |
| Package bytes and manifest | Signed immutable submission; never authority by itself |
| Human approval and revocation | AI-PAM/Authenticator approval path |
| Forgejo write credential | OpenBao through the existing bounded gateway |
| Publication result | Forgejo ref and tree, verified read-only |
| GitHub copy | Derived mirror only; never an input |

## Proposed architecture and data flow

```text
cloud agent workspace
  -> signed immutable document package and manifest
  -> bounded approved exchange or local pull inbox
  <- local publication worker retrieves package
  -> offline schema, path, size, text, privacy and base validation
  -> exact package shown to Jason through the existing approval path
  -> one-use AI-PAM approval bound to package and policy digest
  -> local write gateway obtains Forgejo credential from OpenBao
  -> new ai-pam/<project> branch from exact Forgejo main
  -> read-only Forgejo ref/tree verification
  -> read-only observation of Forgejo's GitHub mirror
```

The worker must not connect directly from the cloud agent to Forgejo. It must
not execute package-controlled code. A valid signature proves producer identity
only; it does not make content safe or authorize a broader action.

## Pre-start risk assessment

| Risk | Concrete failure | Required control | Residual risk / decision |
|---|---|---|---|
| Cloud-agent compromise or prompt injection | A compromised agent submits a malicious or misleading document | No credential or LAN route; signed identity; docs-only paths; text/size/count caps; offline validation; exact human approval | A malicious document can still be approved by mistake; remain Stream M and show the full diff |
| Public mirror exposure | A document contains a private address, token, topology detail or personal data and is mirrored to GitHub | Treat GitHub visibility as a pre-write requirement; secret/private-detail checks; human review; fail closed on ambiguity | Existing checks are narrower than a universal privacy proof; uncertain content is blocked, not waived |
| Base or policy drift | Package is reviewed against one tree but written against another | Bind exact Forgejo base SHA and policy digest; re-read both before approval and consume; regenerate on drift | Availability delay accepted; no silent rebase |
| Replay or duplicate publication | A captured approval or package is reused | Short TTL, nonce, immutable digest, atomic one-use ledger, revocation and restore high-water check | Requires Linux-host recovery evidence before graduation |
| Write-target escalation | A path or manifest attempts to reach `main`, workflows or arbitrary files | Independent allowlist validation; branch prefix; gateway-side recheck; deny deletes/renames/force updates | Any mismatch is a hard stop |
| Runner/gateway compromise | The worker is used to reach Forgejo, OpenBao or unrelated services | Separate identity, local socket only, systemd confinement, no inbound listener, destination allowlist and denial tests | Bounded local risk remains; no graduation without isolation evidence |
| Oversized package or resource exhaustion | Large input consumes worker storage or approval UI | Per-file, total, count and manifest caps; bounded unpacking; quota and cleanup; no unbounded retries | Availability risk accepted only within measured caps |
| Mirror lag or failure | Forgejo accepts a commit but GitHub remains stale | Treat Forgejo as complete source of truth; report mirror pending; verify read-only and never push GitHub directly | Temporary public-mirror inconsistency is observable, not repaired by bypass |
| Receipt or review leakage | Logs expose document contents, private metadata or signing material | Metadata-only mode-0600 receipt; content outside logs; no credential/private-key collection; bounded retention | Operator access still requires ordinary host controls |
| Stale implementation pin | Runner code differs from the reviewed canonical source | Reconcile runner base and policy digest at M0; block deployment until exact pins are recorded | Current known drift is a pre-start blocker, not an accepted risk |

## Recovery and stop conditions

Before any live installation, capture and verify a protected checkpoint of the
affected runner/broker state, policy files, unit files and replay ledger. Do not
include private signing keys or Forgejo credentials in the project evidence.

Rollback disables only the new worker/capability, revokes outstanding requests,
restores the prior policy/runner state and leaves Forgejo, GitHub, the broker's
existing canary and human access unchanged. A published non-main branch remains
an auditable Forgejo record; deleting it is not part of automatic rollback and
would require separate immediate confirmation.

Stop before further work on any exposed secret, unexpected network destination,
privacy classification ambiguity, base/policy mismatch, replay ambiguity,
unverifiable checkpoint, broker regression, need for code execution, request to
write outside the allowlist, or need to alter GitHub directly.

## Milestones and gates

### M0 — reconcile and accept the narrow design

- [x] Reconfirm the canonical Forgejo base and current local AI-PAM policy and
  safe-write sources. The live runner source pin is now confirmed stale and is
  a deployment blocker.
- [x] Read-only verify that the retired GitHub-first Forgejo branch and local
  branch are absent; the replacement Forgejo branch and its GitHub mirror match
  at `d43ca9ee`.
- [ ] Confirm the public-mirror privacy boundary and the exact document path,
  count, per-file and total-size caps.
- [ ] Record owner, recovery checkpoint location, retention and operator path.
- [ ] Decide whether the project remains Stream M through graduation. Stream A
  is not assumed.

Gate: an independent reader can tell exactly what the cloud agent may submit,
what the local worker may write, what it may never reach and how rollback works.
The design gate is recorded; implementation remains blocked on runner-base
reconciliation and explicit acceptance of the public-mirror boundary.

### M1 — policy and offline validator

- [x] Define the versioned manifest and canonical digest encoding in the
  separate `project_document_bundle_verifier.py` capability.
- [x] Implement the validator without widening the existing single-
  file canary policy in place.
- [x] Add adversarial tests for path traversal, collisions, symlinks, deletes,
  renames, binaries, hidden files, executable content, oversized packages,
  secret-like values, private-detail patterns, stale base, replay and policy
  drift.
- [x] Prove the validator performs no network, Git, Forgejo, OpenBao or broker
  I/O and executes no package-controlled content.

Gate: local broker suite passes `119/119`; the new capability is separately
versioned, bounded and fail-closed. **Local gate passed 2026-10-13.** Live
installation and gateway integration remain M2 work and are not authorized by
this gate.

### M2 — isolated approval-path canary

- [ ] Install only the new worker/policy after a verified checkpoint.
- [ ] Exercise synthetic packages through intake, validation, approval, revoke,
  expiry and kill-switch paths without a live Forgejo write.
- [ ] Prove isolation from Forgejo credentials, OpenBao, read gateway, unrelated
  files/sockets, arbitrary network destinations and package execution.
- [ ] Verify metadata-only receipts, cleanup and restart/resume behavior.

Gate: two independent synthetic passes and all denial cases pass; no remote
state changes have occurred.

### M3 — Forgejo-only remote canary

- [ ] Obtain Jason's immediate confirmation for the exact first Forgejo write.
- [ ] Publish one approved document package to a new `ai-pam/` branch only.
- [ ] Verify the exact Forgejo commit/tree and observe GitHub's mirror read-only.
- [ ] Repeat with a fresh nonce and base; prove stale/replayed/revoked requests
  cannot write.

Gate: two complete Forgejo-first passes, no GitHub direct write, no merge and no
  scope expansion.

### M4 — recovery, operation and graduation

- [ ] Restore the ledger/policy/runner in isolation and prove consumed and
  revoked requests remain terminal.
- [ ] Add Doctor/monitoring checks for worker health, stale requests, failed
  validation and mirror lag without logging content.
- [ ] Complete operator walkthrough, retention review and rollback evidence.
- [ ] Record residual risks, accepted limitations and the next allowed package
  class, if any.

Gate: safe publication and recovery no longer depend on the implementation
agent, and the capability remains narrower than arbitrary Forgejo access.

## Evidence log

| Milestone | Evidence | Status |
|---|---|---|
| M0 | This design; branch-rescission verification; canonical base and policy reconciliation | In progress |
| M1 | `project_document_bundle_verifier.py`, manifest rules, denial tests and full broker regression | Local gate passed 2026-10-13; live integration not started |
| M2 | Checkpoint, isolation, approval/revocation and synthetic canary evidence | Not started |
| M3 | Forgejo branch/tree and mirror read-only verification | Not started |
| M4 | Restore, monitoring, operator handover and graduation review | Not started |

## Required integration checks

- Forgejo remains the only authoritative publication target.
- GitHub is checked only as a derived mirror after Forgejo acceptance.
- No new network route, public ingress, firewall rule, DNS record or service
  credential is introduced.
- AI-PAM's existing approval, revocation, one-use and emergency-disable paths
  remain intact and are not bypassed.
- The repository's protected-branch, backup, monitoring and operational
  documentation remain consistent with the new capability.
- Any future content class or path outside the initial allowlist is a new
  scope/risk decision, not an implementation convenience.

## Next safe action

Complete M0 read-only reconciliation and present the exact policy/capability
change for approval. Do not deploy a worker, alter AI-PAM policy, create a
Forgejo branch or push any project commit until M0 is accepted and the normal
immediate confirmation is obtained for each remote write.
