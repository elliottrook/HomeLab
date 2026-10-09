# D3 — supervised session and completed-answer recovery design

Status: ATOMIC ADMISSION AND OWNER-REQUESTED ANSWER RECOVERY CANDIDATES TESTED OFFLINE. No new authority, content retention or live deployment.
Owner: Jason. Revisit after fixture evidence.

## Current proven facts

- One native, user-reviewed request completed through the subscription-backed,
  no-tools worker; Jason saw the answer. The identity was disabled afterward.
- Native submissions are now closed. An authenticated status route reports that
  fact; it does not claim worker readiness. The 44-route gateway is healthy.
- `RequestIntake` holds reviewed text only in memory for at most 240 seconds and
  creates a durable queued envelope. `Gateway.offer` can hand off a queued job
  only once within its window; expired unoffered work is not replayed.
- `WorkerSession` reads the Mac Keychain during a supervised bootstrap and keeps
  one short-lived token in memory without renewal. `connected_worker.py` handles
  one bound job, then exits. Current Authentik worker identity is inactive.
- Gateway answers are memory-only for 15 minutes. The SQLite ledger keeps the
  completed state and answer digest, but not the answer text. The Mac worker
  dispatch store records job/thread/turn identity; Codex threads were created
  with `ephemeral=False`. `recovery.py` parses an explicit full thread snapshot,
  but there is no approved live owner-facing answer-recovery workflow.

These are source and accepted-run facts, not a reliability sample. A single
successful session cannot establish routine availability or correctness.

## Decision: separate readiness, intake, execution and recovery

Aster should have four distinct facts, each with a source and expiry:

| Fact | Authoritative source | Consequence |
|---|---|---|
| Owner authenticated | Existing Companion/OIDC dependency | May view own status and request a session |
| Worker ready for one approved no-tools plan | Fresh broker-validated worker assertion, bound to identity and model | May admit reviewed text during a short session window |
| Job accepted/running/terminal | Existing gateway and worker ledgers | Never infer cancellation or safe retry from a lost connection |
| Answer available | Bound verified answer/digest, or narrowly recovered original turn | May display content to that owner only |

The current `submission_enabled` switch is an administrator configuration flag,
not evidence that the Mac is awake, Codex is reachable, the worker is authenticated
or subscription capacity exists. It must not be presented as such. A future session
lease is an admission prerequisite, not a credential, permission grant or guarantee
that the model will succeed. The policy/broker still authorizes each action.

### Proposed supervised session contract

1. Jason starts a supervised session in Companion. The Mac-side component performs
   local Codex/account/model preflight without inference and presents its exact
   scope: owner, one model, no tools, no history, maximum duration and answer
   retention. It may request a Keychain Allow-once prompt. App-initiated process
   launch and worker-identity activation require a separate reviewed design;
   current code has neither. Never place Keychain secrets in Aster/gateway.
2. Only the authenticated worker may assert readiness. Gateway verifies its token
   online and requires a pre-approved plan fingerprint. A lease record binds
   owner, worker subject, model, scope digest, nonce, and server-side expiry.
   The lease lifetime must be no longer than remaining worker token validity and
   the configured supervised window; the client cannot set either bound. A
   heartbeat may report liveness but cannot extend credential validity or scope.
3. The native app permits Send only after both owner authentication and a fresh
   eligible lease. Aster must revalidate the lease atomically when creating the
   queued job; UI readiness alone is advisory. One lease admits at most one
   assignment during the first experiment. Closing/expiry blocks new admission.
4. The worker consumes only the exact owner-reviewed job; it compares model,
   scope, text digest and delivery ID before Codex creates a thread. Its durable
   inbox prevents duplicate model turns. If the connection or process disappears
   after offer, the job is uncertain until reconciled. Lease expiry does not mark
   an offered/running turn stopped or authorize replay.
5. A session-close action disables new intake immediately, revokes the bounded
   worker identity as authorized, and reports terminal or uncertain jobs
   separately. Closing the UI is not equivalent to stopping a model turn.

The first implementation should retain operator-started worker activation while
proving the lease protocol with synthetic jobs. Only then evaluate a Mac helper
or LaunchAgent for a user-operated Start Session action. Avoid an always-on Mac
agent until its custody, sleep/reconnect and revocation behavior is measured.

### Minimal fixture experiment and gates

Use a fake clock, identity verifier, gateway ledger and fake worker. No Keychain,
AuthToken, Codex or live service is needed. Test: authenticated owner alone cannot
open; worker assertion wrong identity/model/scope fails; lease expiry and Mac sleep
close admission; near-expiry token cannot create a longer lease; restart loses any
volatile readiness and does not requeue jobs; a heartbeat cannot extend authority;
one lease cannot admit two jobs; offline status says unavailable; a work-in-progress
turn remains uncertain after lease loss. Instrument admitted, denied, expired and
uncertain counts. Reject the design if these cannot be made deterministic without
adding another privileged daemon or substantial new custody burden.

After fixture pass, one bounded live trial may compare the current manual
four-minute race to a session-open-then-send flow. Acceptance is Jason sending
one reviewed public question after readiness, with no operator racing the expiry,
no new credential copies, exactly one model turn, explicit closure and full
cleanup. No general availability claim from one trial.

## Completed-answer recovery: compare two bounded routes

**Option A — read the known Codex turn.** The Mac worker already stores job,
thread and turn identifiers, and `recovery.py` can parse a supplied full snapshot.
A recovery request must identify the authenticated owner and one completed job;
no browse/list endpoint. The worker reads only that exact thread and turn with its
existing subscription authentication, extracts only the final answer, verifies
its SHA-256 against the gateway's durable completion digest, and returns the answer
through the owner-scoped gateway. It must not start a new turn, silently include
history in a future prompt, or expose hidden reasoning. The Codex history source
may be unavailable, changed or deleted; those are typed recovery failures. A
fresh worker credential and explicit access to the old thread are still needed.
Current source does not prove a live `thread/read` call or retention guarantee.

**Option B — short encrypted answer retention.** Encrypt the final answer before
writing durable storage, bind owner/job/digest, enforce a short explicit expiry,
and test backup/restore and purge. This improves immediate display after Aster
restart but creates a new sensitive-content store, key lifecycle and cleanup
obligation. Existing OpenBao custody is not an automatic authorization to add
this store. A user-visible retention choice and separate risk decision would be
required. It does not solve uncertain model execution by itself.

Recommendation: fixture-test Option A first because it reuses existing turn
identity and does not add an Aster content store. Do not deploy recovery until
live protocol compatibility, exact-turn binding, owner isolation and digest
verification are demonstrated. If these fail or routine access requires repeated
intrusive authentication, revisit Option B as an explicit privacy tradeoff.

### Recovery fixture criteria

Create synthetic completed and uncertain jobs with separate owner bindings.
Supply full snapshots for exact match, wrong thread, wrong turn, duplicate turn,
missing final item, altered answer, incomplete item view, provider failure and
revoked authorization. Require exact job/thread/turn/digest match; any mismatch
returns no answer. A completed answer may be re-delivered without inference only
when the digest matches. An uncertain job may be reconciled to a verified terminal
state, but never retried automatically. No raw fixture payload goes to logs.

## Approval boundaries and unresolved choices

Local fixture work is within Stream A. Production session opening, Mac helper
installation, worker activation, live `thread/read`, content retention and any
credential renewal each need a concrete risk gate before execution. Existing
one-turn approval is consumed. The offline lease and exact-turn recovery contracts are prototyped. Next is an atomic gateway admission design and a bounded owner-facing recovery
transport. A decision record will then choose the smallest deployable workflow. Do not repeat Orion or use a real user
question merely to test the protocol.

## Offline admission prototype result

`services/aster-agent/delegation/admission_window.py` and its fixture tests now
implement only the volatile decision contract. It binds owner, worker, model,
plan digest and token deadline; caps the window at 240 seconds; requires a fresh
heartbeat; admits one job; refuses a second session until explicit closure and
reconciliation; and loses readiness on restart. Heartbeat does not extend the
credential or lease deadline. The full delegation suite passed 257 tests.

This prototype intentionally has no authenticated transport, persistent lease,
Mac process control or production integration. It is **not** an authority source.
A future gateway must obtain worker identity and token expiry from verified
transport, and consume the lease in the same SQLite transaction that creates the
durable queued job. Without that atomicity, a crash or competing request can
create an inconsistent admission. Live integration is a no-go until this is
implemented and tested. The current native flow remains closed.

## Offline exact-turn recovery prototype result

`services/aster-agent/delegation/verified_recovery.py` now wraps the existing
reconciliation parser for a completed job. It requires the authenticated owner
to own the durable job, a known thread and turn, one complete matching snapshot,
and a final-answer SHA-256 matching the gateway's completed digest. It returns no
answer on a wrong owner, wrong/duplicate turn, partial view, missing/tampered
final item or failed turn. It does not launch Codex, read local history or create
a new gateway route. The full delegation suite passed 261 tests with synthetic
content. The digest must be supplied by the gateway's owner-scoped ledger, never
from the user's request body.

The in-process gate passed; live protocol compatibility was then tested only
with the pre-existing fictional Orion turn. No personal request was read. Do not
connect recovery to the owner UI until owner-scoped transport, broker policy and
credential lifecycle are demonstrated. A single stored turn does not establish
retention guarantees or availability for arbitrary future turns.

## Exact stored-turn compatibility result

Official [Codex App Server documentation](https://learn.chatgpt.com/docs/app-server)
identifies `thread/read` with `includeTurns: true` as a stored-thread read that
does not resume the thread. A scoped local check used only the previously
accepted fictional Orion thread/turn IDs from the private dispatch ledger. The
installed app-server returned that exact turn. `recover_completed` verified the
owner/job/thread/turn and calculated a final-answer SHA-256 equal to the
gateway's durable completion digest. The script printed only boolean results:
exact read true, verified turn true, digest match true, inference false, answer
printed false. No Keychain worker read, Authentik activation, new turn or gateway
write occurred.

This establishes a feasible recovery primitive for one retained fictional turn,
not an owner-facing recovery service. Current app-server local history may be
removed independently; repeat access is not guaranteed. A future worker must
read only the bound turn under an authenticated owner request and reveal the
final answer only after comparing the gateway digest. The original worker
identity is inactive, so an operational recovery path still requires a deliberate
credential and authorization design.

## Atomic gateway admission result — 2026-10-08

The earlier in-memory `admission_window.py` prototype exposed the intended
behavior but would have created a second source of truth. Its behavior was
absorbed into the existing `Gateway` SQLite ledger; the duplicate module and
its five tests were removed, with their Git history retained.

`Gateway.open_session` records a single owner/worker/model/plan-bound session,
server expiry and process epoch. It requires a token expiry supplied by a future
verified transport, reserves a ten-second margin and caps the session at four
minutes. A heartbeat can establish freshness but cannot extend the expiry. A
gateway restart changes the process epoch and makes prior readiness unusable.

`Gateway.create_in_session` now consumes that exact ready session and inserts
the durable queued job in **one SQLite transaction**. Capacity or duplicate-job
failure rolls both effects back. The session admits only one job. Wrong owner,
worker, model, scope, digest, stale heartbeat, near-expiry credential and
restarted-process epoch all fail closed. Closing an admitted session requires
its job to have a terminal ledger state; an offered/running/unknown job cannot
be silently discarded to start another session. A separate explicit recovery
decision will be needed if such a job cannot be reconciled.

The full backend suite passed 264 tests, including synthetic restart, capacity
rollback, duplicate ID, stale/invalid token time, scope mismatch, and a pending
turn blocking the next session. These tests establish local transaction behavior,
not authentication. No route invokes these new methods yet. Live adoption still
requires: verified worker identity and token expiry from Authentik/broker, a
policy-approved fixed plan, owner-scoped request admission, and a way for the Mac
worker to maintain a fresh session without copying credentials into Aster. The
existing owner request route remains closed. Do not deploy this schema change
just to expose a session control before its transport and recovery path are ready.

## Owner-requested recovery ticket and transport candidate

The gateway now has a local-only ticket contract: an authenticated owner can
request one four-minute recovery ticket for a completed job whose temporary
answer is unavailable. The assigned worker may claim it once; a lost claim
remains uncertain and is not automatically reissued. Delivery is accepted only
for the original worker and exact durable completion digest. Answer text remains
volatile. A completed ticket can redeliver the same verified answer after a
restart during its original lifetime. The candidate has no model dispatch path.

An unattached `recovery_router` separates owner request/status from worker
claim/answer. Its disabled mode mounts no routes. `WorkerClient` has bounded
client calls to the fixed recovery path; `recovery_execution.py` reads only a
known thread ID and compares local owner/job/turn plus the gateway digest before
returning text. Synthetic ASGI and client integration checks cover owner/worker
isolation, wrong digest, one-time claim, expiry, restart and no duplicate job.
Full backend suite: 279 passed.

At this checkpoint it was **not** deployed or connected to native UI. Worker identity and
subscription authentication are still inactive in production. A future live
trial must freeze the exact original fictional job/ticket/digest and runner
binary, use one supervised credential bootstrap, verify no inference, have Jason
request recovery explicitly, clean up the worker immediately, and close recovery
routes after acceptance. No existing one-turn approval covers that trial.

## Local recovery integration candidate — 2026-10-08

The gateway assembly now mounts recovery routes only under a separate strict
`ASTER_DELEGATION_RECOVERY_ENABLED=1` flag. Closed request intake remains closed.
Capabilities explicitly advertise whether the recovery control is available.
Native Companion build 8 shows **Recover original answer** only for a completed
job with missing volatile answer when that flag is advertised. It creates one
ticket on a user click, stores only ticket/job identifiers for reconciliation,
polls owner-scoped status and never automatically resends a failed/uncertain
request. It does not promise worker readiness.

`supervised_answer_recovery.py` is an operator-started, single-ticket Mac
candidate. Preparation verifies ChatGPT account, effective no-tools/no-MCP
configuration, Codex binary, source hashes and the existing private completed
dispatch record without a model call. Run mode requires that exact preparation
hash and a fresh ticket. Its Codex client allows only metadata and
`thread/read`; the dispatch database is opened read-only and immutable. The
original owner, job, thread, turn and gateway completion digest must all match
before the answer is returned. It never prints the answer, accesses the
Keychain during preparation, retries a claim or starts a new turn. A failed or
lost claim is uncertain and needs operator reconciliation.

Offline results: 282 backend tests and 35 native tests pass. A composed ASGI
test verifies recovery while new requests remain closed. Signed native build 8
is packaged locally but neither installed nor registered. Read-only live
  checks found the gateway active and the fictional Orion completion digest still
present. Metadata-only Mac preflight passed with ChatGPT authentication and
zero enabled MCP servers. The current local manifest hash is recorded in the
bounded gate; it is not an execution grant.

The [bounded recovery gate](D3-answer-recovery-gate-2026-10-08.md) records
exact deployment scope, human click/worker timing, validation and rollback.
No gateway file, native app, worker identity, Keychain item or Codex history was
changed during this preparation. Live recovery requires fresh explicit approval.
