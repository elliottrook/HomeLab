# Changelog

## v1.5.0

### Added
- Functional `lab doctor` checks for both Pi-hole DNS endpoints, including public, local and blocked-domain resolution
- Stable Primary and Secondary Pi-hole service labels and Homepage tiles
- OPNsense aliases for the two Pi-hole servers and all routed client VLANs
- A single early floating firewall exception limited to TCP/UDP 53 from client VLANs to the Pi-hole pair

### Changed
- OPNsense Dnsmasq now advertises `192.168.1.20` and `192.168.1.40` through DHCPv4 option 6 on every configured DHCP range
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
