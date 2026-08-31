# Jason's HomeLab Roadmap

> Last Updated: 2026-08-24
>
> **Initial-build record:** This file is the completion record for the original
> HomeLab build. Major enhancements are governed by separate project documents
> in [`docs/projects`](docs/projects/README.md). Detailed commands, credentials,
> sensitive configuration and device-specific procedures remain in the relevant
> runbooks and repository documentation.

---

# Current Release

Version 1.7.0

Current Focus:
🟢 Operate the mature production HomeLab; complete the two replacement-switch
cutover checks, then manage every major enhancement as its own project.

Project Status:
✅ Mature and consolidated — release v1.7.0. The original scope lock is lifted.
Only the delivery-dependent PoE-switch reliability close-out remains in this
record; elective work belongs to the enhancement portfolio.

---

# Project Rules

- Check an item only after it has been implemented, validated, documented, and backed up where applicable.
- Update the date and change log whenever milestones are completed.
- Do not add elective platforms, services, VLANs, or major infrastructure projects until the completion gates pass.
- New work must complete a listed milestone, resolve an urgent reliability/security issue, or be required to keep an existing service operational.
- Record urgent unplanned work in the change log, including why it could not wait.
- Add cameras only within the defined surveillance milestone and after capacity has been validated.
- Review the scope lock only after all completion gates at the end of this document pass.

---

# Phase 1 — Foundation ✅ COMPLETE

Infrastructure

- [x] OPNsense Firewall
- [x] Arista 10 GbE Layer 2 Core Switch
- [x] Proxmox Server
- [x] TrueNAS
- [x] Synology
- [x] UniFi Controller, PoE switch and wireless infrastructure

Operations

- [x] GitHub Repository
- [x] HomeLab Toolkit
- [x] SSH Key Authentication
- [x] Infrastructure Backups
- [x] lab doctor / infrastructure health tooling
- [x] Rack, device inventory, addressing and important switch paths documented
- [x] Recovery checkpoints created for core infrastructure

Stability and Resilience

- [x] WAN physical instability diagnosed and faulty cable replaced
- [x] OPNsense WAN RX descriptor tuning validated at 4096
- [x] Post-change WAN load and packet-loss tests passed
- [x] TrueNAS active-backup bond configured and failover/failback tested

Open Reliability Follow-up

- [x] Purchase a replacement for the UniFi PoE switch after repeated failure to boot following power interruptions — replacement purchased 2026-08-24.
- [x] Select a stable managed PoE replacement supporting native VLAN 10 and tagged VLANs 30, 40, 50 and 60 — selected and ordered 2026-08-24.
- [ ] Validate AP management, IoT Wi-Fi, Guest Wi-Fi, camera isolation and Frigate recording after replacement.
- [ ] Capture and back up the replacement switch configuration.

The two installation-dependent items remain scheduled for the replacement-switch
cutover after delivery. They are reliability close-out work, not a reason to
reopen the completed network design.

---

# Phase 2 — Enterprise Network ✅ COMPLETE

Planning

- [x] Validated current-state baseline
- [x] IP address baseline
- [x] Guest and IoT firewall policy
- [x] Active switch port map
- [x] Rack Diagram
- [x] Lab VLAN 70 design

Implementation

- [x] VLAN trunk infrastructure
- [x] Trusted VLAN 10 retained during migration
- [x] VLAN Servers 20 infrastructure
- [x] VLAN IoT 30 migrated into production
- [x] Guest VLAN 40 migrated into production and isolated
- [x] VLAN Management 50 infrastructure
- [x] Cameras VLAN 60 migrated into production
- [x] VLAN Lab 70 infrastructure
- [x] Guest Wi-Fi

Validation

- [x] DHCP for all routed VLANs
- [x] DNS and split DNS
- [x] Inter-VLAN routing through OPNsense
- [x] IoT and Guest firewall isolation
- [x] WAN and VLAN performance testing
- [x] Selective Trusted-to-IoT mDNS discovery validated
- [x] Philips Hue, Lutron, Apple Home and representative IoT functions validated

Validation — Lab VLAN 70 ✅ COMPLETE 2026-08-12

- [x] Create pre-change OPNsense and Proxmox recovery checkpoints
- [x] Deploy disposable Proxmox LXC 970 tagged for VLAN 70
- [x] Validate DHCP, redundant Pi-hole DNS, blocked-domain response and intended Internet access
- [x] Confirm access to protected internal services is blocked except for the explicit DNS exception
- [x] Confirm the previously validated administrator-access policy remains unchanged
- [x] Inspect the effective firewall policy and test permitted/blocked endpoints
- [x] Document the incorrect `igb0` parent, correction to `ix0`, results and rollback context
- [x] Stop and purge LXC 970 and its temporary disk after validation

Completion Gate:
VLAN 70 isolation and administrator access behave exactly as documented.

Passed 2026-08-12: disposable LXC 970 received `192.168.70.112`, used both
Pi-hole resolvers and reached Internet TCP/443. It could not reach Proxmox,
UniFi, Frigate or camera web endpoints. The OPNsense parent-interface defect
was corrected, the complete test was repeated successfully, and the guest was
purged.

---

# Phase 3 — HomeLab Dashboard ✅ COMPLETE

- [x] Homepage deployed
- [x] Internal `home.internal` DNS name
- [x] Quick links to infrastructure and applications
- [x] SSH launch links for Proxmox, Docker LXC, OPNsense and TrueNAS
- [x] Primary and secondary Pi-hole dashboard tiles and network-wide DNS filtering
- [x] Two Pi-hole instances operational
- [x] Public, blocked-domain and local-domain DNS resolution validated
- [x] Private remote access through Tailscale
- [x] Tailscale subnet access restricted to the administrator identity
- [x] Remote web and SSH administration validated without inbound WAN ports
- [x] Frigate dashboard and SSH launch links
- [x] Code Server dashboard tile and live Homepage configuration workflow
- [x] Authentik dashboard tile
- [x] Repair key-based OPNsense SSH login used by the HomeLab toolkit and validate non-interactive access
- [x] Add a dedicated SSH login key for the Frigate VM and validate the Homepage/toolkit launch path
- [x] Device Status
- [x] Backup Status
- [x] Resource Monitoring

Dashboard Follow-up Agenda — 2026-08-23

- [x] Add the reverse proxy to the `Security & Operations` dashboard group.
- [x] Review supported health widgets for OPNsense, Proxmox and TrueNAS — moved optional API-widget deployment into a separate Dashboard Observability enhancement so the initial build does not require new service credentials.
- [x] Create an `AI & Automation` group for Hermes Agent, Ollama and future AI services.
- [x] Rename `Surveillance` to `Security & Surveillance` and transfer BirdNET, camera-tool and Coral TPU status cards to the separate Dashboard Observability enhancement.
- [x] Review the operations-tool grouping — Beszel, Authentik, Code Server, Dockge, Dozzle and the reverse proxy now form `Security & Operations`; File Browser and Forgejo remain in `Application Management`.
- [x] Document the transition from direct internal URLs to friendly HTTPS service names through the reverse proxy and Authentik in `docs/08-Authorization.md` and `docs/09-Service-Authorization-Onboarding.md`.

**Dashboard follow-up complete — 2026-08-24.**

---

# Phase 4 — Backup Resilience ✅ COMPLETE

Existing Foundation

- [x] Configuration backups exist for OPNsense, UniFi, Arista, TrueNAS, Homepage, Pi-hole, Tailscale, Proxmox guests and Frigate
- [x] Proxmox backup schedules consolidated with retention configured
- [x] Checksum-verified recovery set copied to backup Synology
- [x] Current baseline, roadmap, surveillance runbook and changelog documented through release 1.4.0

Recovery Validation

- [x] Restore-test one low-risk service such as Homepage or Pi-hole — Homepage validated 2026-08-10
- [x] Restore-test a disposable Proxmox guest backup — LXC 101 restored offline as temporary guest 901 on 2026-08-10
- [x] Document recovery steps, results and approximate recovery time — Homepage and Proxmox LXC validation recorded in `docs/05-Backups.md` on 2026-08-10
- [x] Define configuration-backup retention — 7 daily, 4 weekly, 12 monthly; pre-change checkpoints 90 days; known-good baselines retained until superseded
- [x] Confirm sensitive camera and infrastructure credentials remain outside Git — current tree and full-history pattern audit passed 2026-08-10

Automation and Same-Site Protection

- [x] Automate copying recovery sets to the backup Synology
- [x] Add backup-age or backup-failure notification

Encrypted Off-Site Backup

- [x] Establish encrypted off-site protection for essential system/recovery material only — media excluded
- [x] Use S3-compatible object storage as the preferred protocol
- [x] Initial cloud target: IDrive e2 S3-compatible storage
- [x] Provision 1 TB off-site capacity, replacing the original approximate 500 GB planning assumption
- [x] Define practical snapshot/version retention before production rollout
- [x] Validate initial upload, incremental backup, encryption and restore
- [x] Document provider configuration and recovery procedure without storing credentials in Git
- [x] Schedule the next lifecycle review — review IDrive e2 by 2027-08-11; Backblaze B2 remains the fallback option
- [x] Preserve the option to replace cloud storage with an S3-compatible off-site system hosted at a trusted remote location

Completion Gate:
At least one application and one VM/guest have been restored successfully, and essential backups have automated same-site and encrypted off-site protection.

Passed 2026-08-11: Homepage and a disposable LXC restore were validated; configuration and retained Proxmox guest archives now have automated same-site copies and client-side-encrypted IDrive e2 protection; initial, incremental and recovered-file integrity tests passed.

---

# Phase 5 — Monitoring ✅ COMPLETE

Operational Monitoring

- [x] Monitor OPNsense WAN availability and error-counter deltas
- [x] Monitor Arista link state, errors, temperature and PSU state
- [x] Monitor Proxmox resource and guest health
- [x] Monitor TrueNAS pool, NFS and bond health
- [x] Monitor both Pi-hole DNS endpoints through functional public, local and blocked-domain checks
- [x] Monitor Frigate service, NFS mount and recording freshness
- [x] Monitor backup success and age
- [x] Send alerts only for actionable conditions — sustained Beszel thresholds configured for Docker, Proxmox and Frigate; iCloud SMTP delivery tested 2026-08-14
- [x] Deploy a bounded Beszel monitoring layer for Docker, Proxmox and Frigate
- [x] Add Beszel and a concise systems-up status widget to Homepage

Monitoring Scope Decision

- [x] Prometheus — not required for the initial build; any deployment belongs to a separately approved observability enhancement
- [x] Grafana — not required for the initial build; Beszel and HomeLab Doctor meet the current operating need
- [x] Alerting — actionable failure-only mail and sustained Beszel alerts are operational
- [x] Historical Metrics — bounded history is provided by Beszel; broader retention is an optional enhancement
- [x] Pi-hole DNS redundancy and network-wide rollout

Completion Gate:
Failures in routing, storage, DNS, surveillance or backups are detected without manually checking every system.

**Phase 5 complete 2026-08-15.** HomeLab Doctor provides functional infrastructure checks, Beszel supplies lightweight host/container metrics with sustained actionable alerts, and Homepage provides the concise daily status view. Prometheus, Grafana and their long-term metrics/alerting stack remain explicitly deferred future enhancements and are not Phase 5 completion dependencies.

---

# Phase 6 — Surveillance Baseline ✅ COMPLETE

Implemented

- [x] Cameras VLAN 60
- [x] Reolink Duo 2V PoE isolated at `192.168.60.10`
- [x] Frigate VM 102 deployed on Servers VLAN 20
- [x] Frigate-to-camera access limited to TCP 80, 554 and 8000
- [x] Main and detection streams configured
- [x] TrueNAS NFS recording storage
- [x] Reboot-safe NFS and Frigate startup ordering
- [x] Continuous recording validated
- [x] Private checksum-verified Frigate configuration backup created

Stability Observation

- [x] Observe Frigate health and recording continuity over an agreed period — clean final 24-hour checkpoint on 2026-08-11
- [x] Confirm the NFS mount remains stable across normal operation
- [x] Confirm recording retention removes data as expected — database and filesystem observation passed beyond the configured 3-day continuous window on 2026-08-12
- [x] Measure storage growth and estimate capacity per camera — approximately 53.7 GB across 2.2 days, or about 24 GB/day for the current camera
- [x] Record CPU, memory, decode and detection baselines
- [x] Document observed recording interruptions and their resolution — initial ffmpeg/preview interruptions did not recur during the final 24-hour checkpoint

Hardware Acceleration and Expansion

- [x] Confirm Quadro K620 capabilities and current driver compatibility
- [x] Compare those capabilities with Frigate's current HEVC 5120x1552 stream
- [x] Decide whether K620 passthrough is worth the complexity — rejected; remove the unused card during the RAM upgrade
- [x] Establish a stable initial memory baseline — 32 GB from two 16 GB ECC RDIMMs at 1866 MT/s passed memory testing; remaining CPU/RAM work is transferred to a separate hardware enhancement
- [x] Create recovery checkpoints before passthrough or driver changes
- [x] Select the Frigate upgrade path — Coral M.2 TPU for object detection, with the purchased E5-2698 v4 CPU and remaining RAM pending; remove the K620 during the next hardware-maintenance window
- [x] Confirm Coral M.2 form-factor/adapter compatibility before installation — single Edge TPU `G650-04527-01`, M.2 2230 A+E key, PCIe Gen2 x1; compatible PCIe x1 E-key carrier selected
- [x] Install and pass through the Coral TPU after creating recovery checkpoints
- [x] Test Coral object-detection acceleration using the existing camera only — `/dev/apex_0` mapped into Frigate and approximately 10 ms inference reported
- [x] Compare stability and resource use with the software baseline — Coral inference is approximately 10 ms and Frigate remained healthy with fresh recordings
- [x] Decide whether to retain or replace the K620 — remove it and use the Coral TPU for object detection
- [x] Evaluate object-detection acceleration separately from video decoding — retain CPU HEVC decode and use Coral for inference
- [x] Establish the initial single-camera capacity baseline — approximately 24 GB/day; multi-camera sizing is transferred to Surveillance Expansion
- [x] Keep the initial build to one validated camera; further cameras are a separate Surveillance Expansion project

Completion Gate:
No unexplained recording gaps, mount failures or resource exhaustion during observation; decoding/detection design is stable, measured, documented and sized for the intended camera count.

**Phase 6 baseline complete — 2026-08-24.** The single-camera production path,
storage, restart ordering, retention and Coral acceleration are operational.
Camera expansion and additional hardware capacity are enhancements, not missing
initial-build requirements.

---

# Phase 7 — Home Assistant and Controlled IoT Migration ✅ COMPLETE

Design and Recovery

- [x] Define Home Assistant goals, required integrations and success criteria
- [x] Choose a supported deployment model and document why
- [x] Deploy a dedicated Home Assistant OS VM on Proxmox
- [x] Place Home Assistant on Servers VLAN 20, not Trusted or IoT
- [x] Define minimum-access cross-VLAN policy: only Home Assistant `192.168.20.11` may initiate TCP/UDP access to IoT VLAN 30; no unrestricted IoT-to-Servers access
- [x] Create OPNsense and Proxmox recovery checkpoints before deployment
- [x] Define off-host Home Assistant backup retention and restore procedure before production migration

Pilot Deployment

- [x] Deploy Home Assistant OS 18.2 as Proxmox VM 103 with a DHCP reservation at `192.168.20.11`
- [x] Confirm current updates, DNS and `home-assistant.home.internal` local naming
- [x] Configure host-scoped firewall access from Home Assistant to IoT VLAN 30, ordered before the Servers RFC1918 block
- [x] Enable only the specific cross-VLAN discovery mechanisms required — mDNS repeater limited to LAN, Servers and IoT
- [x] Validate administration from an approved Trusted device
- [x] Confirm IoT devices still cannot initiate unrestricted internal access — live OPNsense counters verified the IoT-to-RFC1918 block
- [x] Create an initial full backup named `Fresh HAOS installation`

Integration Sequence

- [x] Integrate one low-risk local system first — Philips Hue
- [x] Integrate Philips Hue and confirm its devices are present
- [x] Integrate Lutron Caséta at reserved address `192.168.30.102`; devices imported and local light control validated
- [x] Integrate Aqara M3 through Matter; retain six water sensors, the shutoff valve and lock, and remove stale unavailable endpoints
- [x] Create and validate the Hue Hall motion-to-Lutron `Laundry Main Lights` cross-ecosystem pilot automation
- [x] Integrate the selected bounded set of TVs, Sonos/media devices, hubs and safety sensors; defer fringe devices to deliberate on-demand adoption
- [x] Preserve vendor applications where needed for firmware, recovery or unsupported functions
- [x] Deploy HomeKit Bridge as a Siri/Apple Home presentation layer while retaining Home Assistant as the sole management and automation authority
- [x] Establish duplicate-control policy: vendor apps remain for device lifecycle and safety functions; rebuilt general automations move individually to Home Assistant
- [x] Establish and validate the one-at-a-time automation migration method; future household automations follow this method and are not a project-closeout blocker
- [x] Document unsupported, cloud-dependent and intentionally excluded fringe devices as deferred until a planned use case justifies integration

Operationalization

- [x] Create a simple, maintainable dashboard for daily use
- [x] Define household access without granting infrastructure administration — validated a local non-administrator account
- [x] Enable reliable automated backups and off-host copying — encrypted native backups plus mirrored Proxmox VM archives
- [x] Add Home Assistant health and backup-age monitoring
- [x] Test VM reboot, Home Assistant restart and recovery from backup — isolated VM 903 restore booted successfully and was removed
- [x] Document dependencies, firewall exceptions, integrations, HomeKit/Siri presentation and rollback steps

Completion Gate:
Selected IoT devices are reliably controlled through Home Assistant, essential automations have a single authoritative owner, VLAN isolation remains effective, backups are off-host, and restart/restore testing passes.

**Phase 7 complete 2026-08-15.** The selected production integrations are connected, controllable and verified. HomeKit Bridge publishes the approved Home Assistant domains to Apple Home for natural Siri control; it does not own devices or automations. Remaining fringe-vendor additions and new household automations are deliberate future operations rather than unfinished migration work.

Pilot automation criterion: **complete 2026-08-13**. The Philips Hue Hall motion sensor successfully triggers the Lutron `Laundry Main Lights`. Existing vendor-app automations are not imported; Home Assistant will become the sole automation authority as each automation is rebuilt and validated. Aqara safety functions remain in Aqara while their six live water sensors, shutoff valve and lock are also visible through Matter.

Selected Apple/media endpoints and Sonos control have been validated. The Trusted-media alias and host-scoped Home Assistant rule cover the five Trusted Apple TVs; AirPort Express, Sonos and other media endpoints on IoT use the existing Home Assistant-to-IoT rule. Frigate camera entities and detection sensors remain a later bounded integration requiring a shared MQTT broker and the Frigate Home Assistant integration.

HomeKit Bridge dependency and rollback: the bridge in VM 103 advertises through mDNS and uses its HomeKit TCP listener (default `21063`). The existing bounded mDNS relay across LAN, Servers and IoT plus permitted client access to `192.168.20.11` supports discovery and control. Published domains are `light`, `switch`, `lock`, `climate`, `cover`, `fan`, `vacuum`, `scene`, `script` and `binary_sensor`; media players, cameras, general sensors, automations, buttons and helpers remain excluded to avoid duplication and diagnostic clutter. Home Assistant remains authoritative. Rollback is to remove the bridge from Apple Home and then remove or disable the HomeKit Bridge integration; source integrations, entities and Home Assistant automations remain intact. Native and VM-level backups preserve the bridge pairing state.

Home Assistant learning checkpoint: HACS is installed and authenticated without adding an elective community repository. The validated Laundry workflow now uses a Hue motion trigger, the `Laundry bright` scene, the `Laundry motion lighting` script, a five-minute `Laundry occupancy timer` helper and a separate timer-finished automation that turns the Lutron light off. This establishes the reusable trigger/condition/action, scene, script, helper and trace patterns needed for later automations without importing the conflicting vendor-app automation history.

---

# Phase 8 — Server VLAN 20 Migration ✅ COMPLETE

Server workload migration completed 2026-08-16; related Management VLAN work completed 2026-08-20:

- Frigate VM 102 and Home Assistant VM 103 already prove the VLAN 20 workload pattern, minimum-access firewall policy and rollback method.
- Docker LXC 100 completed its controlled migration on 2026-08-15 from Trusted `192.168.1.20` to Servers `192.168.20.20`. Its Homepage, Portainer, primary Pi-hole, Tailscale and Beszel workloads returned healthy; local and cellular/Tailscale tests passed. A fresh verified backup and explicit rollback copies preceded the move.
- Tailscale now advertises Trusted, Servers and Management, with identity-specific access to those approved routes. A host-scoped rule permits only the subnet-router host to reach Trusted; the general Servers isolation rules remain in force.
- The main Synology migrated to `192.168.20.41` and the Backup Synology to `192.168.20.42`. Hyper Backup, SMB, Home Assistant backup storage and both restricted pull paths were validated after the moves.
- TrueNAS migrated last to `192.168.20.40`. Its secondary Pi-hole and application endpoints passed, and Frigate's NFS dependency survived a complete client reboot with a healthy container and fresh recordings.
- UniFi LXC 101 remains management infrastructure and belongs in Phase 9.

- [x] Inventory each candidate service, dependency, port, client and DNS name
- [x] Select a stateless or easily restored service as the first migration
- [x] Verify backup and rollback before each move
- [x] Add only the required firewall access
- [x] Move one workload at a time
- [x] Validate LAN and Tailscale access for the completed Docker migration
- [x] Observe each workload before starting another migration
- [x] Update DNS, Homepage, inventories and diagrams after every move
- [x] Migrate TrueNAS and core DNS only after the migration method was proven

Completion Gate:
Intended server workloads reside on VLAN 20 with documented minimum-access rules and tested recovery paths.

**Phase 8 complete 2026-08-16.** Docker LXC 100, TrueNAS and both Synology systems now reside on Servers VLAN 20. DNS, NFS, SMB, Hyper Backup, restricted SSH pulls, Homepage and Tailscale dependencies were tested after migration. HomeLab Doctor finished with 39 passes, no functional warning and no failure; the remaining warning was the intentionally dirty Git working tree.

---

# Phase 9 — Management VLAN 50 Migration ✅ COMPLETE

Audit completed 2026-08-14; UniFi migration completed 2026-08-16:

- Deployed addresses are Arista `.50.2`, Proxmox `.50.10`, UniFi controller `.50.21`, PoE switch `.50.30`, Hall AP `.50.31` and Office AP `.50.141`.
- The `MGMT_ADMIN_HOSTS` alias contains Jason's Mac mini (`192.168.1.206`), Mac laptop (`192.168.1.241`) and iPhone (`192.168.1.112`). Other Trusted clients are explicitly blocked from Management.
- Console recovery for OPNsense, Arista and Proxmox must be confirmed before the first address change.
- UniFi LXC 101 and all three managed devices were migrated first, followed by Proxmox and Arista. VLAN 10 remains the trusted/native client network but no longer hosts these management interfaces.
- The Proxmox-facing Arista trunk carries tagged VLAN 50 for the host and LXC 101. Tailscale advertises Trusted `192.168.1.0/24`, Servers `192.168.20.0/24` and Management `192.168.50.0/24`, with explicit identity-based access policy.

- [x] Define which administrator devices may access Management
- [x] Document emergency console and lockout recovery procedures
- [x] Confirm local console access before network changes
- [x] Create explicit Trusted-to-Management access rules
- [x] Migrate one secondary management endpoint first
- [x] Validate DNS, HTTPS, SSH, routing and rollback
- [x] Migrate core management interfaces individually
- [x] Keep VLAN 10 available until the new management path is proven
- [x] Add Tailscale routing and policy only if remote management is required
- [x] Update inventories and recovery documentation for the completed UniFi migration

**UniFi migration complete 2026-08-16.** LXC 101 moved to `192.168.50.21`; the PoE switch, Hall AP and Office AP moved to `192.168.50.30`, `.31` and `.141`. All three devices remained online after address changes. The controller's temporary Trusted interface, disposable VLAN test containers, legacy-device alias and temporary firewall exceptions were removed after validation. Proxmox subsequently moved to `192.168.50.10` and Arista moved to `192.168.50.2`; both retained tested local, routed and Tailscale access. The Arista cutover used a timed EOS configuration session, matching SSH host-key verification and automatic rollback protection before the old VLAN 10 address was removed.

**Phase 9 complete 2026-08-20.** All intended infrastructure management interfaces reside on VLAN 50, approved administrator and remote-access paths are validated, and the previous management addresses have been removed.

Completion Gate:
Management interfaces are isolated on VLAN 50, reachable only from approved administrator devices, with a tested lockout-recovery path.

---

# Lab Pilot — Local AI / Hermes Agent ✅ PILOT COMPLETE

Deployed out of sequence on 2026-08-18 and 2026-08-19 as an isolated CPU-only pilot:

- [x] Deploy unprivileged Hermes Agent LXC 104 at `192.168.70.10` on Lab VLAN 70
- [x] Deploy Ubuntu 24.04 Ollama VM 105 at `192.168.70.11` with 4 vCPU, 14 GB RAM and 32 GB storage
- [x] Bind Ollama to TCP 11434 and connect Hermes through the OpenAI-compatible `/v1` API
- [x] Create and validate `qwen3-64k:8b` with `num_ctx 65536`
- [x] Confirm CPU-only operation and record the current performance limitation
- [x] Confirm LXC 104 and VM 105 are included in the all-guests Proxmox backup job
- [x] Mirror LXC 104 to the Backup Synology and checksum-verify the copy
- [x] Protect LXC 104 through the selected encrypted off-site `automated/proxmox-guests` set
- [x] Mirror VM 105 to the Backup Synology and checksum-verify the copy
- [x] Protect VM 105 through the selected encrypted off-site `automated/proxmox-guests` set
- [x] Validate isolated restores of LXC 104 and VM 105 after the off-host mirror completes
- [x] Keep Ollama normally stopped so the bounded pilot does not destabilize production; sustained-load capacity is transferred to Local AI / GPU Acceleration
- [x] Record the validated 32 GB host baseline and transfer final RAM/Frigate sizing to the next hardware-maintenance project
- [x] Transfer unused Hermes cloud-provider authentication cleanup to Credential Hygiene Enhancements
- [x] Transfer the unrelated Seerr password reset to Credential Hygiene Enhancements
- [x] Transfer GPU passthrough evaluation to Local AI / GPU Acceleration with explicit model, VRAM, fit, PSU and power prerequisites

Completion Gate:
The pilot is isolated, reproducible, backed up according to its recovery priority and can run without destabilizing production guests. GPU expansion remains a separate reviewed change.

**Pilot completion gate passed — 2026-08-24.** The CPU-only implementation is
isolated, reproducible, archive/restore tested and optional to production.

---

# Phase 10 — Automation ✅ COMPLETE

- [x] Nightly Backups — automated configuration pulls, Proxmox guest archives, Home Assistant native backups and encrypted off-site protection are operational
- [x] Configuration Drift Detection — protected OPNsense, Arista and Proxmox manifests are compared with an explicitly accepted known-good baseline
- [x] Automatic Reports
- [x] Certificate Monitoring

Audit completed 2026-08-14: keep this phase bounded. Use the existing `lab doctor` result as the basis for failure-only scheduled reporting, compare protected infrastructure exports with the prior known-good set for drift, and monitor certificate expiry only where expiry has an operational consequence. Do not build a second general monitoring platform here.

Completion Gate:

Automated backups, configuration-drift detection, failure-only health reporting and operationally relevant certificate-expiry monitoring are active and verified without creating a second general monitoring platform.

**Phase 10 complete — 2026-08-20.**

---

# Phase 11 — Final Consolidation and Project Review ✅ COMPLETE

Documentation Reconciliation

- [x] Update repository documentation for the secondary Pi-hole
- [x] Clarify which TrueNAS applications are already operational versus future work
- [x] Remove or annotate stale switch-port and historical planning references
- [x] Record the installed Proxmox RAM after any upgrade
- [x] Confirm the live inventory, addresses, VLANs and service locations
- [x] Record a fresh known-good stability checkpoint
- [x] Update the changelog and project release after reconciliation — published the reconciled work as consolidated release v1.7.0

Final Review

- [x] Confirm every earlier phase completion gate — the original production gates passed; the later PoE-switch reliability replacement remains explicitly tracked for Wednesday, while surveillance expansion and local-AI growth are separate enhancements
- [x] Resolve outdated roadmap entries
- [x] Review firewall aliases, rules and temporary exceptions — removed the obsolete Beszel rule and empty `UNIFI_LEGACY_DEVICES` alias; retained only documented production dependencies
- [x] Remove unused test configurations after confirming they are no longer needed
- [x] Confirm monitoring, backup and restore coverage for every critical service — reconciled live monitoring, nine protected Proxmox guests, verified Synology mirrors and representative application/LXC/VM restore evidence through the Forgejo restore test on 2026-08-24
- [x] Review architecture decisions and document remaining accepted risks — recorded the current authority boundaries, segmentation model, recovery strategy and explicitly accepted availability, capacity, certificate, IPv6 and AI-pilot risks
- [x] Publish an updated network diagram and current-state baseline — reconciled the routed VLAN topology, management migrations, current service locations, remote-access routes and 2026-08-20 stability checkpoint
- [x] Update the changelog and tag a consolidated release — release documentation prepared and validated for annotated tag v1.7.0
- [x] Review whether the scope lock can be lifted — the original consolidation scope lock is lifted; new elective work requires a separately reviewed roadmap

## Earlier phase completion-gate audit — 2026-08-20

- The original production phase gates have passed. The subsequently discovered PoE-switch reliability issue is isolated as a four-item follow-up; purchase and selection are complete, while installation validation and configuration capture await delivery.
- Phase 6 now closes the stable one-camera surveillance baseline. Camera expansion, multi-camera capacity and any later decode acceleration are a separate enhancement project.
- The local-AI environment has passed its bounded pilot gate. Its credential cleanup, sustained-load capacity and GPU growth are transferred to enhancement projects and are not production HomeLab dependencies.
- The Phase 4 lifecycle review is scheduled. Optional Prometheus/Grafana expansion and API-backed dashboard widgets are enhancements, not incomplete production requirements.
- No unfinished pilot item is being relabelled as complete merely to close this project.

Completion Gate:
The handover, roadmap, baseline and live environment agree, and the environment is documented, monitored, recoverable, segmented and stable enough to consider a new roadmap.

**Phase 11 complete — 2026-08-20.**

---

# Enhancement Project Portfolio

Major post-build work is tracked in self-contained project documents with its
own milestones, dependencies, evidence and completion gate.

| Project | Current status | Tracker |
|---|---|---|
| Local AI | Pilot complete; hardware-backed expansion proposed | [`docs/projects/Local-AI.md`](docs/projects/Local-AI.md) |
| Authentik rollout | Foundation proven; staged rollout proposed | [`docs/projects/Authentik-Rollout.md`](docs/projects/Authentik-Rollout.md) |
| Surveillance expansion | One-camera baseline complete; expansion proposed | [`docs/projects/Surveillance-Expansion.md`](docs/projects/Surveillance-Expansion.md) |
| NUT/UPS deployment | Handover ready | [`docs/UPS-Power-Resilience-Claude-Handover.md`](docs/UPS-Power-Resilience-Claude-Handover.md) |
| Synology Drive family cloud | Handover ready for Claude | [`docs/projects/Synology-Drive-Family-Cloud.md`](docs/projects/Synology-Drive-Family-Cloud.md) |
| Prometheus/Grafana observability | Complete; retained in production | [`docs/projects/completed projects/Prometheus-Grafana-Observability.md`](<docs/projects/completed projects/Prometheus-Grafana-Observability.md>) |

See the [enhancement portfolio index](docs/projects/README.md) for common project
rules and status definitions.

# Completed Post-Build Enhancement

## Forgejo ✅ COMPLETE 2026-08-24

- [x] Deploy Forgejo as unprivileged LXC 108 at `192.168.20.30`
- [x] Migrate the complete HomeLab repository, branches and v1.7.0 tag
- [x] Configure and validate SSH authentication
- [x] Include LXC 108 in the nightly Proxmox backup and checksum-verified Backup Synology mirror
- [x] Restore the current archive into isolated LXC 978, verify the service, database and repository, then remove the test guest

Forgejo is the primary self-hosted Git remote. GitHub remains the synchronized
off-site remote. Future Forgejo workflows, runners and package hosting are
optional enhancements and are not part of the initial HomeLab build.

# Small Deferred Cleanup and Ideas

## Credential Hygiene Enhancements

- [ ] Remove unused Hermes cloud-provider authentication remnants after confirming the local provider remains sufficient.
- [ ] Reset the Seerr application password independently of the Hermes/Ollama work.

## Other Deferred Work

- Kubernetes Lab
- PXE Boot Server
- Internal Certificate Authority
- IPv6 rollout
- New broad security-tooling platforms
- Additional dashboards outside the bounded Prometheus/Grafana project
- New self-hosted services not required by this roadmap
- Major network redesign or VLAN renumbering

---

# Operational Application Services

Jellyfin, Immich, Plex, Seerr, Calibre, Audiobookshelf and the existing media-automation applications are operational and represented in the live Homepage inventory. They are not future deployment work.

# Future Services

- Paperless-ngx
- Wiki

---

# Future Ideas

- Remote Environmental Sensors
- Evaluate Tailscale Services after the current project is complete: pilot stable MagicDNS/TailVIP names and service-level grants for a small set of internal web services such as Homepage, Home Assistant and Frigate; compare against existing device MagicDNS and subnet routing before wider adoption; keep access tailnet-only with no Funnel or public exposure

---

# Initial-Build Close-Out Order

1. Install the replacement managed PoE switch after delivery.
2. Validate AP management, IoT Wi-Fi, Guest Wi-Fi, camera isolation and Frigate
   recording.
3. Capture and back up the replacement-switch configuration.
4. Mark the final two Phase 1 reliability items complete and freeze this file as
   the initial-build record.

All other work follows the independent milestones in the enhancement portfolio.

---

# Change Log

| Date | Change | Evidence or Reference |
|---|---|---|
| 2026-08-23 | Recorded the storm-related UniFi PoE switch boot failure, unsuccessful TP-Link TL-SG1016PE fallback, delayed UniFi recovery and decision to obtain a stable managed PoE replacement. | `docs/04-Operations.md` network incident |
| 2026-08-22 | Validated code-server as the live Homepage configuration editor, corrected file permissions and service URLs, added Code Server and Authentik dashboard entries, and captured the current dashboard state. | `docs/04-Operations.md` activity log and dashboard screenshot |
| 2026-08-22 | Documented the tested Authentik-protected NPM integration and a reusable service-by-service authorization onboarding process. | `docs/08-Authorization.md`; `docs/09-Service-Authorization-Onboarding.md` |
| 2026-08-19 | Deployed Hermes Agent LXC 104 and Ollama VM 105 on isolated Lab VLAN 70; connected Hermes to the local OpenAI-compatible Ollama endpoint and validated the `qwen3-64k:8b` 65,536-token profile. | Claude handoff changelog; live addresses `192.168.70.10` and `.11`; successful local-provider test |
| 2026-08-19 | Recorded the local-AI pilot's current constraints: 14 GB was the first stable tested VM allocation, CPU-only responses are slow and aggregate guest memory is overcommitted. Same-site backup, mirror, encrypted off-site coverage and isolated restore coverage were subsequently confirmed. | Claude handoff changelog and Proxmox allocation review |
| 2026-08-16 | Installed and passed through the Coral Edge TPU to Frigate VM 102; disabled guest Secure Boot for the DKMS driver, mapped `/dev/apex_0` into the container and validated approximately 10 ms inference. | `lspci`; `gasket`/`apex`; Frigate detector log and stats |
| 2026-08-16 | Completed the UniFi portion of Phase 9: moved LXC 101, the PoE switch and both APs to Management VLAN 50; validated approved-administrator access and device health; removed the temporary Trusted interface, test containers, alias and migration rules. | UniFi Network showed all three devices online at `192.168.50.30`, `.31` and `.141`; controller reachable at `.50.21` |
| 2026-08-16 | Completed Phase 8 by migrating TrueNAS and both Synology systems to Servers VLAN 20; validated DNS, NFS recording flow after a Frigate reboot, SMB, Hyper Backup, Home Assistant backup storage and restricted backup-pull access. | HomeLab Doctor: 39 passed, 1 Git-state warning, 0 failed |
| 2026-08-15 | Migrated Docker LXC 100 and its Homepage, Portainer, primary Pi-hole, Tailscale and Beszel workloads from Trusted `192.168.1.20` to Servers VLAN 20 at `192.168.20.20`; updated DNS, DHCP, aliases and client configuration and validated local plus cellular/Tailscale access. | Verified pre-change LXC archive, healthy containers, direct DNS/port tests and remote access tests |
| 2026-08-15 | Completed the controlled IoT migration milestone and deployed a domain-filtered HomeKit Bridge for Apple Home/Siri presentation; pairing completed and Siri control of a Home Assistant-managed Lutron light was verified. Home Assistant remains the sole automation authority. | HomeKit Bridge pairing notification, Apple Home accessory import and live Siri control test |
| 2026-08-14 | Installed the first two 16 GB SK hynix ECC RDIMMs in Proxmox DIMM1/DIMM3; firmware and Linux detect 32 GB at 1866 MT/s with no reported memory errors, and a two-pass 24 GB `memtester` validation is in progress before services are restarted. | `free -h`; `dmidecode`; EDAC boot log; `/root/memtester-32gb-20260814.log` |
| 2026-08-14 | Confirmed the purchased Coral is the single M.2 2230 A+E-key PCIe x1 model and selected a compatible PCIe x1 E-key carrier for the planned Sunday installation. | Coral `G650-04527-01` datasheet and adapter compatibility audit |
| 2026-08-14 | Configured sustained actionable Beszel alerts for Docker, Proxmox and Frigate and validated email delivery through iCloud SMTP; temporary test thresholds were reverted. | Beszel alert configuration and received test/threshold email |
| 2026-08-14 | Installed HACS without adding an elective repository and expanded the Laundry pilot into a reusable scene/script/timer workflow with successful countdown and timer-finished light-off testing. | Home Assistant HACS, `Laundry bright`, `Laundry motion lighting`, `Laundry occupancy timer` and automation traces |
| 2026-08-14 | Audited Phases 8–10 and defined the remaining server and management migration order, prerequisites, rollback boundaries and deliberately bounded automation scope. | `PROJECTS.md` Phase 8–10 audit notes |
| 2026-08-13 | Completed the Home Assistant recovery layer: encrypted daily native backups to local and dedicated Synology storage, VM 103 inclusion in checksum-verified guest mirroring, health/backup-age monitoring and a successful isolated restore as temporary VM 903. | `docs/05-Backups.md`; VM 903 booted HAOS/Supervisor/Core with networking disconnected, then was destroyed |
| 2026-08-13 | Completed the first cross-ecosystem automation: the Hue Hall motion sensor controls Lutron `Laundry Main Lights`; created a maintainable Overview and validated a non-administrator household account. | Home Assistant automation trace/control test and incognito household-account validation |
| 2026-08-13 | Integrated Aqara M3 through Matter, retained six live water sensors plus the shutoff valve and lock, removed stale unavailable endpoints and preserved Aqara-owned safety behavior. | Home Assistant Matter integration and live entity review |
| 2026-08-13 | Enabled only the required mDNS relay across LAN, Servers and IoT; added a five-device Trusted Apple TV alias and an ordered host-scoped Home Assistant media rule. Apple TV pairing remains pending after a temporary code failure. | OPNsense compiled rules, alias contents and active `mdns-repeater` process |
| 2026-08-12 | Deployed Beszel 0.18.7 as a lightweight monitoring complement for Docker, Proxmox and Frigate; all three systems report healthy and Homepage shows the systems-up summary through dedicated file-backed widget credentials. | Beszel hub `192.168.1.20:8090`; Homepage `Monitoring & Maintenance` group |
| 2026-08-12 | Integrated Lutron Caséta at reserved address `192.168.30.102`, validated imported-device control, reserved Hue at `192.168.30.164`, and added a host-scoped Home Assistant-to-IoT firewall exception ahead of the Servers RFC1918 block. | Compiled OPNsense rules; Dnsmasq reservations; Home Assistant Lutron devices controllable |
| 2026-08-12 | Verified Frigate retention beyond 72 hours and selected the final upgrade path: incoming RAM, E5-2698 v4 and Coral M.2 TPU, with K620 removal during maintenance. | Frigate recording database/filesystem audit; hardware purchase decision |
| 2026-08-12 | Deployed Home Assistant OS 18.2 as Proxmox VM 103 at `192.168.20.11`, created the clean-install backup and integrated Philips Hue through narrowly scoped VLAN rules. | `docs/01-Architecture.md`; `docs/04-Operations.md`; Home Assistant Hue devices present |
| 2026-08-12 | Fully validated Lab VLAN 70 using disposable LXC 970, corrected its OPNsense parent from `igb0` to `ix0`, confirmed intended DNS/Internet access and internal isolation, then purged the test guest. | `docs/VLAN-Design.md`; DHCP lease `192.168.70.112`; endpoint isolation tests |
| 2026-08-11 | Expanded `lab doctor` with functional OPNsense, Arista, Proxmox, TrueNAS, Frigate and backup-report checks using persistent baselines. | `scripts/doctor.sh`; final run passed 36 checks with no failures |
| 2026-08-11 | Completed network-wide redundant Pi-hole deployment through Dnsmasq option 6, validated both resolver paths across client VLANs and added both roles to Homepage. | `docs/01-Architecture.md`; `docs/04-Operations.md`; release 1.5.0 |
| 2026-08-11 | Completed Phase 4 Backup Resilience with automated checksum-verified Synology pulls, failure email alerts, client-side-encrypted IDrive e2 protection and two-version incremental validation. | `docs/05-Backups.md`; Hyper Backup versions at 00:48 and 12:19 |
| 2026-08-11 | Validated an encrypted off-site Proxmox recovery by downloading an LXC 100 archive through Hyper Backup and obtaining an exact SHA-256 match against the same-site source. | `vzdump-lxc-100-2026_08_06-23_30_04.tar.zst` |
| 2026-08-11 | Repaired OPNsense public-key authentication, enabled macOS Keychain-backed SSH agent loading, and added/validated the Frigate SSH key, alias, toolkit path and Homepage launch link. | Non-interactive SSH tests and `lab ssh frigate` |
| 2026-08-10 | Completed repository credential audit across tracked filenames, current content and full Git history; no high-confidence secret or credential-assignment patterns found. | `docs/05-Backups.md` repository credential audit |
| 2026-08-10 | Adopted configuration-backup retention: 7 daily, 4 weekly, 12 monthly; 90-day pre-change checkpoints; known-good baselines retained until superseded. | `docs/05-Backups.md` configuration-backup retention policy |
| 2026-08-10 | Documented tested Homepage and Proxmox LXC recovery procedures, results, safety controls, cleanup and planning-time estimates. | `docs/05-Backups.md` restore validation record |
| 2026-08-10 | Completed disposable Proxmox guest restore test: verified the newest LXC 101 archive, restored it as stopped guest 901 with isolated networking, validated the recovered filesystem offline, then removed the guest and temporary disk. | `vzdump-lxc-101-2026_08_10-02_30_36.tar.zst`; production LXC 101 remained running and unchanged |
| 2026-08-10 | Completed isolated Homepage restore test from the checksum-verified Synology archive; restored configuration produced a healthy temporary container and HTTP 200, then all test resources were removed. | `homepage-config-20260808-162831.tgz`; production Homepage remained online and unchanged |
| 2026-08-09 | Created consolidated completion tracker and scope lock; added Home Assistant and controlled IoT migration milestone. | Handover, repository baseline, roadmap, surveillance runbook and changelog through 1.3.0 |
| 2026-08-10 | Consolidated PROJECT-TRACKER.md into PROJECTS.md; retained PROJECTS.md roadmap formatting and established it as the single project-level document of truth. | PROJECTS.md and PROJECT-TRACKER.md reconciliation |
| 2026-08-10 | Set backup resilience as current focus; added encrypted off-site S3 plan using IDrive e2, approximately 500 GB planning capacity, with Backblaze B2 fallback and remote self-hosted S3 retained as an option. | Backup planning discussion |
