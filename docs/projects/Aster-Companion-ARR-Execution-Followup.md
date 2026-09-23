# Aster Companion ARR execution follow-up

> Status: Proposed — deferred from Companion close-out by Jason on 2026-09-23
> Owner: Jason
> Authorization stream: Stream M proposed; no implementation authorized here

## Purpose and outcome

Prove the retained Companion action card can review and execute the existing
bounded Radarr queue-record repair after Jason's separate operator approval.

## Current state and evidence

Both production ARR broker services are inactive as verified 2026-09-23. No
fresh report-issued candidate exists. The request/empty-state UI works, and 61
existing broker regression tests pass. No live approve/execute test is claimed.

## Scope and exclusions

Only the existing stale queue-record dismissal. No media deletion, download
client removal, blocklisting, redownload, new service actions or chat approvals.
Preserve Jason's decision to wait for a natural candidate; do not manufacture a
production fault or fixture without a new explicit decision.

## Authority model and architecture

The existing broker owns candidate, approval and audit state. Companion may
submit the reviewed opaque candidate to Aster's structured execution endpoint;
the model cannot grant approval. The operator CLI remains a separate boundary.

## Privacy and security

No new secrets in clients. Recheck the single-use, expiry, freshness, exact
operation, replay refusal and bounded Radarr adapter conditions before enablement.

## Pre-start risk assessment

Pending a concrete natural candidate and a new review. Enabling a dormant
production writer is a material operational change requiring explicit approval.
Before any mutation, record the exact candidate, effect, backup/checkpoint,
rollback, configured identities and expected service interruption. This note
is not authority to enable the service or issue an operator approval.

## Persistence and milestones

- [ ] Verify candidate eligibility and the approved action boundary.
- [ ] Review current service configuration and immediate recovery checkpoint.
- [ ] Obtain explicit enablement approval and Jason's candidate approval.
- [ ] Exercise real web/Mac review and execution, including replay refusal.
- [ ] Confirm postconditions and audit; return to the agreed enabled/disabled state.
- [ ] Update operations and close with evidence.

## Validation and evaluation

Run the existing broker and Aster execution suites unchanged. The live UI test
must prove the same candidate was reviewed, one bounded operation occurred,
and replay/expiry does not cause another broker action. Never substitute a
synthetic test result for a live production approval.

## Observability and maintenance

Use existing Doctor/service status and broker audit records; report an inactive
writer as intentional until a separately approved enablement decision.

## Backup, restore and rollback

Use the existing broker state backup and execution coordinator's recovery
contract. Queue-record dismissal is not a promise that a deleted queue record
can be recreated. Do not proceed with an unverified recovery checkpoint.

## Integration and documentation

Update Aster operations, the Companion operator guide, project portfolio and
security/approval records. Assess backup, Doctor and monitoring when enabling.
No new guest, IP, DNS entry, certificate, rack item, Homepage tile or knowledge
corpus is planned; revisit these only if the final design changes.

## Graduation criteria

An approved real execution through the Companion UI, scoped postcondition and
audit evidence, replay/expiry rejection, and an explicit standing operation state.

## Evidence log

2026-09-23: Jason selected “Defer live repair execution to a follow-up” during
Companion close-out. No broker was enabled and no approval was granted.

## Close-out

Not started. This is the retained follow-up gate, not a completed capability.
