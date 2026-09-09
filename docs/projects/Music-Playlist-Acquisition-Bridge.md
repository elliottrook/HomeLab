# Music Playlist Acquisition Bridge

Status: live playlist creation/replacement path validated (2026-09-07); Lidarr acquisition test pending

## Goal

Read playlists exported from music services, ask Lidarr to acquire missing music, then create the
equivalent Jellyfin playlist only when the files are present in Jellyfin's canonical Music library.
The source remains authoritative; the first implementation is one-way and never writes back to a
commercial music service.

## Investigation and decision

| Option | Acquisition | Jellyfin playlist | Sources | Decision |
|---|---|---|---|---|
| Cmdarr | Lidarr custom import list | Native sync | Spotify, Deezer, ListenBrainz and public sources | Recommended for live supported services |
| SongMirror | Downloads through spotDL, not Lidarr | `.m3u8` plus Jellyfin API | Spotify, Apple Music, YouTube Music and others | Strong service-to-service tool, but bypasses the quality-controlled Lidarr path |
| Jellyplist | Lidarr integration plus spotDL | Native sync | Spotify | Rejected: upstream is archived after Spotify API breakage |
| Jellyfin Spotify Import plugin | None | Native sync with manual mappings | Spotify | Useful matcher, but cannot fill missing media |
| MiniMediaPlaylists | None | Native cross-sync | Several services | Useful only after tracks already exist |
| Local `playlist-bridge` prototype | Lidarr album lookup/add/search | Native playlist after full match | CSV/TSV, Spotify JSON, Apple/iTunes XML, M3U | Selected for exported files and unsupported sources |

The practical architecture is hybrid: deploy Cmdarr for live sources it supports, and use
[`scripts/playlist-bridge`](../../scripts/playlist-bridge/README.md) for exports (especially Apple
Music). Do not deploy Jellyplist: its repository now explicitly recommends alternatives after the
Spotify changes. SongMirror remains a good fallback if track-level downloads matter more than
Lidarr quality profiles and provenance.

## Workflow

1. Export a playlist into the bridge inbox without credentials embedded in the filename.
2. Parse and normalize track, artist, album, and ISRC when the source supplies it.
3. Cache Jellyfin's Audio inventory and match exact normalized title + artist, preferring album.
4. For each missing recording, ask Lidarr for the closest album and add/search it using the
   configured quality and metadata profiles. Lidarr is album-oriented, so one requested song can
   acquire a whole album.
5. Exit `2` while incomplete. Lidarr downloads/imports into the existing canonical music root;
   Jellyfin detects or scans the new files.
6. On a later run, once every track matches, create the complete private Jellyfin playlist. If an
   exact-name playlist already exists, delete it only after its replacement is safely created.
   Jellyfin API keys cannot use its owner-authorized update endpoint because they have no user
   identity; create-first makes a failed deletion leave a recoverable duplicate instead of data loss.

## Safety and known limitations

- Dry-run is the default. `--execute` is required for every Lidarr or Jellyfin mutation.
- The bridge never downloads audio itself and therefore preserves the existing Lidarr naming,
  metadata, quality, and library-integrity controls.
- A source track absent from MusicBrainz/Lidarr cannot be acquired by this route. Report it for
  manual handling; do not silently omit it from the Jellyfin playlist.
- Matching deliberately requires title and artist. ISRC is retained but not yet used because
  Jellyfin metadata coverage varies and Spotify stopped returning ISRC for some API paths in 2026.
- Different editions, classical works, compilations, and localized titles will need a persistent
  manual mapping facility before broad unattended rollout.
- Lidarr adds albums rather than individual tracks. Set monitor behavior and release profile
  carefully to avoid unexpected discography growth.
- The prototype assumes the playlist name is bridge-owned. Before first `--execute`, use a distinct
  suffix such as `[Spotify]` or `[Apple Music]` so it cannot replace a hand-maintained playlist.

## Rollout

- [ ] Create dedicated `playlist-bridge` Jellyfin and Lidarr API keys; the live test temporarily
  reuses the integrity tool's keys. Config remains outside git with mode `0600`.
- [x] Confirm Lidarr root (`/media/media/music`), Lossless profile (`2`) and Standard metadata
  profile (`1`) against Lidarr 3.1.0.4875.
- [x] Dry-run and execute a five-track, existing-library test against Jellyfin 10.11.11.
- [x] Verify the private `Playlist Bridge Test` belongs to Jason, has five ordered tracks, is not
  visible to another user, and a second run leaves exactly one playlist.
- [x] Run a controlled ten-track/ten-album Spotify test. One track matched locally; live execution
  added four monitored Lossless albums (`Music to Be Murdered By`, `Houdini`, `2001`, `Killshot`).
  Lidarr's upstream metadata service returned HTTP 503 for three albums, one edition name did not
  match, and `Kamikaze` stopped resolving after the artist refresh began. These remain pending and
  no partial Jellyfin playlist was created.
- [ ] Verify the four albums download/import, then rerun to exercise Jellyfin reconciliation.
- [ ] Add a retry/backoff state machine for Lidarr metadata refreshes and edition-name matching
  before enabling unattended scheduling.

### Explicit search validation

Lidarr 3.1.0 did not honor `searchForNewAlbum` when the bridge deliberately left the parent artist
unmonitored. The bridge now explicitly queues `AlbumSearch` after adding an album and also re-searches
an already-managed missing album on later runs. Live command `62891` searched album IDs 3532, 3544,
3545 and 3548 successfully. It grabbed releases for all four: `Music to Be Murdered By` imported
36/36 tracks, `Houdini` 1/1, and `2001` 22/22; the selected `Killshot` release failed to import.
After a Jellyfin scan and featured-title normalization, the test playlist improved from 1/10 to
5/10 matched tracks. It remains intentionally uncreated until all ten match.

Killshot was then removed from the test at the user's request. The remaining nine-track source
started a persistent 24-hour incomplete timer at `2026-09-07T21:09:39Z`; four tracks were missing.
TrueNAS cron job `3` runs the bridge every six hours at minute 15. If tracks remain missing after
the deadline, it creates a private partial playlist for Jason and reports the omitted tracks.
Later runs can improve the playlist as additional tracks arrive.
- [ ] Add persistent manual mappings and a bridge ownership marker before unattended scheduling.
- [ ] Install on TrueNAS under `/mnt/Media/data/tools/playlist-bridge/` following the established
  integrity-tool pattern; schedule daily only after two clean manual cycles.
- [ ] Add JSON reports, backup coverage, and a `lab doctor` freshness/failure check.
- [ ] Evaluate Cmdarr separately with one disposable live-source playlist before enabling its
  Lidarr custom list.

## Sources reviewed

- [Cmdarr](https://github.com/DeviantEng/Cmdarr)
- [SongMirror](https://github.com/ahnafnafee/songmirror)
- [Jellyplist](https://github.com/kamilkosek/jellyplist)
- [Jellyfin Spotify Import](https://github.com/Viperinius/jellyfin-plugin-spotify-import)
- [MiniMediaPlaylists](https://github.com/MusicMoveArr/MiniMediaPlaylists)
- [Lidarr API](https://lidarr.audio/docs/api/)
- [Jellyfin playlist API model](https://github.com/jellyfin/jellyfin/blob/master/Jellyfin.Api/Models/PlaylistDtos/CreatePlaylistDto.cs)
