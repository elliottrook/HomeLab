# Music Playlist Acquisition Bridge

Status: active follow-on expansion (2026-10-08); 72-hour hold, report path and portal UI implemented
locally; TrueNAS deployment and cron migration pending explicit remote-change approval

## Expansion request — Spotify sources, durable acquisition and GUI

Jason requested that this project expand beyond exports and public Spotify links to support
authenticated Spotify playlist selection and repeatable future transfers from the Unified Media
Recommendations portal. A transfer must not silently drop a track that is absent from Jellyfin:
the bridge should identify the track's album from Spotify metadata, request that album through
Lidarr, and keep the transfer pending until Jellyfin contains every requested track. Partial
playlists must be opt-in rather than the automatic result of a timer expiring.

### Approved design direction

- Use Spotify OAuth with PKCE for private playlist access. Store only the non-secret client ID and
  the resulting access/refresh tokens in the existing protected unified-media state; never put
  tokens in Git, browser storage, reports or logs. The user sees only a normal Spotify login and
  consent screen.
- Read Spotify playlist and track metadata only: playlist identity/snapshot, track title, artists,
  album identity/name, release information, ISRC when supplied, and Spotify attribution links.
  Spotify remains a metadata source; audio acquisition continues through Lidarr and its configured
  quality, provenance and library-integrity controls.
- Persist one transfer record per Spotify playlist snapshot. Track each source item, its Jellyfin
  match, requested album, Lidarr state, retry history and final disposition. Re-runs must be
  idempotent and must not create duplicate Jellyfin playlists or repeatedly request the same album.
- Change the default completion policy to `wait-until-complete`: no Jellyfin playlist is created or
  replaced while any source track is unresolved. The GUI may offer an explicit, clearly labelled
  partial-snapshot option with a user-selected deadline, preserving the current safety behaviour
  only when deliberately chosen.
- Add a private `/transfers` page to the Unified Media Recommendations portal. It should support
  Spotify connection, playlist selection, preview, target Jellyfin user, transfer start/continue,
  per-track status, requested albums, retry/error details, and an explicit completion/partial action.
  Existing Recommendations and Search pages remain unchanged.
- Accept exported playlist files through the portal inbox. TrueNAS remains the worker: the portal
  does not receive Lidarr/Jellyfin write authority merely to provide the upload and log UI.
- Default incomplete handling is a 72-hour hold. At expiry the bridge creates the playlist with
  all tracks found at that point and records `complete` or `partial` evidence in a JSON report.
- Expose a separate `/transfers/log` page that polls durable reports and shows matched, missing,
  deadline and final playlist status.

### Scope, exclusions and stop conditions

This is a Stream A implementation, explicitly restarted by Jason on 2026-10-07. The autonomous
envelope covers local implementation, tests, documentation, protected-state schema changes and
non-destructive validation of the existing bridge/portal. Deployment, Spotify application
registration, secret installation, callback exposure and production transfer execution remain
authorization boundaries and will pause the stream when reached.
The scope is the bridge, the private Recommendations portal, the existing Lidarr/Jellyfin path,
protected transfer state and the required documentation/tests. It excludes Spotify audio downloading,
writing back to Spotify playlists, automatic deletion or replacement of unrelated Jellyfin playlists,
new public ingress, and broad changes to Lidarr quality or monitoring policy. Stop before deployment
if Spotify OAuth credentials, callback routing, the protected secret path, or the target Jellyfin
user cannot be validated; stop on ambiguous album identity rather than guessing.

### Pre-start risk assessment

- **Confidentiality:** Spotify OAuth tokens and playlist contents are personal data. Mitigation is
  secret-file custody, least-privilege read scopes, redacted logs and no source-track payloads sent
  to the recommendation model.
- **Integrity:** Album-level acquisition may add more tracks than the playlist requires. Mitigation
  is explicit preview, a visible album request list, existing Lidarr profiles, and no Jellyfin
  playlist mutation until every item is matched.
- **Availability:** Lidarr metadata/search providers and Jellyfin scans can be slow or unavailable.
  Mitigation is a durable retry state machine, bounded backoff, and resumability rather than a
  request timeout that silently drops tracks.
- **Privacy/network:** Spotify OAuth callback remains on the existing private Recommendations host;
  no new Internet ingress or firewall trust is required. Validate the existing Authentik/NPM path
  before enabling the callback.
- **Recovery:** Preserve transfer state and reports under protected configuration backup coverage;
  create-first Jellyfin playlist replacement remains the rollback-safe path. No media deletion is
  part of this expansion.

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
   exact-name playlist already exists, delete it only after its replacement is safely created. If
   the 72-hour deadline expires first, create a partial private playlist and record the omitted
   tracks rather than silently dropping them.
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
- [ ] Install the inbox runner on TrueNAS under `/mnt/Media/data/tools/playlist-bridge/` following
  the established integrity-tool pattern; update Cron Job 3 to process the inbox every six hours.
- [x] Add the portal upload page and separate polling transfer log page locally, with bounded file
  types/size and no credential-bearing upload payloads.
- [x] Change the bridge default hold to 72 hours and persist per-run JSON reports.
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

## 2026-10-19 reconciliation checkpoint

The dormant October 8 implementation was recovered from the shared dirty
checkout into the dedicated `codex/playlist-bridge-recovery` branch. The
recovered scope includes the 72-hour reconciliation/report path, inbox runner,
portal upload and transfer-log UI, Spotify PKCE helper, protected Compose mounts
and regression coverage. Twenty Playlist Bridge tests and twenty-four portal /
Spotify tests pass locally.

This checkpoint is source preservation, not deployment evidence. TrueNAS still
needs the dedicated API identities, protected paths, inbox runner installation,
Cron Job 3 migration, backup/Doctor coverage and controlled user-path
validation. No production configuration, credential, timer or playlist was
changed during reconciliation. Forgejo synchronization remains pending explicit
push confirmation.
