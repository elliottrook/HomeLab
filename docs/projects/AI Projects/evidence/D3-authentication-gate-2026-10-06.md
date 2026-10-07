# D3 — Worker authentication canary approval gate

## Current evidence

VERIFIED CURRENT STATE (read-only, October 6 Vancouver / October 7 UTC):
Authentik LXC 106 runs server and worker image `2026.8.0`. A metadata-only ORM
query found the existing `aster-companion` public client and no application
`aster-codex-worker` or user `aster-codex-worker-mac`. It retrieved no credentials.
The canary's read-only default executed inside the installed Authentik shell:
`candidate_names_available=true`, `signing_key_available=true`, `applied=false`.

VERIFIED LOCAL: 117 Python tests and five renderer scenarios pass. The new
worker identity dependency uses online introspection per request (no positive
cache), fixed HTTPS destination, no redirects/environment proxy inheritance,
bounded response size, exact issuer/client/audience/subject, worker scope and
maximum five-minute lifetime. Local kill-switch denial is checked before and
after introspection. Disabled integration makes no identity request. Credentials
and upstream error bodies are not returned to callers. Real secret custody and
AI-PAM kill-switch wiring remain prerequisites, not completed features.

New worker answer endpoint binds final text to the durable completion digest;
owner status projects that answer into the existing renderer's format. Tests use
an ASGI gateway plus simulated Authentik responses, including revocation and
outage. No new route is mounted in production. Remote cancellation and token
usage forwarding are still outstanding; the remote projection explicitly offers
no stop button and reports usage as unknown.

## Why this authentication method

PROPOSAL: use a separate confidential Authentik provider, explicit service
account and short-lived worker tokens. Use online introspection so the gateway
does not rely solely on a previously valid signed token after revocation.
Authentik documents both [service-account M2M token issuance and confidential
provider introspection](https://docs.goauthentik.io/add-secure-apps/providers/oauth2/machine_to_machine/).
Inspection of the installed `TokenIntrospectionView` confirms it computes active
from expiry/revocation and returns scope/client ID. The exact claim shape needed
by our verifier must still be proved by issuance on this installation.

This is a workload identity, not an AI-PAM permission grant. Job ownership,
approved request/scope, probation and execution controls remain separate. A
service account token must never replace a human approval or Codex sign-in.

## Exact approval requested: identity-only experiment

Approve one run of `services/aster-agent/delegation/authentik_canary.py` on
Authentik LXC 106 through its existing container's `ak shell`, with the explicit
global `ASTER_WORKER_AUTH_CANARY=True`. Reviewed source SHA-256:

`5bfb9774220086b4965fbfc11bcecfa86e5df444ca759d3de903c6ec42f3ca58`

The script refuses pre-existing candidate names. It creates only:

- service account `aster-codex-worker-mac`, without administrator/group grants;
- OAuth provider `Aster Codex Worker Canary`, client ID `aster-codex-worker`,
  confidential, client-credentials only, five-minute access-token lifetime;
- scope mapping `Aster Worker Canary Scope` for `aster.worker`;
- application `aster-codex-worker`, bound only to that service account;
- one app-password token `aster-worker-auth-canary`, expiring in ten minutes.

It reuses references to the existing signing key and authorization/invalidation
flows without altering those objects. New secrets remain in this source-local
process's memory. The test uses Django's request client against the installed
OAuth endpoints: issue one access token, introspect its claims, revoke it, prove
inactive. It prints only named boolean checks. This proves issuer behavior, not
Mac HTTPS connectivity or a deployed gateway.

Expected duration under one minute, review after three minutes if incomplete.
Do not forcibly interrupt cleanup simply to meet the estimate. A disconnected
shell requires read-only reconciliation of candidate objects before any retry.
No automatic rerun or silently corrected live experiment is authorized.

## Risk, rollback and custody

Risk is temporary identity/configuration creation in the live identity service,
plus normal authentication/audit events. No existing application/provider,
network rule, target permission or Aster service is changed. No model invocation,
private prompt egress, subscription charge, daemon installation or Git push.

The script's `finally` deletes only objects it created, in reverse dependency
order. Cleanup failure is explicitly reported. After execution, independently
verify all candidate names absent; retained Authentik audit events are expected
and must not be deleted. In abnormal termination, revoke/delete only the exact
new token, binding, application, provider, mapping and service account after
checking identity/provenance. The ten-minute app-password expiry and five-minute
access-token lifetime limit orphan credential duration; do not rely on expiry
as a substitute for cleanup.

No long-lived secret is placed in OpenBao, Mac Keychain, environment files or
Git by this experiment. A permanent deployment will require a separate AI-PAM
registry entry with named custody paths, rotation/revocation procedures and
actual global kill-switch integration. This finite source-local canary does not
authorize a static credential exception for a production worker.

Integration impacts: no new endpoint/service/IP/DNS/certificate/firewall,
Homepage tile, scheduled job, backup scope or monitoring target. Existing
Authentik audit and guest protection remain in place. Record sanitized result
and cleanup evidence in this programme; no wiki/runtime claim until deployed.

## Acceptance and resume

Every printed claim/revocation check must be true and all temporary objects
must be absent on independent recheck. A failure means investigate offline,
not weaken the verifier or broaden scopes. Preserve only boolean outcomes,
version, timing, code hash and non-secret errors.

Then continue local Mac transport, credential-custody/deployment preparation,
Companion wiring and stop/usage handling. The later deployment and fictional
Codex roundtrip need their own concrete approval. This gate grants neither.

The approval requirement comes from the governing project D3 credential and
deployment boundary and repository AGENTS.md's immediate confirmation rule for
remote changes. Local implementation and read-only preparation are complete for
this identity experiment; it is the next validation dependency.
