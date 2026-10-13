# A1 v2 protected evidence: Mac backup-tree copy

**State: local copy verified; subsequent TrueNAS restore passed; off-site pending.** Jason
approved this exact nine-file, fictional A1 v2 backup and isolated restore on
2026-10-12. No backup job was triggered, no credential or retention setting
changed, and the original owner-only evidence remains untouched.

The approved source is
`~/Library/Application Support/Aster-Stream-A-Evidence/answer-holdout-20261012-v2/`.
Immediately before copying, a read-only traversal found nine regular files,
one child directory, no symlinks or other file types, 57,692 file bytes and
owner-only modes. The 20-case holdout validator passed. The canonical
relative-path/size/SHA-256 inventory digest matched its earlier pinned value:
`b2528e2f585465ff8ec830363b9984a5c88db7d13d0243239c593ca5b750fdce`.

One staged copy was written and atomically placed at
`~/lab/private-backups/aster-stream-a/answer-holdout-20261012-v2/`. The
destination did not previously exist. Recomputing all nine destination hashes
gave the same inventory digest and 57,692 bytes; the holdout validator again
reported 20 cases with matching case, key and manifest digests. All files and
directories are owner-only. Every file inherited `truenas-pull` **read-only**
ACL access; both nested directories inherited list/search access. The
backup-root account's scope was not widened and no plaintext entered Git.

Read-only TrueNAS task metadata shows Mac pull task 2 enabled at 03:00 with
destination `/mnt/Recovery/configuration/mac`; its most recent reported job
state was `SUCCESS` **before this new copy**. This does not establish that
TrueNAS has these files. The deployed relay has a `configuration/mac` sync
without an A1-specific exclusion; this is a likely off-site route, not a
verified completed upload or restore. The tracked and deployed relay-script
hashes differ, as recorded in the [plan](../benchmarks/A1-protected-evidence-backup-plan-2026-10-12.md).

**Subsequent result:** the normal TrueNAS pull and isolated re-score passed on
2026-10-13; see the [restore drill](A1-protected-evidence-TrueNAS-restore-2026-10-13.md).
The normal encrypted off-site relay remains a separate unverified gate. Do not
delete either Mac source or rerun the model to recreate lost answers.
