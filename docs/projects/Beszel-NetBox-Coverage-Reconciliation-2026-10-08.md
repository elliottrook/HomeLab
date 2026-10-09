# Beszel and NetBox Coverage Reconciliation — 2026-10-08

> Status: Active — Stream M
>
> Owner: Jason
>
> Started: 2026-10-08

## Purpose and scope

Reconcile live Proxmox guests with Beszel coverage and reconcile NetBox VM
interfaces with the authoritative Proxmox network configuration. Stopped test
guests, appliance-native monitoring and unrelated service-catalog expansion are
excluded.

## Current evidence

- Proxmox has 17 running guests: LXC 100, 101, 104, 106–117 and VMs 102–103.
- Beszel had seven systems before this work: Docker, Forgejo, Frigate,
  Hermes, Proxmox, NetBox and NUT.
- NetBox had all 18 guest records and all 18 primary IP assignments, but VM
  interfaces lacked VLAN assignments and six interfaces lacked MAC records.
- Stopped VM 105 and fixture VMs 118–123 remain excluded from Beszel; TrueNAS,
  Synology and OPNsense remain under Prometheus/Doctor/native monitoring.

## Changes applied

- Added Beszel systems and unique agent tokens for active LXC 101, 106, 107,
  109, 110, 112, 113, 114, 115, 116 and 117.
- Installed pinned Beszel agent 0.18.7 on those guests. Home Assistant OS VM
  103 is intentionally excluded because it is an appliance guest, not a
  normal Debian agent target.
- Updated all 18 NetBox VM interfaces from Proxmox `net0`: MAC address,
  `access` mode and VLAN 20, 50 or 70. API validation reports no missing MAC
  or VLAN values.
- Added a private pre-change Beszel database checkpoint on the Docker guest.

## Pending validation / risk

Seven of the eleven new Beszel systems report `up`. Four Lab VLAN 70 agents
(LXC 110, 114, 115 and 116) are installed and running but cannot reach the
Beszel hub because the current firewall permits only the existing Aster path
from that VLAN. No Lab VLAN firewall rule was added by this change yet.

Completion requires either a narrowly scoped, explicitly approved path for
those four source addresses to the Beszel hub, or an explicit exclusion with
the reason recorded here. The existing service-native and Doctor checks remain
unchanged.

## Rollback

- Stop and disable only the newly installed `beszel-agent` services, remove
  their Beszel systems/fingerprint records, and restore the retained Beszel
  database checkpoint if record rollback is required.
- Revert only the 18 NetBox VM-interface fields to their prior values; do not
  restore the whole NetBox database over unrelated changes.
