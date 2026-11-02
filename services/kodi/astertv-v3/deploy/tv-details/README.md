# AsterTV v3 TV details — bounded Stream M package

This package promotes the accepted v3 TV-series presentation without replacing
the proven v2 episode playback, queue-ownership or recovery engine.

Deployment order:

1. Copy the complete directory to a new target staging directory.
2. Run `deploy.py` against the exact frozen v2.0.7 baseline.
3. If upgrading the first v3 candidate, run `hotfix_dynamic_lists.py` instead;
   it removes every synthetic fixture item and enables OK dispatch for the
   dynamic seasons, cast and related-title controls.
4. Run `repair_digest_entry.py` to reconcile the already-installed, verified
   digest player with its launcher and restore the missing explicit entry call.
5. `hotfix_episode_art.py`, `hotfix_tv_connections.py`, and
   `hotfix_trailer_icon.py` are exact-hash upgrades for the successive live
   candidates; they bind the controller properties, size/connect the season
   and cast controls, and install the dedicated trailer glyph.

Each mutating script validates its host and exact input hashes, creates a
checkpoint under `/storage/.aster-checkpoints`, writes atomically and fails
closed on drift. `rollback.py` restores a named initial-deployment checkpoint.

Accepted installed state on both `AsterTV-Bedroom` and `AsterTV-Family`:

- final series manifest: `8e53c2cc8c1fdb16bc55111893a2986bb9d863e458e998cb48c356b05e6505a6`
- `SeriesPreview.xml`: `cf708381d77b137e17036b44899dca5ce352c7b7dd52efc935875c1b08d07a7d`
- `v3_series_extension.py`: `98c128cbd2d68016b7b2d0981fb1df1fd97a06395d4611975854e0e3d12a9`
- dedicated trailer icon: `b2d7d331f02ddbced8c5eb875c43d3d9a0bdcf1c758cd9e4369ed38392730c71`
- News launcher: `a06cfc95840d218d637671a025b147336cdf17318d0c1ac991d5eaf404e6ed25`

The actor-search add-on is local-library read-only. Trailer playback accepts
only the official YouTube add-on route already recorded in Jellyfin/Kodi. The
installer explicitly enables the packaged actor-search add-on and fails closed
if Kodi does not acknowledge that state.
