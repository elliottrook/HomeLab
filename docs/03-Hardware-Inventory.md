# Hardware Inventory

- Dell EMC E42W (OPNsense)
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
  - Retained for a camera-only role behind Arista Et34 access VLAN 60
  - Camera-path validation is deferred until cameras are reconfigured
- Dell Precision T5810 (Proxmox)
  - Current CPU: Intel Xeon E5-1603 v3; purchased E5-2698 v4 pending installation
  - Current memory: 32 GB ECC RDIMM; additional planned RAM remains to be installed and the final total must be confirmed
  - Coral Edge TPU `G650-04527-01` on a PCIe A+E-key carrier, passed through to Frigate VM 102
  - Quadro K620 remains scheduled for removal during the next hardware-maintenance window
  - Any Intel Arc Pro B60 purchase remains conditional on exact SKU/VRAM, clearance, PSU and power-connector validation
- TrueNAS SCALE
- Synology DS920+
- Backup Synology
- Lenovo ThinkCentre M92p (NUT server, `192.168.50.25`)
  - Intel Core i5-3470T, 7.6 GB RAM, single 119.2 GB disk (LVM)
  - Debian GNU/Linux 13 (trixie), kernel `6.12.101+deb13-amd64`
  - Onboard NIC: Intel 82579LM Gigabit, single interface `eno1`, MAC `00:23:24:55:b1:1a`
