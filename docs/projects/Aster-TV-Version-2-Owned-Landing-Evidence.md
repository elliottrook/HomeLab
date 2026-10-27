# Aster TV Version 2 — owned Music and Books landing contract

Date: 2026-10-26
Status: owned Music hero and Books date feed active on HP; production unchanged

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

The Music producer has now been added against the exact album fields advertised
by the HP's Kodi JSON-RPC 13.5.0 schema. It probes the reported total, then reads
one exact bounded 0..total snapshot to avoid Kodi's unstable equal-label page
boundary. Kodi reports one inaccessible sentinel in the current total, so the
producer permits that one observed discrepancy and fails on any larger gap.
It emits only Kodi-local album identities. Recent
albums use Kodi's real `dateadded`. Hero candidates exclude that recent set and
require either affinity with genres the household has actually played or a
high local user rating; their displayed reason states which signal was used.
Candidates without hero art and holiday-classified albums are omitted. No file
path or MusicBrainz/acquisition identity enters the presentation record.

## HP Music landing activation

The owned Music hero is active on the HP lab through immutable stage
`/storage/.aster-staging/aster-owned-music-landing3`, pinned by manifest
`e12b1b447dee1132976fb829c81ef475e81ee6cc6d1aecd7296f7da66f4a649d`.
Its private recovery checkpoint is
`/storage/.aster-checkpoints/aster-music-integration-20261024/owned-landing3`.
Two earlier candidates were cleanly rolled back after live reads exposed Kodi's
timezone-less source dates and one inaccessible catalogue sentinel; both
failures left the exact predecessor active before the successor was installed.

The accepted HP read evaluated 1,338 readable owned albums, identified twelve
real Recently Added albums and twelve recommendation candidates. The hero
rotates every twelve seconds while the top rail or hero actions own focus;
focusing the album grid immediately makes the selected tile authoritative and
hides the hero actions. Manual Next changed the visible recommendation without
moving to the grid. Open Album reached the existing v2 album player, and Play
started the displayed recommended album. The test playback was explicitly
stopped and HP returned to Home with an empty active-player list. Shuffle still
routes to the existing bounded, holiday-excluding implementation.

The final exact-file verification reports seven active members with checkpoint
recovery intact. Kodi logged no matching Music/XML error. Production was not
changed.

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

Twenty-one focused tests cover real-date ordering, timezone normalization,
Kodi's bounded inaccessible sentinel, undated omission, signal-required
recommendations, recent-item exclusion, action/authority separation, duplicate
rejection, focus-safe rotation, exact installation, rollback and
optimized-Python time checks. The complete Kodi v2 suite passes 1,206 tests in
normal and optimized Python; the one existing Mac-only skip is unchanged.
