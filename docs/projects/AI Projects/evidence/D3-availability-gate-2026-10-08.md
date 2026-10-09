# D3 availability and completed-answer presentation

Status: LOCAL CANDIDATE; live deployment approval pending. No inference proposed.

## Problem and result

After the accepted native pilot, intake is closed. The installed gateway removes
its capabilities endpoint with intake, so the app cannot distinguish a deliberate
closure from an unavailable server. Completed answers are memory-only and disappear
on restart/expiry; the installed message suggests recovery without offering it.

Candidate build 7 adds an authenticated read-only capabilities response while
intake is closed. No submission/payload route is enabled. It reports worker status
as unknown: neither an enabled intake nor a historical completion proves worker
readiness. Fully disabled delegation still exposes no routes. The status endpoint
does not read secrets, introspect worker credentials or call a model.

Native UI disables Ask Codex unless compatible capabilities are confirmed; status
read failures do not prevent attempts to read recorded jobs. Completed missing
answers are described as completed with temporary text unavailable, not failed.
The UI explicitly says the pilot cannot restore them and warns against resending
for recovery. No new content retention, background worker or replay is introduced.

## Validation

33 native tests and 252 backend tests pass. Tests include owner authentication on
closed status, no submission endpoint, no custody/network access for status, no
claim of worker readiness, and completed missing-answer presentation. Release
build succeeded and assembled ad-hoc signature passed strict verification.
[Artifact manifest](D3-availability-artifacts-2026-10-08.json) binds package files.
No installation, new model request or live service change in preparation.

## Proposed bounded rollout

- Recheck installed build 6, gateway hashes against accepted native artifacts,
  healthy service, absent request-enabling drop-in and inactive worker.
- Preserve/verify build 6 at `/Applications/AsterCompanion.pre-availability-20261008.app`
  and the two old gateway modules at
  `/var/lib/aster-delegation-checkpoints/availability-20261008`; refuse collisions.
- Deploy ONLY request_intake.py and gateway_assembly.py from the frozen candidate.
  Leave request-enabling drop-in absent. One brief Aster restart. Verify original
  43 paths plus only the authenticated GET capabilities endpoint (44 total),
  unauthenticated denial, absent POST submission/payload routes and healthy service.
- Install/reopen signed Companion 0.3.0 build 7; verify whole-bundle hashes and
  normal authenticated status. Jason should see submissions closed and retained
  completed request status without a promised recoverable answer.
- On failure restore the two modules and whole app from verified copies and
  restart if required. Preserve ledger, all earlier backups and identity state.

No Keychain worker read, account activation, inference, credential renewal,
policy change or Git push. Deployment requires repository remote-change approval.

## Following milestones — local preparation first

1. Design bounded supervised session admission: status must be freshness-bound to
   an authenticated worker lease, not inferred from the intake flag. Lease renewal
   must never renew authority or credentials. Sleep/disconnect/expiry closes new
   admission and preserves uncertain assignments. Current four-minute manually
   coordinated flow is a pilot limitation, not the final user experience.
2. Define answer recovery without rerunning inference. Compare authenticated
   retrieval of the original completed Codex thread with explicit encrypted local
   answer retention. Bind original owner/job/thread/turn/digest; do not browse or
   import unrelated conversations. Retention and credentials require separate
   review before any implementation that stores real content or reads history.
3. Validate reconnect/cancellation/limits with fixtures before a bounded live
   acceptance. Follow-up context must be separately previewed and consented;
   it cannot silently forward old chat history.

D3 remains open. No sysadmin tools or general autonomous worker are authorized.
