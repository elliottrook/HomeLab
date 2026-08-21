# Architecture

```text
Internet
  |
OPNsense (routing, firewall, DHCP and Unbound DNS)
  |
Arista core
  +-- Proxmox
  |     +-- LXC 100: Docker, Homepage, Portainer, Pi-hole and Tailscale (Servers VLAN 20)
  |     +-- LXC 101: UniFi OS Server
  |     +-- VM 102: Frigate (Servers VLAN 20)
  |     +-- VM 103: Home Assistant OS (Servers VLAN 20)
  |     +-- LXC 104: Hermes Agent (Lab VLAN 70)
  |     +-- VM 105: Ollama (Lab VLAN 70)
  +-- TrueNAS
  |     +-- NFS: Surveillance/Frigate recording storage
  +-- Synology storage
  +-- UniFi switching and wireless
        +-- Reolink Duo 2V PoE (Cameras VLAN 60)
```

## Architecture decisions and accepted risks — 2026-08-20

### Current architectural decisions

- OPNsense remains the Layer 3 gateway, firewall and DHCP authority. The Arista
  switch remains the Layer 2 core.
- Trusted, Servers, IoT, Guest, Management, Cameras and Lab workloads remain
  separated into VLANs 10, 20, 30, 40, 50, 60 and 70.
- Inter-VLAN access is denied by default and opened only through documented,
  host-scoped production exceptions.
- Infrastructure management is restricted to approved administrator devices
  and authorized Tailscale users.
- Tailscale provides remote administration without inbound WAN port exposure.
- Home Assistant is the central automation authority. HomeKit Bridge provides
  selected Apple Home and Siri presentation without becoming a second
  automation platform.
- DNS is provided by two Pi-hole instances on different hosts. OPNsense remains
  their upstream resolver and the authority for the internal namespace.
- Proxmox hosts the core service guests. TrueNAS provides primary application
  and media storage, the main Synology provides family services and the Backup
  Synology provides recovery storage.
- Hermes and Ollama remain isolated Lab VLAN workloads and are not dependencies
  for production HomeLab operation.
- Essential configuration and guest archives receive automated local and
  off-host protection. Large replaceable media libraries and Frigate recordings
  are intentionally excluded from encrypted off-site storage.

### Accepted risks

| Risk | Acceptance and mitigation |
|---|---|
| Proxmox is a single compute host | Guest archives are retained off-host, mirrored with checksum verification and represented by successful isolated restore tests. Host failure still requires manual restoration onto replacement hardware. |
| OPNsense and the Arista core are individual infrastructure appliances | Current configurations are exported and monitored for drift. Recovery is procedural rather than automatically highly available. |
| Proxmox guest memory is overcommitted when all production and AI workloads run simultaneously | Ollama remains optional and normally stopped when its memory would interfere with production guests. Final RAM and CPU work must be completed before sustained simultaneous use. |
| The secondary Pi-hole shares the TrueNAS host | DNS instances are separated across hosts, but a TrueNAS outage also removes the secondary resolver. The Docker-hosted primary remains available. |
| Backup Synology free capacity is finite | Backup retention, Hyper Backup growth and Proxmox mirror usage must continue to be monitored; the appliance is not treated as the only copy of essential data. |
| Media libraries and Frigate recordings are not encrypted off-site | Their size exceeds their recovery value. Configuration, metadata and critical guest recovery paths receive priority instead. |
| Full destructive restore tests were not performed for OPNsense, Arista, TrueNAS or either Synology | Exports, documented recovery procedures, verified backup access and representative LXC/VM restore tests provide proportionate evidence without risking production data. |
| Home Assistant has broad host-scoped TCP/UDP access from its single address to IoT VLAN 30 | This is required for varied integrations and discovery. Other Servers hosts remain blocked, and IoT devices cannot initiate unrestricted access to internal networks. |
| Tailscale can route authorized users to Trusted and Management networks | Access remains identity-controlled in Tailscale and source-restricted by OPNsense. No Tailscale Funnel or public service exposure is enabled. |
| Internal services use a mixture of private, self-signed and publicly issued certificates | Expiry is monitored for operationally important TLS services. Internal certificate trust warnings remain accepted where no public trust is required. |
| IPv6 segmentation has not received the same production validation as IPv4 | The current security design and operational tests are based primarily on IPv4. Wider IPv6 deployment remains deferred until equivalent policy and validation are planned. |
| Hermes and Ollama are not yet in the encrypted off-site selection | Both have verified same-site archives, checksum-verified Synology mirrors and isolated restore evidence. Off-site inclusion remains an explicit AI-pilot follow-up. |

## Local AI Lab architecture

Hermes Agent runs in unprivileged LXC 104 at `192.168.70.10`. Ollama runs in
Ubuntu VM 105 at `192.168.70.11` and listens on TCP 11434. Both workloads are
tagged into isolated Lab VLAN 70. Hermes uses Ollama's OpenAI-compatible `/v1`
endpoint and the locally defined `qwen3-64k:8b` profile with a 65,536-token
context window.

This remains a CPU-only pilot, not a production dependency. The 14 GB Ollama
allocation was the first tested allocation that avoided the observed OOM
failure, but response time remains slow and aggregate Proxmox memory allocation
must be reconciled before sustained simultaneous use. LXC 104 and VM 105 now
have fresh local archives, checksum-verified Backup Synology mirrors and
successful isolated restore evidence. Encrypted off-site inclusion remains a
planned AI-pilot follow-up.

## Surveillance architecture

Frigate VM 102 is isolated on Servers VLAN 20 at `192.168.20.10`. The Reolink
Duo 2V PoE camera is isolated on Cameras VLAN 60 at `192.168.60.10`. OPNsense
permits only Frigate-to-camera TCP 80, 554 and 8000 across those VLANs. Frigate
stores recordings on the TrueNAS NFS export
`/mnt/Media/Surveillance/Frigate`; cameras do not receive broad access to the
Servers or Trusted networks.

## DNS architecture

OPNsense Dnsmasq remains the DHCP authority. DHCPv4 option 6 advertises both Pi-hole resolvers on every configured DHCP range. OPNsense Unbound remains their upstream resolver and conditionally forwards the `internal` namespace to OPNsense dnsmasq on port 53053.

The primary Pi-hole 2026.05.0 is deployed as a Docker container in LXC 100 on Servers VLAN 20. It publishes DNS on `192.168.20.20:53` and its web interface on `http://192.168.20.20:8082/admin/`. The secondary Pi-hole 2026.07.2 is a TrueNAS App at `192.168.20.40:53`, with web administration on TCP 20720. Both resolve public names through OPNsense, preserve `internal` resolution and return the configured blocked response.

```text
DHCP clients -> Pi-hole Primary  192.168.20.20 --+
             -> Pi-hole Secondary 192.168.20.40 --+-> OPNsense Unbound -> Internet DNS
                                                  +-> OPNsense internal namespace
```

Pi-hole is not a DHCP server. A floating OPNsense rule permits only TCP/UDP 53 from the routed client-VLAN alias to the Pi-hole server alias and is evaluated before the existing RFC1918 isolation blocks. Clients using encrypted or private DNS can bypass DHCP-provided resolvers; this rollout does not attempt broad DoH/DoT interception.

## Home automation architecture

Home Assistant OS 18.2 runs as Proxmox VM 103 at `192.168.20.11` on Servers VLAN 20. The VM has 2 vCPU, 4 GB RAM and a 32 GB system disk. OPNsense Dnsmasq reserves the address for MAC `BC:24:11:08:16:A3`, and local DNS publishes `home-assistant.home.internal`.

Home Assistant is the only Servers host permitted to initiate TCP/UDP access to IoT VLAN 30. The host-specific pass rule for `192.168.20.11` precedes the general Servers-to-RFC1918 block; live counters confirmed that IoT devices still cannot initiate unrestricted RFC1918 access. Philips Hue is reserved at `192.168.30.164`, Lutron Caséta at `192.168.30.102`, and Aqara M3 at `192.168.30.158`; all are integrated. The mDNS repeater is limited to LAN, Servers and IoT for required discovery.

Home Assistant is the sole owner of rebuilt general automations. Vendor applications remain available for firmware, recovery, safety behavior and unsupported features. The first cross-ecosystem pilot is complete: the Hue Hall motion sensor controls the Lutron `Laundry Main Lights`. Aqara continues to own its water-leak/shutoff safety behavior while the six sensors, valve and lock are visible in Home Assistant through Matter.

Trusted media access is separately constrained to source `192.168.20.11` and the `TRUSTED_MEDIA_DEVICES` alias containing five Apple TVs. Media endpoints already on IoT, including AirPort Express and Sonos devices, use the existing Home Assistant-to-IoT path. This rule does not grant broad Servers-to-Trusted access.

HomeKit Bridge is the presentation layer for Apple Home and Siri; it is not a second automation authority. It publishes only `light`, `switch`, `lock`, `climate`, `cover`, `fan`, `vacuum`, `scene`, `script` and `binary_sensor`. Media players, cameras, general sensors, automations, buttons and helpers are excluded to prevent duplicate endpoints and diagnostic clutter. Discovery depends on mDNS across the existing bounded LAN/Servers/IoT relay, and control uses the bridge TCP listener on VM 103 (default port `21063`). Pairing and live Siri control were validated on 2026-08-15.
