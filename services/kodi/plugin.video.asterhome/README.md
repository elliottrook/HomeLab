# Aster Media Library

This read-only Kodi video plug-in supplies the Aster Home skin with combined
Movies + TV Shows genre directories. Kodi smart playlists cannot mix those two
media classes, so the plug-in queries both local Kodi library collections over
JSON-RPC, filters their indexed genre metadata, merges the results in memory,
and emits normal Kodi directory items.

It does not write to Kodi, Jellyfin, or the media files. Movie items play their
existing Kodi library path; TV-show items open the existing Kodi seasons node.

v1.1.1 merges resumed films/episodes with available Up Next in Continue Watching.
It reads the complete series directory (1,000-show bound), then the complete
bounded episode catalogue (2,000 per started show). It emits the next unwatched
regular episode only with an indexed playback path and no known future air date.
No caught-up/future placeholders or jumps over missing episode/season numbers.
An older started show can return when its next episode is synced; existing
episode resume takes precedence. The visible rail remains limited to 24 items.
Incomplete series reads retain genuine resumes rather than claim availability.
No new server credentials, downloads, metadata or watch-state writes. The home
directory is regenerated on refresh, not by a new background notification job.
