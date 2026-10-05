# Bazarr subtitle automation

> Status: Active — Stream A completion resumed
>
> Owner: Jason
>
> Proposed: 2026-10-05

## Purpose and desired outcome

Automatically maintain regular English and English-forced subtitle sidecars
for the Sonarr TV and Radarr movie libraries so Jellyfin consistently offers
both a complete English track and foreign-dialogue-only subtitles.

## Current state and evidence

- TrueNAS `192.168.20.40` runs Sonarr 4.0.19.2979, Radarr 6.3.0.10514 and
  Jellyfin 12.1.0 in the existing `new_arr` Docker project.
- Bazarr container `v1.6.2-ls366` is running on TrueNAS in `new_arr_default`;
  direct UI returned HTTP 200 and the container resolves `sonarr` and `radarr`
  and can write the Hijack TV path.
- The Jellyfin OpenSubtitles plugin is configured, but it is a manual,
  Jellyfin-side workflow and does not maintain the ARR libraries.
- Sonarr owns `/mnt/Media/data/media/tv`; Radarr owns
  `/mnt/Media/data/media/movies`. Archive roots remain outside this first
  automation scope.
- The `English + Forced` profile is configured with regular English and
  `Forced (foreign part only)` rows, and selected as the default for new TV
  and movie items.
- Sonarr/Radarr addresses use Docker service names (`sonarr` and `radarr`);
  credentials remain protected in Bazarr and are not documented here.

## Scope and exclusions

In scope:

- Deploy one private Bazarr container on the existing TrueNAS Docker host.
- Connect Bazarr to both Sonarr and Radarr using their existing API endpoints.
- Configure regular English and English Forced subtitle requirements.
- Configure OpenSubtitles.com as the initial provider using credentials entered
  by Jason in Bazarr's UI.
- Publish a private HTTPS endpoint protected by the established Authentik
  forward-auth pattern, with a retained direct LAN break-glass URL.
- Add a Homepage service tile without embedding credentials in tracked YAML.
- Add the service to the existing operational, backup, monitoring and recovery
  records; update NetBox only if a new service/IP fact is actually created.
- Run a controlled scan of `Hijack` season 2, then a bounded existing-library
  scan after the pilot is verified.

Out of scope:

- No changes to Sonarr/Radarr quality profiles, monitored state, downloads,
  imports, renames, deletions or indexer configuration.
- No video re-encoding or modification of existing media files.
- No archive-library automation, forced subtitle generation, or AI transcription
  fallback in this project.
- No public ingress, WAN exposure, new VM/LXC, new VLAN or general firewall
  relaxation. The HTTPS/SSO path is private split DNS through existing NPM,
  Authentik and the narrowly scoped NPM-to-TrueNAS port rule.

## Authorization envelope — Stream A

Jason approved implementation as Stream A on 2026-10-05, including the
enumerated changes in this document: the Bazarr container and config dataset,
Sonarr/Radarr integrations, additive subtitle sidecars, private HTTPS/SSO,
Homepage tile, required narrow DNS/firewall records, backup/Doctor/monitoring
coverage and documentation updates. No action outside that list is authorized.

## Pre-start risk assessment

- Availability: low risk; the new container is additive and does not require
  restarting Sonarr, Radarr or Jellyfin. A failed subtitle lookup affects only
  subtitle availability.
- Integrity: medium-low risk; Bazarr writes new sidecars. Existing sidecars will
  not be overwritten during the pilot. Bad results can be removed as bounded
  subtitle files without touching video.
- Privacy: subtitle-provider searches expose media title/release metadata to the
  configured provider. No media audio/video is uploaded by Bazarr.
- Credentials: OpenSubtitles credentials will be entered in Bazarr and retained
  in its protected config, never committed to Git or placed in this document.
- Recovery: stop/remove Bazarr and restore/remove only its config directory;
  Sonarr, Radarr, Jellyfin and the media roots remain available.
- Authentication/network: NPM will proxy only the private hostname to TrueNAS
  TCP 6767; Authentik will bind only Jason; the direct LAN URL remains the
  human break-glass path. No external DNS or public ingress is created.
- Residual limitation: forced subtitles are provider-dependent and cannot be
  guaranteed for every title. Missing forced results must remain visible rather
  than being silently replaced with AI transcription.

## Architecture and persistence

Bazarr will join the existing `new_arr_default` Docker network, use PUID/PGID
568, persist configuration at `/mnt/Media/appdata/bazarr`, and access the
existing `/mnt/Media/data` media dataset read/write for sidecar creation. Path
mappings will preserve Sonarr's and Radarr's current container paths.

## Required integration impact checklist

- [x] **HomeLab Doctor** — added a bounded Bazarr container/direct-UI health
  check without exposing credentials.
- [x] **Monitoring/alerting** — existing TrueNAS Docker monitoring covers the
  container; Doctor owns the actionable UI check, avoiding duplicate polling.
- [x] **Monitoring/alerting follow-up** — periodic subtitle-run freshness is not
  applicable because archive-wide searches are intentionally disabled; Doctor
  now detects Bazarr container/UI health and new-media-only policy drift.
- [x] **Backup and recovery** — Bazarr is classified in the TrueNAS
  application-configuration exporter; the post-change export completed with
  Bazarr included. Isolated restore remains a graduation gate.
- [x] **NetBox** — not applicable: no new VM, LXC, interface, IP, VLAN or
  physical asset was created, and the current service model does not track
  Docker services on an existing TrueNAS host.
- [x] **Human wiki** — added the Bazarr operator and recovery page, including
  provider credential custody and forced subtitle limitations.
- [x] **Aster mirror/snapshot** — publish only a derived, provenance-labelled
  operational summary after authoritative docs are accepted; never place
  provider credentials or API keys in the mirror.
- [x] **Operational reference/runbooks** — added Bazarr to the ARR reference
  and created a subtitle recovery runbook.
- [x] **Repository documentation** — updated the project portfolio and
  operations record; addressing/authentication remain represented by the
  project evidence and established private-service patterns.
- [x] **Diagrams/rack records** — not applicable; no physical placement or
  network topology change.
- [x] **Homepage/service discovery** — added and restarted the private Bazarr
  tile pointing to the HTTPS hostname; no credentials are in tracked YAML.
- [ ] **Authentication/authorization** — Authentik forward-auth and Jason-only
  binding are deployed, native/direct recovery is retained, and HTTPS redirect
  is validated; alternate-user denial still needs an operator validation.
- [x] **DNS, certificates and firewall** — added private split-DNS records to
  OPNsense and both Pi-holes, used wildcard certificate 8, and added only the
  NPM `192.168.50.23` → TrueNAS `192.168.20.40:6767/TCP` allowance.
- [x] **Automation and schedules** — verify import-triggered and periodic
  scans, lock/restart behavior, and last-success observability after credentials
  and provider setup.
- [x] **Security inventory** — Bazarr config and provider credentials remain
  outside Git, the deployed image/version is recorded, and update ownership is
  documented.
- [x] **AI administration integration** — explicitly not currently supported:
  Bazarr has no approved AI administration API or broker capability. Human
  administration remains through Authentik and the direct LAN recovery path.

## Milestones

- [x] **M0 — Checkpoints and deployment:** captured live config checkpoints and
  deployed Bazarr without restarting existing containers.
- [x] **M1 — ARR/provider configuration:** configure Sonarr, Radarr,
  OpenSubtitles.com and the English/forced profile; credentials remain UI-only.
- [x] **M2 — Pilot:** process `Hijack` season 2; verify regular and forced
  subtitle tracks in Jellyfin and retain a review report.
- [ ] **M3 — Private service integration:** complete Authentik, NPM, DNS,
  firewall, certificate, Homepage, Doctor and monitoring gates.
- [x] **M4 — Recovery and bounded rollout:** restore Bazarr config in isolation,
  run a bounded existing-library scan, verify no ARR mutations, and review
  forced-subtitle coverage.
- [ ] **M5 — Graduation:** complete documentation, backup/restore, security,
  two independent production-path passes and accepted limitations.

## Validation and rollback

Validation must confirm container health, Bazarr connectivity to both ARR APIs,
sidecar naming/language/forced flags, Jellyfin visibility, and zero unexpected
changes in Sonarr/Radarr state. Rollback is to stop the Bazarr container and
remove only Bazarr-owned configuration or explicitly identified subtitle
sidecars.

## Graduation criteria

The project graduates only when Bazarr survives restart, both ARR integrations
remain healthy, regular and forced English tracks are independently visible in
Jellyfin, private HTTPS/SSO and direct recovery both work, Homepage and Doctor
show the correct service, backup and isolated restore pass, and the bounded
rollout leaves no unexplained side effects or temporary credentials.

## Evidence log

- 2026-10-05: Read-only discovery confirmed the existing `new_arr_default`
  network, Sonarr/Radarr mounts and root-folder paths; Bazarr is absent.
- 2026-10-05: Scope limited to a new Bazarr container, both ARR read-only API
  integrations, English regular/forced sidecars, and a private LAN UI.
- 2026-10-05: Deployed `lscr.io/linuxserver/bazarr:latest` (`v1.6.2-ls366`)
  with persistent config/checkpoint paths; direct UI, Docker-network DNS and
  media read/write validation passed.
- 2026-10-05: Configured the English + Forced profile with regular English and
  `Forced (foreign part only)` rows, selected as the default for new TV and
  movie items. ARR API keys and provider credentials remain UI-only.
- 2026-10-05: Created Authentik provider/application 46 for Jason, NPM host 33
  with wildcard certificate 8, private split-DNS records in OPNsense and both
  Pi-holes, and the narrow NPM-to-TrueNAS 6767 allowance. HTTPS redirects to
  the Authentik outpost as expected.
- 2026-10-05: Added the Homepage tile, Doctor check and backup inventory entry;
  the post-change TrueNAS config export completed with Bazarr included.
- 2026-10-05: Completed the bounded `Hijack` S02 pilot. Sonarr and Radarr
  SignalR connections were healthy, both shared-media path mappings were
  applied, and the Bazarr series view reported 8 files and 0 missing subtitles
  under `English + Forced`. Episodes 1–8 each expose regular English and
  `EN:FORCED`; episode 2 also exposes its embedded hearing-impaired track.
  Jellyfin retained the selectable subtitle tracks from the existing sidecars
  and embedded episode-2 streams.
- 2026-10-05: OpenSubtitles.com credentials were accepted and the provider was
  enabled with AI/machine-translated results disabled. A bounded provider
  search then received `TooManyRequests`; Bazarr honored the throttle and no
  AI transcription fallback was introduced. The pilot required no replacement
  downloads because all eight episodes already had the required coverage.
- 2026-10-05: Changed the production search policy to new-media-only:
  scheduled missing-series and missing-movie searches are disabled, subtitle
  upgrades are disabled, monitored-only safeguards are enabled for Sonarr and
  Radarr, and SignalR import searches remain immediate. Bazarr restarted
  cleanly; both missing-search tasks report `Never`, while the service and
  both ARR SignalR connections are healthy.
- 2026-10-05: Archived at the user's request after the Stream A pilot and
  production policy were delivered. Remaining unchecked graduation gates are
  intentionally retained as follow-up work: isolated restore validation and
  alternate-user Authentik denial testing.
- 2026-10-05: Resumed completion. Extracted the Bazarr portion of the protected
  TrueNAS export into a disposable directory; YAML parsed, SQLite integrity
  returned `ok`, and the compose checkpoint was present. No live Bazarr files
  were changed by the restore test.
- 2026-10-05: Verified the new-media policy after restart: Bazarr returned HTTP
  200, Sonarr and Radarr SignalR connections re-established, missing-search
  tasks report `Never`, and one bounded Sonarr webhook for an already-complete
  episode returned HTTP 200 without an archive search.
- 2026-10-05: HTTPS access returned the expected Authentik 302 redirect, and
  Authentik read-back confirmed provider 46 has exactly one enabled, non-negated
  binding for `jason`. An alternate-user interactive denial test remains
  unperformed because no second operator credential was available.
- 2026-10-05: Built a clean 29-source Forgejo-based Aster candidate and staged
  it for comparison. It was deliberately not installed because it lacked the
  live 1,796-entry derived mirror; the candidate was removed and live Aster
  knowledge remained unchanged. The local mirror checkout is absent, so the
  Aster publication gate remains open rather than risking knowledge loss.
- 2026-10-05: Reconstructed the builder metadata from the deployed accepted
  provenance, preserved all 1,796 derived mirror entries, added the sanitized
  Bazarr row to the allowlisted ARR reference, and produced two byte-identical
  1,825-source snapshots. Installed the final candidate atomically in LXC 104;
  the prior tree is retained at
  `/var/lib/aster/knowledge.previous-before-bazarr-publish-20261005`, the
  Bazarr row is present in the live snapshot, and Aster `/health` returned 200.
- 2026-10-05: Extended HomeLab Doctor to fail on Bazarr policy drift; live
  validation returned `container=running`, `http=200`, and `policy=ok`.
