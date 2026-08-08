# Project Mini Atlas Network Design

**Status:** Implementation in progress

**Phase:** Enterprise Network  
**Last Updated:** 2026-08-08

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
- UniFi switching and wireless
- Homepage for internal service navigation
- Tailscale for private, identity-restricted remote access

The Arista carries trusted traffic on VLAN 10, isolated IoT traffic on VLAN 30 and isolated Guest traffic on VLAN 40. OPNsense provides the gateway and policy enforcement for all three networks.

Servers and management infrastructure remain on VLAN 10 during the staged migration. The validated deployed state is recorded in `Current-Network-Baseline.md`.

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

Tailscale runs in the Docker LXC as a subnet router and advertises only `192.168.1.0/24`. Split DNS forwards the `internal` namespace to OPNsense, allowing `home.internal` and other internal names to work remotely. Tailnet grants restrict trusted-LAN access to the administrator identity. No inbound WAN port-forward is required.

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
Telus Fibre
   |
OPNsense
   |
802.1Q trunk
   |
Arista DCS-7050TX
   |
   +-- Proxmox
   +-- TrueNAS
   +-- Synology
   +-- UniFi PoE Switch
   |     +-- UniFi Access Points
   |     +-- Future PoE devices
   |
   +-- Wired clients
   +-- Future camera switching
