# Hardware Inventory

- Dell EMC E42W (OPNsense)
- Arista DCS-7050TX
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
