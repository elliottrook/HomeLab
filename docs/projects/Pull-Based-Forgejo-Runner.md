# Pull-based Forgejo change-bundle runner

> Status: Active — Stream A; M0–M1 complete, M2 in progress
>
> Owner: Jason
>
> Proposed and started: 2026-10-10
>
> Authorization stream: **Stream A — Autonomous**, granted by Jason on
> 2026-10-10 after directing that the project be designed and completed under
> the HomeLab Project Creation Standard. This authority covers the exact scope,
> changes, risks, exclusions and gates below. Non-waivable stops and immediate
> confirmation before each remote Git write still apply.

## Purpose and desired outcome

Let a cloud coding agent submit a narrowly scoped change without receiving a
Forgejo credential, tailnet identity, OpenBao access or general HomeLab network
access. A local, pull-based worker verifies an immutable signed bundle, validates
it without network access and submits the already-established AI-PAM Yellow
`forgejo.write.safe-branch` request. Jason reviews and approves the exact change
in Aster Companion before the existing broker writes one new file to a new
`ai-pam/` branch. Forgejo remains canonical and GitHub remains its automatic
read-only protection mirror.

Success means one synthetic canary follows that full path twice independently,
denied/adversarial cases fail closed, recovery and revocation are proven, and no
public ingress or cloud-held HomeLab credential is introduced.

This project produces no speech; the repository-wide Aster voice requirement is
not applicable.

## Current state and evidence

- HomeLab commit `d22c0d24ecf8679f1c10c21e9870be91b5989bd1` is the design baseline.
- Forgejo 15.0.7 on unprivileged LXC 108 is canonical; GitHub is its automatic
  protection mirror.
- AI-PAM is graduated on unprivileged LXC 104. Its broker uses kernel peer
  credentials on group-restricted Unix sockets. Authentik/passkey approval,
  payload hashes, policy digests, one-use consumption, revocation, OpenBao
  custody, a global kill switch and separate Forgejo read/write gateways are
  already proven.
- The safe-write gateway permits only one new file, at most 4 KiB, below
  `ai-pam-pilot/`, from `main` to a new `ai-pam/` branch. It cannot update,
  delete, merge, push main, administer Forgejo or accept credential arguments.
- LXC 104 has 2 vCPU, 4 GiB RAM, a 20 GiB disk and low observed idle use. It is
  on Lab VLAN 70 and has no Tailscale daemon. The broker exposes no network API.
- The existing Tailscale subnet router on LXC 100 provides private human
  administration without public ingress. VLAN 70 is deliberately not
  advertised to tailnet clients.
- The inherited offline verifier candidate passed 5/5 tests. The existing
  broker non-socket selection passed 65/65. Seventeen Unix-socket tests were
  blocked by the former macOS sandbox and remain a required Linux-host gate.

## Scope and exclusions

### In scope

- Versioned, strict bundle schema for one UTF-8 text file under
  `ai-pam-pilot/cloud-runner/`.
- OpenSSH `sshsig` verification with a dedicated namespace and a root-owned
  allowed-signers file pinned to a named producer principal.
- Exact repository, base SHA, branch, path, size, digest, issue/expiry, policy
  digest and nonce checks.
- Durable replay ledger on protected storage; atomic reserve, request binding,
  consumption, revocation and restore high-water reconciliation.
- A separate unprivileged `hlabundle` identity on LXC 104. It may reach only the
  broker client socket and its own inbox/state/work directories.
- Outbound-only retrieval from one content-addressed immutable exchange after
  that exchange is selected and verified. Polling must use bounded timeouts,
  size limits, TLS verification, no redirects to unknown origins and no
  credential-bearing URL or logs.
- Network-denied validation in a transient systemd sandbox. No bundle-controlled
  command, test, dependency install, Git hook, submodule, binary or symlink runs.
- Reuse of the existing Yellow safe-write capability and Companion approval.
- Synthetic canary branch only; normal merge remains a separate human action.
- Doctor/monitoring, backup/restore, audit, NetBox/Beszel reconciliation,
  operator documentation, rollback and two independent end-to-end passes.

### Explicit exclusions

- No public ingress, inbound tunnel, broker HTTP endpoint, generic Git proxy,
  webhook receiver or cloud-to-LAN connection.
- No tailnet credential in the cloud and no new Tailscale daemon or advertised
  route for the PoC. Installing Tailscale on LXC 104 would broaden its trust
  boundary without enabling the outbound pull or local broker path; the existing
  Tailscale administration route remains unchanged.
- No Forgejo, OpenBao, Authentik or exchange credential in chat, Git, bundles,
  logs or cloud-agent memory.
- No arbitrary patch, multi-file change, file update/delete, binary, symlink,
  submodule, LFS object, workflow change, package install or command execution.
- No direct main write, automatic merge, tag, release, workflow trigger, branch
  deletion or direct GitHub push.
- No widening of the existing safe-write gateway or protected-branch policy.
- No production repository content beyond the isolated canary path until the
  PoC graduates; broader capability requires a new project/risk decision.

## Authority model

| Fact or control | Authority |
|---|---|
| Project intent, schema and policy | HomeLab Git/Forgejo |
| Canonical repository/base revision | Forgejo |
| Human identity and passkey session | Authentik |
| Agent identity, capability and approval lifecycle | AI-PAM broker |
| Forgejo service credential | OpenBao plus Forgejo native scope |
| Producer identity | Root-owned allowed-signers policy on the worker |
| Bundle bytes | Content-addressed immutable exchange; never an authority for acceptance |
| Runtime guest/IP/service inventory | NetBox where adopted |
| Runtime health | systemd, Doctor and existing monitoring |
| GitHub copy | Derived protection mirror only |

## Architecture and data flow

```text
cloud agent
  -> signed, immutable, non-secret one-file bundle
  -> approved content-addressed exchange
  <- outbound polling by hlabundle on LXC 104
  -> schema/signature/hash/replay/base validation
  -> network-denied transient validation workspace
  -> AI-PAM Yellow request over local Unix socket
  -> Jason reviews exact path/content hash/effect/rollback in Companion
  -> payload-bound one-use approval
  -> existing safe-write gateway obtains its credential from OpenBao
  -> one new file on one new ai-pam/ branch in Forgejo
  -> read-only Forgejo ref/tree verification
  -> read-only GitHub mirror observation
```

The worker never connects directly to Forgejo or OpenBao. The existing broker
remains the only promotion path. The bundle is untrusted input even when its
signature is valid.

## Pre-start risk assessment

| Risk | Likelihood / impact | Control | Residual decision |
|---|---|---|---|
| Cloud compromise submits malicious content | Medium / high | No lab credential; signed identity; strict schema; text-only 4 KiB canary; no execution; human approval | Low enough for synthetic PoC |
| Replay or restored ledger resurrects approval | Medium / high | Durable nonce uniqueness, atomic state changes, backup plus append-only audit/high-water reconciliation | Must prove restore before graduation |
| Bundle changes after review | Medium / high | Canonical manifest, artifact hash, immutable storage, re-hash immediately before broker submission/consume | Fail closed |
| Stale Forgejo base or policy | Medium / high | Exact SHA and policy digest checked at intake and immediately before promotion | Regenerate; never rebase silently |
| Runner compromise reaches broader lab | Low / high | Separate UID; local Unix socket only; systemd confinement; no direct Forgejo/OpenBao access; no inbound listener | Accept for bounded PoC after denial tests |
| Existing LXC 104 outage affects AI-PAM | Low / medium | No new guest dependency; staged install; protected checkpoint; existing human access unaffected | Roll back runner files/unit only |
| Secret appears in content/logs | Medium / high | Existing secret-pattern checks, metadata-only audit, no environment dump, quarantine and revoke | Any hit stops project |
| Exchange outage or equivocation | Medium / low | Content address, signature, bounded retries, last-success status; outage cannot promote | Availability loss accepted; integrity preserved |
| Remote branch clutter | Medium / low | Unique canary names; deletion only with immediate explicit authorization | Retain branches until authorized cleanup |
| Tailscale installation broadens trust | Medium / medium | Do not install it; retain current private admin route | Explicit design choice |

No irreversible operation is required. Recovery checkpoint: protected LXC 104
backup/snapshot plus copies of broker database, unit files and runner state
before deployment. Rollback disables/removes only the runner unit and identity,
restores the checkpoint if needed, and leaves broker, Forgejo and human access
unchanged. Abort on an exposed secret, unexpected reachable destination, broker
regression, unverifiable checkpoint, policy mismatch, replay ambiguity, or any
need for multi-file/arbitrary execution.

Expected interruption is none. Installation may restart only a new runner unit;
the broker/gateways are not restarted unless a separately validated compatibility
change is required. No DNS, certificate, public firewall, Authentik flow or
protected-branch change is planned.

## Persistence and resumability

- SQLite state records nonce, request digest, signer principal, bundle hash,
  broker request ID and terminal state; WAL and full synchronous mode are used.
- Intake is `received -> validated -> approval-pending -> consumed` or terminal
  `rejected/revoked`; transitions are atomic and idempotent.
- Partial downloads and workspaces are not visible to the validator.
- A restored database cannot resume until its high-water/audit reconciliation
  passes. A missing or ambiguous record fails closed.
- This project document records the current milestone, exact blocker, evidence
  and next safe action at every boundary.

## Milestones and gates

### M0 — reconcile and authorize

- [x] Read `AGENTS.md`, the Project Creation Standard, canonical Forgejo
  guidance, portfolio, AI-PAM project/reference and current network records.
- [x] Confirm repository clean baseline and preserve unrelated work.
- [x] Perform read-only live placement/capacity/broker inventory.
- [x] Record Stream A envelope, exclusions, risks, rollback and integration plan.

Gate: project is explicit enough for an independent reader to determine whether
each proposed mutation is authorized. **Passed 2026-10-10.**

### M1 — offline verifier and runner candidate

- [x] Land strict verifier, OpenSSH verifier, ledger and runner state machine.
- [x] Add adversarial tests for traversal, symlinks, replay, signer mismatch,
  expiry, stale base/policy, secret-like content, mutation and approval binding.
- [x] Run all credential-broker tests on Linux, including the 17 socket tests.
- [x] Secret-pattern and static review; no Forgejo/OpenBao/write exercised.

Gate: all local and existing regressions pass; code cannot represent a broader
action than the existing safe-write schema. **Passed 2026-10-10.**

### M2 — isolated worker installation

- [ ] Capture and verify recovery checkpoint.
- [ ] Create `hlabundle` identity, root-owned trust policy, protected state and
  inbox, and hardened network-denied validation unit on LXC 104.
- [ ] Register the worker in AI-PAM Probation with only the existing Yellow
  safe-write capability; prove denied access to read gateway, direct write
  gateway, OpenBao, Forgejo credential and unrelated files/sockets.
- [ ] Select and validate the immutable exchange; record retention and owner.

Gate: worker is healthy and observable but cannot promote without exact passkey
approval; global kill switch and identity suspension deny it.

### M3 — synthetic canary

- [ ] Run malformed, tampered, stale, replayed, wrong-signer, wrong-repository,
  wrong-path, oversized, secret-like and dependency-outage cases.
- [ ] Submit one valid canary and verify exact Companion display and approval.
- [ ] Immediately before the remote Forgejo write, obtain the repository-required
  explicit confirmation for that exact write.
- [ ] Verify branch/file/tree in Forgejo and observe GitHub mirror read-only.
- [ ] Repeat independently with a fresh nonce and base; test revoke/expiry.

Gate: two complete passes and all denied cases behave as designed. No merge.

### M4 — recovery, operations and graduation

- [ ] Back up configuration/state/trust metadata without private signing keys.
- [ ] Restore in isolation and prove consumed/revoked requests stay terminal.
- [ ] Add Doctor and monitoring checks, actionable metadata-only alerts, and
  last-success/staleness evidence.
- [ ] Reconcile NetBox and Beszel if LXC 104 service metadata changes; do not add
  a duplicate host. Update human wiki/Aster mirror/operations documentation.
- [ ] Complete post-deployment intent/efficiency review and operator walkthrough.
- [ ] Remove temporary access/workspaces and record accepted limitations.

Gate: safe operation and recovery no longer depend on the implementation agent.

## Validation plan

- Unit: canonical encoding, exact schema, signer principal, expiry, path/branch,
  artifact digest/size, regular-file/no-symlink, replay and state transitions.
- Integration: real `ssh-keygen -Y verify`, systemd sandbox, kernel peer UID,
  broker request/approval/consume, gateway denials and global kill switch.
- Regression: complete `ops/credential-broker` discovery on Linux.
- Security: no inbound listener; socket/file/destination denial; secret scan;
  malformed/adversarial inputs; no bundle-controlled execution.
- Recovery: interrupted download, restart at every state, ledger backup/restore,
  stale checkpoint and revoked-request cases.
- Production-shaped: two synthetic one-file branches, each explicitly approved
  at the remote-write boundary, with Forgejo and mirror evidence.

## Integration impact checklist

| Integration | Required result |
|---|---|
| HomeLab Doctor | Runner unit, ledger integrity, trust-policy metadata, queue age and last success; never content/secrets |
| Monitoring/Beszel | Reuse LXC 104 host coverage; add service failure/staleness alert without duplicate metrics |
| Backup/recovery | Config, ledger and trust public metadata; isolated restore and high-water reconciliation |
| NetBox | Existing LXC 104 remains authority object; record service role only if adopted schema supports it |
| Human wiki | One-page submit/review/revoke/recover procedure |
| Aster mirror | Sanitized derived summary only after operator reference is accepted |
| Operational reference | AI-PAM architecture, commands, states, denial meanings and rollback |
| Repository docs | Project portfolio, changelog, broker README and relevant architecture/reference |
| Diagrams/rack | Not applicable: no physical/topology change |
| Homepage | Not applicable: no new human web UI; Companion is the existing control surface |
| Authentication | Dedicated signer principal and `hlabundle`/AI-PAM identity; no human credential reuse |
| DNS/certificates/firewall | No new records/certificates/inbound rules; exchange TLS uses normal validation |
| Automation/schedules | One bounded systemd timer/service, single-instance lock, timeout and observable last result |
| Security inventory | Root-owned trust policy, no private key on runner, revocation procedure |
| AI administration | Existing AI-PAM capability; Yellow approval; global kill switch and human break-glass retained |

## User-facing handover

Before graduation, document exactly how a producer creates/signs a bundle, how
Jason recognizes the request in Companion, what `pending`, `rejected`,
`expired`, `revoked` and `consumed` mean, and how to suspend the worker or use
the global kill switch. The guide must state that approval creates only a new
canary branch/file; it does not merge, publish, deploy or delete anything.

## Evidence log

### 2026-10-10 — M0 project creation and live reconciliation

- Jason directed creation under the adopted standard and autonomous completion
  under Stream A.
- Local main was clean at `d22c0d24ecf8679f1c10c21e9870be91b5989bd1`.
- Read-only Proxmox inventory observed 9.2.20, ample storage, LXC 104 running as
  an unprivileged 2-vCPU/4-GiB/20-GiB guest, and broker/read/write gateways
  active. LXC 104 has no Tailscale daemon and only its VLAN 70 address.
- Reconciled the existing local-only broker transport and concluded that a new
  network-facing broker or Tailscale install would add risk without enabling the
  required path. The PoC will use a separate local UID and outbound retrieval.
- No production mutation, credential read, network/auth change or remote Git
  write occurred during M0.

### 2026-10-10 — M1 offline candidate complete

- Added `bundle_verifier.py`: exact one-file schema, OpenSSH namespace/principal
  verification, descriptor-based no-symlink reads, 4 KiB UTF-8/secret checks,
  exact base/policy/expiry binding and a monotonic SQLite replay ledger.
- Added `bundle_runner.py`: it can create only the existing
  `forgejo.write.safe-branch` Yellow request and cannot approve it. Immediately
  before consume it rechecks base, policy, expiry, broker-request binding and
  artifact digest.
- First adversarial run found and fixed an exception-sanitization defect in the
  symlink denial path. The operating system already denied the link; the fixed
  implementation now returns a bounded policy denial.
- New candidate tests: 13/13 passed locally, including a real ephemeral Ed25519
  `ssh-keygen -Y sign/verify` principal and namespace test.
- Copied non-secret sources to a disposable Proxmox `/tmp` directory and ran
  the full Linux suite: **95/95 passed in 21.520 seconds**, including all 17
  Unix-socket tests that the macOS sandbox could not run. Two pre-existing
  ResourceWarnings about test database cleanup were non-fatal and did not alter
  results. The disposable directory was removed afterward.
- No Forgejo, broker, OpenBao, Authentik, network-policy or remote Git mutation
  occurred in M1.

### 2026-10-10 — M2 recovery checkpoint established

- Verified the scheduled `backups` storage contains a fresh LXC 104 archive
  from 2026-10-10 (`vzdump-lxc-104-2026_10_10-02_34_36.tar.zst`,
  1,955,376,585 bytes).
- Created live snapshot `forgejo-runner-preinstall-20261010` with the broker and
  both Forgejo gateways healthy. The guest filesystem freeze/thaw completed.
- Proxmox warned that aggregate thin-volume virtual sizes exceed the pool and
  volume-group capacity. Actual `local-lvm` use observed in M0 was about 22%; no
  allocation failed. Treat pool exhaustion monitoring as an existing capacity
  warning, not proof that this project may consume unbounded storage.
- An unauthenticated Forgejo branch API probe from LXC 104 returned 404, proving
  the worker cannot safely obtain canonical base state by bypassing the broker.
  No credential was supplied and no state changed.

## Current checkpoint

M0–M1 are complete. M2 begins with a verified recovery checkpoint and isolated
worker installation. The next controlled operation is creation of a dedicated,
passphrase-protected producer signing key through a human-attended prompt; only
its public key enters the runner trust file. The private key must never be read
by the agent. A human-carried signed bundle is the bootstrap exchange until a
separate private immutable staging service is demonstrably available. Remote
Git writes remain subject to immediate explicit confirmation.

