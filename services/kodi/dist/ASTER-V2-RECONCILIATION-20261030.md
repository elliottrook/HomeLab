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
