# Hardware Inventory

- VMware SD-WAN Edge 620 (OPNsense) — corrected 2026-09-01 via physical
  rack photo confirmation during the NetBox DCIM project's rack
  walk-through; previously misrecorded here and in `CLAUDE.md` as a
  "Dell EMC E42W (SD-WAN Edge 610)"
- Arista DCS-7050TX
- Binarui AP Switch
  - Four 2.5Gb PoE ports; ports 1 and 2 serve the U7 Pro XG access points and
    ports 3 and 4 are spare preconfigured AP trunks
  - 10Gb SFP+ uplink on port 6 to Arista Et33
  - Port 5 is reserved for direct VLAN 1 management recovery
  - Operated as an as-is appliance under a multi-week burn-in trial; no firmware
    update was attempted because no trustworthy exact-model image source was
    identified
- TP-Link 8-port 1Gb PoE switch
  - Camera-only role behind Arista Et34 access VLAN 60 — validated and in
    production since 2026-08-27, after the old UniFi PoE switch failed and
    was replaced by the AP Switch (APs only, no cameras). `front_of_house`
    (Reolink Duo 2V) runs on port 1, stable for several days as of
    2026-08-30.
- Dell Precision T5810 (Proxmox)
  - Current CPU: Intel Xeon E5-2698 v4 (`lscpu` reconfirmed 2026-08-31)
  - Current memory: 32 GB ECC RDIMM; additional planned RAM remains to be installed and the final total must be confirmed
  - Coral Edge TPU `G650-04527-01` on a PCIe A+E-key carrier, passed through to Frigate VM 102
  - ASRock Intel Arc Pro B60 24 GB (`8086:e211`, subsystem `1849:6023`)
    installed behind its onboard PCIe switch; the board-facing link negotiates
    PCIe 3.0 x8 on this host. GPU function `04:00.0` is currently bound to the
    host `xe` driver and mapped into unprivileged inference LXC 110; the earlier
    VM 105 passthrough configuration remains only as a stopped rollback path.
    The unused audio function `05:00.0` is isolated separately in group 57.
  - The B60 currently exposes a 256 MB physical BAR. The Proxmox `xe` driver
    attempted to resize it to 32 GB but the platform could not allocate the
    aperture. Level Zero/OpenCL/OVMS cannot enumerate the GPU with this BAR,
    while Mesa Vulkan acceleration works through the `xe`-backed LXC path.
  - Quadro K620 removed.
  - Confirmed live 2026-08-30 (physical install completed same day): `lspci`
    shows the Battlemage GPU present, and `qm config 105` confirms
    `hostpci0: 04:00.0,pcie=1,rombar=0` assigned to Ollama VM 105 as
    documented above. Ollama's host-RAM footprint now fluctuates with active
    load (observed 7.5–15.7 GiB available across two closely-spaced reads)
    rather than holding a large static allocation, consistent with GPU
    offload replacing the earlier CPU-only pilot's memory pressure.
- TrueNAS SCALE
  - Address: `192.168.20.40` on Servers VLAN 20
  - Media pool baseline: one six-disk 4 TB SAS RAIDZ2 data VDEV
  - Storage HBA: LSI SAS 9300-16i, four internal x4 SFF-8643 Mini-SAS HD
    connectors; two connectors serve the current six disks and two complete x4
    connectors are vacant
  - Current direct-attach cable type: CableDeconn H0204, 1 m SFF-8643 to four
    29-pin SFF-8482 connectors with 15-pin power inputs
  - Planned capacity: eight additional directly attached SAS bays in a
    backplane-free, independently powered printed enclosure; see
    [TrueNAS DIY SAS expansion](projects/TrueNAS-DIY-SAS-Expansion.md)
- Synology DS920+
- Backup Synology
- Lenovo ThinkCentre M92p (NUT server, `192.168.50.25`)
  - Intel Core i5-3470T, 7.6 GB RAM, single 119.2 GB disk (LVM)
  - Debian GNU/Linux 13 (trixie), kernel `6.12.101+deb13-amd64`
  - Onboard NIC: Intel 82579LM Gigabit, single interface `eno1`, MAC `00:23:24:55:b1:1a`
- UPS units (managed by the Lenovo NUT server above; see
  [UPS-Power-Resilience-Claude-Handover.md](UPS-Power-Resilience-Claude-Handover.md)
  for full identification method and telemetry)
  - CyberPower CP1500PFCLCD (`proxmox-ups`, serial `CXXRO7009593`) — Proxmox + both Synology units
  - CyberPower CP1500PFCLCD (`nas-ups`, serial `CXXRP7016137`) — TrueNAS + Arista core switch
  - CyberPower OR500LCDRM1U (`network-ups`, serial `GA4KS2000999`) — OPNsense, the Lenovo NUT server itself, UniFi PoE switch, camera switch
  - APC Back-UPS Pro BN1500M2-CA — dumb battery only (no NUT/monitoring interface exists on this unit); no equipment currently assigned; final disposition undecided
