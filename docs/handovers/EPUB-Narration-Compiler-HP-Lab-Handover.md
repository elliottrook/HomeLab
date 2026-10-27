# EPUB Narration Compiler HP Lab Handover

> Status: M0–M6 complete; HP Lab deployment accepted
>
> Date: 2026-10-26
>
> BOSGAME production: unchanged

## Delivered

- A daily persistent monitor in unprivileged Aster Speech LXC 116 reads the
  Calibre library through a read-only mount and maintains a private queue.
- A low-priority, single-attempt canonical Aster worker is installed with a
  3 GiB ceiling, 300% CPU quota, one lock and no timer. It remains inactive, so
  the 167-item backlog has not started.
- TrueNAS `Media/AsterReader` has a 128 GiB quota, daily 14-day snapshots and
  an accepted-state snapshot. The protected exporter covers main and HP pilot
  queues, status, ready pointers, manifests and the reconstruction marker while
  excluding EPUB text, normalized content, Opus and timing.
- HP Lab has a private direct-launch reader at
  `/storage/.aster-staging/aster-books-compiler-hp-beta1`. It consumes one
  isolated real compiler generation, has no network or normal menu entry and
  stores progress in a dedicated private namespace.
- Two final independent native passes verified no autoplay, exact sentence
  highlighting, pause stability, chapter changes, Back/save, reopen/resume,
  explicit cleanup and empty playback queues. Kodi was not restarted.

## Start and use

HP must be idle on Home. From the operator Mac:

```sh
ssh -o BatchMode=yes root@192.168.1.140 "kodi-send --action='RunScript(/storage/.aster-staging/aster-books-compiler-hp-beta1/default.py,7f770e8cc2dd2564c23c71700fa575275fe4b33d30f31d4ac3c8242930b0dcd8)'"
```

Nothing plays until Play/Pause is selected. Gold marks the current exact
sentence. Previous/Next chapter changes chapters without autoplay. Back stops
only this reader's owned session and saves position. Clear beta progress
removes only this beta's position. A failure notification means the reader
stopped at a validation or ownership gate; do not stop unrelated playback.

This is intentionally not in the normal HP menu. BOSGAME and its menu were not
changed. Adding a normal route or moving this to BOSGAME is a separate project.

## Recovery and backup

- Full guest baseline: `epub-narration-m3-pre-20261026`.
- Pre-M5 renderer: `/opt/epub-narration/rollback-m5-20261026` in LXC 116.
- HP direct-launch absent-state checkpoint:
  `/storage/.aster-checkpoints/aster-books-compiler-hp-beta1-20261026`.
- Accepted dataset snapshot:
  `Media/AsterReader@hp-beta1-accepted-20261026`.
- Protected configuration archive: main/pilot queues, status, ready pointers,
  manifests and pilot marker; generated text/audio/timing remain excluded.

Use [the operations runbook](../runbooks/EPUB-Narration-Compiler.md) for status,
failure, restore and rollback procedures. Never copy book title, identity,
path, text, audio, timing, progress or source hashes into ordinary reports.

## Deliberately deferred

- Starting the full real backlog remains a deliberate operator action.
- A normal HP menu route and any BOSGAME promotion are not part of this close.
- Live missing-chapter synthesis remains optional M7 and is absent.
