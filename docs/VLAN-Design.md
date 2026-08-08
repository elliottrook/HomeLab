# Project Mini Atlas VLAN Design

**Status:** Partially implemented

**Phase:** Enterprise Network  
**Last Updated:** 2026-08-08

---

## Purpose

This document defines the VLAN structure and Layer 3 addressing plan for Project Mini Atlas.

OPNsense provides the default gateway, DHCP services, and firewall enforcement for each routed VLAN.

The Arista core switch and UniFi switching infrastructure provide Layer 2 VLAN transport.

---

## VLAN Plan

| VLAN | Name | Subnet | Gateway | Purpose |
|---:|---|---|---|---|
| 10 | Trusted | 192.168.1.0/24 | 192.168.1.1 | Trusted computers, phones, servers and management during migration; implemented |
| 20 | Servers | 192.168.20.0/24 | 192.168.20.1 | Proxmox workloads, storage and self-hosted services; draft |
| 30 | IoT | 192.168.30.0/24 | 192.168.30.1 | Smart-home and embedded consumer devices; implemented |
| 40 | Guest | 192.168.40.0/24 | 192.168.40.1 | Internet-only guest access; implemented |
| 50 | Management | 192.168.50.0/24 | 192.168.50.1 | Network equipment, hypervisor management, controllers and access points; draft |
| 60 | Cameras | 192.168.60.0/24 | 192.168.60.1 | Surveillance cameras and future recording services; draft |

---

## Design Decisions

### Preserve the existing production subnet

The existing `192.168.1.0/24` network will remain the Production network on VLAN 10.

This minimizes disruption and allows devices to be migrated gradually.

### Separate management and servers

Network management devices will belong to VLAN 50.

Storage systems and application services will belong to VLAN 20.

This creates a clear distinction between the systems that operate the network and the services delivered through it.

### Centralize routing and security

OPNsense remains the default gateway for every routed VLAN.

The Arista switch remains primarily a Layer 2 core switch.

Inter-VLAN access is controlled by OPNsense firewall policy.

### Avoid VLAN 1

VLAN 1 will not carry ordinary production or management traffic after migration is complete.

---

## DHCP Plan

| VLAN | DHCP Range | Static and Reserved Range |
|---:|---|---|
| 10 | 192.168.1.100–192.168.1.250 | 192.168.1.2–192.168.1.99 |
| 20 | 192.168.20.100–192.168.20.199 | 192.168.20.2–192.168.20.99 |
| 30 | 192.168.30.100–192.168.30.199 | 192.168.30.2–192.168.30.99 |
| 40 | 192.168.40.100–192.168.40.199 | 192.168.40.2–192.168.40.99 |
| 50 | 192.168.50.100–192.168.50.199 | 192.168.50.2–192.168.50.99 |
| 60 | 192.168.60.100–192.168.60.199 | 192.168.60.2–192.168.60.99 |

---

## Planned Infrastructure Addresses

| Device | Planned Address | VLAN |
|---|---:|---:|
| OPNsense Production gateway | 192.168.1.1 | 10 |
| OPNsense Servers gateway | 192.168.20.1 | 20 |
| Proxmox workloads | 192.168.20.0/24 | 20 |
| TrueNAS SCALE | 192.168.20.40 | 20 |
| Synology DS920+ | 192.168.20.41 | 20 |
| Secondary Synology | 192.168.20.42 | 20 |
| OPNsense Management gateway | 192.168.50.1 | 50 |
| Arista core switch | 192.168.50.2 | 50 |
| Proxmox management | 192.168.50.10 | 50 |
| UniFi OS Server | 192.168.50.21 | 50 |
| UniFi PoE switch | 192.168.50.30 | 50 |
| UniFi access point | 192.168.50.31 | 50 |

---

## Initial Access Policy

| Source | Destination | Initial Policy |
|---|---|---|
| Trusted | Internet | Allow |
| Trusted | Management | Allow management from selected administrator devices |
| Trusted | Servers | Allow required services |
| Management | Internet | Allow updates, DNS, and time services |
| Management | Other VLANs | Deny unless required |
| Servers | Internet | Allow required outbound access |
| Servers | Management | Deny by default |
| IoT | Internet | Allow as required |
| IoT | Trusted networks | Deny by default |
| Cameras | Internet | Deny by default |
| Cameras | NVR or management host | Allow required traffic |
| Guest | Internet | Allow |
| Guest | Internal networks | Deny |

---

## Migration Notes

The existing network will remain operational while the new VLAN interfaces are introduced.

IoT VLAN 30 and Guest VLAN 40 are implemented and validated. VLAN 10 remains the native trusted network. Servers and Management will be introduced later, one zone at a time, with alternate access and rollback confirmed before any management address changes.

No management address will be changed until an alternate access path and rollback procedure have been confirmed.
