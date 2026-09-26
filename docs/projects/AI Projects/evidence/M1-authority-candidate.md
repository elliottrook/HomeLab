# M1 — local authority-boundary candidate

Date: 2026-09-25. Owner: Jason. State: **local candidate; not deployed; M1 remains open**.
Base: `d954ae4e6d81cfde52e04a99f7768ff3919deb00`. Scope: broker core/transport, approval socket, Companion approval bridge, synthetic regressions. No production access, real identity selection, credential access, provider call or dependency installation occurred in this work package.

## Verified candidate behavior

- `consume_request` requires an authenticated `agent_id`; the Unix transport supplies its kernel-derived identity. Request JSON cannot replace it. Wrong-caller denial leaves the owner's request usable.
- Creation, approval and consumption use the same current capability/grant/agent/service checks. A versioned policy digest includes lifecycle state, capability risk/probation/enabled state, service identity/mode/enabled state and grant presence. Missing legacy digests fail closed; they are never backfilled to retroactively authorize old requests.
- Lifecycle transitions revoke pending/approved work. Demotion followed by promotion cannot resurrect an approval. A no-op state assignment does not invalidate work except suspended/retired states remain restrictive.
- SQLite `BEGIN IMMEDIATE` serializes policy checks and writes across connections, with an `RLock` protecting a shared connection. The consume transition and audit row commit together. A synthetic audit failure rolls back consumption. One of eight simultaneous consumers succeeds; seven are denied.
- Migration holds the database write reservation across schema checks and additions. Eight concurrent starts against a legacy fixture migrate successfully and continue denying unbound legacy requests.
- Approval/revocation races cannot restore revoked work. Expiry remains terminal across denial and restart. An isolated SQLite backup/restore retains consumed-request replay denial.
- Companion approval routes require an explicitly configured subject-hash allowlist. The approval socket independently enforces the configured actor allowlist plus its existing peer-UID check. Empty allowlists deny access, including management reads.
- The bridge no longer asserts passkey assurance merely because a user authenticated. Only an exact, operator-configured ACR value from verified claims maps to passkey. Generic MFA, missing/unknown ACR and malformed ACR do not. A missing authentication timestamp remains acceptable for Yellow but cannot authorize Red/management.

These are synthetic local results, not proof of deployed controls or a complete security audit. The model-facing Aster process remains in the approval trust base; a compromised trusted bridge can assert an allowed actor. This candidate does not establish process-level independence from that bridge.

## Validation

```text
python3 -m unittest discover -s ops/credential-broker -p 'test_*.py'
55 tests passed; no expected failures.

/private/tmp/aster-lab-ops-venv/bin/python -m unittest discover -s services/aster-agent -p 'test_*.py'
163 tests passed (including 10 approval-bridge tests).
```

Broker tests use Python 3.9 on this Mac. Aster tests reused the existing Python 3.12.14 environment: FastAPI 0.133.1, Pydantic 2.13.4, HTTPX 0.28.1, Starlette 1.7.0. Starlette emits an HTTPX test-client deprecation warning; no packages were changed. Initial attempts using system/bundled Python could not import FastAPI; these were environment failures, not passing tests.

Baseline was reproduced before edits: 38 tests, 36 passes and two expected failures. Removing the expected-failure markers accompanied the verified fixes. Added tests cover caller spoofing, lifecycle resurrection, policy drift, policy-code changes, audit failure, concurrency, restart, expiry, restore, migration and approver/assurance denial.

Independent review: the existing AI-PAM Stream A task reviewed the local diff read-only. It found and reproduced a concurrent schema-migration failure. The candidate now holds one migration transaction and includes a concurrent legacy-start regression. Follow-up independent review passed: the reviewer ran 40 iterations of an eight-way old-schema startup stress script without reproducing the race, reran all 55 broker tests and all 10 approval-bridge tests, and reported no new blocker. This is separate-agent review, not human approval or a production penetration test.

## Compatibility and deployment gates

1. Coordinate with AI-PAM's uncommitted M6 candidate in worktree `b42c`. That task owns separate safe-write gateway work and has confirmed it is not changing the core. Preserve `agent_id=agent_id` when combining the dispatch additions. Do not deploy its write capability as part of this candidate.
2. Reconcile source/live transport drift and pin a combined release manifest before deployment. Update core, broker transport, approval service and Companion bridge as one bounded release; old callers lack the required identity and old management reads lack actor metadata.
3. Review the actual authorized human subject hash and configure both `ASTER_BROKER_APPROVER_SUBJECT_HASHES` and approval-service repeated `--approver-subject-hash` arguments. No hash was inferred, copied from a session, or added automatically.
4. Verify actual issuer behavior and passkey-specific ACR semantics before setting `ASTER_BROKER_PASSKEY_ACRS`. Do not map a generic MFA or login-success claim. Until this is proven, Red/management must remain denied. The implementation does not claim Authentik currently emits a suitable ACR.
5. Any change to approver entitlement/assurance mapping must first invalidate outstanding pending/approved requests, then restart the affected services and verify denied identities. The core does not dynamically consult the separate approval service's in-memory allowlist at consume time. Automatic entitlement-policy reload is not implemented.
6. Capture and verify protected database/config/source checkpoints; stop both database-using services during controlled production migration. Confirm human break-glass administration independently of this approval GUI. Do not print credential-bearing configuration or database contents into AI context.
7. Validate positive and negative paths with synthetic identities/resources through the actual deployed bridge and Unix sockets. No production write test is authorized merely by these local results. Check latency/lock contention and timeout behavior under representative bounded load; the current implementation conservatively reserves a write transaction for public store reads as well as mutations.
8. Obtain the project's explicit bounded corrective-deployment approval. Keep M1 open until that deployment and integration verification pass. Offline contract work can proceed independently; expanded broker-dependent integrations cannot.

## Recovery and execution limits

The database migration is additive, but old code must not be re-enabled with broad grants: it lacks the corrected checks. If the candidate fails, disable affected AI capabilities/approval entrypoints, retain human administration and preserve audit/state for diagnosis. Restore a tested restrictive bundle. After restoring an older database snapshot, invalidate all outstanding authorizations before reopening AI access; an old snapshot may predate consumption.

Consumption is **at-most-once authorization**, not exactly-once target execution. A process failure after consumption and before/after a gateway call leaves an uncertain external outcome. The same authorization cannot be replayed; inspect target state before any separately authorized retry. Revocation cannot cancel an already consumed/in-flight external action. Target-specific preconditions, idempotency and reconciliation remain required for effectful adapters.

## Next safe action

Independent review is complete. Preserve a focused local checkpoint and request separate publication approval if publishing. Prepare the exact identity/assurance and coordinated deployment plan before requesting deployment approval. No cloud project upload is part of this programme; canonical documents remain in this repository.
