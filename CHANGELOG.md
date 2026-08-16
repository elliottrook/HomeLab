# Changelog

## v1.6.0

### Added
- Deployed Home Assistant OS 18.2 as Proxmox VM 103 on Servers VLAN 20
- Reserved `192.168.20.11` and published `home-assistant.home.internal`
- Created the initial full Home Assistant recovery point before integrations
- Integrated the Philips Hue bridge using HA-specific TCP 80 and 443 firewall rules
- Integrated Lutron Caséta at reserved address `192.168.30.102` and validated local control of imported devices
- Deployed Beszel 0.18.7 for Docker, Proxmox and Frigate with a Homepage systems-up widget
- Added functional HomeLab Doctor checks for OPNsense WAN counters, Arista links and hardware, Proxmox guests/resources, TrueNAS pools/NFS/bond, Frigate recording freshness and reported backup results
- Added failure-result reporting from the Synology configuration and Proxmox archive pull tasks
- Added encrypted daily Home Assistant native backups to local and dedicated Backup Synology storage
- Added VM 103 to checksum-verified Proxmox archive mirroring and HomeLab Doctor guest/backup-age checks
- Added the Aqara M3 through Matter with six active water sensors, the shutoff valve and lock
- Added a minimal mDNS relay across LAN, Servers and IoT plus a host-scoped Trusted-media exception for five Apple TVs
- Created and validated the Hue Hall motion-to-Lutron `Laundry Main Lights` pilot automation
- Created a simple Home Assistant Overview and a validated local non-administrator household account
- Installed HACS and validated the community-store workflow without adding an elective repository
- Expanded the Laundry pilot with the `Laundry bright` scene, `Laundry motion lighting` script, five-minute occupancy timer and timer-finished light-off automation
- Configured sustained actionable Beszel alerts for Docker, Proxmox and Frigate with verified iCloud SMTP delivery
- Added audited execution orders and rollback boundaries for the remaining Server VLAN 20 and Management VLAN 50 migrations
- Added a domain-filtered HomeKit Bridge as the Apple Home/Siri presentation layer and validated live Siri control while retaining Home Assistant as the sole automation authority
- Documented the completed Server VLAN 20 migration and its dependency/rollback validation

### Changed
- Migrated Docker LXC 100 from Trusted `192.168.1.20` to Servers VLAN 20 at `192.168.20.20`, including Homepage, Portainer, primary Pi-hole, Tailscale and Beszel
- Updated OPNsense DHCP option 6 and `home.internal`, the Pi-hole resolver alias, Homepage links, service inventories and the Mac SSH alias for the new address
- Extended the Tailscale subnet router and identity-specific policy to cover both Trusted `192.168.1.0/24` and Servers `192.168.20.0/24`
- Migrated the main Synology from `192.168.1.41` to `192.168.20.41` and the Backup Synology from `192.168.1.42` to `192.168.20.42`
- Migrated TrueNAS and its secondary Pi-hole from `192.168.1.40` to `192.168.20.40`; updated Frigate NFS, DHCP DNS, aliases, Homepage, SSH and operational inventories

### Validated
- Formally closed Phase 5 Monitoring and Phase 7 Home Assistant/Controlled IoT Migration after their completion gates passed; Prometheus/Grafana remain deferred and Phase 6 remains open for the Coral TPU work
- Fully tested VLAN 70 with disposable Proxmox LXC 970: DHCP, redundant Pi-hole DNS, blocking and Internet access passed; internal application endpoints remained isolated
- Corrected the OPNsense VLAN 70 parent from `igb0` to the active `ix0` trunk and repeated the validation successfully
- Confirmed Frigate's current HEVC 5120x1552 stream, approximately 24 GB/day recording growth and stable NFS recording flow
- Confirmed the Quadro K620 is not worthwhile for the current Frigate workload; it will be removed during the planned CPU/Coral maintenance
- Verified Frigate retention beyond the configured 3-day continuous window
- Selected the incoming E5-2698 v4, RAM and Coral M.2 TPU upgrade path for Frigate
- Restored VM 103 as isolated temporary VM 903, booted HAOS, Supervisor and Core without network connectivity, then removed the test VM
- Confirmed IoT devices remain unable to initiate unrestricted RFC1918 access using live OPNsense rule counters
- Confirmed both Home Assistant native backups and mirrored VM 103 archives are present off-host
- Confirmed the first two 16 GB ECC RDIMMs are detected as 32 GB at 1866 MT/s with no reported boot-time memory error and passed two complete 24 GB `memtester` loops
- Confirmed Coral `G650-04527-01` is the single M.2 2230 A+E-key PCIe x1 model and selected a compatible PCIe x1 E-key carrier
- Validated the migrated Docker services locally and over cellular/Tailscale, including Homepage, Home Assistant, Frigate and Proxmox access
- Validated post-migration Hyper Backup, SMB, Home Assistant backup storage, restricted Synology pull paths, TrueNAS applications, redundant DNS and Frigate NFS recording flow after a full VM reboot
- Formally completed Phase 8 with all intended server workloads on VLAN 20 and HomeLab Doctor reporting 39 passes and no failures

### Planned
- Add MQTT and the Frigate Home Assistant integration after the first automation pilot, not during it
- Add any remaining fringe IoT/media integration only when a planned use case justifies it
- Install the second matching RDIMM pair and E5-2698 v4 when available, then install and validate the Coral TPU in a separate controlled step

### Security
- Kept Home Assistant on Servers VLAN 20 and permitted only host `192.168.20.11` to initiate TCP/UDP access to IoT VLAN 30
- Preserved Lab and IoT isolation; no broad IoT-to-Servers rule was added, and discovery relay scope is limited to LAN, Servers and IoT
- Limited Trusted-media access to Home Assistant host `192.168.20.11` and a five-device Apple TV alias; no general Servers-to-Trusted exception was created
- Added one host-scoped Servers-to-Trusted exception for the Tailscale subnet-router host `192.168.20.20`; the general Servers isolation rules remain in force

## v1.5.0

### Added
- Functional `lab doctor` checks for both Pi-hole DNS endpoints, including public, local and blocked-domain resolution
- Stable Primary and Secondary Pi-hole service labels and Homepage tiles
- OPNsense aliases for the two Pi-hole servers and all routed client VLANs
- A single early floating firewall exception limited to TCP/UDP 53 from client VLANs to the Pi-hole pair

### Changed
- OPNsense Dnsmasq initially advertised `192.168.1.20` and `192.168.1.40` through DHCPv4 option 6 on every configured DHCP range; the current endpoints are `192.168.20.20` and `192.168.20.40`
- Renamed the Docker-hosted Pi-hole internal hostname to `pihole-primary`; the TrueNAS-managed secondary retains its generated container hostname
- Replaced the Mac-only DNS pilot with redundant network-wide DHCP advertisement

### Validated
- Both Pi-holes resolve public and `internal` names and block the test domain
- LAN, Servers VLAN 20, IoT VLAN 30 and Guest VLAN 40 can reach both resolvers
- The consolidated DNS exception precedes the existing RFC1918 isolation blocks in the compiled OPNsense ruleset
- Frigate remained healthy with zero container restarts, fresh NFS recording segments and no recording interruptions during the final 24-hour observation

### Security
- Preserved VLAN isolation by allowing only TCP/UDP 53 to the Pi-hole server alias
- Kept encrypted/private client DNS outside the DHCP rollout guarantee; no broad DoH/DoT interception was introduced
- Created checksum-recorded OPNsense backups before and after the DNS rollout

## v1.4.0

### Added
- Automated checksum-verified configuration pulls from the Mac to the Backup Synology
- Automated read-only Proxmox guest-archive mirroring to the Backup Synology
- Failure-only email alerts through the restricted Synology-to-Mac SSH path and Apple Mail
- Client-side-encrypted Hyper Backup protection in a private IDrive e2 S3-compatible bucket
- Bucket-scoped cloud credentials, 23-version rotation and weekly integrity checking
- Manual `lab backup synology-copy [--dry-run]` fallback
- Frigate SSH alias and toolkit inventory integration
- Deferred post-project evaluation of Tailscale Services

### Validated
- Initial and incremental Hyper Backup runs with two recoverable versions
- Off-site LXC 100 archive recovery with an exact SHA-256 match
- Homepage configuration restore and isolated temporary-container service validation
- Offline disposable Proxmox LXC restore with isolated networking
- Non-interactive OPNsense and Frigate public-key SSH
- `ssh frigate`, `lab ssh frigate` and the Homepage Frigate SSH launch path

### Security
- Restricted the Proxmox export identity to source-address-bound, read-only `rrsync`
- Kept S3 credentials, SSH private keys, Hyper Backup encryption material and raw archives outside Git
- Stored the Hyper Backup recovery key separately in encrypted, backed-up recovery storage
- Preserved tailnet-only scope for the future Tailscale Services evaluation, with no Funnel or public exposure

### Fixed
- Loaded the shared output library before the `lab` command renders backup help
- Removed the abandoned interactive Synology-copy pause from `lab backup all`
- Repaired OPNsense public-key authentication and configured macOS Keychain-backed SSH-agent loading

## v1.3.0

### Added
- Implemented routed infrastructure and baseline policy for VLANs 20, 50, 60 and 70
- Deployed Frigate in Proxmox VM 102 on Servers VLAN 20
- Isolated the Reolink Duo 2V PoE camera on Cameras VLAN 60
- Added narrowly scoped Frigate-to-camera HTTP, RTSP and ONVIF access
- Added TrueNAS NFS recording storage and reboot-safe systemd startup ordering
- Added Frigate web and SSH shortcuts to Homepage
- Added a private, checksum-verified Frigate configuration backup procedure

### Validated
- Frigate and its NFS storage recover automatically after a full VM reboot
- Main and substreams, ONVIF discovery, continuous recording and recent MP4 creation
- Camera TCP 9000 remains blocked from the Frigate VM

### Security
- Camera and Frigate credentials are excluded from repository documentation
- Cameras remain blocked from initiating access to internal RFC1918 networks

## v1.2.4

### Documented
- Recorded the verified second copy of the 2026-08-08 recovery set on the backup Synology
- Recorded successful SHA-256 verification of all six protected files from the Synology destination

### Clarified
- The Mac originals remain intact
- The Synology copy is on a separate host but remains same-site rather than off-site
- Automated replication and deletion remain deferred until retention and restore testing are established

## v1.2.3

### Designed
- Reserved VLAN 70 and `192.168.70.0/24` for isolated Proxmox experiments
- Defined the future Arista Et3 trunk, VLAN-aware Proxmox bridge and per-workload tagging model
- Defined default-deny internal policy, administrator access, implementation validation and rollback requirements

### Clarified
- Proxmox management and existing production containers remain on native VLAN 10 during the Lab rollout
- This release changes documentation only and does not deploy VLAN 70

## v1.2.2

### Added
- Documented the physical 15U rack elevation from U15 through U1
- Recorded shelf contents, patch-panel placement, core switch, OPNsense, PoE switching, UPS and reserved capacity

## v1.2.1

### Added
- Homepage SSH launch group for Proxmox, Docker LXC, OPNsense and TrueNAS
- Remote SSH validation through the private Tailscale subnet route
- Backup and restore guidance for Homepage, Pi-hole, Docker Compose and Tailscale policy
- Verified Proxmox guest archives and consolidated overlapping backup jobs into one retained daily schedule

### Clarified
- Remote SSH uses the hosts' existing OpenSSH services over Tailscale; native Tailscale SSH is not enabled
- No inbound WAN SSH rule or port-forward is required
- Raw backups, credentials, tokens and private configuration must not be committed to this repository

## v1.2.0

### Added
- Validated current-network baseline
- Homepage service dashboard at `home.internal`
- Tailscale subnet-router and split-DNS documentation
- Identity-restricted remote access to the trusted LAN
- Production IoT VLAN 30 and Guest VLAN 40 documentation
- TrueNAS active-backup LAN bond documentation
- Pi-hole 2026.05.0 container and Mac Mini DNS-filtering pilot
- Pi-hole quick link on the Homepage service dashboard

### Improved
- Documented the stable replacement WAN cable and X553 receive-ring tuning
- Updated service inventory and roadmap to match the deployed environment
- Clarified that remote administration uses Tailscale without inbound WAN ports
- Documented the Pi-hole-to-OPNsense DNS chain, validation commands and rollback procedure

## v1.1.0

### Added
- Modular backup framework
- Arista automated backups
- Proxmox host configuration backups
- Unified `lab backup all`
- Passwordless SSH for all infrastructure
- Improved help system
- Guided backup workflow

### Improved
- Shared output library
- Device configuration
- Health monitoring
- Repository organization

## v1.0.0

- Initial infrastructure baseline
