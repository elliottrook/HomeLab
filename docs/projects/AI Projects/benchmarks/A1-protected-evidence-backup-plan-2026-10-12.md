# A1 private evidence: protected-copy and restore gate

**Status: plan only, 2026-10-12.** No evidence was copied, exported,
uploaded, decrypted or deleted by this assessment. It changes no backup job,
retention rule, credential, access control or off-site scope.

## Why this gate exists

The A1 v2 control is a useful immutable development baseline only if its
private questions, returned answers and blind reviews can be recovered and
checked against the published content-free digests. The sole known live copy
is in the owner's `~/Library/Application Support/Aster-Stream-A-Evidence/`
tree. Read-only checks show its directory is mode 0700 and the current
20-case evidence occupies about 72 KiB. `tmutil destinationinfo` reports no
configured Time Machine destination on this Mac. The repository's
[backup architecture](../../../05-Backups.md) describes a restricted TrueNAS
pull scoped to `~/lab/private-backups` only. It cannot cover the A1 path by
that documented design. An undocumented backup, a successful current TrueNAS
job, the exact off-site inclusion and a restore of this corpus are all
**UNKNOWN / REQUIRES VERIFICATION**.

This finding does not invalidate the published score hashes, but it blocks
claims that the raw evidence is safely backed up. Never delete the source
because a local archive exists or because a backup job has a green status.

## Proposed bounded protection path

1. Freeze a source inventory with file names, byte lengths and SHA-256 values
   locally; publish only a content-free manifest/digest in Git. Reject
   symlinks, unexpected file types, changed source hashes or loose modes.
2. Create one source-side encrypted, authenticated archive on this Mac using
   a separately verified recovery identity whose private key is held outside
   the backup set. Do not use a new passphrase typed into Codex or put key
   material, raw questions, answers or reviewer comments in Git/logs.
   Confirm that the recovery identity can decrypt an innocuous probe before
   using it; do not assume the OpenBao recovery keys are suitable.
3. After a specific custody decision, place only that ciphertext and its
   non-sensitive checksum/manifest under a restricted
   `~/lab/private-backups/aster-stream-a/` directory. Verify owner and
   `truenas-pull` read-only ACLs without widening either account beyond the
   current backup root. Do not create a symlink from the private source tree.
4. Verify the exact current TrueNAS pull scope and a successful run containing
   the ciphertext. Separately verify whether the current relay includes this
   destination; repository descriptions mention both `Media/backup` and the
   newer `Recovery` layout, so no off-site claim follows from documentation
   alone. Do not broaden relay scope implicitly.
5. Restore into a fresh owner-only temporary directory from the **backup
   destination**, compare archive and member hashes, decrypt only in that
   isolated private directory, and re-run the content-free scorer against the
   restored evidence. Remove temporary plaintext after validation while
   retaining the original and protected copy. Record date, source/backup
   digests, result and recovery custodian, not contents.

Copying the corpus into `private-backups` changes who can hold its ciphertext
and may place it on TrueNAS and IDrive e2, even if both transport/storage
layers are protected. That privacy/retention boundary needs Jason's **exact
approval before step 3**, after current off-site scope, recipients, retention
and restoration method are verified. Step 2 also requires a verified recovery
identity; if obtaining it would expose a private key, stop. The HomeLab
[project standard](../../../Project-Creation-Standard.md) requires a new risk
decision for a materially different data set or blast radius.

## Failure and exit criteria

The backup status remains `UNVERIFIED` if encryption, key recovery, ACL,
transport, destination, retention or isolated restore cannot be demonstrated.
An archive hash match alone is insufficient; a decrypt-and-score restore is
required. Do not replay model requests to recreate lost answers. Stop on
unexpected contents, plaintext outside owner-only storage, an unplanned cloud
destination or any checksum mismatch. Rollback before a successful copy is
simply to leave the original untouched and remove a failed local ciphertext;
deletion from remote/versioned storage needs a separately reviewed retention
decision.
