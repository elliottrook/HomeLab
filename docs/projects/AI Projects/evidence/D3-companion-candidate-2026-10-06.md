# D2 telemetry / D3 Companion candidate — local evidence

## Implemented locally

Usage processing follows the installed `ThreadTokenUsageUpdatedNotification`
schema: exact thread/turn correlation, last/total numeric snapshots, no arbitrary
payload storage. Missing or malformed usage remains unknown. Repeated snapshots
are not summed. Token figures do not estimate a monetary charge or remaining
subscription allowance. Numeric usage is persisted separately from job identity.

Owner binding occurs when a job is claimed. Legacy unowned records remain
inaccessible to Companion. Owner-scoped queries use the existing gateway's
intended verified owner hash, not browser-supplied identity. The unregistered
router factory exposes only status and a bound stop request; it has no dispatch
or retry endpoint and is disabled by default through its service facade.

Stop requested is distinct from stopped. A lost connection persists uncertainty;
a stored running row without a matching live session is presented as unknown.
Repeated stop requests are not resent. Completed jobs lacking an in-memory reply
retain completion and request recovery instead of claiming failure or resubmitting.
The renderer uses textContent for the faithful answer; HTML in an answer is not
executed. It stores no token or answer in browser storage and performs no fetch.

## Repository integration finding

Existing `companion_notifications.py` changes pending jobs to failed on startup
and keeps replies in memory. Its browser client invites resending failed jobs.
That behavior cannot safely represent uncertain Codex execution. The existing
notification implementation was not modified; delegation has a separate status
contract and must not enter that legacy retry path.

`aster_agent.py` provides `companion_owner`, derived from authenticated Authentik
claims and rejecting delegated actor tokens. The future router must be attached
using that existing dependency. No router or renderer is mounted in live Aster
or its main application candidate yet; network bridging remains a separate gate.

## Validation

- **71 Python tests passed**, including seven HTTP tests with fixture identities
  and a legacy-schema migration check that preserves records without granting ownership.
- **Five Node renderer scenarios passed**, including literal HTML, unknown status,
  stop request/transport failure and usage labelling.
- The HTTP tests cover unauthenticated rejection, cross-owner read/cancel denial,
  disabled service, no-store replies, no dispatch endpoint, cancellation
  acknowledgement, duplicate clicks and uncertain transport outcomes.
- Existing real D2 result remains unchanged: 5.509-second subscription turn and
  identical recovered answer. Its token usage is still UNKNOWN; new fixture
  coverage cannot retroactively supply a missing measurement.

Used a disposable Python 3.11 environment under `/private/tmp`, with existing
repository pins FastAPI 0.133.1, httpx 0.28.1 and Pydantic 2.13.4. Initial Python
3.9 preparation could not resolve the pinned FastAPI; switched to already
installed Python 3.11 without changing pins or the system interpreter. Resolved
transitives included Starlette 1.7.0 and AnyIO 4.15.1. This is not a deployment
lockfile or proof of the production environment. No production packages changed.

## Remaining work and resume

The new HTTP tests verify the authentication dependency boundary with fixtures,
not a live Authentik sign-in. The renderer is a local candidate, not an integrated
or visually validated Companion screen. Live Codex cancellation is still untested.
No new cloud request, secret access, service deployment or Git push occurred.

Next: reconcile gateway/bridge placement and the existing Companion delivery path
read-only; wire a disabled local integration with single-worker lifecycle and
protected state/retention; test startup recovery and local-function independence.
Prepare the exact deployment and connected cancellation/usage canary only after
that engineering work. The prior D2 manifest remains historical and will reject
the changed source files. Do not reuse its consumed approval.
