# SA3 candidate-E journal gateway — 2026-10-27

## Result

Candidate E now has a source-only gateway composition that can request one
sanitized local-model proposal and bind it to the existing incident journal.
The new route is owner-authenticated and returns only the journal's bounded
state digest, decision counts and opaque pending-decision view. It does not
return the model hypothesis, private incident identity, evidence identities or
model authentication.

The composition preserves the existing separation of responsibilities:

- `sysadmin_proposal_boundary.py` constructs sanitized model input and
  revalidates the response against the current registered plan;
- `sysadmin_proposal_transport.py` makes at most one fixed local request with
  no tools, no retry and bounded timeout/output;
- `sysadmin_proposal_gateway.py` refuses an existing pending decision before a
  model call, then submits the accepted decision to the journal; and
- `IncidentStore.bind_follow_up()` reloads the incident and atomically rejects
  a proposal if its state changed while the model request was in flight.

The route cannot execute the selected observation. The separate existing
`/observe` route remains the only path to a registered producer and still
requires an authenticated owner request plus a matching pending decision.
Neither route can perform a repair.

## Validation

- Full dependency-free `test_sysadmin*.py` suite: **69/69 passed**.
- New journal-composition tests: **5/5 passed**.
- The tests prove one-call journaling, refusal before a call when a decision is
  already pending, stale-state rejection after a simulated concurrent
  observation, no journal entry for malformed model output, and refusal before
  transport when model authentication is absent.
- The FastAPI route and all changed Python files parse successfully.
- The local macOS and bundled Codex Python environments do not include FastAPI,
  so the additive HTTP route test has not run in either local environment. This
  remains a target-runtime release-candidate gate rather than an inferred pass.

## Boundary and next gate

No production file, incident database, model setting, route switch, service,
schedule or credential changed. No model request was made. Candidate E's
independent packet review remains open. Before deployment, freeze exact hashes,
run the gateway test against the target Python dependency environment, prepare
an exact rollback checkpoint and obtain approval for the Aster Agent restart.
Deployment must keep automatic routing and all repair authority disabled.
