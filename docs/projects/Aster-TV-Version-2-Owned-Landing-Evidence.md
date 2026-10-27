# Aster TV Version 2 — owned Music and Books landing contract

Date: 2026-10-26
Status: local foundation; no HP or production activation

## Decision

Music and Books will follow Media's accepted interaction pattern without
misrepresenting catalogue data. A title may appear in **Recently Added** only
when its owning library supplies a valid timezone-aware per-title timestamp.
An idle hero recommendation must be an owned title with an explicit bounded
reason and score derived from local-library signals. Undated or unsupported
records are omitted; Acquisition Hub suggestions cannot enter this playable
surface.

## Contract

- Music accepts only owned albums and exposes Play.
- Books accepts owned ebooks, audiobooks and subscribed podcasts, exposing Read
  or Play according to type.
- Identities are source-qualified and unique.
- Recently Added is deterministically newest-first and never substitutes feed
  generation time for a title's added time.
- Recommendation candidates require both a finite 0–100 score and a non-empty
  source reason. Neither field can stand alone.
- The twelve-second hero rotation pauses whenever a real tile owns focus and
  never changes remote focus.
- Empty trustworthy input remains empty rather than inventing content.

## Integration boundary

Kodi already supplies Music's recently-added album ordering. Books now has a
local producer/consumer candidate that projects only Calibre book timestamps
and Audiobookshelf item-added times into the sanitized feed. It canonicalizes
them to timezone-aware UTC, omits missing dates, rejects malformed/future dates
and sorts each Books section with real dated titles first. The currently active
HP snapshot remains unchanged; publishing the enriched feed and adding
domain-appropriate recommendation signals remain separate recovery-tested
steps.

## Verification

Seven focused tests cover real-date ordering, undated omission, signal-required
recommendations, recent-item exclusion, action/authority separation, duplicate
rejection, focus-safe rotation and optimized-Python time checks. The complete
skin-tool suite passes 110 tests and the complete Kodi v2 suite passes 1,192
tests, each in normal and optimized Python; the one existing Mac-only skip is
unchanged.
