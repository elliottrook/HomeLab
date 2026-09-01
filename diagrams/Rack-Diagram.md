# 15U Rack Elevation

> **Refreshed 2026-09-01** via a real photo-based walk-through with Jason
> (`docs/projects/NetBox-DCIM.md`, Milestone 1), replacing the previous
> stale version. U-boundaries below are Jason's on-the-spot estimates, not
> a tape-measure survey — flagged per row where relevant. The same data has
> also been entered into NetBox as the project's authoritative source going
> forward; this file is a convenience snapshot of it.
>
> **Known discrepancy, not yet resolved:** the estimated unit heights below
> sum to approximately 16U against the rack's nominal 15U rating (PDU 1 +
> NAS shelf ~5 + switch/OPNsense shelf ~4 + patch panel 1 + Arista 1 + patch
> panel 1 + camera switch 1 + brush panel 1 + network UPS 1 = 16). One or
> more of the "approximately N U" shelf estimates is probably 1U smaller
> than stated. Not worth blocking on — correct it opportunistically next
> time the rack is open.

Orientation: U15 is the top of the rack and U1 is the bottom.

| Rack unit | Equipment | Contents or role |
|---:|---|---|
| U15 | PDU | Rack power distribution, 1U |
| U14–U10 (~5U, estimated) | Equipment shelf | Main Synology NAS, backup Synology NAS, Lutron bridge, Philips Hue bridge |
| U9–U6 (~4U, estimated) | Equipment shelf | Binarui PoE AP switch, OPNsense (**VMware SD-WAN Edge 620** — corrected this session; previously misrecorded repo-wide as a "Dell EMC E42W / SD-WAN Edge 610"), NUT server (Lenovo ThinkCentre M92p) |
| U5 | Patch panel 1 | 24-port copper patch panel |
| U4 | Arista DCS-7050TX-64-R | 10 Gb Layer 2 core switch |
| U3 | Patch panel 2 | 24-port copper patch panel |
| U2 | PoE camera switch | TP-Link TL-SG1016PE V2, camera-only VLAN 60 |
| U1 | Brush panel | Cable pass-through |
| *(position TBD — see discrepancy note above)* | Network UPS | CyberPower OR500LCDRM1U (`network-ups`) |

## Not rack-mounted (on the floor beside the rack)

Confirmed via the same photo walk-through, left to right:

| Equipment | Role |
|---|---|
| TrueNAS (locked, vented rackmount-style chassis, not actually rack-mounted) | Storage |
| Dell Precision T5810 | Proxmox host |
| CyberPower UPS (reads "117V" in the confirming photo) | `nas-ups` — TrueNAS + Arista |
| CyberPower UPS | `proxmox-ups` — Proxmox + both Synology units |

## Front elevation

```text
TOP
+-----+--------------------------------------------------------------+
| U15 | PDU                                                          |
+-----+--------------------------------------------------------------+
| U14 |                                                              |
| U13 | NAS shelf: main Synology, backup Synology, Lutron, Hue       |
| U12 | (~5U, estimated)                                             |
| U11 |                                                              |
| U10 |                                                              |
+-----+--------------------------------------------------------------+
| U09 |                                                              |
| U08 | Shelf: PoE AP switch, OPNsense (VMware SD-WAN Edge 620),     |
| U07 | NUT server (Lenovo ThinkCentre M92p) (~4U, estimated)        |
| U06 |                                                              |
+-----+--------------------------------------------------------------+
| U05 | Patch panel 1 - 24 port                                      |
+-----+--------------------------------------------------------------+
| U04 | Arista DCS-7050TX-64-R core switch                           |
+-----+--------------------------------------------------------------+
| U03 | Patch panel 2 - 24 port                                      |
+-----+--------------------------------------------------------------+
| U02 | PoE camera switch (TP-Link TL-SG1016PE V2)                   |
+-----+--------------------------------------------------------------+
| U01 | Brush panel                                                  |
+-----+--------------------------------------------------------------+
| ??  | Network UPS (CyberPower OR500LCDRM1U) - position/overflow    |
|     | not yet reconciled against the nominal 15U total, see note   |
+-----+--------------------------------------------------------------+
BOTTOM
```

Proxmox, TrueNAS, and both floor-standing UPS units are part of the HomeLab
but are not shown in this elevation because they are not rack-mounted — see
the table above instead.
