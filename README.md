# HomeLab

Enterprise-inspired home lab documentation for Project Mini Atlas.

## Current state

- OPNsense provides routing, firewalling, DNS and DHCP.
- Arista provides the 10 Gb Layer 2 core.
- VLAN 10 is the trusted `192.168.1.0/24` network.
- VLAN 30 is the isolated IoT `192.168.30.0/24` network.
- VLAN 40 is the Internet-only Guest `192.168.40.0/24` network.
- Homepage provides the internal service dashboard at `http://home.internal:3000`, including SSH launch links for the core infrastructure hosts.
- Pi-hole runs in Docker LXC 100 at `192.168.1.20`; a Mac Mini pilot is validated while OPNsense remains the network-wide DNS service.
- Tailscale provides identity-restricted web and SSH access to the trusted LAN without inbound WAN ports.

Start with [the current network baseline](docs/Current-Network-Baseline.md), then see the [master plan](docs/Master-Plan.md) and [project roadmap](PROJECTS.md).
