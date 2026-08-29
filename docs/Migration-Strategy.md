# Project Mini Atlas Migration Strategy

**Status:** In progress

**Phase:** Enterprise Network  
**Last Updated:** 2026-08-08

---

# 1. Purpose

This document defines the migration strategy for transitioning Project Mini Atlas from a flat network to a segmented VLAN-based architecture.

The primary objective is to introduce the new design without unnecessary downtime while maintaining a clear rollback path at every stage.

---

# 2. Guiding Principles

The migration will follow these rules:

- Never make more than one significant network change at a time.
- Validate every stage before continuing.
- Maintain management access throughout the migration.
- Keep a tested rollback path for every stage.
- Back up configurations before making changes.
- Update documentation after every completed stage.

---

# 3. Current Environment

Current LAN

```
192.168.1.0/24

OPNsense LAN
↓

Arista Ethernet40

↓

Everything
```

Current characteristics:

- Flat network
- OPNsense provides routing, DHCP and firewall services.
- Arista provides Layer 2 switching.
- VLAN 10 carries trusted/native traffic.
- VLAN 30 carries isolated IoT traffic.
- VLAN 40 carries isolated Guest traffic.
- OPNsense LAN interface is `ix0`.
- OPNsense connects to Arista `Ethernet40` using a 10 Gb trunk.

---

# 4. Target Environment

```
Internet
    │
OPNsense
    │
10 Gb 802.1Q Trunk
    │
Arista Ethernet40
    │
──────────────────────────────────
Trusted
Servers
IoT
Guest
Management
Cameras
```

## Current progress

- Phase 1 preparation and recovery checkpoints are complete.
- The core Et42 trunk is operational with native VLAN 10 and tagged VLANs 20, 30, 40, 50, 60 and 70.
- The UniFi uplink on Et33 carries native VLAN 10 and tagged VLANs 30, 40, 50 and 60.
- IoT VLAN 30 and Guest VLAN 40 are deployed and validated in production.
- Routed infrastructure and baseline policy are deployed for Servers, Management, Cameras and Lab. Existing management and storage hosts remain on Trusted pending later migration windows; Frigate is the first production workload on Servers.

---

# 5. Migration Phases

## Phase 1 – Preparation

- Review documentation.
- Confirm backups.
- Verify SSH access.
- Verify console access.
- Confirm rollback procedures.

Success Criteria

- No configuration changes.
- Recovery procedures confirmed.

---

## Phase 2 – Build VLAN Framework

Tasks

- Create VLAN interfaces on OPNsense.
- Configure DHCP.
- Configure DNS.
- Configure firewall interfaces.

Success Criteria

- Existing LAN remains operational.
- New VLAN interfaces exist.
- No devices migrated.

Rollback

- Remove VLAN interfaces.

---

## Phase 3 – Configure Core Trunk

Tasks

- Maintain Arista Ethernet40 as an 802.1Q trunk.
- Maintain VLAN 10 as the native (untagged) VLAN.
- Add only each required tagged VLAN during its implementation window.

Success Criteria

- Existing LAN remains operational.
- Tagged VLANs available.

Rollback

- Restore Ethernet40 from the saved pre-change configuration.

---

## Phase 4 – Infrastructure Migration

Move:

- Arista management
- Proxmox management
- UniFi controller
- UniFi switch
- Access points

Success Criteria

Infrastructure devices reachable using their new management addresses.

Rollback

Return devices to VLAN 10.

---

## Phase 5 – Server Migration

Move:

- TrueNAS
- Synology
- Future self-hosted services

Success Criteria

Storage and services operate normally.

Rollback

Return servers to VLAN 10.

---

## Phase 6 – Lab Migration

Move:

- Experimental systems
- Temporary virtual machines

Success Criteria

Lab isolated from trusted devices.

Rollback

Return systems to VLAN 10.

---

## Phase 7 – IoT and Cameras

Move:

- IoT devices
- Cameras

Success Criteria

Devices function normally while remaining isolated.

Rollback

Return affected devices to VLAN 10.

---

## Phase 8 – Guest Network

Create:

- Guest SSID
- Guest VLAN
- Internet-only firewall policy

Success Criteria

Guests have Internet access but no internal access.

Rollback

Disable Guest VLAN.

---

# 6. Validation Checklist

After every phase verify:

- Internet connectivity
- DNS
- DHCP
- SSH
- Web management
- Firewall policy
- Device communication
- Backup success
- `lab doctor`

Only continue if all checks pass.

---

# 7. Rollback Philosophy

Every migration stage must be independently reversible.

If unexpected behaviour occurs:

1. Stop.
2. Restore the previous configuration.
3. Verify normal operation.
4. Investigate before attempting the change again.

No rollback should require rebuilding the network from memory.

---

# 8. Completion Criteria

The migration is complete when:

- All planned VLANs are operational.
- All devices are documented.
- Firewall policy matches the design.
- Documentation reflects the final environment.
- Configuration backups have been updated.
- Project Mini Atlas is operating entirely from the documented architecture.
