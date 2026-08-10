# Jason's HomeLab Roadmap

> Last Updated: 2026-08-10
>
> **Document of Truth:** This file is the project-level source of truth for completed work, active milestones, deferred projects, and execution order. Detailed commands, credentials, sensitive configuration, and device-specific procedures remain in the relevant runbooks and repository documentation.

---

# Current Release

Version 1.3.0

Current Focus:
🔵 Backup Resilience — automated same-site copies, restore testing, and encrypted off-site backup

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

Remaining Validation — Lab VLAN 70

- [ ] Create a pre-change recovery checkpoint
- [ ] Deploy a disposable Proxmox test VM tagged for VLAN 70
- [ ] Validate DHCP, DNS and intended Internet access
- [ ] Confirm access to protected internal VLANs is blocked
- [ ] Confirm explicitly permitted administrator access works
- [ ] Inspect firewall logs during validation
- [ ] Document results and rollback
- [ ] Remove the VM or retain it as a documented test appliance

Completion Gate:
VLAN 70 isolation and administrator access behave exactly as documented.

---

# Phase 3 — HomeLab Dashboard ✅ CORE COMPLETE

- [x] Homepage deployed
- [x] Internal `home.internal` DNS name
- [x] Quick links to infrastructure and applications
- [x] SSH launch links for Proxmox, Docker LXC, OPNsense and TrueNAS
- [x] Pi-hole dashboard tile and DNS-filtering pilot
- [x] Two Pi-hole instances operational
- [x] Public, blocked-domain and local-domain DNS resolution validated
- [x] Private remote access through Tailscale
- [x] Tailscale subnet access restricted to the administrator identity
- [x] Remote web and SSH administration validated without inbound WAN ports
- [x] Frigate dashboard and SSH launch links
- [ ] Device Status
- [ ] Backup Status
- [ ] Resource Monitoring

---

# Phase 4 — Backup Resilience 🚧 CURRENT

Existing Foundation

- [x] Configuration backups exist for OPNsense, UniFi, Arista, TrueNAS, Homepage, Pi-hole, Tailscale, Proxmox guests and Frigate
- [x] Proxmox backup schedules consolidated with retention configured
- [x] Checksum-verified recovery set copied to backup Synology
- [x] Current baseline, roadmap, surveillance runbook and changelog documented through release 1.3.0

Recovery Validation

- [x] Restore-test one low-risk service such as Homepage or Pi-hole — Homepage validated 2026-08-10
- [x] Restore-test a disposable Proxmox guest backup — LXC 101 restored offline as temporary guest 901 on 2026-08-10
- [ ] Document recovery steps, results and approximate recovery time
- [ ] Define configuration-backup retention
- [ ] Confirm sensitive camera and infrastructure credentials remain outside Git

Automation and Same-Site Protection

- [ ] Automate copying recovery sets to the backup Synology
- [ ] Add backup-age or backup-failure notification

Encrypted Off-Site Backup

- [ ] Establish encrypted off-site protection for essential system/recovery material only — media excluded
- [ ] Use S3-compatible object storage as the preferred protocol
- [ ] Initial cloud target: IDrive e2 S3-compatible storage
- [ ] Planning assumption: approximately 500 GB off-site capacity
- [ ] Define practical snapshot/version retention before production rollout
- [ ] Validate initial upload, incremental backup, encryption and restore
- [ ] Document provider configuration and recovery procedure without storing credentials in Git
- [ ] Review IDrive e2 after the first year; Backblaze B2 remains the fallback option
- [ ] Preserve the option to replace cloud storage with an S3-compatible off-site system hosted at a trusted remote location

Completion Gate:
At least one application and one VM/guest have been restored successfully, and essential backups have automated same-site and encrypted off-site protection.

---

# Phase 5 — Monitoring

Operational Monitoring

- [ ] Monitor OPNsense WAN availability and error-counter deltas
- [ ] Monitor Arista link state, errors, temperature and PSU state
- [ ] Monitor Proxmox resource and guest health
- [ ] Monitor TrueNAS pool, NFS and bond health
- [ ] Monitor both Pi-hole DNS endpoints
- [ ] Monitor Frigate container health and recording freshness
- [ ] Monitor backup success and age
- [ ] Send alerts only for actionable conditions
- [ ] Add a concise status summary to Homepage

Future Monitoring Platform

- [ ] Prometheus
- [ ] Grafana
- [ ] Alerting
- [ ] Historical Metrics
- [ ] Pi-hole DNS redundancy and network-wide rollout

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

- [ ] Observe Frigate health and recording continuity over an agreed period
- [ ] Confirm the NFS mount remains stable across normal operation
- [ ] Confirm recording retention removes data as expected
- [ ] Measure storage growth and estimate capacity per camera
- [ ] Record CPU, memory, decode and detection baselines
- [ ] Document any incidents and their resolution

Hardware Acceleration and Expansion

- [ ] Confirm Quadro K620 capabilities and current driver compatibility
- [ ] Compare those capabilities with Frigate's current stream formats
- [ ] Decide whether K620 passthrough is worth the complexity
- [ ] Complete the planned Proxmox RAM upgrade if still required
- [ ] Create recovery checkpoints before passthrough or driver changes
- [ ] Test acceleration using the existing camera only
- [ ] Compare stability and resource use with the software baseline
- [ ] Decide whether to retain or replace the K620
- [ ] Evaluate object-detection acceleration separately from video decoding
- [ ] Establish safe camera and storage capacity
- [ ] Add further cameras one at a time with validation after each

Completion Gate:
No unexplained recording gaps, mount failures or resource exhaustion during observation; decoding/detection design is stable, measured, documented and sized for the intended camera count.

---

# Phase 7 — Home Assistant and Controlled IoT Migration

Design and Recovery

- [ ] Define Home Assistant goals, required integrations and success criteria
- [ ] Choose a supported deployment model and document why
- [ ] Prefer a dedicated Home Assistant OS VM on Proxmox unless testing identifies a better fit
- [ ] Place Home Assistant on Servers VLAN 20, not Trusted or IoT
- [ ] Document required Trusted, IoT, DNS, NTP and Internet flows before deployment
- [ ] Create OPNsense, Proxmox and relevant application recovery checkpoints
- [ ] Define Home Assistant backup and restore procedures before production migration

Pilot Deployment

- [ ] Deploy Home Assistant with a fixed address or DHCP reservation
- [ ] Apply updates and configure time, DNS and local naming
- [ ] Configure narrowly scoped firewall access between Home Assistant and required IoT endpoints
- [ ] Enable only the specific cross-VLAN discovery mechanisms required
- [ ] Validate administration from approved Trusted devices
- [ ] Confirm IoT devices still cannot initiate unrestricted internal access
- [ ] Create and test an initial Home Assistant backup

Integration Sequence

- [ ] Integrate one low-risk test device or service first
- [ ] Integrate Philips Hue and validate lights, rooms, scenes and local control
- [ ] Integrate Lutron and validate lights, scenes and local control
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

- [ ] Update repository documentation for the secondary Pi-hole
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

---

# Recommended Execution Order

1. Complete backup resilience: restore tests, automated Synology copy and encrypted IDrive e2 off-site backup.
2. Observe Frigate and NFS stability.
3. Add lightweight operational monitoring.
4. Validate VLAN 70 with a disposable VM.
5. Deploy Home Assistant and migrate IoT control gradually.
6. Evaluate Frigate acceleration and camera capacity.
7. Migrate selected services to VLAN 20.
8. Migrate management systems to VLAN 50.
9. Complete automation work.
10. Reconcile and consolidate documentation, remove temporary exceptions and review the scope lock.

---

# Change Log

| Date | Change | Evidence or Reference |
|---|---|---|
| 2026-08-10 | Completed disposable Proxmox guest restore test: verified the newest LXC 101 archive, restored it as stopped guest 901 with isolated networking, validated the recovered filesystem offline, then removed the guest and temporary disk. | `vzdump-lxc-101-2026_08_10-02_30_36.tar.zst`; production LXC 101 remained running and unchanged |
| 2026-08-10 | Completed isolated Homepage restore test from the checksum-verified Synology archive; restored configuration produced a healthy temporary container and HTTP 200, then all test resources were removed. | `homepage-config-20260808-162831.tgz`; production Homepage remained online and unchanged |
| 2026-08-09 | Created consolidated completion tracker and scope lock; added Home Assistant and controlled IoT migration milestone. | Handover, repository baseline, roadmap, surveillance runbook and changelog through 1.3.0 |
| 2026-08-10 | Consolidated PROJECT-TRACKER.md into PROJECTS.md; retained PROJECTS.md roadmap formatting and established it as the single project-level document of truth. | PROJECTS.md and PROJECT-TRACKER.md reconciliation |
| 2026-08-10 | Set backup resilience as current focus; added encrypted off-site S3 plan using IDrive e2, approximately 500 GB planning capacity, with Backblaze B2 fallback and remote self-hosted S3 retained as an option. | Backup planning discussion |
