# Aster TV Version 2 — owned Music and Books landing contract

Date: 2026-10-26
Status: cross-media landing review complete on HP; production unchanged

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

## HP Books recommendation hero activation

Books now uses the same focus-safe landing contract on the HP lab. The existing
six-hour refresh reads only the limited Audiobookshelf account's own progress
endpoints and source-owned author/genre metadata. Confirmed, visible household
listening records establish affinity separately for audiobooks and podcasts;
unstarted owned titles may then receive a finite score and a plain reason such
as `Because you listen to YA Fantasy`. Raw progress, account identity, paths,
URLs and credentials are removed before publication. Ebooks and podcasts do
not receive recommendations until equally defensible history exists.

The accepted live refresh inspected 53 audio titles and four existing progress
records, published eleven audiobook recommendations and retained all 558 owned
Books records. The resulting feed is 224,464 bytes, below its 262,144-byte
limit, and contains no transient/private fields. The landing presents three
Recently Added lanes. While no lane owns focus, the hero rotates every twelve
seconds and provides compact About, Listen and Next actions. Manual Next changed
the recommendation without moving focus. Listen opened the existing chapter
page without starting playback. A focused title immediately hid the
recommendation actions and restored that title's real cover, title and synopsis.

The first candidate was rolled back after visual inspection found that selected
titles still showed the old generic Books emblem. The accepted successor is the
immutable stage `/storage/.aster-staging/aster-owned-books-landing2`, manifest
`8648fd13702aa2744b7cc498ed4667f76eb617fd7c099b37c1a2aa5beea8cbda`,
with recovery checkpoint
`/storage/.aster-checkpoints/aster-books-landing2-20261026`. Final verification
reports all six owned files exact, Home active, the refresh timer active and no
new Kodi error, fatal, traceback or XML-parser event. Production remains
unchanged.

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

Thirty focused tests cover real-date ordering, timezone normalization,
Kodi's bounded inaccessible sentinel, undated omission, signal-required
recommendations, progress privacy, media-type separation, recent-item exclusion,
action/authority separation, duplicate rejection, focus-safe rotation, exact
installation, rollback and optimized-Python checks. The complete Kodi v2 suite
passes 1,214 tests normally and optimized; all 113 skin-tool tests also pass in
both modes. The one existing Mac-only skip is unchanged.

## Cross-media visual close-out

The final native 3840×2160 comparison found the accepted Music and Books
landings visually coherent, but Media's seven destinations after Search were
still using the narrower pre-Acquisition geometry. Kodi therefore truncated
most captions even though all routes were correct. The correction preserves
every control ID, action and focus edge; keeps Search and the 24-hour clock in
their accepted positions; uses the complete safe span between them; and moves
only the destination captions one optical type step smaller.

The active immutable HP layer is
`/storage/.aster-staging/aster-media-top-rail1`, manifest
`151c240abc66555d86bdb7a018b50bef774f29029be111fbb1a87ebed2abc771`,
with recovery checkpoint
`/storage/.aster-checkpoints/aster-media-top-rail1`. Native 4K evidence shows
TV Shows, Movies, Archive TV, Archive Movies, Collections, Requests and YouTube
in full with no clock collision. The exact active member and parent Acquisition
layer verify, no player remains open, and Kodi's trailing log has no error or
fatal event. Five focused tests pass normally and optimized; the full 1,219-test
v2 suite passes with the one existing skip. This closes the landing-page visual
comparison while leaving Acquisition Hub service activation as M7a's remaining
work.
