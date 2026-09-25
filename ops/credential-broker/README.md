# HomeLab AI Access Broker

This directory contains the deny-by-default implementation artifacts for the
broader AI-PAM project in
`docs/projects/homelab-credential-broker.md`.

M2 deploys a **synthetic-only** broker service on LXC 104. It does not connect
to OpenBao, Forgejo or another production target and contains no credential.
The service accepts JSON requests only over a group-restricted Unix socket and
derives the caller identity from kernel peer credentials rather than a
caller-supplied identity field.

Implemented controls:

- SQLite-backed agent, service and capability registries;
- mandatory Probation state for every newly registered agent;
- explicit Green, Yellow, Red and Black risk classes;
- Black capabilities can never be delegated;
- canonical SHA-256 payload binding, bounded TTLs and one-time consumption;
- Yellow/Red approval state ready for the M3 Authentik approval path;
- agent suspension and global emergency disable revoke open requests;
- metadata-only audit rows containing hashes rather than request payloads;
- hardened systemd service with no TCP/IP socket capability; and
- the pre-existing Forgejo MCP response/argument safety adapter.

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
- `setup/install-m2-broker.sh` — idempotent synthetic deployment installer
- `mcp_policy_adapter.py` — deny-by-default Forgejo MCP boundary prototype
- `openbao-pilot-manifest.yaml` — completed M1 deployment/recovery record
