# credential-broker

Untested skeleton for a HomelabHero-style SSH credential broker: a
sudoers-narrowed script lets a low-privilege agent user run remote commands
via a separate vault-owning user, without the agent ever reading key
material. See ../../docs/projects/homelab-credential-broker.md for the full
project document, risk assessment, and Stream A authorization envelope.

The original `hb-connect`/sudoers skeleton is retained as historical design
input and is **not deployable**: it permits arbitrary remote command strings and
does not prevent the agent from invoking its `add` path.

The M0 safety prototype adds `mcp_policy_adapter.py`, a local,
dependency-free boundary for a pinned upstream Forgejo MCP. It exposes only an
explicit read-tool allowlist, requires an allowlisted repository, refuses
credential/environment arguments and sensitive paths, and rejects oversized or
secret-shaped output. It contains no live OpenBao/Forgejo client or credential.

Run its synthetic adversarial suite:

```sh
cd ops/credential-broker
python3 -m unittest -v test_mcp_policy_adapter.py
```

Layout:
  bin/hb              - operator/agent entrypoint (calls hb-connect via sudo)
  bin/hb-connect       - the broker itself; only this may run as the vault user
  setup/setup-vault.sh - one-time user/directory/sudoers installer
  setup/etc-sudoers.d-homelab-broker - the sudoers rule installed by the above
  mcp_policy_adapter.py - deny-by-default Forgejo MCP policy boundary
  test_mcp_policy_adapter.py - synthetic allow/deny and output-safety tests
  openbao-pilot-manifest.yaml - non-secret M1 candidate and recovery gates
