# AsterTV v2.0.5 lab recovery bundle

This is the accepted **lab code and non-secret configuration** for the HP
AsterTV at `192.168.1.140`, running LibreELEC nightly
`20261021-440640e` and Kodi 22 RC1. Production remains on v1.1.1 with stereo
audio. The bundle is not a production promotion.

## Bundle contents

- `astertv-v2.0.5-code-only-lab.tar.gz`: 12 Aster add-ons, 574 files,
  SHA-256 `730cee0755607c79b4dbf4a8d2fe110f901bda851b7d09da51258555584c6bc7`.
- `g20s-pro-plus.xml`: Kodi remote keymap, installed at
  `/storage/.kodi/userdata/keymaps/g20s-pro-plus.xml`.
- `aster-books-refresh.service` and `aster-books-refresh.timer`: the
  six-hour, non-AI Books feed refresh, installed in `/storage/.config/system.d/`.
- `README.md` and `manifest.json`: this recovery guide and exact file hashes.

The archive is a code overlay. Before applying it, checkpoint the installed
add-ons and Kodi user profile, verify the target runtime and package hash, and
use the existing bounded install/rollback procedure. The archive must not be
unpacked blindly over a running Kodi profile. The disposable rehearsal in
`services/kodi/v2/tools/rehearse_code_only_archive.py` verifies safe members,
all add-on identities, exact files, interrupted rollback and preservation of
user data.

## State to restore separately on a fresh client

The following is deliberately absent from Git and from the bundle:

1. Jellyfin and YouTube account sessions and YouTube API credentials. Sign in
   through their normal private setup flows. Do not copy a production profile.
2. Restricted Audiobookshelf, Seerr browse and Acquisition TV identities.
   Provision them privately to the lab; never place token values in a commit,
   release record or support message. The lab uses
   `/storage/.aster-private/seerr-token` and
   `/storage/.aster-private/acquisition-token`, both mode 0600 inside a mode
   0700 directory. Music/Books request submissions require the latter.
3. The Books feed, cover cache and client settings. Rebuild the feed from its
   authorized source, start the packaged refresh timer and check its first
   successful run. The live lab's feed is under
   `/storage/.kodi/userdata/addon_data/skin.asterhome/feeds/`; cover cache is
   local user data. Set the client clock to 24-hour format and restore its
   Music library configuration. Watch and listening history remain with the
   local profile and services.
4. Home Assistant dashboard connectivity, News Digest source, and any camera
   or speech identities. The lab camera service remains disabled; the G20
   microphone and speech credential are not yet present.

The lab has private checkpoints under `/storage/.aster-checkpoints/`, including
`astertv-lab-keymap-20261029`, `astertv-lab-books-refresh-20261029`,
`astertv-lab-books-feed-20261029`, `astertv-lab-books-covers-20261029`,
`astertv-lab-seerr-identity-20261029`, and
`astertv-v205-manifest-reconcile-20261029`. They are recovery evidence, not
substitutes for fresh credential provisioning. Do not publish them.

## Acceptance and remaining gates

The live HP matches all 574 archive files byte-for-byte after the two
checkpointed manifest repairs. Music, Movies, TV season preview, Books lists,
global Search, YouTube browse/Search/Watch Later, Requests tabs and News
Digest entry have been exercised on the lab. The Requests hub completed the
two-press Music path using the already tracked *Homogenic* album and retained
its `available` result on reopen, without a second send. The package rehearsal
passed full and interrupted rollback.

Audible audiobook/podcast playback, Seerr and Books request submission,
physical voice input, camera activation, next-day recommendation rotation and
Dolby passthrough still have separate acceptance gates. Keep production on
v1.1.1 stereo until those are resolved and a production deployment is
explicitly authorized.
