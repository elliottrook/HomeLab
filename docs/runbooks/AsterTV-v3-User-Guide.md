# AsterTV v3 household guide

Status: pre-graduation handover draft  
Audience: household users and the person performing final acceptance

This guide describes the accepted AsterTV v3 interaction model and the safe
recovery path. A feature is available on a room only after that room's complete
v3 composition has been promoted. Jen is the standing low-spec canary; Family
and Bedroom retain their independently accepted v2 recovery points while final
v3 promotion remains open.

## What changes in v3

- Aster pages share one remote-first focus language: the focused action is deep
  green with an antique-gold rim; artwork receives the approved green selection
  wrapper without changing the resting artwork.
- Movies open a details page before playback and expose cast, related titles
  and an available Jellyfin trailer route.
- TV series open the Aster season/episode page with season, cast and related
  artwork navigation.
- YouTube retains the household identity, Recommendations, Subscriptions,
  Watch Later and search while using the Aster presentation.
- Books, Audiobooks and Podcasts retain their own authorities. Only prepared
  eBooks are offered for Aster narration.
- News keeps the current story, artwork and briefing progress on the player
  page while the digest advances.
- Home and Cameras are separate read-only pages. The camera viewer starts only
  from the Cameras page and stops on Back.
- Aster Remote provides immediate private-network control from iPhone or
  Android without embedding a Kodi, Home Assistant or speech credential.
- Aster AI uses a compact floating response for direct actions and the larger
  result surface only for media search.
- The page-aware Aster screensaver uses local media artwork, Music album art or
  a neutral Aster surface according to the page underneath. It has no sound.

V3 does not change Family's accepted Dolby/HDR path, Bedroom's independently
measured audio path, Jellyfin's library authority, Seerr's film/TV request
authority or Audiobookshelf's audiobook/podcast progress authority.

## Normal television use

Use the directional pad to move focus, **OK** to open the focused item and
**Back** to return one level. The green-and-gold treatment shows the action that
will run; a gold rim without green may identify the current choice when focus is
elsewhere.

### Media

1. Choose TV Shows, Movies, Archive TV, Archive Movies, Collections or YouTube
   from the top rail.
2. Select artwork with **OK**.
3. For Movies, review details and then choose Play, Resume or Trailer.
4. For TV, choose a season, then an episode. Watched episodes use the accepted
   small green tick; unwatched episodes use the smaller green dot.
5. Press **Back** to return to the previous Aster page.

### Music, Books and News

- Music: choose a category, album and track. Playback starts without replacing
  the queue through a confirmation dialog.
- eBooks: the visible list contains only books with prepared narration. Open a
  book to read and use Play for Aster narration.
- Audiobooks/Podcasts: Resume appears only when the source authority has a saved
  position.
- News: choose a story or play the whole digest. The player follows the active
  story and retains artwork, progress and semantic playback controls.

### Home and Cameras

Home displays the bounded read-only household summary. Cameras is a separate
page. Opening Live view starts the restricted viewer; **Back** stops it. A
missing or unavailable camera must show a clear unavailable state rather than
an old frame.

## Aster AI

A short direct instruction such as “open cameras” or “play the news” uses the
small lower-right Aster card. Its thin waveform indicates activity and the
green line confirms the action. A media-discovery request opens the larger
artwork result surface instead. **Back** dismisses either surface.

Aster may perform only its named search, navigation, playback, News and exact
Home aliases. It cannot run an arbitrary shell command, select an unrestricted
Home Assistant service or silently request media.

Listening or processing failure must leave the page usable. Repeat the command
once or use the remote; do not treat an absent confirmation as a completed
action.

## Aster Remote

Open [Aster Remote](https://aster.elliottrook.com/remote/) while connected to
the authorized household network.

- iPhone: Safari → **Share** → **Add to Home Screen** → **Open as Web App**.
- Android: Chrome → **Add to Home screen** or **Install app**.
- Use the bottom room selector to choose an AsterTV. The app remembers the last
  valid room on that browser.
- Navigation, Select, Back, Home, menu and playback follow the same bounded
  routes as the physical remote.
- Voice fills the Search draft. Correct or append with the phone keyboard, then
  press Search.
- Kodi text editing appears only while a non-sensitive television text field is
  active. Password fields remain television-only.
- Family volume, mute and power address the accepted Family room-equipment
  bridge. Bedroom equipment controls stay unavailable until their separate
  physical acceptance.

There is no browser login. Network location grants only the declared room set;
each television still uses an independently revocable outbound identity. A red
connection indicator means the selected room is unavailable. Use the physical
remote while it recovers.

## Accounts and privacy

- Jason is the current recovery administrator.
- Guest is fail-closed and can reach only its explicitly mapped catalogue and
  playback services. It cannot use private Books, Music, Requests, YouTube,
  Home, Cameras, Settings or Aster AI routes.
- The future Guest-room AsterTV is not enrolled and receives no network route.
- AsterTV does not put viewing history, dictated text, typed text, recordings
  or camera frames into the release bundle.
- Content-state publication contains only coarse room/page/playback class and
  an opaque session. It contains no title, library ID, path or plot and is not
  recorded in Home Assistant history.
- Camera viewing is bounded to the open page. Aster's page-aware screensaver
  does not read household values or camera images.

## Safe recovery

1. Press **Back** once to dismiss a dialog, Aster surface or viewer.
2. If playback is active, stop it before attempting repair or restart.
3. Try the physical remote. It remains the recovery control if Aster Remote,
   speech or Home Assistant is unavailable.
4. If only the Remote is unavailable, confirm the phone is on the authorized
   home network and select the room again. Do not expose the Remote publicly.
5. Use the AsterTV restart action in Settings only while playback is stopped.
   It restarts Kodi, not the operating system or household services.
6. If the page still fails, stop and use the room's accepted checkpoint and
   fleet runbook. Do not reinstall an old partial overlay or copy files from a
   different room.

Core local media playback must continue when optional Aster AI, Home/cameras,
Remote or Home Assistant integrations are unavailable. A failure that also
breaks local playback is a release/recovery incident, not a normal degraded
state.

## Final acceptance still required

The following must be completed before this guide and AsterTV v3 graduate:

1. Bedroom physical Volume Down/Up, Mute and Power observation through the LG
   ARC/eARC SIMPLINK/CEC chain, including physical recovery and attached-audio
   inventory.
2. Bedroom content-volume choices and the bounded outage/restart/manual-
   override checks.
3. Complete Bedroom composition deployment, reboot and normal-use soak while
   preserving its stereo contract and recovery checkpoint.
4. A non-author physical walkthrough of the workflows above.
5. Explicit final Family promotion while idle, followed by its production-path
   acceptance run and Dolby/HDR confirmation.
6. External Media Lifecycle replacement-view handoff, or explicit acceptance
   of the four current smart-playlist routes as the continuing fallback.

Detailed operator recovery and credential custody remain in the AsterTV wiki,
fleet manifests and [Aster Remote operations](Aster-Remote.md). They are not
duplicated in this household guide.
