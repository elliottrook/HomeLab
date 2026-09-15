# HomeLab Enhancement Project Portfolio

> Established: 2026-08-24
>
> The original HomeLab build is the stable production baseline. Each document
> linked here governs a separate enhancement and must not silently expand the
> scope of another project.

## Portfolio

| Project | Status | Project document | Supporting material |
|---|---|---|---|
| Authentik rollout | Active — Stream M; Milestone 2 complete (Homepage forward auth and Beszel native OIDC), Milestone 3 not started | [Authentik rollout](Authentik-Rollout.md) | [Authorization runbook](../08-Authorization.md), [service onboarding](../09-Service-Authorization-Onboarding.md) |
| Surveillance expansion | One-camera baseline complete; expansion proposed | [Surveillance expansion](Surveillance-Expansion.md) | [Surveillance runbook](../07-Surveillance.md) |
| NUT/UPS deployment | Handover ready | [NUT/UPS handover](../UPS-Power-Resilience-Claude-Handover.md) | Architecture, shutdown and recovery requirements are contained in the handover |
| TrueNAS DIY SAS expansion | Ready | [TrueNAS DIY SAS expansion](TrueNAS-DIY-SAS-Expansion.md) | Eight-bay backplane-free enclosure using two vacant x4 ports on the LSI SAS 9300-16i |
| Backup Synology decommission | Active — Milestones 1–3 passed; Milestone 4 (14-day observation, ends 2026-09-23) in progress | [Backup Synology decommission](Backup-Synology-Decommission.md) | Retires the 484 MB-RAM DS220j that starves under Hyper Backup, redeploys its disks into TrueNAS, and defers the Immich/family-cloud placement question to measurement. Successor to the item the backup redesign placed out of scope |
| Backup architecture redesign | Substantively complete; formal close held for the sibling decommission project | [Backup architecture redesign](Backup-Architecture-Redesign.md) | Replaces Hyper Backup's Synology-to-Synology path with Synology → rsync → TrueNAS/ZFS snapshots → dedicated rclone LXC → encrypted, versioned IDrive e2. All three legacy Hyper Backup jobs stopped; docs and inventory updated |
| Jellyfin library integrity automation | Proposed | [Jellyfin library integrity automation](Jellyfin-Library-Integrity-Automation.md) | Formalizes the orphan-track, featured-artist-scatter, missing-artwork and duplicate-album checks developed and validated by hand during the 2026-09-06/07 music library cleanup into a scheduled Sunday 3am job, plus a collection/playlist-count regression check across all Jellyfin libraries |
| Music playlist acquisition bridge | Prototype | [Music playlist acquisition bridge](Music-Playlist-Acquisition-Bridge.md) | Hybrid Cmdarr plus local export-file bridge: translate Spotify/Apple Music and generic playlist exports into conservative Lidarr album requests, then publish a complete duplicate playlist in Jellyfin after the media is indexed |
| Media sideload import | Active — Milestone 1 complete | [Media sideload import](Media-Sideload-Import.md) | Confirmed Radarr/Sonarr/Lidarr already file manually-acquired media correctly via Manual/Interactive Import and the `DownloadedXScan` commands, without an indexer or download client; defines a staging-inbox workflow to use that path deliberately instead of hand-placing files into the canonical roots. Staging folders created on TrueNAS at `/mnt/Media/data/inbox/{movies,tv,music}` |
| Aster mirror directory-first retrieval | Active — production live; graduation held on B60 backup-path correction | [Aster mirror directory-first retrieval](Aster-Mirror-Directory-Retrieval.md) | Directory-first retrieval is activated on the accepted 1.5.0 mirror with 60/60 behavior accounting, retained rollback and zero directory drift; the nightly all-guests backup deterministically reclaims the B60 through stopped rollback VM 105, so a persistent passthrough correction and backup-path proof remain before graduation |
| FreeCAD MCP connector | Active — Stream A; Milestone 1 (install and vet the connector) in progress | [FreeCAD MCP connector](FreeCAD-MCP-Connector.md) | Local, localhost-only MCP bridge (`neka-nat/freecad-mcp`) to let Claude — and, if locally supported, ChatGPT Desktop — drive FreeCAD directly for CAD work, starting with adapting the TrueNAS DIY SAS Expansion enclosure to fit a standard ATX PSU instead of SFX |
| News aggregator (MuckScraper) | Active — Stream A; Milestone 1 in progress, VLAN 70 placement confirmed. Outbound-firewall and bias-methodology decisions remain explicit Jason checkpoints regardless of stream | [News aggregator (MuckScraper)](News-Aggregator-MuckScraper.md) | Private RSS/Atom reader that clusters same-story coverage across outlets, attaches an automated (non-authoritative) bias/slant estimate, and summarizes via the existing `aster-llama` endpoint |

## Completed projects

| Project | Completed | Closing document | Outcome |
|---|---|---|---|
| Local AI | 2026-09-09 | [Local AI](completed%20projects/Local-AI.md) | Graduated Aster on the B60-backed llama.cpp path with measured capacity, bounded capabilities, source-aware recoverable knowledge, monitoring and rollback; retired live Hermes cloud OAuth state while retaining disabled local rollback paths |
| Aster Forgejo and NetBox read-only integration | 2026-09-09 | [Aster Forgejo and NetBox read-only integration](completed%20projects/Aster-Forgejo-NetBox-Read-Only.md) | Source-local least-privilege readers publish strict sanitized reports to Aster without giving its guest credentials, network reach or mutation authority |
| Aster ARR stack manager | 2026-09-09 | [Aster ARR stack manager](completed%20projects/Aster-Arr-Stack-Manager.md) | Reviewed six-service operational curriculum, sanitized live health/queue evidence, and one production-shaped graduated Radarr queue-record repair behind an execution-disabled, separately approved broker |
| Aster sysadmin second brain | 2026-09-01 | [Aster sysadmin second brain](completed%20projects/Aster-Sysadmin-Second-Brain.md) | Bounded read-only advisor with recoverable authority-aware memory and verified correctness, security and performance gates |
| Aster offline knowledge wiki and mirror | 2026-09-12 | [Aster offline knowledge wiki and mirror](completed%20projects/Aster-Offline-Knowledge-Wiki.md) | Private human-focused manuals/wiki corpus with daily allowlisted updates and a separate provenance-preserving, non-authoritative Aster analysis mirror |
| Aster production corpus expansion | 2026-09-13 | [Aster production corpus expansion](completed%20projects/Aster-Production-Corpus-Expansion.md) | 30 accepted version/model-matched sources, a healthy 1,796-entry deterministic mirror, repeated critical evaluation and retained Aster/wiki rollback generations |
| NetBox DCIM / rack & asset management | 2026-09-13 | [NetBox DCIM](completed%20projects/NetBox-DCIM.md) | Authoritative rack, device, guest and IPAM inventory with all 14 current Proxmox guests, health monitoring, and current local/off-host backup coverage |
| Media archive backup to Synology | 2026-09-13 | [Media archive backup to Synology](completed%20projects/Media-Archive-Synology-Backup.md) | Closed without implementation after Jason declined the proposed copy; records the accepted single-copy media boundary and confirms no account, share, job, credential or production change was created |
| Aster Home Assistant advisor | 2026-09-10 | [Aster Home Assistant advisor](completed%20projects/Aster-Home-Assistant.md) | Instance-specific reviewed curriculum and sanitized live health/version/backup evidence; 20/20 repeated graduation cases passed with no Home Assistant credential or mutation authority |
| Prometheus/Grafana observability | 2026-08-31 | [Prometheus/Grafana close-out](completed%20projects/Prometheus-Grafana-Observability.md) | Retained with four dashboards, seven bounded scrape jobs, two UPS alerts and tested recovery |
| Synology Drive family cloud | 2026-08-31 | [Synology Drive close-out](completed%20projects/Synology-Drive-Family-Cloud.md) | Private per-user storage, a shared Team Folder, on-demand macOS/iOS clients, bounded/revocable friend sharing via Cloudflare Access + Authentik, a proven backup/restore path and HomeLab Doctor monitoring — all validated for the pilot rollout. Rolling out clients to the rest of the family is intentionally deferred as a follow-on, not part of this completion. |
| Video library archiving | 2026-09-10 | [Video library archiving](completed%20projects/Video-Library-Archiving.md) | GPU-accelerated (Intel Arc A380 via the Jellyfin container) downconversion of aged current-library video into the archive roots, unattended Mon–Sat schedule live and proven with a real nobody-watching cron run, with config/state backup coverage closed out |
| Plex-to-Jellyfin media migration | 2026-09-01 | [Plex-to-Jellyfin close-out](completed%20projects/Plex-to-Jellyfin-Media-Migration.md) | Separate checksum-verified Archive Movies/TV libraries, one consolidated and re-tagged music root, 11 playlists and 165 movie collections migrated and validated (including recovery from a same-day Jellyfin data-loss incident), and Plex source media retired with an explicit risk-managed approval. Recurring backup coverage for Jellyfin's own application database is intentionally deferred, entangled with a separate, larger backup-topology effort. |

## Common project rules

The complete normative process is the
[HomeLab Project Creation Standard](../Project-Creation-Standard.md). It defines
the lab ethos, monitored and autonomous authorization streams, pre-start risk
assessment, required integration review, milestone Git workflow and resumable
execution. The concise rules below remain as portfolio-level reminders.

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
