# D3 authentication result and Mac HTTPS gate

## Approved source-local test — complete

Jason approved the identity-only experiment in this chat. The exact historical
canary SHA-256 `5bfb9774220086b4965fbfc11bcecfa86e5df444ca759d3de903c6ec42f3ca58`
was verified before execution from commit `7f8ac60`. One run exited zero in
8.4 seconds (SSH/tool elapsed, not an authentication benchmark).

VERIFIED CURRENT STATE: all nine checks passed: active token, issuer, audience,
client ID, subject present, worker scope, bounded lifetime, revocation response,
revoked token denied. The script reported temporary objects removed. An
independent SSH/ORM query confirmed the application, both candidate provider
selectors, service account, app-password token and scope mapping were absent.
The existing Companion provider remained public with its original one-hour
access-token lifetime. Existing audit events were retained. No credentials were
printed to the chat or saved in this repository. No inference or Aster deployment.

This consumed the approval. Its source remains in Git history; the current
canary adds an injectable HTTP client for the next separately gated test.

## Local continuation — verified

Added an outbound-only `WorkerClient` for the existing private Aster HTTPS
hostname: fixed destination and paths, bounded IDs/responses/deadline, disabled
by default, no redirects, environment proxies or retries. It supplies no model
execution and has no credential-discovery behavior. HTTP fixture integration
passes from worker through identity checks, gateway receipt/answer routes and
owner retrieval. Revocation, bad IDs, unavailable credentials, oversized/malformed
responses and upstream errors fail closed without returning secret diagnostics.

125 Python tests plus five renderer scenarios pass. All HTTP integration
fixtures still use simulated transport; no gateway router has been deployed.
The scope/model restriction and dispatch ledgers remain the separate execution
boundary. Worker authentication alone does not authorize a task.

## Next approval: finite Mac HTTPS identity test

PROPOSAL: repeat only the temporary identity lifecycle from the previous gate,
but relay its four OAuth requests through the Mac over real TLS to the fixed
host `auth.elliottrook.com`. This validates the network path needed by the future
worker. It does not yet prove a deployed Aster worker endpoint.

Reviewed executable: `services/aster-agent/delegation/authentik_network_canary.py`.
Its metadata-only preparation produced the two-source manifest fingerprint:

`271d47526c56750d1ef18c9274c2df1405830c08224170e6146ae26514e1db3c`

Run with the existing disposable Python environment:

```text
/private/tmp/aster-delegation-gateway-py311-20261006/bin/python services/aster-agent/delegation/authentik_network_canary.py --run --approved-sha256 271d47526c56750d1ef18c9274c2df1405830c08224170e6146ae26514e1db3c
```

The controller checks both source hashes before launching SSH. The source-local
helper creates exactly the same bounded temporary objects named in the prior
[authentication gate](D3-authentication-gate-2026-10-06.md). Secrets are generated
there and passed only through the controller-owned SSH pipe into Mac process
memory. The controller sends them to Authentik over normal certificate-validated
HTTPS, never to Codex, a model, arbitrary endpoints, files, environment variables
or user-visible output. The exact allowed paths are token issuance, introspection
and revocation. At most four requests: issue, inspect, revoke, inspect again.

This explicitly authorizes temporary credential handling on the trusted Mac for
this test only, not permanent credential copying or a production custody
exception. No OpenBao/Keychain write, new permission grant, firewall/DNS change,
running Aster change, model invocation or Git push is included.

Expected duration under one minute; controller observation bound 120 seconds
plus cleanup grace. A missing result/SSH loss is uncertain and requires remote
object reconciliation, never automatic rerun. Source-local `finally` deletes
created objects; controller closes stdin on failure to permit cleanup. Abrupt
process/host loss can still leave objects, so independently repeat the prior
metadata cleanup query. Expiring credentials are an additional bound, not the
cleanup strategy. Retain existing audit events.

Success requires four HTTPS requests, all nine booleans true, helper cleanup true
and independent object-absence verification. Failure does not permit relaxing
certificate validation, widening scopes, retrying issuance, or modifying the
test without another review.

## Resume

This is the current approval gate. Do not repeat the consumed source-local
approval. After a successful network test, continue the production custody and
AI-PAM kill-switch integration, remote cancellation/usage and actual Companion
deployment preparation. D3 is not yet complete, and D4 remains unstarted.
