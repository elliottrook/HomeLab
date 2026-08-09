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
  |     +-- VM 102: Frigate (Servers VLAN 20)
  +-- TrueNAS
  |     +-- NFS: Surveillance/Frigate recording storage
  +-- Synology storage
  +-- UniFi switching and wireless
        +-- Reolink Duo 2V PoE (Cameras VLAN 60)
```

## Surveillance architecture

Frigate VM 102 is isolated on Servers VLAN 20 at `192.168.20.10`. The Reolink
Duo 2V PoE camera is isolated on Cameras VLAN 60 at `192.168.60.10`. OPNsense
permits only Frigate-to-camera TCP 80, 554 and 8000 across those VLANs. Frigate
stores recordings on the TrueNAS NFS export
`/mnt/Media/Surveillance/Frigate`; cameras do not receive broad access to the
Servers or Trusted networks.

## DNS architecture

The production network continues to use OPNsense at `192.168.1.1` for DNS. Unbound listens on port 53 and conditionally forwards the `internal` namespace to OPNsense dnsmasq on port 53053.

Pi-hole 2026.05.0 is deployed as a Docker container in LXC 100. It publishes DNS on `192.168.1.20:53` and its web interface on `http://192.168.1.20:8082/admin/`. Pi-hole forwards public queries and the `internal` namespace to OPNsense. Conditional forwarding for `192.168.1.0/24` preserves local names and reverse lookups.

```text
Mac Mini pilot -> Pi-hole -> OPNsense Unbound -> Internet DNS
                         +-> OPNsense internal namespace

Other clients  ----------------> OPNsense Unbound
```

Pi-hole is not a DHCP server. OPNsense DHCP has not yet been changed to advertise Pi-hole, so this remains a reversible single-client pilot until a DNS-resilience design is approved.
