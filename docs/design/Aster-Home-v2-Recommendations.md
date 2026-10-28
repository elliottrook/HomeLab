# Aster Home 2.0 — design and feature recommendations

> **Status, 2026-10-23: scope reviewed; v2 implementation not started.** See the
> governing [v2 project](../projects/Aster-Home-Version-2.md) and separate
> urgent [v1.1 Up Next project](../projects/Aster-Home-Version-1.1-Up-Next.md).
> The owner selected items 01-26 and 31-32, added music Genres (not video),
> all-music shuffle excluding Holiday/Christmas, Seerr, voice search, scrub bar,
> premium texture-free controls and icon cleanup. Unticked 27-30 are deferred
> to v3. Historical optional recommendations below do not override that scope.
> Before v1.1 testing, BOSGAME and HP had the
> same Aster v1.0.5 release files. Their LibreELEC/Kodi versions remain
> hardware-specific. The shared lightweight player treatment and stop-on-exit
> have already shipped in v1; they are not an unstarted v2 rewrite. The marked
> printable inventory and chat clarifications now feed the formal v2 charter.
> This research list itself does not authorize remote implementation.
>
> After scope approval, only obvious corrective defects from the v1.0.5 family
> beta may be added automatically. New feature ideas are parked for a later
> release unless the owner explicitly approves a scope change. HP is the
> future lab target; BOSGAME is not an automatic v2 deployment target.
> Historical findings and priorities below are research evidence, not a claim
> that every proposal is selected or that already delivered work is outstanding.

## 1. Direction

Aster Home 2.0 should keep the calm, warm Aster visual identity and Kodi as the
TV interface, while making each content detail screen behave like a modern
living-room application. The main change is not more decoration. It is a
clearer hierarchy:

1. identity and context;
2. one obvious primary action;
3. a compact set of secondary actions;
4. browsable content with stable directional focus; and
5. deeper information only when requested.

The implementation should borrow interaction patterns, not product artwork,
code, logos, layouts copied pixel-for-pixel, or another product's trade dress.
Approved Aster assets remain the only brand artwork.

## 2. Physical-client findings that shape v2

The HP ProDesk/LibreELEC test confirms that the design can remain visually rich
without becoming sluggish. Live tests passed TV series → season → episode
navigation and playback; album, song and Jellyfin-playlist playback; Daily
Digest story playback and moving highlight; Breaking News; Home status and the
local timer; eBook reader handoff; and all Books catalogue/synopsis views.

The test also found boundaries that v2 must treat as architecture work rather
than skin polish:

- Audiobookshelf catalogue data works, but audio cannot reach the private HTTPS
  reverse proxy at `192.168.50.23` from the client subnet. Do not bypass TLS,
  expose bearer credentials, or substitute token-bearing media URLs. Provide a
  reviewed, least-privilege route before claiming playback.
- Home camera status works, but the preview still references the disposable
  Mac's loopback SSH tunnel. Replace this with a reviewed production camera
  delivery path; do not open Frigate broadly to the media subnet.
- LibreELEC's MP3 player seeks this Digest recording inaccurately by absolute
  time. Aster 1.0.2 now derives a percentage from the verified total duration;
  the selected chapter and on-screen highlight then agree.
- The current sink advertises only 4K30 on the bench path. TV HDR indication,
  AVR passthrough and the selected Bluetooth/USB-HID remote remain physical
  gates, not v2 design assumptions.

## 3. What the reference products teach us

### tvOS and the Apple TV app

Apple's focus guidance is directly applicable to Kodi: every actionable object
must be reachable by directional input; focus should not jump without user
intent; and a focused item should gain elevation/illumination without crowding
its neighbours. The Apple TV app also keeps a show detail context above a
season-specific episode area, with play/resume as the primary action and
episodes, trailers, related content and details below.

**Use in Aster:** stable focus memory, visible but restrained focused-state
scale, hero/details above content, and a season selector immediately adjacent
to an episode list.

### YouTube on TV

YouTube's TV interface makes the left rail expandable, keeps Search reachable
from it, and organizes Home, Subscriptions, History/Watch Later and Playlists
as destinations rather than mixing them into one long page. Voice search is
available from destination pages, and a phone can search or manage the TV
queue.

**Use in Aster:** retain the disappearing Aster rail, add a global search entry
and future microphone affordance, and keep queue destinations explicit. Do not
wrap or imitate YouTube's watch page; launch and visually contain the official
Kodi add-on.

### Playback controls on television

Apple's system player keeps the moving picture dominant and limits custom
transport controls to the actions that matter during playback. Android TV
assigns the centre button to play/pause, left and right to bounded seeking, and
up/down to reveal information without pausing. YouTube places less-frequent
Audio, Subtitles and Quality choices behind a compact settings path rather than
giving each one equal visual weight.

**Use in Aster:** retain every control that Aster 1.0 exposes, but separate
frequency from availability. Use remote buttons for immediate playback and
seeking, one compact unboxed transport rail for visible controls, and a quieter
secondary group for Info, Audio, Subtitles and Quality. The video, title and
progress remain the hierarchy; the controls must not read as a large stone
dialog laid over the programme.

### Plex and Plexamp

Plex uses a useful hierarchy for television: series → seasons → episodes →
episode pre-play. It exposes unwatched episode counts at series level and can
hide season layers for single-season shows. Plexamp prioritizes current art,
queue context, Play Next/Later, related listening, album/artist radio, quality
information, smooth transitions and art-derived backgrounds.

**Use in Aster:** make episode browsing a purpose-built screen, not a generic
poster grid; make the Music player a listening surface with an Up Next lane;
and derive a subdued background colour/blur from art without sacrificing text
contrast.

### Audible

Audible separates the player from a simple chapter/episode list and supports
chapter navigation, adjustable narration speed, chapter-or-title progress,
bookmarks, a queue and sleep timers including end-of-chapter behaviour.

**Use in Aster:** preserve Aster's stripped-back two-column audio player, then
add only high-value listening controls that Audiobookshelf/Kodi can support
honestly: chapter jump, speed, sleep timer, progress and eventually bookmarks.

### Home Assistant

Home Assistant's current Sections view uses a responsive grid, grouped cards,
small at-a-glance badges, per-card features and conditional visibility. It
retains spatial memory by keeping related cards together as widths change.

**Use in Aster:** organize the Home page into named sections with fixed TV
positions, use badges only for exceptional state, and hide unavailable or
irrelevant cards instead of displaying empty shells.

## 4. Recommended 2.0 work, in priority order

### P0 — close v1 production dependencies first

1. Authorize and implement a narrow client-to-Audiobookshelf HTTPS path, then
   test audiobook chapters and podcast episodes for start, seek, pause, resume,
   stop and progress persistence.
2. Replace the Mac camera tunnel with a least-privilege production preview
   path, bounded by camera identity, short lifetime and read-only access.
3. Complete remote pairing/reconnect, TV HDR10 indication, AVR codec/
   passthrough and full-profile recovery tests.
4. Automate safe, atomic Books and Home feed publication with freshness and
   last-success visibility. Never make stale household state look current.
5. Return to official YouTube setup only after the core appliance gates pass.

These are 1.0.x completion items, not reasons to mix unfinished infrastructure
into the v2 visual branch.

### P1 — television series and episode detail

This is the highest-value v2 interface change.

- Keep a full-width, dimmed/graded series hero with title, synopsis, rating,
  year, genre and unwatched count.
- Make **Resume next episode** the primary green button. Use **Play from
  beginning**, **More info** and **Mark watched/unwatched** as secondary actions.
- Put compact season pills or a season chooser directly above episodes. Hide
  the chooser for single-season series; keep Specials explicit.
- Use a vertical episode list on TV: 16:9 still at left; `S02 E05`, title,
  two-line synopsis, duration and air date at right. Show three to five complete
  rows at once and a partial next row as a scroll cue.
- Keep progress bars, watched checks and unwatched dots in fixed positions.
  Focus should illuminate the whole row and expand by only a few percent.
- Restore focus to the prior episode after returning from playback or details.
- Place cast, extras, related titles and other seasons below the episode list,
  not between the primary action and the episodes.
- Treat alternate episode ordering and multi-episode files as metadata facts;
  never invent numbering in the skin.

### P1 — global shell and navigation

- Preserve the compact/expanded left rail but remember the last destination
  and focused item in each page.
- Add a global search overlay that can return Movies, Shows, Episodes, Music,
  Books and Podcasts in grouped results. Keep YouTube search within YouTube.
- Add a top-level **Continue** destination that unifies resumable video, audio
  and reading handoffs while clearly labelling the source and media type.
- Standardize Back: first close an overlay, then return to the parent content
  level, then expose the rail. Never strand focus in decorative controls.
- Standardize empty, loading, stale, offline and permission-denied states.

### P1 — appliance network status and diagnostics

- Add a remote-friendly **Network** panel to Aster Settings so basic
  connectivity does not depend on switching back to the stock LibreELEC skin.
- Show the active interface, connection state, IPv4 address, hostname, wired
  link speed or Wi-Fi signal, default gateway and DNS availability. Present
  sensitive identifiers such as the full MAC address only in an optional
  details view.
- Distinguish the failure layers in plain language: cable/link down, no DHCP
  lease, local network only, DNS unavailable, media services unreachable and
  fully online. Do not label an interface online merely because it has an IP
  address.
- Include **Refresh network**, **Reconnect** and **Copy/show diagnostics**
  actions where LibreELEC exposes safe APIs. Keep reboot as an explicit final
  troubleshooting action rather than the default remedy.
- Display the last successful Jellyfin and Audiobookshelf connection alongside
  current reachability, without exposing service credentials or token-bearing
  URLs. Network failure must produce a clear offline state instead of a generic
  playback error.
- Keep the summary readable at ten feet and available when media services are
  down. The panel must never require Internet access to report local link,
  address and gateway state.

### P1 — remote power, sleep and wake

- Capture the G20 power button's real Linux/Kodi event on every target client;
  do not infer it from the button legend or assume it matches OK's keyboard/
  mouse mode changes. Bind only the identified power event.
- A short power press should pause active playback, allow Kodi/Jellyfin to
  persist progress, and then request the operating system's supported suspend
  state. It must not silently power off, reboot, or expose a generic shutdown
  menu during normal couch use.
- Keep full shutdown and reboot as explicit Settings/Power actions. Do not
  overload a remote long press unless the receiver proves that it emits a
  distinct, stable event rather than repeated short presses.
- Treat wake as part of the same feature. The USB receiver must be permitted to
  wake only the intended client, and BIOS/UEFI, ACPI and LibreELEC must resume
  the GPU, HDMI link, network, audio device and receiver without manual input.
  Do not enable broad wake sources merely to manufacture a pass.
- Run at least ten sleep/wake cycles from idle and ten while media is paused.
  Record suspend and usable-UI times, wall power where available, remote
  re-enumeration, Jellyfin reconnection, retained focus, resume position, HDMI
  resolution/HDR state and receiver audio output. Include an overnight cycle.
- Abort the suspend mapping on any client that intermittently loses video,
  audio, networking, USB wake or Kodi state. Its documented fallback is Kodi
  idle plus display power management/blanking; label that honestly as
  **Display off**, not **Sleep**.
- Implement the final mapping as a separate v2 client-profile keymap with a
  rollback copy and per-hardware acceptance record. Do not retrofit the
  immutable v1.0.3 keymap before the HP lab client and BOSGAME production
  candidate pass this gate.

### P1 — compact video-player controls

**Milestone status, 2026-10-22:** the first implementation pass now replaces
the boxed video OSD with a lower-edge gradient, compact unboxed controls and a
thin sage/gold focus ring. The same reusable control treatment is applied to
Music, Books audio/Podcasts and Daily Digest without changing their Kodi
actions or data authority. This is deployed to the physical client with a
rollback checkpoint and included in the v1.0.3 deployment candidate.

- Remove the current 1800 × 370 stone panel and every persistent per-control
  box. Use only a restrained lower-edge black gradient for contrast over the
  moving picture.
- Preserve the current ten functions: Previous, −10 seconds, Play/Pause,
  +30 seconds, Next, Stop, Info, Audio, Subtitles and Quality. This is a visual
  simplification, not a capability reduction.
- Keep title and episode context at lower left, elapsed/total time at the ends
  of one thin progress line, and active resolution/HDR state as quiet factual
  metadata. Never claim HDR or 4K from filename metadata alone.
- Centre a compact icon-only transport rail. Play/Pause is slightly larger;
  all other transport icons share one smaller size. Unfocused controls have no
  background. The focused control receives a thin sage/gold halo, modest scale
  and elevation, with no clipped glow.
- Keep Info, Audio, Subtitles and Quality in a smaller secondary group on the
  same baseline. Labels may remain beneath their icons for ten-foot clarity,
  but the group must not compete visually with transport controls.
- Make the remote itself the fastest control path: centre toggles play/pause,
  left/right seek by the configured intervals, and up/down reveal the OSD
  without changing playback. OSD focus should initially land on Play/Pause.
- Keep Kodi as playback authority. Audio and Subtitle open Kodi's real stream
  selectors; Quality continues to show the active stream or Kodi processing
  settings when no alternate resolution exists; Info returns to the current
  full-screen information view.
- Auto-hide after inactivity, restore the programme without a residual panel,
  and retain a reduced-motion option. Opening a selector pauses the hide timer
  and Back first closes the selector, then the OSD.
- Standardize player exit semantics across Video, Music, Audiobooks, Podcasts
  and Daily Digest. Back may close an OSD, selector, queue or chapter panel
  without affecting playback, but leaving the full Aster player screen for its
  parent page must stop playback and release the active player. Do not allow
  hidden background playback merely because navigation changed windows.
- Keep an explicit **Keep playing** action available only if background
  playback is deliberately added later; never make it the implicit result of
  pressing Back.

The mockup below is a hierarchy and spacing target, not copied product trade
dress. The fictional programme still and generated layout are disposable;
production implementation must use the exact approved Aster logo and icon
assets already in the private brand package.

![Aster Home 2.0 compact media-player controls mockup](assets/aster-home-v2-player-controls-mockup.png)

### P1 — Music, audiobooks and podcasts

**Music**

- Add an Up Next queue to the right of the stripped-back player.
- Add a visible **Shuffle** control to albums, playlists and the active queue.
  It must use Kodi's real playlist state, preserve the currently playing track
  when enabled mid-session, visibly indicate its active state and remain
  distinct from Repeat.
- Support Play Next, Play Later, remove from queue, save queue as playlist and
  clear queue with confirmation.
- Add album/artist radio or “more like this” only when backed by real Jellyfin
  data; do not present random results as recommendations.
- Expose codec, bit depth/sample rate and output path in a quiet details layer,
  not in the primary controls.
- Use art-derived UltraBlur-style colour fields as inspiration, rendered with
  Aster's stone/green palette and contrast rules.

**Audiobooks**

- Keep cover/player left and unboxed chapter list right.
- **Confirmed v2 requirement — listening resume (2026-10-23):** save the current
  book position during playback and on pause, Stop and Back/exit; restore it
  when the book is reopened. Use Audiobookshelf as the progress authority so
  listening can continue across Aster boxes and other Audiobookshelf clients.
  Preserve whole-book position across chapters and multi-file books. Explicit
  chapter selection should still start the chosen chapter. Test restart,
  network outage/retry and conflicting updates without overwriting a newer
  saved position with zero. Current v1 audio playback and stop-on-exit work,
  but listening-progress save/restore is not implemented.
- Add current chapter, book progress, ±30 seconds, narration speed and sleep
  timer presets including end of chapter.
- Add bookmarks only after Audiobookshelf progress/bookmark authority and
  multi-client conflict behaviour are tested.

**Podcasts**

- Apply the same Audiobookshelf-backed resume behavior per episode: reopen at
  the saved timestamp, persist progress on Back/exit, and synchronize completed
  state across clients. Verify audiobook and podcast resume independently.
- Give each show a detail page with square art, synopsis and a newest/oldest
  order toggle.
- List episodes vertically with publish date, duration, two-line summary,
  played/progress state and download/availability state.
- Add Play Next/Later and a persistent episode queue; never auto-download or
  subscribe without an explicit user action.

### P2 — Aster Reader and synchronized narration

- Replace the television's URL-only eBook handoff with an Aster Reader for
  DRM-free, reflowable EPUB titles while retaining Calibre as catalogue and
  source authority. Do not modify source books or attempt to remove DRM.
- Use a dedicated reader service to sanitize and paginate EPUB XHTML, render
  each television page faithfully, and publish a bounded page manifest with
  stable text locations and word bounding boxes. Kodi should display the page
  and move one lightweight highlight overlay rather than trying to reproduce
  arbitrary EPUB HTML in skin labels.
- Narrate exact book text through Aster's canonical local Kokoro `bm_daniel`
  voice at the approved language, speed, cleanup and sentence/clause cadence.
  Do not create another application-local voice implementation.
- Extend the canonical batch speech contract to return validated phoneme/word
  timing, or align completed local audio against the exact source text when
  the approved model cannot expose duration data. Never estimate timing from
  character or word length.
- Buffer the opening sentences, then synthesize the remainder of the chapter
  through the lower-priority batch queue. Cache private derived chapter audio
  and timing manifests independently of the original book; make cache removal
  explicit and never distribute generated narration.
- Provide a calm reading page with adjustable type size, margins and line
  spacing; word, phrase or sentence highlighting; automatic page turns;
  Play/Pause; sentence/paragraph seeking; chapter navigation; narration speed;
  sleep timer; and a Follow narration toggle.
- Store resume state as a stable EPUB location plus text offset so reading and
  narration return to the same passage. Cross-device synchronization remains
  a later authority decision rather than a second uncoordinated progress store.
- Start with one real EPUB and one chapter. Gate expansion on timing drift,
  page-turn accuracy, pronunciation, first-audio latency, long-run queue
  behaviour and remote-only usability. PDF/OCR, fixed-layout books and complex
  interactive content are explicitly later work.

### P2 — Digest and Breaking News

- Keep the active story image and summary tied to audio position.
- Add a compact progress timeline with story boundary marks and Next/Previous
  story actions.
- Add **Read story** and **Sources** where the published feed provides safe
  links; distinguish generated summary from source reporting.
- Allow a briefing queue (morning, evening, saved stories) only after the news
  service publishes stable identities and durations.
- Preserve the fast Breaking News page as a separate glanceable destination;
  avoid turning the Daily Digest into an infinite news feed.

### P2 — Home dashboard

- Use a responsive four-column Sections-style grid on the 1080p design canvas.
  Camera and timer may span two columns; simple sensors use one.
- Add a restrained header badge row for security, indoor comfort, air quality,
  connectivity and active timers. Show exceptions before normal status.
- Group by intent—**Now**, **Rooms**, **Security**, **Climate**, **Routines**—
  rather than listing raw Home Assistant entities.
- Make controls visually different from read-only state. Require confirmation
  for security-sensitive actions and keep unavailable controls non-focusable.
- Preserve the current Aster timer ring, but source named Home Assistant timers
  when the integration is authorized; retain the local timer as an explicit
  fallback rather than silently conflating them.
- Camera cards should show freshness, privacy state and failure reason. Never
  leave a stale frame looking live.

### P2 — Aster screensaver and idle presentation

- Add an Aster-branded screensaver that activates after a configurable idle
  interval only when no video, audio, Digest narration or timer alarm requires
  the foreground. Audio playback may use a dedicated now-playing idle view;
  it must not be mistaken for a stopped session.
- Use approved Aster artwork, restrained motion and an OLED-safe layout that
  slowly moves or changes composition. Avoid permanent bright logos, static
  clocks, fixed metadata and heavy continuous animation.
- Offer a minimal clock/date option and, where appropriate, quiet now-playing
  art and progress. Never expose private household, camera, notification or
  book information on the screensaver by default.
- Wake on the first remote input without also activating the control beneath
  it. Preserve the previously focused item and restore the correct page.
- Coordinate Kodi dim/blank behavior with the television's power-saving
  settings. Provide explicit **Aster**, **Dim**, **Black** and **Disabled**
  choices, with Black as the conservative fallback for unsupported displays.
- Verify entry, wake, focus restoration, audio behavior and display mode after
  repeated idle cycles at both 1080p and scaled 4K.

### P2 — appliance startup branding

- Extend the accepted Aster startup sequence one stage earlier by replacing
  the HP firmware/POST image with an approved Aster-on-black logo. If visual
  silence proves preferable in the room, test a plain black image as the
  fallback; do not alter or redraw the approved Aster artwork.
- Treat this as firmware state, not a Kodi skin asset. The physical endpoint
  reports an HP ProDesk 400 G5 Desktop Mini with R23 BIOS 02.20.00 dated
  2023-12-15. HP's commercial BIOS utility supports a custom JPEG no larger
  than 32,768 bytes through `HpFirmwareUpdRec.exe -e<filename>` and removes it
  with `-x`; the operation is command-line only and requires a BIOS password
  file when an administrator password is configured.
- Prepare and validate an HP BIOS-recovery USB before changing the logo. Run
  the official utility from a temporary Windows or WinPE environment, never
  from LibreELEC and never through an unofficial firmware editor. Capture the
  current BIOS identity, utility log and clean-boot evidence before and after.
- Keep firmware maintenance separate from artwork installation. HP currently
  lists R23 02.22.00 for this exact model with later security fixes, but a BIOS
  upgrade is not required merely to test custom-logo support. Evaluate and
  authorize any firmware upgrade as its own recoverable maintenance change.
- Fail closed if the utility reports unsupported firmware, an invalid image or
  a security violation. Do not bypass firmware signing, Secure Boot, BIOS
  passwords or HP recovery protections to obtain a branded screen.
- Preserve the already deployed `/flash/oemsplash.png` LibreELEC image and
  `/storage/.kodi/media/splash.png` Kodi image independently. The desired
  sequence is firmware Aster mark → LibreELEC Aster splash → Kodi Aster splash;
  failure or rollback at one layer must not remove branding at the others.

### P2 — optional HDMI-CEC accessory trial

The production-connected HP exposes HDMI video/audio, EDID and hot-plug state
but no Linux CEC adapter: both `cec-ctl` and libCEC found no device. Native HP
HDMI therefore cannot carry TV-remote commands into Kodi or originate CEC
power/input commands. Keep the proven G20 USB-HID remote as the primary control
path.

Only if coordinated TV/receiver power or input selection is worth the added
hardware, test the external Pulse-Eight USB-CEC adapter in v2. Do **not** place
it inline on this media path: the current adapter is rated inline for 4K60
4:2:0 8-bit, while Aster requires HDR10 and high-bitrate receiver audio that
Pulse-Eight identifies as outside or unreliable in that path.

Use Pulse-Eight's two-cable topology instead. Leave the accepted HP HDMI → TCL
connection untouched for picture and sound. Feed a second, otherwise unused
TCL HDMI input from one of the HP's spare DisplayPort outputs through a
DP-to-HDMI adapter and the USB-CEC adapter, and connect its data lead to HP USB.
The second link is CEC-only; its physical HDMI port must be configured in
libCEC and must not become Kodi's display or audio sink. This should allow the
HP to request TV/receiver standby, wake/active-source and receiver volume, and
allow compatible TV-remote keys to reach Kodi, while preserving the existing
4K/HDR/audio path. It cannot guarantee that a powered-off HP will wake; treat
USB suspend wake and TV standby wake as separate acceptance tests.

Record adapter/firmware enumeration, logical and physical addresses, TV and
audio-system power status, active-source switching, receiver volume/mute,
TV-remote navigation, HP suspend/wake behavior, display/audio sink selection,
reboot recovery and ten repeated power cycles. Prevent command loops and
disable any action that unexpectedly powers down other HDMI devices. The
adapter must remain removable without impairing normal Aster playback.

### P2 — polish, accessibility and performance

- Define one focus contract for tiles, rows, pills, buttons and text fields.
  No clipped halos, exposed square image corners or title movement on focus.
- Offer reduced-motion and high-contrast variants. Test 10-foot readability at
  1080p and scaled 4K, including long titles and two-line synopses.
- Keep visible rows bounded and lazy-load artwork. Pre-cache only the selected
  hero and the next screenful; release artwork when a page closes.
- Keep periodic work bounded through Kodi alarms/short scripts. No permanent
  Python worker should be added merely to animate or poll a screen.
- Add automated focus-graph tests for every page and live smoke tests for every
  playable media type before a release candidate is installed.

## 5. Proposed delivery sequence

1. **2.0 design prototype:** compact video OSD, series/season/episode page and
   global focus contract using existing Kodi/Jellyfin data; no new service.
2. **2.0 alpha:** global shell, search overlay and media detail hierarchy.
3. **2.0 beta:** Music queue, audiobook/podcast refinements and Digest controls,
   after their production network paths pass.
4. **Appliance sleep proof:** capture the physical power event, implement a
   bounded suspend candidate, then prove USB wake and the repeated recovery/
   power matrix on the HP before testing the BOSGAME.
5. **Aster Reader proof:** one DRM-free EPUB chapter, canonical Aster narration,
   measured timing and synchronized highlighting; keep this service-dependent
   work independently reversible from the television UI branch.
6. **2.0 release candidate:** Home sections, accessibility, performance soak,
   remote-only navigation audit and recovery rehearsal.
7. **Optional appliance-branding gate:** with the release candidate otherwise
   stable, create the compliant firmware JPEG, prepare HP recovery media, test
   custom-logo install/removal from temporary WinPE, and retain evidence of a
   clean cold boot. This gate must not block the software release if the R23
   firmware reports custom-logo support as unavailable.

Each stage should be a separate resumable milestone with a local commit,
physical endpoint evidence and an immutable release package. Promotion should
not overwrite the last accepted v1 artifact or its rollback checkpoint.

## 6. Acceptance criteria

- Every visible action is reachable and reversible using only the selected
  remote; focus always remains visible.
- A user can reach the next unwatched episode from Home in three selections or
  fewer and can browse another season without losing their place.
- Every player exposes the controls appropriate to its media type and returns
  to the previously focused item.
- Leaving any full Aster player screen stops its active media unless the user
  has explicitly selected a future Keep playing action; closing a temporary
  player overlay does not stop it.
- Music albums, playlists and queues expose a working, visibly stateful
  Shuffle control backed by Kodi's actual playlist order.
- The video OSD exposes all ten accepted v1 functions without persistent
  button boxes; remote centre/left/right/up/down behaviour remains predictable,
  and focus is visible without obscuring programme content.
- The remote power button enters a measured suspend state only on clients that
  pass the repeated sleep/wake matrix; unsupported clients expose the honest
  Display off fallback and retain explicit shutdown/reboot controls.
- The Reader proof highlights the correct spoken passage without cumulative
  drift, turns pages at the right boundary and resumes the same EPUB location
  after restart; no book text or generated narration leaves the HomeLab.
- Empty, stale, offline and forbidden states are truthful and visually calm.
- The screensaver enters only under the documented idle conditions, wakes on
  one remote action without accidental activation and restores focus and
  display mode correctly.
- A user can identify link, DHCP, gateway, DNS and media-service reachability
  from Aster Settings using only the remote, even while the client is offline.
- No credential, token URL, private source path or household entity ID appears
  in skin XML, logs, screenshots or release archives.
- 1080p canvas scaling, 4K output, memory, temperature and artwork loading meet
  or improve the v1 physical baseline.
- The complete v1 skin and profile rollback remain independently usable.
- Firmware branding either displays the approved Aster image through a clean
  cold boot or remains untouched; its rollback restores HP's normal POST image
  without affecting the LibreELEC or Kodi splashes.

## 7. Research sources

- Apple, [Focus and selection](https://developer.apple.com/design/human-interface-guidelines/focus-and-selection/)
- Apple, [Interface fundamentals](https://developer.apple.com/documentation/technologyoverviews/interface-fundamentals)
- Apple, [Find things to watch](https://support.apple.com/guide/tvapp/find-things-to-watch-atvbb35c9fc3/web)
- Apple, [Customizing the tvOS playback experience](https://developer.apple.com/documentation/avkit/customizing-the-tvos-playback-experience)
- Apple, [Playing video](https://developer.apple.com/design/human-interface-guidelines/playing-video)
- Apple, [Remotes](https://developer.apple.com/design/human-interface-guidelines/remotes)
- Google, [Explore the YouTube app on your TV](https://support.google.com/youtube/answer/7583931?hl=en-GB)
- Google, [Latest improvements to YouTube on TV](https://support.google.com/youtube/thread/308597587/q4-24-quarterly-update-latest-improvements-to-youtube-on-tv?hl=en)
- Google, [Playback controls on TV](https://developer.android.com/training/tv/playback/controls)
- Google, [Change video quality](https://support.google.com/youtube/answer/91449)
- Plex, [Using the Library View](https://support.plex.tv/articles/200392126-using-the-library-view/)
- Plex, [Modern Layout](https://www.plex.tv/blog/choose-your-own-adventure-introducing-modern-layout/)
- Plex, [Plexamp](https://plexamp.com/)
- Audible, [Browse chapters and episodes](https://help.audible.com/s/article/browse-chapters-and-episodes?language=en_US)
- Audible, [View player settings](https://help.audible.com/s/article/view-player-settings)
- Audible, [Manage clips and notes](https://help.audible.com/s/article/manage-clips-bookmarks?language=en_CA)
- Home Assistant, [Sections](https://www.home-assistant.io/dashboards/sections/)
- Home Assistant, [Dashboard cards](https://www.home-assistant.io/dashboards/cards/)
- Home Assistant, [Badges](https://www.home-assistant.io/dashboards/badges)
- W3C, [EPUB Media Overlays 3.2](https://www.w3.org/publishing/epub32/epub-mediaoverlays.html)
- W3C, [EPUB Reading Systems 3.3](https://www.w3.org/TR/epub-rs-33/)
- Readium, [Navigator architecture](https://readium.org/technical/r2-navigator-architecture/)
- Readium, [Guided Navigation](https://readium.org/guided-navigation/)
- Kodi, [Python Window API](https://xbmc.github.io/docs.kodi.tv/master/kodi-dev-kit/group__python__xbmcgui__window.html)
- Kokoro ONNX, [duration-enabled model releases](https://github.com/thewh1teagle/kokoro-onnx/releases)
- HP, [Commercial BIOS (UEFI) Setup Administration Guide](https://ftp.hp.com/pub/caps-softpaq/cmit/whitepapers/HPBIOSSetup.pdf)
- HP, [R23 BIOS 02.22.00 for the ProDesk 400 G5 Desktop Mini](https://ftp.hp.com/pub/softpaq/sp156501-157000/sp156688.html)
- Pulse-Eight, [USB-CEC Adapter user manual](https://support.pulse-eight.com/support/solutions/articles/30000048842-usb-cec-adapter-user-manual)
- Pulse-Eight, [USB-CEC Adapter maximum resolution and two-cable topology](https://support.pulse-eight.com/support/solutions/articles/30000053070-what-is-the-maximum-supported-resolution-of-the-usb-cec-adapter-)
- Pulse-Eight, [CEC Adapter getting started](https://support.pulse-eight.com/support/solutions/articles/30000053516-getting-started-%E2%80%94-cec-adapter)
- Kodi, [HDMI-CEC and external adapters](https://kodi.wiki/view/HDMI_CEC)

