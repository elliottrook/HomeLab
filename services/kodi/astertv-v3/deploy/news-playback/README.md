# AsterTV Family News playback reliability repair

This bounded Stream M repair addresses Kodi retaining the last video item after
playback stops. The News player now treats *no active player* as idle while it
captures both native playlists and abandons ownership if direct digest playback
changes either queue. It never clears, removes, adds or reorders playlist data.

The installer is Family-only, pinned to the accepted pre-repair hashes,
checkpointed, atomic and idempotent. Kodi must be stopped. After changing the
four integrity-linked files it refreshes and verifies the host-bound accepted
release baseline, preventing the pre-Kodi guard from restoring the defect.
