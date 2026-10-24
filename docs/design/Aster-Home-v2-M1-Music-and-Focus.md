# Aster v2 M1 - music inventory and interaction contract

Status: local prototype, 2026-10-23. Governing project:
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

Inventory and pure policy tests are complete. M1 is not closed: build local
visual/focus prototypes, confirm category/alias presentation and compile the
bounded HP deployment/rollback proposal. No v2 code is installed on HP and no
production change is authorized. Keep the v1.1 release manifest reproducible.
Before actual playback tests, checkpoint affected queue and per-user state;
prefer disposable fixtures and restore measured test effects explicitly.
