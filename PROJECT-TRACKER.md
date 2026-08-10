# Project Mini Atlas — Completion Tracker

**Tracker version:** 1.0  
**Created:** 2026-08-09  
**Current documented release:** 1.3.0  
**Status:** Active — complete the defined programme before accepting elective new work

## How to use this tracker

- This is the project-level source of truth for completed work and remaining milestones.
- Check an item only after it has been implemented, validated, documented, and backed up where applicable.
- Update the date and change log whenever milestones are completed.
- Detailed commands, credentials, and sensitive configuration do not belong in this file.
- Repository documentation and device-specific runbooks remain the authority for implementation details.

## Scope lock

Until the remaining milestones in this tracker are complete:

- Do not add elective platforms, services, VLANs, or major infrastructure projects.
- New work must either complete a listed milestone, resolve an urgent reliability or security issue, or be required to keep an existing service operational.
- Record urgent unplanned work in the change log, including why it could not wait.
- Add cameras only within the defined surveillance milestone and only after capacity has been validated.
- Review the scope lock only after all completion gates at the end of this document pass.

## Completed foundation

### Core infrastructure

- [x] OPNsense firewall and routing platform deployed
- [x] Arista 10 GbE Layer 2 core deployed
- [x] Proxmox virtualization host deployed
- [x] TrueNAS and Synology storage systems deployed
- [x] UniFi control plane, PoE switch, and wireless infrastructure deployed
- [x] Rack, device inventory, addressing, and important switch paths documented
- [x] GitHub documentation repository and HomeLab toolkit established
- [x] SSH key authentication and infrastructure health tooling established

### Stability and resilience

- [x] WAN physical instability diagnosed and faulty cable replaced
- [x] OPNsense WAN RX descriptor tuning validated at 4096
- [x] Post-change WAN load and packet-loss tests passed
- [x] TrueNAS active-backup bond configured and failover/failback tested
- [x] Recovery checkpoints created for core infrastructure

### Network segmentation

- [x] VLANs 20, 30, 40, 50, 60, and 70 routed through OPNsense
- [x] DHCP scopes and baseline firewall policies deployed
- [x] Arista trunks configured for OPNsense, UniFi, and Proxmox
- [x] IoT VLAN 30 migrated into production
- [x] Guest VLAN 40 migrated into production and isolated
- [x] Cameras VLAN 60 migrated into production
- [x] Selective Trusted-to-IoT mDNS discovery validated
- [x] Philips Hue, Lutron, Apple Home, and representative IoT functions validated

### Core services and access

- [x] Homepage dashboard deployed at `home.internal`
- [x] Infrastructure, application, Frigate, and SSH links added
- [x] Two Pi-hole instances operational
- [x] Public, blocked-domain, and local-domain DNS resolution validated
- [x] Tailscale subnet access restricted to the administrator identity
- [x] Remote web and SSH administration validated without inbound WAN ports

### Surveillance pilot

- [x] Frigate VM 102 deployed on Servers VLAN 20
- [x] Reolink camera isolated on Cameras VLAN 60
- [x] Frigate-to-camera access limited to TCP 80, 554, and 8000
- [x] Main and detection streams configured and continuous recording validated
- [x] TrueNAS NFS recording storage configured
- [x] Reboot-safe NFS and Frigate startup ordering validated
- [x] Private checksum-verified Frigate configuration backup created

### Backup and documentation foundation

- [x] Configuration backups exist for OPNsense, UniFi, Arista, TrueNAS, Homepage, Pi-hole, Tailscale, Proxmox guests, and Frigate
- [x] Proxmox backup schedules consolidated with retention configured
- [x] A checksum-verified recovery set was copied to the backup Synology
- [x] Current baseline, roadmap, surveillance runbook, and changelog documented through release 1.3.0

## Remaining programme

### Milestone 1 — Reconcile documentation and establish a fresh baseline

- [ ] Update repository documentation for the secondary Pi-hole
- [ ] Clarify which TrueNAS applications are already operational versus future work
- [ ] Remove or annotate stale switch-port and historical planning references
- [ ] Record the installed Proxmox RAM after any upgrade
- [ ] Confirm the live inventory, addresses, VLANs, and service locations
- [ ] Record a fresh known-good stability checkpoint
- [ ] Update the changelog and project release after reconciliation

**Completion gate:** The handover, tracker, baseline, roadmap, and live environment agree.

### Milestone 2 — Observe Frigate and NFS stability

- [ ] Observe Frigate health and recording continuity over an agreed period
- [ ] Confirm the NFS mount remains stable across normal operation
- [ ] Confirm recording retention removes data as expected
- [ ] Measure storage growth and estimate capacity per camera
- [ ] Record CPU, memory, decode, and detection baselines
- [ ] Document any incidents and their resolution

**Completion gate:** No unexplained recording gaps, mount failures, or resource exhaustion during the observation period.

### Milestone 3 — Prove recovery and improve backup handling

- [ ] Restore-test one low-risk service such as Homepage or Pi-hole
- [ ] Restore-test a disposable Proxmox guest backup
- [ ] Document recovery steps, results, and approximate recovery time
- [ ] Define configuration-backup retention
- [ ] Automate copying recovery sets to the backup Synology
- [ ] Add backup-age or backup-failure notification
- [ ] Establish an encrypted off-site copy for essential recovery material
- [ ] Confirm sensitive camera and infrastructure credentials remain outside Git

**Completion gate:** At least one application and one VM/guest have been restored successfully, and essential backups have automated same-site and encrypted off-site protection.

### Milestone 4 — Add lightweight operational monitoring

- [ ] Monitor OPNsense WAN availability and error-counter deltas
- [ ] Monitor Arista link state, errors, temperature, and PSU state
- [ ] Monitor Proxmox resource and guest health
- [ ] Monitor TrueNAS pool, NFS, and bond health
- [ ] Monitor both Pi-hole DNS endpoints
- [ ] Monitor Frigate container health and recording freshness
- [ ] Monitor backup success and age
- [ ] Send alerts only for actionable conditions
- [ ] Add a concise status summary to Homepage

**Completion gate:** Failures in routing, storage, DNS, surveillance, or backups are detected without manually checking every system.

### Milestone 5 — Validate Lab VLAN 70

- [ ] Create a pre-change recovery checkpoint
- [ ] Deploy a disposable Proxmox test VM tagged for VLAN 70
- [ ] Validate DHCP, DNS, and intended Internet access
- [ ] Confirm access to protected internal VLANs is blocked
- [ ] Confirm explicitly permitted administrator access works
- [ ] Inspect firewall logs during validation
- [ ] Document results and rollback
- [ ] Remove the VM or retain it as a documented test appliance

**Completion gate:** VLAN 70 isolation and administrator access behave exactly as documented.

### Milestone 6 — Home Assistant and controlled IoT migration

Home Assistant will become the preferred local control and automation layer. Existing IoT devices remain on isolated VLAN 30; “migration” means bringing their supported control, automations, and dashboards into Home Assistant without weakening network isolation or breaking vendor/Apple Home functionality prematurely.

#### Design and recovery

- [ ] Define the Home Assistant goals, required integrations, and success criteria
- [ ] Choose a supported deployment model and document why
- [ ] Prefer a dedicated Home Assistant OS VM on Proxmox unless testing identifies a better fit
- [ ] Place Home Assistant on Servers VLAN 20, not Trusted or IoT
- [ ] Document required Trusted, IoT, DNS, NTP, and Internet flows before deployment
- [ ] Create OPNsense, Proxmox, and relevant application recovery checkpoints
- [ ] Define Home Assistant backup and restore procedures before production migration

#### Pilot deployment

- [ ] Deploy Home Assistant with a fixed address or DHCP reservation
- [ ] Apply updates and configure time, DNS, and local naming
- [ ] Configure narrowly scoped firewall access between Home Assistant and required IoT endpoints
- [ ] Enable only the specific cross-VLAN discovery mechanisms required
- [ ] Validate administration from approved Trusted devices
- [ ] Confirm IoT devices still cannot initiate unrestricted internal access
- [ ] Create and test an initial Home Assistant backup

#### Integration sequence

- [ ] Integrate one low-risk test device or service first
- [ ] Integrate Philips Hue and validate lights, rooms, scenes, and local control
- [ ] Integrate Lutron and validate lights, scenes, and local control
- [ ] Integrate selected TVs, media devices, plugs, sensors, and other supported IoT devices in small groups
- [ ] Preserve vendor applications where needed for firmware, recovery, or unsupported functions
- [ ] Decide whether Apple Home should consume selected Home Assistant entities through HomeKit Bridge
- [ ] Avoid duplicate entities and competing automations across vendor apps, Apple Home, and Home Assistant
- [ ] Move automations individually, validate them, then disable the superseded version
- [ ] Document unsupported, cloud-dependent, or intentionally excluded devices

#### Operationalization

- [ ] Create a simple, maintainable dashboard for daily use
- [ ] Define household access without granting infrastructure administration
- [ ] Enable reliable automated backups and off-host copying
- [ ] Add Home Assistant health and backup-age monitoring
- [ ] Test VM reboot, Home Assistant restart, and recovery from backup
- [ ] Document dependencies, firewall exceptions, integrations, and rollback steps

**Completion gate:** Selected IoT devices are reliably controlled through Home Assistant, essential automations have a single authoritative owner, VLAN isolation remains effective, backups are off-host, and restart/restore testing passes.

### Milestone 7 — Evaluate Frigate hardware acceleration and camera capacity

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

**Completion gate:** The decoding and detection design is stable, measured, documented, and sized for the intended camera count.

### Milestone 8 — Migrate selected servers to VLAN 20

- [ ] Inventory each candidate service, dependency, port, client, and DNS name
- [ ] Select a stateless or easily restored service as the first migration
- [ ] Verify backup and rollback before each move
- [ ] Add only the required firewall access
- [ ] Move one workload at a time
- [ ] Validate LAN and Tailscale access
- [ ] Observe each workload before starting another migration
- [ ] Update DNS, Homepage, inventories, and diagrams after every move
- [ ] Defer TrueNAS and core DNS until the migration method is proven

**Completion gate:** Intended server workloads reside on VLAN 20 with documented minimum-access rules and tested recovery paths.

### Milestone 9 — Migrate management systems to VLAN 50

- [ ] Define which administrator devices may access Management
- [ ] Document emergency console and lockout recovery procedures
- [ ] Confirm local console access before network changes
- [ ] Create explicit Trusted-to-Management access rules
- [ ] Migrate one secondary management endpoint first
- [ ] Validate DNS, HTTPS, SSH, routing, and rollback
- [ ] Migrate core management interfaces individually
- [ ] Keep VLAN 10 available until the new management path is proven
- [ ] Add Tailscale routing and policy only if remote management is required
- [ ] Update all inventories and recovery documentation

**Completion gate:** Management interfaces are isolated on VLAN 50, reachable only from approved administrator devices, with a tested lockout-recovery path.

### Milestone 10 — Deploy Pi-hole DNS network-wide

The two Pi-hole instances must first demonstrate stable, independent operation. Network-wide deployment will happen only after the preceding milestones are complete so DNS changes do not overlap with other infrastructure migrations.

- [ ] Confirm both Pi-hole instances have remained stable during the observation period
- [ ] Confirm both resolve public domains, block test domains, and resolve `home.internal`
- [ ] Confirm local-domain and reverse-DNS forwarding to OPNsense works on both instances
- [ ] Confirm both Pi-hole instances have current, independently restorable backups
- [ ] Test client behavior with the primary Pi-hole unavailable
- [ ] Test client behavior with the secondary Pi-hole unavailable
- [ ] Record current OPNsense DHCP and DNS settings and prepare a rollback checkpoint
- [ ] Define which VLANs will receive Pi-hole DNS and whether any require different policy
- [ ] Confirm OPNsense firewall rules allow only the required client-to-Pi-hole DNS traffic
- [ ] Deploy both Pi-hole addresses through DHCP to one low-risk VLAN or client group first
- [ ] Renew pilot-client leases and validate DNS, blocking, local names, and Internet access
- [ ] Observe the pilot before expanding deployment
- [ ] Roll out to the remaining approved VLANs one at a time
- [ ] Verify clients are actually using the intended Pi-hole endpoints
- [ ] Confirm isolated VLAN policy and Guest Internet-only behavior remain effective
- [ ] Add Pi-hole health, DNS availability, and backup-age monitoring
- [ ] Document failure handling, rollback, DHCP settings, and the final DNS path

**Completion gate:** Approved networks use both Pi-hole endpoints, normal and single-instance-failure tests pass, local DNS continues to work, VLAN isolation is unchanged, and rollback is documented.

### Milestone 11 — Final consolidation and project review

- [ ] Confirm every earlier milestone completion gate
- [ ] Resolve outdated roadmap entries
- [ ] Review firewall aliases, rules, and temporary exceptions
- [ ] Remove unused test configurations after confirming they are no longer needed
- [ ] Confirm monitoring, backup, and restore coverage for every critical service
- [ ] Review architecture decisions and document remaining accepted risks
- [ ] Publish an updated network diagram and current-state baseline
- [ ] Update the changelog and tag a consolidated release
- [ ] Review whether the scope lock can be lifted

**Completion gate:** The environment is documented, monitored, recoverable, segmented, and stable enough to consider a new roadmap.

## Deferred until the completion gates pass

- Forgejo deployment and GitHub migration
- Kubernetes lab
- PXE boot platform
- Internal certificate authority
- IPv6 rollout
- New broad security-tooling platforms
- Additional dashboards or observability platforms beyond the monitoring milestone
- New self-hosted services not required by this tracker
- Major network redesign or VLAN renumbering

## Recommended execution order

1. Reconcile documentation and establish a fresh baseline.
2. Observe Frigate and NFS stability.
3. Complete practical restore tests and improve backup handling.
4. Add lightweight operational monitoring.
5. Validate VLAN 70 with a disposable VM.
6. Deploy Home Assistant and migrate IoT control gradually.
7. Evaluate Frigate acceleration and camera capacity.
8. Migrate selected services to VLAN 20.
9. Migrate management systems to VLAN 50.
10. Deploy Pi-hole DNS network-wide after staged resilience testing.
11. Consolidate documentation, remove temporary exceptions, and review the scope lock.

## Change log

| Date | Change | Evidence or reference |
|---|---|---|
| 2026-08-10 | Added staged network-wide Pi-hole deployment after the existing implementation milestones and before final consolidation. | User-confirmed deferred deployment following the Pi-hole stability observation period |
| 2026-08-09 | Created consolidated completion tracker and scope lock; added Home Assistant and controlled IoT migration milestone. | Handover, repository baseline, roadmap, surveillance runbook, and changelog through 1.3.0 |
