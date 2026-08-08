# Architecture

```text
Internet
  |
OPNsense (routing, firewall, DHCP and Unbound DNS)
  |
Arista core
  +-- Proxmox
  |     +-- LXC 100: Docker, Homepage, Portainer, Pi-hole and Tailscale
  |     +-- LXC 101: UniFi OS Server
  +-- TrueNAS
  +-- Synology storage
  +-- UniFi switching and wireless
```

## DNS architecture

The production network continues to use OPNsense at `192.168.1.1` for DNS. Unbound listens on port 53 and conditionally forwards the `internal` namespace to OPNsense dnsmasq on port 53053.

Pi-hole 2026.05.0 is deployed as a Docker container in LXC 100. It publishes DNS on `192.168.1.20:53` and its web interface on `http://192.168.1.20:8082/admin/`. Pi-hole forwards public queries and the `internal` namespace to OPNsense. Conditional forwarding for `192.168.1.0/24` preserves local names and reverse lookups.

```text
Mac Mini pilot -> Pi-hole -> OPNsense Unbound -> Internet DNS
                         +-> OPNsense internal namespace

Other clients  ----------------> OPNsense Unbound
```

Pi-hole is not a DHCP server. OPNsense DHCP has not yet been changed to advertise Pi-hole, so this remains a reversible single-client pilot until a DNS-resilience design is approved.
