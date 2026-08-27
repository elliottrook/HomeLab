# TrueNAS DIY SAS Storage Expansion Project

> Status: Proposed
>
> Project owner: Jason
>
> Last updated: 2026-08-27

## Purpose

Add storage capacity to the existing TrueNAS Media pool without replacing its
six serviceable 4 TB SAS disks or buying a commercial disk shelf. Build a
backplane-free, independently powered external enclosure that uses the two
remaining disk endpoints on the existing PCIe SAS controller.

The first implementation is deliberately limited to one or two additional
disks. The mechanical design can provide more physical positions, but further
controller or pool expansion is a separate decision after this project is
validated.

## Authoritative baseline

- [x] TrueNAS operates at `192.168.20.40` on Servers VLAN 20.
- [x] The `Media` pool is online as one six-disk RAIDZ2 data VDEV.
- [x] The six existing data disks are 4 TB SAS drives.
- [x] The existing PCIe SAS controller presents the six disks and Jason reports
  two unused disk endpoints.
- [x] All drive positions in the TrueNAS chassis are occupied.
- [x] TrueNAS application data, including Docker data, is stored under
  `Media/ix-apps`.
- [x] Commercial SAS/JBOD shelves and wholesale replacement with larger disks
  are outside the acceptable project budget.
- [x] The selected design is backplane-free.

## Architecture decision

Use a separate ATX power supply in the external enclosure. Do not upgrade the
TrueNAS PSU merely to power disks in another chassis.

The independent PSU is preferred because it:

- keeps additional disk spin-up current off the TrueNAS PSU and its existing
  wiring;
- avoids routing several high-current power leads between chassis;
- lets the enclosure use short native PSU power leads;
- preserves a clear electrical and mechanical boundary;
- permits enclosure cooling and disk power to be tested before pool changes;
- can later support more physical positions without another TrueNAS PSU change.

The external PSU must be synchronized with the TrueNAS server or managed by a
documented manual sequence. An Add2PSU-style synchronization board is the
preferred implementation. A manual ATX jumper/switch is acceptable during the
prototype only if the enclosure is powered before TrueNAS starts and remains
powered until TrueNAS has fully shut down.

Both chassis must use the UPS-protected supply. The enclosure must be included
in the NUT shutdown/recovery design before the pool depends on it.

## Intended topology

```text
Existing PCIe SAS HBA
        |
        +-- six existing internal SAS disks
        |
        +-- free disk endpoint 1 --> external SFF-8482 SAS disk
        +-- free disk endpoint 2 --> external SFF-8482 SAS disk

Independent ATX PSU
        +-- disk power
        +-- enclosure fan power
        +-- synchronized start/stop trigger from TrueNAS chassis
```

The exact controller-side connector is not yet recorded. No data cable may be
purchased until the HBA model, connector and existing breakout wiring are
verified. SAS disks require SFF-8482 drive connectors; ordinary SATA-only
breakout cables are not substitutes.

## Scope

- Inventory the existing HBA, firmware, connectors, cabling and disk mapping.
- Confirm that the reported two free ports are two usable disk endpoints.
- Design or select a PETG/ABS printed carrier with positive screw retention.
- Reuse a suitable protective case where practical.
- Provide independent, synchronized ATX power and forced-air cooling.
- Connect SAS data directly from the HBA to each disk without a backplane,
  expander, port multiplier or hardware RAID layer.
- Pre-flight each new disk before adding it to the pool.
- If the installed TrueNAS/OpenZFS version supports it, extend the existing
  RAIDZ2 VDEV from six to seven disks and optionally from seven to eight disks,
  one disk and one completed validation cycle at a time.
- Add monitoring, UPS behaviour, physical labels, recovery instructions and
  final evidence to the relevant HomeLab documentation.

## Out of scope

- A commercial JBOD or enterprise disk shelf.
- A purchased hot-swap backplane.
- USB, eSATA, SATA port multipliers or USB-to-SAS/SATA bridges.
- Hardware RAID or one RAID0 logical disk per physical disk.
- Extending the current RAIDZ2 VDEV beyond eight disks in this project.
- Adding a SAS expander or another HBA.
- Replacing all six existing disks with larger models.
- Treating pool redundancy as a backup.

## Recommended purchases

Purchase only after Milestone 1 confirms connector types and available space.
Prices are intentionally not fixed because used-component and cable pricing
varies significantly.

### Required

| Item | Recommended specification | Quantity | Notes |
|---|---|---:|---|
| External enclosure | Reused metal PC case or other grounded/protective chassis | 1 | Prefer reuse over printing an entire exposed enclosure. |
| Drive carrier | PETG or ABS printed carrier with standard drive screws and 8–12 mm airflow gaps | 1 | Two positions required now; additional unpopulated positions are acceptable. |
| Independent PSU | Reputable 350–500 W ATX PSU, 80 PLUS rated, sufficient native power leads | 1 | A known-good reused unit is acceptable after inspection and load testing. |
| PSU synchronization | Add2PSU-style board or equivalent isolated ATX PSU synchronizer | 1 | Preferred over permanent paperclip/jumper operation. |
| Cooling fan | Quiet 120 or 140 mm 12 V fan with guard | 1–2 | Airflow must pass across the drive bodies, not only the connectors. |
| Data cable | Forward-breakout cable matching the confirmed HBA connector and ending in SFF-8482 SAS drive connectors | As required | Do not buy a reverse-breakout or SATA-only cable. |
| Disk power interface | Native connector required by the selected SFF-8482 breakout assembly | As required | Prefer native PSU leads; avoid moulded low-quality power splitters. |
| Cable protection | Grommet, edge trim and strain relief at both chassis openings | As required | No cable may rest against an unfinished metal edge. |
| Pool expansion disk | CMR SAS disk at least as large as the smallest current VDEV member | 1 initially | Matching 4 TB model/geometry is preferred where economical. |

### Conditional cable selection

- For an HBA with **SFF-8087**, use an SFF-8087-to-SFF-8482 **forward**
  breakout with the correct power tails.
- For an HBA with **SFF-8643**, use an SFF-8643-to-SFF-8482 **forward**
  breakout with the correct power tails.
- If the controller actually has a free external **SFF-8088** or **SFF-8644**
  connector, use the matching external forward-breakout or a properly secured
  external-to-internal transition.
- If the two unused endpoints are free branches on a cable that also serves two
  internal drives, verify length, connector retention and bend radius before
  deciding whether that cable may cross between chassis.

### Optional

- Washable fan filter if it does not materially restrict airflow.
- Fan splitter or simple temperature-aware fan controller.
- Rubber isolation feet between the printed carrier and enclosure.
- Two-pole illuminated enclosure power/status indicator.
- A second matching 4 TB SAS disk after the first expansion passes its
  observation gate.

### Explicitly avoid

- Modular PSU cables not supplied for that exact PSU model.
- Moulded SATA-power splitters or questionable Molex-to-SATA adapters.
- Reverse-breakout cables.
- SATA-only connectors for SAS disks.
- Unsecured bare-drive stacks or friction-only printed slots.
- PLA close to disks, regulators or other sustained heat sources.
- Smart-plug automation as the only protection against incorrect shutdown
  order.

## Milestone 1 — Inventory and compatibility gate

- [ ] Record the SAS HBA manufacturer, exact model, PCIe location and firmware.
- [ ] Photograph and label the controller-side connectors and existing breakout
  cables.
- [ ] Confirm whether "two ports free" means two drive endpoints, two complete
  multi-lane sockets or another arrangement.
- [ ] Record all six current disk serials, `/dev/disk/by-id` identities,
  controller paths and physical positions.
- [ ] Record the TrueNAS version and confirm RAIDZ extension support and pool
  feature compatibility.
- [ ] Capture `zpool status -P Media`, pool capacity, fragmentation and the last
  successful scrub result.
- [ ] Measure current disk temperatures during representative activity.
- [ ] Confirm the TrueNAS and external-enclosure UPS outlets and NUT shutdown
  dependency.
- [ ] Confirm an off-host copy of TrueNAS configuration, application
  configuration and other irreplaceable data before pool work.

Completion gate: the two usable disk paths, exact cable specification, power
method, pool feature support and rollback/recovery limits are known before any
purchase.

## Milestone 2 — Mechanical and electrical prototype

- [ ] Select a reused protective enclosure and record its available dimensions.
- [ ] Print a PETG/ABS carrier with screw retention, airflow gaps and no sharp or
  load-bearing printed tabs.
- [ ] Mount the PSU so its intake and exhaust are unobstructed.
- [ ] Mount at least one 120/140 mm fan for straight-through disk airflow.
- [ ] Install guards, grommets, strain relief and physical drive labels.
- [ ] Install the PSU synchronizer without mixing modular PSU cables.
- [ ] Verify enclosure start and stop behaviour with no pool disk attached.
- [ ] Confirm the fan restarts after power loss and no cable can contact a fan.
- [ ] Confirm the PSU has sufficient spin-up margin for the maximum approved
  number of disks, not only the first disk.

Completion gate: the empty enclosure powers, cools and follows the documented
TrueNAS power sequence without exposed conductors, unrestrained drives or unsafe
cable routing.

## Milestone 3 — Disk and connection validation

Repeat this milestone for each new disk before pool membership.

- [ ] Install one disk and confirm TrueNAS reports its unique serial, capacity,
  SAS link and SMART data correctly.
- [ ] Confirm no existing disk identity or controller path changed unexpectedly.
- [ ] Run the long SMART self-test and review pending/reallocated/error counters.
- [ ] Perform a destructive burn-in/read-write test only while the disk is
  positively identified as unassigned and contains no required data.
- [ ] Exercise simultaneous disk and network I/O while monitoring temperatures,
  controller errors, PSU behaviour and cable stability.
- [ ] Restart the enclosure and TrueNAS in the documented order while the test
  disk remains outside the pool.
- [ ] Record the final disk serial, bay, cable branch and power lead mapping.

Completion gate: the new disk and direct cable remain error-free, individually
identifiable and adequately cooled through burn-in and controlled restart tests.

## Milestone 4 — Controlled RAIDZ2 extension

- [ ] Confirm the Media pool is healthy and complete a clean scrub immediately
  before expansion.
- [ ] Capture a current TrueNAS configuration backup and recovery checkpoint.
- [ ] Pause avoidable high-write applications and confirm essential services'
  recovery paths.
- [ ] Use the supported TrueNAS UI workflow to extend the existing RAIDZ2 VDEV
  by exactly one validated disk.
- [ ] Monitor extension progress, disk temperatures, SAS errors, application
  availability and pool health until complete.
- [ ] Confirm reported and practically available capacity after expansion.
- [ ] Run and pass the post-expansion scrub.
- [ ] Observe normal applications, SMB/NFS use, backups and reboots for at least
  seven days before considering another disk.
- [ ] Repeat the complete pre-flight and extension process for the optional
  eighth disk; do not add both disks in one change window.

Completion gate: the Media VDEV is healthy at seven disks, or at eight disks if
the optional second change is approved; services, scrubs, reboots and monitoring
pass without SAS, power or thermal faults.

## Milestone 5 — Operations and hand-back

- [ ] Add the enclosure and disk mapping to `docs/03-Hardware-Inventory.md`.
- [ ] Add power-on, shutdown, disk replacement and emergency-disconnection
  prohibitions to `docs/04-Operations.md`.
- [ ] Reconcile configuration/application backup coverage in
  `docs/05-Backups.md`.
- [ ] Add actionable enclosure, SMART, temperature and pool checks to HomeLab
  Doctor and/or Beszel where dependable signals exist.
- [ ] Validate the NUT-controlled shutdown with both chassis on UPS power.
- [ ] Label both ends of every SAS and power connection.
- [ ] Record final usable capacity, operating temperatures and accepted risks.
- [ ] Update this project status and evidence log.

## Safety and operational rules

- Never switch off, unplug or service the enclosure while the Media pool is
  imported.
- Shut TrueNAS down cleanly before removing disk data or power connections.
- The enclosure must be powered before TrueNAS boots and remain powered until
  TrueNAS has fully shut down.
- Keep both chassis on the same UPS-protected power system.
- Add only one disk to the VDEV at a time and wait for validation to complete.
- Do not continue an expansion if the pool, a current disk, the HBA, cabling,
  cooling, UPS or backup state is unhealthy.
- Do not exceed the approved eight-disk VDEV width in this project.

## Principal risks and controls

| Risk | Control |
|---|---|
| External PSU turns off before TrueNAS | Add2PSU synchronization, UPS/NUT integration and shutdown test |
| Wrong SAS cable direction or connector | Inventory gate, photographs and connector-specific purchase approval |
| Cable movement faults a pool member | Grommets, locking connectors, strain relief and end-to-end labels |
| PSU overload during simultaneous spin-up | Size and test for maximum approved disk count with margin |
| Disk overheating in a dense printed carrier | Forced airflow, spacing and monitored burn-in temperatures |
| New/used disk fails during extension | Full pre-flight, clean source pool and one-disk change windows |
| Expansion reduces fault-tolerance margin | RAIDZ2 remains two-disk tolerant; stop at eight members and retain backups |
| External enclosure becomes a pool dependency | Synchronized power, UPS protection, documented recovery and no casual power cycling |

## Definition of done

The project is complete when the backplane-free enclosure is mechanically safe,
independently and predictably powered, adequately cooled, UPS-aware and directly
connected to the existing HBA; at least one new disk has passed burn-in and a
supported RAIDZ2 extension; the Media pool, applications, scrubs and restart
tests pass; and hardware, monitoring, backup and operating procedures are
current.

## Evidence log

| Date | Milestone | Evidence | Result |
|---|---|---|---|
| 2026-08-27 | Project definition | Six-disk RAIDZ2 baseline, two reported free SAS disk endpoints, full internal bays and backplane-free decision recorded | Proposed |
