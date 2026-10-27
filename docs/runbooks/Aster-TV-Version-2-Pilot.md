# Aster TV Version 2 HP pilot guide

> Status: HP lab release candidate; production BOSGAME is unchanged  
> Audience: household testers and operator  
> Updated: 2026-10-27

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

## Voice search

- Voice search is an HP-only pilot. From Aster's Media Home, press the G20
  microphone button once, speak a short title or person, and stop speaking. Do
  not hold the button and do not press OK afterward. Aster listens for at most
  four seconds and opens the normal grouped Search results.
- Natural requests such as “Search for Dune” are accepted; Aster removes only
  that command prefix and terminal dictation punctuation. It does not silently
  substitute a different local title when recognition is uncertain.
- If no useful speech is heard, the Search page remains open and shows a short
  retry notification. Repeatedly pressing the microphone is not a recovery
  action; wait for the current attempt to finish before trying once more.
- Captured audio and transcripts remain in memory only and are not retained in
  Kodi logs or on the speech server. The HP uses the restricted local
  Aster-Speech STT path; it does not send household speech to Google or another
  cloud transcription service.
- The physical title/latency trial and one cold-boot microphone smoke are still
  acceptance items. Until they pass, use the ordinary Search pill whenever
  recognition is slow or inaccurate rather than inventing title aliases.

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

## Acquisition Hub

- **Requests** opens the native Acquisition Hub. Media, Music and Books are
  separate tabs and retain their own selected item.
- Every displayed candidate is a sanitized, currently unowned suggestion from
  the private acquisition services. An unavailable or stale feed must remain
  visibly unavailable; it must not block ordinary local libraries.
- Film and television continue through the existing season-aware Seerr page.
  Jason still approves or declines those requests in Seerr.
- Album, ebook and audiobook actions require two explicit presses. The first
  arms the exact request and the second submits it through the restricted
  broker. A pending, processing or already-available result cannot be submitted
  again.
- If a request reports an uncertain result, do not press OK repeatedly. The
  private request journal deliberately prevents a blind retry.
- The deployment test did not send a request. Until an intentional provider-
  write trial is chosen, use the page for browse, tab, focus, artwork and Back
  testing only.

## Accessibility and screensaver

In Aster skin settings, **Reduce interface motion** removes decorative fades,
slides and pulses while retaining focus and control behavior. Kodi Interface
settings exposes **Aster High Contrast**, which keeps the Aster palette while
meeting the normal-text contrast target. The default palette remains available.

The Aster screensaver places the player logo at changing positions rather than
dimming the interface indefinitely. Any normal remote action should wake it.

## YouTube

- The Media **YouTube** pill opens Aster's presentation of the maintained
  official Kodi YouTube add-on. Aster does not scrape YouTube or provide a
  downloader, browser, alternate client or proxy.
- The landing tiles and selected-item hero use the supplied Aster YouTube mark.
  Search, subscriptions, channels, account state and playback remain owned by the
  official add-on.
- Google API/OAuth values are private per-client state. Never paste them into a
  chat, ticket, screenshot, shell command, skin file or repository. Use only the
  retained hidden-input handoff helper and keep central custody at
  `secret/household/astertv/youtube`.
- Account authorization is completed by Jason on Google's device page when Kodi
  displays a one-time code. Do not photograph or record that screen. If Google
  reports an unexpected project, scope or account, cancel rather than continuing.
- While the Google app remains in testing, the signing-in Google account must be
  listed under **APIs & Services → OAuth consent screen → Audience → Test users**.
  An `Error 403: access_denied` page means the account is not an eligible test
  user; it does not mean the API key or TV OAuth client should be recreated.
- On an established add-on profile, credentials belong in the runtime `user`
  key. Use the retained helper's `verify` or `migrate` mode; do not hand-edit or
  display `api_keys.json`. A stale documented `personal` key can be ignored when
  an empty `user` key already exists.
- The HP stable-playback setting is **MPEG-DASH videos disabled**
  (`kodion.mpd.videos=false`). It avoids the observed GoogleVideo 403 failure on
  the adaptive `ANDROID_VR` path. Do not re-enable it merely to force 4K/HDR;
  that capability remains best-effort until the upstream path is reliable.
- Back from a listing returns to the previous Aster context. Back from full-screen
  playback must stop that YouTube item and return to its listing; report any audio
  or video left playing.
- Engineering playback probes must first establish a real listing/source window.
  Opening a plugin play URL directly and then stopping it can reveal Kodi's blank
  invalid window because no page exists underneath. Confirm there is no active
  player, then return to Home; do not reboot the HP for this condition.
- 4K/HDR is best-effort and separately tested. A title playing normally at 1080p
  is not proof of 2160p or HDR, and a vendor-stream limitation is not repaired by
  changing to an unofficial client.

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

The later Acquisition Hub is a verified layered successor, not a member of
Recovery7. Its accepted checkpoint is
`/storage/.aster-checkpoints/aster-acquisition-page3`; the first activation
checkpoint at `/storage/.aster-checkpoints/aster-acquisition-page2` is retained
as additional recovery evidence. Its active manifest SHA-256 is
`188b5923527f62adb42a02c65c3d3848a73550fda0202eb94fdf1ccedd68815c`.
The accepted visual-label successor is checkpointed at
`/storage/.aster-checkpoints/aster-acquisition-label9`, with manifest SHA-256
`3edb117155442a8d9a035478c019fd6eaf9ae2ad63971bac7d09c2905d8b8930`.
It corrects only the native page action caption/composition; it adds no request
authority. The intermediate `aster-acquisition-label1` through `label8`
checkpoints are retained as an auditable chain and must not be selected as the
active endpoint.
The subsequent skin-hygiene layers are checkpointed separately at
`/storage/.aster-checkpoints/aster-appledouble-quarantine-20261026` and
`/storage/.aster-checkpoints/aster-font-contract-20261026`. The former retains
all 15 quarantined AppleDouble sidecars for inspection or exact recovery; the
latter retains the preceding `Font.xml` while the active file is the canonical
repository catalogue. Do not copy the quarantined `._*` files back into a live
skin. A complete reconstruction of the current HP candidate must retain the
canonical font catalogue and a sidecar-free skin tree.
Restoring Recovery7 alone would remove the Hub launcher/window and is therefore
not a reconstruction of the complete current candidate. Apply or roll back the
Acquisition layer only through its pinned helper and checkpoint until a later
graduation package deliberately consolidates the layers.

Recovery7 has passed one real rollback and reinstall. Never restore profiles,
watch history or listening progress as part of a UI rollback. Stop if a pinned
hash, checkpoint state or recovery marker differs. Production promotion needs a
separate approval and a new production checkpoint.

The YouTube presentation, credential, dialog-focus and progressive-playback
layers have separate HP-only checkpoints:

- `/storage/.aster-checkpoints/aster-youtube-integration3`
- `/storage/.aster-checkpoints/aster-youtube-api-20261026`
- `/storage/.aster-checkpoints/aster-dialog-focus-20261026`
- `/storage/.aster-checkpoints/aster-youtube-progressive-20261026`

Credential rollback must use the retained helper with Kodi stopped so the
pre-authorization state is restored without displaying or exporting tokens.
Dialog recovery restores only `DialogConfirm.xml`. Playback-setting recovery
restores only the saved YouTube `settings.xml`, also with Kodi stopped, followed
by one normal Kodi start. Never copy account-state files into project evidence.

The HP voice-search successor is pinned by candidate manifest
`094455c6574df87b10b4033532d3faecc9928d62aa26ca48a4fac66e72e4db6e`.
Its retained checkpoints include the speech-model predecessor at
`/var/lib/aster-speech/checkpoints/small-en-title-search-20261027`, the HP
event-input retry predecessor at
`/storage/.aster-checkpoints/aster-eventlircd-retry-20261027`, and the visible
failure-feedback predecessor at
`/storage/.aster-checkpoints/aster-voice-feedback-20261027`. Recovery must keep
audio/transcript retention disabled and must not replace the microphone action
with a global OK/Select binding. Production has no voice-search installation.

