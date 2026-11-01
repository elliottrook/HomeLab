# AsterTV v3 Mini page pilot

This directory owns the isolated macOS page-design pilot defined by
`docs/projects/AsterTV-v3.md` PA0–PA4. It is not a production deployment tree.

## Runtime boundary

- Kodi application: `/Users/jelliott/Applications/AsterTV-v3-Pilot/Kodi.app`
- Required release: Kodi `22.0.rc1` for Apple silicon
- Upstream artifact: `kodi-22.0-Piers_rc1-arm64.dmg`
- Published and verified SHA-256:
  `5f50e35df66fdac2eb10b2915249d6ec8230da19833f1f00068200a744341e5b`
- Signing identity: `Developer ID Application: Kodi Foundation (QR7RHK8K4X)`
- Portable data:
  `/Users/jelliott/Applications/AsterTV-v3-Pilot/Kodi.app/Contents/Resources/Kodi/portable_data`

The launcher refuses to start if the dedicated application or portable marker
is absent. Never open this application by double-clicking it: doing so omits
Kodi's `-p` switch. At the owner's direction on 2026-10-31, the obsolete
standard-profile directory was moved intact to
`/Users/jelliott/.Trash/Kodi-legacy-20261031`. It remains recoverable until the
Trash is emptied; the portable profile above is the Mini's sole active pilot.

## Source and data rules

- Source Aster-owned code and assets from the immutable v2.0.7 release archive.
- Apply v3 work as an explicit overlay; never edit the v2 archive or its
  reconciliation payload.
- Use labelled synthetic normal, empty, loading, stale and error fixtures for
  Stream A design acceptance.
- The owner explicitly authorized a bounded Stream M seam in this same isolated
  profile: Jellyfin Kodi Sync Queue 2.2.0 was connected by Quick Connect and
  only Movies was selected. Never commit or display its token or profile data.
- The official Kodi YouTube 7.4.4 and InputStream Adaptive 22.3.23 add-ons are
  installed without a YouTube account solely for the trailer smoke. Do not
  provision Seerr, Audiobookshelf, Home Assistant, camera or Aster credentials.
- Do not use real household state, camera images, history or account data.

## Launch

Run `./run-mini-pilot.sh` from this directory. The script opens a new Kodi
instance with `-p` only after validating the application, release, marker and
portable-data boundary. On a freshly prepared profile, run
`./activate-mini-pilot.sh` after Kodi reaches Estuary. The activation helper
first proves the live `special://home` mapping from Kodi's own log, then enables
and selects only the pilot skin through local Kodi JSON-RPC.

Never launch the application directly. Direct launch omits `-p` and is outside
the pilot boundary.

Press `F8` in the verified portable pilot to open the synthetic PA1 shared-
language page. The fixture contains no media, account, camera or household
state. It exists to review common chrome, focus, target sizing and ready/loading/
empty/error language before those components are applied to individual pages.

Press `F9` to open the account-safe YouTube rework fixture. It preserves the
accepted page hierarchy while demonstrating icon-bearing pills, layered
surfaces, true 16:9 artwork and card-backed titles without calling YouTube.

Press `F10` to open the deterministic artwork-tile fixture. It covers
landscape, square, portrait and compact artwork with transparent rest states
and the locked tight sage artwork/title focus surface.

Press `F11` to open the deterministic button fixture. It covers the locked
Gold Rim treatment on rail pills, primary actions, current/toggle states and
compact player controls using deep Aster green and antique gold `#AD8A4D`.

Press `F12` to open the synthetic Movie rework. It uses portrait Cast & Crew
art, landscape More Like This art, icon Play/Resume actions, no clock and
additional logo clearance. Selecting a cast member opens the companion person
card, whose Films and Television rails represent only titles available to the
current Jellyfin user. The Trailer control represents the Jellyfin-first route:
local trailer when present, otherwise a strictly validated `RemoteTrailers`
YouTube ID handed to the official Kodi YouTube add-on. The pilot data is
synthetic and makes no Jellyfin or YouTube call.

Press `F7` for the bounded live trailer smoke. It refuses to interrupt active
playback, reads exactly one Jellyfin-synced movie title from Kodi, accepts only
the strict `plugin://plugin.video.youtube/play/?video_id=<11-char-id>` route and
enables only the two official playback add-ons. On macOS the YouTube add-on's
adaptive manifest service advertises a non-loopback address while listening on
loopback; the smoke therefore selects its progressive path rather than exposing
that service to the LAN. This pilot-only setting does not change either AsterTV
production target.

The 2026-10-31 bounded sync completed in 14 seconds with 77 movies, of which 75
provided trailer routes. Collection-assignment warnings are expected because
Collections was deliberately excluded. The Buddy smoke opened video and audio
streams through the exact Jellyfin metadata route without copying a YouTube
account into the pilot.

