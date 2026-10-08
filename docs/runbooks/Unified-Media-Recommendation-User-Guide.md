# Unified Media Recommendation User Guide

## What is available

The unified media project gives you one private recommendation view for:

- films and TV, requested through Seerr and then handled by Radarr/Sonarr;
- music albums, requested through Lidarr;
- ebooks and audiobooks, marked wanted through LazyLibrarian; and
- acquired music, which can be published into a Jellyfin playlist.

The recommendation service is advisory. It explains why an item was suggested,
but it never silently acquires media. Every acquisition is an explicit button
press and is recorded by the target service.

The current deployed video feed is populated from TMDB per-title
recommendations, seeded from existing Radarr/Sonarr identities. Seerr's generic
discovery feed is not used. Seerr remains the authenticated request authority
for films and TV; music, ebook and audiobook candidates come from their own
bounded providers.

The existing video lifecycle is unchanged. New high-quality film and TV stays
in the active Jellyfin libraries for the existing four-month period. The
existing Arc A380-backed archiver then creates the smaller archive copy and
moves it to the separate archive library. The archive is not treated as a new
request target merely because it is outside the active library.

## Opening the service

Use the private recommendation portal link from Homepage or the lab's private
DNS. When a direct link is provided, open it in Safari, Chrome or another
normal browser on your device:

1. Open the portal URL.
2. Complete Authentik passkey authentication in that separate browser.
3. Return to the portal after the redirect.

The embedded Codex browser cannot complete this passkey flow reliably. If it
stops at the Authentik passwordless page, that is an authentication limitation,
not evidence that the portal is broken.

The portal uses the approved Unified Media Recommendations icon as its browser
favicon and as its iPhone/iPad home-screen icon. If you add the page to your
home screen, use the browser's Share menu after the authenticated page has
loaded. A stale icon can be cached by the browser; reload the page or remove
and re-add the shortcut before reporting a branding problem.

If the page is read-only or action buttons are disabled, do not work around it
by retrying requests. This is the fail-closed behavior used for maintenance,
stale data, missing credentials or a failed dependency.

## Normal recommendation workflow

1. Open the recommendation list and filter by the category you want.
2. Read the explanation and check the ownership/status labels.
3. Reject anything you already own, have archived, do not want, or that is
   ambiguous.
4. Press the single action button on the exact item you want.
5. Wait for the result. A successful response says **Request sent.** This means
   the owning service accepted the request; it does not mean the download has
   finished.
6. Do not press the button repeatedly while the request is processing. Duplicate
   presses are suppressed, but waiting is clearer and safer.
7. Follow progress in the authority's normal UI: Seerr for films/TV, Lidarr
   for music and LazyLibrarian for books.

The current interface has an **All** filter plus one filter for each category
that currently has candidates: **Film**, **TV**, **Music album**, **Ebook** and
**Audiobook**. The refresh is bounded at up to 40 safe candidates, so the page
may contain fewer than 40 when provider limits, duplicates or owned/archive
suppression apply. Each card shows a poster when available, synopsis, year,
rating, genres, source, why it was selected and whether it is ready for
approval. This is a deliberate improvement over the original diagnostic page.

## Searching for something specific

The search window is now a provider-backed, read-only media search rather than
just a filter for the recommendation cards:

1. Enter a title, author, artist or keyword.
2. Choose **All media**, **Films**, **TV**, **Books**, **Audiobooks** or
   **Music**.
3. Press **Search all media** or press Return.
4. Open the artwork or **Open source** link for a longer synopsis or provider
   page.

Search results are supplied by TMDB through Seerr, Open Library and
MusicBrainz. Search itself never acquires anything. For a supported result,
press its **Request this …** button and wait for **Request sent.** The portal
revalidates the selected provider identity before sending it to Seerr,
Lidarr or LazyLibrarian. TV search results intentionally remain read-only
until a season-aware request flow is available; use Recommendations for TV.

## Trakt recommendations

Personal Trakt recommendations appear with the source label **Trakt personal
recommendations**. They are based on the connected Trakt profile, not generic
Seerr discovery. Trakt credentials remain in the protected TrueNAS secret
boundary and are not shown in the portal or sent to the B60. The service
automatically rotates Trakt's single-use refresh token when an access token
expires. If Trakt is ever disconnected, use the private connection page and
the normal browser device-approval flow; do not paste tokens into chat.

## Category-specific behavior

### Films and TV

Film requests go to Seerr and are handed to Radarr. TV requests go to Seerr
with an explicit validated season list and are handed to Sonarr. The portal
does not guess missing TV seasons. If a TV card has no valid season selection,
the action remains unavailable until the recommendation snapshot is refreshed.

### Music

Music recommendations are album recommendations, identified by the exact
artist and album pair. The action requests that album through Lidarr. Whole
artist following is intentionally disabled, so one album cannot silently turn
into an artist-wide acquisition queue. When the album is indexed by Jellyfin,
the playlist bridge may publish it into the appropriate Jellyfin playlist.

### Ebooks and audiobooks

Ebook and audiobook actions are separate. The portal sends the correct book
identity to LazyLibrarian and queues the requested format. LazyLibrarian is the
book automation authority; Calibre-Web Automated is the ebook reading/catalog
surface, and Audiobookshelf is the audiobook reading/listening surface.

A successful book response means the title is wanted or queued. It does not
guarantee that a provider has supplied a file yet. If a title remains Wanted,
check the owning service and provider status rather than submitting the same
title repeatedly.

## Status meanings and safe responses

- **Accepted/requested** — the authority accepted it; acquisition is still
  pending.
- **Already owned** — no action is needed; check the active or archive library.
- **Archived** — it exists in the long-term archive; do not request a duplicate
  without a deliberate upgrade decision.
- **Ambiguous** — identity was not safely resolved; leave it untouched.
- **Stale** — refresh the recommendation snapshot before acting.
- **Read-only/disabled** — a dependency or safety gate is unavailable; wait or
  report it rather than bypassing the gate.
- **Failed** — record the message and check the target authority. Retry only
  after confirming the first attempt was not accepted.

## Small operator training note

The only recurring manual decisions are: authenticate with your passkey in a
separate browser, choose which recommendation you actually want, and press its
one action button. The system does not decide your taste or auto-request on
your behalf. For an unfamiliar result, use the target service's search/request
page to inspect it, but keep the portal as the approval point.

For an unexpected acquisition, stop submitting new requests and check Seerr,
Radarr/Sonarr, Lidarr or LazyLibrarian for the audit trail. For an unexpected
archive move, check the existing video-archiver status; do not move files by
hand. Report the service and timestamp so the relevant runbook can be followed.

## Recovery and ownership

The recommendation portal is not the source of truth for media state. The
owning services remain the recovery authorities, and the active/archive video
pipeline remains under its existing project and backup boundaries. Configuration
and recommendation state are protected by the lab backup/checkpoint process.

The A380 in TrueNAS remains the media-transcoding and video-archiving GPU. The
Proxmox Intel B60 remains the local inference GPU. The recommendation workflow
does not require a second transcoding GPU or move the media library off
TrueNAS.
