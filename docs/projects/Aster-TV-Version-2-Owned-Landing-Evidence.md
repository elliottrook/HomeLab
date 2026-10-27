# Aster TV Version 2 — owned Music and Books landing contract

Date: 2026-10-26
Status: owned contract and Books date feed active on HP; production unchanged

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

The Music producer candidate has now been added against the exact album fields
advertised by the HP's Kodi JSON-RPC 13.5.0 schema. It paginates the complete
album catalogue up to the existing 20,000-item safety bound, fails on changing
or incomplete pagination, and emits only Kodi-local album identities. Recent
albums use Kodi's real `dateadded`. Hero candidates exclude that recent set and
require either affinity with genres the household has actually played or a
high local user rating; their displayed reason states which signal was used.
Candidates without hero art and holiday-classified albums are omitted. No file
path or MusicBrainz/acquisition identity enters the presentation record.

## HP Books source-date activation

The Books producer/consumer date enrichment is now active on the HP lab only.
The first reversible layer at
`/storage/.aster-checkpoints/aster-books-source-dates-20261026` installed the
three parser/refresh files and proved source dates for all 46 audiobooks and
seven subscribed podcasts while retaining the 505 undated ebooks. The second
layer at `/storage/.aster-checkpoints/aster-books-full-dates-20261026` retained
that state, installed the Calibre snapshot with its real `books.timestamp`
values and refreshed audio through the existing private client.

The resulting sanitized feed contains 558/558 source-dated records: 505 ebooks,
46 audiobooks and seven podcasts. Its accepted post-refresh SHA-256 is
`4dcab0da7292f85b045733b1d120a358e95f3f1f844659ff29a3c34c7266b470`.
Normal Books entry reported **Read-only catalogue · 558 source-dated titles**
and displayed dated rows in all three lanes. Kodi remained active, the refresh
service completed successfully and the log contained no new error, fatal,
traceback or XML-parser event. Listening progress, covers, media files,
credentials and production Aster were unchanged.

## Verification

Seven focused tests cover real-date ordering, undated omission, signal-required
recommendations, recent-item exclusion, action/authority separation, duplicate
rejection, focus-safe rotation and optimized-Python time checks. The complete
skin-tool suite passes 111 tests and the complete Kodi v2 suite passes 1,198
tests, each in normal and optimized Python; the one existing Mac-only skip is
unchanged.
