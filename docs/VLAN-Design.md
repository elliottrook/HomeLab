# Project Mini Atlas VLAN Design

**Status:** Draft  
**Phase:** Enterprise Network  
**Last Updated:** 2026-08-02

---

## Purpose

This document defines the VLAN structure and Layer 3 addressing plan for Project Mini Atlas.

OPNsense provides the default gateway, DHCP services, and firewall enforcement for each routed VLAN.

The Arista core switch and UniFi switching infrastructure provide Layer 2 VLAN transport.

---

## VLAN Plan

| VLAN | Name | Subnet | Gateway | Purpose |
|---:|---|---|---|---|
| 10 | Production | 192.168.1.0/24 | 192.168.1.1 | Trusted household computers, phones, and current production devices |
| 20 | Infrastructure | 192.168.20.0/24 | 192.168.20.1 | Network equipment, hypervisor management, controllers, and access points |
| 30 | Servers | 192.168.30.0/24 | 192.168.30.1 | Storage and self-hosted services |
| 40 | Lab | 192.168.40.0/24 | 192.168.40.1 | Experimental systems and temporary projects |
| 50 | IoT | 192.168.50.0/24 | 192.168.50.1 | Smart-home and embedded consumer devices |
| 60 | Cameras | 192.168.60.0/24 | 192.168.60.1 | Surveillance cameras and future recording services |
| 70 | Guest | 192.168.70.0/24 | 192.168.70.1 | Internet-only guest access |
| 99 | Reserved Management | Reserved | Not configured | Possible future administrator-only management network |

---

## Design Decisions

### Preserve the existing production subnet

The existing `192.168.1.0/24` network will remain the Production network on VLAN 10.

This minimizes disruption and allows devices to be migrated gradually.

### Separate infrastructure and servers

Network management devices belong to VLAN 20.

Storage systems and application services belong to VLAN 30.

This creates a clear distinction between the systems that operate the network and the services delivered through it.

### Centralize routing and security

OPNsense remains the default gateway for every routed VLAN.

The Arista switch remains primarily a Layer 2 core switch.

Inter-VLAN access is controlled by OPNsense firewall policy.

### Avoid VLAN 1

VLAN 1 will not carry ordinary production or management traffic after migration is complete.

### Reserve VLAN 99

VLAN 99 is reserved for a possible administrator-only network but will not be implemented unless it provides a clear operational or security benefit.

---

## DHCP Plan

| VLAN | DHCP Range | Static and Reserved Range |
|---:|---|---|
| 10 | 192.168.1.100–192.168.1.250 | 192.168.1.2–192.168.1.99 |
| 20 | 192.168.20.100–192.168.20.199 | 192.168.20.2–192.168.20.99 |
| 30 | 192.168.30.100–192.168.30.199 | 192.168.30.2–192.168.30.99 |
| 40 | 192.168.40.100–192.168.40.240 | 192.168.40.2–192.168.40.99 |
| 50 | 192.168.50.100–192.168.50.240 | 192.168.50.2–192.168.50.99 |
| 60 | 192.168.60.100–192.168.60.199 | 192.168.60.2–192.168.60.99 |
| 70 | 192.168.70.50–192.168.70.250 | 192.168.70.2–192.168.70.49 |

---

## Planned Infrastructure Addresses

| Device | Planned Address | VLAN |
|---|---:|---:|
| OPNsense Production gateway | 192.168.1.1 | 10 |
| OPNsense Infrastructure gateway | 192.168.20.1 | 20 |
| Arista core switch | 192.168.20.2 | 20 |
| Proxmox management | 192.168.20.10 | 20 |
| UniFi OS Server | 192.168.20.21 | 20 |
| UniFi PoE switch | 192.168.20.30 | 20 |
| UniFi access point | 192.168.20.31 | 20 |
| OPNsense Servers gateway | 192.168.30.1 | 30 |
| TrueNAS SCALE | 192.168.30.40 | 30 |
| Synology DS920+ | 192.168.30.41 | 30 |
| Secondary Synology | 192.168.30.42 | 30 |

---

## Initial Access Policy

| Source | Destination | Initial Policy |
|---|---|---|
| Production | Internet | Allow |
| Production | Infrastructure | Allow management from selected administrator devices |
| Production | Servers | Allow required services |
| Infrastructure | Internet | Allow updates, DNS, and time services |
| Infrastructure | Other VLANs | Deny unless required |
| Servers | Internet | Allow required outbound access |
| Servers | Infrastructure | Deny by default |
| Lab | Production | Deny by default |
| Lab | Servers | Allow selected test services |
| IoT | Internet | Allow as required |
| IoT | Trusted networks | Deny by default |
| Cameras | Internet | Deny by default |
| Cameras | NVR or management host | Allow required traffic |
| Guest | Internet | Allow |
| Guest | Internal networks | Deny |

---

## Migration Notes

The existing network will remain operational while the new VLAN interfaces are introduced.

Migration will proceed one zone at a time, beginning with a test VLAN before moving management devices.

No management address will be changed until an alternate access path and rollback procedure have been confirmed.