# AsterTV v3 M0 recommended decision register

> Status: partially adopted. The local account authority, shared/private matrix,
> restricted Guest posture and no-PIN initial policy were accepted for the
> Jen M2 candidate on 2026-11-04. All other rows remain proposed and this file
> grants no service, identity or client authority by itself.

The recommendations below turn the M0 unknowns into explicit choices that can
be accepted or amended after the low-spec handoff. They prefer local ownership,
opaque service mappings and denial over accidental cross-profile access.

| Decision | Recommended selection | Why / required proof before live use |
|---|---|---|
| Account authority | AsterTV-owned local profile registry, schema-versioned and atomically written. Stable random profile IDs; one recovery-admin role; no password, token or service credential in the registry. | AsterTV needs one UI authority without pretending Jellyfin, Google or Home Assistant identities are interchangeable. M2 must prove switch/restart/sign-out/malformed-state recovery with two synthetic accounts and Guest. |
| Shared/private matrix | Shared: public catalogue metadata, generic artwork, room/device labels and global visual settings. Private per profile: Jellyfin mapping/history/progress, YouTube state, requests, books/listening progress, Aster context, Home/camera entitlement and recent searches. Device-only: audio/video output, client name, capability profile and recovery state. | This is the minimum split that prevents one household profile inheriting another's history or controls. Every private field needs a guest-denial fixture. |
| Guest | Persistent restricted profile with no service mappings by default, not an alias of the primary profile. It may browse only explicitly public/local catalogue surfaces and cannot request, access Books/listening history, Home, Cameras or private Aster context. | Predictable restart behaviour is safer than an implicit shared session. Any optional guest playback must be separately mapped and tested. |
| YouTube guest | Fail closed. Enable only if the official add-on proves separate OAuth/add-on state in a dedicated profile directory and Back/restart cannot cross into the primary account. Otherwise Guest sees no personalized YouTube surface. | API credentials and OAuth session state have different custody. A shared add-on profile is not isolation. Signed-out search may be considered later only if it exposes no primary state. |
| Podcast request authority | Audiobookshelf is the preferred subscription/catalogue authority, using canonical feed URL plus provider/stable feed ID, duplicate preview and explicit final submission. Seerr must not receive podcasts. | Audiobookshelf already owns podcast catalogue/progress. Live work requires API capability verification, duplicate/idempotence proof and a reversible synthetic feed. |
| eBook boundary | Calibre/CWA is read-only metadata/content authority. A title is playable only when a ready-generation manifest names the source revision, canonical Aster voice/lexicon version, audio members and timing mode. Missing/invalid word timing falls back to accepted sentence timing. | Prevents the UI from listing unreadable books or presenting inferred timing as exact. No generation job is authorized by this decision. |
| Camera/event source | Home Assistant is the semantic event/entitlement authority; Frigate remains image/event evidence source behind the existing restricted delivery. Use an explicit source allowlist. Continuous view is owner-profile plus display scoped and opt-in. Door preview is debounced, time-limited, quiet-hours aware and non-interrupting during playback. | Keeps Kodi from receiving broad Frigate/Home Assistant credentials and makes privacy/availability behaviour testable. Exact sources and quiet hours remain owner inputs. |
| Aster broker | Dedicated independently revocable AsterTV client identity. Allow only media search, page navigation, bounded playback, News actions and named Home Assistant aliases. No shell, arbitrary JSON-RPC, arbitrary HA service call, credential retrieval or general whole-home tools. Start with synthetic capture; G20 is enabled only after device/capture proof. | Matches the accepted compact-command and media-search surfaces while keeping model output non-authoritative. M3 requires denial, injection, timeout, cancellation and stale-context tests. |
| Home Assistant bridge | Per-client semantic bridge with room/profile context and an alias registry that maps reviewed verbs to exact entities/actions. Unknown aliases and ambiguous targets deny. Browser/Kodi clients receive short-lived semantic sessions, never a Home Assistant token. | Provides the future PWA/Aster entry point without becoming a general command proxy. Exact aliases and device addresses require later live discovery. |
| Low-spec policy | Capability-driven release profile, not hostname conditionals scattered through features. The profile declares decode/audio/display/resource limits and optional UI reductions; it may constrain transcode/direct-play policy but cannot weaken privacy, navigation, recovery or credential isolation. | The pending handoff report must populate measured facts. Family/Bedroom remain independent acceptance targets and are never inferred from low-spec success. |

## Inputs still required from Jason or the handoff

1. Name the recovery administrator and whether ordinary profiles require a PIN.
2. Confirm whether Guest may play the shared Jellyfin catalogue or is browse-only.
3. Accept fail-closed YouTube Guest if independent official-add-on state cannot
   be proved.
4. Confirm the exact camera source allowlist, continuous-view displays/profiles,
   door-preview duration and quiet hours.
5. Confirm the initial Home Assistant aliases and which require confirmation.
6. Supply the low-spec report described by the handoff template; do not infer
   limits from CPU generation alone.

Acceptance of these decisions is an M0 architecture action, not permission to
create identities, copy tokens, change services or deploy clients.
