# HomeLab Enhancement Project Portfolio

> Established: 2026-08-24
>
> The original HomeLab build is the stable production baseline. Each document
> linked here governs a separate enhancement and must not silently expand the
> scope of another project.

## Portfolio

| Project | Status | Project document | Supporting material |
|---|---|---|---|
| Authentik rollout | Foundation proven; staged rollout proposed | [Authentik rollout](Authentik-Rollout.md) | [Authorization runbook](../08-Authorization.md), [service onboarding](../09-Service-Authorization-Onboarding.md) |
| Surveillance expansion | One-camera baseline complete; expansion proposed | [Surveillance expansion](Surveillance-Expansion.md) | [Surveillance runbook](../07-Surveillance.md) |
| NUT/UPS deployment | Handover ready | [NUT/UPS handover](../UPS-Power-Resilience-Claude-Handover.md) | Architecture, shutdown and recovery requirements are contained in the handover |
| TrueNAS DIY SAS expansion | Ready | [TrueNAS DIY SAS expansion](TrueNAS-DIY-SAS-Expansion.md) | Eight-bay backplane-free enclosure using two vacant x4 ports on the LSI SAS 9300-16i |
| NetBox DCIM / rack & asset management | Active | [NetBox DCIM](NetBox-DCIM.md) | Rack walk-through, VLAN/IPAM, and full guest/device inventory complete. The one previously blocked item (a live Backup Synology DSM task edit) is now moot — that unit's pull role was fully replaced by the TrueNAS backup hub, which already covers the guest that item existed to add |
| Aster sysadmin second brain | Graduated | [Aster sysadmin second brain](Aster-Sysadmin-Second-Brain.md) | Bounded read-only advisor with recoverable authority-aware memory and verified correctness, security and performance gates |
| Backup Synology decommission | Active — Milestones 1–3 passed; Milestone 4 (14-day observation, ends 2026-09-23) in progress | [Backup Synology decommission](Backup-Synology-Decommission.md) | Retires the 484 MB-RAM DS220j that starves under Hyper Backup, redeploys its disks into TrueNAS, and defers the Immich/family-cloud placement question to measurement. Successor to the item the backup redesign placed out of scope |
| Backup architecture redesign | Substantively complete; formal close held for the sibling decommission project | [Backup architecture redesign](Backup-Architecture-Redesign.md) | Replaces Hyper Backup's Synology-to-Synology path with Synology → rsync → TrueNAS/ZFS snapshots → dedicated rclone LXC → encrypted, versioned IDrive e2. All three legacy Hyper Backup jobs stopped; docs and inventory updated |
| Media archive backup to Synology | Deferred — declined 2026-09-10, not proceeding | [Media archive backup to Synology](Media-Archive-Synology-Backup.md) | Scoped backing up TrueNAS's `archive-movies`/`archive-tv` (5.6 TB) to `gowest`; Jason decided not to back up the media archive at all. Kept as a scoping record in case revisited |
| Jellyfin library integrity automation | Proposed | [Jellyfin library integrity automation](Jellyfin-Library-Integrity-Automation.md) | Formalizes the orphan-track, featured-artist-scatter, missing-artwork and duplicate-album checks developed and validated by hand during the 2026-09-06/07 music library cleanup into a scheduled Sunday 3am job, plus a collection/playlist-count regression check across all Jellyfin libraries |
| Music playlist acquisition bridge | Prototype | [Music playlist acquisition bridge](Music-Playlist-Acquisition-Bridge.md) | Hybrid Cmdarr plus local export-file bridge: translate Spotify/Apple Music and generic playlist exports into conservative Lidarr album requests, then publish a complete duplicate playlist in Jellyfin after the media is indexed |
| Media sideload import | Active — Milestone 1 complete | [Media sideload import](Media-Sideload-Import.md) | Confirmed Radarr/Sonarr/Lidarr already file manually-acquired media correctly via Manual/Interactive Import and the `DownloadedXScan` commands, without an indexer or download client; defines a staging-inbox workflow to use that path deliberately instead of hand-placing files into the canonical roots. Staging folders created on TrueNAS at `/mnt/Media/data/inbox/{movies,tv,music}` |

## Completed projects

| Project | Completed | Closing document | Outcome |
|---|---|---|---|
| Local AI | 2026-09-09 | [Local AI](Local-AI.md) | Graduated Aster on the B60-backed llama.cpp path with measured capacity, bounded capabilities, source-aware recoverable knowledge, monitoring and rollback; retired live Hermes cloud OAuth state while retaining disabled local rollback paths |
| Aster Forgejo and NetBox read-only integration | 2026-09-09 | [Aster Forgejo and NetBox read-only integration](Aster-Forgejo-NetBox-Read-Only.md) | Source-local least-privilege readers publish strict sanitized reports to Aster without giving its guest credentials, network reach or mutation authority |
| Aster ARR stack manager | 2026-09-09 | [Aster ARR stack manager](Aster-Arr-Stack-Manager.md) | Reviewed six-service operational curriculum, sanitized live health/queue evidence, and one production-shaped graduated Radarr queue-record repair behind an execution-disabled, separately approved broker |
| Prometheus/Grafana observability | 2026-08-31 | [Prometheus/Grafana close-out](completed%20projects/Prometheus-Grafana-Observability.md) | Retained with four dashboards, seven bounded scrape jobs, two UPS alerts and tested recovery |
| Synology Drive family cloud | 2026-08-31 | [Synology Drive close-out](completed%20projects/Synology-Drive-Family-Cloud.md) | Private per-user storage, a shared Team Folder, on-demand macOS/iOS clients, bounded/revocable friend sharing via Cloudflare Access + Authentik, a proven backup/restore path and HomeLab Doctor monitoring — all validated for the pilot rollout. Rolling out clients to the rest of the family is intentionally deferred as a follow-on, not part of this completion. |
| Video library archiving | 2026-09-10 | [Video library archiving](Video-Library-Archiving.md) | GPU-accelerated (Intel Arc A380 via the Jellyfin container) downconversion of aged current-library video into the archive roots, unattended Mon–Sat schedule live and proven with a real nobody-watching cron run, config/state backup coverage closed out. Not physically relocated into `completed projects/` — left in place to avoid updating its several cross-references |
| Plex-to-Jellyfin media migration | 2026-09-01 | [Plex-to-Jellyfin close-out](completed%20projects/Plex-to-Jellyfin-Media-Migration.md) | Separate checksum-verified Archive Movies/TV libraries, one consolidated and re-tagged music root, 11 playlists and 165 movie collections migrated and validated (including recovery from a same-day Jellyfin data-loss incident), and Plex source media retired with an explicit risk-managed approval. Recurring backup coverage for Jellyfin's own application database is intentionally deferred, entangled with a separate, larger backup-topology effort. |

## Common project rules

- A checkbox is completed only after implementation, validation and relevant
  documentation or backup work are finished.
- Record evidence beside the completed item or in the project's evidence log.
- Take a current recovery checkpoint before changes that could interrupt a
  production service.
- Keep credentials, tokens, private keys and sensitive configuration outside
  Git. Record only their storage location and recovery method.
- Use existing VLANs and authority boundaries unless a project explicitly
  approves an architectural change.
- Do not weaken the production firewall or expose a service publicly merely to
  simplify a project.
- Complete one bounded milestone at a time and retain a tested rollback path.
- A project becomes operational only when its completion gate passes; partial
  work remains a pilot or proposed enhancement.

## Status vocabulary

- **Proposed** — requirements exist, but implementation is not authorized.
- **Ready** — prerequisites are known and the first milestone may begin.
- **Active** — implementation work is underway.
- **Pilot** — bounded functionality is operating but the completion gate has
  not passed.
- **Complete** — every required milestone and the completion gate have passed.
- **Deferred** — intentionally paused without being abandoned.

## Relationship to the initial-build record

[`PROJECTS.md`](../../PROJECTS.md) remains the historical completion record for
the initial HomeLab build and contains only its final reliability follow-up and
small deferred cleanup items. Major enhancement execution is tracked here.
