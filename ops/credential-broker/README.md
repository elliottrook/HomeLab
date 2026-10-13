# HomeLab AI Access Broker

This directory contains the deny-by-default implementation artifacts for the
broader AI-PAM project in
`docs/projects/completed projects/homelab-credential-broker.md`.

M2–M5 deploy the synthetic broker foundation on LXC 104. M6 adds separate
broker-private Forgejo MCP read and safe-write gateways whose credentials remain
in distinct OpenBao paths. The service accepts JSON requests only over a group-restricted Unix socket and
derives the caller identity from kernel peer credentials rather than a
caller-supplied identity field.

## Deployed status-read addition — 2026-10-06

The approval socket accepts exact `{"method":"automation.status"}` after its
configured kernel peer-UID check. It returns only `global_enabled`. No human
actor is needed for this one read; all management/approval methods retain actor
requirements. Extra fields do not select this branch. No group or switch change
accompanied deployment. The delegation callback remains a local candidate.
See [deployment and checkpoint evidence](../../docs/projects/AI%20Projects/evidence/D3-broker-deployment-result-2026-10-06.md).

## Main-broker restart lifecycle — 2026-10-10

LXC 104's main broker unit now uses `RuntimeDirectoryPreserve=restart`. One
normal main-broker restart preserved the independent approval service's PID
and reachable socket; permissions and the non-consuming status read passed.
The approval unit remains independent and unchanged. A full main-broker stop
can still remove their shared runtime directory, so this is a restart fix,
not proof of complete lifecycle separation. See the
[deployment evidence](../../docs/projects/AI%20Projects/evidence/M1-approval-socket-lifecycle-2026-10-10.md).

Implemented controls:

- SQLite-backed agent, service and capability registries;
- mandatory Probation state for every newly registered agent;
- explicit Green, Yellow, Red and Black risk classes;
- Black capabilities can never be delegated;
- canonical SHA-256 payload binding, bounded TTLs and one-time consumption;
- Yellow/Red approval through the existing passkey-only Aster Companion OIDC
  application and a separate approver-only Unix socket;
- Red fresh-auth enforcement (`auth_time` no older than 120 seconds), exact
  payload-hash binding, denial and replay protection;
- allowlisted non-secret approval summaries for the mobile inbox;
- agent suspension and global emergency disable revoke open requests;
- secret-free lifecycle, capability, service metadata, request history and
  audit views, with fresh-passkey agent/service/request/global revocation;
- metadata-only audit rows containing hashes rather than request payloads;
- hardened broker and gateway systemd services; and
- independent Forgejo MCP response/argument safety adapters. The Yellow adapter
  exposes only new-file creation from `main` onto a new `ai-pam/` branch beneath
  `ai-pam-pilot/`; update, delete, merge and direct default-branch writes remain
  unavailable.

The old SSH/sudo wrapper was removed during M2. It allowed arbitrary command
strings and was not a valid AI-PAM enforcement boundary; its history remains in
Git if design archaeology is needed.

Run all synthetic tests:

```sh
python3 -m unittest discover -s ops/credential-broker -p 'test_*.py' -v
```

Key files:

- `broker_core.py` — registries, policy, request lifecycle, audit and kill switch
- `broker_service.py` — kernel-identified Unix-socket transport
- `broker_client.py` — local JSON client
- `broker_admin.py` — root-only state administration
- `homelab-broker.service` — systemd confinement
- `broker_approval_service.py` — Aster-UID-only approval boundary
- `homelab-broker-approval.service` — separately confined approval unit
- `services/aster-agent/broker_approvals.py` — signed-identity Companion bridge
- `setup/install-m2-broker.sh` — idempotent synthetic deployment installer
- `mcp_policy_adapter.py` — deny-by-default Forgejo MCP boundary
- `forgejo_mcp_gateway.py` — broker-private gateway that retrieves the PAT from
  OpenBao and invokes the pinned MCP process
- `forgejo-mcp-gateway.service` — separately confined gateway unit
- `forgejo-mcp-write-gateway.service` — separate Unix identity/socket for the
  Yellow safe-branch credential and gateway
- `setup/install-m6-safe-write.sh` — fail-closed safe-write deployment after
  the distinct AppRole credential has been installed
- `openbao-m6-listener.hcl` / `openbao-m6-nftables.conf` — private TLS listener
  and broker-only ingress policy
- `openbao-pilot-manifest.yaml` — completed M1 deployment/recovery record
- `bundle_verifier.py` — signed, one-file, canary-only bundle verification and
  durable replay state; no network or target-service access
- `bundle_runner.py` — joins a verified bundle to the existing Yellow
  `forgejo.write.safe-branch` request without any approval capability
- `bundle_reader.py` — requests bounded Green repository reads through the
  broker for fixed repository `jason/homelab`; it holds no Forgejo credential

The pull-based Forgejo bundle runner completed its canary/recovery write acceptance. Jason
promoted only `agent-cloud-bundle` through the existing Companion fresh-passkey
management flow after M2 isolation passed. The identity has only the existing
Yellow `forgejo.write.safe-branch` and Green `forgejo.read.repository`
capabilities, and its `hlabundle` Unix account
cannot connect directly to either Forgejo gateway socket. Only the public
producer key is present on LXC 104; the passphrase-protected private key remains
on Jason's Mac. See
`docs/projects/Pull-Based-Forgejo-Runner.md` for current gates and evidence.
Hourly metadata-only health is provided by `homelab-bundle-health.timer`; the
operator procedure is `docs/runbooks/Pull-Based-Forgejo-Runner.md`.

The Green reader permits only `get_repo`, `list_branches`, `get_file_content`,
`list_repo_contents`, `get_repo_tree` and `list_repo_commits`. The independent
gateway still enforces the fixed repository, sensitive-path, credential-shaped
argument, secret-shaped output and size limits. Installation, 112/112 Linux
tests and live allow/deny isolation probes passed.


## Aster M1 deployment split (2026-09-25)

The deployed Stage1 Aster Adaptive Computing core requires authenticated `agent_id`
at consume, rechecks a versioned policy digest, invalidates authorizations on
lifecycle changes, and serializes SQLite checks/transitions and schema migration.
Legacy requests without a policy digest are denied; create new requests after a
coordinated release. Bump `AUTHORIZATION_POLICY_VERSION` for changes to policy
semantics so pending plans cannot inherit new rules silently.

The **local-only Stage2 candidate** approval transport requires `actor` on reads as well as mutations, an explicit
`--approver-subject-hash` allowlist, and the existing configured peer UID.
Companion requires matching `ASTER_BROKER_APPROVER_SUBJECT_HASHES` (comma-separated)
and only maps verified claims to passkey using explicitly configured
`ASTER_BROKER_PASSKEY_ACRS`. Empty configuration fails closed. No production
subject/ACR has been chosen or configured by this candidate. Existing unit files
are not a ready-to-deploy configuration for the new approval service.

See [M1 candidate evidence](../../docs/projects/AI%20Projects/evidence/M1-authority-candidate.md)
for validation, M6 compatibility, identity/recovery/deployment gates and the
at-most-once authorization limit. Only core and broker transport are deployed;
the approval service and Companion retain their prior implementations. Installed
Authentik claims have not yet established a verified passkey-specific assurance
mapping; do not treat generic ACR/MFA as that proof. Full M1 remains open.

[Stage1 deployment evidence](../../docs/projects/AI%20Projects/evidence/M1-stage1-deployment.md)
records exact hashes, protected checkpoint, startup-readiness recovery and live
validation. The release installer is an execution record, not an idempotent
redeployment command. Do not restore an older database or restart old core code
as a casual rollback: that may restore consumed approvals or weaken controls.
