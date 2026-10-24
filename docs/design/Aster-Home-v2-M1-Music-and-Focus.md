# Aster v2 M1 - music inventory and interaction contract

Status: HP-only normal Music pilot with enforced playback/queue checks;
physical remote/listening walkthrough pending; main-page integration is active,
2026-10-24. Historical inventory/design evidence below is dated 2026-10-23;
the project's latest evidence/resume point governs deployed state. Governing project:
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

Those were the initial read-only gates. The later approved HP pilot is now
installed with normal playback, queue safeguards and explicit native checks;
see the governing project's dated evidence rather than treating the earlier
assert-dependent results as accepted proof. Physical remote/listening and final
integration remain open. No production promotion is authorized.

## Current HP pilot operator note — 2026-10-24

Open **Add-ons → Program add-ons → Aster Music v2 Lab**. Normal Music navigation
still uses v1; the pilot has not silently replaced the Recently Added front
page. Existing Kodi/Jellyfin sign-in is used; no new login or API key.

- Genres contains seven agreed groups. Christmas remains browseable; only
  **Shuffle all · no holiday music** excludes track- or album-tagged holidays.
- Albums/Playlists/Songs open the stripped-back player without autoplay.
  Confirm initial Play or whole-library Shuffle. OK on an already queued track
  changes to that exact occurrence; the green playing marker follows it.
- Floating transport icons sit below the square cover. Up from Play/Pause
  enters the seek bar: arrows preview, OK applies, Back cancels that preview.
  The small double-arrow icons seek ten seconds.
- Menu on a track offers Play, Play Next and Add to Queue. When the displayed
  order is the actual owned queue, Remove targets that exact occurrence and
  requires confirmation. The currently playing occurrence cannot be removed.
- Menu on transport offers private Save, factual Audio details, Shuffle/restore
  order and confirmed Stop-and-clear. Turn shuffle off before queue edits.
  Save creates a **new private playlist under the signed-in account**, usable
  on its other devices; it does not share with all household users or overwrite
  existing playlists. A duplicate name or uncertain-save warning is a refusal,
  not an invitation to retry automatically.
- Back or Home stops owned playback and safely cancels background loading.
  Exit can take several seconds while outstanding writes/stop callbacks finish.
  Unrelated external playback is refused, never silently replaced.
- Missing durations remain unknown; indexed durations are shown when present.
  Source codec/sample-rate labels are not measurements of receiver output.
  Subtle artwork colour uses only the existing local thumbnail cache; missing
  cache/decoder falls back to neutral stone. No extra art is downloaded for it.

If a recovery warning appears, stop testing and retain its checkpoint; do not
clear/replay a queue that changed externally. Candidate58 and its exact recovery
references are in the project record. Normal-navigation integration, physical
G20/listening acceptance, longer soak and production promotion are separate
remaining gates. No additional automated server create/delete trial is implied.

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

## Bounded HP pilot — approved and deployed 2026-10-23

The pilot is a separately identified **read-only Music lab script**
(`script.astermusic.v2lab`), not a new production skin or replacement of the
four v1.1.1 add-ons. Its own WindowXML view uses the accepted 1080p layout and
existing supplied Aster assets/fonts. Launch explicitly as a lab tool, without
changing Home navigation, the active skin, G20 mapping or autostart. The owner
explicitly approved deployment in the continuation request; the package was
built/tested locally before executing the following bounded installation.

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

Open gates: physical G20/sofa walkthrough and native visual acceptance. Browser
design acceptance and automated native input checks do not substitute for the
owner's hardware walkthrough. Live queue actions remain a later approval gate.

### Installed artifact and validation

Source: `services/kodi/v2/script.astermusic.v2lab/`, plus the isolated model,
policy and catalogue modules. Deterministic build:

```sh
python3 services/kodi/v2/build_lab.py --output /path/to/new-empty-pilot-directory
python3 -m unittest discover -s services/kodi/v2 -p 'test_*.py'
```

Final immutable artifact is
`services/kodi/dist/aster-music-v2lab-0.1.0-candidate2`; its seven deployed files
and archive checksums are tracked in
`services/kodi/v2/releases/music-v2lab-0.1.0.json`. The supplied Music icon is
copied byte-for-byte; runtime logos, masks, controls and fonts are the existing
v1 assets, not recreated graphics. Native view keeps the accepted neutral/
green/gold identity, product-logo slot, 24-hour clock pill, thin focus outlines
and square detail artwork. Genre tiles have two rows; album/artist/song pages
show four square tiles per page with search and explicit Previous/Next.

50 local tests pass: 31 catalogue/policy, ten pure browse/focus and nine runtime/
geometry/package tests. Three v1.1.1 deterministic package tests remain green.
Native callbacks are asynchronous; a regression explicitly verifies preferred
column survives the deferred focus callback after the short genre row. The
adapter does not reload on focus changes; only visible detail art is requested,
with a bounded 128-entry in-memory art cache. No title/path/token export or disk
library cache is created by the script. Kodi's ordinary artwork cache is reused.

HP-only installation used one clean Kodi stop/start. Verified pre-install
checkpoint of registration database, GUI settings and remote map (three files):
`/storage/.aster-checkpoints/aster-before-music-v2lab-20261023/registration-gui-keymaps.tar.gz`,
SHA-256 `188c5392addb3efcfc6fdeda79e820aabe2ae390e6ab1278081ce997dd7449a4`.
Independent 0600 off-device copy is in
`/Users/jelliott/lab/private-backups/aster-tv/hp/2026-10-23-v2-music-lab/`.
An isolated restoration of the registration database passed SQLite quick_check;
the temporary restored copy was removed, not applied to the live database.
Installed/enabled-map comparison changes only the new lab ID. All 136 selected
AV/language settings and the exact G20 keymap remain unchanged; all 153 v1.1.1
files match before and after the pilot. No BOSGAME command or write was made.

Candidate1 was installed first; native visual review identified inconsistent
focus-corner scaling and missing current-tab emphasis. Candidate2 changes only
the lab XML, checkpointed under
`/storage/.aster-checkpoints/aster-music-v2lab-before-style-20261023/`; no further
restart or changes to ordinary Aster were required.

Two independent native UI paths passed using Kodi input and the **actual existing
G20 Select dispatcher** (not a claim that a person pressed the hardware remote):

1. Genre column down/up, immediate Music rail focus, Back, Rock Albums/Artists,
   search keyboard, truthful empty result, clear, retained genre, shuffle
   eligibility dialog, cancelled refresh retaining last-good catalogue,
   successful refresh and return to ordinary Aster Home.
2. Other / unclassified Albums/Songs, all eight songs retained with an explicit
   three-track unavailable-credit notice, read-only item inspection, next page
   preserving the selected column, Back to the same genre and ordinary Home.

Both paths leave active playback empty and the existing music queue byte-for-
byte equivalent at the RPC-result level. No song was played or marked listened.
The retryable live smoke workflow is retained at
`services/kodi/v2/tools/live_pilot_smoke.py`; run only on the approved HP with
the pilot already open, with the remote untouched. It closes back to Home.
Early harness retries were caused by firing keys before view focus settled and
assuming different Kodi dialog names; the final explicit focus/dialog checks
passed. No runtime Python traceback was observed.

The pilot is left open on HP for owner review. Kodi and the six-hour catalogue
refresh timer are active; Kodi reports zero automatic restarts. No new service,
port, account, subscription, schedule or spoken output is introduced. Existing
Kodi health is the service-native monitoring handoff; no new Beszel/NetBox/DNS/
firewall object exists. AI administration uses the already authorized bounded
HP SSH/Kodi path, not a new static key or autonomous service identity. Wiki/
mirror publication and broader release acceptance wait for the owner walkthrough.

### Owner handover and recovery

The HP now shows **Aster Music / Read-only v2 Lab**. Choose a genre, then Albums,
Artists or Songs. OK inspects a tile; it intentionally does not play. Search
opens Kodi's keyboard; Clear search restores the category. Next/Previous change
pages. Back returns to the previous genre view, then ordinary Aster. Left from
the first tile opens the small lab rail with Music immediately selected; Back
closes that rail first. The shuffle control explains eligibility only. Playlists
explicitly directs users to existing ordinary Aster Music; it is not a fake
playlist catalogue. Refresh may be cancelled without erasing the current view.

There is deliberately no permanent Home shortcut or autostart. To reopen from
the Mac using established HP SSH access:

```sh
ssh root@192.168.1.140 'kodi-send --action="RunScript(script.astermusic.v2lab)"'
```

No authentication/key setup is needed beyond that existing connection. A read
failure produces a safe error code; do not reset/sync-delete the real library
to fix it. Close the pilot and ordinary v1 Music remains available.

Rollback normally means disable/uninstall only `script.astermusic.v2lab` through
Kodi after closing it; its immutable ZIP allows reinstall. A verified registration
checkpoint is retained for exceptional recovery under a stopped Kodi session,
but must not overwrite later unrelated addon changes. Do not restore watch
databases, another client's profile or the v1 add-on trees. Further HP/production
changes, playback/shuffle implementation and metadata repairs need their own
bounded milestone approval. No push is authorized by the deployment approval.

### Owner review, clock correction and offline queue planning — 2026-10-23

Jason accepted the native appearance except the clock's alignment. Candidate3
adds the missing vertical centring to the existing horizontally centred label;
the pill's dimensions, gold outline and 24-hour format are unchanged. Only the
lab XML was replaced after verifying the previous candidate and retaining its
exact XML under
`/storage/.aster-checkpoints/aster-music-v2lab-before-clock-20261023/`.
The pilot was closed and reopened without restarting Kodi. A native 3840×2160
screenshot confirms the correction; all 153 installed v1.1.1 files still match
their baseline. Candidate1/2 artifacts remain immutable. Candidate3's ZIP SHA-256
is `730d11796cfe421402df895f4ff30d85c078e4151eb67cc90ac3fb4e36faa380`.
No production changes or playback occurred.

Continued locally with `services/kodi/v2/music_queue.py`, an **offline proposal
model only**. It is deliberately excluded from the pilot bundle, imports no
Kodi API and has no network, persistence or write adapter:

- Play Next inserts after the identified current track without moving it;
  unknown current position fails closed. Add to Queue preserves the current
  position and existing duplicate/order semantics.
- Replace Queue is explicit and does not imply starting playback. Empty or
  invalid selections and oversized combined queues are rejected.
- A fingerprint guards against stale previews when queue order, duplicates or
  current position change. This is not an atomic transaction or permission to
  clear a live queue; a future adapter must re-read and separately handle races,
  interruption, confirmation and recovery.
- Shuffle proposals use the full validated catalogue, excluding direct and
  album-inherited holiday classifications, never title words. Deterministic
  seeds make tests reproducible. An all-holiday catalogue yields an empty pool,
  which cannot replace the queue.
- Callers must supply verified selection order. Alphabetical browse results
  are not a substitute for album disc/track ordering; that resolver is still
  outstanding. Mixed file/stream queues are not represented and must not be
  silently converted or overwritten by a future adapter.

61 v2 tests (including ten queue tests), ten focus-model checks and three
unchanged v1 packaging tests pass. A Python 3.9 annotation compatibility issue
was caught and corrected locally before completing validation. No speech or new
infrastructure is introduced. Next work is a local ordered album resolver and
queue interaction/confirmation UI; live player/queue integration remains a
separate bounded approval gate, including classification policy and recovery
testing. M1 is not declared complete from visual acceptance alone.

### Ordered album selection — 2026-10-23 continuation

The requested push of saved work through `40f14133` completed to Forgejo on
`codex/aster-home-eh001-m0`; the GitHub protection mirror independently advertised
the same full ref, `40f14133f5bf452ad3539071bf6a55b51e2e1376`.

Added local `music_album.py` for the next playback milestone, **not installed or
bundled in the read-only pilot**. It requests only album ID, disc, track and
duration through `AudioLibrary.GetSongs` (title labels are returned by Kodi),
avoiding paths and the problematic artist-credit join. The HP runtime's
`JSONRPC.Introspect` confirms those fields in API 13.5.0. It requires exact
membership from the complete catalogue's album association, not just the songs
visible in one genre/search/page. Two bounded complete reads must match before
producing an immutable selection sorted by disc then track. Sets larger than
500 tracks are paginated, not truncated; the explicit safety ceiling is 10,000.

Missing track numbers, duplicate positions, mixed known/unknown discs, missing
parents/identities, changed membership or read errors fail with safe codes.
All-zero disc tags remain unknown and may be ordered only by unique track tags;
they are never presented as invented Disc 1 metadata. Returned order feeds the
existing offline Play Next proposal unchanged, preserving the current queue's
duplicates and current position. No player or queue write adapter exists.

Retained `tools/validate_album_order.py` generates a stdin-only, method-allowlisted
HP probe. It installs nothing, writes no remote files, sends no input and prints
only aggregates. A live read indexed all **17,113 songs / 1,335 albums** and
sampled five albums: three multi-disc albums ordered successfully; two refused
with `album-track-number-unavailable`. The complete basic index contains **six
tracks with track number zero, across two albums**. This is a metadata limitation,
not missing content; do not retag or repair the library automatically. A future
album screen should explain this and retain individual-song access rather than
silently guessing album order. Playback/queue RPC results matched before/after.
These five samples are not exhaustive album-order acceptance for all 1,335.

76 v2 tests, ten focus checks and three unchanged v1 package tests pass. Local
coverage includes multi-disc order, 601-track pagination, missing credits,
malformed numbering/pages, same-count changes, error sanitisation and the
generated probe's write-method denial. HP candidate3 remains unchanged and
production remains untouched. No speech, service, port or credential is added.

Next bounded milestone: local album/queue confirmation UI, then seek approval
for an HP-only player candidate with queue checkpoint/recovery and explicit
Replace versus Play Next/Add to Queue behavior. Before enabling live writes,
resolve classification review, mixed file/stream queue handling, races during
mutation and Back/exit-stop behavior. This continuation does not authorize that
deployment, server metadata repairs, production promotion or another push.

### Stream A native album / queue-preview milestone — 2026-10-23

Jason explicitly converted this Music continuation to Stream A and held all
Forgejo pushes. The project charter now enumerates HP-only add-on updates,
checkpoints, native tests and local commits; production/service/credential/
metadata changes and live playback/queue writes remain excluded pending their
specific gate. Earlier Stream M statements above are historical evidence, not
the current per-change authorization model.

Delivered candidate6, an eleven-file deterministic isolated pilot. Its SHA-256
is `0cc540a7bb7d29b389c10f37dfbf82558d7a3cc1121d00c9ff29a734843b4c00`;
the [release record](../../services/kodi/v2/releases/music-v2lab-album-preview-0.1.0.json)
identifies the artifact and checks. Unlike earlier snapshots, the pilot now
**bundles the pure album/queue proposal modules**, plus a new read-only queue
adapter. No write adapter is present; the runtime's method allowlist still
rejects Player.Open/Stop, Playlist.Add/Clear and metadata/settings writes.

Album OK opens a separate native screen with supplied Aster logo and centred
24-hour clock in the same header positions, square artwork left, album title /
track count, and an unboxed track list right using the existing synopsis font.
Disc/track tags determine order and durations are shown. Unknown discs are
labelled unavailable, never guessed. Left reaches compact Play Next, Add to
Queue and Replace Queue controls; Up/Down returns to the track list. All three
are clearly described as previews and only show the proposed effect. Track OK
opens the same options for that track. No sound is started or queue changed.

`queue_reader.py` makes two matching bounded complete song-ID reads and checks
the active player's queue/position. Repeated IDs/order are retained. Streams,
file-only items, unsupported players, changing queues, incomplete pages and
out-of-range positions fail closed with useful messages. No path is requested
or retained. Idle Play Next explains that no current track exists; Add and
Replace can still preview an idle queue. This is not a transaction or a claim
that a future clear/rebuild operation can preserve an active stream.

Native testing found an actual Back-focus reset: `defaultcontrol always=true`
overrode the originating tile when returning from the child window. Candidate5
changed the parent's default to `always=false`; the regression test and real
Back/reopen path now pass. The first sampled Rock album also exercised the
known missing-track-number explanation; this was truthful library metadata,
not a player failure. Candidate6 only clarified unknown-disc copy/module
documentation; the whole native path passed again.

Validation: **90 v2 unit tests**, ten focus-model checks, three unchanged v1
package checks; existing browse/rail/search/paging/refresh smoke and the new
`tools/live_album_smoke.py` pass. The new path uses the real G20 Select dispatcher
but is not evidence of a physical remote press or a human listening test.
Player/queue RPC results matched before/after. All 153 v1.1.1 files hash-match.
A native 3840×2160 screenshot was inspected for art, list, control/clock layout
and clipping. The final album is left open on HP, no audio active. BOSGAME was
not contacted or changed. No speech, infrastructure, accounts, ports or schedule
changes; Kodi remains the native health surface.

Before expansion, candidate3's seven installed files and ZIP were verified,
the full old add-on tree retained under
`/storage/.aster-checkpoints/aster-music-v2lab-before-album-20261023/`, and the new
tree switched only after all hashes matched. Focus XML and final-copy updates
have separate `before-album-focus-20261023` and `before-album-final-20261023`
checkpoints. Candidate5's eleven-file recovery ZIP was independently copied to
the Mac, restored into a disposable directory and every file hash checked.
All prior immutable candidate ZIPs remain available locally and on HP. No Kodi
restart or registration/keymap/settings change was needed.

Recovery: close the pilot and restore only its verified prior whole add-on
tree/ZIP, not the v1 skin, profile or watch databases. Candidate3 is the last
owner-visually-accepted browse-only fallback; candidate5 is the immediate
eleven-file fallback. Do not merge seven-file rollback contents over an expanded
tree and leave stale modules behind. Verify the chosen manifest after restoring,
then reopen; stop on a failed checkpoint rather than resetting Kodi.

**Next owner decision / autonomous stop:** accept (or amend) the seven proposed
Music groups and track-plus-album holiday exclusion, then authorize a first
HP-only live player/queue test using at most three indexed songs while idle,
with a verified queue checkpoint/restore. Ordinary test playback may update
those songs' listening history through existing integrations; unlike the
read-only pilot, that side effect is not promised reversible. No production,
saved-playlist, metadata-tag or infrastructure changes are included. Once
accepted, implement the smallest live adapter with explicit replace confirmation,
no silent mixed-stream queue conversion and tested stop-on-exit. Full-library
16,348-track shuffle/soak is a later performance check, not part of this first
three-song test. Category/exclusion policy remains proposed: Pop/Electronic/
Hip-Hop; Jazz/Blues/R&B/Soul; Rock/Alternative; Country/Folk; Christmas;
Classical; Other/unclassified. Current holiday preview excludes 765 and retains
16,348 tracks. No Forgejo or other remote Git writes were performed.

### Accepted policy and bounded live trial — 2026-10-23

Jason explicitly approved both outstanding decisions. The seven displayed
groups, observed legacy aliases and direct/inherited holiday exclusion are now
the accepted v2 presentation policy; do not retag source files. The first live
HP gate is restricted to three chosen indexed song IDs, a three-item queue,
idle/empty baseline and a verified private checkpoint. Listening-history effects
from normal test playback were disclosed and accepted, not manually reverted.

The pilot is still read-only by default. `music_trial.py` implements a temporary
HP-only capability (`live-trial.json` in the add-on's private profile directory),
positive IDs/expiry validation, exact write parameter/method allowlisting,
checkpoint-before-mutation, serialized own-client actions, current item/queue
ownership checks and explicit replacement confirmation. Writes are limited to
music playlist 0 and player 0: Add/Insert/Clear, Open, explicit PlayPause and Stop.
Paths, other playlists/players, broad options, settings, media-tag and saved-file
writes are rejected. Add/Play Next preserve the current item and do not clear or
restart it. Replace requires idle playback and never auto-starts; Play explicitly
confirms queue replacement. A missing, invalid, expired or wrong-host capability
does not enable live controls. Expiry blocks new live actions; cleanup remains
permitted. This is not a background expiry watchdog or an authentication system.

The native screen exposes compact Play/Pause, Stop, Next, Add and Replace only
in this bounded mode. Track selection offers the equivalent single-track actions.
Back cleans up only owned playback and restores the initial empty queue. Late
input on a closing window is ignored, close is idempotent, and cancellation of a
popup does not become a second Back exit. The short native-release debounce is
only applied after cancelled popups, not positive Play confirmation. Unrelated
queue/player changes stop mutation and retain the checkpoint; no blind restore
over an unknown stream is attempted. Single-client cooperative operation is still
required; Kodi's separate read/write calls are not transactional.

#### Native discovery and corrective evidence

Initial attempts exposed timing assumptions, and were **not** reported as passes:

- Kodi can announce an active player before publishing a current song ID; the
  test now waits for actual identity/time rather than indexing a missing field.
- Double close through Back and the modal `finally` path reset focus. Cleanup is
  now idempotent. Native modal-release input and late Select are guarded/tested.
- What looked like Cancel Replace losing the queue was actually the installed
  Jellyfin add-on's `jellyfin_kodi/monitor.py:110–120`: it sleeps 3,000 ms after
  `Player.OnStop`, then clears the playlist when idle. A queue-only probe proved
  cancellation itself preserves the queue. The isolated trial adapter now waits
  for that known cleanup after its own Stop and accepts only the exact expected
  queue or empty baseline. Different queues/streams still fail closed. **No
  Jellyfin source or setting was changed.** Stop can take about three seconds to
  finish its GUI cleanup; durable queue intent/nonblocking cleanup remain M3 work.
- The exit test originally sent Back during startup as soon as identity arrived.
  It now waits for actual ready-player status/time, then separately for native
  window closure before reopening. Normal playback exit passes. Cancellation
  during early loading is explicitly **not yet accepted** and remains a later
  hardening case; do not infer “every exit at every startup instant” from this run.

All early attempts removed their temporary capability and independently verified
no player/original empty queue before another mutation. A conservative recovery
flag during the unhandled delayed clear was acknowledged only after independent
baseline verification, recorded privately as `recovery-verified-after-cancel.json`.
No unknown queue was overwritten or failed checkpoint bypassed.

Final **candidate13** ZIP SHA-256:
`7cd0a17e7774e8c66a12d6b2b67146414b486d8cf437ab36887237af1f928be7`.
Twelve installed file hashes match. `tools/live_player_trial.py` completed with
exit 0: cancelled Play leaves the queue unchanged; confirmed Play starts the
first approved track with advancing time; Pause/Resume work; adding the third and
inserting the second produces the exact three-ID order without changing the
current item/time; Stop acknowledges Jellyfin cleanup; idle queue is repopulated
for Cancel/confirm Replace, which does not auto-play; ready-player Back stops,
restores the empty baseline and originating tile; capability is removed; album
reopens read-only. Only the first track actually played; the other two were
enqueued. No claim of audible output, every track decoding or physical G20 presses
is made. The actual G20 Select dispatcher was used for activation.

Validation: **107 v2 unit tests + all 144 unchanged v1 tests**, ten focus checks,
native read-only and complete live workflows. A native 3840×2160 live screenshot
was inspected for compact controls, cover/list layout and centred clock. The
post-check independently confirms original queue restored, no active player,
no live capability/recovery flag, default read-only state, all twelve pilot
files and 68 selected audio/display/locale values matching their checkpoint.
All 153 v1.1.1 files still match; Kodi active with zero automatic restarts.

Recovery artifacts remain under
`/storage/.aster-checkpoints/aster-music-live-trial-20261023/`: verified original
queue, test selection, AV fingerprint, per-candidate source checkpoints,
pre-trial candidate6 installed tree and recovery ZIP, and `trial-complete.json`.
The eleven-file candidate6 ZIP was independently transferred/restored and all
hashes checked in a disposable Mac directory. Immutable candidate7–13 ZIPs remain
in staging/local ignored dist; do not discard checkpoints for cosmetic cleanup.
Only the exact temporary capability was removed after the trial. The earlier
private v1 registration/GUI/keymap backup is unchanged.

The [live-trial release record](../../services/kodi/v2/releases/music-v2lab-live-trial-0.1.0.json)
is the current pilot handoff; the HP is left on read-only album detail. New speech,
services, accounts, ports and schedules: none. Existing Kodi health remains the
native monitor; no new NetBox/DNS/firewall object or derived wiki publication.
BOSGAME, v1 source, saved playlists and Jellyfin settings are untouched. No pushes.

Next approval is a broader HP full-album/catalogue playback and holiday-excluding
shuffle/performance trial, retaining private queue checkpoints. Before wider
acceptance, implement durable queue intent compatible with Jellyfin Stop, harden
startup/loading cancellation, finish now-playing/seek/output/queue controls and
obtain physical remote/listening/sofa evidence. This bounded pass does not close
M3 or authorize production promotion, 16,348-item stress writes or a Git push.

## Expanded Music trial — held after recovery, 2026-10-23

Jason subsequently approved HP-only full albums, full nonholiday shuffle,
queue-intent checkpoints and startup-cancellation hardening. Candidate14/15
adds exact batched writes, 20,000-item total/200-item request ceilings,
private atomic ID-only intent and explicit replay, plus a native cancellable
startup dialog with joined RPC worker (no abandoned writer/GUI calls in worker).
118 v2 tests + 144 unchanged v1 tests + ten focus checks pass locally.

Verified on HP: 11-track album order/playback/clock; cancellation before/after
Open; native startup Back cleanup, normal full-album start and Back return to
the same tile; explicit saved-intent replay following Jellyfin Stop. No human
listening/physical-remote acceptance claim, and full shuffle did not pass.

The broader test exposed two gates: one of the first 200 catalogue IDs cannot
be queued by Kodi; the HP music database has 23 songs without a primary artist
relationship. No records/tags were repaired or silently excluded. The proven
199-item owned batch was checkpointed and safely cleared. Separately, the
candidate15 repeated-album cancellation harness caused a Kodi SIGSEGV; top
frame is TCP JSON-RPC announcement code, exact cause unconfirmed. Native
in-process cancellation passed, but this is not proof bulk operations are safe.

Live testing stopped. HP is rolled back to candidate13 (12 member hashes and
off-device recovery ZIP verified), idle/empty at Home, no capability or recovery
flag. All 153 v1 files and 68 AV/language settings unchanged. One automatic Kodi
restart occurred; zero-restart evidence above refers to the earlier trial only.
Production and pushes untouched. Candidate15 is retained, not deployed/accepted.
The project outcome and new expanded-trial release JSON record exact private
checkpoint locations. A new risk decision is required for HP library repair
and bounded in-process retesting; M3 remains incomplete.

## Approved repair and in-process retest — 2026-10-23

Jason approved the HP repair and bounded retest. All 23 original song credits
were blank, so the repair restores only Kodi's canonical `[Missing Tag]` artist
relation, following its 21.3 native policy; no performer inferred from titles
or album artists. Exactly 23 rows inserted in `song_artist`, every other table
hash unchanged at repair commit. Stopped Kodi briefly; private SQLite backup,
independent rehearsal and off-device backup integrity/hash checks passed.
Jellyfin/source tags, mappings, settings and production unchanged. This is not
an automatic recurring repair: a future rebuild/sync should be re-audited.

Retired bulk TCP test transport, not patched Kodi. Exact crash trigger remains
unconfirmed; native in-process tests have no unexpected restart. The first
complete repaired run passed 16,348 exact eligible IDs / 765 holiday exclusions
but took 624.8s. Candidate17 reads the bounded queue in one page rather than
repeated full-list copies per 500-item page, retaining both complete matching
reads, exact order, 200-item write ceiling and external-state refusal. Retest
passed the same full order/membership and brief playback in 176.4s, plus replay,
startup cancellation and native full-album/Back workflows. One GUI harness
attempt encountered normal queue transition during Stop; fixed only that wait,
retained failure record, then reran successfully.

Unknown-tag placeholders remain uncredited in the UI, not real artist counts.
127 v2 tests, 144 unchanged v1 tests and ten focus checks pass. Candidate17 is
HP-only, default read-only; global Shuffle All remains an eligibility preview
pending acceptable loading behaviour. The project record contains exact hashes,
memory/RPC timings and private checkpoints. No production changes or pushes.

176.4s is still not acceptable button-to-audio latency. Next owner decision is
a narrowly bounded progressive-shuffle trial (small verified starting batch,
controlled background append, cancellation joins before Stop/restore), with the
existing ID-only and write ceilings retained. No physical listening/remote/soak
acceptance or M3 graduation is implied by these transport/correctness tests.

## Progressive Music continuation — 2026-10-24

Jason reaffirmed HP Music Stream A authority; the conversational progressive-
worker approval gate in the historical record above is superseded. Production
and remote Git writes remain held. No new service or speech integration.

The native shuffle player now starts a verified 25-song prefix, then fills the
remaining requested order with a single joinable worker. Default fill batches
are 50, below the unchanged 200/write and 20,000-total ceilings. Smaller batches
trade longer background completion for more responsive Pause and exit. Full
two-read identity/order checks remain; no abbreviated queue validation.

The same stripped-back album player presents a 200-row queue page, actual
current song/art/known artist, green current-song marker independent of focus,
Pause/Resume, Stop, Previous page, Next page and Current. Paging does not change
playback; selecting an already loaded song does. Unloaded selection explains
that loading is incomplete rather than pretending it played. Unknown credits
remain “Artist unavailable”; durations not yet known are not displayed as zero.

All native queue controls serialize through the owned session. Control workers
are joinable, never detached, and perform no GUI calls. Exit signals cancellation
before acquiring the queue lock, joins controls and the filler, stops owned
audio and restores the original empty queue. Global Home must also close the
hidden parent window and remain Home after cleanup. Unexpected external state
retains a recovery flag/checkpoint rather than overwriting someone else's queue.

Native 50-item-batch tests before the final Home-parent correction measured
Select-to-player 1.58–1.65s, Pause 1.33–1.45s, Back audio-stop 1.38s and full
Back/Home cleanup 5.02–5.41s. These are native dispatcher automation measurements,
not physical-remote or audible-quality acceptance. An earlier 200-item-batch
full fill passed exact order for 16,363 songs with 765 holiday exclusions, but
its longer control latency prompted the smaller batches. The final full-fill
and preservation evidence belongs in the project/release outcome after it
finishes; do not treat the still-running 50-item test as passed.

Final outcome: the 50-item full fill passed 16,363 exact ordered IDs / 765
exclusions, first player 1.102s and complete fill/sample 587.919s. Candidate30's
Back and stable-Home workflows both passed, with 1.65–1.84s native Select and
1.70–1.82s Pause. All 153 v1 files / 68 AV-language values remain unchanged;
queue empty, grants absent, hidden windows closed, Kodi active without an
unexpected restart. See the project outcome and progressive release record for
run IDs and archive identity. 143 v2 tests plus 144 v1 / ten focus checks pass.

Operator boundary: without its private expiring song-ID capability, the pilot
is read-only. Shuffle All explains eligibility, and ordinary Aster Music remains
available separately. No default/persistent live grant is installed. Temporary
native test grants are removed in test cleanup; private queue intent is retained
for diagnosis, never silently replayed. Candidate/recovery ZIPs remain separate
from v1 packages.

Next local player-control work includes a factual elapsed/duration display and
owned-player seeking; seek must check current song identity, seekability and a
known duration, preserve pause state, and never affect another player. Kodi 21.3
supports a typed `Player.Seek` value containing a time or seconds object:
[upstream schema](https://github.com/xbmc/xbmc/blob/21.3-Omega/xbmc/interfaces/json-rpc/schema/methods.json#L711-L797).
This is an implementation step within Music, not a new conversational approval
gate. It is not yet claimed as implemented or live-tested.

Follow-up implemented and tested on HP candidate32: thin progress line,
elapsed/total readout and compact text-style -10s/+10s controls under the main
player controls. Down from Pause/Stop reaches seek; Up returns, Left/Right
moves between seeks and Back/Home retains stop-on-exit. Unavailable duration
renders an em dash, unsupported seek explains without stopping valid playback.
No false zero duration, seek on another player, queue reorder or volume change.

Kodi PAPlayer resumes paused playback inside SeekTime. The initial candidate31
test caught that and failed safely; candidate32 rechecks native song/playlist
identity, restores pause explicitly, then re-verifies full queue ownership and
pause state. Do not infer that all decoder paths are silent during that native
seek transition; physical listening remains a family/sofa acceptance item.
Both paused-seek directions and native Back/stable-Home workflows passed;
151 v2 tests, 144 unchanged v1 tests and ten focus checks pass. Final screenshot
inspected with no overlap. Project outcome records real timings and failed-run
history; candidate30 and31 recovery artifacts remain available. The pilot still
returns to read-only when its temporary test grant is removed.

## Floating control-icon trial — 2026-10-24

Jason rejected the written pill row as heavy and too wide. Trial replaces it
with original monochrome transparent transport glyphs: charcoal at rest,
slightly larger green on focus, a small gold underline and a focused-action
caption. Native labels remain for accessibility; there is no button backplate.
All hit targets are >=64 units wide and the complete row is <=530 units, matching
the cover width. Cover itself stays 530 x 530 with centred `keep` aspect ratio;
non-square source art is fitted, not stretched or cropped to force a square.
Title/artist metadata now respects that same column width.

Shuffle icons, left to right: back 10 seconds, Play/Pause, forward 10 seconds,
Stop, previous queue page, next queue page, show playing song. The last three
are queue-navigation controls, not previous/next song. Read the focus caption.
Left/Right follows the visible order; Up/Down reaches the queue; Left from the
queue returns to Play/Pause. The focused caption updates immediately rather
than waiting for the one-second playback poll. Busy actions say “Updating
playback…” without replacing the visible icon with a word.

Album live-test icons: Play/Pause, Stop, Play Next, Add to Queue, Replace Queue.
Album preview has only the last three, labelled as previews in the caption.
This is still the isolated HP lab, launched from Programs → Aster Music v2 Lab,
using the existing Kodi library. Without the private expiring test capability,
it does not start music; a queue-preview dialog is intentional, not an apparent
successful Play. No permanent playback grant, production promotion or v1 change.
Back/Home during a live test still stops owned music and cancels its loader.

Glyph sources and transparent 128px PNG derivatives are bundled inside the lab;
`tools/build_control_icons.py` regenerates them deterministically. No new speech,
external service, raster-generation model, vendor change or remote keymap edit.

Native walkthrough automation passes real album Play/Pause/Resume/Stop/restart,
startup cancellation and Back, plus shuffle seeks, queue paging, actual-track
selection and stable Home exit. Final candidate36 and screenshots inspected;
154 v2 tests, 144 unchanged v1 tests and ten focus checks pass. The project log
retains the first failed transition test rather than claiming every attempt
passed; exact initial filler error was not captured and remains unproven.
Production remains independent and unchanged; physical remote/listening/sofa
acceptance is not inferred from native dispatcher tests.

## Current HP operator handover — 2026-10-24

This section supersedes the historical expiring-grant instructions above.
Only the HP lab uses the integrated v2 Music player; BOSGAME is unchanged.
No new login is needed: Music uses the existing signed-in Jellyfin/Kodi index.

1. Open **Music** from the normal side rail. The first page is still Recently
   Added. Its header has Albums, Artists, Songs, Playlists and Genres. Shuffle
   all is on the front hero below its details, not in the destination header.
   During loading, wait for the tiles and selection to become available.
2. Select an album, song or indexed Jellyfin playlist with OK. This opens the
   player without starting audio. Select a track or the floating Play icon;
   replacing the queue requires confirmation. Artists still opens that
   artist's albums. Local Kodi/smart playlists keep their original player.
3. On the player, the focused icon's caption explains its action. The transport
   group is centred beneath the album art: -10 seconds, Play/Pause, +10 seconds,
   Stop, Next track. A second centred row beneath it holds Play Next, Add to
   Queue, Replace Queue. Both rows sit below the scrub bar and within the cover
   width. Up/Down moves between rows; the focused action caption is on the right.
   Playlist and Shuffle artwork follows the playing song's album; missing art
   uses the standard placeholder rather than the previous album's cover.
   **Next track** advances playback; **Play Next** inserts
   the selection into the queue and does not skip the currently playing song.
   Add to Queue switches the list to the actual queue and updates its count.
   Adding while stopped does not start audio; Play starts that accumulated queue
   after confirmation without discarding the added tracks.
   The progress control supports a seek preview: Left/Right adjusts, OK
   applies, and Back cancels the preview before a later Back exits.
4. Genres opens seven truthful categories. Christmas remains browseable.
   **Shuffle all** specifically excludes holiday-tagged tracks and albums;
   it does not exclude songs merely because their titles contain “Holiday”.
   Confirm to start; loading continues behind the player and Back cancels it.
   Queue-page arrows browse the queue, not previous/next-song transport.
5. Menu on a track offers track/queue actions. Menu on controls offers queue
   shuffle, audio details, confirmed clear and Save queue to Jellyfin.
   Saving creates a new private playlist for the current signed-in account,
   not automatically for every household user. A confirmation is required;
   duplicate names, overwrites and existing-playlist edits are refused.
6. Back or Home from the full player stops its owned audio and cancels loading.
   Back returns to the exact source tile, even if the source rows were reordered.
   Home stays on Home. Returning to Music restores that source selection.

Missing/incomplete selections are refused rather than played partially. If
Music says recovery is required, retain the checkpoint and ask for inspection;
do not clear an unknown queue or repeatedly start another player. “Music is
already opening or open” prevents a second controller competing for playback.
Normal Music entry still uses the existing bounded list/search limits; the
new genre explorer and non-holiday shuffle validate the complete indexed
catalogue. Neither retags source files nor changes saved playlists implicitly.

Current corrected deployment: Music candidate64 plus normal integration6 and
the floating shared-rail overlay. Private exact recovery lives under
`/storage/.aster-checkpoints/aster-music-expanded-trial-20261023/before-candidate64`
and `/storage/.aster-checkpoints/aster-music-integration-20261024/` (original
baseline and versioned revisions retained). Restore only verified affected
files with Kodi stopped; do not replace credentials, AV settings or watch
history. Two native correction runs and the broader Home/navigation regression
pass with the five headers and separate hero action. An old programmatic test
playlist has resurfaced server-side; the original16 are unchanged. It is retained
pending separate one-time cleanup permission, not silently deleted. The physical
G20 listening/sofa walkthrough and sustained-use acceptance remain outstanding.

### Floating side navigation

The shorter rail is centred vertically with space above, below and to its left.
The chevron is removed. Press Left from the page to open the menu with the
current page already highlighted; Up/Down chooses a destination and OK opens
it. Right returns to the page. Books returns to its visible first book row.
The Music genre browser keeps its existing smaller Music/Back menu, now with
the same floating geometry. No login, media or volume setting changed.
Shared-rail recovery is separate under
`/storage/.aster-checkpoints/aster-floating-rail-20261024/`; preserve its
original include and versioned revisions alongside the Music recovery.

## Accepted across v2 players — 2026-10-24

Jason accepted floating icons as the common player standard, not just a Music
experiment. `player_controls.py` builds a separate overlay for VideoOSD, the
existing music player, Books listening (audiobook/podcast) and Digest. It keeps
all actions, conditions and navigation, including subtitle/audio/quality
selection and the distinction between a whole digest and one story. Controls
remain labelled natively, with a visible action caption on focus. No pill/ring
background; original monochrome companion glyphs use the same stroke family.

Generated overlay is local/staged, not activated on HP or production. Native
cross-player review belongs to shell/player integration; no v1 source is edited
to manufacture a deployment claim. M2 retains the separate interactive-scrubber,
overlay/auto-hide and remote regression work. HP Music remains candidate36.
