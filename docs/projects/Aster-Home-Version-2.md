# Aster Home version 2 - bounded household upgrade

## 1. Header and authorization

- Owner: Jason. Created: 2026-10-23.
- Status: active, M1 read-only Music pilot deployed on HP; native owner walkthrough pending. **Stream M - Monitored.**
- Started: 2026-10-23, by the owner's explicit start request. Remote milestone
  approvals remain required; this does not convert the project to Stream A.
- Scope authority: owner's marked review and subsequent chat clarification.
  Items 01-26 and 31-32 were selected; all unticked items are deferred.
- HP (`192.168.1.140`) is the v2 lab. BOSGAME (`192.168.1.157`) stays on its
  accepted family-beta release until a separately approved promotion.
- Up Next is urgent and extracted into the separate
  [v1.1 project](Aster-Home-Version-1.1-Up-Next.md); v2 consumes its accepted
  result, not another implementation or an excuse to delay it.
- This document is not permission for service/identity/firewall/firmware
  mutations. Each bounded remote milestone needs immediate approval.

## 2. Purpose and current baseline

Make Aster a coherent, premium, remote-first television interface with useful
episode discovery, music listening, Books narration and Home integration.
BOSGAME and HP now run the separately approved v1.1.1 package
with unified Aster Intro/Outro controls. HP retains LibreELEC 12.2.1/Kodi 21.3
and BOSGAME its accepted hardware-specific OS. English stream
preferences, watch badges, compact player controls, stop-on-exit, audio
playback, six-hour audio catalogue refresh and startup splashes are delivered
baseline/regression checks, not new v2 promises.

Audiobook/podcast progress synchronization is not implemented. eBooks remain
a frozen 505-title catalogue until Reader work. Cameras need a production
delivery path. YouTube API setup remains paused until the owner is available.
Music currently has Home, Albums, Artists, Songs and Playlists; genre metadata
is displayed but there is no dedicated Music Genres destination. The seven
TV/film genre destinations are unrelated to the owner's music-genre request.

## 3. Frozen scope inventory

Review IDs refer to the printable review, not a new priority ordering.

| IDs | Selected delivery and measurable boundary |
|---|---|
| 01 | Series hero, Resume next, season chooser (single-season simplification/Specials), vertical episode still/S-E/synopsis/duration/date rows, stable progress and focus; real numbering only. Up Next behavior comes from v1.1. |
| 02-03 | Predictable rail/Back and destination focus; grouped global search; truthful empty/loading/offline/denied states; unified Continue for video/audio/reader only when real source progress exists. |
| 04-05 | Complete modern compact OSD contract, retaining ten video functions, factual stream details, sensible remote seeking/auto-hide/overlay behavior, and regression protection for stop-on-exit. Add a genuinely interactive scrub bar, not just a passive progress line. |
| 06-08 | Stateful album/playlist/queue shuffle, Up Next queue, Play Next/Later, remove/save/confirmed clear, quiet audio-quality/output details and restrained art-derived atmosphere. Radio only with real recommendation data. |
| 09-12 | Audiobookshelf-authoritative book and per-episode podcast resume/completion, multi-file/chapter correctness, speed, progress and sleep presets; bookmarks after conflict testing; show/episode details and persistent queue. No auto-subscribe/download. |
| 13-15 | One-chapter DRM-free EPUB Reader proof, adjustable reading page, canonical local Aster narration and measured word alignment/highlighting/page turns; stable EPUB-location resume and explicit private cache removal. Expand only after timing/latency/remote gates. |
| 16-17 | Story-aware Digest timeline, Next/Previous, images/selection synchronized to audio, safe source/read actions; briefing queues only with stable service identities/durations. Breaking News stays distinct. |
| 18-21 | Intent-grouped Home grid and exception badges; read-only production camera delivery with freshness/privacy; named HA timers and explicit local fallback; bounded feed freshness and confirmations for sensitive actions. |
| 22 | Remote-friendly offline-capable network/link/IP/gateway/DNS/service diagnostics, refresh/reconnect where safe, no secrets. |
| 23 | Identify real G20 power event; persist progress then supported suspend; targeted USB wake and full HDMI/HDR/audio/network recovery matrix, overnight test and honest Display off fallback. |
| 24 | Aster/Dim/Black/Disabled idle modes, OLED-safe restrained composition, privacy-first defaults, media/alarm handling, one-input wake without accidental click and restored focus. |
| 25 | Modern YouTube destination resembling the media page with tiles, graphics and hero. Official add-on API setup is an owner-dependent gate, not satisfied by ordinary sign-in. No downloader. |
| 26 | Guarded HP POST-logo/black-image feasibility with official model-supported utility, recovery USB and removal/cold-boot proof. Optional gate must not block software release; BIOS upgrade is separate maintenance. |
| 31-32 | Common unclipped focus contract, reduced motion/high contrast, sofa readability, bounded artwork/background work, automated focus tests, live smoke/soak/performance and independent rollback evidence. |

### Confirmed additions and clarifications

- **V2-A Voice search:** microphone capture and remote event discovery,
  explicit listening indicator/cancel, local STT via the approved Aster voice
  contract, grouped search results and keyboard fallback. No ambient recording
  or cloud speech. Voice capture/permissions and server reachability are gated.
- **V2-B Premium controls and icons:** remove stone *texture* from buttons and
  heavy control backgrounds; modern, restrained focus and materials. Retain
  approved Aster identity/assets; tidy icon sizing, alignment, consistency and
  fallbacks. Do not redraw the supplied logo/icon family.
- **V2-C Seerr integration:** the actual project is
  [seerr-team/seerr](https://github.com/seerr-team/seerr). Discover/request/status
  through existing Seerr authority and a dedicated least-privilege user path;
  never embed an admin API key in a skin or call Radarr/Sonarr directly.
  Request submission must be an explicit user action with visible outcome,
  quota/permission failure and duplicate handling. No replacement Seerr service.
- **V2-D Music Genres:** create a dedicated music-genre browse page using the
  owner's roughly seven rationalized categories. Read current catalogue genres
  first; confirm the exact canonical list/aliases rather than copying video
  genres or inventing music buckets. Genre -> albums/artists/songs and Play /
  Shuffle should preserve context and remote focus.
- **V2-E Shuffle all music, excluding Holiday/Christmas:** explicit whole-library
  action, excluding holiday/Christmas classifications at track and inherited
  album metadata level. Test mixed compilations and aliases without removing
  unrelated music just because a title contains a seasonal word. Define the
  canonical exclusion tags at metadata discovery. Do not mutate library tags,
  overwrite saved playlists or silently truncate to the first 500 songs.

## 4. Exclusions and change control

- 27 external CEC accessory trial, 28 mobile Jellyfin branding, 29 lower-spec
  Lenovo deployment and 30 Blu-ray assessment are **deferred to v3**, not v2.
- No YouTube subscription downloader is scheduled for v2 or v3.
- No renewed VNC/Apple Screen Sharing experiment, DRM removal, PDF/OCR or
  fixed-layout Reader expansion, public ingress or automatic production rollout.
- No unrelated firmware/OS updates, automatic purchases/subscriptions or media
  acquisition. Seerr requests retain existing household approval policy.
- Once this scope is set, only obvious corrective fixes from v1.0.5 beta may
  enter automatically. Record reproduction and regression evidence. New features
  are parked for a later release unless the owner explicitly changes scope.
- The owner's later unified Intro skip / credits-triggered Play next request is recorded in v1.1,
  not silently added to this v2 scope. This specific chat addition is explicit.

## 5. Authority, architecture and privacy

Kodi owns client focus, playback/queues and its indexed library. Jellyfin owns
video/music catalogue, watch state and user access; its Kodi add-on syncs the
local index. Audiobookshelf owns listening progress; Calibre owns EPUB source;
Home Assistant owns household/timer state; news publishing owns story identity
and timing; Seerr owns requests. NetBox owns infrastructure facts, not content.

Existing private HTTPS and per-user identities are preferred. Define each new
adapter's API, permission set, timeout, offline/cache behavior and revocation
before deployment. Tokens stay outside source/skin/release archives and URLs.
No cloud book text, narration, microphone recordings or private images. All
new Aster-generated speech must use canonical Kokoro ONNX `bm_daniel`, en-gb,
speed 0.95 and the shared cleanup/cadence; prerecorded media is not new TTS.

The shared [Aster UI guide](../design/HomeLab-UI-Style-Guide.md) governs privacy,
accessibility and voice. The owner-accepted TV gold/green/neutral identity is
the explicit product-specific visual baseline, not an unsolicited navy/cyan
recolour. Latest owner direction removes stone texture from controls.

## 6. Pre-start assessment and approval gates

Local charter/code/tests are authorized; Stream M requires approval of each
live candidate. Main risks: focus/playback regressions, wrong-user progress,
queue loss, microphone privacy, unsafe request authority, stale camera imagery,
sleep/wake failure and firmware recovery. Stage on HP, checkpoint first, stop
on identity/topology surprises, and never broaden service trust as a shortcut.

Before a milestone starts, record actual dependencies, affected user/data,
minimum permissions/network rules, expected interruption, success/failure
tests, private backup and rollback. Reader, voice, camera, Seerr and firmware
require their own bounded gate; this charter is not sufficient live approval.

## 7. Milestones, persistence and resumability

- [x] M0: scope, additions, exclusions and separate v1.1 priority recorded.
- [ ] M1: read-only music genre/tag inventory, focus/design contract and small
  visual prototypes; select canonical music categories and holiday exclusions.
- [ ] M2: series/episode and shell/global search, premium controls/icons and
  scrub behavior; include accepted v1.1 and remote-only tests.
- [ ] M3: music queue, shuffle/whole-library exclusions and genre destination.
- [ ] M4: ABS progress/conflicts and listening tools; Digest refinements.
- [ ] M5: gated Reader/voice and explicit-request Seerr integration.
- [ ] M6: authorized Home camera/timer/feed integration; network/idle/suspend.
- [ ] M7: accessibility/performance/soak/recovery and family candidate.
- [ ] Optional firmware gate: independent recovery/install/removal validation.

Each gate ends with dated evidence, tests, limitations and focused local commit.
Preserve immutable accepted artifacts and private profile checkpoints. Record
the exact next safe action before any pause; no reliance on chat memory.
Push only after specific approval, then verify the Forgejo-owned GitHub mirror.

## 8. Acceptance and operating handover

Every selected visible action must be reachable/reversible by G20 alone, with
stable focus, truthful failures and no hidden background playback on full-player
exit. Episode transition and watch state must agree across repeated sessions.
Music full-library shuffle excludes tagged holiday content without dropping
ordinary tracks; queue edits cannot corrupt saved playlists. ABS resume passes
pause/Stop/Back, restart, outage/retry and cross-client conflict tests. Reader
timing cannot accumulate drift. Cameras cannot show old stills as live.

Validate sleep/wake ten times idle, ten paused and overnight per hardware;
test 1080p canvas/scaled 4K, temperature/memory/artwork latency and AVR output.
Before promotion, owner walkthrough covers launch paths, authentication, normal
buttons/statuses, offline recovery and rollback. Firmware unsupported is a
documented optional failure, never a reason to bypass protections.

## 9. Recovery, maintenance and integration impact

Preserve v1.0.5 and accepted v1.1 packages, user profiles, remote maps, service
settings and splashes outside Git; verify archive/member integrity. Rehearse
restore to an isolated profile/client before release. Roll back only affected
components, not unrelated server or household changes. New adapter/cache state
must have an explicit authority/schema and safe atomic publication.

| Integration | Requirement at its affected milestone |
|---|---|
| Doctor / monitoring / Beszel | Define useful reachability, freshness and progress failures; reconcile affected service/host coverage, document native-monitor exclusions; no duplicate noisy agent solely for a skin. |
| Backup/security inventory | Private verified checkpoints, cache retention and secret custody/rotation/revocation; no secrets in release artifacts. |
| NetBox / DNS / firewall / certificates | No M0 changes. Reconcile actual new service/interface facts; each later narrow rule or endpoint separately approved and validated. |
| Wiki / operational reference / Aster mirror | Update accepted behavior and recovery only after milestone evidence, with provenance; mirror is derived, not authority. |
| Repository / diagrams / rack / Homepage | Portfolio/charter now; topology and service-discovery changes only if real architecture changes. |
| Authentication / AI administration | Use dedicated capability-bounded identities for Seerr/other adapters. Broker preferred; record unsupported AI admin and human path where necessary, never share admin authority. |
| Schedules / feeds | Declare owner, limits, missed-run/failure visibility, atomic last-good state; reuse established refresh where possible. |

## 10. Evidence and next safe action

2026-10-23: owner confirmed Seerr spelling, music (not video) genre question,
whole-library shuffle excluding holiday/Christmas, deferral of all unticked
items, v2 project creation and urgent separate v1.1 Up Next. HP-only v1.1 test
deployment subsequently approved. No v2 live mutation occurred.

Owner subsequently directed v2 to start and deferred v1.1 production deployment
until the production unit is not in use. No automatic deployment or polling
job was created; obtain an explicit idle/promotion confirmation before
interrupting BOSGAME. The existing HP v1.1 candidate stays independently
recoverable while v2 develops locally outside its release source trees.

M1 started with two complete read-only HP AudioLibrary inventories: 1,335
albums, 17,113 songs, 21 raw genres (six broad groups plus 15 legacy labels).
The proposed seventh display bucket is Other / unclassified, retaining eight
unmatched tracks rather than inventing a genre. Track-only Christmas exclusion
would catch 585; album inheritance catches 765 across 74 Christmas albums,
retaining 16,348 eligible tracks. No metadata, queue, playback, service,
credential, network or deployed skin was changed.

Added an isolated pure policy prototype under `services/kodi/v2/`, with 11
passing tests including full-library >500 coverage, album inheritance, unknown
genres and no source mutation. A read-only real-data execution reproduced the
same 16,348/765 split. Category counts, proposed exact aliases, exclusion rules
and focus/control contract are recorded in
[M1 music and focus design](../design/Aster-Home-v2-M1-Music-and-Focus.md).
Current work produces no speech and introduces no live integration objects;
Doctor/Beszel/NetBox/DNS/firewall/backup coverage remains unchanged. Git holds
only aggregate counts, local prototype and tests, not a library export.

Local visual/focus prototype completed under `services/kodi/v2/prototype/`,
using existing supplied assets, flat controls and truthful preview-only actions.
Ten focus-model checks and Chromium checks pass; the browser test covers assets,
row-column restoration, immediate Music rail focus, hero entry, search, modal
return and layout bounds. The inspected 1080p screenshot and reproduction
instructions are included with the prototype. Eleven policy tests and three
unchanged v1 package tests pass. Neither box was changed.

Next safe action: owner visual/category-policy review, then the bounded HP
implementation/deployment/rollback proposal. M1 remains open until its
visual/focus and category-policy review gates pass. Do not begin a
service-dependent live milestone without its immediate approval. Research basis:
[original recommendations](../design/Aster-Home-v2-Recommendations.md),
[Seerr upstream](https://github.com/seerr-team/seerr), and
[existing media request authority](Unified-Media-Automation-and-Recommendations.md).

2026-10-23 follow-up: owner accepted the local Music design preview. Category
aliases/exclusion policy still need explicit confirmation before live queue
integration. Owner also lifted the production hold and requested v1.1 deployment;
both clients now have verified candidate9, including the minor TV hero artwork
fallback repair, tracked in the separate v1.1 project. This does not deploy any
v2 code or authorize its next HP mutation. Next safe action is the bounded HP
implementation/recovery proposal, not another production deployment.

The owner subsequently corrected v1.1 to available episodes only. The approved
v1.1.1 patch is verified on both clients: no caught-up/future placeholders, older
started shows considered beyond the former 24-show cutoff. This correction is
part of the v2 regression baseline, not a deferred new feature.

2026-10-23 continuation: pushed completed Aster work through v1.1.1 to Forgejo;
read-only GitHub mirror verification matched `a326417fc46cafb2588e5f14305442c7053a68d8`.
No direct GitHub push. Continued v2 locally with a full-library genre/album/
artist/song adapter and truthful partial-read handling. Thirty-one v2 tests,
ten focus-model checks and three unchanged release checks pass. Read-only HP
execution resolves the complete 17,113 tracks / 1,335 albums / 1,042 artists and
preserves 23 tracks whose artist-credit joins are missing; those credits are
flagged unavailable rather than guessed. The initial artist-enriched query's
998/1,000 mismatch was detected, investigated read-only and covered by tests.
No database repair, installed v2 code, player/queue action or production change.

The M1 design record now includes the bounded **read-only, separately identified
HP lab-script proposal**, initial 3.18-second two-pass build timing, integration
impact, rollback and unresolved package/G20 gates. Next safe action is to build
that isolated pilot locally, then request its exact HP install/launch approval.
Do not treat this continuation request as permission for live queue operations,
a skin/profile switch or server-side music metadata repair. New v2 work remains
a separate local milestone until another specific push approval.

2026-10-23 HP pilot: owner explicitly approved deployment. Built isolated
`script.astermusic.v2lab` 0.1.0 and installed/enabled only that ID on HP after a
verified private registration/GUI/keymap checkpoint and one clean Kodi restart.
Final candidate2 has seven manifest-matched files. All 153 installed v1.1.1
files, 136 selected AV/language settings and exact G20 map remain unchanged.
BOSGAME was not touched. Recovery archive is independently hashed off-device;
isolated registration restore passed quick_check. Fifty v2 tests and three
v1.1.1 package tests pass; two independent live GUI workflows verify browse,
search/paging, actual Select dispatcher, Back/rail/column restoration, explicit
unknown-credit notices and cancelled refresh preserving last-good data. No
playback, queue or watch-state change; no persistent catalogue export.

The [M1 design/operator record](../design/Aster-Home-v2-M1-Music-and-Focus.md)
contains artifact/checkpoint locations, launch command, recovery and truthful
pilot limits. The native pilot is left open on HP for owner review. M1 stays
open for physical G20/sofa/visual acceptance and policy review before real queue
integration. Next safe action is that walkthrough and local planning for the
next bounded milestone, not changing production or silently enabling playback.
No new infrastructure/credential/monitoring object or speech; existing Kodi
health remains responsible. Wiki/mirror publication waits for acceptance.

2026-10-23 continuation: Jason accepted the native appearance, requesting only
clock centring. HP candidate3 adds vertical alignment in the isolated pilot XML,
with prior XML checkpointed and a native screenshot inspected; 24-hour time and
pill geometry are unchanged. No Kodi restart, production change or v1 baseline
drift (153 files verified). The pilot remains read-only.

Local-only queue proposals now cover Play Next, append, explicit replacement,
stale-preview detection and full-library holiday-excluding shuffle. Ten new
tests cover duplicates/order, current position, empty/invalid/oversized queues,
complete catalogue and inherited holiday tags. This module is deliberately not
packaged or connected to Kodi. Total: 61 v2 tests, ten focus checks and three
unchanged v1 package checks passing. See the M1 record for limitations. Next:
local album track-order resolution and queue UI/confirmation design; physical
remote/policy review and separately approved live playback tests remain gates.
No new push authorized or performed in this continuation.
