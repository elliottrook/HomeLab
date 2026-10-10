# S1 collection gate — ready for human decision

Date: 2026-09-26

Packet manifest SHA-256:
`93b9671b4a7c8e216fec00c1351499441e6e08a1aed50f765566645f3a578911`

Status: **PREPARED; COLLECTION NOT AUTHORIZED**

## Proposed bounded action

After approval, reverify every manifest hash and the current custody exclusions,
then create only `${TMPDIR%/}/aster-s1-holdout-drafts` with mode `0700`. Collect up
to 50 new sanitized families over at most 30 calendar days and 90 minutes of active
human effort. Jason supplies each request and label without AI suggestions or
engine output. Stop with no evaluation if ten label decisions are unresolved, a
secret/private identifier appears, a bound fails or the packet changes.

The validator may report syntax/hash/quota errors without printing request text. It
must not fill, repair, rank or recommend a label. Accepted exact records and
receipts may be retained in the local experiment directory and committed locally.
Rejected/unaccepted text remains outside Git and is deleted at decision or after
seven days. Record collection start plus exact 7/30/90-day dates and active effort.

This proposed approval does **not** authorize:

- running any router or revealing any engine prediction;
- evaluation, threshold/rule tuning, model or semantic-router calls;
- a service, listener, background collector, calendar/web/personal-data access;
- production or network changes, credentials, tools or GPU use;
- shadow traffic, promotion, policy/permission changes;
- remote publication or `git push`; or
- more than 50 families, 30 days, 90 active minutes or ten unresolved labels.

## Prepared evidence

- Plan and registry hashes are embedded in the blank bundle.
- Executable validation and the JSON Schema share the frozen vocabulary.
- Fifty invented fixtures meet the structural quotas while every authority flag
  remains false.
- 58 focused S0/S1 validation tests pass. They include exact acceptance hashes,
  no-suggestion provenance, required prohibitions, sensitive/local inheritance,
  secret/address/email rejection, duplicate prevention, quota enforcement,
  session bounds and no network/process/file access in validator core.
- The empty template validates with zero cases and `structurally_ready=false`.
- The first proposed `/private/tmp` path was rejected after Time Machine reported it
  included. The replacement current `$TMPDIR` parent is Time Machine excluded,
  outside the named repositories and absent; Spotlight is disabled. Recheck at
  activation.
- An invented accepted Git fixture survived a disposable bundle/clone/hash restore.
  This does not claim HomeLab off-host backup verification.

## Known limitations

The validator cannot authenticate Jason, prove the asserted no-suggestion origin,
understand semantic privacy or prevent an administrator reading local files. S1 is
personalized human gold, not inter-annotator agreement. Current engines do not emit
sensitivity/egress/location fields, so privacy-routing quality remains unmeasured.
Even a passing result can only support a later, separately approved read-only
shadow proposal.

## Exact decision requested

Approve the manifest-bound S1 collection window described above, including creation
of the single mode-`0700` draft directory, local sanitized accepted-record writes
and local commits. Keep evaluation, deployment and push excluded.
