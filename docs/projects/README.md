# HomeLab Enhancement Project Portfolio

> Established: 2026-08-24
>
> The original HomeLab build is the stable production baseline. Each document
> linked here governs a separate enhancement and must not silently expand the
> scope of another project.

## Portfolio

| Project | Status | Project document | Supporting material |
|---|---|---|---|
| Authentik rollout | Active — Stream A; six additional apps now use passkey-only single login, private backends and corrected dashboard links; human acceptance, media/infrastructure and graduation remain | [Authentik rollout](Authentik-Rollout.md) | [Authorization runbook](../08-Authorization.md), [service onboarding](../09-Service-Authorization-Onboarding.md), [single-login recovery](../runbooks/Authentik-Single-Login.md) |
| Surveillance expansion | One-camera baseline complete; expansion proposed | [Surveillance expansion](Surveillance-Expansion.md) | [Surveillance runbook](../07-Surveillance.md) |
| NUT/UPS deployment | Handover ready | [NUT/UPS handover](../handovers/UPS-Power-Resilience-Claude-Handover.md) | Architecture, shutdown and recovery requirements are contained in the handover |
| TrueNAS DIY SAS expansion | Ready | [TrueNAS DIY SAS expansion](TrueNAS-DIY-SAS-Expansion.md) | Eight-bay backplane-free enclosure using two vacant x4 ports on the LSI SAS 9300-16i |
| Music playlist acquisition bridge | Prototype | [Music playlist acquisition bridge](Music-Playlist-Acquisition-Bridge.md) | Hybrid Cmdarr plus local export-file bridge: translate Spotify/Apple Music and generic playlist exports into conservative Lidarr album requests, then publish a complete duplicate playlist in Jellyfin after the media is indexed |
| Media sideload import | Active — Milestone 1 complete | [Media sideload import](Media-Sideload-Import.md) | Confirmed Radarr/Sonarr/Lidarr already file manually-acquired media correctly via Manual/Interactive Import and the `DownloadedXScan` commands, without an indexer or download client; defines a staging-inbox workflow to use that path deliberately instead of hand-placing files into the canonical roots. Staging folders created on TrueNAS at `/mnt/Media/data/inbox/{movies,tv,music}` |
| Home Assistant voice assistant | Proposed | [Home Assistant voice assistant](Home-Assistant-Voice-Assistant.md) | Native HA Assist pipeline (wake word/push-to-talk → local STT → `aster-llama` conversation agent → local Piper TTS) against an explicit voice-exposed entity allowlist; open decision is whether the shared single-GPU `aster-llama` backend has concurrency headroom for a third live consumer |
| Recommendarr watch recommendations | Proposed | [Recommendarr watch recommendations](Recommendarr-Watch-Recommendations.md) | Source-local sanitized reader over Jellyfin/Sonarr/Radarr feeding read-only, no-auto-add recommendations via `aster-llama`; open decision is adopting the third-party open-source Recommendarr project versus building bespoke on the lab's least-privilege reader pattern |
| Cantinarr evaluation and controlled pilot | Proposed — Stream M | [Cantinarr evaluation and controlled pilot](Cantinarr-Evaluation-Pilot.md) | Reversible isolated evaluation beside Seerr, with no initial production credentials, media mounts, remediation, AI or MCP authority; later gates compare household requests, Import Doctor, local AI and a restricted read/request MCP surface without weakening Aster's existing ARR broker boundary |
| Document OCR + summarization | Active — Stream A; Milestone 1 (Paperless-ngx deployment) in progress | [Document OCR + summarization](Document-OCR-Summarization.md) | Summarization-only layer over Paperless-ngx's own OCR (Paperless itself not yet deployed — this project's own Milestone 1 prerequisite, kept as one project per Jason's 2026-09-15 decision); write-back into Paperless via a scoped Milestone 4 broker, summarizes every document with no sensitivity exclusion |
| Local subtitle generation/translation | Proposed | [Local subtitle generation/translation](Subtitle-Generation-Translation.md) | Whisper pipeline writing additive `.srt` sidecars to close the measured TV-subtitle gap and restore non-English tracks Video-Library-Archiving strips; open decision is which GPU/host runs it without contending with existing transcode/inference workloads |
| Video duplicate/quality-upgrade finder | Proposed | [Video duplicate/quality-upgrade finder](Video-Duplicate-Quality-Finder.md) | Reframes Jellyfin-Library-Integrity-Automation's music-only duplicate detector around a distinct movie/TV problem (upgradable low-quality copies, not accidental duplicates); report-only, never auto-deletes, and gates on a Milestone 0/1 buy-in and measurement pass given thin evidence |
| Auto-written Plex/Jellyfin collection descriptions | Proposed | [Auto-written Plex/Jellyfin collection descriptions](Auto-Collection-Descriptions.md) | Reader/generator/writer over the 165 migrated Jellyfin collections via `aster-llama`, human-reviewed dry-run plus pre-write backup given this exact metadata was twice destroyed by a Jellyfin scheduled-task bug |
| Music recommender | Proposed | [Music recommender](Music-Recommender.md) | Read-only Jellyfin/Lidarr library-and-play-history reader producing a periodic acquisition-candidate report, never auto-acquiring; open decision is whether Jellyfin's deployed instance actually exposes usable play-history data |
| Book recommender | Proposed | [Book recommender](Book-Recommender.md) | Starts audiobooks-only via Audiobookshelf's working REST API; e-book side is explicitly blocked pending Jason's choice between deploying Kavita/calibre-web or reading Calibre's `metadata.db` directly, since neither Kavita nor a Calibre API exists in this lab today |
| AI Privileged Access Management (AI-PAM) / credential broker | Active — Stream A; M0 complete, M1 human recovery prerequisite pending | [AI-PAM and credential broker](homelab-credential-broker.md) | OpenBao-backed central custody + Authentik/passkey approval + capability/MCP broker + management GUI; live topology/version discovery is complete and a 10-test deny-by-default Forgejo adapter plus recovery-gated OpenBao manifest are committed, with no production credential or service created |
| Aster Companion App | Active — voice accepted; system notifications deployed for device testing; ARR execution deferred | [Aster Companion App](Aster-Companion-App.md) | Native macOS client for Aster: Authentik passkey-only login via a new native-OIDC flow, works identically local/remote through a new NPM-proxied endpoint (no new Tailscale route), multi-persona "Aster Agents" with per-chat tool selection, a generalized gated-action framework surfacing the existing ARR-repair action, lab-hosted speech-to-text/text-to-speech, and an orb/EQ-style thinking/acting indicator; records an explicit, bounded philosophy shift toward a more autonomous Aster and excludes web-access-for-research as separate future work |
| Aster Lab Doctor and backup execution | Active — Stream A; staged deployment and validation | [Aster lab operations](Aster-Lab-Operations.md) | Bounded on-request and task-required diagnostics/backups, durable job status, target allowlists and verified recovery coverage; production access not enabled |
| Aster Companion ARR execution | Proposed — deferred follow-up, production disabled | [ARR execution follow-up](Aster-Companion-ARR-Execution-Followup.md) | Preserve separate operator approval and wait for a natural eligible candidate before live UI execution testing |
| Aster Personal Assistant | Active — Stream M; M0 discovery, decisions D1–D7 accepted | [Aster Personal Assistant](Aster-Personal-Assistant.md) | Pivots Aster toward a multi-person-ready personal assistant: read-only iCloud mail/calendar analysis, morning check-in and nudges via Companion, and isolated overnight web research via new Personal Assistant and Researcher personas; personal-data and web zones never share a process; a committed capability ladder governs any future send/appointment ability, graduating at read-and-analyze only |

## Completed projects

| Project | Completed | Closing document | Outcome |
|---|---|---|---|
| Jellyfin library integrity automation | 2026-09-23 | [Jellyfin library integrity automation](completed%20projects/Jellyfin-Library-Integrity-Automation.md) | Three clean Wednesday runs verified; bounded corrections, monitoring and local/off-site config recovery proven; ambiguous comparisons remain report-only |
| Backup architecture redesign | 2026-09-22 | [Backup architecture redesign](completed%20projects/Backup-Architecture-Redesign.md) | Current local/HA/off-site backups, fresh snapshot/crypt recovery match, monitoring and retired-job cleanup verified; capacity expansion remains separate |
| Backup Synology decommission | 2026-09-22 | [Backup Synology decommission](completed%20projects/Backup-Synology-Decommission.md) | Retired DS220j with early observation closeout, inactive NetBox asset and UPS/monitoring cleanup; disks removed but reuse/data disposition explicitly transferred to follow-ups |
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
| Email triage/summarization digest | 2026-09-23 | [Email triage/summarization digest](Email-Triage-Digest.md) | Superseded before start by [Aster Personal Assistant](Aster-Personal-Assistant.md) |
| Calendar personal assistant | 2026-09-23 | [Calendar personal assistant](Calendar-Personal-Assistant.md) | Superseded before start by [Aster Personal Assistant](Aster-Personal-Assistant.md) |
| Combined morning digest | 2026-09-23 | [Combined morning digest](Combined-Morning-Digest.md) | Superseded before start by [Aster Personal Assistant](Aster-Personal-Assistant.md) |

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
