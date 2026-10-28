# AsterTV Version 2 — Current Stream A resume

Updated: 2026-10-28. Owner: Jason. Lab: HP `192.168.1.140`.

## Production rollback and v2 lab hold — 2026-10-28

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

The v2 code fixes through commit `76540e91` are retained on
`codex/astertv-v2-recovery` for a lab-only candidate. The remaining gate is to
bring the HP lab client to the production LibreELEC 13 nightly / Kodi 22
versions, install the candidate there, and repair/retest recap, intro and
outro controls together with TV seasons/playback, News Digest, YouTube search,
audio output persistence and the rest of the release acceptance. No v2
re-promotion is authorized by this rollback. No Forgejo/GitHub push was made.
The tracked, credential-free source and recovery-record package is
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
