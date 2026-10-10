# M4 synthetic storage checkpoint — 2026-09-25

Status: local storage foundation demonstrated; M4 remains open. Owner: Jason;
implementation: Codex. No production service, dependency installation, private
collection, inference request or remote write occurred in this step.

## Implemented and validated

The caller-owned SQLite ledger accepts strict versioned experiment, outcome,
evaluation and review records. Experiment specifications enter as preregistered
and cannot be replaced. Evaluations must match their frozen dataset, candidate and
evaluator digests. Reviews bind one exact evaluation event; subsequent evaluations
or reviews require a new experiment. Identical event retries are idempotent;
conflicting retries fail. Transactions serialize separate writers. SQL triggers
reject ordinary update/delete, and canonical hashes link the ordered records.

Forty adaptive tests pass, including ten storage tests covering malformed/private
fields, forbidden authority, frozen provenance, duplicate events, concurrent
writers, interrupted transaction rollback, edits, truncation and backup/restore.
The [restore proof](M4-storage/restore-proof.json) retains matching original and
restored hashes for three disposable synthetic events. Temporary databases were
removed. The fixture's 1/10 label is illustrative, not measured model quality or
a retrospective registration of M3. [Manifest](M4-storage/manifest.json) pins
implementation, schemas and proof; versioned Evaluation and Review JSON schemas
are beside it. Semantic checks still require the Python validator.

## Security, privacy and recovery limits

This is a local prototype, not an authenticated evidence service. A database owner
can remove triggers and rewrite records and hashes. Independently retain the head
returned by `verify()` or `backup()`; restore into a separate caller-owned path and
call `verify(expected_head=retained_head)` before using it. Without that external
checkpoint, a self-consistent replacement or truncation may go undetected. A
checkpoint in the same writable location does not provide independent protection.
Backup refuses an existing destination. A failed backup is not an accepted recovery
copy; keep the prior verified copy. No production backup retention is established.

Reviewer references distinguish record roles but do not authenticate people or
provide independent approval. The ledger validates lineage, not the truth of a
verdict, metric interpretation, label quality or signed provenance. Outcome records
do not yet bind directly to an experiment. Bounded reference fields are not a
redaction system; only synthetic opaque identifiers are permitted in this prototype.
No collector, deployment hook or automatic promotion path exists.

## Integration and next gate

Repository docs and synthetic recovery evidence are updated. Doctor, monitoring,
NetBox, wiki, knowledge mirror, operational reference, diagrams, Homepage,
authentication, DNS/firewall, schedules and AI broker integration are not applicable
to this disposable local prototype: no deployed service or operational fact changed.
Security ownership and durable backup/retention remain requirements for any future
deployment, as does explicit private-data collection approval.

Next safe local work: define measured-result/outcome linkage and reproducible dataset
manifests, then exercise a newly preregistered synthetic paired experiment through
the store. Do not relabel completed M3 measurements as preregistered ledger events.
M4 still needs proposal/review separation beyond metadata, label provenance and
calibration where supported, and an approved storage/retention design before live
use. M3 representative labels/model evidence and M1 security/deployment gates remain
open. All M2–M4 commits after the published M1 checkpoint await an explicitly
authorized Forgejo push; production remains on its existing baseline.
