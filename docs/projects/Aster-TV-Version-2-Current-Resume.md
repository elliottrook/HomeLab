# AsterTV Version 2 — Current Stream A resume

Updated: 2026-10-26. Owner: Jason. Lab: HP `192.168.1.140`.

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
- The EPUB compiler project is complete at `fc91fcd4`. Its exact service source
  is now present in this branch, and the dormant normal Books handoff plus
  pinned offline reader pass ordinary and optimized local tests. HP activation
  is waiting on the explicit read-only publication-path decision recorded in
  [EPUB consumer evidence](Aster-TV-Version-2-EPUB-Consumer-Evidence.md).
- The apparent Music/Books landing-navigation regression was isolated to the
  combined test driver. Fresh separate Media, Music and Books runs passed with
  no skin change; evidence is recorded in
  [integrity evidence](Aster-TV-Version-2-Integrity-Evidence.md).

## Next work and gates

| Work | Next action | Dependency |
|---|---|---|
| Cross-media native check | Media, Music and Books now pass separate exact-ID remote-equivalent checks; retain the corrected isolated driver | No product navigation defect was demonstrated |
| Acquisition requests | HP saved-outcome activation and duplicate-only review passed, including matching rendered Books hero | No additional provider write is authorized by the two-title trial |
| Voice search | Join the tested single-attempt assembly to foreground listening controls and restricted STT transport | Physical remote capability and scoped speech identity remain live integration gates |
| EPUB pre-generation | Activate the tested normal Books consumer on HP, then walk through one ready and one not-ready title | Compiler is complete; new HP→TrueNAS read-only publication path needs its explicit bounded risk decision |
| YouTube | Official add-on credentials, device authorization, playback and Aster presentation | Separate **Finish Aster YouTube integration** task; main stream must avoid competing foreground tests |
| Endurance and accessibility | Continue evidence against the final composed client, then owner sofa/remote review | Short automated soaks do not substitute for household use |
| Bedroom sizing | Revise the existing measured/inferred assessment after final client shape | See [client sizing](../reference/Aster-TV-Bedroom-Client-Sizing.md); lower-memory deployment remains deferred |
| Final cleanup | One finite owner-led page-by-page v1/v2 walkthrough and bounded repairs | Feature work first; avoid creating an open-ended new backlog |
| Release | Assemble all component checkpoints into a complete deployment/recovery package and operational handover | Family-only capture is one component; production promotion requires its separate owner decision |

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
