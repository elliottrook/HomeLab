# M1 approval-ingress decision candidate — 2026-10-10

**Status:** architecture proposal for review; no identity, socket, route, unit,
credential, policy or broker change is authorized or deployed by this record.

## Problem and evidence class

**Verified repository state:** The approval service accepts only its configured
Unix peer UID, currently named `aster` in the committed systemd unit. It then
checks a subject-hash allowlist and freshness/assurance fields supplied in the
request. The Companion approval route derives these fields from validated
claims, but the Aster process is the socket peer and constructs the request.
See `broker_approval_service.py`, its service unit and `broker_approvals.py`.
The installed Authentik session has not been shown to emit a passkey-specific
claim; the Stage2 candidate therefore has an empty verified ACR mapping.

**Architectural inference:** If the broad Aster application process were
compromised, it could assert an entitled actor to the approval socket. The
socket allowlist limits ordinary callers but cannot distinguish that forged
assertion from a request the Aster process built after checking a real token.
This is incompatible with claiming that AI-facing code is outside the human
approval trust boundary. It does not prove that Aster is compromised or that an
approval has been forged.

**Live route reconciliation, 2026-10-10:** Nginx Proxy Manager's active
`aster.elliottrook.com` host forwards its default location to Aster LXC 104
at `192.168.70.10:9120`; no approval-specific location was present. The
Companion approval bridge source on LXC 104 matched the tracked file. This
confirms the present request path crosses Aster before the approval socket;
it does not establish any passkey-specific assurance claim. A separate
[socket-lifecycle incident](M1-approval-socket-lifecycle-2026-10-10.md)
temporarily made that listener unreachable. A narrow one-unit fix now preserves
the shared socket directory across a normal main-broker restart, with no policy
change. A deliberate full broker stop remains outside that proof.

## Options

| Option | Benefit | Cost / limit | Recommendation |
|---|---|---|---|
| Keep Aster as approval socket peer | No new process or route; current client shape retained | Aster still asserts actor and assurance; approving a new AI capability can share the AI-facing failure domain | Do not call this separated authority; do not graduate privileged Stage2 on this basis |
| Put a dedicated verifier/approval ingress in front of the existing socket | Companion's approval requests avoid Aster; broker can bind one small verifier UID | New same-origin route, unit, token-validation dependencies and recovery procedure need proof | Preferred candidate if in-app AI-PAM approvals remain a requirement |
| Keep privileged approval in a human-only operational ceremony | No new online approval service | Less usable; cannot claim normal Companion management is complete | Safe interim hold while the dedicated ingress is evaluated |

## Preferred candidate contract, not implementation

The existing private TLS ingress would route only
`/v1/companion/approvals/*` to a small verifier process on LXC 104. All other
Aster routes would remain with Aster. The verifier would independently check
token signature, issuer, audience, expiry and subject against operator-owned
configuration; it would derive actor and assurance from verified claims, never
from request JSON or proxy identity headers. Until a real passkey-specific
claim or dedicated step-up proof exists, Red and management would deny.

The verifier would have its own Unix UID. The approval socket would accept
that UID only; the `aster` UID and group access would be removed from this
socket. The broker would retain its own subject allowlist, policy checks,
freshness check, at-most-once consumption and audit. The verifier would own no
model, tool routing, credential store, or general shell capability. It would
forward only the existing allowlisted approval methods and bounded fields.
The app would keep the same public endpoint if compatibility is proven.

The same gate should give the approval service its own `RuntimeDirectory` and
socket pathname. Today its socket lives inside the execution broker's runtime
directory; that broker can remove the pathname on a full stop. The reviewed
restart fix deliberately did not couple the services with `PartOf=` because
approval-plane independence is a repository invariant. A new directory would
require exact consumer-path, unit-permission, restart, full-stop and recovery
tests. It should be implemented with the verifier/UID migration rather than
as a hidden amendment to the current unit.

This design adds one narrowly scoped security process, not another agent
harness. Aster can continue local household and chat functions if the approval
ingress fails; approval and management fail closed. Human break-glass remains
separate from the new service.

## Proof required before an adoption decision

1. Reconcile the actual reverse-proxy route, client URLs, live socket ACLs,
   service UID/group membership and installed source hashes. Repository paths
   alone do not prove current deployment.
2. Show a fresh real owner login yields a signed, session-derived
   passkey-specific assurance signal, or design an explicit step-up flow.
   Expose only claim names and boolean/classification results to this record;
   never copy tokens, cookies, keys or session contents.
3. In a disposable fixture, prove the `aster` UID cannot connect to the new
   approval socket; forged request actor/assurance fields, another owner,
   generic MFA, stale/future/boolean auth time, wrong issuer/audience,
   missing JWKS and provider outage all deny.
4. Prove the real Companion client still reaches approval views through the
   private same-origin route, while ordinary Aster chat and household paths
   continue during verifier failure. Measure latency and service memory.
5. Exercise pending/approve/deny/revoke, duplicate consumption, demotion,
   policy changes, restart, full execution-broker stop and audit in a synthetic broker fixture. Verify
   fail-closed recovery and the independent human SSH path before any rollout.
6. Produce a bounded deployment/rollback plan with exact files, units,
   route, checkpoints and stop conditions; obtain the required approval then.

**Decision now:** retain Stage2 HOLD. Do not add Codex/worker tool grants or
claim separated human authority from the present Aster-supplied actor metadata.
The dedicated-ingress option is a candidate to test, not an instruction to
install it. No B60, llama, Codex model call or live authentication was used in
preparing this record.
