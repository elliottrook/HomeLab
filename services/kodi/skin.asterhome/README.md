# Aster Home Kodi skin prototype

This is the M3a visual-shell prototype for Aster Home. It is deliberately
small and private: it provides the TV-first visual language and navigation
experiment before real Jellyfin, Home Assistant, news, podcast, audiobook and
recommendation data are connected.

## Current scope

- 1920x1080 / 16:9 Home window
- warm Home Hub palette and typography
- collapsed left navigation rail with a focus reveal affordance
- hero area and two media rows
- Kodi video-library containers as temporary content sources
- no production service writes and no Kodi core changes

The compass mark is a temporary text placeholder. The repository-owned Aster
logo asset and final typeface are deliberately separate follow-up decisions.

## Local test

From the Kodi add-ons directory, install this directory as `skin.asterhome`
or package it as a ZIP and use Kodi's add-on installer. The prototype has
debugging enabled so missing controls and invalid conditions are visible in the
Kodi log during the first visual pass.
