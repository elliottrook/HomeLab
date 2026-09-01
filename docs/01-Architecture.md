# Architecture

```text
Internet
  |
OPNsense (routing, firewall, DHCP and Unbound DNS)
  |
Arista core
  +-- Proxmox
  |     +-- LXC 100: Docker (Servers VLAN 20)
  |     |     +-- Homepage dashboard
  |     |     +-- Portainer
  |     |     +-- Media services
  |     |     +-- Utilities
  |     +-- LXC 101: UniFi OS Server
  |     +-- VM 102: Frigate (Servers VLAN 20)
  |     +-- VM 103: Home Assistant OS (Servers VLAN 20)
  |     +-- LXC 104: Aster Agent API/UI (Lab VLAN 70)
  |     +-- VM 105: stopped legacy Ollama rollback guest (Lab VLAN 70)
  |     +-- LXC 106: Authentik
  |     +-- LXC 107: Reverse Proxy
  |     +-- LXC 108: Forgejo (Servers VLAN 20)
  |     +-- LXC 109: Prometheus / Grafana observability (Servers VLAN 20)
  +-- TrueNAS
  |     +-- NFS: Surveillance/Frigate recording storage
  +-- Synology storage
  +-- NUT server (Management VLAN 50, Arista Et31)
  +-- AP Switch and UniFi wireless (Arista Et33 10G uplink)
  |     +-- Two U7 Pro XG access points at 2.5G
  +-- TP-Link camera-only PoE switch (Arista Et34 access VLAN 60; validation pending)
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
- Forgejo is the primary self-hosted Git remote. GitHub remains a synchronized
  off-site remote rather than the sole repository authority.

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
| OPNsense, Arista and the UniFi PoE/camera switches have no automated software shutdown on UPS low battery | Network switches are power-loss-tolerant with no filesystem to corrupt; OPNsense's shutdown was deliberately left out of this milestone's scope rather than expanded mid-project. They simply lose power abruptly once their UPS is exhausted. |
| Proxmox, TrueNAS and the Lenovo NUT server likely will not auto-restart when mains returns after a UPS-triggered shutdown | No UPS is configured to cut its own output power, so these hosts perform a normal OS-issued soft shutdown while still receiving power — most BIOS "AC Power Recovery" settings only respond to an actual DC power loss/return, not this scenario. Manual (or IPMI/remote) power-on is the current expectation; untested against each host's actual BIOS behavior. |

## UPS and power-resilience architecture

The Lenovo ThinkCentre M92p (`nut-server`, `192.168.50.25`, Management
VLAN 50, direct Arista Et31 connection) runs Network UPS Tools (NUT)
2.8.1-5 on bare metal as the central power-monitoring/shutdown-
orchestration host for three UPS units:

```text
CyberPower CP1500PFCLCD (proxmox-ups) -- Proxmox + both Synology units
CyberPower CP1500PFCLCD (nas-ups)     -- TrueNAS + Arista core switch
CyberPower OR500LCDRM1U (network-ups) -- OPNsense, nut-server itself,
                                          UniFi PoE switch, camera switch
APC Back-UPS Pro BN1500M2-CA          -- dumb battery, no NUT interface,
                                          no equipment currently assigned
```

Equipment is distributed across UPS units differently than a naive
per-service mapping would suggest, driven by physical/cabling
constraints. Proxmox and TrueNAS are independent NUT network clients
(`secondary` role) of their respective UPS, each handling their own
shutdown: Proxmox runs a custom script that stops Frigate (its NFS
dependency on TrueNAS) before other guests, then triggers shutdown on
both Synology units over SSH, then powers off itself; TrueNAS uses its
native `ups` client service for a plain graceful shutdown. Each UPS's
low-battery threshold is overridden (`nas-ups`=50%, `proxmox-ups`=80%,
`network-ups`=25%) rather than using the ~10% hardware default —
`proxmox-ups`'s threshold is set early specifically because its
Synology-shutdown step depends on Arista (on `nas-ups`) still being
powered, not because of its own battery runway. `nut-server`'s own local
`upsmon` only monitors `network-ups` (its actual power source), so it
doesn't shut itself down over a UPS it isn't even connected to. Full
design and validation detail: `docs/UPS-Power-Resilience-Claude-Handover.md`.

## Local AI Lab architecture

Aster's lightweight authenticated API and browser UI run in unprivileged LXC
104 at `192.168.70.10:9120`. A persistent llama.cpp b10507 service runs in
unprivileged LXC 110 at `192.168.70.12:11435`, with the host `xe` DRM devices
mapped into the container. It serves Qwen 3.8 27B `UD-IQ4_XS` through Vulkan
with one 8,192-token slot, flash attention and Q8 KV cache. Both workloads are
confined to Lab VLAN 70 and both APIs require bearer authentication except the
minimal Aster health endpoint.

The Aster harness selects and pre-executes only allowlisted read-only functions:
local time, Aster/inference health and scoped search over a curated documentation
snapshot. It has no arbitrary shell or arbitrary network-target function.
Hermes and Ollama remain installed but disabled as rollback paths; stopped VM
105 remains the older CPU/passthrough rollback guest. Aster is useful but is not
a dependency for core HomeLab operation.

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

## Authorization architecture

Nginx Proxy Manager serves `proxy.elliottrook.com` at `192.168.50.23` using the
Cloudflare DNS-01 wildcard certificate. OPNsense and both Pi-holes resolve the
name internally to that private address. NPM proxy host #2 sends
unauthenticated requests to the Authentik embedded outpost at
`192.168.50.22:9000`.

```text
Client -> HTTPS NPM -> Authentik password + passkey -> NPM login -> NPM
```

The embedded outpost advertises `https://auth.elliottrook.com` as its Authentik
host so browser-facing authentication and WebAuthn redirects retain a secure
origin. See [the authorization runbook](08-Authorization.md).

## Home automation architecture

Home Assistant OS 18.2 runs as Proxmox VM 103 at `192.168.20.11` on Servers VLAN 20. The VM has 2 vCPU, 4 GB RAM and a 32 GB system disk. OPNsense Dnsmasq reserves the address for MAC `BC:24:11:08:16:A3`, and local DNS publishes `home-assistant.home.internal`.

Home Assistant is the only Servers host permitted to initiate TCP/UDP access to IoT VLAN 30. The host-specific pass rule for `192.168.20.11` precedes the general Servers-to-RFC1918 block; live counters confirmed that IoT devices still cannot initiate unrestricted RFC1918 access. Philips Hue is reserved at `192.168.30.164`, Lutron Caséta at `192.168.30.102`, and Aqara M3 at `192.168.30.158`; all are integrated. The mDNS repeater is limited to LAN, Servers and IoT for required discovery.

Home Assistant is the sole owner of rebuilt general automations. Vendor applications remain available for firmware, recovery, safety behavior and unsupported features. The first cross-ecosystem pilot is complete: the Hue Hall motion sensor controls the Lutron `Laundry Main Lights`. Aqara continues to own its water-leak/shutoff safety behavior while the six sensors, valve and lock are visible in Home Assistant through Matter.

Trusted media access is separately constrained to source `192.168.20.11` and the `TRUSTED_MEDIA_DEVICES` alias containing five Apple TVs. Media endpoints already on IoT, including AirPort Express and Sonos devices, use the existing Home Assistant-to-IoT path. This rule does not grant broad Servers-to-Trusted access.

HomeKit Bridge is the presentation layer for Apple Home and Siri; it is not a second automation authority. It publishes only `light`, `switch`, `lock`, `climate`, `cover`, `fan`, `vacuum`, `scene`, `script` and `binary_sensor`. Media players, cameras, general sensors, automations, buttons and helpers are excluded to prevent duplicate endpoints and diagnostic clutter. Discovery depends on mDNS across the existing bounded LAN/Servers/IoT relay, and control uses the bridge TCP listener on VM 103 (default port `21063`). Pairing and live Siri control were validated on 2026-08-15.
