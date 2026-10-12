# M1 independent approval-ingress candidate — 2026-10-11

**Status: offline code and synthetic tests only; Stage2 HOLD.** No service,
reverse-proxy route, socket ACL, Unix account, Authentik flow, credential,
approval or grant changed.

## Hypothesis and boundary

The [live recheck](M1-live-approval-boundary-recheck-2026-10-11.md) confirmed
that the running approval service names `aster` as its accepted socket peer.
The present Aster process can supply actor and assurance metadata, so the
approval path cannot be called independent of AI-facing code. A small
dedicated ingress may remove that trust dependency **only if** it becomes a
separate process with its own UID, independently verified token claims and the
sole permitted approval-socket peer.

`services/aster-agent/approval_ingress.py` is a dormant FastAPI app factory,
not a listener or deployment package. It exposes only the existing Companion
approval routes by reusing `broker_approvals.py`; it has no chat, model,
gateway API-key or tool routes. For each request it verifies a signed RS256
token against an injected JWKS client and exact issuer/audience, requires
expiry and subject claims, rejects delegated `act` claims, and derives the
actor hash from issuer plus subject. It passes only that derived hash,
`auth_time`, and `acr` to the existing approval router. Client-supplied actor
or assurance fields remain forbidden by that router's request schemas.
Verifier failure returns the same generic 401 without logging token material.

The factory's subject allowlist defaults empty, and its passkey ACR mapping
defaults empty. The synthetic `synthetic-passkey` ACR in tests is **not** an
Authentik claim mapping. Ingress classification cannot grant approval: the
broker remains the deterministic decision point for entitlement, request
state, freshness, policy and at-most-once consumption.

## Test result and limits

Seven new synthetic ingress tests plus eleven existing approval-router tests
passed (18 total) using the repository-pinned PyJWT version and a temporary
local test environment. The tests use generated fixture RSA keys and a fake
JWKS client; they cover valid owner derivation, wrong signature/issuer/audience,
expiry/missing claims, delegated token, verifier outage, no API-key fallback,
forged actor fields, generic MFA versus an explicitly mapped fixture ACR,
unentitled/empty allowlists, invalid startup configuration and absence of
gateway routes. No real token, production JWKS, socket or network route was
used. The pinned PyJWT/crypto packages were installed only into the existing
disposable `/private/tmp` test environment; no HomeLab dependency changed.

A further **disposable end-to-end contract check** connected the candidate's
HTTP routes to an actual local Unix-socket broker backed by a temporary SQLite
database. With synthetic signed identities, it showed that a Yellow request
could be approved only with the exact payload hash and only once; a Red request
remained pending under generic MFA and stale fixture passkey assurance, then
accepted a fresh fixture passkey assertion. An unlisted subject, a simulated
wrong Unix peer UID and a missing broker socket could not approve anything;
the missing socket surfaced as HTTP 503. All 21 ingress/router/contract tests
passed. The fixture ACR is deliberately artificial, and the peer-UID test
simulates the broker's check in one process. This is stronger contract evidence
than isolated mocks, but **does not prove separate production UIDs, ACLs,
Authentik claims or reverse-proxy behavior**. No live AI-PAM request was made.

The tests prove the narrow Python and local-socket contract, **not** process isolation or
deployment safety. In particular, no live passkey-specific ACR has been
verified; no companion client has been routed to this app; no new UID/socket
ownership, broker full-stop behavior, availability or rollback has been tested.
The deployed broker `dispatch` lacks one branch in the repository candidate,
so an install plan must use its reconciled current method set rather than
blindly copying the whole tracked file.

## Promotion gate

Before deployment, independently verify a fresh real owner session's signed
passkey assurance **without exporting token contents**; otherwise keep
passkey mapping empty and privileged actions disabled. Prepare and test a
separate UID and approval service runtime directory, then prove `aster` cannot
connect while the verifier can. Check exact private same-origin proxy routing,
Companion compatibility, outage behavior, bounded latency/memory, broker
restart and full-stop independence, revocation/demotion, duplicate consumption,
audit, and the independent human SSH recovery path. Produce an exact
deployment/rollback manifest and obtain its own change approval. Do not
remove `aster` from the current socket group until the replacement path is
ready; do not claim Stage2 or connected Codex tools from this offline pass.
