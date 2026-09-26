# HomeLab AI Access Broker

This directory contains the deny-by-default implementation artifacts for the
broader AI-PAM project in
`docs/projects/homelab-credential-broker.md`.

M2–M5 deploy the synthetic broker foundation on LXC 104. M6 adds separate
broker-private Forgejo MCP read and safe-write gateways whose credentials remain
in distinct OpenBao paths. The service accepts JSON requests only over a group-restricted Unix socket and
derives the caller identity from kernel peer credentials rather than a
caller-supplied identity field.

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


## Adaptive foundation candidate — not deployed

The local M1 candidate requires `agent_id` on core consumption and an explicit
`actor` on approvals. Transport identity remains kernel-derived. Policy changes
invalidate old requests; checks, claims and audit commit atomically. At-most-one
claim does not establish an external effect completed: reconcile uncertain outcomes.

Approval and management socket requests now all require an enrolled hashed human
subject. Operator-only `broker_admin.py approver-enable --subject-hash HASH` and
`approver-disable --subject-hash HASH` manage that allowlist; no socket can enroll
an approver. The allowlist starts empty and revocation invalidates that approver's
outstanding grants. Do not infer enrollment from ordinary Companion authentication.

This candidate requires a compatible core/transport/Companion deployment, independent
security review, verified human identity and migration/recovery planning. The Aster
process remains trusted to assert human identity/assurance; this residual trust must
be resolved or explicitly accepted before expansion. No deployment occurred here.
See [M1 evidence and rollout gate](../../docs/projects/AI%20Projects/evidence/M1-local-authority-candidate.md).
