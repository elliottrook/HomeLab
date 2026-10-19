# Aster Production Source Register

> Status: Milestone 1 reviewed register
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
| SABnzbd manual | `https://github.com/sabnzbd/sabnzbd.github.io.git` `dd1e220a…` | `dd1e220a71e1b54aff16d32fdfdab1324d30bfdf` | `wiki/introduction/howto.html`, `wiki/introduction/downloads-cannot-be-completed.html`, `wiki/configuration/5.1/`, `LICENSE.md` | GPL-3.0 | Import; installed-minor match; exact reviewed commit |
| Home Assistant user/integration docs | `https://github.com/home-assistant/home-assistant.io.git` `ea6e6b35…` | `ea6e6b35e02ca5870efafb497325c30cfe1ede10` | `source/common-tasks/os.markdown`, `source/_docs/{automation/,scripts.markdown,scripts/,scene.markdown,scene/}`, `source/_integrations/{backup,homekit,homekit_controller,hue,lutron_caseta,matter,scene,script,sonos,timer}.markdown`, `LICENSE.md` | CC BY-NC-SA 4.0 | Import privately with attribution and same-licence notice; reviewed for deployed Core 2026.9.1 |
| OPNsense docs | `https://github.com/opnsense/docs.git` `2c85e8a9…` | `2c85e8a9ea43f4e008a536734ad428783fae94f9` | 20 named `source/manual/` RST pages for interfaces, firewall/NAT, Dnsmasq/Unbound/DHCP, backups and diagnostics plus `LICENSE` | BSD-2-Clause | Import at exact reviewed commit |
| Proxmox VE docs | `https://github.com/proxmox/pve-docs.git` `14247d9d…` | `14247d9da540e08d40268d80e0d6cd2749edd588` | 14 named AsciiDoc pages for host administration, networking/firewall, LXC/QEMU, PCI passthrough and used storage/backup types plus `LICENSE` | GFDL-1.3 | Import with licence/attribution at exact reviewed commit |
| Servarr Wiki | `https://github.com/Servarr/Wiki.git` `master` | `198dcb59ef1c08828455232fc7b7d908284f69e7` | per-application quick start, settings, activity, library, system, troubleshooting and Docker pages | No repository licence found | Link only; do not copy |
| Jellyfin documentation | `https://github.com/jellyfin/jellyfin.org.git` `40d3fde8…` | `40d3fde8ad1a2efcffef0e043304e1e46b20a40a` | administration, backup/restore, storage, troubleshooting, networking and Intel acceleration pages | CC BY-ND 4.0 | Human only at exact reviewed commit after no-derivative mirror enforcement |
| TrueNAS documentation | `https://github.com/truenas/documentation.git` `0c73733a…` from release branch `25.10` | `0c73733ae2d689c0b288dc56f8c51e70d961f532` | 21 exact paths under `content/{SCALETutorials,SCALEUIReference,GettingStarted}` plus `LICENSE.md` | CC BY-NC-SA 4.0 | Import at exact reviewed 25.10-branch commit for deployed TrueNAS 25.10.5; never follow newer-version `master` |
| Pi-hole documentation | `https://github.com/pi-hole/docs.git` `873b42ad…` | `873b42ada09e8bcd2fe76f0e9f824fd7b378a350` | DNS operation, upstreams, blocking, backup/restore and troubleshooting pages plus `LICENSE` | CC BY-SA 4.0 | Import at exact reviewed commit for deployed 2026.05.0/2026.07.2 instances |
| authentik documentation | `https://github.com/goauthentik/authentik.git` `version/2026.8.0` | `f3753ec20ce13ef672401a131379d1a5a2d3439b` | selected `website/docs/{install-config,sys-mgmt,add-secure-apps,customize,troubleshooting,security}/` pages plus `LICENSE` | CC BY-SA 4.0 for `website/` | Import; exact deployed tag |
| Forgejo documentation | `https://codeberg.org/forgejo/docs.git` `28300386…` from release branch `v15.0` | `28300386afa884d287e07165192516a0352b36b8` | selected `docs/admin/` installation, configuration, backup/upgrade, reverse-proxy, authentication, Actions and troubleshooting pages plus selected `docs/user/actions/` and `docs/license.md` | CC BY-SA 4.0 with identified Apache-2.0 inherited portions | Import; exact reviewed commit for deployed Forgejo 15.0.7 |
| Nginx Proxy Manager | `https://github.com/NginxProxyManager/nginx-proxy-manager.git` `v2.15.1` | `76f09db610cfcaecf6d608a8947d6f75aa028870` | `README.md`, `docs/`, `LICENSE` | MIT | Import; exact deployed tag |
| Prometheus | `https://github.com/prometheus/prometheus.git` `v3.13.2` | `bb5dff00cf8fdfbf5c65e0531aa835fa238a43a2` | selected `docs/` pages for configuration, storage, querying, alerting and operations plus licence | Apache-2.0 | Import; exact deployed tag |
| Grafana | `https://github.com/grafana/grafana.git` `v13.2.0` | `f681b1359f6a0b8ecb9f2c49a88ac72b75bde73b` | `docs/sources/administration/{back-up-grafana,provisioning}/`, `docs/sources/alerting/{set-up,fundamentals,best-practices,troubleshooting}/`, `docs/sources/setup-grafana/configure-grafana/`, `LICENSE` | AGPL-3.0-only | Import; exact deployed tag; 40 files / 593,350 bytes |
| Network UPS Tools | `https://github.com/networkupstools/nut.git` `v2.8.1` | `4ba352d8f82e4c51032d4166d4cc3276b31fb3a5` | selected `docs/` and man-page sources for `upsd`, `upsmon`, drivers, shutdown and troubleshooting plus licence | GPL-2.0-or-later | Import; exact deployed version family |
| Frigate | `https://github.com/blakeblackshear/frigate.git` `v0.17.2` | `3d4dd3ac4b00e7257bd3412608a783001d7d77ed` | selected `docs/docs/` pages for installation, configuration, detectors, recordings, cameras, review and recovery plus `LICENSE` | MIT | Import; exact deployed tag |

## Official vendor web references

These sources have no suitable versioned Git documentation. Each is bounded to
the exact URL shown. Vendor copyright terms are not treated as permission to
create derivatives, so accepted text is `human-only`; pages that cannot be
collected reliably remain metadata/link-only.

| System | Deployed scope | Exact canonical boundary | Disposition |
|---|---|---|---|
| Synology DSM | DS920+, DSM 7.4.1-90080 | `https://kb.synology.com/en-global/DSM/help/DSM/AdminCenter/system_configbackup` and separately enrolled exact DSM help pages for storage, shares, NFS and recovery | Human-only; one exact URL per source |
| UniFi OS Server / Network | OS Server 5.1.42 / Network 10.5.67 | `https://help.ui.com/hc/en-us/articles/34210126298775-Self-Hosting-UniFi` plus exact Help Center pages for updates, backup, adoption, VLANs and troubleshooting | Human-only; current vendor docs, version context retained |
| Arista EOS | DCS-7050TX-64 hardware 01.11, EOS 4.20.15M | `https://www.arista.com/en/um-eos` and exact topic URLs for initial recovery, upgrades, interfaces, VLANs, port channels and configuration management | Link-only: currently published manual is newer than installed EOS; do not silently substitute it |
| Arista hardware | DCS-7050TX-64 | `https://www.arista.com/assets/data/docs/Manuals/QSG/QS_7000-Gen3.pdf` | Human-only exact-model manual |
| Reolink camera | Duo 2V PoE | `https://reolink.com/ca/product/reolink-duo-2v-poe/` | Human-only exact product/setup/specification page |
| UniFi access points | two U7 Pro XG units | `https://techspecs.ui.com/unifi/other/u7-pro-xg` | Human-only exact-model specification page |

## Collection controls and measured limits

Every Git boundary below was enumerated at its recorded expected commit using
the same supported text suffixes as the production collector. Directory
boundaries exclude images, generated binaries and source code. The collector
also enforces the hard 256-file ceiling independently.

| Source group | Measured maximum | Manifest byte limit | Refresh | Class / authority | Mirror policy |
|---|---:|---:|---:|---|---|
| Installed-version product README/licence pairs | 2–3 files; largest 40,513 bytes | 256 KiB | 8,760 h; explicit version review | Upstream / generic product reference | `allow-derived` with recorded source licence |
| SABnzbd manual | 18 files / 238,314 fetched bytes | 512 KiB | 720 h; exact reviewed commit | Upstream / generic product reference | `allow-derived`, GPL-3.0 |
| Home Assistant selected docs | 28 files / 364,426 fetched bytes | 1 MiB | 720 h; exact reviewed commit | Upstream / generic and integration reference | `allow-derived`, CC-BY-NC-SA-4.0 |
| OPNsense selected docs | 21 files / 280,714 fetched bytes | 1 MiB | 720 h; exact reviewed commit | Upstream / generic infrastructure reference | `allow-derived`, BSD-2-Clause |
| Proxmox VE selected docs | 15 files / 268,373 fetched bytes | 1 MiB | 720 h; exact reviewed commit | Upstream / generic infrastructure reference | `allow-derived`, GFDL-1.3 |
| TrueNAS selected docs | 21 files / 226,250 fetched bytes | 2 MiB | 720 h; exact reviewed 25.10 commit | Upstream / generic storage reference | `allow-derived`, CC-BY-NC-SA-4.0 |
| authentik selected docs | 103 files / 325,991 bytes | 1 MiB | 8,760 h; explicit version review | Upstream / generic identity reference | `allow-derived`, CC-BY-SA-4.0 |
| Forgejo selected docs | selected paths / 169,429 fetched bytes | 1 MiB | 720 h; exact reviewed v15.0 commit | Upstream / generic Git-service reference | `allow-derived`, CC-BY-SA-4.0 |
| Nginx Proxy Manager selected docs | 13 files / 38,952 bytes | 256 KiB | 8,760 h; explicit version review | Upstream / generic reverse-proxy reference | `allow-derived`, MIT |
| Frigate selected docs | 53 files / 544,084 bytes | 1 MiB | 8,760 h; explicit version review | Upstream / generic surveillance reference | `allow-derived`, MIT |
| Prometheus selected docs | 32 files / 542,268 bytes | 1 MiB | 8,760 h; explicit version review | Upstream / generic monitoring reference | `allow-derived`, Apache-2.0 |
| Grafana selected docs | 40 files / 593,350 bytes | 1 MiB | 8,760 h; explicit version review | Upstream / generic monitoring reference | `allow-derived`, AGPL-3.0-only |
| Network UPS Tools selected docs | 187 files / 1,167,928 bytes | 2 MiB | 8,760 h; explicit version review | Upstream / generic power reference | `allow-derived`, GPL-2.0-or-later |
| Vendor manuals/specification pages | one exact file/URL per source; 100 MiB collector ceiling reduced per observed asset before enrollment | Exact observed size rounded up, never above 100 MiB | 8,760 h manual review | Vendor / exact-model reference | `human-only` or metadata/link-only |
| Reviewed HomeLab sources | one named file and exact repository commit per source | 2 MiB | 720 h or milestone-triggered | Local-reviewed / lab-specific current state | `allow-derived`; higher retrieval authority than upstream |

The Home Assistant operational reference is a deliberate narrower exception:
it is retained in the authenticated human corpus as `human-only` because it
contains household workflow labels and internal addressing. Aster's existing
separately reviewed current-state snapshot remains the retrieval authority;
the production-corpus mirror does not duplicate those private details.

## Reconciled deployed infrastructure versions

| System | Live/reviewed version | Evidence disposition |
|---|---:|---|
| TrueNAS SCALE | 25.10.5 | Live `system.version`; no configuration read |
| Synology DS920+ | DSM 7.4.1-90080 | Live non-secret version file through the established restricted account |
| UniFi OS Server | 5.1.42, bundling Network 10.5.67 | Live executable version plus official matching release record |
| Frigate | 0.17.2 (`3d4dd3a`) | Live loopback version endpoint; matches exact Git tag commit |
| Pi-hole primary / secondary | 2026.05.0 / 2026.07.2 | Reviewed current operational baseline; no secret-bearing container configuration read |
| authentik | 2026.8.0 | Live container image names only; matches exact annotated Git tag commit |
| Forgejo | 15.0.7 | Live executable version; product tag and 15.0 documentation branch resolved separately |
| Nginx Proxy Manager | 2.15.1 | Live container package version; exact Git tag resolved |
| Prometheus / Grafana | 3.13.2 / 13.2.0 | Live executable versions and build commits; both exactly match dereferenced Git tags |
| Network UPS Tools | 2.8.1-5 | Reviewed installed Debian package baseline; upstream 2.8.1 tag used for generic documentation |

Moving documentation branches are used only while selecting and reviewing an
update. The accepted manifest fetches the reviewed 40-character commit itself,
with `git_ref` and `expected_commit` equal, so unrelated later movement of
`master`, `current`, or a release branch cannot create a recurring quarantine.
Installed-version tags remain preferred wherever present. A product upgrade or
deliberate documentation refresh requires a new branch-to-pin comparison and
then an explicit update of both commit fields.

## Reviewed local authority

| Source | Authority | Disposition |
|---|---|---|
| `docs/reference/ARR-Stack-Operational-Reference.md` | Reviewed lab-specific current state with exclusions | Version-import/link above generic ARR material |
| `docs/reference/Home-Assistant-Operational-Reference.md` | Reviewed lab-specific current state with exclusions | Version-import/link above generic Home Assistant material |
| `docs/Current-Network-Baseline.md` | Reviewed topology/current network baseline | Select bounded current-state sections; do not import historical secrets/config |
| `docs/03-Hardware-Inventory.md` | Reviewed equipment identity | Use to bind manuals to exact models |
| `docs/04-Operations.md`, `docs/05-Backups.md`, `docs/reference/Aster-Operations.md` | Reviewed operations/recovery | Select bounded procedures and retain repository path/commit |

## Exact-model manual candidates

| Equipment | Canonical source | Status |
|---|---|---|
| Dell Precision Tower 5810 | `https://www.dell.com/support/product-details/en-ca/product/precision-t5810-workstation/resources/manuals` | Exact model confirmed; vendor-hosted owner manual, metadata/link accepted pending human-only policy |
| ASRock Intel Arc Pro B60 Passive 24GB | `https://www.asrock.com/Graphics-Card/Intel/Intel%20Arc%20Pro%20B60%20Passive%2024GB/` | Exact installed passive one-slot variant confirmed; vendor specification/manual page human-only |
| LSI SAS 9300-16i | `https://docs.broadcom.com/doc/12353308` | Exact HBA model and official user guide confirmed; human-only |
| UniFi U7 Pro XG | `https://techspecs.ui.com/unifi/other/u7-pro-xg` | Exact model confirmed for both APs; vendor tech specs accepted as human-only content/link |
| CyberPower CP1500PFCLCD | `https://www.cyberpowersystems.com/product/ups/pfc-sinewave/cp1500pfclcd/` | Exact model confirmed for two units; official manual and function guide located, copyright disposition pending |
| Synology DS220j | `https://global.download.synology.com/download/Document/Hardware/HIG/DiskStation/20-year/DS220j/enu/Syno_HIG_DS220j_enu.pdf` | Exact model confirmed; official PDF located, human-only/link disposition pending |
| Synology DS920+ | `https://global.download.synology.com/download/Document/Hardware/HIG/DiskStation/20-year/DS920%2B/enu/Syno_HIG_DS920_Plus_enu.pdf` | Exact model and official installation guide confirmed; human-only |
| Arista DCS-7050TX-64 | `https://www.arista.com/assets/data/docs/Manuals/QSG/QS_7000-Gen3.pdf` | Exact model is explicitly covered by official 7000 Series 1RU Gen 3 guide; human-only |
| Reolink Duo 2V PoE | `https://reolink.com/ca/product/reolink-duo-2v-poe/` | Exact recorded model has an official specifications/setup page; human-only/link because copying terms are not granted |
| Coral M.2 Accelerator A+E key `G650-04527-01` | `https://www.coral.ai/static/files/Coral-M2-datasheet.pdf` | Exact recorded part number and A+E key variant confirmed in official datasheet; human-only |
| CyberPower OR500LCDRM1U | `https://www.cyberpowersystems.com/product/ups/smart-app-lcd/or500lcdrm1u/` | Exact official product page exposes the matching user manual; human-only |
| APC BN1500M2-CA | `https://www.apc.com/ca/en/product/BN1500M2-CA/` | Exact Canadian SKU official product record confirmed; manual download identifier remains to resolve, so link-only for now |
| VMware SD-WAN Edge 620 | Broadcom/VMware documentation | Hardware identity confirmed; OPNsense behavior comes from OPNsense docs, vendor hardware manual still to resolve |
| Lenovo ThinkCentre M92p | Lenovo support/download centre | Exact model confirmed locally; exact official maintenance-manual locator not yet resolved, so link-only/quarantined |
| TP-Link 8-port PoE switch | None exact | Quarantined: inventory lacks the exact model and no manual is assigned by inference |
| Binarui AP Switch | None trustworthy | Quarantined: UI exposes no exact model and no trustworthy firmware/manual source exists |

The VMware SD-WAN Edge 620 identity is confirmed by physical inventory, but no
public exact official hardware manual survived canonical-source review. It is
quarantined rather than being matched to an Edge 610/640 family document.

## Quarantined or deferred items

- Reconcile the backup DS220j DSM version if a future restricted source can
  expose it without interactive access; retain model-only hardware scope now.
- Resolve an exact official VMware Edge 620 hardware-manual locator and the APC
  BN1500M2-CA manual document identifier; keep both link-only until then.
- Additional exporter-specific Prometheus/Grafana documentation is deferred
  unless later evaluation proves a retrieval gap.
