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

`services/aster-agent/approval_ingress_service.py` now supplies a **dormant
process factory** for a future separate service. It refuses startup if the
exact HTTPS issuer, audience, same-provider JWKS URL, absolute broker socket
path or explicit SHA-256 approver hash set is missing or malformed. Unlike the
library factory, this service factory has no environment switch for passkey
ACRs: it always leaves that mapping empty. A later passkey-capable release
would need an explicit review after real assurance proof. This module does not
bind a port, create a Unix identity, alter the broker peer or install a proxy
location.

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

Two further startup tests bring the focused suite to **23 passes**. They prove
the process factory rejects absent or mismatched settings before startup and
keeps `passkey_verified=false` even when a synthetic signed token carries the
fixture passkey ACR. The only positive ACR tests are on the underlying library
factory, not the production-shaped process factory. No real JWKS fetch was made.

The pinned PyJWT 2.14.0 source says its optional signing-key LRU has **no
time-based expiry**. The process factory therefore disables both that cache
and the JWKS-set cache, with a three-second fetch timeout. This makes issuer
unavailability deny approval requests rather than relying on a potentially
stale cached key. It also adds a network round-trip to each approval-view call;
latency, polling load and Authentik availability must be measured before
deployment. The existing Aster gateway's cache setting was not changed by
this candidate.
One read-only GET from LXC 104 to that provider's JWKS URL returned HTTP 200
in 0.412 seconds, with the response body discarded. This proves reachability
at that moment only; it is not a latency distribution, sustained-load test or
proof of issuer availability during an outage.

The tests prove the narrow Python and local-socket contract, **not** process isolation or
deployment safety. In particular, no live passkey-specific ACR has been
verified; no companion client has been routed to this app; no new UID/socket
ownership, broker full-stop behavior, availability or rollback has been tested.
The deployed broker `dispatch` lacks one branch in the repository candidate,
so an install plan must use its reconciled current method set rather than
blindly copying the whole tracked file.

## Promotion gate

A further read-only LXC 104 recheck after the startup-factory work found the
same live boundary: `aster` belongs to `hlabroker-approvers`; the approval
socket is `hlabroker:hlabroker-approvers` mode `0660` under the main broker's
mode-`0755` runtime directory. Both services report active. The main broker
retains `RuntimeDirectoryPreserve=restart`; the approval service owns no runtime
directory. No actor, approval content, credential or socket method was read or
called. The separate-process factory is therefore **not** a deployed authority
boundary and a full execution-broker stop remains unproven.

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

The safest proposed cutover accepts a **short approval outage** rather than a
period where both Aster and the new verifier can authorize. Stage the code,
account and private listener without routing traffic. Then stop only the
approval service, move its socket to an approval-owned runtime directory,
change its accepted peer UID and socket group to the dedicated verifier, and
restart it. Prove that `aster` is denied and the verifier can connect **before**
switching the private same-origin approval route. Finally remove Aster's stale
approver-group membership and restart Aster when safe so its live groups also
drop that privilege. If any check fails, keep approval mutations unavailable
and retain the human SSH recovery path; do **not** restore the old AI-facing
approver privilege merely to make the UI work. Aster chat and household paths
must remain healthy throughout. This ordering has not been tested or approved.

A read-only topology recheck found no `aster-approval` account, the current
`hlabroker-approvers` group still contains `aster`, and LXC 104 has no listener
on proposed private port 9121. Nginx Proxy Manager LXC 107's current
`aster.elliottrook.com` host still has `/voice/` and default `/` locations,
with default upstream `192.168.70.10:9120`; it has no approval-specific
location. These are observations, not proof that port 9121 is allowed through
the firewall or that NPM can route it. The original Companion rollout used a
narrow NPM `192.168.50.23` to Aster `192.168.70.10:9120` rule on the
Management interface, ahead of its RFC1918 block; a second port would need
its own compiled-ruleset and end-to-end check if adopted. This is a historical
precedent, not evidence that a 9121 rule exists. Exact UID, internal firewall rule,
listener address, NPM location, unit files, socket-directory ownership,
current Authentik claim shape and rollback checkpoints remain **UNKNOWN /
REQUIRES VERIFICATION** for an install manifest. The code and sequence are not
deployment authorization.

The first release, if chosen, would be **Yellow-only**: an explicitly entitled
signed owner could review and approve Yellow requests, while Red and management
mutations remain unavailable through Companion because the production-shaped
factory has no passkey mapping. This is a narrower usable service, not M1
Stage2 completion or permission to connect Codex tools. The user-visible loss
or preservation of any current Companion management workflow must be checked
before accepting that tradeoff.

**Value gate before adding infrastructure:** this option creates a new process,
Unix identity, private listener, firewall rule, proxy location and recovery
procedure. It should be adopted only if Companion Yellow approvals are an
actual useful workflow or the separated boundary is demonstrably necessary
for the first connected read-only role. Their real usage frequency and Jason's
tolerance for a brief approval outage are not established. If the need is
weak, retain the human-only operational ceremony and do not build a permanent
second approval service merely because the offline code passes tests. The
existing Aster-peer trust flaw must remain visible in that decision; it cannot
be described as resolved or used to justify tool grants.

**Aggregate value check, 2026-10-11:** a source-local projection of retained
NPM host-18 access logs emitted counts only, with no request IDs, addresses,
tokens, bodies or identities exported. The available files contained 18 POSTs
to an `/approve` path, three to `/deny`, and 22 other POSTs under the
approvals prefix. The approve requests were dated 25–27 September (15) and
10 October (3); no approval POST appeared in the current log after that. The
same logs had many GETs, which may include polling. These counts do **not**
establish successful approvals, distinct human actions or a complete
historical usage record. The dates overlap known setup/test work, so routine
need remains unproven. On this evidence, **defer the Yellow-only production
cutover** rather than add its process/firewall/proxy overhead now. Revisit only
if a real use case or connected-tool security gate justifies it and a full
deployment manifest is ready. Stage2 and connected tools remain HOLD.
