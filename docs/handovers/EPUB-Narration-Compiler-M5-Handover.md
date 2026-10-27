# EPUB Narration Compiler M5 Handover

> Status: Compiler/monitor and inactive Aster Books beta deployed
>
> Date: 2026-10-26
>
> Production AsterTV: unchanged

## Delivered

- A daily persistent monitor in unprivileged Aster Speech LXC 116 reads the
  Calibre library through a read-only bind mount and maintains a private,
  durable generation queue.
- A static single-attempt worker is installed with one lock, low priority, a
  3 GiB memory ceiling and 300% CPU quota. It has no timer or enable target and
  remains inactive; the real backlog has not started.
- TrueNAS `Media/AsterReader` has a 128 GiB quota, daily 14-day snapshots and a
  protected configuration export covering queue/status/ready/manifests while
  excluding source-derived content, audio and timing.
- Publication uses immutable generations and atomic ready pointers. Exact
  normalized chapter content, sentence sample cues and Opus files are all
  hash-bound before a generation is visible.
- HP has an inactive synthetic Aster Books beta only. It is not linked from a
  menu, add-on or service and has no network path or shared progress. BOSGAME
  production is unchanged.

## Normal state

Healthy pilot state is: monitor timer active, both speech services active,
worker inactive, aggregate queue status fresh, source mount read-only and
output mount read-write. HomeLab Doctor reports these facts without book
identity. Beszel continues LXC 116 host-resource history.

Use `docs/runbooks/EPUB-Narration-Compiler.md` for exact status, retry, restore
and rollback commands. Never copy a title, path, source text, generated media,
timing record, progress value or source hash into an ordinary report.

## Recovery

- Full guest baseline: `epub-narration-m3-pre-20261026`.
- Pre-M5 renderer: `/opt/epub-narration/rollback-m5-20261026` in LXC 116.
- HP inactive beta checkpoint:
  `/storage/.aster-checkpoints/aster-books-compiler-beta1-20261026`.
- Aster knowledge pre-update directory and root-only checkpoint are retained in
  LXC 104.
- Dataset snapshots provide fast bulk rollback. The protected configuration
  archive has passed an isolated queue restore, and isolated synthetic
  source-driven regeneration also passed.

Rollback preserves Calibre, the queue, dataset and last-known-good generation.
It never deletes the only ready copy or restores over live state as the first
step.

## Remaining gate

The next action is not another background implementation task. Production
AsterTV promotion was explicitly excluded from the autonomous phase. It needs
a bounded production checkpoint and explicit production decision, followed by
two independent playback/progress passes. Do not start the multi-month real
backlog merely to satisfy that gate. The optional live missing-chapter fallback
remains absent.
