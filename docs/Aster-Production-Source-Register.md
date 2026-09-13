# Aster Production Source Register

> Status: Milestone 1 working register
>
> Reviewed: 2026-09-13
>
> Authority: source-selection record; live systems and adopted systems of record
> remain authoritative for installed state

This register prevents broad or mutable collection. `Import` means the exact
listed ref, expected commit and text boundary may enter the private human wiki.
`Link only` stores metadata and a canonical locator, not copied content.
`Human only` requires an enforced no-derivative-mirror policy before collection.
Pipeline 1.3.0 implements that policy and carries the declared licence into
accepted provenance and every permitted derived entry.

## Installed-version Git sources

| Source | Installed version | Repository/ref | Expected commit | Boundary | Licence | Disposition |
|---|---:|---|---|---|---|---|
| Sonarr | 4.0.19.2979 | `https://github.com/Sonarr/Sonarr.git` `v4.0.19.2979` | `4ff1b780010d3d9ec76a4864dce96b6494e9caea` | `README.md`, `LICENSE.md` | GPL-3.0 | Import |
| Radarr | 6.3.0.10514 | `https://github.com/Radarr/Radarr.git` `v6.3.0.10514` | `7827e5368947f158ad06f757334f5cde6c406411` | `README.md`, `LICENSE` | GPL-3.0 | Import |
| Lidarr | 3.1.0.4875 | `https://github.com/Lidarr/Lidarr.git` `v3.1.0.4875` | `350860e524029b7fb4165ed14fbcabb11217ada2` | `README.md`, `LICENSE.md` | GPL-3.0 | Import |
| Prowlarr | 2.5.2.5491 | `https://github.com/Prowlarr/Prowlarr.git` `v2.5.2.5491` | `c0f8c2c5bc0d7906e8d97e30a9bb7616f37d7090` | `README.md`, `LICENSE` | GPL-3.0 | Import |
| SABnzbd | 5.1.2 | `https://github.com/sabnzbd/sabnzbd.git` `5.1.2` | `10609644c8b5eef462845ec6443f24dd8fcba96a` | `README.md`, `LICENSE.txt` | GPL-2.0-or-later | Import |
| Jellyfin server | 10.11.11 | `https://github.com/jellyfin/jellyfin.git` `v10.11.11` | `1fbd8739292cce610231be93daf43368733edf63` | `README.md`, `LICENSE` | GPL-2.0 | Import |
| Home Assistant Core | 2026.9.1 | `https://github.com/home-assistant/core.git` `2026.9.1` | `fc034572d0216a04ed40a07154394908a594dfed` | `README.rst`, `LICENSE.md` | Apache-2.0 | Import |
| Home Assistant OS | 18.2 | `https://github.com/home-assistant/operating-system.git` `18.2` | `3c196f5144ae78e124d2ae1a067c1841af71a51c` | `README.md`, `Documentation/README.md`, `LICENSE` | Apache-2.0 | Import |
| Home Assistant Supervisor | 2026.09.0 | `https://github.com/home-assistant/supervisor.git` `2026.09.0` | `75e47083b96c97c46d411ea0292e5b699a7850c2` | `README.md`, `LICENSE` | Apache-2.0 | Import |

## Operational documentation repositories

| Source | Repository/ref | Expected commit | Selected boundary | Licence | Disposition |
|---|---|---|---|---|---|
| SABnzbd manual | `https://github.com/sabnzbd/sabnzbd.github.io.git` `master` | `dd1e220a71e1b54aff16d32fdfdab1324d30bfdf` | `wiki/introduction/howto.html`, `wiki/introduction/downloads-cannot-be-completed.html`, `wiki/configuration/5.1/`, `LICENSE.md` | GPL-3.0 | Import; installed-minor match |
| Home Assistant user/integration docs | `https://github.com/home-assistant/home-assistant.io.git` `current` | `18035547fe0ea9b1847f145bf395d88fdce9d63e` | `source/common-tasks/os.markdown`, selected automation/script/scene pages, `source/_integrations/{backup,homekit,homekit_controller,hue,lutron_caseta,matter,sonos,timer}.markdown`, `LICENSE.md` | CC BY-NC-SA 4.0 | Import privately with attribution and same-licence notice |
| OPNsense docs | `https://github.com/opnsense/docs.git` `master` | `2c85e8a9ea43f4e008a536734ad428783fae94f9` | exact RST pages for interfaces, VLAN/LAGG, firewall, NAT, Dnsmasq, Unbound, DHCP, backups and diagnostics; `LICENSE` | BSD-2-Clause | Import |
| Proxmox VE docs | `https://github.com/proxmox/pve-docs.git` `master` | `439ce4394b050b0e55b6a85cc74cfccab3e0b474` | exact AsciiDoc pages for host administration, networking, firewall, LXC/QEMU, PCI passthrough, storage, backup and restore; `LICENSE` | GFDL-1.3 | Import with licence/attribution |
| Servarr Wiki | `https://github.com/Servarr/Wiki.git` `master` | `198dcb59ef1c08828455232fc7b7d908284f69e7` | per-application quick start, settings, activity, library, system, troubleshooting and Docker pages | No repository licence found | Link only; do not copy |
| Jellyfin documentation | `https://github.com/jellyfin/jellyfin.org.git` `master` | `1edeb876d1a197de6ead0148ca32e4ae241a6f2d` | administration, backup/restore, storage, troubleshooting, networking and Intel acceleration pages | CC BY-ND 4.0 | Human only after no-derivative mirror enforcement; otherwise link only |
| TrueNAS documentation | `https://github.com/truenas/documentation.git` `master` | `e523684d5b274a807f38223c0d4cdb9999f6402f` | installed-release storage, datasets, shares, apps, backup and recovery pages plus `LICENSE.md` | Creative Commons; exact identifier to verify from licence file | Quarantine until exact installed release and licence identifier are reconciled |
| Pi-hole documentation | `https://github.com/pi-hole/docs.git` `master` | `873b42ada09e8bcd2fe76f0e9f824fd7b378a350` | DNS operation, upstreams, blocking, backup/restore and troubleshooting pages plus `LICENSE` | CC BY-SA 4.0 | Import at pinned current-doc commit for deployed 2026.05.0/2026.07.2 instances |
| authentik documentation | `https://github.com/goauthentik/authentik.git` `main` | `2e85913317be77f29af7198ca74843efb7df25e7` | selected `website/docs/` pages for flows, providers, outposts, backup/recovery and troubleshooting plus `LICENSE` | CC BY-SA 4.0 for `website/` | Quarantine until installed version is reconciled; then pin matching tag if available |
| Forgejo documentation | `https://codeberg.org/forgejo/docs.git` `next` | `b99b3730c3c35e371e52fa54754fb7091907e385` | installation, administration, backup/restore, Actions and troubleshooting pages | Licence still to verify | Quarantine until a 15.0.7-specific/current boundary and licence are verified |
| Nginx Proxy Manager | `https://github.com/NginxProxyManager/nginx-proxy-manager.git` `v2.15.1` | `76f09db610cfcaecf6d608a8947d6f75aa028870` | `README.md`, `docs/`, `LICENSE` | MIT | Import; exact deployed tag |
| Prometheus | `https://github.com/prometheus/prometheus.git` `v3.13.2` | `bb5dff00cf8fdfbf5c65e0531aa835fa238a43a2` | selected `docs/` pages for configuration, storage, querying, alerting and operations plus licence | Apache-2.0 | Import; exact deployed tag |
| Grafana | `https://github.com/grafana/grafana.git` `v13.2.0` | `f681b1359f6a0b8ecb9f2c49a88ac72b75bde73b` | selected `docs/sources/` administration, provisioning, alerting, backup and troubleshooting pages plus licence | AGPL-3.0-only | Import; exact deployed tag |
| Network UPS Tools | `https://github.com/networkupstools/nut.git` `v2.8.1` | `4ba352d8f82e4c51032d4166d4cc3276b31fb3a5` | selected `docs/` and man-page sources for `upsd`, `upsmon`, drivers, shutdown and troubleshooting plus licence | GPL-2.0-or-later | Import; exact deployed version family |
| Frigate | `https://github.com/blakeblackshear/frigate.git` `v0.17.2` | `3d4dd3ac4b00e7257bd3412608a783001d7d77ed` | selected `docs/docs/` pages for installation, configuration, detectors, recordings, cameras, review and recovery plus `LICENSE` | MIT | Import; exact deployed tag |

Branch-backed documentation is frozen by both branch name and expected commit.
Any upstream movement quarantines collection until a human reviews and updates
the expected commit. Installed-version tags remain preferred wherever present.

## Reviewed local authority

| Source | Authority | Disposition |
|---|---|---|
| `docs/ARR-Stack-Operational-Reference.md` | Reviewed lab-specific current state with exclusions | Version-import/link above generic ARR material |
| `docs/Home-Assistant-Operational-Reference.md` | Reviewed lab-specific current state with exclusions | Version-import/link above generic Home Assistant material |
| `docs/Current-Network-Baseline.md` | Reviewed topology/current network baseline | Select bounded current-state sections; do not import historical secrets/config |
| `docs/03-Hardware-Inventory.md` | Reviewed equipment identity | Use to bind manuals to exact models |
| `docs/04-Operations.md`, `docs/05-Backups.md`, `docs/Aster-Operations.md` | Reviewed operations/recovery | Select bounded procedures and retain repository path/commit |

## Exact-model manual candidates

| Equipment | Canonical source | Status |
|---|---|---|
| Dell Precision Tower 5810 | `https://www.dell.com/support/product-details/en-ca/product/precision-t5810-workstation/resources/manuals` | Exact model confirmed; vendor-hosted owner manual, metadata/link accepted pending human-only policy |
| UniFi U7 Pro XG | `https://techspecs.ui.com/unifi/other/u7-pro-xg` | Exact model confirmed for both APs; vendor tech specs accepted as metadata/link |
| CyberPower CP1500PFCLCD | `https://www.cyberpowersystems.com/product/ups/pfc-sinewave/cp1500pfclcd/` | Exact model confirmed for two units; official manual and function guide located, copyright disposition pending |
| Synology DS220j | `https://global.download.synology.com/download/Document/Hardware/HIG/DiskStation/20-year/DS220j/enu/Syno_HIG_DS220j_enu.pdf` | Exact model confirmed; official PDF located, human-only/link disposition pending |
| Synology DS920+ | Synology Download Center / Knowledge Center | Exact model confirmed; exact official guide URL still to resolve |
| Arista DCS-7050TX | Arista product/documentation portal | Family confirmed; exact hardware revision and accessible manual still to resolve |
| Reolink Duo 2V PoE | Reolink support/download center | Recorded model string requires vendor-page reconciliation before collection |
| CyberPower OR500LCDRM1U | CyberPower product resources | Exact model confirmed; exact official manual URL still to resolve |
| APC BN1500M2-CA | APC product/support resources | Exact model confirmed; exact official manual URL still to resolve |
| VMware SD-WAN Edge 620 | Broadcom/VMware documentation | Hardware identity confirmed; OPNsense behavior comes from OPNsense docs, vendor hardware manual still to resolve |
| Binarui AP Switch | None trustworthy | Quarantined: UI exposes no exact model and no trustworthy firmware/manual source exists |

## Unresolved gate items

- Resolve installed versions and remaining licence details for TrueNAS,
  Synology DSM, UniFi Network, authentik and Forgejo documentation.
- Reconcile remaining exact hardware variants and canonical manual URLs.
- Validate every proposed boundary below 256 files and its explicit byte limit.
