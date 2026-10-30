# AsterTV v2 prompt reconciliation — 2026-10-30

Scope: the 2026-10-29/30 regression reports and image set, later requests to preserve the prior two days' work, check YouTube recommendations, and retain the News Digest. The lab is `192.168.1.140`; production was not touched.

## Completed or present in the lab

| Request | Evidence / result |
| --- | --- |
| YouTube personalized recommendations | Official YouTube Kodi add-on 7.4.4 exposes signed-in `special/recommendations` separately from public `special/popular_right_now` (Trending). The lab landing row and both recommendation pills now use Recommendations. Kodi directory queries returned 50 recommendations + 50 thumbnails, 51 subscription folders + 50 thumbnails, 50 Watch Later videos + 50 thumbnails, and 47 search results + 47 thumbnails. |
| News Digest | Digest player and reader are present in the live `script.asterruntime` family and preserved snapshot. Focused digest tests pass. |
| 24-hour clock / Aster screensaver | Live Kodi settings contain `H:mm:ss` and `screensaver.asterhome.v2lab`; the Aster screensaver assets are installed. Kodi's built-in black/dim add-ons remain installed but are not selected. Screensaver skin test confirms the mark does not black out the underlying feed. |
| V2 rail / icons | Lab audit records the centered floating rail with Requests present; stone launcher marks are rail-only. Settings content uses its regular unstoned settings art. |
| TV season preview / movie detail route | `aster-series-preview24` is installed and the live Select dispatcher contains its TV route; movie detail route remains in global-search UI. Prior movie-detail selection check opened the detail window without starting playback. A new physical-remote navigation check was not run in this pass. |
| Home, Music, Books hero sources | Live Home and Music XML include fade layers and Home uses the refreshed recommendation provider. Books hero XML has the fade source. Source/UI tests pass; current on-TV visual blending and recommendation rotation still need human display confirmation. |
| Music Play confirmation | The lab add-on still prompted in trial mode even for a direct Play selection. Fixed on the lab: selecting Play is now treated as the user's confirmation. Explicit queue replacement and start-queued actions retain their prompts. Pre-change file checkpoint: `/storage/.aster-checkpoints/astertv-music-direct-play-20261030/default.py.before`; updated live/package file SHA-256 `3419eb149d2a0a11066050dc420a7cdc049df6866a5371da9f6d214253ffb375`. |
| Camera page | Camera page and `aster-camera2` viewer route are installed. Earlier approved still test produced a JPEG. The viewer service was active after that test and is now stopped; it remains disabled at boot. A new on-TV page check is still needed. |
| EPUB narration backend / helper | The deployed compiler and recurring helper are active on Aster Speech LXC 116 (`192.168.70.14`). `epub-narration-worker.service` (PID 21073, started 2026-10-30 12:21 PDT) is processing one EPUB in a bounded `Type=oneshot` run; its five-minute-after-completion timer and the read-only Calibre monitor timer are enabled. Speech services and both data mounts are active. The live queue has 167 EPUBs: 3 ready, 152 queued, 1 narrating and 11 failed. The HP normal-entry compiled-reader activation is hash-pinned and enabled. |
| Books page presentation and selection | Restored missing `11-books.png` from recovery Git history as a non-stone compass/book mark; stone launcher marks remain rail-only. Reordered hero layers so the floating rail stays visible, removed unused hero buttons, and corrected focus links. Books and Music handlers now fall back to the focused container when Kodi returns an item before its custom properties are available; unresolved selections show a diagnostic. Kodi reloaded Books without XML errors. Owner playback confirmation remains pending. Checkpoint: `/storage/.aster-checkpoints/aster-books-playback-layout-20261030`. |
| Narrated-only eBook lists | The Aster Books eBook home row, hero, eBooks page/search, and global Books search now retain only rows with a published ready pointer and an active hash-pinned reader. Audiobooks and podcasts are unchanged. The live catalogue check finds 3 readable eBooks; a global Books query returned only those ready matches. The change is checkpointed at `/storage/.aster-checkpoints/aster-books-ready-list-20261030`. |
| Books/Music/search/Seerr/voice source fixes | The book and music modules, global search details, Seerr request UI, and voice search implementation remain in the recovered source and deployed snapshot. Focused source tests pass as detailed below; these are not a substitute for end-to-end remote interaction. |

## Still incomplete or needs user-side acceptance

- **Book 505 narration/TTS:** this book is KFX-ZIP, not EPUB, and has no ready narration pointer, so it is now omitted from the Aster Books eBook lists and Books search. The compiler intentionally ingests EPUB only. The TTS backend itself is deployed and running. Of 167 eligible EPUBs, 152 remain queued, 11 have failed, and only 3 are ready. The current compiler estimate was about 1,912 worker-hours for the backlog at the measured render rate, so completion is a long-running process rather than an immediate conversion.
- **Voice search:** receiver and software path were restored, but the user deferred speaking a test phrase. Microphone capture and end-to-end transcription remain unverified.
- **On-screen confirmation:** Kodi's JSON-RPC web server is disabled, so I did not enable it merely to automate navigation. The recent Music Play change is installed, but the TV's next direct Play action should confirm the dialog is gone. Music title selection, live Books hero appearance, Home recommendation rotation, camera-page rendering, and Seerr pill focus still lack a fresh physical remote check.
- **Seerr edge case:** prior read-only broker check succeeded for a general title query; `Hocus Pocus` returned HTTP 409 `seerr-text-invalid`. The request-page UI/model tests pass, but the title-specific failure remains unresolved and may explain a blank result screen.
- **Global search integration test:** 68 of 69 tests in the focused batch passed; `test_exact_dialog_control_readiness` errored because its Kodi stub lacks `xbmc.getInfoLabel`, which the production dispatcher calls. This is a test-harness defect candidate, not proof of a live navigation failure. The live global-search page must still be checked with a remote.
- **Narration runbook drift:** the runbook heading still says the worker is intentionally inactive, but the later project record and Git commits say Jason activated the full backlog on 2026-10-26. The current live worker state agrees with the project record; the runbook header is stale.

## Regression cause and release handling

The main regression mechanism is incomplete, independently versioned overlays: the `v2.0.6 ... r2` archive was a seven-file overlay and omitted Home and required TV series runtime updates. Stale skin XML could overwrite reviewed rail assets/routes. The new package contains all 573 installed add-on/skin files plus its manifests, recovery material and this audit (618 archive entries total), and excludes profile data and credentials. It incorporates the current personalized YouTube routes and the Music direct-Play fix. It is a lab preservation package, not a production release or an assertion that every feature passed acceptance.

Focused checks: 41 Music/Movie/News tests passed. A broader source batch passed 68/69, with the single test-stub error above. Other attempted broad installer tests were not a clean acceptance run because their companion release bundles/resources were absent from the copied scratch tree; one legacy series-installer test also rejects the newer live dispatcher predecessor. Do not use those installer results to promote a release.

Production remains on its stable v1.1.1 rollback. No remote Git push or production deployment was performed. The EPUB narration worker is active on LXC 116; no microphone capture was performed.


## Books/Music visual follow-up r6 (2026-10-30)

Books hero layers now span the full screen. eBook, audiobook and podcast category pages use the selected cover as a full-screen backdrop with the shared fades. Kodi-compatible visibility syntax is covered by the package regression gate. The Podcasts screen is visually verified; Music XML loads without the previous focus errors. Remote OK playback/selection acceptance remains pending; production unchanged. Package: `astertv-v2-lab-reconciled-2026-10-30-r6.tar.gz`.

## Remote OK activation r7 (2026-10-30)

The shared G20 selection dispatcher now falls back to Kodi's skin focus conditions for custom windows and Python-populated lists. Input-level verification opened podcast and audiobook listings, the eBook read-along screen, and a Music album track list; Music track OK started playback. Playback was stopped and the music playlist verified empty. Lab checkpoint: `/storage/.aster-checkpoints/aster-select-dispatch-r7-20261030`. Production unchanged. Superseding package: `astertv-v2-lab-reconciled-2026-10-30-r7.tar.gz`.

## Physical G20 OK activation r8 (2026-10-30)

The physical remote emits Linux `KEY_SELECT`, which Kodi resolves through the named `<select>` keyboard mapping rather than numeric key 353 alone. The reconciled keymap now includes the named mapping in navigation and OSD contexts, and current Books/Music page dispatch runs before stale TV-series preview state. A physical G20 OK press was verified at Podcasts window 11120/focus 500 and opened the selected show's episode list. Lab checkpoints: `/storage/.aster-checkpoints/aster-select-dispatch-r8-20261030` and `/storage/.aster-checkpoints/aster-select-keymap-r8-20261030`. Production unchanged. Superseding package: `astertv-v2-lab-reconciled-2026-10-30-r8.tar.gz`.
