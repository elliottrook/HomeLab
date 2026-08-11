# HomeLab

Enterprise-inspired home lab documentation for Project Mini Atlas.

## Current state

- OPNsense provides routing, firewalling, DNS and DHCP.
- Arista provides the 10 Gb Layer 2 core.
- VLAN 10 is the trusted `192.168.1.0/24` network.
- VLAN 20 is the routed Servers `192.168.20.0/24` network.
- VLAN 30 is the isolated IoT `192.168.30.0/24` network.
- VLAN 40 is the Internet-only Guest `192.168.40.0/24` network.
- VLANs 50, 60 and 70 provide Management, Cameras and Lab segmentation.
- Frigate VM 102 records an isolated Reolink camera to TrueNAS NFS storage.
- Homepage provides the internal service dashboard at `http://home.internal:3000`, including SSH launch links for the core infrastructure hosts.
- Pi-hole runs in Docker LXC 100 at `192.168.1.20`; a Mac Mini pilot is validated while OPNsense remains the network-wide DNS service.
- Tailscale provides identity-restricted web and SSH access to the trusted LAN without inbound WAN ports.
- The Backup Synology pulls and checksum-verifies configuration sets and retained Proxmox guest archives on independent schedules.
- Hyper Backup provides client-side-encrypted, versioned IDrive e2 off-site protection for essential recovery material; media and Frigate recordings are excluded.

Start with [the current network baseline](docs/Current-Network-Baseline.md), then see the [master plan](docs/Master-Plan.md), [surveillance runbook](docs/07-Surveillance.md) and [project roadmap](PROJECTS.md).
