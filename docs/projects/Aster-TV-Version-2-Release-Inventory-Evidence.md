# AsterTV Version 2 release inventory evidence

> Status: HP inventory complete; consolidated recovery remains open  
> Date: 2026-10-27  
> Scope: HP lab only; production unchanged

## Outcome

The active HP candidate now has a bounded, read-only release inventory. It
verifies 21 exact anchors spanning the active family runtime, compiled Books
reader and Doctor, Acquisition Hub, official YouTube presentation, voice-search
pilot, Music player and owned landings, Media rail, startup sound, UI sounds,
screensaver and camera service.

The inventory is complete, but recovery is correctly reported as incomplete.
Recovery7 records the older family manifest and cannot reconstruct the current
EPUB Doctor successor. It remains valid predecessor evidence and must not be
presented as a complete v2 recovery package.

## Privacy and safety boundary

`release_inventory.py` reads only paths listed in the repository-owned spec.
Every anchor must be a regular non-symlink file, no larger than 1 MiB, and must
match its pinned SHA-256. JSON anchors must also satisfy their declared schema
and kind where available. Opaque add-on/service identities are hashed without
parsing or returning their contents.

Paths containing credential, secret, token, password, userdata, database,
profile, watch-history or listening-progress identities are refused. Reports
contain only labels, fixed paths, sizes, formats, expected metadata and hashes.
They exclude credentials, user profiles, watch history, listening progress,
media databases and cached media.

## Validation

- Eight unit tests pass for exact anchors, optional missing anchors, required
  relation failure, digest drift, malformed JSON, non-object JSON, symlinks,
  oversized files, denied paths, duplicate identities and opaque anchors.
- The live HP run verified all 21 declared anchors.
- The compiled Books Doctor's `after.family_manifest` matches the active family.
- The reader activation's `bundle_sha256` matches the compiled reader bundle.
- Recovery7's family reference is stale relative to the active family, so the
  report returns `recovery_complete: false` without mislabelling the verified
  component inventory as corrupt.
- Kodi was not restarted and no player, settings, account or history state was
  changed.

## Pins and operation

The repository spec is
`services/kodi/v2/hp_release_inventory_spec.json`. The checker is
`services/kodi/v2/release_inventory.py`. Run the checker on the HP with:

```text
python3 release_inventory.py hp_release_inventory_spec.json
```

Any required missing anchor, changed digest, unsafe path or malformed relation
fails closed. A successful component inventory is not production promotion.
The next release gate is a new consolidated recovery package whose manifest
covers the active family and every separately pinned successor.

The subsequent recovery-source audit mapped every one of the 21 anchors to an
exact retained source or predecessor-evidence disposition. The apparent final
gap—the active screensaver identity—was resolved to immutable stage
`/storage/.aster-staging/aster-idle-presentation5`, manifest SHA-256
`8756238b796579dbff1cfc1ecb6e9fc976561235e579b00c5c258f1155fa92ba`.
Recovery coverage therefore reports ready for assembly; no live add-on bytes
need to be adopted as an undocumented source.

## Consolidated source bundle

The first consolidated HP bundle was assembled at
`/tmp/aster-v2-recovery-bundle1` and copied independently to
`/tmp/aster-v2-recovery-restore1`. Both verify against manifest SHA-256
`b5856b6c3ce7d18c2a6b1e3f65f4e3060dbb08be592f7fa80f8af4b1a893463f`:

- 17 exact source stages;
- 159 regular files;
- 3,261,620 payload bytes; and
- no credential, profile, history, listening-progress, database, result-log,
  lock, proof-screenshot, bytecode or generated-publication content.

The compiled reader's `data` symlink is an exact forbidden mount boundary and
is not followed or copied. All other symlinks are rejected. The bundle verifier
recomputes every file hash and each source-tree digest and refuses missing,
changed or extra files.

This is successful source-material recovery, not yet a clean-client install
rehearsal. Graduation still requires an ordered installer contract and an
isolated apply/verify/rollback test. The temporary HP copies are retained until
that rehearsal so the accepted artifact can be tested without rebuilding it.
