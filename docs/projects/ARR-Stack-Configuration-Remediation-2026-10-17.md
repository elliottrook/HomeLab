# ARR Stack Configuration Remediation — 2026-10-17

> Status: Complete — Stream A; remote Git synchronization pending approval
> Owner: Jason / HomeLab operations
> Proposed: 2026-10-17
> Approved: 2026-10-17 by Jason after review of the recorded pre-start risk assessment
> Service release: V1 production configuration maintenance
> Current environment: Production applications, TrueNAS VLAN 20
> Target environment: Unchanged
> Rollback reference: pre-change TrueNAS checkpoint and application config backups captured in M0

## Purpose and desired outcome

Correct the Bazarr synchronization regression, bring Lidarr to the current
stable release, reduce unnecessary container privilege and exposure, make
service health explicit, and improve future-import naming without changing the
existing acquisition, request, subtitle or archive authority model.

The project produces no speech and does not interact with the Aster voice path.

## Current state and evidence

Read-only review on 2026-10-17 found:

- Sonarr 4.0.20.3014, Radarr 6.4.4.10685, Lidarr 3.1.0.4875,
  Prowlarr 2.6.5.5623, SABnzbd 5.1.3, Bazarr 1.6.2, Seerr 3.5.0 and
  Profilarr 2.2.0 are running.
- Upstream publishes Lidarr 3.1.5.5066 as a prerelease. LinuxServer's reviewed
  stable channel remains Lidarr 3.1.0.4875 and advanced from image revision
  `ls42` to `ls43`; the project does not promote the prerelease.
- Bazarr addresses Sonarr and Radarr by Docker DNS names. Their current Allowed
  Hosts settings reject those Host headers with HTTP 400, and Bazarr records an
  hourly response-decoding exception for both synchronizations.
- The fresh sanitized ARR report shows Sonarr healthy with an empty queue,
  Radarr with one blocked import, Lidarr with six queued records including four
  failed imports, Prowlarr healthy and SABnzbd with no download errors.
- Sonarr and Radarr do not rename future imports; Lidarr naming is enabled.
- All core images use mutable `latest` tags, although critical services are
  correctly excluded from unattended Watchtower updates.
- Core ARR, SABnzbd and Bazarr containers lack Docker health checks.
- Prowlarr has an unnecessary read/write media mount. Published recovery ports
  bind all IPv4 and IPv6 interfaces rather than only the TrueNAS application
  address.
- Seerr is running with debug logging. Bazarr has analytics and application
  self-update enabled even though deployment updates are container-owned.
- Existing daily configuration backup coverage and the five-minute sanitized
  ARR report are operational authorities for recovery and health respectively.

## Scope and exclusions

### In scope

- Capture a root-private pre-change checkpoint of deployment definitions,
  image identities, relevant non-secret settings and application databases;
  verify the existing configuration backup is fresh and readable.
- Add only the Docker-internal `sonarr` and `radarr` names to the corresponding
  Allowed Hosts policies, then validate Bazarr sync and all existing private
  ingress/recovery paths.
- Diagnose existing Radarr/Lidarr queue failures source-locally and record only
  aggregate/error-class evidence. Correct a proven configuration or permission
  defect if it is within this project; leave item-specific ambiguous failures
  for operator review.
- Upgrade only Lidarr to the current stable container release in a controlled
  restart, preserving its database and configuration.
- Replace mutable image declarations with reviewed explicit release tags or
  immutable digests for the scoped stack.
- Add lightweight local Docker health checks without embedding credentials in
  Compose or granting automatic destructive remediation.
- Remove Prowlarr's unused media mount after proving it has no consumer.
- Bind recovery ports to `192.168.20.40` after validating all current consumers
  use the existing Docker network or that address.
- Enable Sonarr and Radarr naming for future imports using information-preserving
  formats. Validate the formats synthetically; do not invoke library-wide rename.
- Return Seerr logging to `info`; disable Bazarr analytics and application
  self-update if the deployed release exposes those supported settings.
- Review SABnzbd history database size and retention without deleting history.
- Update operational, recovery and user-facing documentation.

### Explicitly excluded

- No media deletion, move, re-encoding, bulk rename or library-wide rescan.
- No automatic retry, removal or dismissal of existing queue records and no
  new acquisition initiated as a test.
- No changes to profiles/custom formats owned by Profilarr, indexers owned by
  Prowlarr, request policy owned by Seerr, SAB extraction/category behavior, or
  the active/archive lifecycle.
- No Recyclarr, Unpackerr, Cleanuparr, Maintainerr, Decluttarr, Huntarr,
  Autobrr, torrent tooling, Notifiarr, Tdarr or other new add-on.
- No SABnzbd history deletion or retention change without a separately recorded
  size-based decision.
- No firewall, DNS, certificate, Authentik, NPM, public-ingress or VLAN change.
- No credential display, rotation or storage in Git or evidence.
- No remote Git push without immediate explicit confirmation.

## Authority model and architecture

| Concern | Authority |
|---|---|
| Live containers, mounts, ports and deployment | TrueNAS Docker state and deployed Compose definition |
| Application configuration | Each live ARR/Bazarr/SAB/Seerr application |
| Profiles and custom formats | Profilarr |
| Indexers | Prowlarr |
| Download/extraction/category handoff | SABnzbd |
| Requests | Seerr and the existing unified-media workflows |
| Subtitles | Bazarr |
| Active/archive lifecycle | Existing video-archiver workflow |
| Current aggregate health | Fresh schema-validated Aster ARR report |
| Stable operating model | ARR operational reference |

The request-to-library path remains:

`Seerr/monitor -> Prowlarr -> SABnzbd -> ARR import/naming -> Jellyfin`

Bazarr remains an additive subtitle sidecar consumer of Sonarr and Radarr.

## Privacy and security design

The work remains on private LAN and Docker paths. Source-local scripts may read
protected configuration to extract only required booleans, hostnames, version
and aggregate error classes; raw configuration, tokens, titles and download
identifiers are not emitted. Narrow port binding and removal of Prowlarr's media
mount reduce attack surface. Allowed Hosts is expanded only to two existing
Docker service identities, not to wildcards.

## Pre-start risk assessment

| Risk | Likelihood / impact | Control and rollback | Residual risk |
|---|---|---|---|
| Allowed Hosts repair weakens host filtering | Low / medium | Add exact Docker names only; retain existing names/address; rejected-host test; restore captured setting | Low |
| Lidarr upgrade causes migration/startup failure | Low / medium | Fresh DB/config checkpoint, exact prior image identity, one-service restart, API/log/database validation, roll back image and config if required | Low/medium |
| Port narrowing breaks NPM, Homepage or peer containers | Medium / medium | Inventory consumers first; change one deployment boundary; test private HTTPS, direct recovery and Docker peers; restore prior port declarations | Low |
| Health check marks a working app unhealthy | Medium / low | Use lightweight local endpoint/TCP checks; do not couple to auto-restart; validate normal and dependency-failure behavior | Low |
| New naming format causes undesirable filenames | Low / medium | Validate format preview/synthetic examples; enable for future imports only; preserve original setting checkpoint; no bulk rename | Low |
| Image pin prevents future security updates | Medium / medium | Record update owner and monthly/current-release review; retain deliberate maintenance-window process | Low/medium |
| Queue remediation alters media or download state | Medium / high | Diagnosis only; no retry/delete/dismiss/import when ambiguous; stop on item-specific mutation requirement | Low |
| Secrets or media identity enter evidence | Low / high | Source-local redaction and aggregate output; secret-pattern review before commits | Low |

No destructive or irreversible operation is planned. Expected interruption is a
brief Lidarr restart plus one bounded stack recreation if Compose-only controls
cannot be applied service-by-service. Sonarr, Radarr, SABnzbd, Prowlarr, Bazarr
and Seerr should otherwise remain available. Any unexpected database migration,
credential prompt, media mutation, public exposure, broken backup or materially
different topology is an abort condition.

Recovery uses the pre-change deployment/config checkpoint, existing daily
configuration export and exact prior image identities. Synthetic URL/filename
checks and disposable health probes are sufficient; production media is not a
test fixture.

## Persistence plan

The project document is updated before and after every milestone. The private
TrueNAS checkpoint contains the exact rollback material; this Git document
records only its path, timestamp and non-secret validation result. Resume by
re-reading this project, repository status, the latest ARR report and live
container identities, then continue at the first unchecked milestone.

## Milestones

### M0 — Checkpoint and consumer map

- [x] Verify current backup freshness and application/database health.
- [x] Capture deployment definitions, image identities and scoped application
  settings in a root-private checkpoint.
- [x] Inventory all consumers of published ARR ports and Prowlarr's media mount.

Gate: rollback material is readable and every network/mount consumer is known.

### M1 — Restore Bazarr synchronization

- [x] Add exact Docker service names to Sonarr and Radarr Allowed Hosts.
- [x] Run Bazarr Sonarr and Radarr synchronization twice and confirm success.
- [x] Prove private HTTPS, direct recovery, accepted Docker hosts and rejected
  arbitrary hosts behave as intended.

Gate: two successful synchronization passes and no ingress regression.

### M2 — Application settings and queue diagnosis

- [x] Diagnose Radarr/Lidarr failures without intentionally changing queue or media state.
- [x] Enable and validate future-import naming in Sonarr and Radarr.
- [x] Set ARR/Seerr logging to info and disable supported Bazarr telemetry/self-update.
- [x] Measure SAB history database size; record a retention recommendation only.

Gate: settings persist, aggregate health remains valid and no existing media or
queue record changed.

### M3 — Container maintenance and least privilege

- [x] Refresh Lidarr to the current stable LinuxServer image revision and validate startup/API/database/logs.
- [x] Pin scoped image releases/digests and record update ownership.
- [x] Add and validate container health checks.
- [x] Remove Prowlarr's unused media mount.
- [x] Narrow host port bindings after consumer validation.

Gate: all containers are healthy, every existing consumer path works, Lidarr
retains its library/configuration, and rollback remains available.

### M4 — Regression, documentation and handover

- [x] Run two acquisition-path health passes without creating a download.
- [x] Reconcile Doctor/Aster report, Beszel coverage, backups, service registry,
  operational reference and relevant human wiki guidance.
- [x] Perform intent/efficiency, secret-pattern and documentation-adequacy review.
- [x] Record user handover for future-import naming and recovery behavior.
- [x] Create focused local commits; request confirmation before any push.

Gate: all graduation criteria pass or remaining work is explicitly deferred.

## Validation and evaluation

Validation covers Compose rendering, container health, API status, Bazarr sync,
allowed and denied Host headers, private HTTPS, direct recovery, peer-container
connectivity, Lidarr database/log health, mount absence, port listeners, naming
preview, backup freshness and two fresh sanitized ARR reports. Failure tests are
bounded and do not inject media or queue mutations.

## Observability and maintenance

Aster's five-minute sanitized ARR report remains the aggregate workflow monitor.
Docker health checks provide local lifecycle state rather than duplicate alerts.
Beszel coverage must be reconciled after container recreation. Critical images
remain outside Watchtower; HomeLab operations owns explicit update review.

## Backup, restore and rollback

M0 records the private checkpoint location and validates the existing daily
configuration archive. Each setting can be restored independently. Container
changes roll back to the saved Compose definition and prior image identities;
Lidarr additionally uses its captured application database/configuration. Port
bindings and mounts revert by restoring the prior deployment definition and
recreating only affected services.

## Integration impact checklist

- [x] HomeLab Doctor / Aster ARR report — two fresh reports delivered; health semantics unchanged.
- [x] Monitoring and Beszel — no TrueNAS host/agent object changed; Aster remains the declared service-level monitor and Docker health does not duplicate alerts.
- [x] Backup and recovery — pre/post recursive snapshots, private checkpoints and daily export verified.
- [x] NetBox — not applicable; no service address, VM, interface or VLAN changed.
- [x] Human wiki — ARR operator page and Bazarr recovery procedure updated.
- [x] Aster mirror — authoritative ARR source updated; activation deliberately deferred because the shared source repository contains unrelated uncommitted work and the builder correctly refuses a clean accepted snapshot.
- [x] Operational reference and runbooks — current host-policy, image, health, naming and rollback facts recorded.
- [x] Environment/release lifecycle and service registry — ARR V1 build/configuration record added.
- [x] Repository documentation and changelog — project, portfolio and changelog updated.
- [x] Diagrams/rack records — not applicable; no topology or physical change.
- [x] Homepage/service discovery — existing private ARR links return Authentik redirects; no new tile required.
- [x] Authentication/authorization — Authentik routes and direct recovery behavior remain unchanged.
- [x] DNS/certificates/firewall — no writes; established ARR private HTTPS routes still answer.
- [x] Automation/schedules — Watchtower exclusions preserved; corrected scoped timezone makes application schedules local as documented.
- [x] Security inventory — immutable image ownership and controlled update responsibility recorded; secret review passed.
- [x] AI administration — unchanged; Aster reporting remains read-only and no mutation capability was added.

## Graduation criteria

- Bazarr completes two Sonarr and Radarr sync passes without the current errors.
- Lidarr runs the reviewed stable release with preserved configuration/library.
- All scoped services report healthy and all existing private access paths work.
- Prowlarr has no media mount and recovery ports are narrowly bound where proven safe.
- Sonarr/Radarr future imports use accepted information-preserving naming without
  renaming existing media.
- Queue/media state is unchanged except for a separately documented safe repair.
- Recovery, monitoring, documentation, intent/efficiency and handover gates pass.

## Evidence log

| Date | Action | Evidence | Result |
|---|---|---|---|
| 2026-10-17 | Read-only stack review | Live versions, mounts, listeners, sanitized APIs/report and source-local log summaries | Bazarr Host-header regression confirmed; Lidarr update and hardening opportunities bounded |
| 2026-10-17 | Stream A approval | Jason accepted the recorded scope, exclusions, risks and rollback envelope | Implementation authorized; no production mutation had occurred at approval |
| 2026-10-17 | M0 checkpoint | Daily configuration export from 2026-10-16 05:02 PDT passed gzip/tar traversal; recursive `Media/appdata` and `Media/ix-apps` snapshots plus root-private Compose/image checkpoint `arr-remediation-20261017T0745Z` captured | Rollback is readable; 29 scoped snapshots exist and no credential content entered evidence |
| 2026-10-17 | Consumer and least-privilege review | No Prowlarr process file descriptor or text configuration referenced `/media`; current clients use Docker DNS or `192.168.20.40` | Prowlarr media mount is removable; recovery listeners can bind the application address |
| 2026-10-17 | M1 Bazarr repair | Added exact `sonarr` and `radarr` Docker identities to Allowed Hosts; retained private FQDNs and `192.168.20.40`; rejected arbitrary Host remains HTTP 400 | Two post-change Sonarr/Radarr sync passes completed, both SignalR feeds connected and no decode/job exception recurred |
| 2026-10-17 | M2 naming/privacy settings | Enabled Sonarr/Radarr future-import rename and appended conditional release-group tokens; set ARR/Seerr logs to info; disabled Bazarr analytics and self-update | Settings persisted; no bulk rename or media scan invoked |
| 2026-10-17 | M2 queue/SAB review | Radarr's prior queue warning was absent with no recent import history; Lidarr's retained import failure was a 49.3% track match below the 60% safety threshold; SAB history DB is 2.8 MB | No queue retry/dismissal or retention deletion justified; ordinary live queue activity remains visible in the sanitized report |
| 2026-10-17 | Stable-channel review | Registry `latest` for LinuxServer Lidarr resolved to 3.1.0.4875-ls43; upstream 3.1.5.5066 is a prerelease | Deployed stable ls43; did not promote the prerelease |
| 2026-10-17 | M3 container maintenance | Scoped images pinned by digest; Prowlarr media mount removed; recovery ports bound only to `192.168.20.40`; health checks added; all scoped TZ values corrected from the malformed shared value to `America/Vancouver` | Eight scoped containers running; all health checks healthy, including Profilarr's image-provided check; direct recovery endpoints return HTTP 200/redirect as expected |
| 2026-10-17 | Post-change report | Fresh report `2026-10-17T08:04:08Z` delivered successfully | Sonarr, Radarr, Prowlarr, SABnzbd and Jellyfin healthy; Lidarr warning reflects one safe import refusal amid live queue activity; no repair candidate issued |
| 2026-10-17 | Accepted recovery point | Root-private accepted Compose/image manifest plus recursive `post-arr-remediation-20261017T0805Z` snapshots | 58 pre/post snapshot entries cover appdata and Docker state; prior and accepted definitions retained independently |
| 2026-10-17 | Final regression | Direct recovery endpoints passed; established private ARR HTTPS routes returned Authentik redirects; eight report producer/validator tests passed; second report `2026-10-17T08:07:12Z` settled at Sonarr/Radarr/SAB zero and one safe Lidarr warning | Functional, denied-host, monitoring and recovery gates pass without a new acquisition or media mutation |
| 2026-10-17 | Documentation and efficiency review | Operational reference, service registry, human ARR guide and Bazarr runbook reconciled; scoped containers use local timezone and info logs | Intended single-authority design retained; Aster snapshot activation deferred rather than ingesting unrelated dirty source work |

## Close-out and documentation adequacy reflection

The remediation graduated on 2026-10-17. The ARR ownership model did not
change and no add-on was introduced. Sonarr/Radarr future-import naming now
retains release-group information, but existing files are untouched. The first
Sonarr restart took roughly two and a half minutes because its historical log
database is large; subsequent info-level, health-checked recreation completed
normally. Historical Sonarr/Radarr log databases remain a deliberate cleanup
follow-up because deleting them was outside the non-destructive envelope.

The private pre/post checkpoints, service registry, operational reference and
human wiki are sufficient for another operator to validate, update and roll
back the stack. The authoritative ARR reference is ready for Aster's next clean
knowledge snapshot. Immediate activation was deliberately deferred because the
shared HomeLab repository contains unrelated uncommitted work; building with
`--allow-dirty` would weaken provenance and could include unrelated changes.

Remote repository synchronization remains pending the repository's required
immediate push confirmation. This does not affect the running deployment or its
TrueNAS-local recovery material.
