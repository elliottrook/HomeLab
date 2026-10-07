# Unified Recommendation Engine — mini-project

> Status: Active — Stream A
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

## Purpose

Build the recommendation engine behind the existing private Unified Media
Recommendations page. It will provide one explainable, one-stop queue for
films, TV, music, ebooks and audiobooks while leaving acquisition authority in
Seerr, Lidarr and LazyLibrarian. The page remains the approval surface; the
engine supplies better candidates, evidence and freshness.

## Recommendation contract

- Video candidates combine Jellyfin history/library signals with TMDb/Seerr
  discovery; Seerr remains the request authority.
- Music candidates use Jellyfin listening signals plus MusicBrainz identity and
  a configured discovery source such as ListenBrainz or Last.fm; Lidarr remains
  the request authority.
- Ebook and audiobook candidates use Audiobookshelf/Calibre signals plus
  Open Library or Google Books metadata; LazyLibrarian remains the wanted-item
  authority.
- The B60 may produce local explanations and embeddings, but not direct access
  to download clients or production credentials. Core ranking is deterministic
  and auditable.
- Every card records source, rationale, candidate age and exact downstream
  action. No automatic acquisition, artist following, author following or
  series following.

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
- The current snapshot is refreshed by the shadow refresher and currently has
  real Seerr discovery candidates for film and TV, with the deterministic
  ranking foundation now in Git. Music, ebook and audiobook provider feeds
  remain to be connected.
- TrueNAS remains authoritative for the media services and active/archive
  libraries. Jellyfin and Audiobookshelf own user history; Sonarr/Radarr/Lidarr
  own managed media; Seerr/Lidarr/LazyLibrarian own request actions.
- The repository is authoritative for the portal code, ranking logic, design
  guide, icon source and project evidence. Aster on the Proxmox B60 may provide
  local explanations only; it is not an acquisition authority.

## Scope and exclusions

In scope are read-only signal collection, bounded external metadata adapters,
deterministic ranking, local explanations, source/rationale display, the
existing explicit request adapters, portal icon/manifest integration, and the
operator manual required for the resulting user workflow.

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

## Architecture and data flow

```text
Jellyfin / Audiobookshelf / Calibre signals (read-only)
                    +
   Seerr/TMDb · MusicBrainz/music discovery · Open Library/Books
                    |
          sanitized candidate adapters
                    |
       deterministic ranker + local B60 explanation
                    |
      private recommendation portal and audit state
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
session cookies or personal history payloads. Request adapters remain the only
write boundary.

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
- [ ] **M3 — Ranking and explanations.** Implement deterministic scoring,
  duplicate/owned/archive suppression, source evidence, and optional local B60
  explanations.
- [ ] **M4 — Approval integration.** Reuse the page's one-button actions and
  route to Seerr/Lidarr/LazyLibrarian; preserve idempotency and audit records.
- [ ] **M5 — Quality review and handover.** Compare a fixed sample against
  current Seerr-only output, verify all five domains, and publish a short user
  manual covering refresh, explanations and approval behavior.

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

- [ ] **HomeLab Doctor:** add or confirm snapshot freshness and failed-refresh
  checks before graduation.
- [ ] **Monitoring/alerting:** reuse existing service/container health; add
  recommendation freshness/action failure visibility if the current checks do
  not cover it.
- [ ] **Backup/recovery:** protect recommendation snapshots, state, provider
  configuration and icon source; prove the portal can return to its last-good
  snapshot.
- [ ] **NetBox:** no new host, VM, LXC or address; no change expected.
- [ ] **Homepage:** update only the existing private tile/icon if it consumes
  the recommendation portal asset; no credentials in the tile.
- [ ] **Auth/networking:** reuse Authentik/NPM/private DNS; no new ingress or
  authentication change.
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
