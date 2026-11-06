# AsterTV v3 M9 — page-aware idle candidate

Date: 2026-11-05

Status: repository-only candidate; no appliance deployment

## Boundary

Kodi selects one global screensaver add-on. The candidate therefore keeps one
Aster screensaver and dispatches internally from a deliberately coarse last-page
class. It does not create competing Kodi screensavers or read page titles,
accounts, media history, Home Assistant values or camera state.

## Candidate behavior

- `media`: preserve the accepted balanced round-robin sampling of TV Shows,
  Movies, Archive TV and Archive Movies and prefer landscape/fanart.
- `music`: select random local Kodi-library album art and present it as a
  centred square without stretching it across the display.
- `neutral`: show only the black background and AsterTV mark.
- Missing/malformed/unknown context fails closed to `neutral`.
- The mark rotates between four safe corners on the existing 18-second artwork
  interval to reduce static-pixel exposure.
- Playback, an active or expired Home timer, a foreign dialog, wrong host,
  wrong selected add-on or deactivated screensaver suppresses or exits the
  candidate through the inherited boundary.

The companion startup service publishes only `media`, `music` or `neutral` to
`Window(Home).Property(AsterIdle.Context)`. It freezes that value while the
screensaver is active, preventing the screensaver window itself from replacing
the originating page context.

## Privacy and authority

The candidate queries only local Kodi video playlists and
`AudioLibrary.GetAlbums`. It contains no URL client, service credential,
camera/Frigate source, household-state query, clock or sound call. It reuses the
accepted Aster skin assets and does not write library or profile data.

## Verification

- Seven policy/structure tests pass.
- The tracker explicitly ignores window changes while the screensaver is
  active.
- All three Python modules compile using an isolated temporary bytecode cache.
- XML parses and includes separate 1920x1080 media and 760x760 album surfaces.
- `git diff --check` passes.

## Remaining gate

Do not deploy this candidate yet. A non-production client must first prove
actual Kodi window classification, album-art loading, four-corner movement,
wake return, playback/timer suppression, missing-art fallback and a sustained
idle resource envelope. Only then may M9 be considered for a host-bound fleet
package and later promotion.

