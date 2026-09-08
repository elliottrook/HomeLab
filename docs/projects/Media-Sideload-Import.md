# Media Sideload Import

> Status: Active — Milestone 1 complete
>
> Project owner: Jason
>
> Last updated: 2026-09-07

## Purpose

Radarr, Sonarr and Lidarr already own the canonical library roots
(`/mnt/Media/data/media/movies`, `/mnt/Media/data/media/tv`,
`/mnt/Media/data/media/music`, fed by Prowlarr/SABnzbd — see
[04-Operations.md](../04-Operations.md)). That pipeline handles everything
acquired through it correctly: identified against TMDB/TVDB/MusicBrainz,
named to each app's convention, filed into the right folder, picked up by
Jellyfin.

Media that arrives a different way — a friend's drive, a personal rip, a
salvaged download, anything not routed through an indexer/download client —
has no equivalent path today. Dropped straight into the library roots by
hand, it bypasses identification and naming entirely and risks exactly the
kind of scattered/mis-tagged folder structure
[Jellyfin-Library-Integrity-Automation.md](Jellyfin-Library-Integrity-Automation.md)
was written to detect and clean up after the fact. This project defines a
**before-the-fact** path instead: get sideloaded files identified, tagged
and correctly filed on the way in, using the same metadata sources and
naming conventions the rest of the library already trusts.

## Investigation and decision

The original framing for this research assumed Sonarr/Radarr/Lidarr were
not deployed here. They are (confirmed via
[04-Operations.md:47](../04-Operations.md) and
[Video-Library-Archiving.md:49-54](Video-Library-Archiving.md)), so the real
question is narrower: can the existing stack file manually-acquired media
correctly, without an indexer or download client involved at all?

Verified 2026-09-07 directly against the Radarr, Sonarr and Lidarr GitHub
source (not just documentation, which was thin on this specific point):

| Mechanism | Confirmed in source | Behavior |
|---|---|---|
| `ManualImportController` (`GET`/`POST /api/v3/manualimport`) | Present in Radarr; Sonarr and Lidarr ship the equivalent controller/service pair | Scans an arbitrary folder, proposes a match against a movie/series/artist, and imports (move/copy/hardlink) using the app's own naming convention |
| `DownloadedMoviesScanCommand` / `DownloadedEpisodesScanCommand` / `DownloadedAlbumsScanCommand` | Present in all three repos' `MediaFiles/Commands` | The same filename-parsing match-and-import logic normally triggered by a completed download, but can be pointed at any folder on demand — no download client required |
| Interactive Import (UI) | Documented in the Servarr wiki's Radarr Library page | Human-reviewed version of the same match, for files the automatic parser can't place confidently |

Key constraint, confirmed the same way: Manual/Interactive Import only
**attaches a file to an item already added to that app's library** — it
cannot create a new library entry from an arbitrary file. So sideloading a
title Radarr/Sonarr/Lidarr has never heard of still needs a one-time
search-add step (TMDB/TVDB/MusicBrainz lookup) before any file for it can be
imported. That add can be unmonitored with no search triggered, so it never
touches the indexer/download-client side of the app.

| Option | Verdict |
|---|---|
| Radarr/Sonarr/Lidarr native Manual/Interactive Import + `DownloadedXScan` | **Recommended.** Already deployed, already the source of truth for every other file in these libraries, zero new dependency |
| Standalone tagger (FileBot, TinyMediaManager, beets) run directly against the library folders | Rejected — would create a second metadata/naming authority running in parallel with Radarr/Sonarr/Lidarr, the same "scatter" risk class the integrity-automation project was built to catch, for no capability the native import lacks |
| Drop files into the root folders by hand, let Jellyfin's own scanner sort it out | Rejected — this is the failure mode the Purpose section above describes; Jellyfin's scanner doesn't rename/relocate, it just reads whatever folder structure exists |

## Recommendation

Yes — the capability already exists in the deployed stack. No new tool is
required to do the identification/tagging/filing itself; what's missing is
a bounded **workflow** for using it deliberately for sideloaded content
instead of ad hoc by hand.

Proposed workflow:

1. Land sideloaded files in per-type staging folders **outside** the
   canonical roots, e.g. `/mnt/Media/data/inbox/{movies,tv,music}` — so
   nothing reaches `media/movies`, `media/tv` or `media/music` unvetted.
2. If the title isn't already in the relevant app's library, search-add it
   once (unmonitored, no search) so Manual Import has something to match
   against.
3. Well-named files (`Movie Name (Year)/Movie Name (Year).mkv`,
   `Show - S01E02 - Title.mkv`, tagged/foldered music): trigger
   `DownloadedMoviesScan` / `DownloadedEpisodesScan` / `DownloadedAlbumsScan`
   against the matching inbox subfolder. The app auto-matches by filename
   parsing and imports into the canonical root with correct naming — no
   human step, same mechanism as a normal completed download.
4. Ambiguous or poorly-named files: use the app's Interactive Import screen
   to pick the correct match by hand, same effort as fixing a bad
   auto-import from the normal pipeline.
5. Jellyfin's existing library scan picks the newly-filed media up exactly
   as it does anything Radarr/Sonarr/Lidarr acquire normally — no
   Jellyfin-side change needed.

This reuses TMDB/TVDB/MusicBrainz and each app's existing naming convention
rather than introducing a second one, so sideloaded media is
indistinguishable from normally-acquired media once filed — which is also
why [Jellyfin-Library-Integrity-Automation.md](Jellyfin-Library-Integrity-Automation.md)
needs no changes to cover it.

## Out of scope

- Content with no TMDB/TVDB/MusicBrainz entry at all (home movies,
  bootlegs, personal recordings). No *arr app can match this by design;
  if it's ever needed, it's a much smaller, separate problem (a manually
  organized folder Jellyfin reads as a mixed-content library), not this
  project.
- Any change to Prowlarr/SABnzbd or the existing acquisition pipeline —
  this project only adds a manual-entry path alongside it.
- Building a standalone tagging tool — evaluated and rejected above.

## Proposed milestones

1. **Confirm the inbox convention.** Create the three staging folders on
   TrueNAS; no import triggered yet. Gate: folders exist, correct
   ownership/permissions, empty.

   - [x] Created 2026-09-07: `/mnt/Media/data/inbox/{movies,tv,music}`,
     `root:apps`, mode `770`, matching the existing
     `media/{movies,tv,music}` roots exactly. Also mirrored
     `/mnt/Media/data`'s own POSIX ACL (`user:Jason:rwx`,
     `group:home_users:rwx`, `group:apps:rwx`) onto the inbox and each
     subfolder, as both an access and a default ACL, so Jason can write
     into them over the existing share and anything he drops in stays
     readable by the `apps` group the Radarr/Sonarr/Lidarr containers run
     as — without that, files landed with restrictive permissions the
     containers couldn't read. Verified via `getfacl` on all three.
     Confirmed empty. Gate passed.
2. **Supervised manual run.** Sideload one real movie, one real TV episode
   and one real album through the workflow above by hand, end to end,
   watching each step. Gate: all three land correctly named in the
   canonical roots and appear correctly in Jellyfin, with no root-folder
   file ever touched before Manual Import runs.
3. **Optional automation** (only if manual UI use proves too slow in
   practice): a small script, following the
   `/mnt/Media/data/tools/` precedent set by video-archiver and
   jellyfin-integrity, that triggers the scan command against any
   non-empty inbox subfolder on a schedule and reports anything left
   unmatched for human review. Not started until Milestone 2 shows it's
   actually needed.

## Sources reviewed

- Radarr GitHub source, 2026-09-07: [`ManualImportController.cs`](https://github.com/Radarr/Radarr/blob/develop/src/Radarr.Api.V3/ManualImport/ManualImportController.cs), [`DownloadedMoviesScanCommand.cs`](https://github.com/Radarr/Radarr/tree/develop/src/NzbDrone.Core/MediaFiles/Commands)
- Sonarr GitHub source, 2026-09-07: [`DownloadedEpisodesScanCommand.cs`](https://github.com/Sonarr/Sonarr/tree/develop/src/NzbDrone.Core/MediaFiles/Commands)
- Lidarr GitHub source, 2026-09-07: [`DownloadedAlbumsScanCommand.cs`](https://github.com/Lidarr/Lidarr/tree/develop/src/NzbDrone.Core/MediaFiles/Commands)
- [Servarr Wiki — Radarr Library (Manual/Interactive Import)](https://wiki.servarr.com/radarr/library)
- [Video Library Archiving project — precedent for the `/mnt/Media/data/tools/` install pattern](Video-Library-Archiving.md)
- [Jellyfin Library Integrity Automation — why this project must not introduce a second tagging authority](Jellyfin-Library-Integrity-Automation.md)
