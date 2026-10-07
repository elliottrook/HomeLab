# Delegation candidate — not connected to production

This is the D1 foundation for [Codex delegation](../../../docs/projects/AI%20Projects/Codex-Delegation.md).
It is not an Aster service, an intent classifier or a complete security boundary.

- `contract.py`: explicit intent routing and correlated final-answer events.
- `store.py`: durable dispatch claims; uncertain jobs cannot be claimed again.
- `probe.py`: explicit metadata-only installed Codex check, no inference methods.
- `session.py`: offline coordination of dispatch claims, acknowledgements, events
  and terminal persistence, including events arriving before acknowledgement.
- `isolation_probe.py`: metadata-only effective child configuration check. Tool
  feature and MCP disables affect only the owned child, not saved user settings.
- `transport.py` and `recovery.py`: bounded pipe deadlines and recovery from a
  matching complete thread snapshot, tested with local pipes and fixtures.
- `offline_tool_capture.py`: explicit offline diagnostic, runs a temporary
  loopback fake provider and a synthetic turn. Captures only tool names/counts
  and authorization-header presence, then returns an intentional HTTP error.
  No real model call. The installed build offered zero tools and no authorization.
- `pilot.py`: defaults to metadata-only manifest preparation. `--run` is reserved
  for the approved fictional D2 test; requires a matching manifest fingerprint
  and fresh absolute result directory. Not a deployed user-facing bridge.

Run offline checks from the repository root:

```sh
python3 -m unittest discover -s services/aster-agent/delegation -p 'test_*.py'
```

The metadata probe requires `--inspect-installed` to do anything. It uses the
existing supported Codex sign-in and prints no account address or credentials.
It may need host runtime permissions. It cannot start a thread or model turn.

## Deliberate limitations

The router accepts an already classified intent; it does not classify free text.
Cloud permission and capacity are caller inputs, not authorization grants.
No unqualified local model becomes an administrator by passing this router.

Job events and dispatch storage now have a coordinator and bounded pipe transport.
No production queue, access-controlled database deployment, retention
cleanup or Companion integration exists yet. Only a
single owner may orchestrate a job; the SQLite claim prevents repeated dispatch,
not every possible concurrency problem. Storage failures must prevent dispatch.

Only final-answer items with an explicit phase become answers after terminal
success. The installed protocol allows a null phase; this candidate abstains in
that case. It does not guess that commentary is final. The coordinator classifies
documented quota/authentication error codes without retaining error text.
Failed/unknown work is never auto-retried.

Rejecting client-directed tool/approval requests does not disable tools that
Codex executes internally. D2 requires independently verified effective tool and
context isolation before inference. Do not connect these primitives to a normal
fully privileged Codex session and call it a safe read-only pilot.

The pinned restriction profile passed an offline outgoing tool-inventory check.
This supports the bounded fictional test, not a general OS isolation claim.
Real HomeLab context and tool access remain later gates. Unknown dispatch lacking
a turn acknowledgement requires manual reconciliation; it cannot auto-retry.
