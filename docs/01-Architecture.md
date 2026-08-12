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

OPNsense Dnsmasq remains the DHCP authority. DHCPv4 option 6 advertises both Pi-hole resolvers on every configured DHCP range. OPNsense Unbound remains their upstream resolver and conditionally forwards the `internal` namespace to OPNsense dnsmasq on port 53053.

The primary Pi-hole 2026.05.0 is deployed as a Docker container in LXC 100. It publishes DNS on `192.168.1.20:53` and its web interface on `http://192.168.1.20:8082/admin/`. The secondary Pi-hole 2026.07.2 is a TrueNAS App at `192.168.1.40:53`, with web administration on TCP 20720. Both resolve public names through OPNsense, preserve `internal` resolution and return the configured blocked response.

```text
DHCP clients -> Pi-hole Primary   192.168.1.20 --+
             -> Pi-hole Secondary 192.168.1.40 --+-> OPNsense Unbound -> Internet DNS
                                                  +-> OPNsense internal namespace
```

Pi-hole is not a DHCP server. A floating OPNsense rule permits only TCP/UDP 53 from the routed client-VLAN alias to the Pi-hole server alias and is evaluated before the existing RFC1918 isolation blocks. Clients using encrypted or private DNS can bypass DHCP-provided resolvers; this rollout does not attempt broad DoH/DoT interception.
