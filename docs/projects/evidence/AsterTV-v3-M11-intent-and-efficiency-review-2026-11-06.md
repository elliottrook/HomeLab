# AsterTV v3 M11 intent and efficiency review — 2026-11-06

Status: repository review complete; final household acceptance still open

## Outcome

AsterTV v3 remains proportionate to its intended household outcome. The
implementation reuses Kodi, Jellyfin, Seerr, Audiobookshelf, Home Assistant,
the existing Aster broker and the existing private web origin instead of
introducing duplicate media, request, progress, automation or public-access
authorities. Optional services fail closed without becoming a dependency for
core local media playback.

No B60 workload, scheduled local-AI job, cloud inference service, public
ingress, always-on microphone, continuous background camera feed or new
viewing-history store was added.

Final graduation still depends on physical Bedroom acceptance, full Bedroom
soak, Family promotion and the non-author walkthrough. This review does not
convert those observations into passes.

## Outcome-to-cost review

| Outcome | Chosen implementation | Avoided cost or risk | Evidence |
| --- | --- | --- | --- |
| One coherent television UI | Kodi v3 overlay composed over immutable v2 plus fail-closed design/focus gates | A second player stack, room-specific forks and unguarded partial overlays | 15 pages, 127 controls, zero conformance failures |
| Household media search/action | Capability-scoped Aster route with compact direct-action and larger media-search surfaces | General agent authority, arbitrary shell/HA/Kodi execution and an always-listening microphone | Broker denials, canonical speech and recovery gates pass |
| Accounts and Guest | Local Aster registry plus service-specific opaque references and a restricted Jellyfin Guest identity | Shared production credentials, browser tokens and a false global low-spec limit | Guest direct-route denials and real playback pass; Guest appliance remains non-deployable |
| Movies/TV/YouTube | Existing Jellyfin and official YouTube authorities with Aster presentation adapters | Copying library/account state or replacing proven playback engines | Trailer, person search, episode, YouTube lifecycle and rollback gates pass |
| Books/News/Podcasts | Existing narration, News timeline, Audiobookshelf and bounded request broker | Duplicate progress stores, unreviewed TTS promotion and automatic acquisitions | Word-alignment negative result retained; News and podcast failure/restart gates pass |
| Home and Cameras | Read-only Home export and page-scoped camera viewer | Broad Home Assistant authority, background camera collection and retained frames | Camera starts only from its page and stops on Back |
| Aster Remote | Private PWA with network-scoped browser access and outbound per-room client identities | App Store/Play Store work, public Kodi listeners and embedded credentials | iPhone/Android path, route denial, three-room Doctor and rollback pass |
| Equipment control | Native Home Assistant integrations and exact semantic actions | Costly CEC adapters, Bluetooth pairing fragility and blind toggles | Family volume/mute/power/standby accepted; Bedroom remains disabled |
| Content-aware volume | Volatile coarse playback class with per-session manual override | Title/history export, Kodi-volume changes and fixed household-wide levels | Family ramp/outage/restart/manual override/Dolby pass; Bedroom open |
| Idle presentation | Local page-aware Aster screensaver | Network fetches, sound, private page content and a second idle daemon | Jen owner acceptance, suppression and resource gates pass |
| Fleet maintenance | Global release plus hardware/peripheral profiles and named overlays | Unique undocumented room builds and live-hotfix-as-authority drift | Deterministic compositions, Doctor, isolated restore and v2 rollback pass |

## Measured resource envelope

- Jen's accepted 1080p HEVC run stayed at 667–669 MiB Kodi RSS, approximately
  104–106% of one logical CPU and at most 57 °C, with no OOM, throttle, hang or
  reset. This remains a Jen-only 1080p/stereo constraint, not a v3-wide limit.
- Page activation took 33.5–85.9 ms; declared data readiness stayed below
  1.02 s and per-route receive traffic stayed below 74 KiB.
- Artwork binding completed in 284.6–820.9 ms with no player and at most
  82,727 received bytes per route.
- The 12-second Jen camera measurement used four frames, 4.44% CPU,
  116,388.75 B/s receive and 26,848 KiB RSS growth; the viewer stopped and Home
  was restored.
- Canonical end-to-end Remote speech returned the fixed phrase in 256.6 ms,
  without retained audio or transcript.
- The page-aware idle canary held 529–550 MiB observed Kodi RSS and uses no
  sound or network path.

These figures leave practical headroom for the accepted low-spec role. They do
not qualify 4K, passthrough or production-room behavior on Jen.

## Permission, privacy and network review

- Browser Remote access is limited to explicitly mapped private sources; direct
  gateway access and forged Guest access fail closed.
- Each room polls outbound with an independently revocable identity. No inbound
  television listener or browser-held service credential exists.
- Equipment actions are fixed by room and capability. The gateway cannot name a
  Home Assistant entity, domain, service or arbitrary payload.
- Content publication contains no media title, library identifier, path, plot
  or account. Home Assistant recorder remains empty for that schema.
- The camera viewer and speech path retain no images, audio or transcripts.
- Secret-pattern scanning covers 93 candidate files; release artifacts contain
  opaque custody references only.
- Guest remains non-deployable until its hardware, identity, address, network
  and acceptance gates are complete.

## Reliability and operational-cost review

- The immutable v2.0.7 payload, per-room checkpoints and host-bound accepted
  state remain the recovery authority.
- Complete compositions are deterministic. Two post-acceptance builds
  reproduced every pinned bundle, plan, guard and SBOM hash.
- Doctor, Beszel, NetBox, wiki, reviewed reference, derived mirror and isolated
  restore currently report zero automated readiness gaps.
- The reliability service can clear only the narrow stale Music latch after
  repeated idle/empty proof. It cannot stop playback or mutate queues.
- Optional Aster AI, Remote, Home/cameras and Home Assistant paths have explicit
  degraded states; their outage must not break local media playback.
- Historical freeze records are retained rather than rewritten. This adds a
  small documentation burden but preserves an auditable recovery chain.

## Deliberate residual work

1. Bedroom's accepted content transport is narrower than its complete desired
   composition. The equipment helper and wider manifest must not be installed
   by inference.
2. Bedroom equipment and content-volume authority remain disabled until the
   owner observes the LG/ARC/eARC/CEC chain and chooses room levels.
3. The external Media Lifecycle replacement view has not been handed off. The
   four exact v2 smart-playlist routes remain the safer fallback.
4. Family's final v3 promotion follows Bedroom soak and explicit authorization;
   accepted M7 slices are not a substitute for that release decision.
5. The household guide is drafted but needs a non-author walkthrough and owner
   acceptance.

## Recommendation

Retain the current architecture and complete the remaining physical gates
without adding new services. Do not solve the open Bedroom observations with a
global default, borrowed Family values or a hardware adapter unless the native
LG path fails its bounded test. Do not replace the Media Lifecycle fallbacks
until the external artifact carries stable Jellyfin/TVDB/IMDb identity and
passes search, resume, watch-state and screensaver continuity.

Evidence sources:

- `docs/projects/evidence/AsterTV-v3-M10-Jen-HEVC-2026-11-06.md`
- `docs/projects/evidence/AsterTV-v3-M10-Jen-page-latency-2026-11-06.md`
- `docs/projects/evidence/AsterTV-v3-M10-Jen-artwork-readiness-2026-11-06.md`
- `docs/projects/evidence/AsterTV-v3-M10-Jen-camera-and-identity-2026-11-06.md`
- `docs/projects/evidence/AsterTV-v3-M10-Mac-speech-authority-2026-11-06.md`
- `docs/projects/evidence/AsterTV-v3-M10-automated-closure-and-M11-freeze-2026-11-06.md`
- `docs/projects/evidence/AsterTV-v3-M11-post-acceptance-reconciliation-2026-11-06.md`
