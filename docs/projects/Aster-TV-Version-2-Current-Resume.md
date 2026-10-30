# AsterTV Version 2 — Current Stream A resume

Updated: 2026-10-29. Owner: Jason. Lab: HP `192.168.1.140`.

## Lab regression repair after owner walkthrough — 2026-10-29

The broad regression report exposed a clean-client assembly failure. The
v2.0.3 archive installed add-on code but did not install the Aster remote
keymap or provision the client data and identities expected by the pages.
Every installed component and skin pin checked out before repair; this was
not a random corruption of the add-on files. The recovery recipe still names
LibreELEC 12/Kodi 21 and assumes an already configured v1.1.1 client, whereas
the reinstalled lab is LibreELEC 13/Kodi 22 with a fresh profile.

The missing keymap was restored from the versioned G20/keyboard map, with a
checkpoint at `/storage/.aster-checkpoints/astertv-lab-keymap-20261029`.
Kodi's restart log confirmed the map loaded. A lab TV library selection then
opened the v2 season/episode preview at window `13001` and returned to the
library with no active player. Music needed a separate client flag and a
bounded catalogue repair: Kodi's full song read had 221 omissions from its
enriched artist join and 46 unresolved artist IDs affecting 204 songs. The
adapter now recovers all 23,610 songs, discards only unresolved artist links
in memory, and reports the reduced credit quality. Its 22 tests pass; a live
album selection opened a 16-track page without starting playback. Checkpoints
are `/storage/.aster-checkpoints/astertv-lab-normal-music-20261029` and
`/storage/.aster-checkpoints/astertv-lab-music-catalogue-20261029`.

Kodi 22's Settings category template was incorrectly nested inside its
dynamic category list. Moving the template outside made the brown pane's
Skin, Regional, Screensaver, Master lock, and Startup buttons visible. Live
Right/Left input moved between the category pane and the settings. A movie
selection from the native movie library now opens the ID-verified v2 details
page with no autoplay; Back returns to the movie library. The movie route,
search overlay pin, and Back behavior have separate lab checkpoints named
`astertv-lab-movie-entry-20261029`,
`astertv-lab-search-select-sync-20261029`, and
`astertv-lab-movie-back-20261029`. Search was reopened after the pin update
and the lab was idle.

The credential-free v2.0.4 lab repair archive is
`services/kodi/dist/astertv-v2.0.4-code-only-lab.tar.gz` (13,142,749 bytes,
658 members, SHA-256
`7a0d45665978b28179b0ba6d73a7e6150d97c8c441f1f8541e4fa0e0dd25b416`).
Its separate keymap is `services/kodi/dist/astertv-v2.0.4-lab-keymap.xml`
(SHA-256 `befaf9072814579d4727d8f75ab78e4136abeaec371decc5f34b719e6800b320`).
All component, music, and skin hashes inside the archive pass. This is a lab
repair overlay, not a clean-client installer; the per-client music flag,
24-hour clock setting, private credentials, and feeds remain separate. The
release record is `services/kodi/releases/aster-home-v2.0.4-lab-candidate.json`.

The subsequent v2.0.5 lab overlay added Ebooks, Audiobooks and Podcasts to
global Search using the bounded local Books feed. An exact-ID result opens its
Books page; Back restores the Search query and selected result. A temporary
three-item feed proved all eight groups appeared and an audiobook result
opened and returned without playback. The test feed was removed and its prior
absence recorded at
`/storage/.aster-checkpoints/astertv-lab-books-search-fixture-20261029`.
The code checkpoint is
`/storage/.aster-checkpoints/astertv-lab-books-search-20261029`. The
credential-free v2.0.5 archive is
`services/kodi/dist/astertv-v2.0.5-code-only-lab.tar.gz` (13,143,943 bytes,
659 members, SHA-256
`730cee0755607c79b4dbf4a8d2fe110f901bda851b7d09da51258555584c6bc7`).
All 8 component manifests, the music manifest and the skin pins pass. Its
release record is `services/kodi/releases/aster-home-v2.0.5-lab-candidate.json`.

The real lab Books feed was rebuilt from the read-only TrueNAS snapshot and
validated before installation. It contains 505 ebooks, 46 audiobooks, and
7 podcasts; the Books page showed the corresponding populated rows. Its
private feed is at `/storage/.kodi/userdata/addon_data/skin.asterhome/feeds/books.json`,
checkpointed at `/storage/.aster-checkpoints/astertv-lab-books-feed-20261029`.
This one-shot feed expires after 24 hours. Jason approved reusing the existing
restricted Audiobookshelf configuration from the Mac pilot, matching the
earlier HP/BOSGAME setup. The Mac source was a 0600 regular file and its API
returned HTTP 200. A private SSH-stdin installer created only the lab's
previously absent `client.json` as 0600 beneath a 0700 profile, checkpointed
at `/storage/.aster-checkpoints/astertv-lab-books-identity-20261029`; no key
was printed, placed in argv, saved in Git, or left in staging. The lab API
returned HTTP 200. Kodi was idle before its restart. The live loopback bridge
resolved 36 audiobook entries and nine podcast entries; both first entries
returned HTTP 206 and exactly 4096 bytes of audio through localhost. The
Audiobooks and Podcasts pages showed 46 and seven titles respectively, and
selecting a title opened its real listening list with no active player.
Audible playback and Back/stop still need a short owner-approved test because
they may update listening progress. A separate interactive helper remains
staged at `/storage/.aster-staging/configure_lab_books_client.py` for future
fresh-client setup; it takes a key only in a hidden private terminal prompt.
The packaged non-AI Books refresh service and six-hour timer were restored
from `services/kodi/libreelec/`, with absence checkpoint at
`/storage/.aster-checkpoints/astertv-lab-books-refresh-20261029`. The manual
refresh and timer's first run both succeeded; the latter recorded 53 audio
items, 505 retained ebooks, and its next run six hours later. This refresh
uses the Audiobookshelf API and the lab's local feed, not the AI stack. The
previous 24-hour expiry gap is closed while the timer keeps passing.

Audiobookshelf returned HTTP 404 for an audiobook cover, so the fresh lab
could not reconstruct the prior art from that API. Production had 554 regular,
opaque-name JPEG cache entries. These were read from production, verified and
copied to a private lab stage; the lab installer added only 547 absent entries
and preserved its seven existing covers. The lab checkpoint is
`/storage/.aster-checkpoints/astertv-lab-books-covers-20261029`. The first ten
Audiobooks tiles all resolved to cached JPEGs. No production file was changed.

The Home Assistant publisher and receiver were reconciled to the lab's new
SSH host key. The lab receiver accepts only the established source-IP-limited,
forced-command Home Assistant delivery key. An initial 63-reading snapshot
was installed, and a one-shot live publication returned `ok: true` with
63 readings at 17:44 PDT. The unmodified Home Assistant publisher also
delivered its next automatic edition at 17:47 PDT with 63 readings. The lab checkpoint is
`/storage/.aster-checkpoints/aster-home-delivery1`; the source host-key
checkpoint is `/config/aster-checkpoints/home-delivery-lab-hostkey-20261029`
on Home Assistant. Home displayed real data and the 24-hour clock after the
repair.

The News digest's existing source served HTTP 200 at 17:48 PDT with a current
19-chapter edition generated at 17:28 PDT. The lab News page opened at window
11111 with focus on its Play control and no active player, then returned Home.
The news playback/return path was not rerun during the regression repair.

The lab camera proxy and a new lab-only SSH key are prepared at
`/storage/.aster-camera`, checkpointed at
`/storage/.aster-checkpoints/astertv-lab-camera-prepare-20261029`. Its service
is disabled and the Frigate source does not yet authorize this key. Enabling
it requires the owner's pending confirmation for the Frigate remote change.
Voice cannot be live-tested yet: the fresh lab exposes only Intel PCH capture,
while the guarded voice policy expects the G20 remote at `hw:1,0`, and its
separate STT identity is absent. The lab Seerr and Acquisition broker tokens
are also absent, so Requests and Seerr search remain blocked on lab identity.
No production files were changed; production remains v1.1.1 stereo.

## Lab Media and YouTube acceptance update — 2026-10-29

Jason reported a stale Media recommendation hero, 12-hour clock, missing
YouTube thumbnails, broken pill/Back navigation, and an empty Watch Later
page. The Media plugin now chooses within rank bands using the local date and
refreshes the Home widget once when the day changes. The lab's Kodi setting
`locale.use24hourclock` is `24hours`; the original GUI settings are in
`/storage/.aster-checkpoints/astertv-lab-24h-20261029`. The hero refresh code
is installed and unit-tested, but an actual next-day change remains for owner
observation.

The official YouTube 7.4.4 add-on is signed in to Jason's intended lab account;
Jason confirmed its subscribed channels. Its sign-in and sign-out routes
reopened their dialogs after completing, so Kodi was restarted after sign-in;
the session persisted and the normal YouTube menu showed `Sign Out`. The custom
skin formerly left focus on controls hidden by the new route. Root focus now
recovers to a visible pill, and each pill route hands focus to Kodi's native
item list. A live remote test reached Subscriptions from the root, moved down
its 51-item list, and returned using the on-screen Back button. Jason confirmed
that the remote navigation now works.

The original Watch Later pill targeted the add-on's empty local SQLite list.
The current signed-in account is configured for its online `WL` list. The
official `plugin://plugin.video.youtube/special/playlist/WL` route returned
51 items on its first page with thumbnails; both Watch Later pill buttons and
the landing row now use that route. Jason confirmed his Watch Later content
appears and navigation works. The general YouTube landing also showed populated
Subscribed Channels and Trending rows with thumbnail art. The add-on's
My Subscriptions video feed can still return an upstream HTTP 404, so the
landing uses its working subscribed-channel list instead.

Checkpointed lab installs are
`/storage/.aster-checkpoints/astertv-v2-ui-acceptance-20261029`,
`/storage/.aster-checkpoints/youtube-root-focus-hidden-control-20261029`,
`/storage/.aster-checkpoints/youtube-pill-route-focus-20261029`, and
`/storage/.aster-checkpoints/youtube-online-watchlater-20261029`. During
diagnosis, two Kodi 22 processes crashed when a temporary in-process probe
called `getListItem` on the native panel; systemd restarted Kodi. That probe
was removed, the crash reports were retained on the lab, and subsequent
directory/count/focus probes and the owner walkthrough succeeded. Avoid native
panel item enumeration through that Python API on this runtime.

The credential-free v2.0.3 lab code update is
`services/kodi/dist/astertv-v2.0.3-code-only-lab.tar.gz` (13,141,699 bytes,
658 members, SHA-256
`bedee92f711fe62b3e18921cf7b9fa8e2421117030cd678886461da8bc1c90af`).
It overlays the pinned v2.0.2 archive with the tested Media plugin files,
YouTube navigation XML, focus helpers and refreshed family pins. The archive
passed a 12-add-on, 573-file isolated full-install and interrupted-rollback
rehearsal while preserving a disposable userdata sentinel. The release record
is `services/kodi/releases/aster-home-v2.0.3-lab-candidate.json`. It remains a
lab code update, not a clean-client installer; the 24-hour Kodi setting and
account credentials are separate. Production remains on v1.1.1 stereo.

## Production rollback and v2 lab hold — 2026-10-28

### Reinstalled lab discovery — 2026-10-28

Jason updated the HP lab. Its SSH host key changed; Jason explicitly approved
the new ED25519 fingerprint
`SHA256:CFJcdaUaL72BX/yg6wsxksJs6UXSSDpnXQuWVTco61c`, which was checked
against a fresh key scan before login. Both HP lab and BOSGAME production now
report LibreELEC `nightly-20261021-440640e` and Kodi 22 RC1 revision
`01d4146d5d251a0118b99a1de0d713395c93bd46`.

The lab is a clean install: no Aster, official YouTube, or Jellyfin add-ons,
no Aster staging tree, and no old lab backup under `/storage/backup`. The
default `LibreELEC` hostname was restored to the established `AsterTV` name
with its original file retained at
`/storage/.aster-checkpoints/astertv-lab-hostname-20261028/hostname.before`.
The read-only `/etc` filesystem refused `hostnamectl set-hostname`, so the
guarded successor updated LibreELEC's persistent cache hostname and the
runtime hostname; both verified as `AsterTV`. No reboot was needed.

Jason supplied the temporary default LibreELEC SSH login after the clean
install. An existing Mac public key was installed and key-only access
verified. The SSH service's password authentication and keyboard-interactive
authentication were disabled in the LibreELEC service override, with exact
on-box checkpoint at
`/storage/.aster-checkpoints/astertv-lab-ssh-key-only-20261028`.
After sshd restarted, key login succeeded, password-only login was refused,
and the checkpoint state was finalized as `password-disabled`. This removes
default-password *SSH access*; it does not rotate the local root password.

V2 was **not** installed during discovery. The existing recovery recipe still
declares LibreELEC 12/Kodi 21 and assumes a preconfigured v1.1.1 baseline,
Jellyfin, YouTube and separately provisioned restricted lab identities. The
source package is not a clean-client installer. Reconcile this fresh-client
boundary and obtain separate lab account provisioning before live v2 install;
do not import production tokens or profile databases.

Follow-up clarification: Jason intended a fresh OS/Kodi slate and expected
HomeLab service access except YouTube to remain available. Key-based SSH works.
Read-only lab probes returned HTTP 200 for Jellyfin `/health` and Audiobookshelf
`/ping`; the restricted request broker answered HTTP 401 without credentials,
confirming its route but not a signed-in session. Direct Seerr timed out,
consistent with its documented broker-only isolation. These network results
do not restore Kodi's removed add-ons or authenticate a new Jellyfin/Books
client. The next lab install should reuse the existing restricted service
design with fresh lab-only client provisioning, while YouTube waits for
Jason's separate sign-in. No production account state should be copied.

### Fresh Kodi 22 lab candidate installation — 2026-10-28

The lab now has Kodi's official YouTube 7.4.4 and InputStream Adaptive
22.3.23.1 packages, plus their repository-installed dependencies. Jellyfin's
published repository ZIP still points at a metadata URL returning HTTP 404;
the matching official Python 3 Jellyfin 2.2.0 package and its Kodi modules
were fetched from the live upstream package indexes, path-validated and
installed without importing any production profile or token. Jellyfin account
setup is not complete. Its lab route at `192.168.20.40:8096` is reachable.

The 12-addon, code-only Aster v2 archive with SHA-256
`13d586ae3a30ba03ccc9ea3f2f291e337b814d38dc1805dbbc998d690c4b8f7d`
was installed on the fresh HP lab after verifying that all targets were
absent and playback idle. Its pre-install Kodi userdata is retained at
`/storage/.aster-checkpoints/astertv-v2-fresh-lab-install-20261028`.
Kodi registered all 12 add-ons, they were enabled, and the Aster v2.0.0
skin rendered on the lab. This is a **test installation**, not release
acceptance. The archive did not preserve the empty `skin.asterhome/fonts`
directory, so the lab installer now recreates it.

Jellyfin's own setup dialogs initially rendered without text because they
reference standard Kodi `font12` and `font13` aliases absent from Aster's
`Font.xml`. Those aliases were added to the tracked skin and installed on
the lab with the predecessor retained at
`/storage/.aster-checkpoints/astertv-v2-jellyfin-fonts-20261028`.
After idle Kodi restart, the server-selection text and manual server address
were visibly correct. Jason authorized Jellyfin 2.2.0 Quick Connect from his
MacBook without a password in chat; no code or credential is recorded here.
The lab uses the add-on playback mode. Initial sync completed in 6:28 and
populated the v2 smart playlists: 134 Archive TV series and 76 Shows series.
Archive TV series, season and episode grids were navigated visibly. A short
episode played in Kodi and was then stopped. Jellyfin's own Skip Intro button
appeared, and Aster's marker reader returned real Intro and Outro windows for
that episode without printing token or item ID. This does **not** yet prove
recap, credits/next-episode activation, or the absence of conflicting prompts.
The fresh Jellyfin profile had intro and credits buttons enabled but recap off;
the lab-only recap setting was changed to button mode through Kodi after
checkpointing settings at
`/storage/.aster-checkpoints/astertv-v2-jellyfin-skip-settings-20261028.xml`.
The change read back correctly and survived one idle Kodi restart; the synced
210-series library remained available through Kodi JSON-RPC. A live
recap/credits test remains open; do not seek near credits in the owner's
account merely to test a prompt because that could alter watched state.

The main TV page now visibly lists 76 shows. The YouTube landing and search
keyboard render, and a public query reaches the official add-on, but results
show its `key.requirement` message because this clean lab has no YouTube API
credentials. Do not import production credentials; Jason will provision the
lab from his MacBook. A separate v2 navigation defect was reproduced: the
landing visually highlighted Search while Kodi retained focus on hidden view
50, so Select opened Archive Movies. The lab skin's YouTube-root onload now
runs `youtube_root_focus.py`, waits for Kodi's native view 50 to become focused
(bounded to 10 seconds), then focuses the real Search button. An initial fixed
1.2-second wait failed once after the credential-install Kodi restart; the
event-based revision handled that race. The lab log showed native focus 50 and
a subsequent Select visibly opened the YouTube search keyboard. The predecessor
skin XML is checkpointed at
`/storage/.aster-checkpoints/astertv-v2-youtube-root-focus-20261028.xml`.
The production-payload builder and its unit test now include this helper;
this does not authorize production promotion. The clean OS removed the old
YouTube credential installer stage, so its tracked, secret-free installer and
parser were restaged on the lab for hidden MacBook SSH entry. Jason's MacBook
public SSH key was added to the lab allowlist with the prior entry preserved;
the exact prior file is checkpointed at
`/storage/.aster-checkpoints/astertv-lab-macbook-ssh-20261029.authorized_keys.before`.
Jason ran the hidden-prompt installer. Its non-secret verification returned
`configured: true`, owner-only file mode, and Kodi active. A fresh visible
Search-button test submitted `Kodi` and displayed real YouTube video results
with thumbnails. No credential value was read or transferred by this task.
Unauthenticated subscriptions/recommendation widgets
also produce add-on errors and stay empty. The News Digest page loaded a
current 20-story briefing; its dedicated audio player started, displayed
story progress, and was stopped after a short test. Physical lab audio and
YouTube playback acceptance remain open. Production remains on
owner-confirmed v1.1.1.

### Kodi 22 lab skip and digital-audio recovery — 2026-10-29

Jason corrected the fresh-install assumption: the established v1.1 lab
disabled Jellyfin's own intro/credits popups while leaving media segments
enabled, so Aster's marker-owned prompt retained focus. The fresh Jellyfin
2.2.0 profile had native intro, recap and credits buttons enabled by a
temporary setup script; a live Intro marker showed native dialog 12901 and
suppressed Aster dialog 11125. After stopping playback, the lab add-on
settings were checkpointed at
`/storage/.aster-checkpoints/astertv-v2-jellyfin-native-popups-20261029.xml`.
Only those three native skip modes were set to Off; media-segment reading
remained enabled. The temporary enable script was removed from source.

The Aster `next_episode.py` helper now reads typed Recap markers and offers
an explicit Skip recap button alongside its existing Intro and Outro behavior.
The predecessor helper is checkpointed at
`/storage/.aster-checkpoints/astertv-v2-next-episode-20261029.py`.
Live Kodi 22 tests: on a previously played episode, Aster Skip intro appeared
without Jellyfin's overlay and Select sought from 2:30 to the true 2:59.579
marker end. On an already-watched episode, Aster Skip recap appeared for a
0:00–1:20.08 marker and Select sought to its end. A real credits marker at
47:05.254 displayed Play next episode; Select opened the indexed following
episode, which was stopped after verification. All three tests used actual
Jellyfin segment data, not estimated timestamps. Ten skip-helper tests and
nineteen movie-player tests pass locally. The lab Search/movie component guard
was resealed with both the new helper hash and the fresh official Jellyfin
player hash; its native `verify_stage` passes. The exact prior files are at
`/storage/.aster-checkpoints/astertv-v2-skip-runtime-20261029`.

The short initial Intro probe created a resume bookmark on an unwatched test
episode. Its Kodi bookmark was cleared with `VideoLibrary.SetEpisodeDetails`
and read back as unwatched/no-resume. The Jellyfin server still held 179
seconds, so the local OpenAPI `UpdateItemUserData` route was used for that one
mapped item, changing only position/percentage to zero while preserving
Played, PlayCount and Favorite. A fresh server read returned zero ticks;
Kodi's local database has no resume bookmark. Normal test play count and
last-played timestamps were not rewritten.

The HP's clean OS install also removed the tracked
`snd_hda_codec_hdmi enable_all_pins=1` setting. Before repair, ALSA listed
only analog despite a connected LG HDR 4K display, and the module parameter
was `N`. The absent predecessor is recorded at
`/storage/.aster-checkpoints/astertv-lab-hdmi-pins-20261029.json`.
After restoring the exact tracked HP config and rebooting the idle lab,
the parameter became `Y` and ALSA exposed HDMI 0/1/2. Kodi's newly enumerated
HDMI 0 option matched the connected LG display; the prior analog selector
was checkpointed at `/storage/.aster-checkpoints/astertv-lab-hdmi-audio-20261029`
and normal stereo output switched to HDMI 0 with passthrough off. Kodi opened
`hdmi:CARD=PCH,DEV=0` and retained it across an idle Kodi restart. Physical
audibility awaits Jason's check; Dolby passthrough remains unvalidated.

The 2026-10-29 lab passthrough investigation found a hardware-path gate, not
a Kodi setting to toggle: the connected `LG HDR 4K` DisplayPort/HDMI 0 ELD is
valid but contains just one two-channel LPCM descriptor and no encoded Dolby
or DTS format. Other HDMI ELD entries are disconnected. ALSA maps the LG to
device 3, and saved Kodi settings retain HDMI 0 stereo with passthrough off.
Kodi's stored codec flags are dormant while passthrough is off. No encoded
stream was forced into this unadvertised sink; a Dolby playback test here
would risk silence and could not establish end-to-end passthrough. The old
HP/TCL/eARC profile is a different physical chain. A real fix/test requires
the lab to be connected to a Dolby-capable receiver/TV route and its live ELD
to advertise the intended codec, followed by a checkpointed known-format
playback test and receiver-display confirmation. The stereo profile remains
unchanged while Jason's physical audibility check is pending.

Jason clarified that the goal is to isolate the HP/Kodi output stage before
retesting on the Dolby-capable production chain. Kodi's startup enumeration
advertises generic raw stream types even for the LG HDMI 0 device, so two
six-second, checkpointed live probes used an already-watched six-channel
E-AC-3 episode. With passthrough temporarily true, both Kodi's existing
Optimized output mode and a temporary Best Match mode played the E-AC-3
source but opened ALSA HDMI 0 with `AES0=0x04` (PCM). Kodi's ALSA source uses
`AES0=0x06` for the non-audio/raw path. The corrected second and third probe
results reported `sink_mode: pcm`, `passed: false`, `restored: true`. Their
checkpoints are `/storage/.aster-checkpoints/astertv-lab-eac3-path-20261029-v2`
and `-v3`; the first probe's source-codec-only success criterion was explicitly
rejected as a false positive. The corrected guarded probe source is
`services/kodi/v2/tools/test_lab_eac3_passthrough_path.py`. Playback is
stopped, and an independent saved
settings read confirms HDMI 0, passthrough off and Optimized mode restored.
This test therefore does **not** exonerate the AsterTV/Kodi output stage or
prove that encoded frames left the HP. Physical wire-level proof still needs
a Dolby-capable sink or compatible HDMI audio analyzer/capture device; then
the same raw-sink check, receiver indication and rollback should be repeated.

The credential-free v2.0.2 lab source archive was built from committed tree
`37a1eecb` at
`services/kodi/dist/aster-home-v2.0.2-lab-candidate-source.tar.gz`.
It has 1,960 entries and SHA-256
`5874ca91c1bc775fd6b1528bf491a1d374c746122d1f7d3d6a76d3fa38a936c7`.
Archive members were checked for credential/profile files and path traversal;
none were present. This is a source and recovery-record package, **not** a
clean-client installer or production deployment bundle. The tracked release
boundary is `services/kodi/releases/aster-home-v2.0.2-lab-candidate.json`.

A separate lab-only code update archive is
`services/kodi/dist/astertv-v2.0.2-code-only-lab.tar.gz` (13,196,100 bytes,
657 unique members; SHA-256
`9c89d3e95a6deb35377bf5b3a042e80e73c3657b0ed6c80eb46396046f8debb1`).
It overlays seven pinned live lab files, including the new YouTube Search focus
helper, on the preceding 12-add-on code-only archive (SHA-256
`13d586ae3a30ba03ccc9ea3f2f291e337b814d38dc1805dbbc998d690c4b8f7d`).
The result was checked for duplicate members, unsafe paths and account/profile
files; none were found. This is an update payload for the already-provisioned
lab, **not** a fresh-install recipe: it does not carry the HP HDMI kernel
setting, Kodi audio selection, Jellyfin's native popup modes, or YouTube and
Jellyfin credentials. On 2026-10-29, the exact SHA-pinned archive passed an
isolated install/file-integrity/rollback rehearsal on macOS and on the HP's
LibreELEC 13/Python 3.14 runtime. Both normal and interrupted installs left
the disposable Kodi userdata sentinel intact. See
`services/kodi/v2/tools/rehearse_code_only_archive.py`. This did not install
the archive into live Kodi, activate add-ons/services or prove full clean-client
provisioning; those release gates and production authorization remain open.
The 19 historical untracked diagnostic and repair scripts are triaged in
`docs/projects/Aster-TV-Version-2-Untracked-Triage.md` and excluded from the
archive. The production stereo and Dolby findings are in
`docs/projects/Aster-TV-Version-2-Audio-Passthrough-Research.md`.

Jason reported the v2 player had lost skip recap/intro/outro and directed that
v2 be pulled from production. This is a release-blocking regression; the v2
candidate is **not production-ready**, even where individual pages passed
earlier checks. The production pre-v2 checkpoint was confirmed to contain the
four v1.1.1 add-ons and remote keymap. Its SHA-256 was
`d077c42505824856be88d9b65c78fcbb5f0d7bffc7203fe64164465da7d9aa5d`.
Jason confirmed playback stopped, and the Kodi TCP JSON-RPC reported no active
player immediately before the bounded rollback.

`rollback_prod_to_v111.py` restored only those four v1.1.1 add-ons and the
v1.1.1 remote keymap. It parked all 12 currently installed Aster add-on
directories in the private on-box checkpoint
`/storage/.aster-checkpoints/astertv-v2-pull-20261028`. It did **not** restore
old Kodi databases, watch history, add-on account state, YouTube credentials,
playlists, display or audio settings. The checkpoint state is
`v1.1.1-active`; Kodi restarted and is active, the skin reports 1.1.1, the
v1 skip helper exists, and the player is idle. The last 200 Kodi log lines
contained no errors. Kodi's startup enumeration again reset its audio selector
to the system default; with playback idle, the known connected HDMI 0 selector
was set live and read back. Physical sound and player-control confirmation
remain pending from Jason. Do not restart Kodi blindly until the HDMI 0
enumeration problem is understood. Jason subsequently confirmed that the
v1.1.1 interface looks right and sound works. A physical skip-control playback
check was not performed during the rollback.
The v2-only `aster-camera.service` was found active and enabled after the UI
rollback; the pre-v2 archive contains neither its unit nor its proxy. It was
stopped and disabled, then verified inactive/disabled while Kodi stayed
active. Its unit and proxy files were retained for recovery; no camera
credentials were read or changed.

The v2 code fixes through commit `76540e91` are retained on
`codex/astertv-v2-recovery` for a lab-only candidate. The remaining gate is to
bring the HP lab client to the production LibreELEC 13 nightly / Kodi 22
versions, install the candidate there, and repair/retest recap, intro and
outro controls together with TV seasons/playback, News Digest, YouTube search,
audio output persistence and the rest of the release acceptance. No v2
re-promotion is authorized by this rollback. No Forgejo/GitHub push was made.
The original, now-superseded credential-free source and recovery-record package was
`services/kodi/dist/aster-home-v2.0.1-lab-candidate-source.tar.gz` (1,946
archive entries, 23 MiB), SHA-256
`97c312324b3f220bf0c46ef99edea54b7438d3a5f1d5e0c595189541c84e9e51`.
It is **not** a clean-client install image or production deployment bundle;
see `services/kodi/releases/aster-home-v2.0.1-lab-candidate.json`. Focused
offline checks passed: 24 season/YouTube/production-builder tests and 8
next-episode tests. The actual Kodi 22 skip regression remains unresolved.

## Historical production regression recovery — superseded by rollback

Jason reported Books, News Digest, Cameras and Requests unavailable; old TV
landing pages; misaligned Search pills; broken YouTube navigation; clipped
YouTube text and rows; and an unreachable catalogue-search selection path after
the 2026-10-27 promotion. The repair target is `AsterTVProd` (`192.168.1.157`),
running LibreELEC 13 nightly and Kodi 22. The HP lab at `192.168.1.140` is on
LibreELEC 12.2.1/Kodi 21 and was left unchanged.

Takeover and repair evidence on 2026-10-28:

- After the TV playback check, Jason reported system-wide silence. Kodi was
  unmuted at 100%, but the active normal sink was the PC's analogue output;
  passthrough targeted HDMI 1. ALSA/ELD showed only `Beyond TV` on HDMI 0 as
  connected and valid. The earlier `audio-before-receiver-20261023-0825`
  checkpoint recorded a working TV stereo profile. With no active player, an
  exact-predecessor script saved Kodi's prior settings privately at
  `/storage/.aster-checkpoints/astertv-tv-audio-20261028`, restored normal and
  passthrough selectors to HDMI 0, disabled passthrough, and selected stereo.
  Runtime values verified and Kodi reopened `hdmi:CARD=PCH,DEV=0` without
  fallback. Jason confirmed sound is back. Surround passthrough remains
  deliberately disabled until separately validated.
- Jason then requested receiver passthrough. The connected `Beyond TV` HDMI 0
  ELD advertises AC-3, E-AC-3, TrueHD and multichannel LPCM, but the earlier
  DTS-HD test silenced the eARC chain until the receiver was rebooted. Two
  guarded live attempts to set codec controls refused and restored stereo;
  their checkpoints are marked rolled back. With Kodi stopped, an exact
  five-setting XML edit installed the documented 7.1 PCM/Dolby-only profile
  at checkpoint `astertv-dolby-passthrough-offline-20261028`: AC-3, E-AC-3
  and TrueHD enabled; DTS/DTS-HD disabled; AC-3 transcoding off. Kodi's
  restart reselected analogue and disconnected HDMI 1 despite the saved
  HDMI 0 entries. A subsequent idle, two-selector correction set both normal
  and passthrough output to HDMI 0; checkpoint
  `astertv-dolby-route-20261028-v3` is installed. Kodi's engine reopened
  HDMI 0, but a physical E-AC-3 test had audible sound without a Dolby
  indication; Kodi logged an E-AC-3 decoder and PCM HDMI channel status.
  A filtered `Settings.GetSettings` query then exposed the underlying
  incompatibility: Kodi 22's current device options omit HDMI 0, and the
  settings framework fell back to analogue/default plus HDMI 1 even though
  direct `GetSettingValue` had temporarily shown HDMI 0. This is not proven
  passthrough. The idle profile was restored to the owner-confirmed HDMI 0
  stereo route with passthrough off; checkpoint
  `astertv-audio-post-pass-rollback-20261028` is installed, and Jason
  reconfirmed audible sound. ALSA independently lists `hdmi:CARD=PCH,DEV=0`
  as `Beyond TV`, but Kodi's startup log records `Unable to open device` for
  that exact PCM at 13:45:15, followed immediately by its device-validation
  fallback; the same PCM opened successfully from 13:46 onward. The leading
  hypothesis is a Kodi-startup/HDMI-audio readiness race, not an absent TV
  ELD or permanently unavailable ALSA device. Do not restart Kodi
  blindly: HDMI 0 selector enumeration/persistence is unresolved and a
  restart may revert to silent analogue/HDMI 1.
- Jason approved a bounded Kodi startup readiness fix. A new systemd
  `ExecStartPre` probe checked the TV ELD and silently opened HDMI 0 with
  ALSA, with a 45-second fail-open bound and exact checkpoint
  `astertv-hdmi-ready-20261028`. The first restart probe succeeded, but Kodi's
  immediate ALSA enumeration still logged `Unable to open device
  "hdmi:CARD=PCH,DEV=0"` and reset the selectors. A three-second settle
  successor also succeeded as a standalone ALSA probe but failed to prevent
  the same Kodi rejection. Both startup-gate generations were rolled back;
  the service drop-in and probe file were removed, and systemd reloaded.
  Kodi's normal HDMI 0 stereo selectors were restored live with passthrough
  off at checkpoint `astertv-audio-after-gate-20261028`; physical sound
  reconfirmation is pending. The delay hypothesis is therefore disproven.
  PulseAudio is simultaneously enabled (`--audio-backend=alsa+pulseaudio`)
  and advertises HDMI stereo; contention is only a hypothesis, not an
  established cause. Do not disable PulseAudio or change Kodi's backend
  without a separate risk decision, because that could affect other audio
  routes including Bluetooth.

- the stalled task was archived after two output-limit failures and an empty
  in-progress turn; its complete dirty checkout was retained by snapshot
  `31f5620344bf90ada2d12e52bb5cfdd15dd49d94` and restored into the managed
  `astertv-v2-recovery` worktree;
- Books visibility is installed through the production-safe
  `aster-books-visibility-prod2` checkpoint; its installed
  `IncludesBooks.xml` hash is `7f1d5168da31b8b834e07756d4df15c44d7e9752de56d4171eedc26cae051549`.
  The HP-only installer correctly refused production before this dedicated
  successor was built.
- Requests uses the production Seerr host guard. Search's two pill labels are
  centred, and the Select dispatcher can activate the catalogue path. The
  series launcher, runtime manifest and Search handoff share the repaired
  `66b6303f2dab9162e0f1fe305dcd173aae90fa7c1c6be395ba6b8f4a7e6ed9ae`
  pin. A production Home TV selection opened the ready v2 preview in 1,015 ms
  and returned idle.
- News Digest's production launcher/import/pin chain was repaired. A fresh
  native check showed 20 ready stories, started the opening briefing with
  `Playing=true`, then returned Home with empty playback and playlists.
- The production camera viewer uses the restricted on-demand Frigate client.
  `aster-camera.service` is active; a native test fetched images in two sessions,
  stopped on toggle and exit, and left playback idle.
- Git history on `codex/aster-home-eh001-m0` and the retained
  `codex/astertv-youtube` worktree supplied the lab-proven YouTube design:
  dedicated landing controls `9530`–`9532`, generic result container `50`, and
  a named delayed focus action. Production Kodi 22 needed a three-second root
  focus delay and a one-shot Back handler scoped to `MyVideoNav`. Checkpoints
  `aster-youtube-production-navigation2`,
  `aster-youtube-production-entry-timing1` and
  `aster-youtube-production-compact1` are installed. The active navigation
  hash is `2c3f04be5d4a52a2cbc5d51ee298a7c637481a1360152030076f1a961b04339b`;
  family manifest hash is
  `ebb5e65b87990b3343e59bb6cd0669a9d03882ab107c3cb3ec77c76876f8a53c`.
- Two fresh production runs passed YouTube root focus, all three rows, top
  rail, ordinary browse, Back to root and Back to Home with no manual focus.
  The Aster search keyboard submitted `OpenAI`, the official add-on returned
  49 result entries, the result grid and rail responded, and both Back buttons
  returned through root to Home. A private 4K capture confirmed that the
  synopsis and all three rows, including Watch Later captions, fit the screen.
  No player started and Kodi stayed active without a new crash.
- A later real TV entry failed even though the show-200 library snapshot was
  complete (one season, six episodes): Kodi had no active player but retained
  one parked video playlist item. The old global `idle()` gate incorrectly
  prevented even read-only season browsing. A targeted production successor
  now permits browsing when no player is active and asks before replacing an
  exact singleton parked queue for episode playback. Unit tests cover decline,
  confirmation and refusal of active/audio/multiple-item states. The seven
  changed runtime/pin files have an exact rollback checkpoint at
  `/storage/.aster-checkpoints/astertv-series-parked-queue-20261028`.
  The new series manifest pin is
  `1f1142545750c8bde616b698a7ea663006e818b31be9c75c67c589bc36d9d0db`;
  family hash is
  `5acbc0ea9843421d4efbb55cfef4b845dfb9e3844e5b23705612d5bb6e2a6271`.
  A fresh native screenshot confirmed the VisionQuest season/episode page
  opened. Playback of VisionQuest S1E5 was subsequently observed in Kodi's
  player log and then returned idle with both playlists empty. The separately
  approved queue checkpoint/clear test was not run: the live queue changed
  during its two-snapshot guard, so it safely refused to act. The empty queue
  now makes that specific clearance unnecessary. Do not treat the earlier
  preview-only smoke check as season or playback coverage.

The YouTube investigation included unsuccessful focus experiments. A combined
Home route-reset and Back-adapter candidate crashed Kodi while the video window
opened; it was rolled back from `aster-youtube-production-navigation1` to the
exact released hashes before the narrower successful changes. Earlier
experiments triggered LibreELEC safe mode once; the original profile was
recovered intact and the released YouTube files were restored from
`aster-youtube-production-release-restore1`. These checkpoints are retained as
incident and recovery evidence. Do not replay superseded experimental scripts.

The remaining acceptance is Jason's physical sofa/remote review, including the
TV episode prompt and a multi-season selection, representative YouTube video
playback/stop, and production audiobook/podcast progress sign-off.
Kodi 22 and the lab's Kodi 21 should not be treated as interchangeable test
runtimes. No Forgejo or GitHub push was made; remote synchronization awaits the
required immediate push approval.

The sections below record the earlier HP engineering baseline and historical
release gates. The production state above supersedes their older
"production unchanged" assertions.

This is a compact continuation index for the main Version 2 work. The charter
and dated historical decisions remain in
[Aster-Home-Version-2.md](Aster-Home-Version-2.md). Completed engineering slices
do not imply household acceptance or production promotion.

## Accepted current engineering state

- Media, Music and Books have owned recommendation heroes and recent-item
  rails. The Acquisition Hub remains a separate discovery/request destination.
  See [landing evidence](Aster-TV-Version-2-Owned-Landing-Evidence.md).
- The Media top rail fits all destinations and the clock. The active Home hash
  is `4c118dd42c3d97c1899a0dcbdce8e6ab42b22d3f309c09802f1a861fac9f830d`.
- Search's family integrity record now matches the accepted Home. The active
  family manifest hash is
  `c865df1863d8511a6685f491588746cfd255854ccc96ada4d2fbcf7b6dd66247`.
  Ordinary grouped Search opened successfully after reconciliation.
- A fresh family recovery capture independently reconstructed on HP and Mac.
  It contains 67 runtime files, eight launcher pairs, twelve guarded skin files
  and the Jellyfin idle-callback guard. The manifest pin is
  `dc77517df6e91cb4b0697593c7f0b5354f0bfa13327e7857a9cf1d81a2c3a1b6`.
  See [integrity and recovery evidence](Aster-TV-Version-2-Integrity-Evidence.md).
- The recorder process adapter passed synthetic Mac and HP Linux checks for
  release, deadline, bounded memory, cancellation and forced child cleanup.
  It is prepared code, with no remote-button/microphone activation. See
  [voice evidence](Aster-TV-Version-2-Voice-Evidence.md).
- Saved Acquisition Hub outcomes are active on HP. The native duplicate-only
  checks and Books screenshot passed after a page-local cached-render fix;
  both approved request journals stayed unchanged. See
  [acquisition evidence](Aster-TV-Version-2-Acquisition-Evidence.md).
- Voice capture-to-query assembly now passes synthetic Mac/HP checks, including
  cancellation and late-result refusal. It remains unbound to live hardware.
- The EPUB compiler project is complete at `fc91fcd4`. Its pinned Books
  consumer is active on HP through two HP-only read-only NFS publications.
  Native narration, sentence highlighting, saved progress, stop-on-Back and
  unchanged Calibre fallback all passed. Production remains unchanged. See
  [EPUB consumer evidence](Aster-TV-Version-2-EPUB-Consumer-Evidence.md).
- Settings Diagnostics now includes a read-only Books narration Doctor. It
  verifies the pinned reader, automount policy, fixed NFS sources/options and
  every ready generation manifest without repairing anything. Native HP review
  reports two valid publications. See
  [Doctor evidence](Aster-TV-Version-2-EPUB-Doctor-Evidence.md).
- A bounded release inventory verifies 24/24 active and base-release HP anchors without reading
  credentials, profiles, history, listening progress or media databases. It
  deliberately reports recovery incomplete because Recovery7 predates the
  active EPUB Doctor family. See
  [release inventory evidence](Aster-TV-Version-2-Release-Inventory-Evidence.md).
- The corrected recovery source plan covers all 24 anchors. Bundle6 independently
  verifies after an isolated copy: 21 source stages, 280 files, 8,866,055 bytes,
  manifest `ca12e217bc0017762e5f3a07ed3d20319f92a60fdeebfb1f8d17d9749662475f`.
  Its thirteen-step recipe covers every source and eight explicit prerequisites
  with two bounded Kodi restart points. Full ordered apply/rollback rehearsal remains open.
  The base archives → Recovery7 → Music → EPUB Doctor core has now passed an
  isolated apply/verify/rollback. Compiled Books, its read-only mount units,
  camera, sounds, startup, screensaver and the active accessibility overlay
  have now passed a second isolated apply/verify/rollback with no identity
  provisioning. The remaining release
  gate is one full clean-client replay with Kodi/systemd activation and
  separately provisioned restricted identities.
- Accessibility semantic verification found and repaired one unguarded page
  fade introduced by a later `Includes.xml` successor. Home, Hub and Video OSD
  animations now retain reduced-motion guards; the consolidated final six-file
  layer is the Bundle6 recovery source, so older overlay files cannot overwrite
  newer UI work.
- The official YouTube add-on reports the HP user fully signed in. Version 2
  now explicitly owns the Aster presentation milestone: replace the add-on's
  generic entrance with a Media-home-style YouTube landing page and preserve
  official add-on search, subscriptions, account and playback behavior. No
  credential is stored in the skin or repository.
- The apparent Music/Books landing-navigation regression was isolated to the
  combined test driver. Fresh separate Media, Music and Books runs passed with
  no skin change; evidence is recorded in
  [integrity evidence](Aster-TV-Version-2-Integrity-Evidence.md).
- A fresh read-only HP resource capture supports the current conservative
  bedroom target: N95/N100-class x86-64, 8 GiB RAM, 64 GB minimum storage
  (128 GB preferred), gigabit Ethernet and a proven HDMI chain. This remains a
  qualified estimate until the final composed client is measured on the N95.
  See [resource evidence](Aster-TV-Version-2-Resource-Evidence.md).
- The final composed HP client passed a six-cycle native mixed video/audio
  soak, returned Home idle, produced no crash or inspected error line, and
  stabilized below 665 MiB Kodi RSS. See
  [endurance evidence](Aster-TV-Version-2-Endurance-Evidence.md).
- A finite release-readiness record now distinguishes completed unattended
  engineering checks from owner, hardware, destructive clean-install and
  production-promotion gates. The live HP prerequisite audit is clean, but the
  candidate is deliberately not labelled release-ready or production-authorized.
  See [release-readiness evidence](Aster-TV-Version-2-Release-Readiness.md).

## Next work and gates

| Work | Next action | Dependency |
|---|---|---|
| Cross-media native check | Media, Music and Books now pass separate exact-ID remote-equivalent checks; retain the corrected isolated driver | No product navigation defect was demonstrated |
| Acquisition requests | HP saved-outcome activation and duplicate-only review passed, including matching rendered Books hero | No additional provider write is authorized by the two-title trial |
| Voice search | Join the tested single-attempt assembly to foreground listening controls and restricted STT transport | Physical remote capability and scoped speech identity remain live integration gates |
| EPUB pre-generation | Fold the verified consumer and Doctor layers into final release/recovery assembly | HP consumer and read-only Doctor are active; production promotion remains separately gated |
| YouTube | Complete owner sofa-distance review of the active Aster landing/search successor, including playback and Back/stop behavior | Official add-on remains the data/playback owner; production unchanged |
| Endurance and accessibility | Complete owner sofa/remote and multi-day household review of the final composed client | Six-cycle native mixed-player soak passes; short automation does not substitute for household use |
| Bedroom sizing | Reconcile the N95 host identity, then capture the final composed client idle and under representative 4K playback | Current qualified target and evidence are in [resource evidence](Aster-TV-Version-2-Resource-Evidence.md); lower-memory deployment remains deferred |
| Final cleanup | One finite owner-led page-by-page v1/v2 walkthrough and bounded repairs | Feature work first; avoid creating an open-ended new backlog |
| Release | Run one full disposable clean-client install/verify/rollback with Kodi discovery, systemd activation and separately provisioned restricted identities, then complete the operational handover | Core and late-stage source-material rehearsals pass; destructive HP reset is not implied, and production promotion remains a separate gate |

## Continuation controls

HP lab tests, reversible deployments and restarts retain Jason's standing
Stream A authorization. Avoid interrupting an active owner test or another
task's sign-in workflow. Local commits are permitted; Forgejo synchronization
waits for a fresh specific push instruction. BOSGAME production has not been
promoted by this continuation.

Preserve the existing unrelated dirty documentation and release registry.
Read live hashes before any next installer; old package manifests are historical
and must not be reapplied to a newer composed Home. Do not restore playback,
watch history or listening positions merely to roll back UI/code.
