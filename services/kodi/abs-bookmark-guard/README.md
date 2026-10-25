# Audiobookshelf bookmark safeguard — shared server active, client UI pending

Governing record: [safeguard project](../../../docs/projects/Aster-Books-Bookmark-Safeguard.md).
The exact overlay was activated with Jason's approval on2026-10-25. The governing
project records its private checkpoint, isolated restore, target-runtime tests
and existing-client checks. No real bookmark mutation or normal UI enablement
has been performed. Build/verify tools remain non-deploying; `deploy_guard.py`
is the bounded, one-shot NAS checkpoint/activation helper and requires explicit
operator authorization. It never restores an older DB over live progress.

## Contract

Existing authentication and per-item access checks remain in place. New routes:

| Method / suffix after `/api/me/item/:id/bookmark` | Result |
|---|---|
| GET `/aster-guard` | Authenticated book-specific protocol probe; no-store |
| POST `/create-only` | 201 + strong ETag for a genuinely new book/time;409 on collision |
| DELETE `/conditional/:time` | Requires exact `If-Match`;204 only for unchanged record;412 if changed |

These are deliberately different paths from legacy upsert. Removal or a
version mismatch must never make Aster fall back to POST `/bookmark`.
Only audiobook items are accepted by the added routes. No podcast-specific
bookmark identity is invented. Aster normal UI may use create only; deletion
is restricted by the client trial grant, not automatically authorized by this
server capability. Server access remains the authenticated user's existing
own-bookmark permission; ETag is a precondition, not a replacement for auth.

All ordinary bookmark mutations now take a fresh user-row snapshot inside a
SQLite IMMEDIATE transaction and persist only `bookmarks`. Legacy create/rename,
edit and deletion keep their expected behavior. A bounded per-database process
queue reduces contention, but the **database lock**, not that process queue,
provides cross-process serialization. Busy/queue expiry is503, not blind retry.
Uncertain client results must be fenced rather than replayed. No schema change.

New records carry `asterGuardGeneration`, an opaque random field. It is also
rotated by a genuine legacy edit. ETag includes this generation, preventing
old cleanup tokens from matching delete/recreate or edit-away/edit-back records.
Removing the overlay leaves that inert JSON field in legitimate records;
do not wipe data to remove it. A legacy client's deliberate later edit remains
an edit, not a permanent lock against the household owner's other apps.

## Reproducible build/tests

`build_guard.py --source SOURCE --output NEW_DIRECTORY --node NODE` accepts
only the three exact static sources exported from the deployed2.36.0 image.
Source paths/hashes and base image ID are pinned in the builder. It emits three
modified upstream files plus two original guard modules, syntax-checks all
five and records hashes. Existing output is immutable. `verify_guard.py ROOT
MANIFEST_SHA256` verifies the complete artifact without activation.

`package.json` pins the same Sequelize/sqlite3 library versions as the live
image for **isolated synthetic tests only**. Install them into a temporary
test prefix, not the repository or shared container. Set `NODE_PATH` to that
prefix's node_modules, and `ASTER_GUARD_CANDIDATE` to the built package. Run
`node --test test_guard.cjs`. The harness uses temporary fake users/books and
SQLite files, never the real configuration/database. Two independent Node
processes test the cross-process race. Python builder/removal tests run with
`ASTER_GUARD_NODE=NODE python3 -m unittest discover -s THIS_DIRECTORY`.

The approved pinned Linux/Node20 image test passed all20 tests on2026-10-25;
see the governing project evidence. It used a disposable container, no network,
no production config/media mounts, a read-only root and private bounded tmpfs.
No test may import `/config` from the real container for convenience.

## Deployment/removal procedure

First verify exact image ID `sha256:66b24f73e543959d5df7e57bc0edbeab5e759730ec356656198b5da123468c15`
and three original code hashes. Preserve current Compose privately at
`/mnt/Media/appdata/dockge/unified-media-shadow/compose.yaml`, all live mounts/
ports and environment; never export its secrets. Config is
`/mnt/Media/appdata/unified-media-shadow/audiobookshelf`; metadata is the sibling
`audiobookshelf-metadata`. Source DB is `/config/absdatabase.sqlite` inside ABS.

After explicit deployment approval, verify a private SQLite-consistent backup
and a config checkpoint without exporting keys; prove isolated restore and
integrity. Stage immutable code in a separate private versioned directory,
check complete hashes, and add only five read-only code-file mounts to this
one service. Render/compare Compose privately, ensuring existing media/config/
podcast mounts, ports, user/environment and other services stay unchanged.
An idle-listener check and a short recreate/restart of only Audiobookshelf
are required. Do not run broad Compose up, pull, prune or remove operations.

Validate status, existing login/read/playback paths, capability access/denial,
source preservation and the newly approved single disposable UI trial once HP
is available. Do not reuse the earlier consumed API-trial grant. A conditionally
deleted bookmark must match its own exact freshly created ETag. Unknown result
or a changed token is retained for review, not an excuse for broad cleanup.

Rollback removes only these five mounts and restarts the same pinned base
image, preserving data/mounts/credentials. Existing bookmark/progress state is
**never** restored from an older backup as routine rollback. The new routes
then disappear and Aster must disable creation. Keep code/checkpoints for audit.
Actual live removal/recovery remains a gate; local tests restore all original
code hashes and preserve an independent synthetic data sentinel.

## Provenance

Base code is from the user's deployed
[Audiobookshelf](https://github.com/advplyr/audiobookshelf/tree/v2.36.0), GPL-3.0;
its upstream license remains in the unchanged base image. Distribute the
modified source overlay together with that upstream license/attribution if
publishing it; this candidate is local/private and has no new binary release.
The two guard modules, patch builder and test harness are maintained here.
