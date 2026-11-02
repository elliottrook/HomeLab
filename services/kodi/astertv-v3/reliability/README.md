# AsterTV reliability guard

This package addresses the two recurring failure classes seen during the v2/v3
transition:

1. **Orphaned player recovery state.** Kodi/Jellyfin can finish clearing the
   player and queues after Aster Music has already latched
   `AsterV2Lab.TrialRecovery=required`. The persistent service clears only that
   volatile latch after three consecutive idle-and-empty observations and one
   final read. It never stops playback, changes a playlist, or removes the
   retained queue-intent/checkpoint evidence.
2. **Accepted-release drift.** A host-bound snapshot outside Kodi's add-on tree
   records every file in the Aster skin and runtime add-ons. A pre-Kodi systemd
   unit validates the immutable accepted payload and atomically restores only
   missing or changed accepted files. It never reads or changes Kodi userdata,
   account data, databases, caches, or unlisted extra files.

The release baseline must be refreshed only after the cumulative release has
passed its regression suite and live acceptance checks. A hotfix must not call
`snapshot`; this ensures an old overlay is repaired at the next Kodi start
rather than silently becoming the new accepted release.
