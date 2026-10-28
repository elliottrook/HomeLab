# SA2 NetBox network producer boundary — 2026-10-28

## Result

**SOURCE-ONLY PASS; NOT DEPLOYED.** A fifth fixed read-only producer can now
turn the existing validated NetBox report into aggregate network-inventory
evidence. It cannot contact NetBox, refresh a report, discover a target, run a
subprocess, use a credential or change infrastructure.

## Model-visible boundary

The adapter emits only:

- counts of devices, virtual machines, sites, racks, VLANs and prefixes;
- a 24-character digest of the validated report;
- the fixed pair `netbox-main/network` and producer identity
  `netbox-main-report/v1`.

Names, IP addresses, roles, device types, clusters, sites, racks, VLAN names,
prefix values and placement do not enter incident evidence. A missing, stale,
malformed or untrusted report becomes one content-free `unavailable`
observation. An accepted report produces `state=ok` only to mean that inventory
evidence is available; it does not claim that the network is healthy.

## Validation

- The focused adapter, producer, investigation, selector, proposal-boundary and
  transport suite passes **52/52** locally.
- The same temporary candidate passes **52/52** under LXC104's application
  Python and installed dependencies.
- One read-only target compatibility check consumed no incident decision and
  returned aggregate counts only: 23 devices, 22 virtual machines, one site,
  one rack, seven VLANs and seven prefixes, with digest
  `c29c92bf139d5be0688e530b`.
- The live report remained root-owned, group-readable to Aster, non-writable by
  group/other and bounded at 8,671 bytes.
- Temporary target files were removed. No service, model, route, incident
  database, report or schedule changed.

The next gate is a reviewed exact release combined with another source where
possible so deployment does not spend a restart on each individual adapter.
Backup, log and configuration evidence remain open.
