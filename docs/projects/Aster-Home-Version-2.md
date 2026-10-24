# Aster Home version 2 - bounded household upgrade

## 1. Header and authorization

- Owner: Jason. Created: 2026-10-23.
- Status: active; Music implementation and HP pilot continuation is now
  **Stream A - Autonomous**, explicitly directed by Jason on 2026-10-23.
- Started: 2026-10-23. Earlier evidence below retains its historical Stream M
  approvals; the bounded Stream A envelope below governs current continuation.
- Scope authority: owner's marked review and subsequent chat clarification.
  Items 01-26 and 31-32 were selected; all unticked items are deferred.
- HP (`192.168.1.140`) is the v2 lab. BOSGAME (`192.168.1.157`) stays on its
  accepted family-beta release until a separately approved promotion.
- Up Next is urgent and extracted into the separate
  [v1.1 project](Aster-Home-Version-1.1-Up-Next.md); v2 consumes its accepted
  result, not another implementation or an excuse to delay it.
- Service/identity/firewall/firmware changes and production promotion remain
  outside the current autonomous Music envelope. All Forgejo pushes are held
  at Jason's request; retain focused local commits instead.

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

Local charter/code/tests are authorized. Current Music continuation follows the
bounded Stream A envelope below; other service-dependent gates remain closed.
Main risks: focus/playback regressions, wrong-user progress,
queue loss, microphone privacy, unsafe request authority, stale camera imagery,
sleep/wake failure and firmware recovery. Stage on HP, checkpoint first, stop
on identity/topology surprises, and never broaden service trust as a shortcut.

Before a milestone starts, record actual dependencies, affected user/data,
minimum permissions/network rules, expected interruption, success/failure
tests, private backup and rollback. Reader, voice, camera, Seerr and firmware
require their own bounded gate; this charter is not sufficient live approval.

### Current Stream A authorization envelope — 2026-10-23

Jason directed: “Continue stream a on this work. Don’t stop until you need my
approval. Reserve forgejo pushes until later.” This supersedes per-change
Stream M approval for the current Music implementation, not the frozen scope or
non-waivable controls. Enumerated changes:

- Local v2 Music code, tests, album/queue UI, package generation, docs and
  focused local commits outside the accepted v1 source trees.
- Checkpoint, install/update and launch only `script.astermusic.v2lab` on HP
  `192.168.1.140`; bounded native navigation/screenshot tests and reopening the
  pilot are permitted. Verify previous files and rollback before each update.
- Read Kodi catalogue and queue state without retaining paths/tokens; develop
  queue proposal/confirmation and playback safeguards locally. Keep HP writes
  to queue/playback disabled until a concrete live playback/recovery assessment
  and unresolved category/exclusion policy are accepted. This is a retained
  decision gate, not a request for approval of routine reads or pilot updates.

Affected authority is HP's isolated lab add-on; existing Kodi owns the index
and queues. No new service/network path/account is needed. Risks are a broken
pilot, lost browse focus or misleading preview: preserve the immutable prior
ZIP plus exact installed files, verify the new manifest, fail closed on stale
or unsupported queues, exercise Back/focus and confirm unchanged player/queue
and all 153 v1 files. Roll back only the pilot. Stop rather than interrupt real
playback or restore an unverified checkpoint. A Kodi restart is not expected;
an unexpected need to stop it must be assessed before proceeding.

Exclude BOSGAME, server metadata/watch/progress changes, saved-playlist writes,
credentials, voice/microphone, Seerr submission, cameras, infrastructure,
firmware and all Git remote writes. No cloud catalogue export, new spoken
output or monitoring object; existing Kodi health remains the native monitor.
Operational/wiki publication and release promotion wait for accepted behavior.
Policy decisions, unexpected blast radius or failed recovery require Jason.

#### Approved first live Music trial — 2026-10-23

Jason explicitly approved both outstanding decisions: retain the seven displayed
Music groups and track-plus-album holiday exclusion (16,348 eligible / 765
excluded in the current index), and enable/test HP-only live controls with at
most three indexed songs and verified queue checkpoint/restore. Listening-history
updates for these test songs through normal playback were disclosed and accepted;
no source-tag repair or manual server progress edits are authorized.

Implementation remains inside the isolated lab add-on. A short-lived HP-only
capability identifies the three test song IDs; absent/expired capability means
read-only previews. For this first test, require an idle empty music queue,
retain/verify its private checkpoint, cap the trial queue at three items and
refuse files/streams, stale state or unrelated playback. Replace needs explicit
confirmation; append/insert must preserve the current item without clear/reopen.
Stop-on-exit stops only the trial-owned player and restores the original idle
queue; refuse to overwrite unexpected external changes. Verify actual play,
pause/resume, queue order, Back/exit-stop and restoration. Disable/remove the
capability after testing. No production, audio/display settings, saved playlists,
credentials, new services or pushes. A failed safe restore or material side effect
outside this envelope requires Jason before further mutation.

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

2026-10-23 next continuation: Jason requested the push; saved work through
`40f14133` is now on Forgejo and verified at the same GitHub mirror ref. Continued
locally with a read-only ordered-album resolver, excluded from the pilot bundle.
Two complete reads and exact complete-catalogue album membership guard against
truncation/change; disc/track sorting never substitutes title order. The retained
HP stdin-only probe validates three multi-disc sample albums and truthfully
rejects two albums containing six unnumbered tracks. No metadata repair,
installation, playback/queue write or production change. 76 v2 tests, ten focus
checks and three unchanged release checks pass. The M1 design record contains
limits/evidence and the next bounded player/queue approval gates. New ordered-
album work is a local milestone; no second push implied by the completed push.

2026-10-23 Stream A milestone: updated the autonomous envelope and portfolio;
installed only the HP isolated candidate6 with verified recovery checkpoints.
Album selection now opens artwork-left / unboxed-tracks-right native detail,
per-track options and whole-album queue previews. Queue snapshots are read-only,
complete, duplicate-preserving and fail closed for files/streams or changing
state. Fixed actual native Back-focus reset and verified the exact tile returns.
90 v2 tests, ten focus checks, three unchanged package checks and both native
smoke paths pass. Native screenshot inspected; immediate recovery ZIP restored
independently into a disposable Mac directory and all eleven hashes verified.
All 153 installed v1 files unchanged; no playback/queue writes, production
contact, Kodi restart, settings/keymap/registration or infrastructure changes.

The [M1 design record](../design/Aster-Home-v2-M1-Music-and-Focus.md) and
`services/kodi/v2/releases/music-v2lab-album-preview-0.1.0.json` hold artifacts,
recovery, operator behavior and remaining gates. HP is left on album detail.
Autonomous continuation now reaches the retained decision gate: category/holiday
policy acceptance and a first idle HP-only live queue/player test of at most
three songs, with queue checkpoint/restore and acknowledgement that test playback
may update listening history. No automatic source retagging or production
promotion. Forgejo pushes remain expressly held; completed milestone stays local.

2026-10-23 approved live trial completed: Jason approved both the seven Music
groups/inherited holiday policy and the bounded three-song HP test. Final
candidate13 passed the retained complete native trial with exact current-track
identity/advancing clock, Pause/Resume, Add/Play Next without restart, confirmation
and cancellation, Replace without auto-play, ready-player Back stopping audio,
empty queue/originating tile restore and return to read-only after capability
removal. One track actually played; three approved IDs exercised queue order.
This is transport/decoder evidence, not a human listening or output-quality test.

Found a real existing integration behavior: Jellyfin's monitor unconditionally
clears playlists three seconds after Stop. The isolated adapter now settles that
known cleanup without modifying Jellyfin or fighting it by silently re-adding
tracks. Queue persistence across Stop remains M3 work. Also fixed idempotent
close, cancel-only popup Back isolation and ignoring late input while closing;
the harness now waits for ready-player/window-close states. Early startup Back
can be consumed during loading and remains an explicit hardening/acceptance case,
not a passed claim. All failed attempts had capabilities removed and empty queue
restoration independently verified before continuation; no last recovery copy
was removed or unrelated queue overwritten.

#### Approved broader HP Music testing — 2026-10-23

Jason approved expanding the HP-only trial to full albums, holiday-excluding
full-catalogue shuffle, recoverable queue backups and startup cancellation
hardening. This supersedes the earlier three-ID test ceiling only for the
current isolated HP Music candidate. Production and all Git pushes stay held.
Normal listening-history effects of short test samples remain accepted; do not
play the entire catalogue unattended or edit source tags/server history manually.

Enumerated implementation/test changes: extend the expiring HP-local grant to
the verified indexed song-ID set, cap its queue at 20,000 items, populate in
batches of at most 200, retain private atomic queue-intent/checkpoint records,
test explicit replay of intent after Jellyfin Stop, and add cancellable startup
within the isolated add-on. Profile files and the lab add-on are the only write
targets. No Jellyfin patches, existing keymap edits, services or infrastructure.

Before each live run require idle/empty queue, verified checkpoint and prior
package recovery, no foreign player and at least 512 MiB available memory. Record
queue timings/resource use and exact membership/order. Abort further staging on
low memory or unexpected state; stop only owned test playback and restore the
known baseline. Requests/pending writes are not transactional: retain intent and
halt rather than overwriting an unknown queue or retrying an uncertain write.
Startup cancellation must either prevent Open or wait for its owned outcome and
clean up; never leave an unresolved writer running while starting another test.
Metadata-only source operations remain read-only; no cloud exports or new speech.
Any need for keymap/vendor changes, failed recovery or broader resource impact
requires Jason rather than treating this approval as unrestricted admin access.

Prior three-song trial evidence, before the expanded trial below:
107 v2 tests plus all 144 unchanged v1 tests and ten focus checks pass. All 153
installed v1 files and 68 selected AV/language settings hash-match; Kodi active,
zero automatic restarts. Pre-trial eleven-file ZIP restore verified independently
on the Mac. The private `trial-complete.json` confirms no player, original empty
queue, no capability/recovery flag and read-only album state. Final release record:
`services/kodi/v2/releases/music-v2lab-live-trial-0.1.0.json`.

No production contact, Jellyfin patch, saved-playlist edit, tag repair, credential,
service, network or Git remote change. Normal test-track listening-history updates
were explicitly accepted and are not rolled back. Next gate is broader HP-only
full-album/full-catalogue shuffle/performance testing, with recoverable queue
intent and startup cancellation work; this first three-ID approval is not an
unbounded live-playback grant. Scope expansion/promotion and all pushes stay held.

#### Expanded trial outcome and hold — 2026-10-23

Implemented local candidate14/15: explicitly bounded grants (20,000 total,
200 IDs per write), complete two-read queue verification after each batch,
private atomic queue-intent journals, explicit confirmed replay after Stop,
and native cancellable startup. No silent automatic replay or skipped songs.
118 v2 unit tests, all 144 unchanged v1 tests and ten focus checks pass.

HP evidence: full 11-track Cranberries album queued in disc/track order and
played with advancing clock. Candidate14 passed cancellation both during staging
and immediately after accepted Open, restoring the original empty queue. Native
`live_startup_cancel.py` passed actual progress-dialog Back cancellation, a
subsequent normal full-album start and Back stop/origin-tile restoration. Candidate15
also verified durable intent and explicit replay after Jellyfin's delayed Stop
cleanup. These are bounded samples, not a soak or listening-quality acceptance.

Two blockers prevent graduation:

1. The first 200-ID catalogue batch yielded exactly 199 items: one known song
   with an unavailable primary artist relationship was omitted by Kodi. No
   unexpected IDs/order changes. Read-only SQLite audit of HP `MyMusic83.db`
   finds **23 songs lacking primary song_artist relations**, zero dangling
   artist references. The diagnostic batch was checkpointed, provenance/order
   verified and only that owned idle batch cleared; original empty queue was
   independently restored. Do not claim the full 16,348-item holiday-excluding
   shuffle passed or silently exclude these records. Library repair is outside
   this add-on/profile-only authorization.
2. During candidate15's larger repeated-album cancellation test Kodi crashed
   (SIGSEGV, service exit 139, one automatic restart). Its crash report's top
   frame is `JSONRPC::CTCPServer::Announce`. The harness uses TCP JSON-RPC with
   per-request connections; the exact crash trigger/cause is not established.
   Do not conflate passing native in-process cancellation with a crash-free
   bulk TCP test, change vendor Kodi, or resume live stress tests without a new
   explicit risk decision. Report: private
   `/storage/.kodi/temp/kodi_crashlog_20261023222828.log`.

Stop-on-surprise was applied. HP isolated add-on rolled back to known candidate13;
all 12 hashes verified against its recovery ZIP, also independently copied to
the Mac and all member hashes checked. Candidate15 and all intent/checkpoint/
crash evidence retained. Kodi is active on ordinary Home, original queue empty,
no player/capability/recovery flag; all 153 v1 files and 68 AV/language values
still match. No production contact, database repair, Jellyfin/keymap/settings
change, intentional service restart or remote Git write. Source candidate15 is
retained locally but **not active/accepted**. M3 remains open.

Private evidence root:
`/storage/.aster-checkpoints/aster-music-expanded-trial-20261023/`:
`before-candidate14`, `before-candidate15`, per-run intent/baseline records,
verified partial-batch recovery and `rollback-complete.json`. Latest release
record: `services/kodi/v2/releases/music-v2lab-expanded-trial-0.1.0.json`.
Next decision: separately authorize a checkpointed HP-only primary-artist-link
repair using verified metadata (no guessed credits), plus bounded retesting
through Kodi's in-process interface rather than the bulk TCP harness. This is
not production promotion or permission to patch Kodi/Jellyfin. Forgejo hold stays.

#### Approved HP repair and bounded retest — 2026-10-23

Jason approved checkpointed HP-only repair of verified artist links and crash
investigation/bounded retesting. Production and Forgejo remain held. Audit shows
all 23 song display credits blank, with no existing primary/secondary relations;
no exact named-artist match. Kodi 21.3's own source requires a canonical missing-
tag artist relation when credits are absent. Existing HP artist 1 is verified
as `[Missing Tag]` / `Artist Tag Missing`; restore only that structural link,
not guessed named performers or album-artist inference. Leave display credits,
source files/tags, Jellyfin mapping/history, all other DB tables and settings
unchanged. No credential-store reads, server writes or vendor patches.

Before mutation: require idle/empty HP; briefly stop only Kodi, make private
SQLite backup, integrity/hash verify and rehearse repair/restore on a disposable
copy. Apply in one guarded transaction; fail/rollback on changed count, nonempty
credit, secondary relation, trigger side effect or unrelated table hash drift.
Retain before/after evidence and restart Kodi. Retest in-process only, bounded
stages with queue restoration, memory/health checks and no repeated bulk TCP
connection churn. Another crash or unverifiable recovery stops live work.
No new voice, network exposure, scheduled task or production promotion.

2026-10-23 repair evidence: all 23 missing relations had blank song display
credits and no secondary artists, not a uniquely verifiable named performer.
Restored Kodi's own canonical missing-tag relation only (artist 1 already
verified as `[Missing Tag]` / `Artist Tag Missing`), matching its
[21.3 AddSong policy](https://github.com/xbmc/xbmc/blob/21.3-Omega/xbmc/music/MusicDatabase.cpp#L730-L732).
No names inferred from titles or compilation album artists. Source metadata,
every original song field/history and every other SQLite table hash unchanged
at repair commit. Backup/rehearsal passed integrity and logical-table checks;
independent Mac copy SHA-256 matches, integrity OK and original 23 missing
relations retained. Private recovery:
`/storage/.aster-checkpoints/aster-music-artist-repair-20261023/`.
Normal playback history updates during approved subsequent samples are expected,
not undone. No vendor/server/credential edits; no automatic recurring DB repair.

Crash mitigation: retire the bulk per-call TCP harness and run queue/GUI tests
inside Kodi with `xbmc.executeJSONRPC`. The original top frame and
[Kodi 21.3 TCP source](https://github.com/xbmc/xbmc/blob/21.3-Omega/xbmc/network/TCPServer.cpp#L219-L237)
are consistent with connection/disconnection concurrency, but do not establish
the exact crash cause or a general Kodi fix. Do not patch/upgrade Kodi from
this evidence. One planned stop/start for the SQLite repair; no unexpected
restart since that planned restart.

First repaired in-process complete test passed all 16,348 eligible IDs in exact
seeded order, 765 holiday exclusions, sample playback/advancing clock and
original empty-queue cleanup; album replay and both startup-cancellation cases
also passed. Run `run-1792821428900959476` retains ID-only intent and results.
Staging/sample took **624.8 seconds**; Kodi process peak RSS 883,840 KiB and
minimum system available memory 14,767,624 KiB. The old result key says
`harness_peak_rss_kib`; in-process this actually measures Kodi's process peak.
This passes correctness, not family-facing loading performance or all-track
decoding/physical listening. No silent exclusion of uncredited songs.

Candidate16 native read-only album smoke and startup cancel/full-album/Back
passed in-process. Initial GUI harness attempt caught a changing queue between
its own reads during normal Stop cleanup; it restored the baseline, removed its
grant and reported failure. Harness now waits/retries only that explicit
read-transition condition; the retained second run passed, not hidden as a
first-attempt pass. Placeholder artists remain explicitly uncredited in the
v2 category model, not counted as real performers.

Candidate17 keeps all writer limits and full two-read order checks, but reads
the approved <=20,000-item trial queue in one bounded page. Kodi GetItems copies
its whole queue before pagination, so repeated 500-item pages cause avoidable
work. Default preview reader remains 500; all 127 v2 tests pass including full
16,348-ID two-read and external reorder rejection. Native performance retest
completed: private run `run-1792822397090396741` passes full 16,348-item exact
order/membership, 765 exclusions, sample clock/playback, intent replay, both
startup cancellation cases and original queue cleanup. The order hash matches
the earlier slower run. Staging/sample improved to **176.4 seconds** (3.54x);
Kodi process peak RSS 1,003,480 KiB, minimum system available 14,498,572 KiB.
Whole-run RPC profiling records 108.3 seconds in 551 GetItems calls and 65.3
seconds in 86 Add calls; remaining pre-play staging is still too slow for a
family-facing button. No unexpected restart during either complete retest.

Candidate17 also passed native read-only album smoke and startup-cancel / normal
album start / Back-stop tests, all in-process. Native temporary grants removed.
127 v2 tests, all 144 unchanged v1 tests and ten focus checks pass. Candidate17
ZIP SHA-256 `fb2767b1145ccadf9a851eb9d8cd238b4582c35ffea83bd19989d135558002a6`,
13 files; all intermediate ZIPs and candidate13/16 recovery trees retained.
The pilot remains read-only by default; global Shuffle All is still a truthful
eligibility preview, not a falsely advertised instant player.

Next bounded risk decision: an HP-only progressive shuffle trial, initially
start a small verified batch then append the remainder in a controlled worker.
This is a new concurrent playback/background-staging phase, not automatically
authorized by this repair. Keep existing ID-only guard, 200-per-write/20,000-total
ceilings, complete queue checks and temporary grant expiry. Back/Cancel must
signal cancellation, join/resolve its writer before Stop/Clear, and restore the
original queue; no abandoned worker or overwriting external state. Brief samples
only; pause during extended fill if necessary. Production/pushes/vendor changes
stay excluded. M3 is not graduated and physical remote/listening/soak remain.

Final native post-check `postcheck-1792822789043203801.json` verifies candidate17
13 files, all 153 v1 files, all 68 selected AV/language values, SQLite integrity,
zero missing primary links, no player, original empty queue, no temporary grant
or recovery flag and read-only album. Kodi active with zero unexpected restarts
since the planned DB-repair stop/start. Recovery records retained; new release
handoff: `services/kodi/v2/releases/music-v2lab-repair-retest-0.1.0.json`.
No production contact or Forgejo/GitHub push. Stop at progressive-worker risk
decision, not routine read-only validation or another general project approval.

#### Stream A clarification and progressive loading — 2026-10-24

Jason clarified: “Why stop you are authorized to continue and you have work.”
Continue HP-only Music implementation and progressive trial under Stream A;
the self-imposed progressive-worker conversational gate above is superseded.
Do not ask again for ordinary implementation choices within this envelope.
Production, remote Git writes, vendor/credential/infrastructure changes and
non-waivable recovery/surprise controls remain excluded/mandatory respectively.

Progressive implementation: first 25 verified song IDs start playback; one
owned joinable worker appends at most 200 IDs per request, <=20,000 overall,
with unchanged full queue checks, short-lived grants, private complete-intent
checkpoint and >=512 MiB resource floor. No GUI calls in worker. Exit signals
cancellation without acquiring its queue lock, joins the pending batch, then
stops only owned playback and restores the original idle queue. Fail on external
queue/player changes; no blind retry or detached writer. Initial HP tests use
brief real samples, pause during full fill if needed, explicit private recovery
and unchanged v1/AV checks. No new speech or service/monitoring object.

Full native candidate29 test `run-1792852425749841437` passed the final default
50-item fill size: first owned player **1.102s**, complete background fill and
brief resumed sample **587.919s**; **16,363 eligible / 765 excluded**, exact order
SHA-256 `cd4849fdec675ca6ed14e810993e0ed19ec19a2d502b57a3d00fec938d3f7277`.
An earlier cancellation in the same run started in 0.843s and restored idle in
3.643s. Audio was paused during the extended fill. The catalogue legitimately
gained 15 ordinary songs since the previous 16,348-ID snapshot; counts were
re-read, not hardcoded or dropped. Complete intent, grant/evidence and original
empty-queue checkpoint are private under the progressive checkpoint root.

The longer background fill is an explicit responsiveness tradeoff, not a
regression hidden as instant full-library readiness. Native UI reports loaded
count, refuses unloaded selection, pages the queue in 200-row windows and
separately marks current playback. Actual controls use a joinable worker with
priority between fill batches. Natural track-boundary inconsistencies may retry
only reads; no queue mutation is blindly retried. Stop waits for the existing
Jellyfin delayed-clear window, without modifying Jellyfin/vendor code.

Retained failed GUI attempts exposed asynchronous list initialization and
unawaited test focus transitions. Initialization now waits for the populated
list; harness waits for each native focus transition. Subsequent native runs
passed paging without playback change, loaded-track selection/title/art,
Pause/Resume, Back-stop and Home-stop. No physical-remote/listening or complete
file-decode acceptance is claimed. Global Home's hidden parent-window cleanup
is the final candidate30 correction; its own native/preservation outcome is
recorded below after validation, not inferred from candidate29.

Candidate30 final native runs passed: Back `native-ui-1792853137532588373.json`
(Select 1.649s, Pause 1.816s, audio stop 1.558s, cleanup 5.544s), and Home
`native-ui-1792853211877776472.json` (Select 1.836s, Pause 1.703s, cleanup including
one-second stable-Home check 6.356s). Both verify queue paging does not alter the
playing song, loaded-track selection updates metadata, grants removed and queue
restored. The postcheck verifies 14 installed lab files/archive, all 153 v1 files,
all 68 AV/language values, SQLite integrity and zero missing primary artist
links; no player, queue, grant, recovery flag or hidden lab window. Kodi active,
zero unexpected restarts since the planned repair restart.

Candidate30 ZIP SHA-256
`16d0b9b3b12ccf1bc21b65aeb93d44fcef072842a736ca82c6f01b818211c968`.
Candidate29 recovery ZIP/tree retained at
`/storage/.aster-checkpoints/aster-music-expanded-trial-20261023/before-candidate30`.
143 v2 tests, 144 unchanged v1 tests and ten focus checks pass locally. Historical
failed attempts and crash evidence remain retained. This is a passing HP
engineering milestone, not M3/production graduation or family acceptance.
Continue Music controls under Stream A; no production contact or remote push.
