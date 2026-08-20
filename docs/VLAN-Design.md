# Project Mini Atlas VLAN Design

**Status:** Routed VLAN infrastructure implemented

**Phase:** Enterprise Network  
**Last Updated:** 2026-08-19

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
| 20 | Servers | 192.168.20.0/24 | 192.168.20.1 | Proxmox workloads and self-hosted services; implemented |
| 30 | IoT | 192.168.30.0/24 | 192.168.30.1 | Smart-home and embedded consumer devices; implemented |
| 40 | Guest | 192.168.40.0/24 | 192.168.40.1 | Internet-only guest access; implemented |
| 50 | Management | 192.168.50.0/24 | 192.168.50.1 | Network equipment, hypervisor management, controllers and access points; infrastructure implemented |
| 60 | Cameras | 192.168.60.0/24 | 192.168.60.1 | Isolated surveillance cameras; implemented |
| 70 | Lab | 192.168.70.0/24 | 192.168.70.1 | Experimental Proxmox VMs and temporary test workloads; infrastructure implemented |

---

## Design Decisions

### Preserve the existing production subnet

The existing `192.168.1.0/24` network will remain the Production network on VLAN 10.

This minimizes disruption and allows devices to be migrated gradually.

### Separate management and servers

Network management devices will belong to VLAN 50.

Storage systems and application services will belong to VLAN 20.

This creates a clear distinction between the systems that operate the network and the services delivered through it.

### Isolate experimental workloads

Temporary and experimental Proxmox workloads will use VLAN 70 rather than sharing the trusted or production-server networks.

The Proxmox host management address remains on the native trusted network during the initial Lab rollout and can move to VLAN 50 only during a separate management migration. Production LXCs and VMs are not moved as part of the Lab change.

A Lab VM must not also have an interface on Trusted, Servers or Management unless that dual-homed design is explicitly required, reviewed and documented. This prevents a test workload from becoming an unintended path around OPNsense policy.

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
| 70 | 192.168.70.100–192.168.70.199 | 192.168.70.2–192.168.70.99 |

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
| UniFi Hall access point | 192.168.50.31 | 50 |
| UniFi Office access point | 192.168.50.141 | 50 |
| OPNsense Lab gateway | 192.168.70.1 | 70 |
| Experimental Proxmox workloads | 192.168.70.0/24 | 70 |
| Hermes Agent LXC 104 | 192.168.70.10 | 70 |
| Ollama VM 105 | 192.168.70.11 | 70 |
| Frigate VM 102 | 192.168.20.10 | 20 |
| Reolink Duo 2V PoE | 192.168.60.10 | 60 |

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
| Selected administrator devices | Lab | Allow management and testing |
| Lab | OPNsense Lab address | Allow DHCP, DNS and NTP only |
| Lab | Internet | Allow outbound access |
| Lab | RFC1918 internal networks | Deny by default |
| IoT | Internet | Allow as required |
| IoT | Trusted networks | Deny by default |
| Cameras | Internet | Deny by default |
| Cameras | NVR or management host | Allow required traffic |
| Guest | Internet | Allow |
| Guest | Internal networks | Deny |

---

## Lab VLAN 70 Design

### Intended topology

```text
OPNsense ix0 trunk
  +-- VLAN 70 gateway: 192.168.70.1
             |
             | Arista Et40 trunk
             v
Arista core: VLAN 70
             |
             | Et4 trunk: native VLAN 10, tagged VLANs 20,70
             v
Proxmox vmbr0: VLAN-aware
  +-- Host management 192.168.1.10: untagged/native VLAN 10
  +-- Existing LXC 100 and 101: untagged/native VLAN 10
  +-- Experimental VM NICs: tagged VLAN 70
```

The current persistent Lab workloads are Hermes Agent LXC 104 at
`192.168.70.10` and Ollama VM 105 at `192.168.70.11`. They use only tagged VLAN
70 interfaces and do not receive secondary interfaces on Trusted, Servers or
Management.

The physical Proxmox link carries both networks, but each experimental virtual NIC receives VLAN tag 70. The bare-metal host and existing production containers continue using untagged/native VLAN 10.

### Planned components

- OPNsense VLAN interface on parent `ix0`, tag 70, address `192.168.70.1/24`.
- Dnsmasq DHCP range `192.168.70.100-192.168.70.199` with OPNsense providing gateway and DNS.
- Arista VLAN 70 named `Lab`.
- Arista Ethernet4 converted from an access port to a trunk with native VLAN 10 and allowed VLANs 10, 20 and 70.
- Proxmox bridge `vmbr0` made VLAN-aware without moving the host address.
- VLAN tag 70 assigned per experimental VM or container virtual NIC.
- An administrator-device alias used for narrowly scoped inbound management access to Lab systems.

### Planned OPNsense rule order

1. Permit DHCP for Lab clients.
2. Permit TCP/UDP DNS from the Lab network to the Lab interface address.
3. Permit UDP NTP from the Lab network to the Lab interface address.
4. Block remaining Lab access to the firewall itself.
5. Block Lab access to RFC1918 networks.
6. Permit remaining Lab IPv4 traffic to the Internet.

Inbound access from selected trusted administrator devices to Lab workloads is defined on the source interface and is not created as a broad Lab-to-Trusted exception.

### Validation and future workload checklist

1. Confirm fresh OPNsense, Arista and Proxmox recovery copies and local console access.
2. Create the OPNsense interface, DHCP scope and rules without moving existing clients.
3. Add VLAN 70 to the OPNsense and Proxmox-facing Arista trunks while retaining native VLAN 10.
4. Enable VLAN awareness on `vmbr0` using Proxmox's tested network-change workflow.
5. Attach one disposable test VM to VLAN 70.
6. Verify DHCP, gateway, DNS, Internet access and administrative access.
7. Verify the test VM cannot reach Trusted, Servers, Management, IoT, Cameras or Guest networks.
8. Save configurations only after validation; remove VLAN tags 20 and 70 and restore Et4 access mode if rollback is required.

The OPNsense interface, DHCP scope, firewall policy, Arista VLAN transport and
VLAN-aware Proxmox bridge are deployed. Validation completed on 2026-08-11 with
a disposable unprivileged LXC 970 attached to `vmbr0` with tag 70. The test
received `192.168.70.112`, both Pi-hole resolvers, Internet TCP/443 access and
the expected Lab domain. It could reach only the two Pi-hole DNS endpoints on
internal networks; Proxmox, UniFi, Frigate and camera web endpoints were
blocked. The temporary container was stopped and purged after validation.

During validation, the OPNsense Lab VLAN was found incorrectly attached to
`igb0`. A pre-change OPNsense backup was created, the parent was corrected to
the production trunk `ix0`, carrier and DHCP were verified, and the full
isolation test then passed. No persistent experimental workload is currently
assigned to VLAN 70.

---

## Cameras VLAN 60 Implementation

- OPNsense interface `vlan0.60` uses `192.168.60.1/24` on parent `ix0`.
- Dnsmasq serves `192.168.60.100-192.168.60.199`; the Reolink camera has the
  reservation `192.168.60.10`.
- Arista carries VLAN 60 over Et40 to OPNsense and Et33 to the UniFi PoE
  infrastructure.
- Cameras are blocked from the firewall and RFC1918 destinations by default.
- A narrowly scoped rule on the Servers interface permits Frigate
  `192.168.20.10` to reach camera `192.168.60.10` on TCP 80, 554 and 8000.
- Camera TCP 9000 is not allowed from Frigate.
- HTTP, RTSP and ONVIF tests succeeded from Frigate; continuous recording to
  TrueNAS NFS was validated after a full VM reboot.

---

## Migration Notes

The existing network will remain operational while the new VLAN interfaces are introduced.

VLANs 20, 30, 40, 50, 60 and 70 now have routed OPNsense interfaces, DHCP
scopes and baseline firewall policy. VLAN 10 remains the native trusted
network. The UniFi controller, PoE switch and two access points have moved to
Management VLAN 50. Proxmox and Arista management remain on Trusted VLAN 10;
their future moves remain separate controlled migrations.

No management address will be changed until an alternate access path and rollback procedure have been confirmed.
