# Aster Home Kodi skin

Version 1.1.1 is deployed to HP and BOSGAME with owner-approved promotion.
Continue Watching includes available Up Next episodes, not caught-up/future
series placeholders; real Intro/Outro
markers drive explicit Aster Skip intro / Play next episode controls. TV hero
artwork falls back to inherited series fanart. No automatic skipping/playback.
See [v1.1 deployment, recovery and operator note](../../../docs/projects/Aster-Home-Version-1.1-Up-Next.md)
for verified evidence and the remaining household walkthrough gate.

Version 1.0.5 established the previous private deployment baseline. It retains
the v1.0.1 selection-dialog correction and uses percentage-based seeking for
Daily Digest MP3 chapters after the physical LibreELEC player proved inaccurate
absolute-time seeking. The complete Mac-validated interface and physical HP
ProDesk baseline now include cold boot, a 20-minute high-bitrate 4K soak and
live Music, Digest, News, Home and TV-episode tests, but do not yet claim
receiver-audio or destructive recovery gates. The selected G20 remote now has
a physical navigation and dynamic-list activation pass.
The source uses Kodi's 1920x1080
16:9 design canvas and scales to 4K output; media fanart remains independent
and can render at its native source resolution. See `RELEASE.md` for the
private deployment bundle, install order, client-state boundary, rollback and
hardware graduation checklist.

The final v1 scope adds the official Kodi `plugin.video.youtube` 7.4.4 as an
external dependency and a first-class Aster navigation destination. The skin
opens the add-on's own root catalogue and uses its maintained icon; it does not
fork, vendor or scrape YouTube. Google API/OAuth credentials remain private
per-client add-on state and are never stored in this repository or release
bundle. Blu-ray support is deliberately deferred to a possible v2 decision.

Version 0.8.20 gives Kodi's settings landing and category windows a restrained
Aster treatment. Required Kodi settings control IDs remain unchanged, while a
dark identity column, warm layered work surface, rounded controls, 24-hour
clock and sage/gold focus language bring system configuration into the same
visual family as the rest of Aster Home.

Version 0.8.19 replaces the seven single-media genre destinations with the
read-only `plugin.video.asterhome` companion. Each genre page now merges
matching movies and TV shows from Kodi's existing local library, alphabetizes
the shared result, plays movies through their indexed path and opens a show's
existing seasons view. Its browse heading identifies the active genre as a
combined Movies & TV collection. Landing-page previews remain native one-item
playlists. Kodi must enable the companion add-on after it is first installed.

Version 0.8.18 keeps Continue Watching, Recommended for You and Genre in Aster
ink in every focus state. The permanent black treatment gives all three rail
headings reliable contrast against the light stone field; tile rings retain
the navigation cue. Individual media and genre captions also remain black.

Version 0.8.17 added the dedicated Genre heading and established its reserved
space above the portrait rail.

Version 0.8.16 dissolves the full-screen hero artwork into the existing Aster
stone background while any genre tile is focused. The transition follows the
same 220 ms movement as the lifted media lanes, preserving the top-of-page hero
while giving the below-poster genre names a quiet, consistently legible field.

Version 0.8.15 adds Family as a seventh genre and narrows the complete rail to
seven evenly spaced 240-pixel lanes with 210 × 315 portrait artwork. All seven
choices fit across the established content width without changing the poster
ratio, caption treatment or peek/lift interaction.

Version 0.8.14 removes the dark caption plates from the genre portraits and
places each genre name beneath its tile in Aster ink, matching the established
media-poster treatment while preserving the initial artwork peek.

Version 0.8.13 adds a portrait genre rail beneath Recommended for You. Comedy,
Drama, Action, Sci-Fi, Documentary and Horror each use a randomly selected,
slightly washed local movie or TV poster. The rail deliberately peeks into the
initial viewport, lifts into view on focus, and opens a bounded local smart
playlist for the represented media type and exact indexed genre. It performs
no metadata write or remote lookup. Both preview and browse data use native
Kodi smart-playlist containers; no background script mutates a live GUI
control.

Version 0.8.12 adds a deliberate left inset and vertical centring to search
entry text, and strengthens the utility-field outline with Aster gold while
leaving the shared clock outline restrained.

Version 0.8.11 aligns the camera live-view action with the timer presets and
introduces one shared charcoal-and-gold treatment for every header clock and
the media, music, books and keyboard search controls. Stone texture remains
reserved for primary navigation and major actions.

Version 0.8.10 registers a dominant 80-point timer font and enlarges the timer
name so the countdown reads as the dial's focal point. It also preserves the
circular marker texture's aspect ratio when Kodi runs in a non-16:9 window.

Version 0.8.9 enlarges the digital timer readout and moves its timer name closer
so the two labels read as one centred unit inside the circular second markers.

Version 0.8.8 reduces the circular timer markers to 16 pixels so every second
has visible breathing room, then recentres the smaller ring within the timer
card and above the preset controls.

Version 0.8.7 reduces the timer markers to the midpoint between their original
and enlarged sizes, centres the complete ring horizontally within its card,
and keeps the completion wording safely inside the circle beneath the pulsing
Aster Home mark.

Version 0.8.6 gives each preset its full visible name, doubles the timer dots
from 14 to 28 pixels, and adds a five-second local completion state. When a
local visual timer reaches zero, Kodi pulses the existing Aster Home mark and
plays a bundled five-second chime; both effects clear automatically and perform
no Home Assistant or household action.

Version 0.8.5 replaces the perspective-sensitive radial pills with unrotated
circular dots. It adds a dedicated timer-name line and three bounded local
visual presets—1, 5 and 30 minutes—without calling Home Assistant or performing
any household action. The name field also reserves the Home Assistant timer
helper's validated friendly name for the later read-only connection.

Version 0.8.4 turns the timer into a larger, full-height black feature panel.
The separate circular face is removed: a wider, mathematically circular ring
of sixty longer pills now supplies the entire clock silhouette around the
centred digital display. The label and bounded test control remain inside the
same panel so the timer reads as one component rather than stacked cards. Live
Mac Kodi validation confirmed the complete and partially depleted rings on the
black panel, with no skin-load or timer-script error in the Kodi log.

Version 0.8.3 adds a bounded **Test 60 seconds** action to the Home timer card.
It drives only Kodi window properties: no Home Assistant timer or household
action is created. A one-second Kodi alarm recalculates the display from a UTC
deadline so delayed ticks do not accumulate drift, and page exit cancels the
test. Live Mac Kodi validation observed `01:00` with all 60 pills active,
`00:21` with exactly 21 active pills, and a clean `00:00` state with the ring
fully muted. The Kodi log contained no skin or script error during the run.

Version 0.8.2 keeps the timer card at 370 pixels but expands its dial to 360
pixels, centres a larger 56-pixel digital readout on the card, and replaces the
twelve broad marks with sixty radial pills—one for each second. The muted ring
is shown while no approved timer source is active. Each pill also has an
active sage layer driven by the bounded `AsterHub.HomeTimerSecond` property, so
the ring can deplete from 60 to 0 when the read-only timer feed is connected;
this visual milestone does not invent or start a household timer. The
transparency-preserving timer-base builder keeps the dial independent of the
card colour. Live Mac Kodi validation confirmed the complete ring and centred
reader with no skin-load error.

Version 0.8.1 enlarges the circular timer face from 280 to 340 pixels while
preserving its 370-pixel square card. It also proves an explicitly selected
Front of House preview inside the dashboard card. The disposable Mac pilot
reads Frigate's loopback-only latest-frame endpoint through a manually started
SSH tunnel on `127.0.0.1:15102`; it stores no camera credential, refreshes at a
bounded two-second cadence, stops on page exit or a second button press, and
expires automatically after five minutes. This is evidence for the interface,
not the production delivery architecture. Each LibreELEC client still needs a
monitored, least-privilege private bridge before this can be promoted.

Version 0.8.0 replaces the Home status list with a living-room Home Assistant
dashboard: fixed lighting, comfort and camera summary cards; a large camera
status surface; a compact validated-entity list; and a square timer card with
a central digital readout and twelve-position circular countdown treatment.
The existing pilot remains read-only. Camera imagery still stays inside
Frigate, and the timer displays an inactive state until an approved timer
source supplies countdown data. The Home publisher now separates snapshot
capture time from upstream registry activity, matching the Books freshness
contract.

Version 0.7.9 repairs the disposable Books catalogue publisher's freshness
contract. A snapshot is now dated when it is captured; the upstream library's
modification time is retained separately for audit. An unchanged library can
therefore be safely republished without being rejected immediately as stale.

Version 0.7.8 advances the Digest list's green story highlight from the same
bounded active index as its headline, synopsis, source and artwork. The
two-second sync queues Kodi's supported `Control.SetFocus` built-in only when
the chapter changes; it still avoids direct background access to the list
control.

Version 0.7.7 makes the visible Digest story follow audio chapter boundaries
every two seconds while the Digest window and its own audio remain active.
It uses Kodi's per-skin looping alarm to invoke a short, one-shot sync and
cancels the alarm as soon as the page unloads. It does not restore the
persistent Python watcher that previously crashed Kodi during shutdown, and
it performs no network read or live list-control access during a sync tick.
Mac playback followed multiple chapter boundaries, the alarm stopped on page
exit, and Kodi stopped playback and quit cleanly. LibreELEC remains a later
hardware validation gate.

Version 0.7.6 adds a read-only Breaking News sibling to the Daily Digest. A
two-tab Aster News header moves between the two views. Breaking News reads the
existing server-rendered `/` coverage, bounds it to 40 grouped stories and
shows the selected headline, summary and outlet labels beside a compact story
list. It does not autoplay, open source links, retain articles, or add a new
news-server endpoint. Missing or malformed coverage fails closed. This is a
local candidate pending Mac visual verification and LibreELEC testing.

Version 0.7.5 is a Mac Kodi pilot Digest-page candidate, not yet accepted on
LibreELEC. It reads the current Aster news briefing and its existing `/digest`
story cards, joins published headlines to chapter times, and shows available
source summaries and pictures beside a plain chapter list. The two-column
layout uses the same player language as Aster Books/Music. Missing source art
uses the approved Aster News icon. Playback and chapter selection are explicit;
Refresh also re-reads the currently playing audio time to show the story at
that chapter. The page does **not** continuously auto-follow chapter changes.
The first live Mac attempt to auto-follow with a persistent Python watcher
crashed Kodi on shutdown; the pilot files were restored from a checkpoint and
the watcher was removed from this candidate. A subsequent watcher-free quit
was clean. The live pilot loaded 19 stories and started the published audio;
seeking to a selected chapter worked once, but the corresponding panel/art
has not been consistently verified after Kodi reopens the Digest page. The
current local candidate uses Kodi's selected-list-item API for the chapter,
windowed playback, and a requested-chapter property to protect the startup
refresh race. This exact combination still needs a Mac visual check before
acceptance. Do not deploy this as an
automatic story-sync solution. It neither changes the news server nor stores
or republishes its content.

Version 0.7.4 builds Aster Music into five linked screens: the Recently Added
landing, then Albums, Artists, Songs and Playlists. The four icon-led pills
open the browse screens; Recently Added is reached from the Music launcher.
The pages share the media shell's full-width selected fanart blending into the
stone lower surface, rounded square cover tiles with labels beneath, and a
right-side search panel on browse screens. Selected artwork stays in the tile
lane, not a duplicate hero cover. Missing covers use the approved square music
icons centered on an ivory tile. Artwork and metadata come from Kodi's indexed
music library. Playlists are read from Kodi's `special://musicplaylists/` and
the logged-in Jellyfin Kodi add-on's playlist views (not the transient
now-playing queue); Aster does not store Jellyfin credentials. The page states
clearly when neither source is available. Selecting an artist opens its albums;
selecting an album, song or playlist opens the same two-column Aster player
with art, track list and transport controls. Playback starts only after Play
or a track is selected. Jellyfin playlist tracks use the existing add-on's
authenticated paths; Kodi-local playlist files remain Kodi-resolved. Search uses Kodi's indexed album/artist/song filters
across the full local library and shows the first 500 matches; the recently-added
landing shows up to 50 albums. Playlist search filters saved playlist names.
No background playback, media-file write or new credential is introduced.

## Player exit and Books focus (v1.0.5 candidate)

Leaving fullscreen video, the Music player, Books listening or Digest stops
playback. The G20 fullscreen Back/right-click now means Stop instead of hiding
the running player. Back within a playback dialog keeps its existing dismissal
behavior. Books listening waits for Kodi's native list to populate before
selecting the first real chapter/episode, and its parent entry returns to Books
home. Already-selected chapters are not moved by the focus helper.

The BOSGAME received these changes as checkpointed v1.0.4 hotfixes. Live checks
proved first-entry focus, later audiobook chapter playback at its offset,
podcast playback and no active player after Back. Movie resume after Back was
owner-confirmed. The complete v1.0.5 bundle is now installed on the BOSGAME;
the HP remains unchanged. Audiobookshelf listening-progress save and restore
are still **not implemented**.

On LibreELEC, the supplied `aster-books-refresh.service` and `.timer` refresh
audiobooks, subscribed podcasts, descriptions and missing covers through the
existing private HTTPS audio configuration. The timer runs after boot and every
six hours. EBooks remain the owner-accepted frozen snapshot, with their original
snapshot timestamp recorded separately. Failed or malformed upstream responses
do not replace or retimestamp the last good audio feed. Covers use Aster icons
if unavailable. No media files, subscriptions or listening progress are changed.
The 24-hour feed freshness check remains in place.

Check `systemctl status aster-books-refresh.timer aster-books-refresh.service`
and the private `feeds/refresh-status.json` file for timer health and the last
successful refresh. A service failure is reported through systemd/journal using
only a failure class; no credential or upstream private path is logged. Run
`systemctl start aster-books-refresh.service` for an immediate refresh.

## Books catalogue layout (v0.7.2)

The Books landing has eBook, audiobook and podcast lanes, with three matching
icon-led browse pages, a shared hero, 24-hour clock and right-side search.
Titles come only from the bounded, sanitized local `books.json` feed. The
current one-shot pilot contains 505 Calibre eBooks, 46 Audiobookshelf
audiobooks and seven subscribed podcasts. Separate bounded one-shot cover
copies provide 501 eBook, 46 audiobook and seven podcast JPEGs; missing art
uses approved Aster icons. Search filters the local catalogue and never
contacts a source service.

The feed includes plain-text, bounded source synopses for 141 eBooks, 41
audiobooks and all seven podcasts. Missing descriptions are not invented. It
contains no per-title added dates, cover binaries, file paths, playback URLs or
credentials. The cover cache is a separate local file set keyed by source ID.
Accordingly the audiobook row remains a **catalogue snapshot**, not "Latest
Added". The selected synopsis appears in the hero and the About button opens
the full text in a branded Kodi dialog. The eBook action hands off a validated
Calibre ID to the existing Calibre-Web reader: on the Mac it opens the title in
the default browser; on LibreELEC it displays a URL to open on another device.
This was verified on the Mac with a Calibre-Web title. Audio actions route
validated IDs to the local `plugin.audio.asterbooks` bridge, which is being
tested without a credential; actual playback has **not** been verified. The
official Audiobookshelf Kodi add-on was rejected for this use because it puts
its bearer token in artwork and media URLs. The Aster bridge uses private
HTTPS header authentication and loopback-only playback capabilities. Refreshing
the Mac pilot remains the explicit
one-shot `pilot_books_feed.py` step described below. Podcast covers can then
be copied by `pilot_podcast_covers.py`. These are manual Mac test-profile
operations, not a continuous publisher. The podcast browse page shows
subscribed shows; its action delegates episode browsing to the audio add-on.

## Kodi and LibreELEC startup branding

Kodi's startup image is separate from the skin. The 1920 × 1080
`branding/splash.png` places the unmodified, approved AsterTV production
lockup on a solid dark-green background. It was generated from the
checksum-verified `aster-brand-v2-tv-2026-10-22.zip` release with
`python3 tools/build_startup_splash.py ARCHIVE branding/splash.png`
(Pillow required). The builder verifies both the release archive and selected
1254 px PNG before composition; the original logo is not redrawn or bundled
separately.

For the disposable Mac Kodi profile, install the file as
`~/Library/Application Support/Kodi/media/splash.png` and restart Kodi. Check
for an existing `splash.jpg` first: Kodi prefers that filename over
`splash.png`. The Kodi app bundle and its bundled splash remain unchanged;
removing only this profile override restores the bundled startup image.

On LibreELEC, install the same approved asset in both supported locations:

- `/storage/.kodi/media/splash.png` controls Kodi startup; and
- `/flash/oemsplash.png` controls the earlier LibreELEC boot stage.

Use `tools/install_libreelec_startup_branding.sh` on the endpoint with the PNG
path as its only argument. The script checkpoints existing overrides under
`/storage/.aster-checkpoints`, refuses to continue if a higher-precedence
`splash.jpg` would hide the approved image, writes `/flash` only while it is
explicitly remounted read-write, and returns it to read-only even on an
interrupted install. Removing the two installed overrides restores the bundled
LibreELEC and Kodi images; restore checkpointed files if they existed.

The computer manufacturer's logo is firmware/POST output before LibreELEC owns
the display and cannot be changed by the skin or these overrides. Disabling a
firmware logo, if the model exposes that option, is a separate BIOS decision;
replacing firmware artwork is outside this project.

## macOS Kodi Dock icon (disposable test app only)

The Dock/Finder icon is an application-bundle resource, not a Kodi skin image.
On the disposable Mac pilot, run
`sh tools/install_macos_dock_icon.sh /tmp/Kodi-test.app` from this directory.
The script converts the existing approved `media/aster-icon-512.png` (Aster
compass on its stone surround) into macOS `kodi.icns`, checks Kodi's bundle ID
and declared icon filename, preserves the original next to the app as
`/tmp/Kodi-test.original-kodi.icns`, and touches the bundle for Finder refresh.
Finder shows the Aster icon on the test app. The installer restarts Dock to
refresh its cached icon, or reports if sandbox controls prevent that (run
`killall Dock` in a normal Mac shell then). This does not change Kodi's
menu-bar name, splash, or any installed `/Applications/Kodi.app`; do not use it on a
production/signed app without a signing and rollback plan.

To restore the disposable app's original icon, copy the saved `.icns` back to
`/tmp/Kodi-test.app/Contents/Resources/kodi.icns` and touch the app bundle.

Version 0.6.9 imports twelve right-sized PNG exports from the owner-approved
private `aster-brand-v2-expansion-2026-10-14` release. The release ZIP SHA-256
is `e030b6104fbdffb44faf035471f8c55320c3869065046a1ff5f9f0433069c48e`;
ZIP CRC and all 173 listed file hashes were verified before extraction. Books,
Music and Settings use their launcher icons in both rail states; Media, Books,
Music and Digest use their stacked product marks in page headers. The Music
album symbol labels the existing album list. Podcasts and the artist/song/
playlist symbols are packaged for future real views, not shown as dead
navigation. Existing Media, Home Hub and Digest launcher icons remain from the
approved original family. The Mac test showed the rail, Media and Books pages;
other views still need endpoint visual acceptance. No remote service changed.

Version 0.6.8 shifts the media hero's lower fade from ivory to a solid warm
stone colour on Home, browse and video-info views. The fade remains a plain
colour gradient, not a texture. The Home background matches its endpoint so
the queues meet the fade without a white strip. Mac Kodi was visually checked;
this is not LibreELEC/TV acceptance.

Version 0.6.7 replaces the stone clock with a dark translucent inset and a
subtle warm outline on the media and hub pages. Kodi's clock label requests
`HH:mm`, but the active regional preference still controls 12/24-hour display.
Set **Settings → Interface → Regional → Use 12 / 24-hour format** to
**24-hour clock** on each Kodi/LibreELEC profile; the disposable Mac test
profile was changed through Kodi's local settings API and visibly showed
`00:04` after midnight. This profile preference is not part of the skin add-on
and must be checked during endpoint setup.

Version 0.6.6 carries the approved limestone treatment into the search/filter
heading and keeps selected hero artwork visible, dimmed, behind the expanded
navigation rail. The lower ivory fade and interactive media copy/queues hide
while the rail is open. The Mac Kodi test confirmed the menu no longer opens
onto a blank canvas; this is visual acceptance only, not LibreELEC playback or
remote-control acceptance. No remote service changed.

Version 0.6.5 added a restrained limestone material to unfocused category,
filter and secondary-action pills, and initially to the clock pill. The clock
was revised in 0.6.7. Green primary actions and sage focus states remain solid for
contrast. `media/ui-limestone-panel.png` is cropped from the **limestone-tile**
layer of the approved Aster v2 `SVG/01-aster.svg`; it is not a redrawn or
AI-generated texture. Regenerate only from the SHA-verified release archive
with `python3 tools/build_limestone_surface.py ARCHIVE OUTPUT`. The source
archive is not bundled with the skin. Kodi on the Mac was restarted and the
media home visually checked after the texture change. No service or remote
Git state changed.

Version 0.6.4 displays a manual, ten-minute Home pilot. Run
`python3 tools/pilot_home_feed.py` from the skin directory to pull only the
approved VM 103 light/temperature snapshot and a bounded Frigate camera
online/offline status. Mac Kodi shows Laundry and the available closet
temperature; unavailable hall/outside values are omitted. The camera row is
status only: live view remains in the separately authenticated Frigate app,
not in Kodi. No frames, recordings, camera credentials, new firewall rule or
Home Assistant control actions are involved. Kodi's **Refresh** reloads the
local feed, not the servers; rerun the script after ten minutes. The v1 Aster
recording exporter remains separate and unchanged.

Version 0.6.3 prepares, but does not deploy, a three-entity Home Assistant
pilot: laundry light on/off and hall/outside temperature in °C or °F. The
offline exporter emits only reviewed aliases and valid bounded values; a v2
Home feed reader displays those values and omits unavailable readings. The
exporter is not installed on VM 103, no `home.json` has been delivered to
Kodi, and household controls remain disabled. A recovery checkpoint, exact
configuration review, Home Assistant validation and protected delivery path
are separate deployment gates. Read-only preflight found that an older v1
exporter is already live for Aster's no-effect recording pilot. The v2
candidate must not replace its file or schema; an isolated output path or a
tested consumer migration is required first.

Version 0.6.2 provides a manual, one-shot Books pilot. Run
`python3 tools/pilot_books_feed.py` from the Mac to query the existing TrueNAS
`library.json` over read-only SSH. The script filters on TrueNAS to just
Audiobookshelf audiobooks and Calibre ebooks, carries the source file's mtime
as the feed timestamp, validates the result, and installs it mode 0600 into
the disposable Mac Kodi profile. It prints counts only; it neither changes
TrueNAS nor exposes an endpoint. The live source contained 46 audiobooks and
no Calibre ebooks. The Books screen visibly displayed all 46 as a read-only
catalogue after Kodi restart. **About library** now explains that playback and
ebooks are not connected. Refresh reloads the local feed; it does not query
TrueNAS. This one-shot file expires after 24 hours. No personal titles or
source credentials are stored in Git. The Home feed remains absent and its
display remains explicitly unconnected.

Version 0.6.1 adds opt-in, credential-free local feed readers for Books and
Home. The skin reads only bounded JSON files under Kodi's own
`special://profile/addon_data/skin.asterhome/feeds/` directory. It neither
creates those files nor contacts the underlying services. A missing, malformed,
oversized or stale feed leaves an explicit unconnected screen; no sample data
is shipped as household data. The contracts are:

- `books.json`: `schema_version: 1`, a timezone-aware `generated_at`, and
  `items` from a sanitized unified-media library snapshot. Only
  `audiobookshelf/audiobook` and `calibre/ebook` records with an
  `authority_id` and `title` render, at most 80. The currently deployed
  library snapshot has Audiobookshelf records; a Calibre source is not yet
  confirmed there. The raw snapshot is **not** exposed by the portal API.
- `home.json`: the same version/timestamp envelope and a `snapshot` containing
  the Aster registry export contract. Snapshot v1 displays reviewed aliases
  only; v2 may also display approved light on/off and bounded temperature
  readings. Neither version provides controls, security or air-quality data.
  The exporter is offline and has not been deployed; a reviewed publisher
  would also need to add the timestamp envelope before Kodi can read it.

Books expires after 24 hours and Home after 10 minutes. Neither file may be
symlinked. The reader discards unexpected library authorities and fields and
does not offer acquisition or household-control actions. Offline tests use
synthetic records; at the 0.6.1 contract milestone no real book or home feed
was installed in the Mac test.
Next, define a protected read-only delivery route from the existing snapshots
to this Kodi profile, and separately design reviewed live-state aliases for
the richer Home Hub display. Do not expose `library.json` on the current
unauthenticated LAN portal or install HA's offline integration merely to
populate a test screen. These steps need their own risk review and deployment
authorization. The previous local milestone is `7bf22a7e`.

Version 0.6.0 adds a shared side menu and four matching destinations: Books &
Audiobooks, Daily Digest, Aster Home, and Music. The Aster Media entry returns
to the existing video home. Move Left from a hub action to reveal the menu,
Right to enter it, Up/Down to choose a destination, and Select to open it.
All hero marks are direct exports from the approved Aster v2 artwork family.

Music reads recently added albums and covers from Kodi's existing local music
library. **Play newest** queues up to 200 indexed tracks from the first album
and starts playback; Refresh only reloads the list. Album rows can be browsed,
but row-specific playback is not yet wired. Kodi's normal playback keys control
the audio. The live Mac test displayed 25 albums and opened the first album's
15-track playlist through the existing Jellyfin integration.

Daily Digest reads the existing published chapter metadata on the private LAN,
shows a bounded list of stories, and **Play selected** starts the published
audio at the selected story only on request. An edition older than 36 hours,
future-dated, malformed, or absent is treated as unavailable. Kodi's list
control does not reliably dispatch a row click, so the separate button is used
for chapter playback. The chapter panel after seeking remains a live-test gate.
This skin does not synthesize a new voice or store headlines in Git.

Books and Home show the intended information architecture and honest connection
states. The one-shot Audiobookshelf catalogue is available in the disposable
Mac pilot, but ebook, audiobook playback, Home Assistant and Aster
private-assistant adapters are not connected. Their rows do not operate
household controls. Those connections need bounded data contracts and approved
identity paths before they can function. No Kodi core,
production service, firewall or credential changes are included. Restore the
prior local commit `d4b6944b` to roll back this milestone; the Mac Kodi copy is
a disposable test installation. No remote push accompanies the local commit.

Version 0.5.8 vertically centres the home hero-copy/action block between the
header and queues, enlarges the existing horizontal logo to fill its header
slot, and gives category pages their corresponding approved icon. Hero scores
are labelled out of 10, with age classifications alongside when available;
the score is not a parental-control policy or a personal rating.

In a TV Shows, Movies, Archive TV or Archive Film category, choose **Genre** and
enter a genre fragment such as `Drama`, then choose Done. **Minimum score** accepts
a number from 0 to 10, including decimals. The two filters combine, retain the
category tag, and show active values on their buttons. Title search narrows the
current results further. **Clear all filters** restores the original category.
Cancel leaves existing filters unchanged; clear all before starting fresh.
Genre/score filters apply to these four category roots, not collection groups or
nested season/episode lists. Collections have no meaningful single numeric score.
Missing scores are not invented and will not pass a positive minimum threshold.
The small Python helper writes only its bounded generated view playlists under
`special://profile/addon_data/skin.asterhome/filters/`; it performs no library,
playback, artwork, network or server writes. Restore the prior local commit
`a58b2d77` to roll back this skin milestone; generated views are disposable.

Version 0.5.7 moves the category pills into the header, separated from the hero
actions, and uses the approved TV, Film and Archive artwork plus the supplied
Collections SVG rendered unchanged to a runtime PNG. Asset provenance and hashes
are recorded in `media/category-icons-provenance.json`.
Category pages now share the full-screen hero treatment and display rounded 2:3
portrait posters, with two-line captions. Existing library posters often include
the title in the artwork; this depends on the supplied poster, not the skin.
A separate left-hand cluster provides native title filtering, Clear search and
Reverse order. Select the search field to open the Aster on-screen keyboard,
or type using a physical keyboard. Filtering is confined to the current category.
More Info opens a matching artwork/poster/synopsis dialog. No server artwork,
library tags or media files are modified.

Version 0.5.6 adds a dedicated category lane with five 280×56 pills: TV Shows,
Movies, Archive TV, Archive Film and Collections. The queues move down and use
320×180 tiles so five tiles and both rows fit within 1080p. Up from Continue
Watching reaches the lane; Left/Right chooses a category, Select opens it,
and Back/Escape returns. A new Aster tile browser supports the video library.
Categories use existing Jellyfin-synced Kodi tags (`Shows`, `Movies`,
`Archive TV`, `Archive Movies`); Collections uses Kodi movie sets, not a new
server-side collection. These filters do not modify media or tags.

Version 0.5.5 replaces the split tile with full-screen 1920×1080 hero artwork.
A continuous left-side dark gradient keeps copy readable without a boxed panel;
the image fades into ivory behind the queues. Rounded Play (green) and More Info
(ivory) buttons switch to sage with a white outline when focused. Press Up from
Continue Watching to reach Play, Right for More Info, and Down to return.
Card artwork uses `scalediffuse="false"` so cropping cannot crop the rounded
alpha mask. Corners are truly transparent, not covered with ivory patches.

Version 0.5.4 presents a single rounded hero tile split evenly between solid
charcoal copy and artwork. The year follows the genre in green; the separate
year line and duplicate backdrop are removed. Navigation rails are square.
Continue Watching now uses paused episodes ordered by last played, with
captions such as `Dark — S1 E4` and actual episode resume bars. Hero headings
show the series name and the synopsis follows the selected episode. The
playlist is read-only and does not change playback history.

Version 0.5.3 preserves the full hero artwork in a fitted rounded image on the
right, with a subdued full-width backdrop and rounded translucent copy panel.
Hero metadata is reduced to the year. Media captions are plain ink text with
no boxes; playback percentages become rounded resume bars. All media cards,
focus outlines and navigation surfaces have rounded corners. Neutral raster
masks are reproducible with `python3 tools/build_surfaces.py`; existing Aster
brand artwork is unchanged. Filled bars were verified using a temporary
playlist of real movies with resume positions, then the normal TV row restored.
The current show-level TV row supplies zero PercentPlayed values, so its bars
remain empty until episode-level resume data is used.

Version 0.5.2 enlarges the media artwork from 320×180 to 400×225 with four
cards per row. Landscape art is preferred, followed by fanart and then the
library thumbnail. Captions and focus surfaces sit below the image so they
do not obscure it. The shorter hero and compact headings leave room for both
larger rows on the 1080p canvas. Existing brand assets are reused.

Version 0.5.1 makes the selected hero artwork fill the upper canvas, places
the approved logo and dynamic copy on a translucent charcoal panel, and adds
native-size charcoal caption boxes plus a correctly proportioned mint focus
surface to both media rows. The expanded rail is rendered above the page and
switches into a clean navigation state so labels and cards are not cut by it.
Hero copy uses the approved light rail text token over that panel so the
dynamic title, synopsis, metadata and actions remain readable against bright
fanart.
Version 0.5.0 made the selected hero artwork fill the upper canvas and added
the first layered queue treatment.
Version 0.4.0 adopts the owner-approved Aster v2 runtime exports, uses the
approved horizontal logo and tile-free compass in the shell, makes the hero
eyebrow/metadata/time dynamic, and gives focused media cards a stable mint
focus surface without zooming their geometry. The expanded rail now uses the
approved Home Hub and Media marks for its branded destinations; utility entries
retain simple Kodi-safe glyphs until matching approved exports exist. Version
0.3.0 reshapes the Kodi canvas around the Aster Home reference: narrow
rail, greeting/eyebrow hero copy, wide dynamic artwork, landscape media cards,
and dark caption overlays with live progress percentages. Version 0.2.1 adds a
two-line dynamic synopsis treatment with a local font face.
Version 0.2.0 adds a focus-aware dynamic hero: title, synopsis, artwork, year,
duration and playback path follow the selected Jellyfin/Kodi media item across
both home rows. Version 0.1.9 adds the optional timer manifest Kodi expects when
loading a skin.
Version 0.1.8 adds deterministic focus routing between the live Jellyfin-backed
media rows. Version 0.1.7 added the supplied Aster compass artwork as
Kodi-ready header and rail textures, plus a working tvOS-style disappearing
rail. Version 0.1.4
added the standard startup windows and settings scaffolding Kodi requires
before it will keep a custom skin active. The windows are deliberately small
Aster-owned shells; richer interactions and media-specific dialogs are the next
pass. The rail opens from the edge affordance, accepts vertical menu focus,
and collapses when focus returns to the media content.

The Home rows use Kodi library paths already populated by the installed
Jellyfin add-on. This keeps the skin read-only with respect to Jellyfin and
avoids embedding server URLs or credentials in the skin.

This is the M3a visual-shell prototype for Aster Home. It is deliberately
small and private: it provides the TV-first visual language and navigation
experiment before real Jellyfin, Home Assistant, news, podcast, audiobook and
recommendation data are connected.

## Current scope

- 1920x1080 / 16:9 Home window
- warm Home Hub palette and typography
- disappearing left navigation rail with a focus reveal affordance and focus map
- hero area with focus-aware live title, synopsis and artwork
- two-line live synopsis block with metadata-safe clipping
- two landscape media rows backed by Kodi's Jellyfin-populated video library
- caption overlays with live `ListItem.PercentPlayed` values
- explicit Up/Down routing between media rows
- Kodi video-library containers as temporary content sources
- no production service writes and no Kodi core changes

The artwork is sourced from the owner-approved private Forgejo release
`aster-brand-v2-2026-10-14`, package SHA-256
`2c770b52cfc04cb90d49f01bec1067566e9b1e3c89fd9235a82c0e86be6bcffc`.
The add-on carries only right-sized PNG exports: the 128/512 px Aster mark,
horizontal and compass marks, and the approved Home Hub, Media, News Digest,
Audiobooks and monochrome utility marks. The 20 MB SVG masters and the full
family release remain outside this add-on. The handoff explicitly limits the
family to private Aster/HomeLab use; this prototype does not assert public
trademark, font or redistribution clearance.

## Video playback controls

Version 0.8.25 adds Aster-owned `VideoOSD`, `VideoFullScreen` and seek-overlay
contracts. During full-screen video, Kodi's normal OSD action now opens a
large remote-first control panel with playback identity, elapsed/total time,
progress, previous/next, discrete −10/+30 second seeking, pause/resume, stop
and information controls. The skin changes presentation only; playback and
all actions continue to use Kodi's built-in player.

Version 0.8.26 extends that panel with Audio, Subtitles and Quality controls
and adds Aster-styled runtime settings and full-screen information dialogs.
Audio and subtitle buttons expose Kodi's real stream selectors and related
offset/passthrough controls. Quality opens Kodi's resolution picker when the
active player advertises alternatives; direct-play files normally expose only
their active video stream, in which case the button shows that resolution and
Kodi's video-processing settings. Info now opens the current title,
series/episode/year, synopsis, time and progress instead of doing nothing.

Version 0.8.27 makes both information paths explicit. The playback OSD closes
before opening `fullscreeninfo`, while the Media landing page restores focus
to its selected media container before requesting the standard Kodi video
information dialog. This avoids the no-op caused by invoking `Info` while the
button itself, rather than a media item, owns focus.

Version 0.8.28 adds watch-state cues to the Media landing rails and the
TV/movie library grids. Unwatched movies and episodes use a small standalone
sage dot, watched titles use a sage check, and TV-show/season cards display
Kodi's live `UnWatchedEpisodes` count. Resumable items deliberately show only
their existing progress bar so an in-progress title cannot also appear fully
watched. The skin reads Kodi library metadata and does not maintain a parallel
watch-state database.

The first Aster Home 2.0 visual milestone introduces shared player-control
includes without changing playback behaviour. Video now uses a full-width
lower-edge gradient, one thin progress line and compact unboxed transport and
stream controls. Music, audiobook/podcast and Digest players use the same
focus ring and remove their enclosing player cards in favour of open gradients.
Music and Books page tabs and Media category buttons use restrained translucent
charcoal backplates so they remain legible over variable hero artwork, while
secondary Digest actions remain visually quiet until focused. Search fields
retain their explicit input affordance but no longer sit inside a large
enclosing card. The accepted milestone and subsequent remote activation fix
are packaged in the private v1.0.4 deployment candidate.

## Local test

The Books pages show bounded, plain-text source synopses and a full-text About
dialog. Titles without source descriptions explicitly show that no synopsis
is available. The visual cards use full-bleed rounded art with portrait eBook
and square audio/podcast shapes, while missing-art tiles retain an Aster
fallback. "Read this book" opens the corresponding Calibre-Web title in the
Mac's default browser; this was verified with a real title and its browser
reader control. On LibreELEC it shows the reader URL for a phone/tablet.
"Listen in Kodi" and "Browse episodes" route to Aster's private audio bridge,
which has synthetic byte-range tests but no credential or live playback test.
Those audio actions are not yet verified as playable. The local feed and art cache still
contain no readable eBook file or authenticated audio stream.

From the Kodi add-ons directory, install this directory as `skin.asterhome`
or package it as a ZIP and use Kodi's add-on installer. The prototype has
debugging enabled so missing controls and invalid conditions are visible in the
Kodi log during the first visual pass.
