# Aster v2 M1 - music inventory and interaction contract

Status: local design accepted; read-only catalogue adapter validated, 2026-10-23. Governing project:
[Aster Home v2](../projects/Aster-Home-Version-2.md).

## Live inventory (read-only HP Kodi index)

Two complete reads on 2026-10-23 each returned 1,335 albums and 17,113 songs.
Pagination fetched the entire index in 1,000-row pages, not the existing UI's
500-song limit. Queries used only local Kodi AudioLibrary reads over existing
SSH; no title/path, token, source media or listening history was exported.
Inventory took about 0.55 seconds. Source metadata remains unchanged.

The genre directory contains 21 labels. Six dominant categories are already
the owner's broad classification; 15 legacy labels remain alongside them.
Do not split broad labels at their commas or the R&B ampersand.

| Proposed display category | Track memberships after exact alias mapping |
|---|---:|
| Pop, Electronic & Hip-Hop | 4,308 |
| Jazz, Blues, R&B & Soul | 4,365 |
| Rock & Alternative | 3,919 |
| Country & Folk | 3,782 |
| Christmas | 585 |
| Classical | 174 |
| Other / unclassified | 8 |

These are memberships, not mutually exclusive track counts: a multi-genre
track may appear in more than one category. The seventh tile is a truthful
fallback for eight unmatched tracks, not an invented seventh music genre.
Keep those tracks playable and eligible for ordinary shuffle. Twenty-six
tracks lack direct genre tags; album inheritance resolves most of them.

### Exact proposed legacy aliases (presentation only)

- Pop, Dance-Pop, Alternative Pop, Synth-Pop -> Pop, Electronic & Hip-Hop.
- Funk, New Jack Swing -> Jazz, Blues, R&B & Soul.
- Rock, Pop Rock, Alternative Rock, Funk Rock, Soft Rock -> Rock & Alternative.
- Country, Country Pop, Country Rock, Americana -> Country & Folk.

Existing canonical track tags win for browse membership; inherit album tags
only when the track has no recognized category. Preserve intentional multi-genre
membership. These exact aliases are reviewable UI policy, never an instruction
to retag audio files or overwrite Jellyfin metadata.

## Shuffle all except Holiday / Christmas

Live direct Christmas classification covers 585 tracks. Seventy-four albums
are tagged Christmas, containing 765 tracks; 180 of those would be missed by
track-only exclusion. The tested combined rule therefore excludes 765 and
retains **16,348 eligible tracks**, including eight uncategorized tracks.

- Exclude when either track or parent album has a holiday classification.
- Match explicit holiday/Christmas/Xmas/X-mas/Noel/Noël genre aliases, with
  Unicode normalization and word boundaries. Only Christmas is currently
  present; other aliases are defensive handling, not new live facts.
- Do not inspect the title to decide: an ordinary song named Holiday must
  remain eligible unless its classification says otherwise.
- A Christmas-classified compilation is excluded at album level even if a
  constituent track is tagged Jazz/Rock. Before deployment, review that
  inheritance policy rather than silently making compilation exceptions.
- Require complete song and album snapshots. Abort on missing/duplicate IDs,
  missing parent album metadata or incomplete pagination. Do not silently
  shuffle the first page, assume unseen albums are non-holiday or clear the
  user's queue before validation succeeds.
- Shuffle on explicit action, using Kodi's real queue/state at integration.
  Keep current-track behavior defined; never overwrite a saved playlist.

The local pure prototype lives under `services/kodi/v2/`, outside the four v1
add-on roots. Eleven tests cover exact categories/aliases, malformed inventory,
direct and inherited exclusion, missing genres, mixed classifications, title
false positives, full 17,113-track coverage and non-mutation. A source-local
run of that same policy against the real inventory independently reproduced
16,348 eligible / 765 excluded. No playlist/playback command was issued.

## Music page interaction contract (prototype specification)

Header destinations: Albums, Artists, Songs, Playlists, Genres. Keep the
product logo in its accepted header slot. Shuffle all (no holiday music) is
an explicit music action, not a seventh genre or a hidden long press.

Genres opens the seven-category presentation above; each category can expose
Albums / Artists / Songs and Play / Shuffle with retained context. Christmas
remains deliberately browseable and playable; it is excluded only from the
dedicated whole-library non-holiday action. Never hide it from the library.

Remote focus contract:

1. Vertical tile movement preserves the visible column; clamp only when the
   next row is shorter. Do not jump to an old selected item in another row.
2. Left at the first content column opens the rail and immediately focuses
   Music. Back closes a temporary overlay before moving to its parent.
3. OK on an album/playlist opens its player; OK on a track plays that track.
   No floating action button that steals selection when scrolling upward.
4. Genre detail returns to the same genre and scroll position. Player exit
   stops media and restores source focus; v1.1 episode actions are unchanged.
5. Use modest focused scale, visible warm-gold/sage edge and contained artwork;
   no black title slabs, clipped halos, exposed square corners or moving labels.
6. Replace stone texture with restrained flat/material fills on controls,
   preserving approved Aster art/icons and the accepted TV colour identity.

## Gates and next work

Inventory and pure policy tests are complete. The isolated
[visual/focus prototype](../../services/kodi/v2/prototype/README.md) now uses
the supplied Aster assets, restrained texture-free controls, seven category
tiles and an explicitly simulated non-holiday shuffle action. It makes no API
or playback calls. Ten focus-model checks and Chromium interaction checks pass:
short-row column restoration, rail entry with Music immediately focused,
hero entry, search/empty/clear and modal return focus. All images load; lower
tiles clear the footer at 1080p and proportional 720p has no horizontal overflow.
The screenshot was visually reviewed. Eleven policy and three unchanged v1
package tests also pass. Browser simulation is not live Kodi/G20 validation.

M1 is not closed: confirm the visual/category/alias presentation and compile the
bounded HP deployment/rollback proposal. No v2 code is installed on HP and no
production change is authorized. Keep the v1.1 release manifest reproducible.
Before actual playback tests, checkpoint affected queue and per-user state;
prefer disposable fixtures and restore measured test effects explicitly.

## Read-only catalogue adapter — 2026-10-23

The owner accepted the visual prototype and directed continuation. New local
`services/kodi/v2/music_catalogue.py` injects a read-only Kodi RPC transport,
fetches complete pages and builds category-to-song/album/artist membership.
Search/pagination use that verified full index rather than truncate the source
to the first 500 titles. Two complete reads must match before publication;
this is optimistic consistency, not a claim of a transactional RPC snapshot.
Bounds: 100,000 songs, 10,000 albums/artists, pages at most 2,000 records.
Only indexed IDs, labels and classification/relationship fields are retained;
unexpected fields and media paths are discarded. No RPC error text is exposed.

Thirty-one v2 tests pass (20 adapter, 11 policy), including the full 17,113-song
fixture, changing totals/tags, duplicates, missing references, explicit empty
libraries, partial reads, private-field removal and browse-copy independence.
Ten focus-model and three immutable v1.1.1 packaging checks also pass. The
adapter has no player/queue/file write API. It runs from stdin memory for live
validation, not as an installed add-on. No source metadata was exported.

### Real HP edge case and handling

The initial strict read rejected a real page mismatch: GetSongs requested with
artist IDs reported a 1,000-row range but returned 998 rows. A basic genre/
album-ID query returned all 1,000. Read-only SQLite aggregate diagnosis found
23 songs with no `song_artist` credit row and zero dangling artist references;
per-item detail lookup also rejected the two omitted sample IDs. Changing sort
did not fix it. No database repair or sync/reset was attempted.

The adapter now requires a complete basic page for that same range, checks all
enriched rows agree on identity/classification, and preserves omitted tracks
with explicit unavailable artist credit rather than guessing an artist or
dropping music. The fallback is capped at 128 omissions per pass. A short basic
page, changed limits, duplicate ID or inconsistent metadata still fails closed.
Category and browse results expose uncredited-song counts for an honest UI
notice; those tracks remain in Albums/Songs and normal shuffle eligibility.
They do not create a fictional artist card. No database version/path is baked
into the runtime adapter: SQLite was diagnostic only.

The upstream [Kodi 21.3 AudioLibrary implementation](https://github.com/xbmc/xbmc/blob/21.3-Omega/xbmc/interfaces/json-rpc/AudioLibrary.cpp)
is the API-boundary reference; actual HP responses, not an assumed upstream
fix or OS upgrade, determine the handling above.

Live two-read validation resolves 1,335 albums, 1,042 artists and all 17,113
tracks; 16,348 shuffle-eligible / 765 excluded, matching the previous policy
inventory. It explicitly reports the 23 unavailable credits. Two independent
complete two-pass builds took 3.181/3.187 seconds; refresh must be explicit/bounded, not repeated
on every focus change. Art loads should remain lazy for visible items.

| Category | Albums represented | Known artists | Missing-credit tracks |
|---|---:|---:|---:|
| Pop, Electronic & Hip-Hop | 340 | 458 | 1 |
| Jazz, Blues, R&B & Soul | 360 | 299 | 0 |
| Rock & Alternative | 283 | 138 | 5 |
| Country & Folk | 315 | 221 | 0 |
| Christmas | 74 | 106 | 14 |
| Classical | 15 | 16 | 0 |
| Other / unclassified | 2 | 1 | 3 |

These are overlapping memberships, not distinct library totals. The alias and
inherited holiday policy remain reviewable before live queue integration.

## Bounded HP pilot proposal — not yet installed or authorized

Next implementation is a separately identified **read-only Music lab script**
(`script.astermusic.v2lab`), not a new production skin or replacement of the
four v1.1.1 add-ons. Its own WindowXML view uses the accepted 1080p layout and
existing supplied Aster assets/fonts. Launch explicitly as a lab tool, without
changing Home navigation, the active skin, G20 mapping or autostart. Build/test
the package locally before requesting the following live approval.

- Target only HP `192.168.1.140`; BOSGAME stays on v1.1.1. Verify hostname,
  current package hashes and no active playback immediately before testing.
- Capture/verify private add-on registration/GUI/keymap checkpoint and any
  pre-existing lab-addon directory. Do not overwrite a different existing lab
  install. Register only the isolated script, launch the view, then close it
  back to the same v1 page. A skin/profile switch is not part of this pilot.
- Read the existing per-user Kodi music index through the adapter. Seven genre
  tiles open Albums / Artists / Songs views with search, real empty/error and
  unavailable-credit notices. Keep full-index loading outside focus handlers;
  failed refresh never replaces a valid prior view with a fabricated empty list.
- This first pilot does not play, shuffle, clear a queue, edit/save playlists,
  retag files, invoke voice, add credentials, subscribe or download media.
  The non-holiday shuffle control may show its eligibility preview but must
  clearly say it does not play yet. Queue actions require their own later gate.
- Validate G20-only OK/Back/row/rail restoration, stable selected category and
  filters after returning, known uncredited tracks retained, cancelled/failed
  refresh, artwork fallbacks and 1080p/scaled-4K readability. Confirm ordinary
  Aster still works after closing the view and after a normal Kodi restart.
- Rollback disables/removes only the new lab addon and restores checkpointed
  registration if required. Never restore another client's credentials/watch
  database or overwrite the installed v1 add-on trees. Retain immutable v1.1.1
  packages and the existing private recovery archives independently.
- No new service/port/identity/DNS/firewall/NetBox/Beszel object or spoken output.
  Kodi/refresh health remains service-native. Record timing and truthful error
  codes, not titles, media paths, tokens or a persistent exported library.

Open gates: build the isolated Kodi pilot; approve its exact HP install/launch
checkpoint procedure; verify actual G20 behavior. Visual acceptance is recorded,
but neither a browser prototype nor passing adapter tests closes those gates.
