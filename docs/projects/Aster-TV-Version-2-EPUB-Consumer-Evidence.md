# AsterTV v2 — compiled EPUB consumer evidence

Updated: 2026-10-26. Status: local gate passed; HP storage gate pending.

## Outcome being built

Selecting a compiled ebook in Aster Books will open the narrated reading page,
with sentence highlighting and generation-bound resume. Selecting an ebook
that is not ready, is malformed or cannot be validated will retain the existing
Calibre-Web handoff. Nothing autoplays.

The separate EPUB Narration Compiler is complete at Forgejo commit `fc91fcd4`.
Its worker, monitor, dataset and backup lifecycle remain authoritative for
generation. AsterTV is only a consumer and must never inspect compiler queue,
work or failed-attempt state.

## Consumer contract

The skin accepts only a numeric Calibre ID already present in its sanitized
Books feed. It then checks all of the following before exposing the local
reader route:

1. an exact owner-created activation record names the fixed reader bundle and
   output root and pins the bundle manifest SHA-256;
2. the exact `ready/<book-id>.json` file is a small regular non-symlink file;
3. the pointer has only the compiler's five allowed fields, matches the
   selected book ID and names only `generations/<id>/<source-sha256>`; and
4. the normal-entry reader is a regular non-symlink file.

The reader rechecks its complete bundle, pointer, generation containment,
manifest hash, every published member, content/timing hashes, sentence spans,
24 kHz sample clock and Ogg/Opus duration before showing the book. It uses a
unique hash-bound playback copy, stops only its own playback on Back, saves
private generation-bound progress and contains no network client or URL.

## Local implementation evidence

- Imported the completed compiler service subtree exactly from `fc91fcd4` so
  the consumer and compiler contract can be tested together.
- Added a normal-entry HP reader bundle. It takes a pinned manifest plus one
  numeric book ID, opens only from Home/Books/ebooks while Kodi is idle, and
  preserves the accepted reading page and sentence highlighting.
- Added a dormant Books handoff. Without a valid activation record and ready
  pointer, current ebook behaviour is unchanged.
- Passed 36 compiler tests, 24 Books tests and two normal-reader tests under
  ordinary and optimized Python. The bundle is byte-repeatable and offline.

## Storage boundary and pending risk decision

Live discovery found the existing TrueNAS AsterReader NFS share is writable
and restricted to Proxmox `192.168.50.10`. Mounting it on HP would expose
private queue/work state and grant an unnecessary write path, so that design
is rejected.

The narrow candidate is two new read-only exports, restricted to HP
`192.168.1.140`:

- `/mnt/Media/AsterReader/ready`;
- `/mnt/Media/AsterReader/generations`.

HP would mount them at `/storage/aster-reader/ready` and
`/storage/aster-reader/generations` over NFSv4.2. A firewall permit would allow
only HP to TrueNAS `192.168.20.40` TCP 2049. The compiler remains the only
writer; `state`, `work` and `pilots` are not exported to the client. There is no
Internet exposure, credential, Calibre write, source EPUB mount or production
BOSGAME change.

This is a new LAN trust path and therefore remains inactive until Jason accepts
that exact risk boundary. Before activation, checkpoint the two absent exports,
firewall state, HP mount-unit absence, reader absence and Books helper. Validate
read-only behaviour by attempting a disposable write, validate that unpublished
paths cannot be reached, run one ready-title reader test, then verify stop,
resume, no autoplay and rollback. A failed checkpoint, unexpected broader
export, writable mount or foreign playback is an abort condition.

## Remaining steps

1. Obtain the bounded storage/firewall decision.
2. Build and verify the reversible HP installer and mount units locally.
3. Add the two read-only exports and one narrow firewall permit.
4. Deploy the pinned reader and Books helper to HP only, with checkpoints.
5. Run one compiled-title native walkthrough and a not-ready fallback check.
6. Add Doctor/mount staleness and recovery evidence before considering
   production promotion.
