# Aster Home Kodi skin prototype

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
- hero area and two media rows
- explicit Up/Down routing between media rows
- Kodi video-library containers as temporary content sources
- no production service writes and no Kodi core changes

The Aster compass mark is supplied as user-owned artwork and is rasterized for
Kodi as `media/aster-icon-128.png` and `media/aster-icon-512.png`. The source
SVG is approximately 20 MB and is retained outside this add-on. It has no
embedded copyright or licence metadata, so these textures remain internal
Aster artwork until provenance and distribution rights are recorded.

## Local test

From the Kodi add-ons directory, install this directory as `skin.asterhome`
or package it as a ZIP and use Kodi's add-on installer. The prototype has
debugging enabled so missing controls and invalid conditions are visible in the
Kodi log during the first visual pass.
