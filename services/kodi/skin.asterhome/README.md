# Aster Home Kodi skin prototype

Version 0.6.5 adds a restrained limestone material to unfocused category,
filter and secondary-action pills, and to the clock pill across the media and
hub pages. Green primary actions and sage focus states remain solid for
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
shows a bounded list of stories, and **Listen** starts the published audio only
on request. An edition older than 36 hours, future-dated, malformed, or absent
is treated as unavailable. The chapter list is browsable; selecting an
individual chapter is not yet guaranteed on this Kodi list control. This skin
does not synthesize a new voice or store headlines in Git.

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

## Local test

From the Kodi add-ons directory, install this directory as `skin.asterhome`
or package it as a ZIP and use Kodi's add-on installer. The prototype has
debugging enabled so missing controls and invalid conditions are visible in the
Kodi log during the first visual pass.
