# Family media lifecycle repair

This bounded repair fixes two independent v2.0.7 client defects:

- Continue Watching no longer accepts a stale resume bookmark when Kodi also
  reports the item as played.
- the manual next-episode picker requests `playcount` and excludes watched
  episodes before selecting the following available item.

`repair.py` is Family-host-bound, refuses active playback, pins every input
hash, checkpoints every changed file, repins the search runtime guard and
manifest, refreshes the accepted release snapshot, and verifies it before
Kodi returns. Any failure restores the original files and leaves a recovery
marker naming the checkpoint.

The Jellyfin-side Intro Skipper correction is operational rather than packaged
in the client release: `repair_jellyfin_intro_skipper.py` installs the
checksum-pinned 12.0.5 archive transactionally. Jellyfin 12.1 requires that
build (`targetAbi` 12.1); version 12.0.6 targets Jellyfin 12.2. The repair
creates a ZFS snapshot plus a file checkpoint, retains the analysis databases,
disables plugin auto-update until the server reaches 12.2, and automatically
restores 12.0.6 if health or plugin-load verification fails.
