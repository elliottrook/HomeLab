# Bounded S0 manual pilot approval — 2026-09-25

Jason directly replied “Approve” to the exact collection-start statement in task
`01a0da33-48a7-7130-b567-5e0eb698139f`. This is an authorization record, not a case,
label, content-review receipt or cryptographic identity attestation.

## Authorized envelope

- Collection dates: **26 September through 25 October 2026**, America/Vancouver.
  Operational interval: 2026-09-26 00:00 PDT inclusive to 2026-10-26 00:00 PDT exclusive.
- Jason is reviewer and labeler. At most 30 sanitized, authored synthetic S0
  train/dev families, in batches of 10. No main-study or hidden test cases.
- Every case and label requires explicit human approval of its exact revision.
  AI proposals must be identified as such; never claim human authorship or approval
  from this blanket pilot authorization.
- Stop for review if median labeling time exceeds two minutes or unresolved cases
  exceed 20%. Do not infer elapsed labeling time from chat timestamps. No timing
  or satisfaction observation has been collected.
- Unreviewed drafts stay outside Git for at most seven days; rejected drafts are
  discarded after human review. No staging of unreviewed content.
- Approved sanitized cases, labels and negative results may remain durably in Git,
  mirrors and backups. Withdrawal stops use but cannot guarantee historical erasure.
- Exclude real interactions, private facts, identifiers and secrets.
- No model calls by pilot tooling, router evaluation, production execution,
  deployments, permission changes, further push or later 300-family study.

## Start and storage checks

Local clock at verification: 2026-09-25 20:15:38 PDT, before the approved start.
No cases, labels, review records, pilot data directory or drafts were created.
A coordinating message used a September 25 start; the directly approved September
26 start above governs. No retrospective case creation is permitted.

Read-only `tmutil isexcluded /private/tmp` reported Included. Do not use that root
for unreviewed drafts. `getconf DARWIN_USER_TEMP_DIR` identified the existing user
scratch root; its resolved path is
`/private/var/folders/c4/206kfl8n3938m5crwmy_yp5h0000gn/T/`.
`tmutil isexcluded` reported Excluded for that root; `mdutil -s` reported Spotlight
server disabled. No backup or indexing configuration was changed.

At collection start, recheck the clock and those properties on the actual draft
subdirectory before writing content. Use a private task-specific subdirectory with
mode 0700 and draft files 0600. No cloud upload, synchronization or external staging
is part of this workflow. These checks establish Time Machine/Spotlight behavior,
not protection against every third-party backup product; other capture remains
UNKNOWN. Only non-identifying synthetic drafts are permitted. Deleting a draft
is not a promise of secure erasure.

## Resume

On or after September 26, recheck this authorization, dates and scratch safeguards.
Prepare the first ten AI-proposed S0 drafts outside Git, one per approved stratum.
Present each draft and its proposed labels for Jason to accept, revise or reject.
Do not mark any accepted, measure human effort or retain a repository pilot record
before that case-by-case decision. The current validator remains fixture-only and
its collection/evaluation-authorized outputs remain false; it is not an intake
or human-authentication tool. No validator bypass or permission expansion is implied.

No scheduled wakeup was requested or configured. No remote publication is authorized.
