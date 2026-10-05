# S1 local custody design

Status: **proposed and unactivated**. No directory or case has been created.

## Chosen minimal path

Use `${TMPDIR%/}/aster-s1-holdout-drafts` for unaccepted drafts. On the current
Mac, `$TMPDIR` resolves below the per-user
`/private/var/folders/.../T` directory. It is outside the repository,
intentionally ephemeral and not a recovery store. Create it only after collection
approval with mode `0700`; create files with mode `0600`. The collection session
must fail if the path is a symlink, has another owner or has broader mode.

After Jason accepts an exact sanitized case and label hash, copy only that accepted
record and its receipt into the experiment's `accepted/` directory in the local
worktree. The accepted directory is durable Git history after a local commit, but
remains unpublished until a separate push approval. Do not store rejected draft
text; retain only a no-content count and reason code.

This deliberately avoids a database, cloud account, Notion, secret service or new
backup dependency for 50 sanitized records. It is sufficient only if Jason accepts
loss of unaccepted drafts. It does not provide cryptographic secrecy from the local
administrator or the repository process.

## Exclusion checks required before activation

Before creating the directory, prove:

1. the exact path is absent or an owned empty directory;
2. it resolves immediately below the current `$TMPDIR`, not through a symlink;
3. permissions are exactly `0700` and draft files exactly `0600`;
4. a resolved-path `commonpath` check proves the scratch path is outside every
   repository worktree; `git check-ignore` is not used as evidence for an outside
   path;
5. the current backup configuration does not collect the scratch path, or Jason
   explicitly accepts loss of drafts without calling that a tested exclusion;
6. the current OS search/index configuration excludes the scratch path, verified
   by an appropriate local read-only check rather than inferred from permissions;
7. no Aster knowledge or mirror configuration includes the resolved scratch path;
8. no draft text is present in the packet, tests, shell history or Git diff.

Read-only checks on 2026-09-26 established that the current `$TMPDIR` parent is
Time Machine excluded, the proposed child is absent and resolves outside all four
local HomeLab repositories, Spotlight is disabled, and no reviewed Aster
operations/agent configuration names the resolved path. Recheck these facts at
activation because `$TMPDIR`, backup configuration and indexing state can change.
Mode `0700`, ephemerality and outside-repository placement are not themselves proof
of backup or indexing exclusion.

The repository's normal backup and mirror behavior for accepted sanitized records
is the restore mechanism. On 2026-09-26 an invented accepted fixture was committed
to a disposable Git repository, bundled, cloned and hash-compared successfully
(`250a43a5802676c4217ef41b36544c61c5d4a34160af6d0bdfc29a9c37ece5f0`).
The temporary repositories were automatically removed. This proves the fixture
mechanic, not HomeLab publication or off-host backup; those remain later gates.

## Retention

- Unaccepted drafts: delete at acceptance/rejection, or after seven days.
- Accepted sanitized records: durable local Git retention, subject to review 30
  and 90 days after collection begins.
- Withdrawn records: retain hash/provenance and exclusion reason without request
  text where deletion is requested and compatible with Git history.
- Secret/private-data incident: stop collection, do not stage, remove the draft,
  record a content-free incident fact and reassess the custody method.

No collection approval, evaluation approval or production authority is encoded by
this design.
