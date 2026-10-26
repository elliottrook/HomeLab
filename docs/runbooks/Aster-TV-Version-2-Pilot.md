# Aster TV Version 2 HP pilot guide

> Status: HP lab release candidate; production BOSGAME is unchanged  
> Audience: household testers and operator  
> Updated: 2026-10-26

## What this pilot is

Version 2 is active only on the HP AsterTV lab box. It is a remote-first preview
of the next household interface, not a production upgrade. Ordinary viewing and
listening are safe to test. Do not treat a request, bookmark warning or recovery
message as permission to repair server data manually.

The left floating rail opens the five household areas: **Media, Books, News,
Home** and **Settings**. The focused destination has the prominent Aster focus
treatment. Top rails use the same dark glass, green focus and white rim. Search
is separated by its gold band.

## Media

- **TV Shows** opens Aster's series page. Up/Down moves episode by episode. Up
  from the first episode reaches the season chooser. Back returns to the exact
  series tile.
- Episodes already in Jellyfin use colour artwork and play normally. Catalogue-
  only episodes use monochrome artwork and cannot play.
- On a catalogue-only episode, the first OK arms **Request Season N** and the
  second OK submits it to Seerr. A submitted season becomes pending and cannot
  be submitted again. Jason still approves or declines it in Seerr; Aster never
  self-approves requests.
- **Search** groups results by type. Move Up/Down between groups and Right into
  results; OK opens the real destination page rather than a duplicate details
  window. Back returns to the same query and result.
- During video, Pause reveals the discreet OSD. Soundtrack, Subtitles and
  Quality open small in-place menus. Fullscreen Back stops Aster-owned playback
  and returns to its source page, preserving the normal Continue Watching path.
- The progress bar supports preview then commit: focus it, press OK, move with
  Left/Right, then OK to seek or Back to cancel.

## Music

- Albums, songs, artists, Jellyfin playlists and the seven music genres open
  their dedicated pages. OK on a playable row opens the player.
- Controls are centred below the artwork: back 10 seconds, Play/Pause, forward
  10 seconds, Stop and Next. Queue tools sit separately.
- **Shuffle all** excludes the accepted holiday/Christmas classification. Aster
  refuses an incomplete or stale library snapshot rather than silently making a
  partial queue.
- Queue replacement, clearing and saving require confirmation. Shared playlist
  saving is create-only: Aster refuses duplicate names and does not overwrite an
  existing Jellyfin playlist.
- Back/Home stops only the playback owned by this Aster Music session. It does
  not stop an unrelated player.

## Books and podcasts

- Audiobooks and downloaded podcast episodes use the shared household
  Audiobookshelf position. Resume is server-authoritative; an explicit chapter
  choice starts that chapter rather than jumping back to Resume.
- Pause and Back save the owned position. An uncertain write is shown as a
  warning and is not retried blindly. Do not reset listening history to clear a
  warning.
- The moon control offers Off/15/30/45/60-minute sleep. It counts wall-clock
  time, shows minutes and seconds for the final two minutes, saves the position
  and stops only its owned audio at expiry.
- Shared bookmark creation is not exposed in the normal HP interface. The server
  safeguard is installed, but the remaining user control stays gated until its
  final acceptance.
- The EPUB reader and synchronized Aster-voice read-along are engineering
  previews. Bulk narration belongs to the separate EPUB Narration Compiler
  project; do not expect every Calibre title to have generated audio yet.

## News

- **Daily briefing** plays the opening and each story in order while moving the
  active story highlight and artwork with the audio.
- Selecting a story starts that story. Previous/Next includes the opening. Back
  stops the briefing owned by the page.
- **Read briefing** is a separate published-summary reader. It does not pretend
  that web cards and audio chapters have matching identities when the publisher
  does not provide them.
- **Breaking News** remains distinct from the daily briefing.

## Home and Settings

- Home shows read-only temperature, lighting, sensor, battery, weather and
  availability summaries from the restricted Home Assistant feed. Missing or
  stale data is labelled; old data is never repainted as current.
- **Live view** fetches only Front of House images while the viewer is open,
  refreshes every two seconds and closes after five minutes or on exit. It is a
  refreshed still view, not full-motion video.
- The timer uses the Aster circular countdown, named presets and completion
  attention state. It is independent of the Books sleep timer.
- Settings includes Network status and the optional log viewer. Diagnostics are
  explicit/manual and do not run hidden background probes.

## Accessibility and screensaver

In Aster skin settings, **Reduce interface motion** removes decorative fades,
slides and pulses while retaining focus and control behavior. Kodi Interface
settings exposes **Aster High Contrast**, which keeps the Aster palette while
meeting the normal-text contrast target. The default palette remains available.

The Aster screensaver places the player logo at changing positions rather than
dimming the interface indefinitely. Any normal remote action should wake it.

## What to report during household testing

Record the page, selected title and last remote button when reporting:

- focus disappears or moves to an unexpected row;
- Back leaves audio/video playing;
- a resume point moves backwards or to the wrong episode/chapter;
- a catalogue-only episode plays, or a pending season can be requested twice;
- stale Home/camera information looks current;
- memory, responsiveness or navigation degrades during an evening of use; or
- Kodi restarts, freezes or leaves a recovery warning.

Do not repeatedly press OK after a request or save reports an uncertain result.
That state is deliberately fenced for operator inspection.

## Operator recovery boundary

The active HP family recovery pin is
`08299ef534f54499d2d69c60c95e32087f622a0f3c6d89bbc87f9c4293e2e17d`
at `/storage/.aster-staging/aster-family-recovery7b`. Its checkpoint is
`/storage/.aster-checkpoints/aster-family-runtime7`. The Jellyfin segment guard
has its separate checkpoint at
`/storage/.aster-checkpoints/aster-jellyfin-segments-guard-20261026`.

Recovery7 has passed one real rollback and reinstall. Never restore profiles,
watch history or listening progress as part of a UI rollback. Stop if a pinned
hash, checkpoint state or recovery marker differs. Production promotion needs a
separate approval and a new production checkpoint.

