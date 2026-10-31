# AsterTV v3

> Status: Active — Stream A page-redesign pilot on the Mac mini; M0 read-only
> discovery started, live pilot setup pending pre-start risk acceptance
>
> Project owner: Jason
>
> Proposed: 2026-10-31
>
> Current authorization stream: Stream A — limited to the Mac-mini page-
> redesign pilot enumerated below. The project transitions to Stream M at the
> pilot acceptance gate; every later live state change and external write then
> requires a fresh, bounded approval.

## Purpose and desired outcome

Develop AsterTV v3 as a private, account-aware household interface that brings
the existing whole-home Aster AI, media, books, music, news, requests and Home
Assistant together without making Kodi, Aster or automation an undocumented
single point of failure.

The user-visible outcome is a coherent remote-first television experience with:

- the existing whole-home Aster AI available through a clear, cancellable TV
  interaction;
- system-wide household accounts plus a deliberately isolated guest mode;
- richer movie details and cast/crew discovery;
- a redesigned YouTube experience with safe guest access;
- better eBook pronunciation and accurately timed single-word follow-along;
- consistent Aster iconography on News;
- podcast discovery and requests;
- a more informative Home page and a separate camera page, including an
  explicitly enabled continuous feed and safe door-event previews;
- a least-privilege Home Assistant bridge for AsterTV state, playback,
  notifications and room automations, with economical TV/soundbar control;
- a free, installable iPhone Aster Remote web app for touch navigation,
  playback, search, room power and volume without App Store distribution;
- page-aware media and music idle presentations; and
- an evidenced low-spec hardware baseline.

V3 must preserve the accepted v2 navigation, playback, Dolby/HDR, recovery and
privacy behaviour unless a replacement passes the same or stronger gate.

## Current state and evidence

### Accepted v2 baseline

- AsterTV v2.0.7 is frozen in
  `services/kodi/dist/astertv-v2.0.7-release-2026-10-31.tar.gz` with SHA-256
  `e813de8a74af769ebbfeb744ad65249760292f647dc2d91c4bafb9fc7ba83cf7`.
- Git commit `47005298bbaf058de8427342e54deb3e1878c0f5` records the
  release builder, manifest, regression gates and deployment evidence.
- **AsterTV Family** is the production client at `192.168.1.157`, system
  hostname `AsterTV-Family`.
- **AsterTV Bedroom** is the current lab/baseline client at `192.168.1.140`,
  system hostname `AsterTV-Bedroom`.
- The Family display chain includes a TCL QM8L Google TV and an Onkyo TX-RZ30
  9.2-channel receiver. The receiver supports network standby and direct local
  Home Assistant control; the television exposes Google/Android TV remote
  control and CEC/eARC settings. Reconfirm exact addresses, firmware, cabling
  and enabled standby controls in M0.
- Both clients run the same 577-file Aster-owned snapshot, 24-hour clock and
  Aster media-art screensaver. Family retains verified HDMI 0 Dolby/HDR
  passthrough with PulseAudio persistently masked; Bedroom retains its supported
  stereo route.
- A fresh read-only Family check on 2026-10-31 reports Kodi 22.0 RC1
  (`21.90.901`), Git `01d4146d5d251a0118b99a1de0d713395c93bd46`, on
  LibreELEC 13 nightly `20261021-440640e`. Bedroom did not answer SSH during
  that check and remains a PA0 re-verification item; the Mini pilot must match
  the confirmed Family Kodi release rather than the Mini's retained Kodi 21.3
  profile.
- The v2 release gate contains 21 reconciliation tests plus focused Genre,
  Resume and media-screensaver gates. Recovery checkpoints and the prior v1.1.1
  Family baseline remain available.

### Existing service boundaries

- Jellyfin remains the film, television and music library/playback authority.
- Seerr remains the film/television household request authority.
- Audiobookshelf remains the audiobook, podcast and listening-progress
  authority; the eBook reader consumes prepared narration generations without
  packaging credentials.
- The deployed eBook narration path uses the canonical Aster Kokoro voice and
  exact sentence timing. Earlier word-level experiments did not meet the real-
  book timing gate and were not promoted.
- The official Kodi YouTube add-on provides the signed-in account's
  recommendations, Subscriptions, Watch Later and search. V2 deliberately does
  not copy YouTube credentials between clients.
- Home Assistant is the household-state authority. Camera imagery is exposed
  to AsterTV through a restricted source path; it is not ordinary media-library
  content.
- The existing whole-home Aster AI is a separate, established system. V3 will
  integrate through its reviewed service and broker boundaries rather than
  embedding a new model or copying its credentials into Kodi.
- A tentative low-spec test machine is expected on 2026-11-01: likely a
  fourth-generation Intel Core i5 with 8 GB RAM and a 240 GB SSD. CPU, GPU,
  firmware, network and display outputs are unverified.
- In lieu of that unavailable machine, Jason selected the M4 Mac mini as the
  immediate page-redesign pilot. Read-only discovery on 2026-10-31 found macOS
  26.6.2 on `Mac16,10` with 16 GB RAM, a retained Kodi 21.3 ARM profile last
  used in October, Aster skin/add-ons versioned `1.0.0`, and no current
  `/Applications/Kodi.app` or `~/Applications/Kodi.app`. The retained skin is
  an earlier prototype with substantial drift from the accepted v2 payload;
  it is evidence only and must not become the v3 source of truth.

Reconfirm all live versions, endpoints, account capabilities and hardware facts
in Milestone 0; this document does not turn remembered state into authority.

## Scope and permitted local work

The repository's common project authorization permits read-only discovery,
project/design work, local candidates, tests and local commits. After the
applicable Stream A envelope or a fresh bounded Stream M approval, the project
may:

- create a replaceable v3 candidate on the new low-spec test client or another
  explicitly selected lab target;
- extend the Aster skin and owned Kodi add-ons for the approved v3 features;
- define and implement a least-privilege Aster AI client path;
- add a bounded Home Assistant bridge for Kodi/AsterTV state, commands and
  events, plus model-verified television and soundbar control;
- build a local-first Progressive Web App (PWA) remote backed only by that
  bounded bridge, with no Kodi or Home Assistant credential shipped to the
  browser;
- add account/profile selection and per-account data separation;
- redesign Movies, YouTube, Books, News, Requests and Home/camera surfaces;
- add a page-aware Music idle presentation to the existing Aster screensaver;
- create narrow service identities, broker capabilities and private network
  paths needed by accepted features;
- add regression, performance, security, recovery and user-workflow tests;
- freeze an immutable v3 candidate and deploy it Lab first, then Family only
  after explicit acceptance and promotion approval; and
- reconcile Doctor, Beszel, NetBox, backup, operational reference, wiki and the
  derived Aster knowledge mirror where those systems own affected facts.

During the current Stream A pilot only, the project may additionally install an
official hash-recorded Kodi 22.0 RC1 ARM application in a dedicated writable Mini
pilot location, always launch it in portable mode, create a credential-free
synthetic AsterTV v3 data directory, deploy page candidates to that portable
instance, restart only that pilot instance, capture screenshots/navigation
evidence and restore or remove only the dedicated pilot. These autonomous
permissions do not extend to the retained Mini Kodi profile, Family, Bedroom,
Home Assistant, cameras, credentials, source services or network policy.

## Explicit exclusions

- No public ingress, WAN port forward, public camera URL or broader Home
  Assistant trust path.
- No production-first development and no writable code/configuration shared
  between Lab and Family.
- No copying Family, Bedroom, YouTube, Aster, Home Assistant or camera
  credentials into a new client, Git, prompts or release artifacts.
- No automatic media acquisition from an AI response. Requests remain explicit
  user actions and use the authority for that media type.
- No camera recording, facial recognition, person identification or new
  retention policy merely to support a TV preview.
- No unbounded always-on microphone, hidden recording or wake-word capture.
- No door-event pop-up that silently overrides protected playback, ignores
  quiet hours or exposes a camera to an unauthorized account.
- No inferred word timing presented as exact narration alignment.
- No replacement of Jellyfin, Seerr, Audiobookshelf, Home Assistant, Frigate or
  the existing whole-home Aster AI under this charter.
- No automatic firmware, LibreELEC, Kodi, add-on or model upgrades.
- No Bluetooth audio route for television playback: HDMI/DisplayPort remains
  the accepted audio/video path and must preserve the target's Dolby/stereo
  contract.
- No assumption that Bluetooth availability is a generic power, input, volume
  or state-control API. Device profiles and standby behaviour must be proved
  per model before Bluetooth control can graduate.
- No arbitrary shell, unrestricted Kodi JSON-RPC or broad Home Assistant
  service execution exposed through the bridge.
- No public remote-control endpoint, direct browser-to-Kodi credential, App
  Store dependency or paid Apple developer account.
- No promise that an iPhone Home Screen web app can intercept the phone's
  physical volume/side buttons, enter Apple Control Centre, provide native Siri
  Remote integration, remain continuously active in the background or replace
  a physical remote during a network/bridge outage.
- No tag, Forgejo/GitHub release, remote workflow mutation or Git push without
  the repository's required immediate confirmation.
- No mutation, migration or deletion of the Mini's retained
  `~/Library/Application Support/Kodi` profile during the Stream A pilot.
- No real household credentials, library databases, viewing history, Home
  Assistant state or camera imagery in the portable page-design fixture.
- No Family or Bedroom deployment, production promotion or source-service
  mutation under the Stream A page-redesign authorization.

## Authority model

| Fact or action | Authority |
|---|---|
| V3 scope, decisions, milestones, risks and evidence | This project document and its Git history |
| Accepted v2 code, release bytes and rollback contract | Commit `47005298`, v2 release manifest and reconciliation record |
| Installed client state and hardware capability | The named client's live, sanitized evidence |
| Film, TV and music library/playback state | Jellyfin |
| Film and television requests | Seerr |
| Audiobook/podcast catalogue and progress | Audiobookshelf |
| eBook catalogue | Adopted Calibre/CWA metadata source; confirm exact read boundary in M0 |
| eBook narration readiness | Accepted narration-generation manifest and ready-generation store |
| YouTube identity, subscriptions and watch lists | Google/YouTube account exposed through the official Kodi add-on |
| Household identity and profile mapping | The identity design selected in M1; no authority is assumed yet |
| Household entities, state and automations | Home Assistant |
| Kodi/AsterTV playback and application state | The named AsterTV client, represented in Home Assistant through the bounded bridge |
| TV/soundbar power, input and volume state | The device's verified native network integration where available; otherwise the selected bounded control adapter |
| Aster Remote identity, session and permitted actions | The v3 account authority plus the bounded bridge; the PWA is an untrusted presentation client |
| Camera events and imagery | Frigate/camera source plus Home Assistant event state, as deployed |
| Aster AI answers, capabilities and approvals | Existing Aster service, AI Access Broker and their governing projects |
| Device, address, interface and service inventory | NetBox |
| Credentials | Central secrets system and source service; values never enter Git or project evidence |
| Human operation and recovery | Human wiki/runbook after handover acceptance |
| Derived Aster knowledge | Aster mirror, explicitly non-authoritative and provenance-labelled |

AsterTV is a presentation and interaction client. It must not overwrite a
source because its cached view disagrees with that source.

## Proposed architecture and data flows

```mermaid
flowchart LR
    U["Household user + G20 remote"] --> TV["AsterTV v3 client"]
    P["iPhone Aster Remote PWA"] --> RB["Authenticated remote gateway"]
    RB --> KB
    ID["Account/profile authority\nselection pending"] --> TV
    TV --> J["Jellyfin\nlibrary + playback"]
    TV --> Y["Official YouTube add-on"]
    TV --> S["Seerr\nfilm + TV requests"]
    TV --> B["Audiobookshelf / eBook reader"]
    TV --> H["Restricted Home adapter"]
    H --> HA["Home Assistant"]
    H --> C["Camera/event source"]
    HA --> KB["Bounded AsterTV/Kodi bridge"]
    KB --> TV
    HA --> AV["TV/soundbar control\nnetwork preferred; IR fallback"]
    TV --> AB["AI Access Broker"]
    AB --> A["Existing whole-home Aster AI"]
```

Initial trust rules:

| Flow | Initial v3 state | Expansion gate |
|---|---|---|
| User to AsterTV | Local remote interaction | Account selection must remain operable offline with documented recovery |
| AsterTV to Aster AI | Denied until client contract is reviewed | Dedicated identity, exact broker capabilities, cancellation and content-free audit tests |
| AsterTV to YouTube guest | Not implemented | Prove profile isolation and primary-account non-disclosure before acceptance |
| AsterTV to requests | Existing film/TV Seerr path only | Podcast provider and duplicate/idempotence contract selected before writes |
| AsterTV to Home Assistant | Existing restricted display data | Add only exact entities/events needed by the redesigned page |
| Home Assistant to AsterTV | Not yet adopted as a v3 control contract | Dedicated Kodi credential, source-restricted private path, allowlisted playback/navigation/Aster actions and denial tests |
| Home Assistant to TV/soundbar | Capability unknown by exact model | Prefer official local network integration; use learned local IR when state feedback is unnecessary; evaluate Bluetooth only after profile/standby proof; buy CEC hardware only for an uncovered requirement |
| iPhone PWA to remote gateway | Not implemented | Private HTTPS/WSS, authenticated short-lived session, account/room allowlist, rate limits, CSRF/origin checks and no embedded service credential |
| Remote gateway to Kodi/Home Assistant | Denied except allowlisted actions | Translate semantic actions such as Up, OK, Back, Play/Pause, Search, Power, Volume and Mute; never proxy arbitrary methods or service calls |
| AsterTV to camera source | Existing bounded still path | Live feed and door preview require account, quiet-hour, timeout and playback gates |
| Narration generation to local AI stack | Existing registered workloads only | Every exclusive workload requires a verified Lab Hours reservation plus lease and shared lock |

## Privacy and security design

- Keep account mappings, watch/listening history, YouTube state, household
  presence and camera access separated by explicit profile rules.
- A guest profile must not expose or mutate the primary user's YouTube history,
  subscriptions, Watch Later, requests, books, Home controls or camera access.
- Prefer broker/proxy execution so AsterTV never receives Aster AI credentials.
  Use a dedicated `ai-*` identity and minimum capability set if supported.
- Display visible listening, processing, speaking, cancelled and failed states.
  Microphone capture must be user-initiated unless a separately reviewed wake-
  word design is accepted; recordings are not retained by default.
- Door previews must be opt-in, account-authorized, labelled by source, bounded
  by timeout, immediately dismissible and subject to quiet hours. Default policy
  during playback is non-interrupting notification; any overlay exception needs
  explicit acceptance and test evidence.
- A continuously visible camera feed is permitted only on an explicitly chosen
  display/profile and must not become a globally available route.
- Minimize logs: keep timing, state and error codes, not spoken phrases, titles,
  account identifiers, camera images or household entity values unless an
  accepted diagnostic requires a protected short-lived capture.
- Keep all credentials and recovery material out of release packages. Packages
  carry schemas and non-secret identity metadata only.
- Give each AsterTV client its own Home Assistant/Kodi identity and restrict the
  network path to the Home Assistant host and the minimum required ports.
  Expose allowlisted media/navigation/Aster actions rather than a general
  command or shell endpoint.
- Treat TV/soundbar volume as room equipment control during passthrough; do not
  alter Kodi's decoded volume or route protected playback over Bluetooth.
- For automatic volume, AsterTV reports an explicit coarse content class rather
  than forcing Home Assistant to infer custom News/Books playback from fragile
  metadata. Apply room-specific targets only at playback start or class change,
  ramp changes, cap nighttime levels, retain unknown content volume and suspend
  automation after a manual adjustment for the rest of that session.
- Treat the PWA as an untrusted client. Keep service credentials server-side,
  require an authenticated household session, authorize every action by room
  and profile, rate-limit commands and provide immediate session revocation.
- Use the Aster internal UI style guide for all surfaces, adapted to Kodi's
  remote/10-foot constraints and the accepted green/gold/stone AsterTV language.
- Any speech produced on Aster's behalf uses canonical Kokoro ONNX
  `kokoro-v1.0.fp16.onnx`, `bm_daniel`, `en-gb`, speed `0.95`, sentence/clause
  synthesis and the shared cleanup rules. A different voice requires an
  explicit decision and listening comparison.

## Pre-start risk assessment

| Risk | Likelihood / impact | Required control and residual risk |
|---|---|---|
| System-wide accounts leak one person's history or controls to another | Medium / High | Define a field-level profile matrix, guest-denial tests, clean-session switching and recovery admin. Some shared-library metadata remains inherently household-visible. |
| Guest YouTube uses or changes the primary account | Medium / High | Validate the official add-on's actual multi-profile capability; use separate profile storage or reject guest sign-in if isolation cannot be proved. |
| Aster AI integration exposes private context or gains excess authority | Medium / High | Dedicated broker identity, minimal tools, content-free audit, cancellation and prompt-injection/denied-action tests. Residual model error remains visible and non-authoritative. |
| Camera or door preview exposes private imagery | Medium / High | No public route, explicit account entitlement, quiet hours, short timeout, no default retention and denial tests from guest/unauthorized profiles. |
| Door pop-up disrupts playback or becomes nuisance automation | Medium / Medium | Non-interrupting default, debounce, rate limit, timeout, mute/quiet mode and direct playback regression. |
| Home Assistant bridge becomes a remote-control or command-execution backdoor | Low / High | Per-client credentials, source-restricted firewall, minimal ports, allowlisted actions, content-free audit and explicit denied-command tests. |
| Bluetooth appears cheaper but cannot wake or reliably control room equipment | Medium / Medium | Inventory exact models and advertised profiles; prove pairing, reconnect, standby wake and each command. Prefer native local network control, then IR; treat Bluetooth HID/AVRCP as experimental, not a CEC-equivalent assumption. |
| IR fallback loses state or sends a destructive toggle twice | Medium / Medium | Prefer discrete commands, correlate with network/power state, make automations idempotent and retain manual remote operation. |
| Automatic volume produces a startling jump or fights a manual adjustment | Medium / High | Per-room calibrated targets, bounded ramp, nighttime cap, playback-start/class-change triggers only, session manual-override latch, safe unknown-content behaviour and physical control fallback. |
| PWA exposes household control or becomes a general command proxy | Low / High | Private HTTPS/WSS, authenticated short-lived sessions, origin/CSRF checks, rate limits, per-room/profile authorization and a semantic allowlist with no arbitrary JSON-RPC, shell or Home Assistant service proxy. |
| iOS web-app limits are mistaken for native Apple Remote capability | Medium / Low | Document on-screen volume, foreground/reconnect and Siri/side-button limitations; keep the G20 and equipment remotes as supported fallbacks. |
| Word highlighting drifts from real narration | High / Medium | Use measured word timestamps from actual output; reject/invalidate a generation outside tolerance and retain sentence fallback. |
| TTS pronunciation changes damage accepted books | Medium / Medium | Versioned lexicon, representative listening corpus, canonical cleanup regression and per-generation manifest/rollback. |
| Podcast requests create duplicates or bypass subscription ownership | Medium / Medium | Select one request/subscription authority, stable IDs, duplicate-aware preview, explicit final action and reversible test feed. |
| Large skin rewrite repeats v2 navigation regressions | Medium / High | One bounded surface at a time, immutable v2 baseline, focus-graph tests, physical G20 walkthrough and cross-page regression suite at every milestone. |
| Mini pilot overwrites its retained Kodi profile | Low / High | Separate writable Kodi app bundle, mandatory `-p` launch wrapper, dedicated `portable_data`, preflight path assertion and untouched-profile hash/inventory comparison before and after every pilot milestone. |
| Old Mini prototype is mistaken for the accepted v2 baseline | Medium / High | Build v3 only from the immutable v2.0.7 release/payload and record overlay provenance; use the old profile only for read-only historical comparison. |
| Synthetic page design hides a broken live integration | Medium / Medium | Label every fixture, keep data adapters outside the visual contract, repeat navigation with malformed/empty/error fixtures and require later Stream M integration tests against each real authority. |
| Low-spec client produces misleading capability conclusions | Medium / Medium | Confirm exact hardware, measure rather than infer, separate hardware limit from software defect and retain Family/Bedroom acceptance. |
| Page-aware screensaver shows private Home/camera state | Low / High | Only allowlisted media/music artwork; fail closed to black Aster mark; never camera, Home, account or title-history metadata. |
| Local AI/TTS workload competes with protected lab work | Medium / High | Registered hash-pinned workload, authoritative Lab Hours window check/reservation, whole-host lease and shared lock; fail closed if any control is unavailable. |
| Production promotion causes loss of sound, Dolby/HDR or navigation | Medium / High | Lab-first immutable release, playback-idle precondition, profile/audio checkpoint, reboot validation, user acceptance and tested v2 rollback. |

No destructive or irreversible operation is required for design or Lab
development. A checkpoint failure, unexpected credential disclosure, undeclared
outbound path, unexplained source mutation, camera exposure, profile crossover,
unavailable Lab Hours ledger or loss of v2 rollback is an immediate stop.

Expected interruption is limited to the selected lab client during approved
deployments. Family interruption requires a separate promotion approval,
playback-idle evidence and a stated maintenance window.

The current Mini pilot does not interrupt either AsterTV appliance. It may open
and restart only the dedicated portable Kodi instance on the Mini. Discovery
and local candidate work can continue now; installing or launching that pilot
begins only after Jason accepts this updated pre-start risk envelope.

## Persistence and resume plan

This project is the durable state record. Before any long-running or risky step,
record the current milestone, exact candidate/commit, target, checkpoint,
validation state, blocker and next safe action in the evidence log.

On resume:

1. re-read `AGENTS.md`, `docs/Project-Creation-Standard.md` and this project;
2. inspect Git status and preserve unrelated work;
3. verify the v2 archive/hash and both retained v2 rollback paths;
4. recheck the live identity, Kodi/LibreELEC version and audio state of the
   intended target;
5. verify the latest accepted v3 candidate manifest and evidence rather than
   replaying completed work;
6. check Lab Hours before proposing or starting any exclusive local-AI/TTS
   workload; and
7. continue from the first unchecked gate only.

During the page pilot, also verify branch `codex/astertv-v3`, the official Kodi
artifact digest, the portable launch assertion and the retained Mini-profile
integrity record before opening the pilot.

Candidate installs must be idempotent, hash-pinned, checkpointed and atomic.
Partial generations or packages remain invisible to users. Jobs use bounded
retries, timeouts, locks and durable status; process absence is never success.

## Stream transition and page-redesign pilot

The project has exactly one active authorization stream at a time. It is
currently Stream A for the bounded pilot below. Completion or abandonment of
PA4 automatically ends Stream A. Before any remaining v3 implementation, this
document must record the transition to Stream M; no Stream A authority carries
forward.

### PA0 — Mini pilot foundation

- [x] Record the official Kodi 22.0 RC1 ARM download URL, digest and
  provenance evidence. The macOS ARM artifact is
  `kodi-22.0-Piers_rc1-arm64.dmg`, official SHA-256
  `5f50e35df66fdac2eb10b2915249d6ec8230da19833f1f00068200a744341e5b`.
- [ ] Reconfirm Bedroom's Kodi build when it is reachable and stop if it
  materially differs from Family's 22.0 RC1 release contract.
- [ ] Install it in a dedicated user-writable pilot location and create a
  launch wrapper that asserts portable mode and the expected `portable_data`
  path before execution.
- [ ] Seed only accepted v2.0.7 Aster-owned code/assets plus synthetic fixture
  data; do not copy the retained Mini profile or any deployed credential.
- [ ] Record an inventory/hash comparison proving the retained Mini profile was
  unchanged.

Gate: a disposable, credential-free Kodi 22.0 RC1 pilot starts independently on the
Mini and can be removed without changing the retained profile, Family or
Bedroom.

### PA1 — Shared v3 page language

- [ ] Create the v3 overlay/build boundary without modifying the immutable v2
  release payload.
- [ ] Reconcile common page chrome, focus, pills, Back/Home behaviour, hero
  treatment, empty/error/loading states and remote target sizing against the
  Aster internal UI guide.
- [ ] Add deterministic structural/focus tests and screenshot fixtures before
  applying the language to individual pages.

Gate: the shared shell passes static/focus regression tests and Jason accepts a
representative Mini walkthrough before all page conversions proceed.

### PA2 — Media page redesigns

- [ ] Redesign Movies/details with cast/crew artwork, roles, contextual cast
  search, More Like This, Play/Resume focus and details-before-playback.
- [ ] Redesign YouTube chrome, recommendation/subscription/watch-later/search
  surfaces and return paths using synthetic account-safe fixtures.
- [ ] Preserve the accepted v2 TV season/episode design as a locked regression
  reference; this pilot does not redesign it unless Jason explicitly adds it.

Gate: every entry/Back/OK/focus route passes on the Mini with synthetic normal,
empty, loading and error fixtures; no autoplay or v2 TV regression is present.

### PA3 — Aster, News, Requests, Home and Cameras page redesigns

- [ ] Build the Aster AI interaction shell for idle, listening, processing,
  speaking, cancelled and failed synthetic states without connecting a model or
  microphone service.
- [ ] Apply Aster icons and shared chrome to News while preserving digest and
  article interaction contracts in fixtures.
- [ ] Design podcast request discovery, details, duplicate/status and explicit
  submission surfaces without making a real request.
- [ ] Redesign the Home dashboard and separate Cameras page with synthetic,
  clearly labelled fresh/stale/unavailable/door-event states and no real image.

Gate: all surfaces pass the physical navigation/failure-state walkthrough and
contain no credential, household state, camera image or live write path.

### PA4 — Pilot reconciliation and mandatory Stream M transition

- [ ] Run cross-page focus, Back/Home, empty/error/loading, secret-pattern,
  retained-profile-integrity and v2 locked-surface regressions.
- [ ] Package the page overlay, fixture schema, screenshots, build manifest and
  removal/restore proof as a reproducible candidate; do not call it a release.
- [ ] Obtain Jason's page-design acceptance and record changes requested.
- [ ] Stop/remove or retain the portable pilot deliberately, record its exact
  state, and change this project's current authorization stream to Stream M.

Gate: page designs are accepted or their remaining changes are listed; the
Mini's prior profile and both appliances are unchanged; Stream A is closed and
all subsequent work is Stream M.

## Milestones

### M0 — Baseline discovery and decision register

- [ ] Reconfirm Family, Bedroom and the new low-spec machine hardware, OS,
  Kodi, add-ons, routes, audio/video capabilities and recovery state.
- [ ] Reconfirm the Mac-mini portable pilot boundary, retained-profile
  inventory and accepted-v2 overlay provenance recorded in PA0.
- [ ] Inventory existing Aster AI, account, YouTube, Seerr, Audiobookshelf,
  eBook narration, Home Assistant and camera contracts without reading secrets.
- [ ] Capture v2 user workflows and focus graphs as regression fixtures.
- [ ] Decide the account authority, profile data matrix, podcast request
  authority, YouTube guest feasibility and camera event source.
- [ ] Refresh this risk assessment and record unresolved owner decisions.

Gate: no v3 live mutation; an evidence-backed architecture and decision register
identify every authority, credential class and unsupported assumption.

### M1 — Low-spec lab foundation and release harness

- [ ] Confirm the new machine's exact CPU/GPU/RAM/storage/display/network facts
  and reconcile its NetBox record before configuration.
- [ ] Install the accepted v2 release as a credential-free baseline using a
  dedicated test identity and checkpoint.
- [ ] Measure boot, navigation, artwork, 1080p playback, screensaver, memory,
  storage and reboot behaviour.
- [ ] Create the v3 branch/build manifest, package validator and automatic v2
  rollback path without modifying Family.

Gate: the low-spec client can be rebuilt from documented inputs and restored to
the accepted v2 baseline; its measured limits are recorded honestly.

### M2 — Accounts, profiles and guest isolation

- [ ] Define system-wide account/profile schema, switching UX, recovery admin,
  shared versus private state and service mappings.
- [ ] Implement accounts first with synthetic users and no production tokens.
- [ ] Prove account switching, restart persistence, sign-out, missing identity,
  malformed state and guest denials.
- [ ] Test that guest mode cannot access primary YouTube state, requests, books,
  Home controls, cameras or Aster private context.

Gate: two synthetic accounts and guest remain isolated across restart and
adversarial navigation; recovery does not require the implementation agent.

### M3 — Aster AI television integration

- [ ] Define the dedicated AsterTV client identity, broker tools, approval class,
  secret custody metadata, rotation/revocation and break-glass path.
- [ ] Build visible listen/process/respond/cancel/error states using the G20
  microphone or a synthetic capture fixture first.
- [ ] Apply account context only after authorization and data-minimization tests.
- [ ] Test prompt injection, unavailable broker/model, timeout, cancellation,
  stale context, denied tools and restart during a request.
- [ ] Validate spoken output against the canonical Aster voice and cleanup.

Gate: AsterTV can complete two independent bounded Aster interactions without
receiving credentials, exposing another profile or obtaining general admin
authority.

### M4 — Movies and YouTube redesign

- [ ] Restyle the movie landing/details page while preserving details-before-
  playback, Resume, Back and Search return behaviour.
- [ ] Add cast/crew artwork, names and roles plus cast/crew search that retains
  current-movie context.
- [ ] Restyle YouTube with consistent artwork, pills, focus and return paths.
- [ ] Preserve recommendations, thumbnails, Subscriptions, Watch Later and
  search, then implement guest access only if M0/M2 isolation is proven.
- [ ] Run physical G20 focus/Back/playback tests from every entry route.

Gate: visual acceptance plus complete focus graph; no autoplay regression,
primary-account leak or loss of existing YouTube functions.

### M5 — Books, News and podcast requests

- [ ] Version and test an expanded pronunciation lexicon against representative
  real books while preserving current Aster corrections.
- [ ] Produce measured single-word timestamps from actual canonical narration;
  reject drift and retain sentence fallback.
- [ ] Add Aster icons to News pills without changing digest selection, reading,
  playback or shared chrome.
- [ ] Extend Requests to podcasts through the selected authority with stable
  IDs, preview, duplicates, status and explicit submission.
- [ ] Book every exclusive local-AI/TTS run through Lab Hours and retain
  workload/lease/lock evidence without secrets.

Gate: real-book listening and timing acceptance, News regression pass and one
synthetic/reversible podcast request path with no duplicate side effect.

### M6 — Home dashboard, cameras and door events

- [ ] Design a denser but remote-readable Home page using an explicit allowlist
  of Home Assistant entities and freshness/failure states.
- [ ] Build a separate Cameras page with named still/live sources, refresh state
  and reliable Back navigation.
- [ ] Add optional continuous feed mode for an explicitly authorized profile and
  display only.
- [ ] Add debounced door-event preview with source, timeout, dismiss, open-
  camera action, quiet hours and non-interrupting playback default.
- [ ] Test guest denial, stale/forged event, camera outage, HA outage, event
  storm, playback and immediate privacy disable.

Gate: approved accounts see only allowed entities/cameras; denials and failures
are explicit; playback and network isolation remain intact.

### M7 — Home Assistant bridge and room-equipment control

- [ ] Inventory the exact Family and Bedroom television, soundbar/receiver,
  connection path, network capabilities, Bluetooth profiles and standby/wake
  behaviour; do not infer control support from the presence of Bluetooth.
- [ ] Validate the Family TCL QM8L through Home Assistant's Android TV Remote
  path with Screenless/network standby enabled, and the Onkyo TX-RZ30 through
  the native local Onkyo integration with Network Standby enabled. Use direct
  receiver control for volume/mute and explicit on/off actions rather than a
  blind power toggle.
- [ ] Register both Kodi clients in Home Assistant with separate credentials,
  stable room names and only the minimum private network path required for
  state, playback, notifications and approved navigation events.
- [ ] Implement an allowlisted Aster action surface for safe page opens,
  searches and household scenes; reject arbitrary shell, unrestricted JSON-RPC
  and commands outside the active profile's authority.
- [ ] Define useful room entities and events: playing/paused/idle, media class,
  current Aster page, screensaver state, availability and explicit remote
  actions, without exporting viewing history into long-lived logs.
- [ ] Evaluate equipment control in this order: official local network
  integration, Wake-on-LAN where the model supports it, learned local IR,
  verified Bluetooth HID/AVRCP, then a CEC adapter only for requirements still
  uncovered. Record the capability and cost matrix.
- [ ] Prove Bluetooth pairing/reconnect, every required key, power-on from
  standby and state feedback before accepting it. Never use Bluetooth audio as
  the AsterTV media route.
- [ ] Build bounded automations such as cinema start/stop, door notification,
  pause/resume and room hand-off only after the underlying controls are
  idempotent and retain a physical-remote fallback.
- [ ] Add an explicit Aster content-class event/state covering Movie,
  Television, Music, YouTube, Podcast, News, Book/Audiobook and Unknown.
- [ ] Calibrate separate Family and Bedroom volume profiles. Movies are the
  loudest baseline, then Television, YouTube, Music, Podcast/News and Books,
  while the exact levels remain owner-accepted room settings rather than
  release constants.
- [ ] Apply the profile only at playback start or content-class transition,
  ramp safely, enforce a nighttime ceiling, latch manual override for the
  current session and optionally restore the pre-playback level at stop.
- [ ] Test Home Assistant outage, stale state, duplicate commands, restart,
  denied source, malformed action, passthrough playback and manual recovery.

Gate: Home Assistant can observe and safely control both AsterTV clients and
the accepted room-equipment functions without broad trust, loss of Dolby/stereo
behaviour or dependence on costly CEC hardware where a verified local network
or IR path is sufficient.

### M8 — Aster Remote iPhone web app

- [ ] Capture the useful Apple TV Remote interaction set as a design reference:
  swipe or directional navigation, tap/OK, hold for context, Back/Home,
  Play/Pause, volume, mute, power, text entry/search and explicit voice search.
- [ ] Build a responsive installable PWA with an Aster icon, manifest, service
  worker and offline shell. Safari's **Add to Home Screen → Open as Web App** is
  the supported free installation path; no App Store package is required.
- [ ] Provide Family/Bedroom selection, connection and playback state, a large
  touchpad plus accessible directional-button mode, OK/Back/Home, Play/Pause,
  on-screen volume/mute/power, search keyboard, voice-search gesture and
  allowlisted Aster page shortcuts.
- [ ] Provide two keyboard paths: a direct Aster unified-search field that does
  not require opening Kodi's television keyboard, and an explicit Kodi text-
  entry mode for the currently focused field with Send, Backspace, Clear,
  Cancel and Enter.
- [ ] Use the native iPhone keyboard for symbols, paste and optional iOS
  dictation. Submit completed text as one bounded action where possible rather
  than streaming every key; mask credential fields and never retain entered
  text, clipboard content or partial passwords in gateway logs or caches.
- [ ] Route every command through the authenticated remote gateway and semantic
  bridge allowlist. Keep Kodi, Home Assistant and equipment credentials out of
  browser storage, JavaScript and logs.
- [ ] Use private trusted HTTPS/WSS, short-lived sessions, account/room
  authorization, CSRF/origin checks, command rate limits, revocation and a
  visible disconnected/read-only state.
- [ ] Make foreground reconnect fast and deterministic. Cache only the static
  shell and non-sensitive preferences; never cache titles, history, household
  state, camera images or tokens as offline content.
- [ ] Document that iPhone physical volume/side buttons, native Siri Remote,
  Control Centre placement, guaranteed background operation, native haptics
  and lock-screen media controls are outside the PWA acceptance contract.
- [ ] Test touch/hold/swipe/rapid-repeat, direct search, active-field text,
  symbols, paste, dictation, masked input, keyboard and microphone permission,
  rotation/safe areas, sleep/wake, background/foreground, expired session,
  bridge/HA/Kodi outage, wrong account/room and command-flood denial on a real
  iPhone.

Gate: the PWA installs free from Safari, operates both rooms through only the
bounded bridge, covers the accepted on-screen Apple-Remote-like controls and
fails safely without exposing a service credential or creating a public route.

### M9 — Page-aware idle presentation and visual reconciliation

- [ ] Retain the accepted balanced TV/movie presentation.
- [ ] Add a Music presentation using random album artwork when the last active
  page is Music, with the AsterTV mark bottom right.
- [ ] Define neutral fallbacks for other pages and unknown state.
- [ ] Verify burn-in movement, wake return, playback/Home-timer suppression and
  absolute exclusion of cameras, household/account data and sound.
- [ ] Review every changed surface against the Aster internal UI guide and
  accepted AsterTV green/gold/stone interaction language.

Gate: page-aware behaviour is deterministic, private and reversible, with a
black branded fallback on missing or malformed artwork.

### M10 — Integrated validation, recovery and efficiency review

- [ ] Run functional, account-isolation, failure, security, focus/navigation,
  playback, audio/video and secret-pattern suites on the low-spec client.
- [ ] Prove interrupted install, corrupt package, dependency outage, reboot and
  full v2 rollback.
- [ ] Measure CPU, GPU, RAM, storage, page latency, artwork latency, network
  traffic, camera stream cost, speech latency and idle overhead.
- [ ] Complete Doctor, Beszel, backup/restore, NetBox, wiki, reference, mirror
  and AI-administration integration work.
- [ ] Complete a non-author walkthrough and correct avoidable friction.

Gate: two clean full-path passes, isolated restore, v2 rollback and documented
resource headroom; every deviation is fixed or explicitly accepted.

### M11 — Immutable release, Bedroom soak and Family promotion

- [ ] Freeze v3 as an identified commit plus reproducible manifest containing
  code, dependencies, schemas and material asset hashes.
- [ ] Deploy independently to Bedroom, preserving its v2 recovery checkpoint,
  credentials and stereo configuration; soak through reboot and normal use.
- [ ] Obtain explicit Family promotion approval after Bedroom acceptance and
  confirm playback is idle.
- [ ] Deploy independently to Family, preserving its v2 checkpoint, account
  state and verified HDMI 0 Dolby/HDR contract.
- [ ] Complete the user-facing handover, final intent/efficiency review, project
  records, focused commit and separately authorized Forgejo push/mirror check.

Gate: Jason accepts the household workflow on both targets; stopping Aster AI,
Home/cameras or any optional integration degrades clearly without breaking core
local media playback or recovery.

## Validation and evaluation matrix

| Class | Required evidence |
|---|---|
| Functional | Every named feature works from all intended entry points using the physical remote |
| Navigation | Explicit focus graph, OK/Menu/Back behaviour, return cursor and no inert controls on every changed page |
| Accounts | Cross-profile reads/writes denied, guest isolation, clean switch, restart persistence and recovery admin |
| AI | Dedicated broker identity, denied tools, cancellation, prompt injection, dependency failure and two independent passes |
| Speech | Canonical voice/settings, pronunciation corpus and measured word-alignment tolerance with sentence fallback |
| Privacy | No secret, phrase, image, household value or other account's behavioural state in logs, packages or UI |
| Cameras | Account entitlement, quiet hours, stale/forged event, outage, storm, dismiss and playback tests |
| Home Assistant bridge | Per-client identity, state accuracy, allowlisted actions, denied arbitrary commands, HA outage and source-restricted network path |
| Equipment control | Per-model power/input/volume matrix, standby/reconnect, duplicate-command safety, manual fallback and no Bluetooth-audio regression |
| Content volume | Correct class, per-room calibration, ramp/night cap, manual override, unknown fallback, stop/restore choice and passthrough preservation |
| Aster Remote PWA | Home Screen install, both rooms, touch/buttons/search/voice, foreground reconnect, session expiry, denied actions, no embedded credentials and physical-remote fallback |
| Media regression | Jellyfin playback, Resume, Intro/Recap/Outro, Search, TV seasons, Movies, Music, Books, News, YouTube and Requests |
| AV regression | Family Dolby/HDR HDMI 0 after reboot; Bedroom/low-spec supported stereo/video behaviour preserved |
| Failure/recovery | Interrupted promotion, corrupt state, missing dependency, restart, rollback and isolated restore |
| Performance | Low-spec and normal-client CPU/GPU/RAM/storage/latency/network measurements with accepted budgets |
| Accessibility | 10-foot readability, visible focus, non-colour status, remote target sizing and no clipped text |

## Observability and maintenance

- Add Doctor checks for release drift, required add-ons, account-store health,
  broker/camera/Home adapter/bridge/remote-gateway health and backup age using
  non-secret output.
- Reconcile all three clients in Beszel. Avoid duplicate alerts where Kodi/
  service-native health or Doctor already owns a failure mode.
- Record client CPU/RAM/storage/temperature and restart trends sufficient to
  identify the low-spec floor without collecting viewing history.
- Alert ownership remains Jason. Door/camera availability should not page unless
  explicitly chosen; core client/release drift and backup failures should be
  actionable.
- No automatic release/model/add-on upgrade. Review upstream changes, rebuild
  the immutable candidate, rerun gates and soak in Lab.
- Any recurring narration or AI job must record its registered workload,
  reservation, last success, bounded failure and concurrency controls.

## Backup, restore and rollback

- Retain the immutable v2 archive, manifest, commit, Family/Bedroom checkpoints
  and exact audio profiles until v3 graduates and its rollback has been tested.
- Protect v3 code, non-secret schemas, profile/account mapping state, user
  preferences, narration manifests/lexicon, Home/camera adapter configuration
  Home Assistant bridge/equipment capability manifests, remote-gateway
  configuration and system service definitions according to sensitivity.
- Keep service credentials in central secret custody and document rotation/
  revocation without values. A release restore must require reprovisioning, not
  contain the secret.
- Restore proof uses an isolated/disposable client or network-denied target
  first. Verify login/profile separation, navigation, playback and database/
  state integrity before reconnecting service paths.
- Rollback replaces only Aster-owned code/configuration from the accepted v2
  package, restores the target's own pre-v3 profile/audio/service checkpoint,
  restarts Kodi and validates no active player, sound, clock, screensaver,
  navigation and recovery-marker state.
- Revoke new v3 identities and remove narrow network paths if the project is
  abandoned. Do not delete household source data as rollback.

## Documentation and systems-of-record updates

| Integration | Required project treatment |
|---|---|
| HomeLab Doctor | Add non-secret client/release, adapter, bridge, account-store and backup-age checks; test failure output. |
| Monitoring/alerting | Reconcile Beszel names/agents for every client, including the low-spec device; document alert ownership and deliberate exclusions. |
| Backup and recovery | Add protected v3 state and exact restore order; prove isolated restore and v2 rollback. |
| NetBox | Reconcile Family, Bedroom and the new low-spec device/interface/MAC/IP/service facts through the API. |
| Human wiki | Publish AsterTV account, AI, media, Home/camera, privacy and recovery operator guidance. |
| Aster mirror/snapshot | Publish only salient, provenance-labelled non-secret operation/recovery knowledge after human docs are accepted. |
| Operational reference/runbooks | Record current client identities, release/hash, audio profiles, deployment, rollback and failure procedures. |
| Repository documentation | Maintain this project, release manifest, tests, package notes, portfolio, roadmap and changelog. |
| Diagrams/rack records | Update only if the new physical client or cabling is an adopted topology fact; otherwise record not applicable. |
| Homepage/service discovery | Add a private Aster Remote launch tile only if it improves household discovery; expose health without credentials and keep the remote unavailable outside its authenticated private route. |
| Authentication/authorization | Define account authority, guest isolation, recovery admin, Aster broker identity and per-service mapping. |
| DNS/certificates/firewall | No new public path. Add only exact private records/rules required by accepted adapters/bridge, source-restrict Home Assistant access and prove denial outside them. |
| Automation/schedules | Register narration/AI jobs; enforce Lab Hours, lease and lock requirements; document missed-run and last-success state. |
| Security inventory | Record secret custody identifiers, modes, temporary access removal, patch responsibility and rotation/revocation. |
| AI administration | Prefer a dedicated brokered `ai-astertv` identity with allowlisted capabilities; if unsupported, record human-only administration rather than weaken security. |

## User-facing handover

Before graduation, publish and walk through a concise AsterTV v3 guide that:

- identifies what changed from v2 and what remains deliberately unchanged;
- explains profile switching, guest limitations and account recovery;
- explains Aster listening/processing/cancel/error indicators and what Aster can
  and cannot do;
- covers Movies/cast search, YouTube, Books narration, News, Requests, Home,
  Cameras, door previews, Home Assistant room controls and screensaver
  behaviour;
- explains how to install the Aster Remote from Safari, select a room, use
  touch/directional controls, search, control volume/power, sign out/revoke a
  session and recover with the physical remote;
- states which information is private/shared and how to disable microphone,
  camera preview, continuous feed and door pop-ups;
- explains common failure messages, offline/degraded behaviour and safe
  recovery to v2; and
- records any manual account/device-code authentication Jason must complete
  outside chat.

Graduation requires a physical-remote walkthrough on Bedroom and Family plus
explicit user acceptance.

## Graduation criteria

- Every milestone gate is evidenced and all required integration items are
  complete or explicitly not applicable with reason.
- The immutable release is reproducible from Git and contains no credentials,
  profile data, recordings, camera images or household state.
- Account and guest isolation, camera privacy, Aster broker authority and
  canonical speech pass adversarial and recovery tests.
- The low-spec baseline has measured, documented limits and does not lower the
  Family/Bedroom acceptance standard.
- Bedroom and Family each pass two full production-path runs plus reboot; Family
  retains accepted Dolby/HDR and Bedroom retains working sound.
- Backup/isolated restore and v2 rollback are exercised, not merely described.
- Doctor/Beszel/NetBox/wiki/reference/mirror state agrees with deployment.
- The post-deployment intent and efficiency review confirms that every created
  integration delivers the desired user outcome without avoidable resource,
  latency, permission, storage, reliability or operational cost.
- Jason completes and accepts the user-facing walkthrough.
- Home Assistant bridge and room-equipment controls retain physical-remote
  recovery, preserve each target's audio contract and have no unverified
  Bluetooth dependency.
- Content-aware volume passes calibrated start/class/manual-override/nighttime
  tests in both rooms without changing Kodi passthrough volume.
- Aster Remote installs and runs as a free iPhone Home Screen web app, exposes
  no service credential and does not claim unsupported native iOS behaviour.
- No unexplained temporary identity, firewall rule, credential, candidate,
  recovery marker or working-tree state remains.

## Evidence log

| Date | Action | Evidence | Result / next safe action |
|---|---|---|---|
| 2026-10-31 | Established v3 backlog | Owner supplied eight feature groups; existing screensaver and low-spec items retained | Backlog converted into this project charter |
| 2026-10-31 | Recorded accepted predecessor | v2.0.7 archive SHA-256 `e813de8a…3cf7`, commit `47005298`, 21 tests plus focused gates, dual-target deployment evidence | V2 is the immutable baseline and rollback source |
| 2026-10-31 | Selected authorization model | Accounts, Aster AI, microphone, cameras and production playback create high privacy/availability coupling | Stream M selected; no v3 live mutation authorized by project creation |
| 2026-10-31 | Project integration | Added portfolio/roadmap/changelog records; retained the old wish list byte-for-byte because it is hash-pinned in the accepted v2 package | This project is authoritative; next safe action is M0 read-only discovery and owner decisions |
| 2026-10-31 | Added Home Assistant bridge workstream | Owner requested AsterTV automation and a lower-cost alternative to CEC adapters | M7 now requires per-model capability discovery and prioritizes native local network control, then IR; Bluetooth is accepted only after profile, reconnect, standby and command proof |
| 2026-10-31 | Refined Family equipment and content-volume design | Family equipment identified as TCL QM8L plus Onkyo TX-RZ30; official device and Home Assistant documentation confirms local network/standby paths | M7 now targets direct Onkyo volume/mute/power, TCL Android TV control, CEC/eARC coordination and guarded per-content room volume profiles |
| 2026-10-31 | Added Aster Remote PWA workstream | Apple Remote interaction review and Apple Home Screen web-app documentation | M8 specifies a free installable iPhone PWA through a private authenticated semantic bridge, with native iOS limitations explicit |
| 2026-10-31 | Completed Aster Remote input scope | Owner confirmed keyboard input is part of the requested remote | M8 now distinguishes direct Aster search from Kodi active-field entry and requires symbols, paste, dictation, masking and no input retention |
| 2026-10-31 | Started project and selected temporary design target | Owner authorized Stream A page redesign on the Mac mini followed by Stream M for all remaining work; created local branch `codex/astertv-v3` | Read-only PA0 discovery started; no live target changed and no remote Git write performed |
| 2026-10-31 | Inspected Mini Kodi state | M4/16 GB Mini on macOS 26.6.2; retained Kodi 21.3 ARM log/profile with Aster `1.0.0`; no installed Kodi app found; retained skin differs materially from accepted v2 payload | Use a production-matched official Kodi build in separate portable mode, seed from immutable v2.0.7, and leave the old profile untouched |
| 2026-10-31 | Defined sequential authorization | PA0–PA4 enumerate the only Stream A changes; Family, Bedroom, credentials, real integrations and source services excluded | Await owner acceptance of updated pre-start risk envelope before installing/launching the portable pilot; PA4 mandates transition to Stream M |
| 2026-10-31 | Pinned pilot Kodi to production | Family reports Kodi 22.0 RC1 (`21.90.901`), Git `01d4146…`, LibreELEC nightly `20261021-440640e`; official macOS ARM RC1 SHA-256 is `5f50e35d…341e5b`; Bedroom SSH timed out | PA0 uses Kodi 22.0 RC1 on the Mini and must recheck Bedroom when reachable; Kodi 21.3 is not the pilot runtime |

## Close-out

Not started. At completion, replace this section with the final architecture,
release/commit/hash, deployed identities, account authority, service and secret
ownership, recovery references, observed resource envelope, accepted residual
risks and deliberately deferred v4 work. Move the project only after all links
and systems of record are reconciled.
