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
6. `hotfix_series_cache_bounds.py` attaches valid cached Seerr artwork before
   the page is shown and clamps/crosses episode boundaries through regular
   seasons only. `hotfix_series_cache_limit.py` is the exact-hash follow-up for
   the Bedroom-first candidate whose rendered-PNG limit was initially too low.

Each mutating script validates its host and exact input hashes, creates a
checkpoint under `/storage/.aster-checkpoints`, writes atomically and fails
closed on drift. `rollback.py` restores a named initial-deployment checkpoint.

Accepted installed state on both `AsterTV-Bedroom` and `AsterTV-Family`:

- final series manifest: `aa589c8939b627aa19f9ec9b7abf9a0852eb3b33595b8c884e2b56f8ddb2dba0`
- `default.py`: `f81658e70630ed5c4b8c6e995b073be6c8287faabf5127fac8c1335fbbff720a`
- `series_seerr_client.py`: `26615b4ca67745d60fd1ce60517fb4d4f2908407c4d2e44a40c4194c741e8c33`
- `SeriesPreview.xml`: `cf708381d77b137e17036b44899dca5ce352c7b7dd52efc935875c1b08d07a7d`
- `v3_series_extension.py`: `c4c183c0ada6f7b7152760b78d837e01d39f546a0ec8491c253949138ecaf111`
- dedicated trailer icon: `b2d7d331f02ddbced8c5eb875c43d3d9a0bdcf1c758cd9e4369ed38392730c71`
- News launcher: `a06cfc95840d218d637671a025b147336cdf17318d0c1ac991d5eaf404e6ed25`

The actor-search add-on is local-library read-only. Trailer playback accepts
only the official YouTube add-on route already recorded in Jellyfin/Kodi. The
installer explicitly enables the packaged actor-search add-on and fails closed
if Kodi does not acknowledge that state.
