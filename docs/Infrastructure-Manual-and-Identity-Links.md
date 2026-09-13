# Infrastructure manuals and inventory identities

> Authority: source navigation and identity binding only
>
> Reviewed: 2026-09-13
>
> Current state and exact device identity remain authoritative in NetBox and
> [`03-Hardware-Inventory.md`](03-Hardware-Inventory.md).

This page records official manual locators that cannot safely enter the copied
corpus and binds collected documentation to the recorded device identity. A
link is not evidence that current firmware or configuration matches the manual.

## Collected exact-model manuals

| Wiki source ID | Inventory identity | Official document | Disposition |
|---|---|---|---|
| `synology-ds220j-install-guide` | Synology DS220j backup NAS | [Synology DS220j Hardware Installation Guide](https://global.download.synology.com/download/Document/Hardware/HIG/DiskStation/20-year/DS220j/enu/Syno_HIG_DS220j_enu.pdf) | Exact model; protected human-only PDF |
| `synology-ds920plus-install-guide` | Synology DS920+ main NAS | [Synology DS920+ Hardware Installation Guide](https://global.download.synology.com/download/Document/Hardware/HIG/DiskStation/20-year/DS920%2B/enu/Syno_HIG_DS920_Plus_enu.pdf) | Exact model; protected human-only PDF |

## Official links retained without copied content

| Inventory identity | Official locator | Reason |
|---|---|---|
| Arista DCS-7050TX-64 | [7050 Series 1RU Gen 3 guide](https://www.arista.com/en/qsg-7050-series-1ru-gen3/7050-series-1ru-gen3-overview) | Exact model is listed; PDF delivery is currently bot-gated, so link only |
| Coral M.2 Accelerator A+E key `G650-04527-01` | [Official Coral M.2 datasheet](https://www.coral.ai/static/files/Coral-M2-datasheet.pdf) | Exact part is documented, but the origin currently returns 404; link only pending repair |
| Dell Precision Tower 5810 | [Dell manuals and documents](https://www.dell.com/support/product-details/en-ca/product/precision-t5810-workstation/resources/manuals) | Exact model support page; vendor copyright, link only |
| ASRock Intel Arc Pro B60 Passive 24GB | [Official product page](https://www.asrock.com/Graphics-Card/Intel/Intel%20Arc%20Pro%20B60%20Passive%2024GB/) | Exact passive 24 GB variant; vendor copyright, link only |
| LSI SAS 9300-16i | [Broadcom user guide](https://docs.broadcom.com/doc/12353308) | Exact HBA; vendor copyright, link only |
| UniFi U7 Pro XG | [Official technical specifications](https://techspecs.ui.com/unifi/other/u7-pro-xg) | Exact model for both recorded access points; human reference link |
| Reolink Duo 2V PoE | [Official product and specification page](https://reolink.com/ca/product/reolink-duo-2v-poe/) | Exact camera identity; vendor copyright, link only |
| CyberPower CP1500PFCLCD | [Official product/manual page](https://www.cyberpowersystems.com/product/ups/pfc-sinewave/cp1500pfclcd/) | Exact model for two recorded UPS units; link only pending copying permission |
| CyberPower OR500LCDRM1U | [Official product/manual page](https://www.cyberpowersystems.com/product/ups/smart-app-lcd/or500lcdrm1u/) | Exact rack UPS; link only pending copying permission |
| APC BN1500M2-CA | [Official Canadian product record](https://www.apc.com/ca/en/product/BN1500M2-CA/) | Exact SKU; manual download identifier unresolved |
| VMware SD-WAN Edge 620 | Broadcom/VMware documentation portal | Hardware identity confirmed, but no exact public official manual locator survived review |
| Lenovo ThinkCentre M92p | Lenovo support portal | Exact local model; exact official maintenance-manual locator unresolved |

## Quarantined identities

- The TP-Link eight-port PoE switch has no recorded exact model. No manual is
  assigned from port count or appearance.
- The Binarui AP switch exposes no trustworthy exact model or firmware/manual
  source. It remains quarantined.
- Arista EOS documentation currently published for newer releases does not
  replace the installed EOS 4.20.15M behavior record.

## Software-to-inventory binding

| Wiki source | Authoritative deployed identity |
|---|---|
| `opnsense-docs-2026-09` | OPNsense on the recorded VMware SD-WAN Edge 620 appliance |
| `proxmox-ve-docs-9-2` | Proxmox VE 9.2.10 on the recorded Dell Precision T5810 |
| `truenas-scale-docs-25-10` | TrueNAS SCALE 25.10.5 main storage system |
| `pihole-docs-2026-09` | Recorded primary and secondary Pi-hole services |
| `frigate-docs-0-17-2` | Frigate 0.17.2 with recorded Reolink camera and Coral TPU |
| `authentik-docs-2026-8-0` | Authentik 2026.8.0 identity service |
| `forgejo-docs-15-0` | Forgejo 15.0.7 private Git service |
| `nginx-proxy-manager-docs-2-15-1` | Nginx Proxy Manager 2.15.1 reverse proxy |
| `prometheus-docs-3-13-2` and `grafana-docs-13-2-0` | Recorded monitoring stack |
| `nut-docs-2-8-1` | Network UPS Tools 2.8.1 service and recorded UPS estate |

When this page, NetBox and a live read disagree, do not infer a correction:
report the conflict and review the authoritative system separately.
