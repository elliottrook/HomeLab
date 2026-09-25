# HomeLab Enhancement Project Portfolio

> Established: 2026-08-24
>
> The original HomeLab build is the stable production baseline. Each document
> linked here governs a separate enhancement and must not silently expand the
> scope of another project.

## Portfolio

| Project | Status | Project document | Supporting material |
|---|---|---|---|
| Aster Adaptive Computing — Foundation and First Evidence Loop | Active — Stream A; M0 verified, M1 local security regressions started; no production changes | [Implementation project](AI%20Projects/Aster-Adaptive-Computing.md) | [AI Projects index and assessment](AI%20Projects/README.md); replaces five archived standalone assistant plans; retains AI-PAM and operational dependencies |
| B60 inference engineering | Proposed — Stream M | [B60 inference engineering](B60-Inference-Engineering.md) | Scientific optimization of the fixed T5810/B60 Aster inference path; read-only state reconciled, fresh control/harness and exact rollback inventory pending before any operational experiment |
| MacBook administration layer | Active — Stream A; M0-M3 closed (baseline, toolkit, independent SSH identity/enrollment, Doctor parity); M4 (recovery, integration, graduation) in progress | [MacBook administration layer](MacBook-Administration-Layer.md) | Independent internal toolkit, credentials and recovery; mini-only scheduled automation; no SSD migration |
| Authentik rollout | Active — Stream A; six private browser apps, Audiobookshelf, Calibre and Proxmox accepted; 13 earlier providers normalized to passkeys; admin-access/capability holds and final logout/recovery/client gates remain; Jellyfin/Seerr deferred | [Authentik rollout](Authentik-Rollout.md) | [Authorization runbook](../08-Authorization.md), [service onboarding](../09-Service-Authorization-Onboarding.md), [single-login recovery](../runbooks/Authentik-Single-Login.md) |
| Surveillance expansion | One-camera baseline complete; expansion proposed | [Surveillance expansion](Surveillance-Expansion.md) | [Surveillance runbook](../07-Surveillance.md) |
| NUT/UPS deployment | Handover ready | [NUT/UPS handover](../handovers/UPS-Power-Resilience-Claude-Handover.md) | Architecture, shutdown and recovery requirements are contained in the handover |
| TrueNAS DIY SAS expansion | Ready | [TrueNAS DIY SAS expansion](TrueNAS-DIY-SAS-Expansion.md) | Eight-bay backplane-free enclosure using two vacant x4 ports on the LSI SAS 9300-16i |
| Music playlist acquisition bridge | Prototype | [Music playlist acquisition bridge](Music-Playlist-Acquisition-Bridge.md) | Hybrid Cmdarr plus local export-file bridge: translate Spotify/Apple Music and generic playlist exports into conservative Lidarr album requests, then publish a complete duplicate playlist in Jellyfin after the media is indexed |
| Media sideload import | Active — Milestone 1 complete | [Media sideload import](Media-Sideload-Import.md) | Confirmed Radarr/Sonarr/Lidarr already file manually-acquired media correctly via Manual/Interactive Import and the `DownloadedXScan` commands, without an indexer or download client; defines a staging-inbox workflow to use that path deliberately instead of hand-placing files into the canonical roots. Staging folders created on TrueNAS at `/mnt/Media/data/inbox/{movies,tv,music}` |
| Recommendarr watch recommendations | Proposed | [Recommendarr watch recommendations](Recommendarr-Watch-Recommendations.md) | Source-local sanitized reader over Jellyfin/Sonarr/Radarr feeding read-only, no-auto-add recommendations via `aster-llama`; open decision is adopting the third-party open-source Recommendarr project versus building bespoke on the lab's least-privilege reader pattern |
| Cantinarr evaluation and controlled pilot | Proposed — Stream M | [Cantinarr evaluation and controlled pilot](Cantinarr-Evaluation-Pilot.md) | Reversible isolated evaluation beside Seerr, with no initial production credentials, media mounts, remediation, AI or MCP authority; later gates compare household requests, Import Doctor, local AI and a restricted read/request MCP surface without weakening Aster's existing ARR broker boundary |
| Local subtitle generation/translation | Proposed | [Local subtitle generation/translation](Subtitle-Generation-Translation.md) | Whisper pipeline writing additive `.srt` sidecars to close the measured TV-subtitle gap and restore non-English tracks Video-Library-Archiving strips; open decision is which GPU/host runs it without contending with existing transcode/inference workloads |
| Video duplicate/quality-upgrade finder | Proposed | [Video duplicate/quality-upgrade finder](Video-Duplicate-Quality-Finder.md) | Reframes Jellyfin-Library-Integrity-Automation's music-only duplicate detector around a distinct movie/TV problem (upgradable low-quality copies, not accidental duplicates); report-only, never auto-deletes, and gates on a Milestone 0/1 buy-in and measurement pass given thin evidence |
| Auto-written Plex/Jellyfin collection descriptions | Proposed | [Auto-written Plex/Jellyfin collection descriptions](Auto-Collection-Descriptions.md) | Reader/generator/writer over the 165 migrated Jellyfin collections via `aster-llama`, human-reviewed dry-run plus pre-write backup given this exact metadata was twice destroyed by a Jellyfin scheduled-task bug |
| Music recommender | Proposed | [Music recommender](Music-Recommender.md) | Read-only Jellyfin/Lidarr library-and-play-history reader producing a periodic acquisition-candidate report, never auto-acquiring; open decision is whether Jellyfin's deployed instance actually exposes usable play-history data |
| Book recommender | Proposed | [Book recommender](Book-Recommender.md) | Starts audiobooks-only via Audiobookshelf's working REST API; e-book side is explicitly blocked pending Jason's choice between deploying Kavita/calibre-web or reading Calibre's `metadata.db` directly, since neither Kavita nor a Calibre API exists in this lab today |
| AI Privileged Access Management (AI-PAM) / credential broker | Active — Stream A; M0–M5 and M6 Green Forgejo read complete | [AI-PAM and credential broker](homelab-credential-broker.md) | Recoverable OpenBao, Unix-only capability/approval services, mobile management and mandatory Probation are live; broker-private Forgejo MCP read is proven with root revoked, and the next gate is a separately approved Yellow safe-branch write |
| Aster Lab Doctor and backup execution | Active — Stream A; staged deployment and validation | [Aster lab operations](Aster-Lab-Operations.md) | Bounded on-request and task-required diagnostics/backups, durable job status, target allowlists and verified recovery coverage; production access not enabled |
| Aster Companion ARR execution | Proposed — deferred follow-up, production disabled | [ARR execution follow-up](Aster-Companion-ARR-Execution-Followup.md) | Preserve separate operator approval and wait for a natural eligible candidate before live UI execution testing |
| Infrastructure resilience and operations hardening | Approved — Stream A; always-on ops console (M-O) can start now; second-node hardware (H1) postponed; mobile GUI approach (D7) pending | [Infrastructure resilience and operations hardening](Infrastructure-Resilience-Hardening.md) | From the 2026-09-23 health check: one small second node hosting Proxmox Backup Server, standby DNS/NPM and the ops runner (scheduled jobs off the Mac), pinned images with an update notifier, Doctor drift checks, failure push alerts, host swappiness and CI lint |
| Archive large-file compaction | Active — pilot passed (SSIM 0.976–0.994); nightly 02:00–07:30 schedule live | [Archive large-file compaction](Archive-Large-File-Compaction.md) | Re-encodes the 477 archive files over 2.5 GB (2.41 TB) in place on the Arc A380: HEVC, never upscaled, capped at 1080p with aspect kept, HDR10 retained, ≤2.3 GB, same path for Jellyfin identity, 7-day ZFS rollback snapshots; ~1.68 TB expected saving |

## Completed projects

| Project | Completed | Closing document | Outcome |
|---|---|---|---|
| Aster Companion App | 2026-09-23 | [Aster Companion App](completed%20projects/Aster-Companion-App.md) | Mac/iPhone voice and notifications accepted; native authentication persistence repaired; permission regressions and notification recovery verified; bounded operational exceptions recorded, live ARR execution deferred |
| Jellyfin library integrity automation | 2026-09-23 | [Jellyfin library integrity automation](completed%20projects/Jellyfin-Library-Integrity-Automation.md) | Three clean Wednesday runs verified; bounded corrections, monitoring and local/off-site config recovery proven; ambiguous comparisons remain report-only |
| Backup architecture redesign | 2026-09-22 | [Backup architecture redesign](completed%20projects/Backup-Architecture-Redesign.md) | Current local/HA/off-site backups, fresh snapshot/crypt recovery match, monitoring and retired-job cleanup verified; capacity expansion remains separate |
| Backup Synology decommission | 2026-09-22 | [Backup Synology decommission](completed%20projects/Backup-Synology-Decommission.md) | Retired DS220j with early observation closeout, inactive NetBox asset and UPS/monitoring cleanup; disks removed but reuse/data disposition explicitly transferred to follow-ups |
| Document OCR + summarization | 2026-09-23 | [Paperless deployment close-out](completed%20projects/Document-OCR-Summarization.md) | Private HTTPS UI and dashboard tile, local OCR/summaries, service-only offsite export and verified local/TrueNAS restore. Personal login and first real-document quality review remain explicit operator follow-ups. |
| Aster mirror directory-first retrieval | 2026-09-15 | [Aster mirror directory-first retrieval](completed%20projects/Aster-Mirror-Directory-Retrieval.md) | Activated deterministic source-first routing on the 1,796-entry mirror with accepted 60/60 production behavior, rollback and zero drift; eliminated recurring B60 loss by removing rollback VM 105's persistent GPU mapping and proving the real backup trigger leaves all samples on `xe` |
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
| News aggregator (MuckScraper) | 2026-09-15 | [News aggregator (MuckScraper)](completed%20projects/News-Aggregator-MuckScraper.md) | Private RSS/Atom reader on LXC 114 (VLAN 70) clustering same-story coverage across 10 real feeds (AP News assessed and dropped — no source-published feed), attaching a named-source (AllSides) bias rating with an honest unverified-this-session caveat surfaced via a live UI tooltip, and summarizing via the existing `aster-llama` endpoint on a dedicated least-privilege key. HomeLab Doctor, NetBox, Homepage, firewall/DNS and checksum-verified local + off-host backup coverage all closed |
| News aggregator Phase 2 — digest, sections and rebrand | 2026-09-15 | [News aggregator Phase 2](completed%20projects/News-Aggregator-Digest-and-Sections.md) | Rebranded "Your News", with a twice-daily digest of multi-outlet stories only (abridged summary plus deviation notes via the existing `aster-llama` key), a `/settings` page queuing new source/category requests for verification, and a full dark-theme redesign. Fixed three real production bugs found via live testing along the way: HTML-polluted summaries, duplicate cards from cross-posted stories (whose first fix attempt was itself a caught-and-reverted false-positive regression), and an over-broad digest scope |
| News aggregator Phase 3 — audio digest | 2026-09-15 | [News aggregator Phase 3](completed%20projects/News-Aggregator-Audio-Digest.md) | Local Piper TTS narrates the latest digest run as a single MP3 briefing on `/digest`, chained into the existing twice-daily timer; closes a real HomeLab Doctor gap (a silently-stale audio file) and gives Jason a real trial of Piper ahead of a planned Home Assistant project. Confirmed working by Jason on desktop and his own iPhone after two real-screenshot-driven mobile rendering fixes |

## Closed projects — partial success or abandoned

| Project | Closed | Closing document | Outcome |
|---|---|---|---|
| FreeCAD MCP connector | 2026-09-23 | [FreeCAD MCP connector](completed%20projects/FreeCAD-MCP-Connector.md) | MCP successful with recorded CAD editing/export evidence; remaining enclosure design and print/fit validation abandoned because Jason reused an old PC case |
| Email triage/summarization digest | 2026-09-23 | [Email triage/summarization digest](archive/Email-Triage-Digest.md) | Superseded before start by [Aster Personal Assistant](archive/Aster-Personal-Assistant.md) |
| Calendar personal assistant | 2026-09-23 | [Calendar personal assistant](archive/Calendar-Personal-Assistant.md) | Superseded before start by [Aster Personal Assistant](archive/Aster-Personal-Assistant.md) |
| Combined morning digest | 2026-09-23 | [Combined morning digest](archive/Combined-Morning-Digest.md) | Superseded before start by [Aster Personal Assistant](archive/Aster-Personal-Assistant.md) |

## Superseded AI plans — 2026-09-25

The [Aster Adaptive Computing project](AI%20Projects/Aster-Adaptive-Computing.md) is the governing execution plan. [Archive index](archive/README.md) preserves predecessor requirements and status. Supersession does not mean implementation completed or remove prior privacy/safety constraints.

| Archived plan | Disposition |
|---|---|
| [Aster Personal Assistant](archive/Aster-Personal-Assistant.md) | Standalone queue superseded; M0 evidence and later personal/research/photography requirements retained |
| [Home Assistant Voice Assistant](archive/Home-Assistant-Voice-Assistant.md) | Standalone architecture superseded; household requirements retained for a later gated release |
| Email / Calendar / Combined Morning Digest | Previously superseded predecessors now archived; see closed-project links above |

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
- **Closed** — archived by explicit decision with incomplete or abandoned scope recorded; does not imply every graduation gate passed.

## Relationship to the initial-build record

[`PROJECTS.md`](../../PROJECTS.md) remains the historical completion record for
the initial HomeLab build and contains only its final reliability follow-up and
small deferred cleanup items. Major enhancement execution is tracked here.
