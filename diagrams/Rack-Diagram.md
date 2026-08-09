# 15U Rack Elevation

Orientation: U15 is the top of the rack and U1 is the bottom.

| Rack unit | Equipment | Contents or role |
|---:|---|---|
| U15 | Power supply / PDU | Rack power distribution |
| U14-U11 | 4U equipment shelf | Synology DS920+ four-bay NAS, two-bay backup Synology, Philips Hue Bridge and Lutron hub |
| U10 | Patch panel 1 | 24-port copper patch panel |
| U9 | Arista DCS-7050TX-64-R | 10 Gb Layer 2 core switch |
| U8 | Patch panel 2 | 24-port copper patch panel |
| U7-U4 | 4U equipment shelf | UniFi PoE switch and Dell EMC E42W running OPNsense |
| U3 | Reserved | One empty rack unit for airflow or future expansion |
| U2-U1 | UPS | 2U uninterruptible power supply |

## Front elevation

```text
TOP
+-----+--------------------------------------------------------------+
| U15 | Power supply / PDU                                           |
+-----+--------------------------------------------------------------+
| U14 |                                                              |
| U13 | NAS shelf: Synology DS920+, backup Synology, Hue and Lutron  |
| U12 |                                                              |
| U11 |                                                              |
+-----+--------------------------------------------------------------+
| U10 | Patch panel 1 - 24 port                                      |
+-----+--------------------------------------------------------------+
| U09 | Arista DCS-7050TX-64-R core switch                           |
+-----+--------------------------------------------------------------+
| U08 | Patch panel 2 - 24 port                                      |
+-----+--------------------------------------------------------------+
| U07 |                                                              |
| U06 | Equipment shelf: UniFi PoE switch and OPNsense appliance     |
| U05 |                                                              |
| U04 |                                                              |
+-----+--------------------------------------------------------------+
| U03 | Reserved / empty                                             |
+-----+--------------------------------------------------------------+
| U02 | UPS                                                          |
| U01 | UPS                                                          |
+-----+--------------------------------------------------------------+
BOTTOM
```

The Dell Precision T5810 Proxmox host and TrueNAS system are part of the HomeLab but are not shown in this elevation because no in-rack position is assigned to them.

Exact PDU, UPS and UniFi PoE-switch models can be added when their labels are recorded.
