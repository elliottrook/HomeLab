# playlist-bridge

Dependency-free bridge for playlist export files → Lidarr → Jellyfin. It supports:

- CSV/TSV with common `title`/`track`, `artist`, `album`, and `isrc` columns;
- Spotify account-data `Playlist*.json` exports;
- Apple Music/iTunes library XML (select a playlist with `--playlist-name`);
- extended M3U/M3U8 entries formatted as `artist - title`.
- public Spotify playlist links (read through Spotify's public embed metadata; no login required).

The bridge first matches every source track against Jellyfin. Missing tracks cause an album lookup
and album request in Lidarr. Because Lidarr is album-oriented, a playlist track may acquire its
whole album. The Jellyfin playlist is not replaced until every source track is present, preventing
silent partial playlists. Run it periodically after Lidarr and Jellyfin have had time to import.

After adding an album, the bridge explicitly queues Lidarr's `AlbumSearch` command. This works
around Lidarr's `searchForNewAlbum` bug when the requested album is monitored but its parent artist
is deliberately left unmonitored to prevent full-discography acquisition.

Incomplete playlists wait up to 24 hours by default. The timer is persisted in `state.json` beside
the config and resets when the source playlist changes. After the deadline, the bridge creates a
partial playlist containing every matched track and reports the omitted tracks. Override the delay
with `--max-wait-hours`; the bridge must be invoked periodically for the deadline to fire.

Spotify's public embed metadata currently omits album identity. Link tracks already present in
Jellyfin can be matched, but unmatched tracks are reported as `needs-album-metadata` and are never
sent to Lidarr until a reliable album-enrichment step is available.

Copy `config.example.json` outside git, add dedicated API keys and discover the Lidarr profile IDs
from `/api/v1/qualityprofile` and `/api/v1/metadataprofile`. Confirm Lidarr's container root path;
in this homelab the host path is `/mnt/Media/data/media/music`, but its API may require `/music`.

```sh
# Safe preview (still performs read-only API calls)
python3 playlist_bridge.py --config /path/to/config.json /path/to/playlist.csv

# Request missing albums; on later runs, replace the Jellyfin playlist once complete
python3 playlist_bridge.py --execute --config /path/to/config.json /path/to/playlist.csv
```

Exit status is `0` when complete and `2` while tracks are missing. Keep the config and source
exports out of git because they may contain credentials and private listening data.
