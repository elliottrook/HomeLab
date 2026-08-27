# TrueNAS DIY SAS Storage Expansion Project

> Status: Ready
>
> Project owner: Jason
>
> Last updated: 2026-08-27

## Purpose

Add storage capacity without replacing the six serviceable 4 TB SAS disks or
buying a commercial disk shelf. Build a backplane-free, independently powered
eight-bay external enclosure connected directly to the two vacant x4 ports on
the existing LSI SAS 9300-16i HBA.

The enclosure provides eight additional physical and controller-addressable
drive positions. Physical completion does not authorize a particular ZFS pool
change: the Media pool layout must pass the separate storage-topology gate in
Milestone 4 before any validated disk becomes a pool member.

## Authoritative baseline

- [x] TrueNAS operates at `192.168.20.40` on Servers VLAN 20.
- [x] The `Media` pool is online as one six-disk RAIDZ2 data VDEV.
- [x] The six existing data disks are 4 TB SAS drives.
- [x] The existing controller is an LSI SAS 9300-16i HBA with four internal x4
  SFF-8643 Mini-SAS HD connectors.
- [x] Two complete SFF-8643 ports are vacant; each provides four direct SAS
  lanes, for eight additional drive connections.
- [x] The identified direct-attach cable type is CableDeconn H0204: SFF-8643 to
  four 29-pin SFF-8482 connectors with 15-pin power inputs, 1 m, rated for
  12 Gb/s SAS. Two matching assemblies are required for all eight bays; confirm
  whether expansion cables are already on hand before purchasing more.
- [x] All drive positions in the TrueNAS chassis are occupied.
- [x] TrueNAS application data, including Docker data, is stored under
  `Media/ix-apps`.
- [x] Commercial SAS/JBOD shelves and wholesale replacement with larger disks
  are outside the acceptable project budget.
- [x] The selected design is backplane-free.

## Architecture decision

Use a separate 400-500 W SFX power supply in the external enclosure. Do not
upgrade the TrueNAS PSU merely to power disks in another chassis.

The independent PSU is preferred because it:

- keeps additional disk spin-up current off the TrueNAS PSU and its existing
  wiring;
- avoids routing several high-current power leads between chassis;
- lets the enclosure use short native PSU power leads;
- preserves a clear electrical and mechanical boundary;
- permits enclosure cooling and disk power to be tested before pool changes;
- supports all eight external positions without another TrueNAS PSU change.

The external PSU must be synchronized with the TrueNAS server. An Add2PSU-style
board or equivalent 12 V-triggered isolated relay is the preferred
implementation. A manual ATX jumper/switch is acceptable only for an unloaded
bench prototype; it is not acceptable once pool-member disks are installed.

Both chassis must use the UPS-protected supply. The enclosure must be included
in the NUT shutdown/recovery design before the pool depends on it.

## Intended topology

```text
LSI SAS 9300-16i HBA
        |
        +-- occupied SFF-8643 ports 1-2 --> six existing internal SAS disks
        |
        +-- vacant SFF-8643 port 3
        |       +-- H0204 forward breakout --> external bays 1-4
        |
        +-- vacant SFF-8643 port 4
                +-- H0204 forward breakout --> external bays 5-8

Independent 400-500 W SFX PSU
        +-- native power harness A --> H0204 power inputs for bays 1-4
        +-- native power harness B --> H0204 power inputs for bays 5-8
        +-- two 120 mm enclosure fans
        +-- synchronized start/stop trigger from TrueNAS chassis
```

The controller and cable direction are now confirmed. The H0204 is a forward
breakout with the correct SFF-8482 SAS drive connector. Ordinary SATA-only or
reverse-breakout cables are not substitutes.

The 1 m H0204 assemblies are internal cables used across a chassis boundary in
this design. They must run directly from HBA to disk with no extension and must
be protected by rounded cable exits, grommets and independent strain relief at
both chassis. The internal SFF-8643 connector and PCB socket must never carry
the weight or movement of the external cable run.

## Scope

- Record the installed 9300-16i firmware, cooling, occupied-port mapping and
  disk identities; the model and eight-lane expansion capacity are confirmed.
- Use the MakerWorld NAS Hard Drive Bay / Enclosure V1 eight-bay design as the
  mechanical starting point, with the safety modifications in Milestone 2.
- Print structural parts in PETG, ASA or ABS and add positive drive retention,
  cable restraint and anti-tip support.
- Provide independent, synchronized SFX power and two-fan forced-air cooling.
- Connect all populated external bays directly to the HBA through two H0204
  forward breakouts, without a backplane, expander, port multiplier or hardware
  RAID layer.
- Pre-flight each new disk before adding it to the pool.
- Select and approve a ZFS topology separately. Do not turn eight available
  physical lanes into a fourteen-disk-wide RAIDZ2 VDEV by default.
- Add monitoring, UPS behaviour, physical labels, recovery instructions and
  final evidence to the relevant HomeLab documentation.

## Out of scope

- A commercial JBOD or enterprise disk shelf.
- A purchased hot-swap backplane.
- USB, eSATA, SATA port multipliers or USB-to-SAS/SATA bridges.
- Hardware RAID or one RAID0 logical disk per physical disk.
- Extending any RAIDZ2 VDEV beyond eight disks in this project.
- Adding a SAS expander or another HBA.
- Replacing all six existing disks with larger models.
- Treating pool redundancy as a backup.

## Recommended purchases

The HBA and cable type are confirmed. Confirm cable inventory, the selected
PSU's native connector count and one-bay fit before ordering the remaining
parts. Prices are intentionally not fixed because used-component and cable
pricing varies significantly.

### Selected printed enclosure assessment

Mechanical starting point:
[NAS Hard Drive Bay / Enclosure V1](https://makerworld.com/en/models/150766) by
plucbernier.

Inspection of the three supplied main-body STL files produced the following
external mesh envelopes:

| Supplied part | External envelope | Assessment |
|---|---:|---|
| Main body 1 | 132 x 218.6 x 185 mm | Eight repeated 3.5-inch drive positions |
| Main body 2 | 132 x 82 x 185 mm | PSU/transition portion |
| Main body 3 | 132 x 40 x 185 mm | End/base portion |
| Nominal assembled body | 132 x 340.6 x 185 mm | Tall enclosure requiring anti-tip support |

The main cage envelope and guide pitch are consistent with standard 3.5-inch
SAS disks, nominally up to 101.85 x 26.1 x 147 mm. The 185 mm enclosure depth
leaves only about 38 mm gross beyond the drive body before wall thickness,
connector length and cable bend are considered. The rear opening appears usable
for direct SFF-8482 breakouts, but this remains the critical physical fit.

Before the full multi-day print:

- print one drive position or a short rear-depth coupon;
- test it with the exact disk and H0204 SFF-8482 connector;
- verify that the drive slides without force and cannot move after retention is
  installed;
- verify the cable exits without a sharp bend or load on the drive connector;
- add a wide base, rubber feet and positive joining hardware between printed
  sections; and
- plan for approximately two filament spools, subject to the final slicer
  estimate and print settings.

### Required

| Item | Recommended specification | Quantity | Notes |
|---|---|---:|---|
| Printed enclosure | MakerWorld model 150766, three main-body sections and associated model parts | 1 set | Perform the one-bay/rear-clearance test before the complete print. |
| Filament | Quality PETG, ASA or ABS suitable for sustained drive temperatures | Approximately 2 kg | Final quantity comes from the selected slicer profile; do not use PLA for the structural cage. |
| Independent PSU | Reputable 400-500 W SFX PSU with adequate 12 V spin-up current, 5 V capacity and native peripheral leads | 1 | Size against the installed drives' labels/data sheets; target at least 20-25 A available on 12 V for an eight-drive design. |
| PSU synchronization | Add2PSU-style board or equivalent isolated ATX PSU synchronizer | 1 | Preferred over permanent paperclip/jumper operation. |
| Cooling fans | Quiet 120 mm 12 V fans with guards | 2 | Use the model's two fan positions for straight-through airflow across all disks. |
| Direct-attach SAS cables | CableDeconn H0204 SFF-8643 to 4 x SFF-8482 with 15-pin power inputs, 1 m | 2 total | Deduct verified spares already on hand; no extension, reverse breakout or SATA-only substitute. |
| PSU power harnesses | Native PSU leads matching every H0204 15-pin power input | 2 independent harnesses preferred | Allocate bays 1-4 and 5-8 across separate native harnesses; avoid loading all disks through one splitter. |
| Cable-exit protection | Rounded PCIe-slot exit plate, grommet/edge trim and independent clamps at both chassis | As required | Strain relief must act on the cable jacket, not the SFF-8643 socket or disk connector. |
| Drive retention and reinforcement | Printed or metal retention bar, through-bolts/washers or metal straps, wide feet | As required | The completed eight-drive tower must not depend on friction-only slots or printed snap tabs. |
| Pool expansion disks | CMR SAS disks compatible with the approved Milestone 4 topology | Staged, up to 8 | Do not buy a topology by accident; confirm VDEV/pool plan first. |

### Optional

- Washable fan filter if it does not materially restrict airflow.
- Fan splitter or simple temperature-aware fan controller.
- Small dedicated fan or duct providing forced airflow across the 9300-16i
  heatsinks if existing TrueNAS chassis airflow is inadequate.
- Two-pole illuminated enclosure power/status indicator.
- Grounded metal cable-exit plate or protective subframe where practical.

### Explicitly avoid

- Modular PSU cables not supplied for that exact PSU model.
- Moulded SATA-power splitters or questionable Molex-to-SATA adapters.
- Reverse-breakout cables.
- SATA-only connectors for SAS disks.
- Unsecured bare-drive stacks or friction-only printed slots.
- PLA close to disks, regulators or other sustained heat sources.
- SAS cable extensions or unrestrained internal SFF-8643 cables crossing the
  chassis boundary.
- Smart-plug automation as the only protection against incorrect shutdown
  order.

## Milestone 1 — Inventory and compatibility gate

- [x] Record the SAS HBA manufacturer, exact model and connector count: LSI SAS
  9300-16i with four internal x4 SFF-8643 ports.
- [ ] Record the HBA PCIe location, firmware version/mode and both controller
  instances reported by the operating system.
- [ ] Photograph and label the controller-side connectors and existing breakout
  cables.
- [x] Confirm that "two ports free" means two complete x4 SFF-8643 sockets,
  providing eight additional direct-attach lanes.
- [x] Record the current cable specification: CableDeconn H0204, 1 m,
  SFF-8643-to-4 x SFF-8482 forward breakout with 15-pin power inputs.
- [ ] Confirm whether two additional H0204 assemblies are already on hand and
  inspect their connectors and latches for damage.
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

Completion gate: the installed firmware and disk mapping, two vacant x4 ports,
two physical cable assemblies, PSU model/lead count, pool feature support and
rollback/recovery limits are verified before construction or disk purchase.

## Milestone 2 — Mechanical and electrical prototype

- [x] Select MakerWorld model 150766 as the eight-bay mechanical starting point
  and inspect its three supplied main-body STL meshes.
- [ ] Slice the complete model in PETG, ASA or ABS and record estimated filament,
  print time, orientation, wall count and infill.
- [ ] Print a one-bay/rear-depth test coupon and verify the exact drive plus
  H0204 connector and bend clearance.
- [ ] Print and assemble the complete carrier without relying on friction-only
  drive retention or load-bearing snap tabs.
- [ ] Add a wide anti-tip base, rubber feet and through-bolts, washers or metal
  straps tying the printed sections together.
- [ ] Fabricate rounded, independently clamped cable exits at the TrueNAS and
  enclosure chassis boundaries.
- [ ] Mount the PSU so its intake and exhaust are unobstructed.
- [ ] Mount two 120 mm guarded fans for straight-through disk airflow.
- [ ] Install guards, grommets, strain relief and physical drive labels.
- [ ] Install the PSU synchronizer without mixing modular PSU cables.
- [ ] Verify enclosure start and stop behaviour with no pool disk attached.
- [ ] Confirm the fan restarts after power loss and no cable can contact a fan.
- [ ] Confirm forced airflow across the 9300-16i heatsinks under simultaneous
  I/O; add a dedicated fan or duct if the TrueNAS tower does not provide it.
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

## Milestone 4 — Storage topology and controlled pool change

Eight physical bays do not imply that all disks belong in the existing VDEV.
Select exactly one documented topology before buying a batch of disks or
changing `Media`:

| Candidate | Advantages | Constraints |
|---|---|---|
| Extend the existing six-disk RAIDZ2 to seven and then no more than eight members | Lowest initial disk purchase; uses supported RAIDZ expansion if available | Only one or two external bays are used by this VDEV; each expansion is a production pool change |
| Add a complete six- or eight-disk RAIDZ2 VDEV to `Media` | Large capacity increase and all disks remain directly visible to ZFS | Requires the complete VDEV disk set at creation; failure of either VDEV loses the pool; existing data is not automatically rebalanced |
| Create a separate external pool | Separates failure and power domains logically and permits a different lifecycle | Capacity is not automatically combined with `Media`; datasets, shares and applications may need migration |

Default control: do not extend the existing RAIDZ2 beyond eight members. A
fourteen-disk-wide RAIDZ2 VDEV is not an approved use of the eight new lanes.

- [ ] Record required usable capacity, disk count/budget, failure-domain choice,
  application dependencies and backup coverage.
- [ ] Confirm the installed TrueNAS/OpenZFS capabilities and use only supported
  TrueNAS workflows.
- [ ] Approve one candidate topology and record its capacity, redundancy,
  replacement and rollback implications.
- [ ] Confirm every proposed member completed Milestone 3 and map each serial to
  its external bay, H0204 branch and PSU harness.
- [ ] Confirm the Media pool is healthy and complete a clean scrub immediately
  before any change involving `Media`.
- [ ] Capture a current TrueNAS configuration backup and recovery checkpoint.
- [ ] Pause avoidable high-write applications and confirm essential services'
  recovery paths.
- [ ] Execute only the approved TrueNAS UI workflow and monitor progress, disk
  temperatures, SAS errors, application availability and pool health.
- [ ] Confirm reported and practically available capacity, then run and pass the
  post-change scrub.
- [ ] Observe normal applications, SMB/NFS use, backups and controlled reboots
  for at least seven days before another pool-layout change.

Completion gate: the approved pool/VDEV topology is healthy; capacity,
services, scrubs, restart behaviour, thermals, SAS links and monitoring pass
without faults.

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
- Do not add a disk or VDEV merely because a physical bay is available; follow
  the approved Milestone 4 topology and change sequence.
- Do not continue an expansion if the pool, a current disk, the HBA, cabling,
  cooling, UPS or backup state is unhealthy.
- Do not exceed an approved eight-disk RAIDZ2 VDEV width in this project.

## Principal risks and controls

| Risk | Control |
|---|---|
| External PSU turns off before TrueNAS | Add2PSU synchronization, UPS/NUT integration and shutdown test |
| Internal cable is damaged crossing chassis boundaries | Direct 1 m run with no extension, rounded exits, grommets and independent strain relief at both chassis |
| Cable movement faults a pool member | Locking connectors, cable clamps, service loops and end-to-end labels |
| PSU overload during simultaneous spin-up | Size and test for maximum approved disk count with margin |
| Disk overheating in a dense printed carrier | Two 120 mm fans, unobstructed flow and monitored burn-in temperatures |
| 9300-16i overheats under added traffic | Verify chassis airflow across both HBA heatsinks and add a dedicated fan/duct if required |
| Tall printed enclosure tips or joints creep | PETG/ASA/ABS, wide base, rubber feet, positive drive retention and through-bolted/metal reinforcement |
| New/used disk fails during pool change | Full pre-flight, clean source pool, approved topology and staged change windows |
| Available ports encourage an unsafe VDEV width | Separate topology gate; no RAIDZ2 VDEV wider than eight members in this project |
| External enclosure becomes a pool dependency | Synchronized power, UPS protection, documented recovery and no casual power cycling |

## Definition of done

The project is complete when the backplane-free enclosure is mechanically safe,
independently and predictably powered, adequately cooled, UPS-aware and directly
connected across both vacant x4 ports of the existing HBA; every installed disk
has passed burn-in; the approved pool topology and change have passed health,
scrub and restart tests; and hardware, monitoring, backup and operating
procedures are current.

## Evidence log

| Date | Milestone | Evidence | Result |
|---|---|---|---|
| 2026-08-27 | Project definition | Six-disk RAIDZ2 baseline, full internal bays and backplane-free decision recorded | Proposed |
| 2026-08-27 | HBA and cable correction | LSI SAS 9300-16i confirmed with two vacant x4 SFF-8643 ports; H0204 SFF-8643-to-4 x SFF-8482 cable type identified; expansion capacity corrected from two to eight drives | Pass |
| 2026-08-27 | Printed enclosure assessment | Supplied MakerWorld model 150766 main-body meshes inspected; eight-bay geometry selected subject to one-bay SFF-8482 clearance test, reinforcement and strain relief | Ready for prototype |

## References

- [Broadcom LSI SAS 9300-16i quick installation guide](https://docs.broadcom.com/doc/12352362)
- [MakerWorld NAS Hard Drive Bay / Enclosure V1](https://makerworld.com/en/models/150766)
- [Seagate Exos 2X18 physical specifications](https://www.seagate.com/files/www-content/datasheets/pdfs/exos-2x18-DS2093-1-2202US-en_CA.pdf)
