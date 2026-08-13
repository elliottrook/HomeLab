# Jason's HomeLab Roadmap

> Last Updated: 2026-08-12
>
> **Document of Truth:** This file is the project-level source of truth for completed work, active milestones, deferred projects, and execution order. Detailed commands, credentials, sensitive configuration, and device-specific procedures remain in the relevant runbooks and repository documentation.

---

# Current Release

Version 1.6.0

Current Focus:
🔵 Home Assistant pilot — restore a Hue motion sensor and build the Hue-to-Lutron automation

Project Status:
🚧 Active — complete the defined programme before accepting elective new work

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

---

# Phase 2 — Enterprise Network ✅ CORE COMPLETE

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

# Phase 3 — HomeLab Dashboard ✅ CORE COMPLETE

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
- [x] Repair key-based OPNsense SSH login used by the HomeLab toolkit and validate non-interactive access
- [x] Add a dedicated SSH login key for the Frigate VM and validate the Homepage/toolkit launch path
- [x] Device Status
- [x] Backup Status
- [x] Resource Monitoring

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
- [ ] Scheduled lifecycle review: review IDrive e2 by 2027-08-11; Backblaze B2 remains the fallback option
- [x] Preserve the option to replace cloud storage with an S3-compatible off-site system hosted at a trusted remote location

Completion Gate:
At least one application and one VM/guest have been restored successfully, and essential backups have automated same-site and encrypted off-site protection.

Passed 2026-08-11: Homepage and a disposable LXC restore were validated; configuration and retained Proxmox guest archives now have automated same-site copies and client-side-encrypted IDrive e2 protection; initial, incremental and recovered-file integrity tests passed.

---

# Phase 5 — Monitoring

Operational Monitoring

- [x] Monitor OPNsense WAN availability and error-counter deltas
- [x] Monitor Arista link state, errors, temperature and PSU state
- [x] Monitor Proxmox resource and guest health
- [x] Monitor TrueNAS pool, NFS and bond health
- [x] Monitor both Pi-hole DNS endpoints through functional public, local and blocked-domain checks
- [x] Monitor Frigate service, NFS mount and recording freshness
- [x] Monitor backup success and age
- [ ] Send alerts only for actionable conditions
- [x] Deploy a bounded Beszel monitoring layer for Docker, Proxmox and Frigate
- [x] Add Beszel and a concise systems-up status widget to Homepage

Future Monitoring Platform

- [ ] Prometheus
- [ ] Grafana
- [ ] Alerting
- [ ] Historical Metrics
- [x] Pi-hole DNS redundancy and network-wide rollout

Completion Gate:
Failures in routing, storage, DNS, surveillance or backups are detected without manually checking every system.

---

# Phase 6 — Surveillance 🚧 PILOT OPERATIONAL

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
- [ ] Complete the planned Proxmox RAM upgrade if still required
- [ ] Create recovery checkpoints before passthrough or driver changes
- [x] Select the Frigate upgrade path — incoming E5-2698 v4 CPU, RAM and Coral M.2 TPU; remove the K620 during the same maintenance window
- [ ] Confirm Coral M.2 form-factor/adapter compatibility before installation
- [ ] Install and pass through the Coral TPU after creating recovery checkpoints
- [ ] Test Coral object-detection acceleration using the existing camera only
- [ ] Compare stability and resource use with the software baseline
- [x] Decide whether to retain or replace the K620 — remove it and use the Coral TPU for object detection
- [x] Evaluate object-detection acceleration separately from video decoding — retain CPU HEVC decode and use Coral for inference
- [ ] Establish safe camera and storage capacity
- [ ] Add further cameras one at a time with validation after each

Completion Gate:
No unexplained recording gaps, mount failures or resource exhaustion during observation; decoding/detection design is stable, measured, documented and sized for the intended camera count.

---

# Phase 7 — Home Assistant and Controlled IoT Migration

Design and Recovery

- [x] Define Home Assistant goals, required integrations and success criteria
- [x] Choose a supported deployment model and document why
- [x] Deploy a dedicated Home Assistant OS VM on Proxmox
- [x] Place Home Assistant on Servers VLAN 20, not Trusted or IoT
- [x] Define minimum-access cross-VLAN policy: only Home Assistant `192.168.20.11` may initiate TCP/UDP access to IoT VLAN 30; no unrestricted IoT-to-Servers access
- [x] Create OPNsense and Proxmox recovery checkpoints before deployment
- [ ] Define off-host Home Assistant backup retention and restore procedure before production migration

Pilot Deployment

- [x] Deploy Home Assistant OS 18.2 as Proxmox VM 103 with a DHCP reservation at `192.168.20.11`
- [x] Confirm current updates, DNS and `home-assistant.home.internal` local naming
- [x] Configure host-scoped firewall access from Home Assistant to IoT VLAN 30, ordered before the Servers RFC1918 block
- [ ] Enable only the specific cross-VLAN discovery mechanisms required
- [x] Validate administration from an approved Trusted device
- [ ] Confirm IoT devices still cannot initiate unrestricted internal access
- [x] Create an initial full backup named `Fresh HAOS installation`

Integration Sequence

- [x] Integrate one low-risk local system first — Philips Hue
- [x] Integrate Philips Hue and confirm its devices are present
- [x] Integrate Lutron Caséta at reserved address `192.168.30.102`; devices imported and local light control validated
- [ ] Integrate selected TVs, media devices, plugs, sensors and other supported IoT devices in small groups
- [ ] Preserve vendor applications where needed for firmware, recovery or unsupported functions
- [ ] Decide whether Apple Home should consume selected Home Assistant entities through HomeKit Bridge
- [ ] Avoid duplicate entities and competing automations across vendor apps, Apple Home and Home Assistant
- [ ] Move automations individually, validate them, then disable the superseded version
- [ ] Document unsupported, cloud-dependent or intentionally excluded devices

Operationalization

- [ ] Create a simple, maintainable dashboard for daily use
- [ ] Define household access without granting infrastructure administration
- [ ] Enable reliable automated backups and off-host copying
- [ ] Add Home Assistant health and backup-age monitoring
- [ ] Test VM reboot, Home Assistant restart and recovery from backup
- [ ] Document dependencies, firewall exceptions, integrations and rollback steps

Completion Gate:
Selected IoT devices are reliably controlled through Home Assistant, essential automations have a single authoritative owner, VLAN isolation remains effective, backups are off-host, and restart/restore testing passes.

Pilot automation criterion: create and test one automation in which a Philips Hue motion sensor triggers a non-essential Lutron light. Existing vendor-app automations are not imported; Home Assistant will become the sole automation authority as each automation is rebuilt and validated. Aqara water sensors, water shutoff and lock are excluded from this first pilot.

Restart point: both candidate Hue motion sensors are unreachable in the Hue app and Home Assistant. Replace/reseat their batteries, bring one close to the Hue bridge, reconnect it without resetting if possible, then use it to trigger the Lutron `Laundry Main lights`. Frigate camera entities and detection sensors are a later bounded integration requiring a shared MQTT broker and the Frigate Home Assistant integration; do not interrupt this pilot to deploy it.

---

# Phase 8 — Server VLAN 20 Migration

- [ ] Inventory each candidate service, dependency, port, client and DNS name
- [ ] Select a stateless or easily restored service as the first migration
- [ ] Verify backup and rollback before each move
- [ ] Add only the required firewall access
- [ ] Move one workload at a time
- [ ] Validate LAN and Tailscale access
- [ ] Observe each workload before starting another migration
- [ ] Update DNS, Homepage, inventories and diagrams after every move
- [ ] Defer TrueNAS and core DNS until the migration method is proven

Completion Gate:
Intended server workloads reside on VLAN 20 with documented minimum-access rules and tested recovery paths.

---

# Phase 9 — Management VLAN 50 Migration

- [ ] Define which administrator devices may access Management
- [ ] Document emergency console and lockout recovery procedures
- [ ] Confirm local console access before network changes
- [ ] Create explicit Trusted-to-Management access rules
- [ ] Migrate one secondary management endpoint first
- [ ] Validate DNS, HTTPS, SSH, routing and rollback
- [ ] Migrate core management interfaces individually
- [ ] Keep VLAN 10 available until the new management path is proven
- [ ] Add Tailscale routing and policy only if remote management is required
- [ ] Update all inventories and recovery documentation

Completion Gate:
Management interfaces are isolated on VLAN 50, reachable only from approved administrator devices, with a tested lockout-recovery path.

---

# Phase 10 — Automation

- [ ] Nightly Backups
- [ ] Configuration Drift Detection
- [ ] Automatic Reports
- [ ] Certificate Monitoring

---

# Phase 11 — Final Consolidation and Project Review

Documentation Reconciliation

- [x] Update repository documentation for the secondary Pi-hole
- [ ] Clarify which TrueNAS applications are already operational versus future work
- [ ] Remove or annotate stale switch-port and historical planning references
- [ ] Record the installed Proxmox RAM after any upgrade
- [ ] Confirm the live inventory, addresses, VLANs and service locations
- [ ] Record a fresh known-good stability checkpoint
- [ ] Update the changelog and project release after reconciliation

Final Review

- [ ] Confirm every earlier phase completion gate
- [ ] Resolve outdated roadmap entries
- [ ] Review firewall aliases, rules and temporary exceptions
- [ ] Remove unused test configurations after confirming they are no longer needed
- [ ] Confirm monitoring, backup and restore coverage for every critical service
- [ ] Review architecture decisions and document remaining accepted risks
- [ ] Publish an updated network diagram and current-state baseline
- [ ] Update the changelog and tag a consolidated release
- [ ] Review whether the scope lock can be lifted

Completion Gate:
The handover, roadmap, baseline and live environment agree, and the environment is documented, monitored, recoverable, segmented and stable enough to consider a new roadmap.

---

# Deferred Projects

## Forgejo

- [ ] Deploy Forgejo
- [ ] Migrate HomeLab Repository
- [ ] SSH Authentication
- [ ] Daily Backup

## Local AI / GPU Acceleration

- [ ] Evaluate local LLM deployment on Proxmox after the current project concludes
- [ ] Evaluate NVIDIA Tesla P40 24 GB as the value-oriented GPU option
- [ ] Verify Dell Precision 5810 PCIe clearance, PSU capacity and GPU power connections before purchase
- [ ] Design active cooling/airflow for a passively cooled datacenter GPU
- [ ] Test local model performance with the planned 48 GB system RAM
- [ ] Keep Frigate object detection on a dedicated TPU/accelerator where practical, reserving GPU capacity for local AI and advanced Frigate workloads

## Other Deferred Work

- Kubernetes Lab
- PXE Boot Server
- Internal Certificate Authority
- IPv6 rollout
- New broad security-tooling platforms
- Additional dashboards or observability platforms beyond the monitoring phase
- New self-hosted services not required by this roadmap
- Major network redesign or VLAN renumbering

---

# Future Services

- Jellyfin
- Immich
- Paperless-ngx
- Wiki

---

# Future Ideas

- UPS Integration
- Remote Environmental Sensors
- Evaluate Tailscale Services after the current project is complete: pilot stable MagicDNS/TailVIP names and service-level grants for a small set of internal web services such as Homepage, Home Assistant and Frigate; compare against existing device MagicDNS and subnet routing before wider adoption; keep access tailnet-only with no Funnel or public exposure

---

# Recommended Execution Order

1. Restore one Hue motion sensor, complete the Hue-to-Lutron pilot and migrate IoT control gradually.
2. Complete the planned RAM/CPU/Coral maintenance, remove the K620 and validate Frigate against its baseline.
3. Let Beszel collect a 24-hour baseline, then configure actionable-condition alerts.
4. Migrate selected services to VLAN 20.
5. Migrate management systems to VLAN 50.
6. Complete the listed automation work.
7. Reconcile and consolidate documentation, remove temporary exceptions and review the scope lock.

---

# Change Log

| Date | Change | Evidence or Reference |
|---|---|---|
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
