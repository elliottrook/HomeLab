# Unified Recommendation Engine — mini-project

> Status: Active — Stream A; M6 refresh-quality maintenance
>
> Owner: Jason
>
> Proposed: 2026-10-07
>
> Started: 2026-10-07
>
> Authorization stream: Stream A
>
> Governing project: [Unified Media Automation and Recommendations](Unified-Media-Automation-and-Recommendations.md)
>
> Service ID / release: `media-acquisition-hub` / V1
>
> Environment: production application on TrueNAS VLAN 20 with private VLAN 50 ingress
>
> Build reference: repository revision pending M6 validation
>
> Rollback reference: deployed pre-M6 image plus the 2026-10-10 last-known-good snapshot

## Purpose

Build the recommendation engine behind the existing private Unified Media
Recommendations page. It will provide one explainable, one-stop queue for
films, TV, music, ebooks and audiobooks while leaving acquisition authority in
Seerr, Lidarr and LazyLibrarian. The page remains the approval surface; the
engine supplies better candidates, evidence and freshness.

## Recommendation contract

- Video candidates combine Jellyfin history/library signals with TMDb per-title
  recommendations and, optionally, personal Trakt recommendations; Seerr
  remains the request authority.
- Music candidates use Jellyfin listening signals plus MusicBrainz identity and
  a configured discovery source such as ListenBrainz or Last.fm; Lidarr remains
  the request authority.
- Ebook and audiobook candidates use Audiobookshelf/Calibre signals plus
  Open Library or Google Books metadata; LazyLibrarian remains the wanted-item
  authority.
- The B60 may produce local explanations and embeddings, but not direct access
  to download clients or production credentials. Core ranking is deterministic
  and auditable.
- Every card records source, rationale, candidate age, read-only source link
  and exact downstream action. No automatic acquisition, artist following,
  author following or series following.
- Jellyfin's official Trakt plugin is an optional personal-history feed. It may
  synchronize Jason's selected Jellyfin watch state to Trakt after explicit
  account authorization; it is not a bulk catalogue mirror or an authority
  for acquisition.

## Design-system prerequisite

The shared visual baseline is now documented in
[`docs/design/HomeLab-UI-Style-Guide.md`](../design/HomeLab-UI-Style-Guide.md),
with icon-family tokens in
[`docs/design/App-Icon-Family.css`](../design/App-Icon-Family.css). A new
Unified Media Recommendations icon source plus 180px and 32px derivatives are
tracked under `docs/assets/unified-media/`. Another agent may use the guide to
refresh the briefing UI without importing recommendation-specific code.

The approved icon is a required deliverable of this project: during the portal
milestone it will be wired into the private webpage favicon, manifest/touch
icon metadata and any Homepage tile that consumes the portal icon. The petals,
orbit and media cues are now the accepted visual baseline; future changes must
be separate revisions rather than incidental redesign during engine work.

## Current state and authority model

- The private recommendation portal already runs in the shadow Docker project
  at `recommendations.elliottrook.com` behind the existing Authentik/NPM path.
- The current snapshot is refreshed by the shadow refresher and uses bounded
  TMDb per-title video recommendations, deployed non-video adapters and
  personal Trakt recommendations. Trakt credentials are protected in the
  existing secret boundary and are refreshed on expiry with single-use token
  rotation.
- TrueNAS remains authoritative for the media services and active/archive
  libraries. Jellyfin and Audiobookshelf own user history; Sonarr/Radarr/Lidarr
  own managed media; Seerr/Lidarr/LazyLibrarian own request actions.
- The repository is authoritative for the portal code, ranking logic, design
  guide, icon source and project evidence. Aster on the Proxmox B60 may provide
  local explanations only; it is not an acquisition authority.

## Scope and exclusions

In scope are read-only signal collection, bounded external metadata adapters,
deterministic ranking, local explanations, source/rationale display, the
existing explicit request adapters, portal icon/manifest integration, source
detail links, the unified media search/discovery page, optional Trakt
personal-history integration, and the operator manual required for the
resulting user workflow.

Excluded are a second GPU, migration of Jellyfin/ARR services, changes to the
four-month active-to-archive lifecycle, automatic acquisition, whole-artist or
whole-author following, public ingress, weaker authentication, new firewall
trust, direct AI access to production credentials, and deletion or bulk rewrite
of media or library databases. Bazarr remains another task's authority and is
not changed here.

## Pre-start risk assessment and Stream A authorization

Jason explicitly requested that this document start as Stream A on 2026-10-07,
accepting the scope above and the following bounded risk envelope:

- **Confidentiality:** watch/listening history and provider credentials remain
  inside existing protected snapshots/secrets. The engine stores sanitized
  titles, IDs, source and timestamps, not raw tokens or private credentials.
- **Availability:** the initial work is shadowed and read-only. Portal refresh
  failure leaves the last snapshot available; the icon rollout is static and
  can be reverted without changing authentication or request services.
- **Integrity:** provider IDs, duplicate suppression and owned/archive checks
  fail closed. No AI-generated candidate can directly invoke a downloader.
- **Privacy:** external requests are limited to configured metadata sources;
  personal history is not sent to those providers. The B60 remains local.
- **Recovery:** retain the prior portal image/metadata and recommendation
  snapshot; revert only the focused portal/icon files if visual or runtime
  validation fails. Existing media, archive and service checkpoints remain
  untouched.
- **Expected changes:** code, tests, protected shadow configuration, private
  portal static metadata and documentation. No DNS, firewall, storage, NetBox
  or public-ingress change is expected.
- **Stop conditions:** stop for a new credential exposure, public route,
  authentication weakening, unverified backup/checkpoint, destructive library
  operation, materially different topology, or a provider identity that cannot
  be matched safely.

Stream A covers the enumerated project changes through graduation, including
unattended continuation after a session stop. Platform approval prompts and
the repository's immediate confirmation requirement for Forgejo pushes remain
mandatory.

## M6 refresh-quality maintenance — 2026-10-14

Jason reported that recommendations had remained substantially unchanged for
days and that Trakt TV was the only consistently useful source. Read-only live
discovery confirmed two independent causes: the refresher container remained
`running` while its recommendation, source-status, library and history files
stopped advancing on 2026-10-10; and the non-Trakt adapters repeatedly queried
fixed title/album seeds or the same leading library records.

Jason approved this focused Stream A maintenance on 2026-10-14. Its scope is:

- make refresh due-state persistent and freshness-aware so a running process
  cannot silently sleep past a stale snapshot;
- prefer recent Jellyfin viewing signals and rotate fallback library seeds for
  bounded TMDB per-title recommendations;
- retain sanitized author/subject signals from recent Audiobookshelf activity
  and use bounded Open Library author/subject discovery instead of only fixed
  title searches;
- use public, read-only ListenBrainz similar-artist discovery plus MusicBrainz
  release-group identity/artwork for music, with fixed exact-album seeds only
  as a fail-soft fallback;
- retain a bounded exposure ledger and cool down recently displayed candidates
  so a larger safe pool rotates instead of presenting the same page each day;
- add container freshness health plus Doctor evidence without duplicating
  existing service monitoring.

No acquisition automation, public ingress, new firewall rule, media mutation,
provider write, user-history export, new credential or broader service identity
is authorized. Trakt, Seerr, Lidarr and LazyLibrarian authority boundaries are
unchanged.

### M6 pre-start risk assessment

| Risk | Likelihood / impact | Control and accepted residual risk |
|---|---|---|
| A dynamic source returns irrelevant or malformed metadata | Medium / Low | Treat responses as untrusted, require stable provider identity and artwork, retain deterministic scoring and explicit request approval. Some weak candidates may still require rejection. |
| Extra provider reads cause latency or throttling | Medium / Low | Bound seeds/results, use timeouts, perform no bulk crawl and fail soft to the last-good snapshot. |
| Cooldown removes too many candidates | Low / Low | Bound ledger retention, fall back to least-recently shown safe candidates when the unseen pool is exhausted, and preserve per-media balancing. |
| Refresher repair interrupts the portal | Low / Low | Build and test locally, preserve the deployed image/configuration and snapshot, recreate only the refresher first, and keep the portal serving the last snapshot during refresh failure. |
| Sanitized taste signals disclose private history | Low / Medium | Store only title, media type, creator/genre/provider IDs and timestamps inside the existing protected state boundary; never log raw service responses or tokens. |
| New remote dependency is unavailable | Medium / Low | ListenBrainz and Open Library discovery are read-only, bounded and optional; source failures do not abort other adapters. |

The live snapshot is the recovery checkpoint. Rollback is the prior refresher
image/configuration plus the preserved snapshot; no database or media rollback
is needed. Abort on credential output, unexpected write traffic, public-route or
firewall change, loss of the last-good snapshot, ambiguous request identity, or
materially increased provider/network load. Tests use injected provider
fixtures; no synthetic acquisition request is required because M6 changes only
read-side recommendation generation.

## Architecture and data flow

```text
Jellyfin / Audiobookshelf / Calibre signals (read-only)
                    +
   Seerr/TMDb · optional Trakt · MusicBrainz/music discovery · Open Library/Books
                    |
          sanitized candidate adapters
                    |
       deterministic ranker + local B60 explanation
                    |
      private recommendations + unified discovery portal
                    |
 Seerr / Lidarr / LazyLibrarian only after explicit user approval
```

All containers remain on TrueNAS except the existing local B60 explanation
service on Proxmox. The page is reached through the existing private
Authentik/NPM route. The icon integration is static web metadata only.

## Privacy and security design

Readers use dedicated least-privilege API keys/tokens from protected secret
paths. Raw service responses and credentials are not written to the Git tree or
sent to the B60. Provider queries are bounded, cached and rate-limited. Logs
must contain source names, counts and failure classes, never tokens, passwords,
session cookies or personal history payloads. Personal watch history is sent
to Trakt only if Jason explicitly authorizes the Jellyfin/Trakt connection.
Request adapters remain the only write boundary.

## Milestones

- [x] **M0 — Shared visual contract.** Capture the recommendation UI tokens,
  update the shared guide, and add the new icon assets.
- [ ] **M0b — Portal icon integration.** Add the approved icon to the private
  webpage favicon/manifest/touch metadata and validate desktop/mobile loading;
  leave Authentik, NPM and request behavior unchanged. Code is prepared locally;
  live shadow rebuild and browser validation remain open.
- [ ] **M1 — Signal readers.** Read Jellyfin, Audiobookshelf, Calibre and
  existing music/recommendation state with least-privilege credentials and
  bounded retention.
- [ ] **M2 — Candidate adapters.** Add TMDb/Seerr, MusicBrainz plus the chosen
  music discovery provider, and Open Library/Google Books adapters with cache,
  rate limits and stale-source handling.
- [ ] **M2b — Personal taste and discovery.** Install/configure Jellyfin's
  official Trakt plugin only after Jason's account authorization; read personal
  Trakt recommendations and synchronized watch/rating signals without exposing
  credentials to the recommendation UI. Add source links behind artwork and
  complete the unified all-media search page using TMDb, Open Library and
  MusicBrainz. Trakt authorization, personal recommendations and source links
  are complete; the search page remains open.
- [ ] **M3 — Ranking and explanations.** Implement deterministic scoring,
  duplicate/owned/archive suppression, source evidence, and optional local B60
  explanations.
- [x] **M4 — Approval integration.** Reuse the page's one-button actions and
  route to Seerr/Lidarr/LazyLibrarian; preserve idempotency and audit records.
- [x] **M5 — Quality review and handover.** Compare a fixed sample against
  current Seerr-only output, verify all five domains, and publish a short user
  manual covering refresh, explanations and approval behavior.
- [x] **M6a — Scheduler and observability repair.** Make due-state recover from
  stale files/restarts, add freshness health, and prove failure preserves the
  last-good snapshot.
- [x] **M6b — Taste-driven source adapters.** Rotate recent-history video seeds,
  add Open Library author/subject discovery and add ListenBrainz similar-artist
  album discovery with bounded fallbacks.
- [x] **M6c — Exposure cooldown and deployment.** Persist a bounded exposure
  ledger, validate multi-day rotation with fixtures, deploy only the refresher,
  verify two production refreshes and update the operator handover.

## Risk controls and approvals

The initial implementation is read-only and shadowed beside the current portal.
API keys stay in the existing protected secrets boundary. Candidate fetches are
bounded and cached; external provider access is private and rate-limited. The
existing active-versus-archive lifecycle, TrueNAS ownership, A380 transcoding
and Proxmox B60 ownership split are unchanged.

Any new provider credential, production request adapter, deployment, firewall/
proxy change or remote Git push requires the relevant milestone approval and
the repository's immediate confirmation rule. Rollback is removal of the new
reader/adapter and restoration of the previous recommendation snapshot; no
media deletion or library rewrite is part of this mini-project.

## User-facing handover requirement

Before graduation, provide a short manual/training note that explains the
private URL, separate-browser passkey authentication, media-type filters,
source and rationale fields, refresh age, the exact effect of each request
button, stale/failed states, and the safe recovery path. Jason must review the
updated webpage and accept the workflow before the project can be marked
complete.

## Validation and evaluation

Validation must cover deterministic unit tests, stale-source and provider
failure behavior, owned/archive/duplicate/ambiguous suppression, snapshot
freshness, private authentication, request idempotency, and desktop/mobile
review of the portal including the final icon. Synthetic or explicitly selected
disposable candidates are required for any live request test; ordinary refresh
is read-only.

## Observability, backup and maintenance

The project extends the existing Docker health and HomeLab Doctor boundaries;
it does not introduce a parallel monitoring stack. Track last successful
refresh, candidate counts by media type/source, failed adapter class and
request-action result. Protect portal state, snapshots, adapter configuration,
and icon/source files through the existing configuration backup boundary. A
restore test must demonstrate that the portal can render the last-good snapshot
without a provider being online.

## Graduation criteria

Graduate only after the five domains have useful fixed-sample candidates, every
card explains its source and rationale, safe suppression and one-button action
tests pass, the approved icon is live on the private webpage, Doctor/backup
coverage is verified, and Jason completes the user walkthrough/manual review.
Known provider gaps or generic fallback behavior must remain explicitly listed
in the evidence log rather than being silently treated as complete.

## Integration impact checklist

- [x] **HomeLab Doctor:** snapshot freshness and failed-refresh
  checks before graduation.
- [x] **Monitoring/alerting:** reuse existing service/container health; add
  recommendation freshness/action failure visibility if the current checks do
  not cover it.
- [x] **Backup/recovery:** protect recommendation snapshots, state, provider
  configuration and icon source; prove the portal can return to its last-good
  snapshot.
- [x] **NetBox:** not applicable; no host, VM, LXC, address or service placement changed.
- [x] **Homepage:** existing tile and icon remain correct; no change required and
  no credentials are embedded.
- [x] **Auth/networking:** existing Authentik/NPM/private DNS reused; no ingress,
  authentication or firewall change.
- [ ] **Wiki/Aster mirror:** publish sanitized operator guidance and project
  status at graduation.

## Persistence and rollback

Each milestone ends with tests, an evidence-log entry and a focused local Git
commit. Remote synchronization remains pending until Jason confirms the exact
Forgejo push. Resume from the unchecked milestone and the latest commit; do
not repeat completed provider migrations or icon generation. A failed portal
icon rollout is reversed by restoring the prior static metadata and restarting
only the portal if needed.

## Evidence log

| Date | Action | Evidence | Result |
|---|---|---|---|
| 2026-10-07 | Stream A start requested | Jason explicitly asked to start this mini-project as Stream A | Scope, risks and exclusions recorded; project active |
| 2026-10-07 | Icon approved | Local asset revision `7c14030`; six-petal Aster compass with balanced colour-shifting media orbit | Accepted as the webpage icon deliverable; portal integration remains M0b |
| 2026-10-07 | Engine foundation present | Local commits `12692ab` and `0eab42d`; 41 unified-media tests passing | Deterministic ranking foundation ready for provider milestones |
| 2026-10-07 | M0b portal icon deployed | TrueNAS shadow portal rebuilt from a timestamped rollback copy; health returned `ok`, all four icon/manifest routes returned HTTP 200 with expected content types, and the page references the favicon and manifest. The refresher, LazyLibrarian and Audiobookshelf containers remained unchanged. | Backend deployment is validated; visual favicon/home-screen review in Jason's authenticated desktop and mobile browsers remains before marking M0b complete |
| 2026-10-07 | M1/M2 non-video adapters prepared locally | Added bounded, read-only Open Library ebook/audiobook and exact MusicBrainz release-group adapters; explicit seed configuration is empty by default, provider failures are isolated, and 47 tests pass. | Live shadow configuration and candidate-source review remain before deployment; no provider credentials or request behavior changed |
| 2026-10-07 | M1/M2 adapter deployment | Preserved a TrueNAS rollback copy, rebuilt the shared shadow image, and recreated only the refresher and portal. Health returned `ok`, both containers remained running, the 20-item Seerr snapshot stayed unchanged, and no non-video seed variables were present. | Adapter code is live but inactive by design; candidate population awaits explicit seed selection and later refresh validation |
| 2026-10-07 | Starter seeds selected | Jason delegated seed selection. Chosen bounded seeds avoid exact title matches in the sanitized library: ebooks `The Dispossessed`, `The Fifth Season`; audiobooks `The Murderbot Diaries`, `The Long Way to a Small Angry Planet`; music `Talk Talk — Spirit of Eden`, `Portishead — Dummy`, `Joni Mitchell — Blue`. | Local configuration is prepared; activation on the shadow refresher remains a separate deployment step |
| 2026-10-07 | Ranking balance defect found and fixed locally | Live adapter probes returned book, audiobook and music candidates, but the global 20-item cap allowed Seerr film/TV results to crowd them off the page. The deterministic ranker now uses stable round-robin selection across available media types; 48 tests pass. | Local fix awaits focused shadow deployment and multi-category snapshot validation |
| 2026-10-07 | Multi-category ranking deployed | Preserved a TrueNAS rollback copy, rebuilt and recreated only the snapshot refresher, and validated portal health. The live snapshot now contains 16 film/TV, 1 album, 1 ebook and 2 audiobook candidates; portal filters expose all five media types and actions remain disabled. | M1/M2 shadow validation passed; source quality and user review remain before enabling ordinary approval flow |
| 2026-10-07 | Recommendation cap expanded | Jason authorized increasing the bounded recommendation page from 20 to 40. The cap remains configurable and hard-limited at 40; balanced media-type selection and provider limits remain active. | Local configuration awaits deployment with the Open Library relevance fix |
| 2026-10-07 | Relevance fix and 40-item cap deployed | Preserved build/compose rollback copies, rebuilt and recreated only the refresher, and completed a refresh. The snapshot contains 29 safe candidates: 21 film/TV, 2 albums, 3 ebooks and 3 audiobooks. The portal exposes all five filters, health is `ok`, and actions remain disabled. | Expanded multi-category shadow validation passed; 29 is below the cap because provider limits and fail-closed suppression removed unsafe or duplicate candidates |
| 2026-10-07 | Non-video metadata/art enrichment prepared locally | Book candidates now retain author, first sentence, subjects and Open Library cover art; album candidates retain artist, description and Cover Art Archive front art where available; cards render creator fields and explicit artwork fallbacks. 49 tests pass. | Local UI/data change awaits focused shadow deployment and visual review |
| 2026-10-07 | Non-video metadata/art enrichment deployed | Preserved a rollback copy, rebuilt both shadow services, and completed a fresh refresh. The live snapshot contains 27 candidates; every displayed album, ebook and audiobook has creator metadata, synopsis/description and artwork, with zero missing-art records. Portal health remains `ok`. | Metadata/art deployment validated; visual review of the updated cards remains part of user handover |
| 2026-10-07 | Video source refactor prepared locally | Replaced generic Seerr discovery in the refresher with bounded TMDB per-title recommendations seeded from Radarr/Sonarr identities; Seerr remains only the request authority. Added regression coverage; 51 tests pass. | Local refactor awaits shadow deployment and live source validation |
| 2026-10-07 | TMDB fail-soft fix prepared locally | A live probe found one Seerr-proxied TMDB seed returning HTTP 500, which could abort the entire refresh. TMDB seed and TV-detail failures now skip only the affected item; 52 tests pass. | Local fix awaits redeployment and completion-time validation |
| 2026-10-07 | TMDB per-title source deployed and validated | Preserved a timestamped rollback build, rebuilt and recreated only `snapshot-refresh`, and waited for a completed refresh. The live snapshot now contains 10 candidates: 4 video items labeled `TMDB per-title recommendations`, 3 ebooks, 2 albums and 1 audiobook; the previous `Seerr discovery` label is absent. A failed provider seed was skipped without aborting the refresh, and the refresher remains running. | TMDB-backed video source is live in the shadow portal; generic Seerr discovery is removed from the recommendation path |
| 2026-10-07 | Trakt/discovery expansion started | Verified Jellyfin's official Trakt plugin is available through the Jellyfin plugin catalog for watch-state synchronization. Added the optional personal-history integration, unified search/discovery page, and source-link requirements to Stream A. The portal now links artwork and an explicit `Open source page` affordance to TMDB, Open Library or MusicBrainz; focused portal tests pass 17/17. | Trakt account authorization and live plugin configuration remain intentionally pending; unified search backend and Trakt adapter are the next implementation milestone |
| 2026-10-07 | Jellyfin Trakt setup verified; portal adapter prepared | TrueNAS contains the official Jellyfin Trakt plugin `33.0.0.0` and its configuration, verified without reading credential values. Added a separate fail-closed Trakt adapter requiring its own protected access-token/client-id paths; it is not coupled to Jellyfin's plugin XML. Adapter tests pass 2/2 and portal tests pass 17/17. | Jellyfin-side setup is complete; portal Trakt credentials and remote adapter deployment remain pending to preserve credential separation |
| 2026-10-07 | Trakt PKCE connection flow prepared locally | Added the private `/oauth/trakt/start` and callback flow using PKCE, exact registered HTTPS redirect URI, state validation and protected access/refresh-token writes. No client secret is required or stored. OAuth/adapter tests pass 3/3 and portal tests pass 17/17. | Remote deployment and the first account connection remain pending the Stream A deployment authorization boundary |
| 2026-10-07 | Trakt PKCE flow deployed to shadow | Stored the user-provided client ID in the protected shadow secret boundary, created empty protected token placeholders, rebuilt and recreated only the recommendation portal/refresher, and verified health plus a 302 authorization response with the exact registered callback. | Deployment is validated; final Trakt account approval in the user's normal browser is pending before live recommendation refresh |
| 2026-10-07 | Trakt device authorization fallback deployed | The mobile callback returned without OAuth query parameters. The pending state was preserved; the cause was isolated to the browser/proxy handoff. Added and deployed Trakt's device-code flow with a short activation code, protected polling, user-agent compatibility and no public callback exception. The device page returned HTTP 200 and both scoped containers remained running. | Device flow was subsequently approved and credentials were exchanged successfully |
| 2026-10-07 | Trakt personal recommendations activated | Jason approved the device code in his normal browser. The live Trakt API returned personalized movie and show recommendations; the snapshot contained six Trakt candidates, all with protected credentials and no token output. | Personal Trakt source is live; Jellyfin remains the optional history-sync authority |
| 2026-10-07 | Trakt reliability and artwork completed | Fixed JSON device-token polling, bind-mounted secret writes, automatic refresh-token rotation, and writable mounts limited to the Trakt access/refresh files. Trakt requests now use `extended=full` and preserve poster art, ratings, genres and source slugs. 56 unified-media tests pass; live validation showed six Trakt cards with HTTPS artwork. Local commit `33025e8` was pushed to Forgejo and verified on the GitHub mirror. | Trakt integration is operational; broader all-media search and final approval-flow graduation remain open |
| 2026-10-07 | Unified provider search deployed | Added the live `/api/search` backend and UI controls for TMDB/Seerr, Open Library and MusicBrainz. Results are bounded, read-only, include artwork/source links, and support media-type selection. Local commit `abb4b01` was pushed to Forgejo; the live endpoint was validated for film, ebook and album queries. | Search milestone is operational; search-result acquisition remains intentionally read-only |
| 2026-10-07 | M4 request actions authorized and enabled | Jason explicitly approved enabling the existing safety-checked request boundary. The shadow portal now exposes 16 safe recommendation actions and routes only snapshot candidates to Seerr, Lidarr or LazyLibrarian with idempotent state. A fabricated validation request was rejected with HTTP 409 and no downstream call. | One-button recommendation approval is live; individual requests still require Jason's click |
| 2026-10-07 | M5 quality review and handover update | The live snapshot contains 16 candidates across all five media types, with zero missing artwork and zero missing explanations. Provider search was validated for film, ebook and album queries; both shadow services are running and health is `ok`. Updated `docs/runbooks/Unified-Media-Recommendation-User-Guide.md` with search, Trakt, request and authentication training. | Technical quality gate passes; remaining close-out is Jason's visual review of the new search/actions UI and final project acceptance |
| 2026-10-07 | M5 user acceptance completed | Jason confirmed the page looks good and successfully tested requests for films, TV, books, audiobooks and music. Non-video routing now maps discovery identities to LazyLibrarian and Lidarr; confirmation text is `Request sent.`. | All five media domains and the user-facing handover are accepted; project is ready for close-out after the final Forgejo push |
| 2026-10-14 | M6 refresh-quality maintenance authorized | Jason reported static recommendations and approved the recommended focused Stream A repair. Live read-only evidence found both services running but the snapshot/status/library/history files last advanced on 2026-10-10; the last source status contained 9 Trakt, 1 TMDB, 33 Open Library and 4 MusicBrainz raw candidates, while the displayed 33 cards had no film or album cards. Code review confirmed fixed non-Trakt seeds and no exposure cooldown. | M6 active. Existing snapshot is the rollback point; no live state has yet changed. |
| 2026-10-14 | M6 implementation and first production pass | Added durable file-age scheduling, container freshness health, per-source last-good isolation, recent-history TMDB identities, Open Library author/subject readers, public ListenBrainz similar-artist discovery, valid MusicBrainz album identity and a bounded exposure ledger. Preserved build/config/snapshot checkpoint `20261014-m6-refresh-quality`, rebuilt and recreated only the refresher. The first pass completed despite an Audiobookshelf 401: 32 safe cards across all five media types, 16 new versus the stale snapshot, 2 ListenBrainz albums, 13 TMDB cards, zero missing art and zero unsafe records. | Passed. Audiobookshelf's 46 last-good library records were preserved; its absent/unauthorized history means books currently use the reviewed fallback pool plus display rotation until the reader credential is repaired separately. |
| 2026-10-14 | M6 independent second refresh | Triggered a second ordinary refresh through the deployed watcher. It completed in 20 seconds with a different snapshot hash and 31 cards: 1 album, 8 audiobooks, 8 ebooks, 6 films and 8 TV shows. Exposure generations prove 15 first-pass-only identities and 26 second-pass selections; portal health/root remained `ok`/HTTP 200, the refresher became Docker `healthy`, and no portal, LazyLibrarian, Audiobookshelf or Calibre-Web container was recreated. | M6 functional, failure-isolation, rotation and collateral-service gates passed. 73 local tests pass; local Docker Compose execution was unavailable, so the authoritative TrueNAS Compose validation and image build supplied that gate. |
| 2026-10-14 | M6 Doctor and efficiency review | Full HomeLab Doctor reported the unified-media Audiobookshelf/CWA health, portal state and recommendation freshness check healthy. The whole-lab run had 76 passes, 10 warnings and 3 failures, all outside this project (Aster approval identity, AI-PAM drift and an observability expected-job-count mismatch). The refresher has zero restarts, refresh completion was 47 seconds then 20 seconds, and provider calls remain bounded to six-hour/manual runs. The focused local M6 commit contains only M6 files/hunks; unrelated working-tree changes remain unstaged. | Intent and efficiency gate passed for M6. Existing unrelated Doctor findings were not changed. Audiobookshelf reader reauthorization remains a credential-maintenance follow-up; its 46 last-good library records are retained and book cards rotate through the safe fallback pool meanwhile. Forgejo synchronization remains pending the repository's separate immediate push confirmation. |

## Acceptance evidence

- A recommendation card can name its source and supporting signal.
- A fixed sample contains genuinely different, non-generic candidates across
  video, music, books and audiobooks.
- Owned, archived, duplicate and ambiguous items fail closed.
- Refresh timing and stale data are visible to the user.
- One-button approval reaches the correct authority without direct AI or
  download-client access.
- The page and icon pass desktop/mobile visual review, and a short operator
  manual is delivered with the production handover.
