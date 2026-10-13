# ARR Stack Reliability and Update Hardening

> Status: Complete — Stream A
> Owner: Jason / HomeLab operations
> Started: 2026-10-08
> Completed: 2026-10-08
> Authorization: Jason requested execution as Stream A after the live ARR assessment.

## Purpose and desired outcome

Improve the reliability and recoverability of the existing TrueNAS media
acquisition stack without changing its media model. The active high-quality
library, four-month video archive/transcode workflow, Jellyfin archive
libraries, recommendation portal and book/music automation remain authoritative.

The project targets the observed Radarr archive-import permission failure,
application hardening, controlled container updates and actionable import
monitoring. It does not add a second download client or replace an existing
workflow merely because a third-party tool exists.

## Current state and evidence

Live discovery on TrueNAS on 2026-10-08 found:

- Sonarr 4.0.20, Radarr 6.4.4, Lidarr 3.1.0, Prowlarr 2.6.5 and SABnzbd 5.1.3.
- Bazarr 1.6.2, Seerr 3.5.0, Profilarr 2.2.0, Newtarr and Watchtower 1.23.0.
- All primary images use `:latest`; Watchtower runs on a 03:00 America/Vancouver schedule.
- Radarr logs show repeated `UnauthorizedAccessException` failures writing into
  `/media/movie/archive-movies/...`.
- Sonarr logs warn that Allowed Hosts is not configured.
- SABnzbd already owns repair, unpack and category handoff.
- The archive directories and files have inconsistent owners/modes, including
  archive title directories created as `root:root` mode 0755.

The operational authority remains the live TrueNAS deployment for current
state, the ARR operational reference for stable roles, the video archiver
project for archive lifecycle behaviour, and Profilarr for profile-management
configuration.

## Scope and exclusions

### In scope

- Read-only inspection of current Docker mounts, identities, ACLs, logs and
  deployment definitions.
- A recoverable correction to the archive-directory ownership/ACL policy after
  a checkpoint and a narrowly scoped write test.
- Explicit Allowed Hosts hardening for ARR services, preserving Authentik,
  Tailscale/LAN recovery and existing reverse-proxy boundaries.
- Watchtower allow-list/update-policy changes that keep Watchtower running but
  prevent unattended updates of critical ARR and custom media services.
- A read-only ARR doctor check for stuck downloads, failed imports, API health,
  indexer sync and archive write readiness.
- Profilarr backup/drift evidence and a Newtarr overlap audit.
- Operational documentation, backup references, validation and rollback notes.

### Explicitly excluded

- No deletion, bulk rename, unmonitoring, re-encoding or movement of media.
- No change to the active/archive directory model or the video archiver's
  four-month policy.
- No new public ingress, firewall broadening, DNS exposure or authentication
  weakening.
- No Recyclarr alongside Profilarr, because that would create two profile
  authorities.
- No Unpackerr while SABnzbd owns extraction and post-processing.
- No Cleanuparr or Maintainerr automated deletion/unmonitoring.
- No Autobrr unless a future torrent/IRC acquisition project is approved.
- No new GPU, transcoder or B60 workload.
- No remote Git push without immediate explicit confirmation under repository
  policy.

## Authority model

| Concern | Authority |
|---|---|
| Current container/runtime state | TrueNAS Docker live state |
| Sonarr/Radarr/Lidarr/Prowlarr/SAB configuration | Each service's live configuration |
| Profiles, custom formats and quality settings | Profilarr, with ARR as deployed consumer |
| Active-to-archive lifecycle | Existing video-archiver workflow |
| Downloads and extraction | SABnzbd |
| Request routing | Seerr, Lidarr, LazyLibrarian and the unified recommendation portal |
| Subtitles | Bazarr |
| Stable topology and documented procedures | ARR operational reference and runbooks |

## Privacy and security design

All checks remain private on the existing TrueNAS/LAN path. No credentials,
API keys or raw configuration files enter Git or project evidence. The doctor
emits service names, states, timestamps and bounded error classes only.

The archive correction uses the narrowest existing service identity and
inherited ACLs; it will not make the media tree world-writable. Watchtower's
Docker socket remains a high-impact control boundary, so its update scope is
reduced rather than expanded.

## Pre-start risk assessment

| Risk | Control | Residual risk |
|---|---|---|
| Incorrect ACL change blocks archive or Jellyfin access | Capture current ACLs; change only archive roots; validate read/write with disposable paths; retain rollback record | Low/medium |
| Radarr import continues to fail | Validate with a non-destructive write test and one controlled existing queue item only if needed; no bulk retry | Medium |
| ARR update breaks API or migrations | Keep critical services outside unattended Watchtower updates; use config backups and maintenance-window updates | Low |
| Health checks create noisy alerts | Add only bounded thresholds and one owner; test failure output without injecting production failures | Low |
| Archive workflow is disturbed | Exclude its code, schedule and media movement from this project; inspect only | Low |
| Sensitive config appears in evidence | Use redacted queries and path/permission summaries only | Low |

Recovery checkpoint: the existing TrueNAS media/config backup coverage and
Docker deployment definitions are the rollback source. Before any ACL or
container-policy mutation, record the affected ACLs, compose labels and
container image digests in a root-private checkpoint on TrueNAS. Roll back only
the changed ACL/policy if validation fails.

## Milestones

### M0 — Baseline and checkpoint

- [x] Inspect live services, versions, mounts, logs and current policies.
- [x] Record the observed Radarr archive-import failure and Sonarr host warning.
- [x] Capture sanitized ACL, compose-label and image-digest checkpoint.
- [x] Confirm backup freshness before mutation.

Gate: checkpoint is readable, secret-free and sufficient to restore the prior
policy.

### M1 — Archive import reliability

- [x] Define the existing archive roots and intended service group.
- [x] Apply the least-privilege inherited ACL/ownership correction.
- [x] Validate Radarr and Sonarr can traverse and create a disposable test file
  in a temporary, isolated archive test directory.
- [x] Remove the disposable fixture and verify no media changed.
- [x] Recheck archive write readiness and confirm no media changed.

Gate: archive write readiness passes and no production media was altered.

### M2 — Application and update hardening

- [x] Set explicit Allowed Hosts for Sonarr and review equivalent settings in
  Radarr, Lidarr and Prowlarr.
- [x] Restrict Watchtower to an intentional update set while preserving its
  always-running restart policy.
- [x] Verify Authentik/private recovery paths remain unchanged.

Gate: protected interfaces remain reachable through the existing path and no
critical ARR service is silently subject to uncontrolled image updates.

### M3 — Observability and profile/update evidence

- [x] Add or extend a read-only ARR doctor check for import and queue boundaries.
- [x] Confirm existing protected Profilarr configuration coverage without
  introducing Recyclarr.
- [x] Audit Newtarr schedule/overlap and record the decision: retain it
  isolated and conservative; no active search schedule was observed in the
  current log window, so no schedule change was justified.
- [x] Avoid duplicate Homepage/Prometheus/Doctor alerts by extending the
  existing sanitized report contract.

Gate: a simulated or naturally observed failure produces useful, non-secret
diagnostic output and a normal pass is recorded.

### M4 — Documentation and graduation

- [x] Update operational reference, recovery/runbook and project evidence.
- [x] Validate the available request → Prowlarr → SABnzbd → ARR import →
  Jellyfin boundary using live service state and the existing sanitized report;
  no new acquisition was triggered.
- [x] Run final regression and backup/recovery checks.
- [x] Perform the post-deployment intent and efficiency review: all changed
  systems meet their stated purpose; archive write readiness is consistent,
  critical updates are controlled, monitoring is aggregate and non-secret, and
  no additional container or duplicate authority is justified. Remaining
  queue warnings are deliberately retained for separate operator review.
- [x] Commit only focused project changes; request permission before Forgejo push.

## Validation and rollback

Validation includes container health, API reachability, non-secret log review,
archive ACL checks, controlled disposable write/read/remove, Watchtower policy
inspection, profile backup presence, and two independent acquisition-path
checks where safely available. No production media is used as a test fixture.

If an ACL change fails, restore the captured ACL/ownership policy for the named
archive roots only. If an update-policy change fails, restore the prior compose
labels/arguments and restart only Watchtower. If application hardening blocks
the expected private path, restore the prior application setting and leave
Authentik/reverse-proxy configuration untouched.

## Integration impact checklist

- [ ] HomeLab Doctor — add bounded ARR/import checks.
- [ ] Monitoring/alerting — reuse existing alert owner and avoid duplicate checks.
- [ ] Backup/recovery — verify existing ARR/config coverage before mutation.
- [x] NetBox — not applicable; no device, interface, IP, VLAN or service endpoint changes.
- [ ] Human wiki — update the ARR operator procedure if the manual recovery changes.
- [ ] Aster mirror/snapshot — not applicable until a durable operational fact changes.
- [ ] Operational reference/runbooks — update after accepted changes.
- [ ] Repository documentation — this project and changelog at milestone close.
- [x] Diagrams/rack records — not applicable; no physical/topology change.
- [ ] Homepage/service discovery — only if a new operator-facing check is added.
- [ ] Authentication/authorization — hardening only; preserve existing recovery path.
- [x] DNS, certificates and firewall — not applicable; no exposure change planned.
- [ ] Automation and schedules — Watchtower policy and doctor scheduling reviewed.
- [ ] Security inventory — record no secret values; document policy ownership.
- [x] AI administration integration — not currently supported; this project adds no AI mutation path.

## Evidence log

| Date | Action | Evidence | Result |
|---|---|---|---|
| 2026-10-08 | Live discovery | TrueNAS Docker inventory, mounts, versions and recent logs | Baseline captured; Radarr archive permission failures confirmed |
| 2026-10-08 | Upstream review | Official SABnzbd, Watchtower, Profilarr, Recyclarr, Newtarr and maintenance-tool documentation | Recommendations narrowed to reliability and single-authority changes |
| 2026-10-08 | M0 checkpoint | Root-private TrueNAS checkpoint and current `Media@auto-2026-10-08_00-00` / `Recovery/configuration@backup-daily-2026-10-08_05-30` snapshots | Recovery evidence current; no secrets recorded |
| 2026-10-08 | M1 archive permissions | Normalized group ownership to `apps` and group write/traverse permissions under `/mnt/Media/data/archive-tv` and `/mnt/Media/data/archive-movies`; disposable Radarr/Sonarr write tests passed and fixtures were removed | Archive roots now have consistent service-group access; no media changed |
| 2026-10-08 | M2 hardening | Set Sonarr, Radarr and Prowlarr Allowed Hosts to their private hostname plus direct TrueNAS recovery address; enabled Watchtower label-only updates and labelled Dozzle only | Intended Host headers return 200; rejected Host headers return 400; Watchtower remains healthy and scheduled |
| 2026-10-08 | M3 observability | Extended the existing sanitized ARR report with aggregate import counters, deployed it through the existing forced-command path and validated local/receiver reports | Import boundary is observable without titles, paths, queue IDs or credentials; one existing Radarr and one existing Lidarr warning remain for operator review |
| 2026-10-08 | M4 regression | 13 focused tests passed; compose syntax passed; all ten checked containers running; archive permission counters are zero; report mode 0640 and fresh; no new permission/import errors in the post-change window | Operational gates passed; local focused commit remains before remote synchronization |
| 2026-10-08 | Local commit | `1578eb6` — `Harden ARR archive imports and update monitoring` | Focused seven-file commit created; unrelated working-tree changes preserved |

## Close-out

The project graduated on 2026-10-08 after archive import reliability, update
policy, hardening, observability, recovery, documentation and the
post-deployment intent/efficiency review passed. The active/archive library
separation and four-month video archiver remain unchanged. Third-party cleanup
or second-authority tools remain deliberately deferred unless a new project is
approved.

The remaining Radarr `importBlocked` and Lidarr `importFailed` queue records
were not automatically retried or dismissed. They are retained for normal
operator review because retrying or removing them could reacquire, delete or
alter media outside this bounded reliability project.
