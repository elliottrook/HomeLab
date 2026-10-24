# Aster Media Library

This read-only Kodi video plug-in supplies the Aster Home skin with combined
Movies + TV Shows genre directories. Kodi smart playlists cannot mix those two
media classes, so the plug-in queries both local Kodi library collections over
JSON-RPC, filters their indexed genre metadata, merges the results in memory,
and emits normal Kodi directory items.

It does not write to Kodi, Jellyfin, or the media files. Movie items play their
existing Kodi library path; TV-show items open the existing Kodi seasons node.

v1.1 also merges resumed films/episodes with Up Next in Continue Watching.
For up to 24 recently watched shows it reads a complete bounded local episode
catalogue (2,000 maximum per show), selects the unwatched regular episode after
the last completed one, or provides an honest caught-up series card. No new
server credentials or watch-state writes. Existing episode resume takes
precedence; failed/truncated catalogues cannot imply being caught up.
