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
