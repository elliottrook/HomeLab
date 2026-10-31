# AsterTV v2 lab reconciliation — 2026-10-30

Canonical preservation artifact: `astertv-v2-lab-reconciled-deployed-snapshot-2026-10-30.tar.gz`.

SHA-256: `427dea0b96df44dbcce5c64609a1c2916c13033e685690186bed9961e187d4f3`.

The artifact captures 573 Aster-owned Kodi add-on and skin code/art files from the live lab, excludes Kodi profile data and credentials, and includes a hash-pinned nine-file route, icon-scope and greeting reconciliation. It records source ref `codex/astertv-v2-recovery` at `1970007a`. Production was not changed.

The earlier `astertv-v2.0.6-lab-repair-complete-20261030*.tar.gz` bundles are retained as historical inputs. Their base overlay is not complete by itself; the current snapshot is the authoritative record of the installed lab state. Do not deploy the old base overlay alone.

The active lab repair checkpoints are `/storage/.aster-checkpoints/astertv-v2-rail-routes-20261030`, `/storage/.aster-checkpoints/astertv-stone-icons-rail-only-20261030-r2`, and `/storage/.aster-checkpoints/astertv-home-greeting-20261030`.

YouTube recommendation reconciliation (same date): the official `plugin.video.youtube` 7.4.4 add-on exposes its signed-in personalized Recommendations feed at `plugin://plugin.video.youtube/special/recommendations`, separately from its public Trending feed at `plugin://plugin.video.youtube/special/popular_right_now`. The live Aster YouTube page had been using Trending for its featured row and both pill entry points. The updated lab skin now labels these Recommendations and uses the personalized feed for the landing row and search-results pill. Subscriptions and the account-backed Watch Later list remain unchanged.

Updated preserved package: `astertv-v2-lab-reconciled-youtube-recommendations-2026-10-30.tar.gz` (SHA-256 `a6990436f2d466f5f61d73123e69302d477dacf2186f41c028dea92de160e6d0`). Updated `MyVideoNav.xml` SHA-256: `6798822d0218b96cde69e385545ad36a425c01c455fdfcb69a5d8ab7208fcf8a`. The lab file was checkpointed before replacement at `/storage/.aster-checkpoints/astertv-youtube-recommendations-20261030/MyVideoNav.xml.before`. A direct Kodi JSON-RPC directory query returned 50 personalized videos, all with thumbnails. Production remains unchanged.

YouTube route verification after skin reload: the landing path returned 50 personalized recommendations with 50 thumbnails; Subscriptions returned 51 channel folders with 50 thumbnails; Watch Later returned 50 videos with 50 thumbnails; a direct search returned 47 videos with 47 thumbnails. The current Kodi window is back on the official add-on root; no player was started.

Music direct Play follow-up: the lab add-on had still shown the queue replacement dialog in trial mode. The lab now accepts selection of Play as confirmation while retaining explicit prompts for Replace Queue and Start Queued Tracks. Pre-change code is checkpointed at `/storage/.aster-checkpoints/astertv-music-direct-play-20261030/default.py.before`. Updated module SHA-256: `3419eb149d2a0a11066050dc420a7cdc049df6866a5371da9f6d214253ffb375`.

Updated full preservation package: `astertv-v2-lab-reconciled-2026-10-30.tar.gz`, SHA-256 `951e927168cf988691f49fa25ea0ff0bc9c691e2c46dc42bb4e10c63a750d94e`. It carries the YouTube Recommendations route, direct Music Play behavior, narrated-only Books listings and the corrected prompt-by-prompt status report inside the archive. Kodi profile data, credentials, narration output and the separate LXC 116 compiler runtime remain outside this Kodi code snapshot. This is a lab snapshot, not a production release.

Books availability follow-up: Books home/eBook rows and the global Books search now include only eBooks with a valid published narration pointer and active hash-pinned reader. Audiobooks and podcasts were preserved. Checkpoint: `/storage/.aster-checkpoints/aster-books-ready-list-20261030/books_data.py.before`; updated `books_data.py` SHA-256 `d1eb9d2986d26d99267732a8a24e5e80b43990345191d56054510d024f784ce1`. Live catalogue count: 3 readable eBooks.

Books page repair: restored `media/11-books.png` from recovery Git history (non-stone compass/book icon); corrected Books rail/hero stacking, removed unused hero actions, and repaired focus links. Books and Music selection now fall back to Kodi container properties when selected-item properties are empty. Live checkpoint: `/storage/.aster-checkpoints/aster-books-playback-layout-20261030`. Kodi successfully reloaded the skin; playback confirmation remains with the user. The recovery payload includes the same changes and safely supports restoring the previously absent icon.

EPUB narration correction: the compiler/worker was already deployed and explicitly activated for the full backlog in the EPUB project. A live check found the worker running on LXC 116; see the prompt reconciliation for current queue counts. Book 505 is KFX-ZIP, not EPUB, which is why that page falls back to Calibre-Web instead of opening generated narration.


## Books/Music visual follow-up r6 (2026-10-30)

Books hero layers now span the full screen. eBook, audiobook and podcast category pages use the selected cover as a full-screen backdrop with the shared fades. Kodi-compatible visibility syntax is covered by the package regression gate. The Podcasts screen is visually verified; Music XML loads without the previous focus errors. Remote OK playback/selection acceptance remains pending; production unchanged. Package: `astertv-v2-lab-reconciled-2026-10-30-r6.tar.gz`.

## Remote OK activation r7 (2026-10-30)

The shared G20 selection dispatcher now falls back to Kodi's skin focus conditions for custom windows and Python-populated lists. Input-level verification opened podcast and audiobook listings, the eBook read-along screen, and a Music album track list; Music track OK started playback. Playback was stopped and the music playlist verified empty. Lab checkpoint: `/storage/.aster-checkpoints/aster-select-dispatch-r7-20261030`. Production unchanged. Superseding package: `astertv-v2-lab-reconciled-2026-10-30-r7.tar.gz`.

## Physical G20 OK activation r8 (2026-10-30)

The physical remote emits Linux `KEY_SELECT`, which Kodi resolves through the named `<select>` keyboard mapping rather than numeric key 353 alone. The reconciled keymap now includes the named mapping in navigation and OSD contexts, and current Books/Music page dispatch runs before stale TV-series preview state. A physical G20 OK press was verified at Podcasts window 11120/focus 500 and opened the selected show's episode list. Lab checkpoints: `/storage/.aster-checkpoints/aster-select-dispatch-r8-20261030` and `/storage/.aster-checkpoints/aster-select-keymap-r8-20261030`. Production unchanged. Superseding package: `astertv-v2-lab-reconciled-2026-10-30-r8.tar.gz`.

## Books resume activation r9 (2026-10-30)

The clean lab rebuild retained the valid restricted Audiobookshelf client and all resume-capable code but omitted the non-secret `progress-enabled.json` activation marker, causing the service's intentional playback-only fallback. r9 installs only the hash-pinned AsterTV marker at mode 0600; credentials remain separately provisioned and are not packaged. The transactional installer checkpoint is `/storage/.aster-checkpoints/astertv-v206-reconcile-r9-20261030`. After restart, a content-free control-socket audit found 1,491 shared-progress audiobook entries and 39 shared-progress podcast entries across the complete 46/7-item catalogue, four audiobook Resume rows from existing positions, zero playback-only entries and no playback. Podcast progress remains per episode and resumes when that episode is selected rather than through a synthetic top-level Resume row.

The eBook reader did not regress to an older binary: its three live reader hashes match the packaged compiler consumer exactly. All three ready generations declare exact `sentence-sample-index`, canonical `bm_daniel`/`en-gb`/0.95 and cleanup contract `sha256:0476a393…`. Historical word/connected-phrase highlighting at commit `d5b7b5e7` was a synthetic measured-timing proof only. The real ASR and native timing attempts failed closed, so r9 explicitly gates the accepted sentence timing and pinned Aster pronunciation cleanup rather than enabling inferred word positions. Production unchanged. Superseding package: `astertv-v2-lab-reconciled-2026-10-30-r9.tar.gz`.

## Owner acceptance repair r12 — 2026-10-30

r12 preserves the complete post-walkthrough lab state and supersedes r9. Live bounded checks verified: Music grid Up returns to the Albums pill; YouTube returns from Subscriptions with Search focused; Seerr search remains in Requests; the camera returns a valid JPEG and its service stops on exit; News opens the article reader, starts briefing playback, stops it and returns; Recently Added movies carry DB IDs and open details without autoplay; and the seven podcast catalogues expose four progress-backed Resume rows. TV now starts on episodes, crosses season boundaries, uses translucent dark cards and a green watched marker. Movie Play/Resume/Back have visible focus surrounds and the page populates local Cast & Crew and More Like This rails. The Aster screensaver is opaque black rather than a transparent logo overlay. The spoken G20 phrase remains an owner acceptance item; credentials and recordings are excluded. Production remains unchanged. Package: `astertv-v2-lab-reconciled-2026-10-30-r12.tar.gz`, SHA-256 `dca0014893c5bc3351bf54f39ba672e14ac0edbaeb6656239d2fec6913325346`.

## TV/Seerr regression repair r13 — 2026-10-30

r13 supersedes r12 after the owner found the TV episode controller orphaned and the Seerr season controls overlapping their artwork rail. Kodi 22 was invoking the series page's `onInit` while still reporting the source window, so the page published the wrong identity, its owner exited, and a visually complete but inert page remained. The runtime now waits for the allocated WindowXML ID before publishing ownership or applying episode focus, republishes season identity after each list rebuild, and visibly styles the season selector. A live content-free test opened a multi-season series, focused the season menu, changed season index 0 to 1, and returned focus to the episode list. Seerr's season list, centred selection/request pills, hint and artwork rail now occupy non-overlapping regions. Component, wrapper and family pins were regenerated together. Production remains unchanged.

## Series visual acceptance repair r14 — 2026-10-30

r14 supersedes r13 after direct owner review of the Series page. The invisible ivory-on-ivory clock was replaced with the established dark Aster clock pill and readable 24-hour label. Season, Play/Resume and Back are now compact 220x46, 240x46 and 140x46 controls without changing their IDs or focus routes. Episode state now follows the shared Aster badge contract: a small sage dot for unwatched and a 32px sage disc with an ink tick for watched. Episode stills use the shared compact-card mask so their corners match the enclosing cards. A direct Kodi screenshot after restart verified the clock, compact controls, rounded art and unwatched dots. The live page retained episode focus and controller ownership. Production remains unchanged.

## Series finish repair r15 — 2026-10-30

r15 supersedes r14 after the second owner visual check. Play/Resume and Back now explicitly centre their labels vertically. Season, Play/Resume and Back use one identical translucent charcoal normal surface, preserving the compact geometry and existing focus/navigation routes. Rounded episode stills overscan the square placeholder by four pixels on all sides so no pale corner slivers remain. A direct Kodi screenshot verified the installed result. The season menu was then reopened, season index changed 0 to 1, and focus settled back on the episode list; no playback was started. Production remains unchanged.

## Shared header and rail repair r16 — 2026-10-30

r16 supersedes r15 and defines Clock, Search and the floating stone side rail as one shared visual contract on every page where all three appear. Media and Smart Home already used the shared `75cbb991` translucent gold token. Books Search now uses that token instead of its opaque page-specific gold. News now renders Search, Clock and rail after the digest content group, so the hero fade no longer washes out the upper collapsed-rail icons. Direct installed News and Books captures verified matching trim and consistent icon opacity. A News list selection opened the digest player, audio started, and playback was stopped before handoff. Music was audited and intentionally unchanged because it does not expose the same Search/Clock/rail header. Production remains unchanged.

## Books and Requests rail layering repair r17 — 2026-10-30

r17 supersedes r16 after the owner showed Books covers and headings drawing through the expanded rail around Requests. Books now renders the unchanged shared rail after its entire content group. The Requests launcher was also traced to `custom_1133_acquisition.xml`; its hero/results group had similarly rendered over the upper collapsed icons, so its unchanged rail now renders last. Direct lab captures verified expanded Books, collapsed Requests with all seven icons, and expanded Requests. The request recommendations remained populated, no player was active, and no skin XML load errors occurred. The canonical shared rail and the separate `custom_1132` Seerr detail view were restored after diagnosis and remain otherwise unchanged. Production remains unchanged.

## Production candidate r18 — 2026-10-30

r18 freezes the complete post-acceptance lab state as AsterTV v2.0.7. Requests
now opens recommendation artwork directly into its detail stage, supports
focus-preserving multi-season selection and exposes one final Request action;
the acquisition page no longer carries the obsolete intermediate Request
button. Music now uses the shared gold Search/Clock/stone-rail treatment, no
legacy underline, and 220-pixel category pills so Albums and Playlists remain
fully readable at the lab display's font scale. The accepted 1920x1080 AsterTV
artwork is installed through LibreELEC's Kodi profile splash override rather
than replacing an OS image.

The package manifest pins 577 credential-free Aster-owned add-on files plus
the G20 keymap and splash. The production promoter is host-bound, refuses
active playback, preserves Kodi profile/account data and all audio settings,
checkpoints every replaced add-on/keymap/splash, verifies installed hashes and
rolls back automatically if Kodi does not remain active. Final lab preflight:
Kodi active, no active player, final Music hash
`052ff612d6f776e281401d140b148c2425dec4732ecc6e7f68de139ceeb148cc`,
splash hash
`912228f3866b33749905eb8154b470d3170fe4747f92799811470bb49b986cce`.

## Production promotion — 2026-10-30

Owner-confirmed production SSH identity:
`SHA256:qup6j5SaoLYSgeUyrMbXMD2+lpd+DGupbgO6DkHxhm8`. The immutable release archive
at local release commit `31312c17` has SHA-256
`c10cba951db2a95344f94db7c576060ba7ec3cf07f8b953a9efa42aab53f2b71`.
The promoter replaced 13 Aster-owned add-ons and verified all 577 snapshot
members. Rollback checkpoint:
`/storage/.aster-checkpoints/astertv-v2.0.7-production-20261030`.

Post-promotion evidence: Kodi 22 RC1 remained active with no active player;
the v2 skin reports version 2.0.0; Music, Requests, dispatcher and splash hashes
match the release; no recent relevant skin/XML errors were present; Jellyfin
returned 19 populated root sections. HDMI 0 remains the selected PCH device,
two-channel output remains configured and passthrough remains disabled. The
profile and account directories were not copied or replaced. Kodi's normal
restart updated only Jellyfin's data/settings/sync files and the skin settings
file during the ten-minute audit window; the profiles file digest remained
unchanged. Production YouTube is not signed in: a bounded query received the
official add-on's `authorization_pending` response, was cancelled, and Kodi was
restarted cleanly to Home. A one-time production YouTube sign-in is therefore
an explicit owner acceptance item; the lab account/session was deliberately
not copied.

### Production HDMI startup repair and r19 recovery successor

Immediately after r18 promotion Jason reported system-wide silence. The
pre-deployment route had been the known-good explicit HDMI 0 selector, stereo,
passthrough off. After Kodi's deployment restart, Kodi 22 had rewritten only
the normal selector to its generic `ALSA:@` HDMI alias—the same documented
early-start device-validation fallback seen during the October 28 audio work.
With playback idle, the current settings were checkpointed at
`/storage/.aster-checkpoints/astertv-v2.0.7-audio-repair-20261030`, the exact
explicit HDMI 0 selector was restored, and passthrough remained off. Jason
immediately confirmed sound was audible; the explicit route is persisted in
`guisettings.xml`.

No further production restart was performed. The immutable r18 archive remains
the exact artifact used for the initial deployment. Its r19 recovery successor
keeps the same 577 installed snapshot bytes but enhances the promoter to save,
reapply and verify all five audio-route settings after Kodi is ready, including
the rollback path. This prevents replay/recovery from silently reproducing the
known HDMI-startup regression.

The immutable r19 recovery archive has SHA-256
`40acbb064c7fc067469ca96fa9070e465f6dbd80b2be5a7f653c131f37056833`
and is staged on production at
`/storage/.aster-staging/astertv-v2.0.7-production-2026-10-30-r19.tar.gz`.
It was not executed and production was not restarted after the audible route
was restored.

### Production activation and media-selection repair — r21

The first production copy exposed two promotion defects that the lab could not
show. Kodi registered eight newly copied v2 runtime add-ons disabled, while
Music, Requests and the Aster screensaver still contained lab-only hostname
fences. A bounded live repair checkpointed the add-on database and affected
files, enabled the eight production runtime add-ons, kept the lab bootstrap
disabled, and expanded only those three fences to the two named Aster clients.
No Kodi restart was used, so the confirmed HDMI 0 stereo route remained live.

The Home art dispatcher also relied on Kodi `DBTYPE`/`DBID` labels. Those labels
can be blank for plugin-populated Home rows even though the plug-in supplies the
validated `AsterMediaKind` and `AsterDbId` properties. This caused OK to fall
through to native selection, producing either no visible response or direct
movie playback. r21 uses the Aster properties only as a fallback, preserving
native library selection while restoring movie details and TV-series routing.
Production checkpoints are
`/storage/.aster-checkpoints/astertv-v2.0.7-production-activation-r20-20261030`
and
`/storage/.aster-checkpoints/astertv-v2.0.7-media-select-r21-20261030`.

The r21 recovery archive is staged, not re-executed, at
`/storage/.aster-staging/astertv-v2.0.7-production-2026-10-30-r21.tar.gz` with
SHA-256
`d92c77b72b99351f54158909bd80c12fbbffcfa60103257a4d6e8e148b0a03a0`.
Its promoter activates the required runtime add-ons, disables the lab-only
bootstrap, preserves/restores prior add-on states on rollback, and retains the
r19 post-start audio-route verification. The release gate verified all 577
snapshot members, XML/Python syntax, accepted routes, splash, activation,
audio preservation and rollback. Final live audit: Kodi active; no active
player; all eight runtime add-ons enabled; bootstrap disabled; explicit HDMI 0,
stereo and passthrough-off unchanged.

### Production eBook and Home Assistant completion — r22–r25

Production eBook selection reached the accepted reader but failed closed for
two independent conversion omissions. The multi-client bundle declared
`hp_only: false` while its verifier still required `true`, and the two reader
installations lacked their intentionally external
`data -> /storage/aster-reader` links. r22 changes only the verifier contract
and repins both reader bundles, the consumer manifest and activation pin. r23
restores only the two links after verifying the mounted `ready` and
`generations` trees. A no-playback reader-open check then reached the native
Aster reader window with no new reader error. Checkpoints:
`/storage/.aster-checkpoints/astertv-v2.0.7-ebook-boundary-r22-20261030` and
`/storage/.aster-checkpoints/astertv-v2.0.7-ebook-data-link-r23-20261030`.

The production Smart Home page initially contained an old local snapshot
because the approved restricted publisher was intentionally bound only to the
lab (`192.168.1.140`). The production completion preserves the same HA-held
Ed25519 identity and forced command, adding only a second source-IP-constrained
receiver on `192.168.1.157` and one logged OPNsense permit from
`192.168.20.11` to that host's TCP/22. The existing lab rule is unchanged.
Production holds no HA/admin private key. The receiver can atomically replace
only `home-dashboard.json` and its bounded recovery journals.

The first production publication failed closed because the copied receiver's
destination check still named `.1.140`; r25 pins it to `.1.157`. The next
publication was independently acknowledged by both lab and production with
63 readings. Home Assistant configuration validation passed before its brief
Core restart. Startup truthfully published an empty loading snapshot, followed
by a fresh 63-reading dual-target publication after integrations loaded. A
direct production page check displayed the current lighting, temperature,
weather, household list and camera. The temporary diagnostic screenshot was
deleted from production and the operator Mac after inspection.

Recovery boundaries: production receiver
`/storage/.aster-checkpoints/aster-home-delivery-prod1`; receiver destination
`/storage/.aster-checkpoints/aster-home-delivery-prod-destination-r25`; HA
publisher `/config/aster-checkpoints/home-delivery-prod-20261030`; firewall
`/conf/backup/config-aster-home-feed-prod-before-20261030.xml`. Firewall rule
UUID `e5f0fcb0-3ff0-5bd8-a44b-e810fe7a1687` is exactly
`192.168.20.11 -> 192.168.1.157:22/TCP` on the HA VLAN. No Kodi restart or
audio-setting change was used for either repair.

### Production Home lifecycle durability and r27 recovery release

The dual-target publisher proved its first automatic post-restart run at
`2026-10-31T04:04:41Z`: both lab and production acknowledged all 63 readings.
The production Home XML nevertheless lacked the status adapter's `entry` and
`leave` lifecycle calls, so a manually refreshed page could become empty after
a later Kodi or skin restart. The r27 repair adds exactly those two calls while
preserving the existing camera `entry` and `leave` hooks. Its first JSON skin
reload attempt was rejected by Kodi and rolled back automatically; the verified
rollback hashes allowed the recovery marker to be cleared. The corrected
LibreELEC `kodi-send` reload then installed successfully under checkpoint
`/storage/.aster-checkpoints/astertv-v2.0.7-home-entry-r27-20261030`.

After page entry the production adapter reported a fresh source, the feed
contained 63 readings, both external eBook data links resolved to
`/storage/aster-reader`, the player was idle, the recovery marker was absent,
and the explicit HDMI 0 stereo/passthrough-off route was unchanged.

The immutable r27 archive supersedes r21 and is staged on production at
`/storage/.aster-staging/astertv-v2.0.7-production-2026-10-30-r27.tar.gz`.
SHA-256:
`c1b6d62a21ee56ae042595d9e024eb014683a75753f8fd0730e7770ae0718b82`.
The release gate passed all 577 add-on files, XML/Python compilation, accepted
Media/TV/Movies/YouTube/Requests/Books/Music routes, splash, audio-preserving
rollback, Home and camera lifecycle calls, and the guarded external eBook/Home
recovery scripts. A direct production comparison found zero mismatches across
all 577 installed files. Credentials, Kodi profile/add-on data, HA private key,
narration output and audio configuration remain outside the archive.

### Production Settings, clock and Aster screensaver recovery — r30–r35

The first production Settings repair exposed two independent issues. Kodi 22's
setting mutation RPC returns boolean `true`, not the older `"OK"` sentinel;
the first two guarded attempts therefore rolled back without leaving a live
change. r30 uses Kodi's supported `locale.use24hourclock=24hours` override,
verifies the resulting `H:mm:ss` format and adds explicit focus links between
the native Settings category and value groups. Checkpoint:
`/storage/.aster-checkpoints/astertv-v2.0.7-settings-clock-r30-20261030`.

The remaining physical G20 failure was in Aster's global OK dispatcher. It
handled custom media lists explicitly but delegated the Settings rail and
native category pills to a generic Select fallback. r34 now directly dispatches
the Settings rail plus Interface, Player, Services and Add-ons pills. A bounded
runtime check opened Aster Settings, entered Settings - Interface and returned
to the Aster chooser. The selected Aster screensaver was also correctly
installed but its presentation default was explicitly `black`, with no saved
override. r34 changes only that Aster-owned setting to `aster`; the existing
opaque black background, restrained moving mark and wake behaviour remain.
Checkpoint:
`/storage/.aster-checkpoints/astertv-v2.0.7-settings-screensaver-r34-20261031`.
The add-on launched its Aster idle dialog after the repair; physical visual
confirmation of the rendered mark remains the owner acceptance check.

The immutable r35 recovery archive reconciles r27, r30 and r34 without profile
credentials or audio configuration. It contains 577 hash-pinned add-on files,
pins the 24-hour override after a future Kodi restart, restores the prior clock
setting on rollback, carries direct G20 Settings dispatch, and defaults the
Aster saver to its logo presentation. Package:
`astertv-v2.0.7-production-2026-10-31-r35.tar.gz`; SHA-256
`4a7a6768e4ea115e09d36d8d0c126e809d716128db4bbfebeecdc1a6980721d3`.

During runtime verification, invoking a separate Python diagnostic while the
screensaver dialog was active crashed Kodi 22. The service recovered
automatically, but the known early-start HDMI validation race again rewrote the
normal output from explicit HDMI 0 to Kodi's generic alias. The diagnostic was
not repeated. With playback idle, the route was restored without another
restart under checkpoint
`/storage/.aster-checkpoints/astertv-v2.0.7-r34-test-audio-recovery-20261031`.
The engine then opened `hdmi:CARD=PCH,DEV=0` successfully. Final audit: zero
mismatches across the 577 r35 snapshot files, explicit HDMI 0/stereo with
passthrough disabled, 24-hour clock, selected Aster saver, no active player and
no recovery marker.

### Production Search, player return, busy mark, Dolby and HDR — r36–r46

r36 replaces Kodi's indefinite `Working…` presentation with one static,
opaque AsterTV splash and no animation or background worker. Checkpoint:
`/storage/.aster-checkpoints/astertv-v2.0.7-busy-logo-r36-20261031`. A later
UHD Blu-ray ISO test demonstrated why the overlay must not be treated as
player health: Kodi held an active player while opening the 65 GB ISO without
reaching a decoder. The bounded `Player.Stop` recovery returned directly to
the movie page without restarting Kodi or changing audio.

Search had two coupled regressions. The G20 OK dispatcher delegated Media
Search control 135 and shared Search control 139 to a generic Select action;
r40 dispatches their actual scripts. The first live patch correctly changed
the dispatcher but did not update the Search runtime's accepted skin hash, so
the runtime failed closed. r41 reconciles that family-manifest hash. The next
movie selection exposed a pre-existing missing
`from search_details import read_details`; r42 restores the import and updates
the component and family manifests atomically. Checkpoints:
`/storage/.aster-checkpoints/astertv-v2.0.7-search-dispatch-r40-20261031`,
`/storage/.aster-checkpoints/astertv-v2.0.7-search-manifest-r41-20261031` and
`/storage/.aster-checkpoints/astertv-v2.0.7-search-details-r42-20261031`.

The repaired Search result opened the native movie details page, but stopping
fullscreen playback could leave Kodi reporting Home while the movie
controller redrew window 11130. Its focus then failed and the controller timed
out to Media Home. r43 explicitly restores the movie window after playback
and Search window 11127 when leaving a movie launched from Search. Production
acceptance confirmed Search -> details -> playback -> details -> Search.
Checkpoint:
`/storage/.aster-checkpoints/astertv-v2.0.7-movie-return-r43-20261031`.

The production ELD for `Beyond TV` advertises AC-3, E-AC-3, TrueHD, DTS,
DTS-HD and eight-channel LPCM. The earlier Dolby-labelled receiver state was
not passthrough: Kodi logged E-AC-3 decoded to PCM and ALSA IEC status
`AES0=0x04`. The connected ALSA HDMI 0 device was unavailable during Kodi's
capability scan while system PulseAudio was active, causing device validation
to fall back before playback. Official Kodi guidance notes that passthrough is
exclusive and another application owning the device prevents it; Sync
Playback to Display also disables passthrough:
https://kodi.wiki/view/PulseAudio and
https://kodi.wiki/view/Settings/System/Audio.

r44 proved that stopping PulseAudio before Kodi exposes
`TCL Beyond TV on HDMI #0` with E-AC-3 and TrueHD capabilities, but its exact
display-label validator rejected the expanded label and rolled back safely.
r45 accepts the connected sink label, pins both normal and passthrough routes
to `ALSA:hdmi:CARD=PCH,DEV=0|HDA Intel PCH`, leaves PulseAudio inactive and
preserves rollback to the previously audible route. Production acceptance
with `300: Rise of an Empire` logged E-AC-3 `pass-through` and ALSA raw IEC
status `AES0=0x06`; both receiver and TV showed Dolby. `The Croods` then logged
BT.2020, SMPTE ST 2084 HDR10 and E-AC-3 raw passthrough; the TV showed HDR and
Dolby. Checkpoint:
`/storage/.aster-checkpoints/astertv-v2.0.7-alsa-exclusive-r45-20261031`.

The deterministic r46 archive reconciles the accepted r36–r45 state with all
577 prior snapshot files. Promotion now pins the Search/component/family hash
chain, busy logo, exclusive ALSA HDMI 0 route, codec flags and 24-hour clock;
it disables PulseAudio before Kodi starts and restores the prior service and
audio states on rollback. The full 21-test reconciliation suite, Python/XML
compilation, archive inventory, security exclusions and release gate pass.
Package: `astertv-v2.0.7-production-2026-10-31-r46.tar.gz`; SHA-256
`0ee3331bbdb9ef34196e08b057b1a535dfb1893322d9c985d771ded2281753eb`.

### Native Resume presentation — r47

Production exposed one remaining Kodi-era presentation when a title had a
saved position: `DialogContextMenu.xml` still rendered a centred 620x720 stone
panel over a full-screen dim layer. Its Resume and Start actions were correct;
only their presentation was obsolete. The accepted live repair preserves those
native actions while adopting Aster's own `custom_1125_next_episode.xml`
language: 730x205 at the player-safe bottom right, `e6202923` dark-green canvas,
horizontal 68-pixel controls, font24 labels and the shared sage/ivory player
focus ring. The rejected upstream Jellyfin blue overlay trial was rolled back
before this Aster source was applied. Original production XML remains at
`/storage/.aster-checkpoints/resume-dialog-r47-20261031/DialogContextMenu.xml.before`.

The regression gate rejects the abandoned full-screen geometry, stone panel
and generic Kodi texture, verifies the Aster footprint/palette/focus flow and
pins the dialog in `family-manifest.json`. The full 21-test reconciliation suite
and the added Resume gate pass; all 577 snapshot entries compile and hash-match.
The deterministic r47 archive was reproduced byte-for-byte. Package:
`astertv-v2.0.7-production-2026-10-31-r47.tar.gz`; SHA-256
`d979a42fca62fac3dac00a456b4790229c5907f9636942cc4cee6ee46f1cd226`.

### Media Genre artwork — r48

The Genre row's unfocused poster layout placed a translucent ivory panel over
the complete image (`48f2ede4`), creating the accepted-but-washed-out visual
difference from the rows above. r48 removes that image-wide wash. Both focused
and unfocused posters retain full source colour through the existing rounded
poster mask; unfocused tiles use the thin shared sage ring, focused tiles use
gold, and a compact charcoal ribbon carries the genre name in ivory. The
focused ribbon becomes slightly more opaque without changing artwork colour.

The focused gate preserves the Genre panel ID, preview plug-in path, Browse
action and all four directional routes while rejecting the former tint and
requiring both edge/ribbon states. The prior 21-test reconciliation suite and
r47 Resume gate still pass. The 577-file release gate passes and two builds are
byte-identical. Package: `astertv-v2.0.7-production-2026-10-31-r48.tar.gz`;
SHA-256
`76b8fc4a3171013250a5088b3ced777940d5cfb0637f3eeba9794a7be3e6ac5a`.

### Accepted Genre label placement — r49

Direct production review accepted r48's full-colour posters and sage-to-gold
edge change but preferred the genre names in their original below-art position.
r49 removes the temporary ribbon, restores both labels to top 330 and
left-aligns them while retaining font20, the poster mask, full-colour art and
both edge states. Its guard rejects the original ivory wash and the temporary
ribbon and requires both left-aligned below-art labels. The complete release
gate passes across all 577 files and two builds are byte-identical. Package:
`astertv-v2.0.7-production-2026-10-31-r49.tar.gz`; SHA-256
`e583db6a76327a46c71aa61723f82d13a1962fae9c38c9463c1308a355b160bb`.

### Final dual-target release and identities

The final release preserves the accepted r49 UI and all 577 hash-pinned files,
then adds the approved balanced media-art screensaver. It rotates evenly across
TV Shows, Movies, Archive TV and Archive Movies so the larger archive cannot
dominate, chooses random Kodi artwork within each source, changes every 18
seconds and keeps a fixed AsterTV mark at bottom right. Playback, Home timers,
cameras, household status, credentials and sound remain outside the saver.

The identical snapshot was installed on both targets under checkpoints
`/storage/.aster-checkpoints/astertv-v2.0.7-release-20261031-family` and
`/storage/.aster-checkpoints/astertv-v2.0.7-release-20261031-bedroom`. The OS,
Kodi device and restricted Books marker identities were then atomically changed
under `/storage/.aster-checkpoints/astertv-identity-release-20261031`:

- AsterTV Family: `AsterTV-Family`, 192.168.1.157
- AsterTV Bedroom: `AsterTV-Bedroom`, 192.168.1.140

Bedroom initially rejected unsupported passthrough codec settings before any
checkpoint or Kodi stop. The corrected target-aware installer now preserves
only settings Bedroom exposes while requiring Family's complete release audio
contract. The identity reboot also demonstrated that merely disabling
PulseAudio does not survive Kodi's D-Bus activation: Family briefly fell back
to generic/HDMI 1. The bounded repair at
`/storage/.aster-checkpoints/astertv-family-pulse-mask-release-20261031`
restored HDMI 0 and persistently masked PulseAudio; the final promoter carries
the same behaviour and rollback of the prior mask state. The complete 21-test
suite, focused Genre/Resume/screensaver gates and dual-host post-reboot checks
passed. The deterministic final archive is
`astertv-v2.0.7-release-2026-10-31.tar.gz`; SHA-256
`e813de8a74af769ebbfeb744ad65249760292f647dc2d91c4bafb9fc7ba83cf7`.
