# Unified Recommendation Engine — mini-project

> Status: Ready — Stream A, design-system phase started
>
> Owner: Jason
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

## Milestones

- [x] **M0 — Shared visual contract.** Capture the recommendation UI tokens,
  update the shared guide, and add the new icon assets.
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
