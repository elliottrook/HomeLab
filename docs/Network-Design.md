# Project Mini Atlas Network Design

**Status:** Reconciled production baseline

**Phase:** Enterprise Network  
**Last Updated:** 2026-08-20

---

## 1. Purpose

This document defines the logical and physical network design for Project Mini Atlas.

It is the authoritative reference for:

- Network architecture
- Trust boundaries
- VLAN roles
- Routing responsibilities
- Firewall enforcement
- Switch topology
- Wireless integration
- Future expansion

No major network change should be implemented until it is reflected here.

---

## 2. Current State

Project Mini Atlas retains `192.168.1.0/24` as the trusted network on VLAN 10 while lower-trust device classes move to routed VLANs.

Core infrastructure includes:

- OPNsense as the firewall, router, DHCP, and DNS platform
- Arista DCS-7050TX-64 as the 10 Gb core switch
- Proxmox as the virtualization platform
- TrueNAS SCALE and Synology systems for storage
- Binarui AP Switch with UniFi wireless
- Homepage for internal service navigation
- Tailscale for private, identity-restricted remote access

The Arista carries native Trusted VLAN 10 and tagged VLANs 20, 30, 40, 50,
60 and 70. OPNsense performs inter-VLAN routing and enforces the default-deny
policy between trust zones.

The planned migrations are complete. Docker, Frigate, Home Assistant, TrueNAS
and both Synology systems reside on Servers VLAN 20. The UniFi controller,
both access points, Proxmox and the Arista management SVI reside on Management
VLAN 50. The AP Switch is numbered `192.168.50.26`, but its management plane
appears on VLAN 1/untagged and requires the documented direct-recovery path.
IoT, Guest and Camera devices use VLANs 30, 40 and 60.
Aster (LXC 104) and its llama.cpp GPU inference backend (LXC 110) are the
production local-AI workloads on Lab VLAN 70. Hermes and Ollama (VM 105) are
retained, disabled/stopped, as rollback paths. The validated deployed state
is recorded in `Current-Network-Baseline.md`.

---

## 3. Design Goals

The network should provide:

- Clear separation between trusted, untrusted, and experimental devices
- Reliable 10 Gb connectivity for servers and storage
- Simple administration
- Predictable addressing
- Secure wireless segmentation
- Minimal unnecessary complexity
- A clean path for future expansion
- Recovery without physical reconfiguration wherever practical

---

## 4. Routing and Enforcement

OPNsense will remain the central Layer 3 router and firewall.

The Arista will primarily provide:

- High-speed Layer 2 switching
- VLAN transport
- Access and trunk ports
- Core aggregation

Inter-VLAN routing and security policy will be enforced by OPNsense unless a future design decision explicitly changes this.

This preserves one central policy enforcement point and keeps the switch configuration easier to understand.

## Remote access

Tailscale runs in the Docker LXC as a subnet router and advertises `192.168.1.0/24`, `192.168.20.0/24` and `192.168.50.0/24`. Split DNS forwards the `internal` namespace to OPNsense, allowing `home.internal` and other internal names to work remotely. Tailnet grants restrict Trusted, Servers and Management access to the administrator identity. No inbound WAN port-forward is required.

---

## 5. Proposed Trust Zones

The initial design will use the following trust zones:

| Zone | Purpose | Trust Level |
|---|---|---|
| Infrastructure | Network equipment and management interfaces | Highest |
| Production | Trusted personal devices | High |
| Servers | Proxmox workloads and self-hosted services | High but controlled |
| Lab | Experimental systems and temporary testing | Medium |
| IoT | Consumer and embedded devices | Low |
| Cameras | Surveillance devices and NVR traffic | Low |
| Guest | Visitor Internet access | Untrusted |

The final VLAN numbers and subnets will be documented separately in:

- `IP-Addressing.md`
- `VLAN-Design.md`
- `Firewall-Policy.md`

---

## 6. High-Level Architecture

```text
                            Internet
                                |
                         TELUS fibre / 10 GbE
                                |
                    +-----------------------+
                    |       OPNsense        |
                    | Routing, DHCP, policy |
                    +-----------+-----------+
                                |
                       802.1Q trunk — Et42
                                |
                    +-----------+-----------+
                    |   Arista 10 Gb core   |
                    |     192.168.50.2      |
                    +-----------+-----------+
                                |
      +---------------+---------+----------+----------------+
      |               |                    |                |
 VLAN 10           VLAN 20              VLAN 50          VLAN 70
 Trusted           Servers              Management       Lab
      |               |                    |                |
 Personal        Docker / Pi-hole      Proxmox          Aster
 computers       Frigate / HA          Arista           llama.cpp
 and phones      TrueNAS               UniFi
                 Synology
                      |
                 +----+-----+
                 |          |
              VLAN 30    VLAN 60
              IoT        Cameras

 VLAN 40 Guest is Internet-only.
 Inter-VLAN routing remains centralized at OPNsense.
 Remote access uses Tailscale routes to VLANs 10, 20 and 50.
```
