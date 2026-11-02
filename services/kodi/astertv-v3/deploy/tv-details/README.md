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

Each mutating script validates its host and exact input hashes, creates a
checkpoint under `/storage/.aster-checkpoints`, writes atomically and fails
closed on drift. `rollback.py` restores a named initial-deployment checkpoint.

Accepted installed state on both `AsterTV-Bedroom` and `AsterTV-Family`:

- series manifest: `bd4bffc5d94064142337243f2e3a21584c00e05059ccd7753aeabbdf6769207a`
- `SeriesPreview.xml`: `61502e614b786c513cd110cde5a399b6e842e695ca471533365e8e983816074a`
- `v3_series_extension.py`: `4e94f92818f4bf3ab4b48677426bffa6cc83c7e94c5ef9854ec2d087404903ef`
- News launcher: `a06cfc95840d218d637671a025b147336cdf17318d0c1ac991d5eaf404e6ed25`

The actor-search add-on is local-library read-only. Trailer playback accepts
only the official YouTube add-on route already recorded in Jellyfin/Kodi.
