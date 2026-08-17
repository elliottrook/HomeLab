# Jason's HomeLab Roadmap

> Last Updated: 2026-08-16
>
> **Document of Truth:** This file is the project-level source of truth for completed work, active milestones, deferred projects, and execution order. Detailed commands, credentials, sensitive configuration, and device-specific procedures remain in the relevant runbooks and repository documentation.

---

# Current Release

Version 1.6.0

Current Focus:
🔵 Complete the planned Proxmox CPU/RAM and Coral TPU maintenance, then begin the audited Phase 9 management-migration sequence

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

Future Monitoring Platform

- [ ] Prometheus
- [ ] Grafana
- [ ] Alerting
- [ ] Historical Metrics
- [x] Pi-hole DNS redundancy and network-wide rollout

Completion Gate:
Failures in routing, storage, DNS, surveillance or backups are detected without manually checking every system.

**Phase 5 complete 2026-08-15.** HomeLab Doctor provides functional infrastructure checks, Beszel supplies lightweight host/container metrics with sustained actionable alerts, and Homepage provides the concise daily status view. Prometheus, Grafana and their long-term metrics/alerting stack remain explicitly deferred future enhancements and are not Phase 5 completion dependencies.

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
- [x] Confirm Coral M.2 form-factor/adapter compatibility before installation — single Edge TPU `G650-04527-01`, M.2 2230 A+E key, PCIe Gen2 x1; compatible PCIe x1 E-key carrier selected
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

# Phase 8 — Server VLAN 20 Migration

Audit completed 2026-08-14; UniFi migration completed 2026-08-16:

- Frigate VM 102 and Home Assistant VM 103 already prove the VLAN 20 workload pattern, minimum-access firewall policy and rollback method.
- Docker LXC 100 completed its controlled migration on 2026-08-15 from Trusted `192.168.1.20` to Servers `192.168.20.20`. Its Homepage, Portainer, primary Pi-hole, Tailscale and Beszel workloads returned healthy; local and cellular/Tailscale tests passed. A fresh verified backup and explicit rollback copies preceded the move.
- Tailscale now advertises Trusted and Servers, with identity-specific access to both. A host-scoped rule permits only the subnet-router host to reach Trusted; the general Servers isolation rules remain in force.
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

# Phase 9 — Management VLAN 50 Migration

Audit completed 2026-08-14; UniFi migration completed 2026-08-16:

- Planned addresses remain Arista `.50.2` and Proxmox `.50.10`. Deployed UniFi addresses are controller `.50.21`, PoE switch `.50.30`, Hall AP `.50.31` and Office AP `.50.141`.
- The `MGMT_ADMIN_HOSTS` alias contains Jason's Mac mini (`192.168.1.206`), Mac laptop (`192.168.1.241`) and iPhone (`192.168.1.112`). Other Trusted clients are explicitly blocked from Management.
- Console recovery for OPNsense, Arista and Proxmox must be confirmed before the first address change.
- UniFi LXC 101 and all three managed devices were migrated first. Proxmox remains next and Arista remains last. VLAN 10 stays available throughout validation.
- The Proxmox-facing Arista trunk now carries tagged VLAN 50 and LXC 101 uses it in production. Tailscale currently advertises Trusted `192.168.1.0/24` and Servers `192.168.20.0/24`; Management remote access is a later explicit policy decision, not part of the local pilot.

- [x] Define which administrator devices may access Management
- [x] Document emergency console and lockout recovery procedures
- [x] Confirm local console access before network changes
- [x] Create explicit Trusted-to-Management access rules
- [x] Migrate one secondary management endpoint first
- [x] Validate DNS, HTTPS, SSH, routing and rollback
- [ ] Migrate core management interfaces individually
- [x] Keep VLAN 10 available until the new management path is proven
- [ ] Add Tailscale routing and policy only if remote management is required
- [x] Update inventories and recovery documentation for the completed UniFi migration

**UniFi migration complete 2026-08-16.** LXC 101 moved to `192.168.50.21`; the PoE switch, Hall AP and Office AP moved to `192.168.50.30`, `.31` and `.141`. All three devices remained online after address changes. The controller's temporary Trusted interface, disposable VLAN test containers, legacy-device alias and temporary firewall exceptions were removed after validation. Phase 9 remains open for the separate Proxmox and Arista management migrations.

Completion Gate:
Management interfaces are isolated on VLAN 50, reachable only from approved administrator devices, with a tested lockout-recovery path.

---

# Phase 10 — Automation

- [x] Nightly Backups — automated configuration pulls, Proxmox guest archives, Home Assistant native backups and encrypted off-site protection are operational
- [ ] Configuration Drift Detection
- [ ] Automatic Reports
- [ ] Certificate Monitoring

Audit completed 2026-08-14: keep this phase bounded. Use the existing `lab doctor` result as the basis for failure-only scheduled reporting, compare protected infrastructure exports with the prior known-good set for drift, and monitor certificate expiry only where expiry has an operational consequence. Do not build a second general monitoring platform here.

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

## Synology Drive Family Cloud

- [ ] Reactivate and pilot Synology Drive on the existing primary Synology after the current roadmap and VLAN migrations are complete
- [ ] Confirm current Synology Drive Server and client versions before configuration; use macOS client 4.1 or later
- [ ] Provide individual DSM accounts and private `My Drive` storage for family members
- [ ] Create only the required shared family Team Folders with explicit group permissions
- [ ] Configure macOS On-demand Sync so Synology Drive appears as a live Finder location without downloading every file
- [ ] Test iPhone/iPad access, automatic photo and video upload, offline pinning and two-way synchronization
- [ ] Validate password-protected and expiring share links and file-request links for friends who do not have accounts
- [ ] Use HTTPS in transit and a dedicated encrypted DSM shared folder where compatible; document that this is not client-side or zero-knowledge encryption
- [ ] Select a safe external-sharing method without broadly exposing DSM; retain Tailscale for private family administration and access where practical
- [ ] Set conservative version retention and monitor capacity on both Synology systems
- [ ] Prove Synology Drive data, configuration, version recovery and deleted-file recovery through Hyper Backup before production use
- [ ] Keep the scope limited to simple file sync, sharing, encryption and mobile access; do not enable collaboration-suite features without a later decision
- [ ] Retain Seafile Community Edition only as a fallback if Synology Drive fails a defined encryption, sharing or client requirement

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

1. Complete the staged RAM/CPU maintenance and remove the K620. The first 2 x 16 GB ECC RDIMM stage passed a two-loop 24 GB `memtester` validation; the second matching pair and CPU remain pending.
2. Install the selected PCIe x1 A+E-key carrier and Coral TPU during the planned maintenance window, then validate one camera against the software baseline.
3. Migrate management systems to VLAN 50 only after local-console and trunk prerequisites pass.
4. Complete the bounded drift, reporting and certificate automation work.
5. Reconcile and consolidate documentation, remove temporary exceptions and review the scope lock.

---

# Change Log

| Date | Change | Evidence or Reference |
|---|---|---|
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
