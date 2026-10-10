# Beszel and NetBox Coverage Reconciliation — 2026-10-08

> Status: Complete — Stream M
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
- Added four narrowly scoped OPNsense rules allowing only the four Lab VLAN 70
  Beszel agent addresses (`192.168.70.12`, `.13`, `.14` and `.15`) to reach
  `192.168.20.20:8090`; the rules are above the Lab-to-RFC1918 deny and the
  firewall filter reload completed successfully.

## Completion evidence

- Beszel now reports all 18 retained systems `up` (the 16 retained Proxmox
  guests plus Proxmox and the NUT server). The four previously blocked agents
  connected after the firewall reload.
- NetBox API validation reports 18 VM interfaces with no missing MAC or VLAN
  values; the interface mode and VLAN facts match current Proxmox
  configuration.
- The Beszel enrollment-token staging file was removed after validation.
- OPNsense pre-change backup:
  `/conf/backup/config-beszel-coverage-before-20261009-010139.xml`, SHA-256
  `6bb1688fc89c41a6874fd5759ca142c33472cbb4ad3a3e406977d739b42b9103`.

## Closed risk

The four Lab VLAN 70 agents initially timed out at the hub because the
existing firewall permitted only the prior Aster path. The approved,
source/destination/port-scoped rules resolved that reachability gap without
changing the VLAN isolation policy. The existing service-native and Doctor
checks remain unchanged.

## Rollback

- Stop and disable only the newly installed `beszel-agent` services, remove
  their Beszel systems/fingerprint records, and restore the retained Beszel
  database checkpoint if record rollback is required.
- Revert only the 18 NetBox VM-interface fields to their prior values; do not
  restore the whole NetBox database over unrelated changes.
