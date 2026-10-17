# Jellyfin LRCLIB installation — 2026-10-17

> Status: completed and validated  
> Owner: Jason  
> Authorization: Stream M; exact install and Jellyfin restart approved in chat  
> Production target: Jellyfin 12.1.0 on TrueNAS `192.168.20.40`

## Purpose and scope

Add Jellyfin's official LrcLib Lyrics provider so music clients can retrieve
plain or synchronized lyrics from `lrclib.net`. The change was limited to one
plugin directory, one ZFS recovery snapshot and one Jellyfin container restart.
Media, user accounts, SSO, DNS, firewall policy, certificates and other services
were excluded.

LRCLIB receives track-identifying metadata when Jellyfin searches for lyrics.
No new inbound path or credential was added. After the initial installation was
validated, Jason separately approved a protected one-time backfill using
Jellyfin's existing `Download missing lyrics` scheduled task.

## Pre-change state and risk controls

- Live Jellyfin reported version `12.1.0`; container image remained pinned by
  digest `sha256:51252e7a416e703cdc3cd91e8a54673a2430cc80409be8a38abe511411577b95`.
- `/mnt/Media/appdata/jellyfin` was the `/config` bind mount and had 10.6 TiB
  available.
- Existing external plugins were Community SSO 5.0.0.0, Intro Skipper 12.0.5.0,
  Open Subtitles 25.0.0.0, TMDb Box Sets 15.0.0.0 and Trakt 33.0.0.0.
- Official LrcLib Lyrics 5.0.0.0 targets server ABI 12.0.0.0. The downloaded
  package MD5 matched the official catalog value
  `122f89ba5195c14967c6e9c0cc7b55fc` before installation.
- Recovery checkpoint:
  `Media/appdata/jellyfin@pre-lrclib-20261017T071208Z`.
- Rollback is to remove only `data/plugins/LrcLib Lyrics_5.0.0.0` and restart
  Jellyfin. The full snapshot is retained for unexpected configuration damage;
  rolling back all Jellyfin state would discard newer watch state and is not the
  first-line uninstall procedure.

## Implementation and validation evidence

The verified package was extracted atomically into
`/mnt/Media/appdata/jellyfin/data/plugins/LrcLib Lyrics_5.0.0.0`, using the same
owner and permissions as the existing plugins. Only the `jellyfin` container was
restarted.

- The restart produced a shutdown-time WebSocket exception for an already closed
  client connection. Docker restarted the container normally; this was not an
  LRCLIB load failure.
- During startup, the public endpoint briefly refused connections and returned
  503, then returned Jellyfin 12.1.0 with setup complete. Startup completed in
  42.2 seconds.
- Logs confirm assembly `Jellyfin.Plugin.LrcLib` and plugin `LrcLib Lyrics
  5.0.0.0` loaded. All five previously installed external plugins also loaded.
- A source-local read-only API test used the existing protected Jellyfin reader
  credential without exposing it. Thirty recent audio candidates were considered;
  the first match returned one remote result with provider `LrcLib Lyrics`.
- No media file was changed by the validation. No bulk lyrics task was started.

## Approved lyrics backfill

Before the backfill, ZFS snapshot
`Media/data@pre-lrclib-backfill-20261017T071932Z` captured the media dataset.
Jellyfin's existing `Download missing lyrics` task was then started once and
left uninterrupted. It completed successfully from `2026-10-17T07:19:51Z` to
`2026-10-17T12:03:08Z`.

A post-run `zfs diff` against the snapshot found 5,279 new lyric sidecar paths:
4,403 `.lrc` files and 876 `.txt` files. The required `Scan Media Library` task
subsequently completed successfully from `2026-10-17T12:17:27Z` to
`2026-10-17T12:30:11Z`. A source-local API read then returned a stored lyric
document with 65 lines for a sampled audio item. Jellyfin remained on 12.1.0
with setup complete, and the private HTTPS SSO endpoint returned HTTP 200.

The daily scheduled trigger remains in place for future missing lyrics. The
backfill did not restart Jellyfin, expose its protected API credential, or alter
media other than the expected lyric sidecars.

## Operation and integration impact

For a track in a compatible Jellyfin client, open its lyrics action. Jellyfin
can now search LRCLIB and present synchronized lyrics when the provider has a
match. Accuracy depends on artist, album, title and duration metadata.

- Existing configuration backup coverage already includes Jellyfin plugins and
  plugin configuration; the new snapshot adds an immediate local checkpoint.
- Existing Jellyfin availability monitoring remains applicable. No new host,
  container, port, DNS record, certificate, firewall rule, Homepage tile,
  NetBox object, Beszel object, authentication identity or AI administration
  capability was introduced.
- This provider produces no speech and does not affect the Aster voice standard.
- Human wiki and Aster knowledge-mirror updates are not required for this small
  provider addition; this runbook is the operational and recovery record.

## Close-out

The requested provider and automatic lyric retrieval are installed and
functionally validated. The approved existing-library backfill completed, its
sidecar changes are recoverable from the retained snapshot, and the library
scan made the results available to clients. Keep LRCLIB updates aligned with
Jellyfin's server ABI and repeat the snapshot, checksum, restart and
provider-query checks for future major upgrades.
