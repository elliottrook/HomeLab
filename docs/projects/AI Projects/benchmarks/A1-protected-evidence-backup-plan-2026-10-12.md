# A1 private evidence: protected-copy and restore gate

**Status: Mac backup-tree copy verified 2026-10-12; TrueNAS/off-site copy and
isolated restore pending.** The [local-copy result](../evidence/A1-protected-evidence-local-copy-2026-10-12.md)
records Jason's exact approval and source/destination hashes. No backup job,
retention rule, credential or access-control scope changed.

## Why this gate exists

The A1 v2 control is a useful immutable development baseline only if its
private questions, returned answers and blind reviews can be recovered and
checked against the published content-free digests. The sole known live copy
is in the owner's `~/Library/Application Support/Aster-Stream-A-Evidence/`
tree. A read-only, no-content traversal of the v2 subtree found nine regular
files totalling 57,692 bytes, one child directory, no symlinks or other file
types, and no group/world-accessible entry; the parent is mode 0700. This is
an inventory count, not a complete integrity manifest. A later content-free
source integrity pass validated the 20-case corpus schema and produced the
canonical nine-file path/size/SHA-256 inventory digest
`b2528e2f585465ff8ec830363b9984a5c88db7d13d0243239c593ca5b750fdce`.
The per-file inventory stays private; this digest is a pre-copy checkpoint,
not a backup.
`tmutil destinationinfo` reports no configured Time Machine destination on
this Mac. The repository's
[backup architecture](../../../05-Backups.md) describes a restricted TrueNAS
pull scoped to `~/lab/private-backups` only. It cannot cover the A1 path by
that documented design. An undocumented backup, a successful current TrueNAS
job, the exact off-site inclusion and a restore of this corpus are all
**UNKNOWN / REQUIRES VERIFICATION**.
The main backup overview still lists the Mac pull at 04:15. A read-only
TrueNAS task query confirms the enabled Mac pull is now configured for 03:00;
the enabled Proxmox and other TrueNAS backup jobs also match the platform
owner's 00:30/01:00/02:00 sequence. This is configured timing, not a successful
copy or restore of this corpus. Correcting the central backup overview belongs
to the backup/platform owner.
The tracked [IDrive relay script](../../../../scripts/backup/idrive-relay-sync.sh)
syncs the entire `configuration/mac` tree to an encrypted cloud remote with
no A1-specific exclusion. The deployed relay's read-only source projection
also shows `sync_tree configuration/mac mac` and no A1-specific exclusion.
Its full file hash differs from the tracked script, so source/deployment
parity is **UNKNOWN** beyond those inspected lines. Treat a new copy under
`private-backups` as off-site-bound unless an explicit exclusion is
established.

This finding does not invalidate the published score hashes, but it blocks
claims that the raw evidence is **recoverably** backed up until the new
TrueNAS copy and restore are checked. Never delete the source because a local
copy exists or because a backup job has a green status.

## Recommended bounded protection path

1. Immediately before copying, recompute the private nine-file integrity
   inventory and require the digest above, owner-only modes, regular files,
   no symlinks, and the 20-case schema check. Stop on any drift.
2. **Only after the exact custody approval below**, make one owner-only copy
   of the v2 subtree at
   `~/lab/private-backups/aster-stream-a/answer-holdout-20261012-v2/`.
   Preserve bytes and do not create a symlink. The existing backup-root ACL
   already grants `truenas-pull` read/list only; verify inheritance on the
   new directory and files without widening the account or other trees.
   Keep the original untouched.
3. Verify the copied nine-file inventory matches the source. Observe the next
   normal TrueNAS Mac pull (task 2) and verify a destination copy at
   `/mnt/Recovery/configuration/mac/aster-stream-a/answer-holdout-20261012-v2/`.
   Do not trigger or reschedule a backup solely to make this test pass.
4. Restore from **TrueNAS**, not the Mac source, to a fresh owner-only
   temporary directory, recheck every file hash and the 20-case schema, and
   reproduce the content-free score. Remove temporary restored plaintext
   after verification while retaining source and protected backup copy.
   Check the next normal off-site relay's exact inclusion/retention separately
   before claiming disaster-site recovery. Record result/digests, not content.

Steps 1–2 passed on 2026-10-12. Steps 3–4 remain open and must use the normal
scheduled pull/relay; a previous green job cannot close them.

The recommended path reuses the established restricted Mac→TrueNAS backup and
encrypted IDrive relay. It avoids introducing a new decryption key and its
own recovery failure mode for this small, fictional-but-private corpus. It
does put readable evidence on the Mac backup tree and TrueNAS for authorized
backup operators, then encrypted material at IDrive e2. Source-side OpenPGP
encryption would reduce same-site plaintext custody but requires an additional
verified recovery identity and restore drill; it is an optional **separate**
design decision, not an assumed use of the OpenBao recovery keys.

Copying this dataset into `private-backups` changes its custody and off-site
retention scope. Jason **approved the exact nine-file v2 source, destination
and expected TrueNAS/IDrive path before step 2**, as recorded in the
local-copy result. No other evidence tree, credential, backup job or
retention setting is included. The HomeLab
[project standard](../../../Project-Creation-Standard.md) requires a new risk
decision for a materially different data set or blast radius.

## Failure and exit criteria

The backup status remains `UNVERIFIED` if ACL, transport, destination,
retention or isolated restore cannot be demonstrated. A Mac-side hash match
alone is insufficient; a TrueNAS restore and re-score are required. Do not
replay model requests to recreate lost answers. Stop on unexpected contents,
plaintext outside the established restricted backup scope, an unplanned
cloud destination or any checksum mismatch. If the copy fails before any
remote transfer, leave the original untouched and remove only the failed new
local copy after checking that no backup reader has seen it. Deletion from
TrueNAS or versioned off-site storage needs a separately reviewed retention
decision.
