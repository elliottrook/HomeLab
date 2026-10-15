# Aster Home Kodi skin prototype

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
