# AsterTV Version 2 — Current Stream A resume

Updated: 2026-10-27. Owner: Jason. Lab: HP `192.168.1.140`.

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
