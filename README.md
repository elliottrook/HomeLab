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
- Home Assistant OS VM 103 is operational at `home-assistant.home.internal` on Servers VLAN 20; Hue, Lutron and Aqara Matter are integrated, and the Hue Hall motion-to-Lutron Laundry light pilot is validated.
- Homepage provides the internal service dashboard at `http://home.internal:3000`, including SSH launch links for the core infrastructure hosts.
- Redundant Pi-hole resolvers run on Docker LXC 100 at `192.168.20.20` and TrueNAS at `192.168.20.40`; OPNsense Dnsmasq advertises both to every DHCP range.
- Tailscale provides identity-restricted web and SSH access to the trusted LAN without inbound WAN ports.
- The Backup Synology pulls and checksum-verifies configuration sets and retained Proxmox guest archives on independent schedules.
- Hyper Backup provides client-side-encrypted, versioned IDrive e2 off-site protection for essential recovery material; media and Frigate recordings are excluded.
- `lab doctor` functionally monitors OPNsense, Arista, Proxmox (including VM 103), TrueNAS, Frigate, both Pi-holes and backup-report freshness using persistent counter baselines where appropriate.
- Beszel provides lightweight historical host/container metrics for Docker, Proxmox and Frigate, with a concise systems-up widget on Homepage.

Start with [the current network baseline](docs/Current-Network-Baseline.md), then see the [master plan](docs/Master-Plan.md), [surveillance runbook](docs/07-Surveillance.md) and [project roadmap](PROJECTS.md).
