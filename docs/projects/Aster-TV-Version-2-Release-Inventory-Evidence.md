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

This first bundle exposed one omitted clean-install dependency during the next
gate: the reader's separate consumer stage owns the read-only automount units
and Books handoff. The first bundle is therefore retained as audit evidence but
superseded, not promoted. The corrected inventory adds
`aster-epub-consumer1`, pins its reader relationship and requires its complete
source tree in the next bundle.

The ordered-install review then identified the second distinction: all v2
successors require the complete v1.1.1 client baseline. Its four exact archives
and release manifest are now a required recovery source, not an undocumented
assumption. The baseline declares and the HP confirms official YouTube add-on
7.4.4; the current HP also reports Jellyfin add-on 2.2.0+py3. External services,
network endpoints and restricted credentials remain prerequisites and are not
copied into the bundle.

Replay inspection also confirmed that the EPUB Doctor stage is deliberately a
delta: it contains the updated Doctor component, family manifest and Settings
file, not the other seven family runtime components. Recovery7 is therefore a
required source baseline followed by the Doctor delta, even though Recovery7
alone remains stale relative to the active family. Its complete source tree is
now pinned in the recovery plan; the earlier evidence-only disposition is
superseded.

The corrected Bundle4 is the first source-material candidate that includes all
three discovered clean-install foundations: the v1.1.1 base client, Recovery7
family base and compiled-reader consumer integration. It independently verifies
after copying with:

- 23 declared active/release anchors;
- 20 exact source stages;
- 273 regular files and 8,764,273 payload bytes; and
- manifest SHA-256
  `e614d1c85716f9c3fef73e02ae57a88ac142b28138ef8025933cfb7f0664eeda`.

The declarative replay recipe validates twelve ordered phases, all twenty
sources, eight non-secret prerequisites and only two planned Kodi restart
boundaries. It explicitly requires LibreELEC 12.2.1/Kodi 21.3, official YouTube
7.4.4, Jellyfin 2.2.0+py3, the existing private services and separate
least-privilege identity provisioning. Credentials and account state are never
recovered by copying another client's profile.

The core material chain then passed a real isolated apply/verify/rollback on
the HP without touching live Kodi paths. A disposable `/tmp` root extracted and
verified all four v1.1.1 archives, applied Recovery7, installed the Music
package, applied the EPUB Doctor delta, verified the resulting active family
SHA `11d4e7ab45f0123aa5135e1fdd7924fcf14010cb7ba12add1828c9f3fc139a58`
and Jellyfin guard SHA
`3f3478185c87cce9ff6e8c7bbe16e11de5a1d3d1eac89c51fe914d47b2121661`,
then removed the disposable tree and proved it absent. Secure archive handling
rejects duplicate, unexpected, absolute and traversal members; source copying
rejects symlinks. Live settings, profiles, players and services were unchanged.

This is successful source-material recovery, not yet a clean-client install
rehearsal. Graduation still requires an ordered installer contract and an
isolated apply/verify/rollback test. The temporary HP copies are retained until
that rehearsal so the accepted artifact can be tested without rebuilding it.
