# Changelog

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
