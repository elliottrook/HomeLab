# D3 — supervised session and completed-answer recovery design

Status: DESIGN CANDIDATE. No new authority, content retention or live deployment.
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
one-turn approval is consumed. The next implementation step is the offline lease
contract and recovery fixtures, followed by a decision record choosing the
smallest deployable session workflow. Do not repeat Orion or use a real user
question merely to test the protocol.
