# HomeLab AI Access Broker

This directory contains the deny-by-default implementation artifacts for the
broader AI-PAM project in
`docs/projects/homelab-credential-broker.md`.

M2–M5 deploy the synthetic broker foundation on LXC 104. M6 adds a
broker-private Forgejo MCP gateway whose repository-read credential remains in
OpenBao. The service accepts JSON requests only over a group-restricted Unix socket and
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
- an independent Forgejo MCP response/argument safety adapter.

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
- `openbao-m6-listener.hcl` / `openbao-m6-nftables.conf` — private TLS listener
  and broker-only ingress policy
- `openbao-pilot-manifest.yaml` — completed M1 deployment/recovery record
