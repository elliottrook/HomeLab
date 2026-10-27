# EPUB Narration Operational Reference

> Authority: current-with-exclusions
>
> Reviewed: 2026-10-26

## Purpose and authority

The EPUB narration compiler is a private, local-only lab service. Calibre owns
book metadata and EPUB source membership. The compiler reads that source
through a read-only mount, maintains its own durable generation queue and
writes only to the separate quota-bounded AsterReader dataset. This reference
contains operating facts only; it deliberately excludes book identities,
paths, text, audio, timing data, listening progress and source hashes.

## Current operating state

- The daily persistent monitor is active and reconciles new or changed EPUBs
  idempotently.
- The low-priority single-attempt worker is installed but intentionally
  inactive. It has no recurring schedule and the queued backlog has not been
  started.
- The worker uses Aster's canonical local voice contract and publishes 48
  kbit/s mono Opus with exact sentence-level sample cues.
- A generation becomes visible only after all file hashes, timing bounds and
  codec properties pass and an atomic ready pointer is replaced. A failed
  replacement leaves the previous ready generation selected.
- The inactive Aster Books beta consumes only those ready pointers. It has no
  production entry point, network listener or shared progress store.

## Status and failure meaning

Normal queue states are `queued`, `extracting`, `narrating`, `aligning`,
`ready` and `failed`. Monitoring exposes only aggregate counts and bounded
failure classes. A queued item means work is known, not that narration is
available. A failed item must be investigated by its bounded class without
printing or exporting the affected source identity.

HomeLab Doctor owns functional checks for mount direction, monitor freshness,
queue state and worker resource controls. Beszel already monitors the Aster
Speech guest's host resources; no duplicate service or agent is needed for the
offline compiler. TrueNAS remains under its existing infrastructure and native
monitoring.

## Privacy, backup and recovery

There is no public route, application credential or Calibre write authority.
Listening progress belongs only to Aster Books' private generation-bound state
and is neither written to Calibre nor mixed with Audiobookshelf.

Daily dataset snapshots retain local generated payloads. The protected
configuration export stores an online backup of queue state plus sanitized
status, ready pointers and immutable manifests while excluding generated
content, audio and timing. Restore queue/manifests into an isolated location
and verify integrity before changing live state. Calibre EPUBs remain the
authoritative regeneration source.

Rollback stops the monitor and worker, removes any inactive Aster Books bundle
reference and preserves the AsterReader dataset, snapshots, queue and last
known-good generations. It never writes to Calibre or deletes the only ready
copy.

Exact operator commands are maintained in
`docs/runbooks/EPUB-Narration-Compiler.md` in the HomeLab repository.
