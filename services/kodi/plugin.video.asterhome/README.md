# Aster Media Library

This read-only Kodi video plug-in supplies the Aster Home skin with combined
Movies + TV Shows genre directories. Kodi smart playlists cannot mix those two
media classes, so the plug-in queries both local Kodi library collections over
JSON-RPC, filters their indexed genre metadata, merges the results in memory,
and emits normal Kodi directory items.

It does not write to Kodi, Jellyfin, or the media files. Movie items play their
existing Kodi library path; TV-show items open the existing Kodi seasons node.
