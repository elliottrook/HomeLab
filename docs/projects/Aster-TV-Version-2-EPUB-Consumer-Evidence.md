# AsterTV v2 — compiled EPUB consumer evidence

Updated: 2026-10-26. Status: HP release candidate active and verified.

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

## Active storage boundary

Live discovery found the existing TrueNAS AsterReader NFS share is writable
and restricted to Proxmox `192.168.50.10`. Mounting it on HP would expose
private queue/work state and grant an unnecessary write path, so that design
is rejected.

The active implementation uses two read-only exports, restricted to HP
`192.168.1.140`:

- `/mnt/Media/AsterReader/ready`;
- `/mnt/Media/AsterReader/generations`.

HP mounts them at `/storage/aster-reader/ready` and
`/storage/aster-reader/generations` over NFSv4.2. A firewall permit would allow
only HP to TrueNAS `192.168.20.40` TCP 2049. The permit is the deterministic
rule `73937312-5b75-59b7-861a-b65ebe641620`. The compiler remains the only
writer; `state`, `work` and `pilots` are not exported to the client. There is no
Internet exposure, credential, Calibre write, source EPUB mount or production
BOSGAME change.

TrueNAS maps the root process from this one read-only HP export to server root
because the compiler deliberately publishes its output under private `0700`
directories. The first mount attempt retained normal root squashing, was denied
at traversal, and triggered the installer's clean rollback. The corrected
exports remain `ro`, host-restricted and path-restricted; no write permission
was added.

## Activation and live evidence

- Jason approved the bounded HP activation. TrueNAS checkpointed the absent
  exports at `/root/.aster-checkpoints/aster-epub-reader-consumer-20261026`.
  OPNsense checkpointed its prior configuration at
  `/conf/backup/config-aster-epub-nfs-apply-20261026.xml` and proved that copy
  parseable and byte-identical before replacing the live file.
- The installed package manifest is
  `33a8ef7c087f2437bf03eb35c2101c38b48bf652b6094bc4119ff20cef807a87`.
  Its reader pin is
  `d41eddcd7fe754eba6d00677e17aa0a69c2dd10991b434586fc6aa4578bc6f89`.
  The prior Books helper is retained under
  `/storage/.aster-checkpoints/aster-epub-consumer1-20261026`.
- Both NFSv4.2 mounts independently reported `ro,nosuid,nodev,noexec`; a
  disposable write failed with `Read-only file system`. The unpublished
  `state`, `work` and `pilots` trees were absent from the HP view.
- The live routing check retained all 505 catalogue ebooks. Its one ready
  title resolved to the pinned local reader; a separate unready title resolved
  to the unchanged Calibre-Web fallback.
- The native reader opened from Home while Kodi was idle, played canonical
  narration, observed sentence highlighting, advanced naturally to the next
  chapter, saved a private HP progress record and returned to Home through Back
  with no active player. Post-test package and active Books hashes still
  verified.

## Remaining gate

Add stale-mount/Doctor reporting and include this layer in the final composed
recovery package. Production promotion remains a separate owner decision; the
current candidate is intentionally HP-only.
