# Changelog

## Unreleased

### Changed
- Readdressed the AP Switch from `192.168.50.26` to `192.168.1.26` on Trusted VLAN 10, resolving a long-standing mismatch where the device carried a Management-VLAN number it could never be reached on. Confirmed the switch has no Management-VLAN setting, so its untagged management always lands in Arista Et33's native VLAN 10; a VLAN 50 address would not have isolated it, only disguised it, while forcing a `192.168.50.x` alias whose connected route shadows the real path to VLAN 50 and severs the host's access to Arista, Proxmox and the UniFi controller. It is now reachable directly from Trusted at `http://192.168.1.26` with no alias and no physical recovery path, and the superseded port-5 procedure is marked historical. Updated `devices.conf`, the IP addressing table, network design and baseline records to match; the NetBox primary-IP record remains outstanding.

### Added
- Extended HomeLab Doctor with wireless coverage, closing the detection gap that let the AP Switch outage run roughly six days unnoticed. `check_unifi` queries the UniFi Network integration API and fails if either access point is missing or not `ONLINE`; `check_wireless_vlans` fails if IoT VLAN 30's DHCP lease count collapses toward zero, the signature a VLAN-tagging failure produces. Guest VLAN 40 is reported but deliberately not alerted on, since an empty guest network is normal. The API key is read from `~/.config/lab/unifi-api-key` (mode 600, outside the repository, overridable via `UNIFI_API_KEY_FILE`), and the check warns and skips rather than failing when no key is present.

### Fixed
- Restored Guest and IoT wireless after the Binarui AP Switch silently factory-reset itself, dropping every 802.1Q-tagged VLAN while untagged traffic continued to reach Arista Et33's native VLAN 10. That asymmetry left Trusted Wi-Fi working, Guest at 0 DHCP leases, IoT down to its 2 wired devices from a baseline of 23 wireless clients, and both U7 Pro XG APs reporting OFFLINE in UniFi while still powered and broadcasting. Isolated by Arista's MAC address table on Et33, where every learned MAC — including both APs' own management MACs — sat on VLAN 10 with none on VLAN 30/40/50. Rebuilt the Static VLAN Table and all six port trunk definitions, then confirmed both APs ONLINE, 52 clients reconnected, IoT leases recovered to 42 and a Guest client leased `192.168.40.175`; Guest firewall isolation was verified unchanged throughout.
- Established that the original AP Switch configuration was never written to NVRAM, which is why a power event wiped it. The rebuilt configuration was explicitly saved and then proven to survive a deliberate reboot.

### Added
- Recorded the AP Switch's previously unknown identity — MAC `84:E5:D8:E2:8D:92`, serial `6202510300069`, firmware `V100SP11251021`, hardware `V1` — closing the "Not yet recorded" MAC gap in the device inventory and the inconclusive model-identification item in the NetBox DCIM project. The unit exposes no real model string, confirming the generic `AP Switch` device type is accurate rather than a placeholder.
- Documented the AP Switch's full port/VLAN recovery reference as its sole disaster-recovery artifact, since the device offers save-to-NVRAM only and has no config export capability.
- Superseded the AP Switch's physical port-5 recovery procedure with a no-recabling method: because its management plane is untagged and lands in Arista's native VLAN 10, a temporary IP alias on any Trusted-VLAN host reaches it over existing cabling, with a documented warning against using the same trick on `192.168.50.0/24`.
- Confirmed the AP Switch has no Management-VLAN setting, establishing its long-documented VLAN 50 addressing mismatch as a hardware limitation rather than a misconfiguration, and logged the resulting open addressing decision.
- Confirmed a physical Proxmox hardware upgrade (2026-09-02 RAM, 2026-09-04 CPU replacement): all 8 DIMM slots now populated at 80 GB total (4×16 GB + 4×4 GB, ~78 GiB usable), and the CPU replaced like-for-like with the same Intel Xeon E5-2698 v4 (single socket, 20 cores/40 threads). Post-upgrade reboot showed 0 failed systemd units, no OOM/MCE/ECC errors, and all 9 LXCs plus both autostart VMs (frigate, home-assistant) came back healthy; VM 105 (ollama) remained stopped as expected (no `onboot` flag). Configured memory across all running guests is now ~46 GB against ~78 GB usable, a large improvement over the pre-upgrade ~44 GB allocated vs ~46 GB usable.
- Connected Hermes Desktop v0.21.0 to Aster through a saved authenticated OpenAI-compatible endpoint and added server-sent-event streaming to the Aster gateway. End-to-end agent turns now work, while testing confirms Hermes' roughly 4,900-token harness still takes about 65–69 seconds per turn on the current 8K llama.cpp slot; direct Aster remains the preferred conversational interface.
- Replaced the too-slow Hermes/Ollama runtime with the lightweight Aster service in LXC 104 and llama.cpp Vulkan inference in LXC 110, serving Qwen3.8 27B `UD-IQ4_XS` on the Intel Arc Pro B60. Added authenticated Lab-VLAN APIs, a browser UI, allowlisted read-only functions, curated source-attributed HomeLab retrieval, automatic model warm-up, systemd hardening, operations documentation and HomeLab Doctor coverage.
- Created named production rollback snapshots for LXC 104 and LXC 110 and passed full container-reboot recovery: both services returned enabled and active, and the first authenticated post-warm-up conversation completed in approximately 4.7 seconds.
- Closed the Prometheus/Grafana observability project at the owner's direction after same-day final validation: HomeLab Doctor passed 54 checks with no failures, live services and private TLS were healthy, resource/cardinality use remained well within budget, alerting and recovery were proven, and the close-out record moved into the completed-projects portfolio.
- Added the private HTTPS Grafana address `monitoring.elliottrook.com` through Nginx Proxy Manager and split DNS, enabled an admin-restricted Authentik sign-in while retaining the local recovery login, and updated the live Homepage tile.
- Corrected a provider-cloning error caught during consent testing: restored Forgejo's original Authentik client configuration, created Grafana as a separate provider/application, and verified Forgejo with a real OIDC login plus Grafana's correctly labelled consent path.
- Provisioned `jason@yampy.ca` as Grafana's sole alert contact. After a controlled test exposed the residential outbound-TCP-25 block, configured authenticated iCloud SMTP on TCP 587 with mandatory STARTTLS. A Grafana-generated test was received successfully; the temporary rule was removed and only the two production UPS rules remain.
- Added HomeLab Doctor and protected-backup coverage for the observability stack. The backup passed archive, SQLite, dashboard JSON, and isolated restored-Grafana boot tests; the live Synology guest-pull task now includes matching LXC 109 copy and checksum filters, and both retained archives were copied off-host with zero checksum differences.
- Completed the focused Grafana pilot set with compute/storage/network, Frigate surveillance/AI and UPS power-resilience dashboards. All 53 queries across the four provisioned dashboards returned live data; the missing TrueNAS pool-capacity series is recorded as a collection gap instead of an empty panel, and a refreshed protected backup passed checksum and archive validation.
- Added a link-only Grafana tile beside Beszel in Homepage's Security & Operations group, pointing directly to the provisioned HomeLab infrastructure overview without introducing widget polling or credentials during the observation period.
- Started the Grafana observability pilot on LXC 109: deployed checksum-verified Grafana OSS 13.2.0 on the private TCP 3000 path, provisioned the local Prometheus data source and a bounded HomeLab infrastructure overview, disabled unapproved alerting and automatic plugins, validated all 16 dashboard queries, and created an integrity-tested protected configuration backup.
- Completed the Prometheus observability pilot in unprivileged LXC 109 at `192.168.20.31`: checksum-verified Prometheus 3.13.2 LTS now collects bounded read-only Proxmox, TrueNAS, Frigate and three-UPS metrics through narrowly scoped network paths. All seven jobs are healthy at 1,686 active series; failure isolation, protected configuration recovery and an integrity-tested guest snapshot passed.
- Added `truenas.internal` as a persistent `192.168.20.40` record on both Pi-hole resolvers and verified it from the Mac.
- Replaced the failed UniFi PoE switch role with the Binarui **AP Switch**, documented its complete port/VLAN inventory, management recovery procedure and as-is burn-in decision.
- Preconfigured AP Switch ports 1–4 as native-VLAN-1 AP trunks permitting VLANs 1,10,20,30,40,50,60,70; reserved port 5 for recovery and port 6 for the 10G Arista uplink.
- Reassigned Arista Et34 as `Camera-PoE-TPLink`, access VLAN 60, for the old TP-Link switch's future camera-only role; single-camera validation remains deferred.
- Added follow-up work to forget the retired PoE switch in UniFi Network and investigate Mac-only access failure to Arista management.
- Documented the tested Authentik forward-auth integration for Nginx Proxy Manager, including DNS, TLS, WebAuthn, NPM regeneration and rollback details.
- Added a reusable native-OIDC, forward-auth and private-access onboarding process for current and planned services.
- Added the current Homepage dashboard milestone, code-server editing workflow and dashboard follow-up agenda.
- Recorded the NUT server at `192.168.50.25` on Arista Et31.
- Recorded the NUT server MAC `00:23:24:55:b1:1a` and confirmed it is directly connected to Arista Et31, independent of the UniFi PoE-switch uplink on Et33.
- Deployed Forgejo LXC 108 at `192.168.20.30`, migrated the complete HomeLab repository and made Forgejo the primary remote while retaining synchronized GitHub protection.
- Added Forgejo to nightly Proxmox archives and the checksum-verified Backup Synology mirror; isolated LXC 978 restore validation confirmed the service, database and repository.
- Reorganized Homepage into `Security & Operations`, `AI & Automation` and `Security & Surveillance`, with Forgejo retained under `Application Management`.
- Split the post-build enhancement portfolio into separate milestone-driven Local AI, Authentik rollout, surveillance expansion, NUT/UPS, Synology Drive and Prometheus/Grafana project documents.
- Added a Claude-ready Synology Drive family-cloud handover and a concise milestone tracker to the existing NUT/UPS handover.
- Closed Milestone 1 of the NUT/UPS project: inventoried the Lenovo (ThinkCentre M92p), confirmed hostname/DNS/time and reboot/network independence, and disabled SSH password authentication on the NUT server.
- Identified and configured the CyberPower CP1500PFCLCD (UPS #3, dedicated to Proxmox) as a NUT client via `usbhid-ups`; determined the APC BN1500M2-CA (UPS #1) has no NUT-compatible monitoring interface and will be replaced.
- Replaced UPS #1 with a second CyberPower CP1500PFCLCD, configured as NUT client `nas-ups` (dedicated to TrueNAS + both Synology units); pinned both CyberPower units' driver bindings by USB serial to avoid ambiguous matching.
- Configured least-privilege `upsd`/`upsmon` monitoring for both NUT-managed UPS units.
- Extended HomeLab Doctor (`scripts/doctor.sh`) with a `check_nut` health check covering NUT service state and both UPS units' status/battery charge.
- Added NUT/UPS server config backup coverage: a manual pull lands `ups.conf`, `nut.conf`, `upsd.users`, `upsmon.conf` and SSH hardening config in the existing `~/lab/private-backups` pipeline (Backup Synology pull + encrypted IDrive e2), with a `check_backup_age` Doctor check and documented bare-metal recovery procedure.
- Added the NUT server to Beszel for host-level monitoring (CPU, memory, disk, temperature); required a new OPNsense rule permitting Management VLAN 50 to reach the Beszel hub on Servers VLAN 20.
- Relocated the NUT server to its permanent placement and identified/configured UPS #2 (CyberPower OR500LCDRM1U, NUT device `network-ups`) as the third NUT client, now carrying real production load (Arista switch, OPNsense, UniFi PoE switch); extended `upsmon` monitoring and HomeLab Doctor's `check_nut` to cover all three units.
- Documented the live UPS power topology and runtime baseline: `nas-ups` has the shortest runtime of the three monitored units despite matching capacity, since it's serving three NAS-class devices at once — the key input for Milestone 3's shutdown-threshold planning.
- Closed Milestone 2 of the NUT/UPS project: a reboot test with all three UPS units connected confirmed every NUT driver, `nut-server`, `nut-monitor` and `beszel-agent` recover automatically and rebind to the correct serial after USB re-enumeration.
- Started Milestone 3 (coordinated shutdown): Proxmox is now a NUT network client of `proxmox-ups`, with a custom `SHUTDOWNCMD` script that stops Frigate (its NFS dependency on TrueNAS) first, then remaining guests, then triggers shutdown on both Synology units via SSH, then powers off Proxmox itself. Not yet live-tested.
- TrueNAS is now a NUT client of `nas-ups` via its native `ups` middleware service (not a manual package install), configured to wait for the real low-battery signal and never cut the UPS's own outlet power (shared with the Arista switch). Not yet live-tested.
- Tightened shutdown thresholds via `override.battery.charge.low` (replacing each unit's ~10% hardware default): `nas-ups`=50%, `proxmox-ups`=80% (early, since its Synology shutdown step depends on Arista/`nas-ups` staying powered), `network-ups`=25%.
- Validated the threshold trigger mechanism via a safe simulated test (briefly unplugging `proxmox-ups` with `SHUTDOWNCMD` swapped for a harmless command). Caught and fixed a real gap: `override.battery.charge.low` alone doesn't make the driver compute `LB` from charge without also setting `ignorelb`. Fixed on all three UPS units; confirmed working.
- Closed Milestone 3 of the NUT/UPS project (coordinated shutdown). Caught and fixed a self-shutdown bug on the Lenovo NUT server itself: its local `upsmon` was treating any of the three UPS units going critical as grounds to shut itself down, even though only `network-ups` actually powers it. Documented the final shutdown order, power-return behavior, and manual override options.
- Updated repository-wide architecture, operations, network baseline and hardware inventory docs to reflect the final UPS/NUT design: a new architecture section and accepted-risk rows, a UPS quick-reference for operators, the new narrow OPNsense rules, and all four physical UPS units added to hardware inventory.
- Produced the UPS & Power Resilience Implementation Close-Out report for Aster/ChatGPT's review, and explicitly deferred controlled failure/recovery testing and push-style alerting (both with documented reasons and risks), closing out Milestone 5.
- Added a milestone-driven TrueNAS DIY SAS expansion project for a backplane-free, independently powered enclosure using the existing controller's two free disk endpoints.

### Fixed
- Reconciled the main Synology's dual-homed wiring by mapping DSM MACs to the live switch ports: Et28 is now `GoWest-NAS-Servers` on VLAN 20 for `192.168.20.41`, and Et24 is `GoWest-NAS-Trusted` on VLAN 10 for `192.168.1.41`; saved the Arista configuration and validated ping, SSH, SMB and DSM access through both addresses.
- Added the main Synology's Et28 link to HomeLab Doctor's expected Arista links.
- Reconciled the post-UPS recabling: restored the OPNsense all-VLAN trunk to Et42, the TrueNAS primary to Et9 and the camera switch handoff to Et34; repurposed Et15 as the 10G TrueNAS standby access port on VLAN 20.
- Updated HomeLab Doctor's expected Arista links from stale Et17/Et40 entries to the verified Et15/Et42 production paths.
- Corrected the Mac Ethernet DNS search domain from the stale numeric `192.168.1.20` value to `internal` and verified both Pi-hole resolvers, routing and Internet access.
- Validated both U7 Pro XG links at 2.5G full, the AP Switch uplink at 10G full and all three SSIDs after configuring the AP-facing ports as trunks.
- Documented the AP Switch native-VLAN anomaly: management IP `192.168.50.26` is effectively reached through VLAN 1/untagged rather than VLAN 50, while Arista Et33 classifies untagged traffic into native VLAN 10.
- Documented the storm-related UniFi PoE switch boot failure, rejected TP-Link fallback and managed PoE replacement requirement.
- Selected and purchased the managed PoE replacement; installation validation and configuration capture remain scheduled after delivery.

## v1.7.0

### Project Completion
- Completed Phase 11 final consolidation and published the reconciled network baseline, topology, architecture decisions, accepted risks and recovery coverage.
- Closed production Phases 1–5 and 7–10 while retaining surveillance and local AI as explicitly bounded follow-on pilots.
- Lifted the original project scope lock; future elective work now requires a separately reviewed roadmap.

### Added
- Deployed unprivileged Hermes Agent LXC 104 at `192.168.70.10` on isolated Lab VLAN 70
- Deployed Ubuntu 24.04 Ollama VM 105 at `192.168.70.11` with 4 vCPU, 14 GB RAM and a 32 GB disk
- Published Ollama on TCP 11434 and connected Hermes through its OpenAI-compatible `/v1` endpoint
- Created the local `qwen3-64k:8b` Ollama model profile with a 65,536-token context window
- Installed and passed through the Coral Edge TPU to Frigate VM 102
- Added HomeLab Doctor service and backup-age coverage for Hermes LXC 104 and Ollama VM 105
- Added privacy-safe configuration drift detection for protected OPNsense, Arista and Proxmox backups

### Validated
- Published the reconciled 2026-08-20 network diagram and current-state baseline covering all seven VLANs, completed management migrations and the final healthy stability checkpoint
- Reconciled the HomeLab architecture decisions and accepted-risk register, including single-host dependencies, storage capacity, recovery-test boundaries and IPv6 deferral
- Confirmed Hermes can use the local Ollama provider from Lab VLAN 70; CPU-only responses work but are slow enough that the deployment remains a pilot
- Confirmed 8 GB and 10 GB allocations were insufficient for the local model and that the 14 GB VM allocation runs without the observed OOM failure
- Confirmed the Coral PCIe device is isolated in its own IOMMU group, loads through `gasket`/`apex`, appears as `/dev/apex_0` in the Frigate container and reports approximately 10 ms inference
- Confirmed Frigate remained healthy with the Coral detector loaded and fresh recordings after the passthrough change
- Confirmed the enabled all-guests Proxmox job covers LXC 104 and VM 105 and that both have fresh local archives
- Confirmed the Backup Synology mirrored and checksum-verified the retained LXC 104 and VM 105 archives on 2026-08-20
- Validated isolated restores of Hermes LXC 104 and Ollama VM 105, including a healthy Hermes service start and a successful Ollama guest boot
- Confirmed the mirrored LXC 104 and VM 105 archives are included in the encrypted `automated/proxmox-guests` Hyper Backup selection

### Planned
- Resolve Proxmox memory overcommit before sustained simultaneous use of all guests
- Install the purchased E5-2698 v4 and remaining planned RAM, then re-baseline Frigate and local-AI capacity
- Evaluate the exact Intel Arc Pro B60 SKU, VRAM, physical clearance, PSU capacity and passthrough plan before purchase or installation
- Remove unused Hermes cloud-auth remnants after confirming they are no longer required

### Security
- Kept Hermes and Ollama on isolated Lab VLAN 70 rather than Trusted, Servers or Management
- Kept reusable credentials, tokens and provider-authentication material outside Git

## v1.6.0

### Added
- Deployed Home Assistant OS 18.2 as Proxmox VM 103 on Servers VLAN 20
- Reserved `192.168.20.11` and published `home-assistant.home.internal`
- Created the initial full Home Assistant recovery point before integrations
- Integrated the Philips Hue bridge using HA-specific TCP 80 and 443 firewall rules
- Integrated Lutron Caséta at reserved address `192.168.30.102` and validated local control of imported devices
- Deployed Beszel 0.18.7 for Docker, Proxmox and Frigate with a Homepage systems-up widget
- Added functional HomeLab Doctor checks for OPNsense WAN counters, Arista links and hardware, Proxmox guests/resources, TrueNAS pools/NFS/bond, Frigate recording freshness and reported backup results
- Added failure-result reporting from the Synology configuration and Proxmox archive pull tasks
- Added encrypted daily Home Assistant native backups to local and dedicated Backup Synology storage
- Added VM 103 to checksum-verified Proxmox archive mirroring and HomeLab Doctor guest/backup-age checks
- Added the Aqara M3 through Matter with six active water sensors, the shutoff valve and lock
- Added a minimal mDNS relay across LAN, Servers and IoT plus a host-scoped Trusted-media exception for five Apple TVs
- Created and validated the Hue Hall motion-to-Lutron `Laundry Main Lights` pilot automation
- Created a simple Home Assistant Overview and a validated local non-administrator household account
- Installed HACS and validated the community-store workflow without adding an elective repository
- Expanded the Laundry pilot with the `Laundry bright` scene, `Laundry motion lighting` script, five-minute occupancy timer and timer-finished light-off automation
- Configured sustained actionable Beszel alerts for Docker, Proxmox and Frigate with verified iCloud SMTP delivery
- Added audited execution orders and rollback boundaries for the remaining Server VLAN 20 and Management VLAN 50 migrations
- Added a domain-filtered HomeKit Bridge as the Apple Home/Siri presentation layer and validated live Siri control while retaining Home Assistant as the sole automation authority
- Documented the completed Server VLAN 20 migration and its dependency/rollback validation

### Changed
- Migrated Docker LXC 100 from Trusted `192.168.1.20` to Servers VLAN 20 at `192.168.20.20`, including Homepage, Portainer, primary Pi-hole, Tailscale and Beszel
- Updated OPNsense DHCP option 6 and `home.internal`, the Pi-hole resolver alias, Homepage links, service inventories and the Mac SSH alias for the new address
- Extended the Tailscale subnet router and identity-specific policy to cover both Trusted `192.168.1.0/24` and Servers `192.168.20.0/24`
- Migrated the main Synology from `192.168.1.41` to `192.168.20.41` and the Backup Synology from `192.168.1.42` to `192.168.20.42`
- Migrated TrueNAS and its secondary Pi-hole from `192.168.1.40` to `192.168.20.40`; updated Frigate NFS, DHCP DNS, aliases, Homepage, SSH and operational inventories
- Updated the secondary Pi-hole upstream and `internal` conditional-forwarding destination from the Trusted gateway `192.168.1.1` to the Servers gateway `192.168.20.1`
- Identified and labelled Arista Et15 as the wired Downstairs Apple TV and Et16 as the Aqara Hub M3, then moved both access ports from Trusted VLAN 10 to IoT VLAN 30
- Migrated UniFi OS Server LXC 101, the UniFi PoE switch and both access points from Trusted VLAN 10 to Management VLAN 50 at `192.168.50.21`, `.30`, `.31` and `.141`
- Migrated Proxmox management from `192.168.1.10` to tagged Management VLAN 50 at `192.168.50.10`
- Migrated the Arista management SVI from VLAN 10 at `192.168.1.2` to VLAN 50 at `192.168.50.2`, added its management default route and removed the former address after a protected timed cutover
- Extended Tailscale advertisement and identity-based policy to Management `192.168.50.0/24` and validated remote access
- Updated Homepage, HomeLab Doctor, guided backups and device/service inventories for the UniFi management addresses

### Validated
- Formally closed Phase 5 Monitoring and Phase 7 Home Assistant/Controlled IoT Migration after their completion gates passed; Prometheus/Grafana remain deferred and Phase 6 remains open for the Coral TPU work
- Fully tested VLAN 70 with disposable Proxmox LXC 970: DHCP, redundant Pi-hole DNS, blocking and Internet access passed; internal application endpoints remained isolated
- Corrected the OPNsense VLAN 70 parent from `igb0` to the active `ix0` trunk and repeated the validation successfully
- Confirmed Frigate's current HEVC 5120x1552 stream, approximately 24 GB/day recording growth and stable NFS recording flow
- Confirmed the Quadro K620 is not worthwhile for the current Frigate workload; it will be removed during the planned CPU/Coral maintenance
- Verified Frigate retention beyond the configured 3-day continuous window
- Selected the incoming E5-2698 v4, RAM and Coral M.2 TPU upgrade path for Frigate
- Restored VM 103 as isolated temporary VM 903, booted HAOS, Supervisor and Core without network connectivity, then removed the test VM
- Confirmed IoT devices remain unable to initiate unrestricted RFC1918 access using live OPNsense rule counters
- Confirmed both Home Assistant native backups and mirrored VM 103 archives are present off-host
- Confirmed the first two 16 GB ECC RDIMMs are detected as 32 GB at 1866 MT/s with no reported boot-time memory error and passed two complete 24 GB `memtester` loops
- Confirmed Coral `G650-04527-01` is the single M.2 2230 A+E-key PCIe x1 model and selected a compatible PCIe x1 E-key carrier
- Validated the migrated Docker services locally and over cellular/Tailscale, including Homepage, Home Assistant, Frigate and Proxmox access
- Validated post-migration Hyper Backup, SMB, Home Assistant backup storage, restricted Synology pull paths, TrueNAS applications, redundant DNS and Frigate NFS recording flow after a full VM reboot
- Formally completed Phase 8 with all intended server workloads on VLAN 20 and HomeLab Doctor reporting 39 passes and no failures
- Confirmed Et15 and Et16 each learn only the expected endpoint MAC, negotiate at 100 Mbps and obtain working IoT VLAN 30 DHCP leases after migration
- Validated Management VLAN DHCP, redundant DNS, Internet access and internal isolation with disposable LXC 970 before migrating UniFi
- Confirmed the controller and all three UniFi devices online on VLAN 50, then removed the temporary Trusted interface, validation containers and legacy migration rules
- Revalidated secondary Pi-hole public DNS, `home.internal` resolution and domain blocking after correcting its VLAN-local forwarding destination

### Planned
- Add MQTT and the Frigate Home Assistant integration after the first automation pilot, not during it
- Add any remaining fringe IoT/media integration only when a planned use case justifies it
- Install the second matching RDIMM pair and E5-2698 v4 when available, then install and validate the Coral TPU in a separate controlled step

### Security
- Kept Home Assistant on Servers VLAN 20 and permitted only host `192.168.20.11` to initiate TCP/UDP access to IoT VLAN 30
- Preserved Lab and IoT isolation; no broad IoT-to-Servers rule was added, and discovery relay scope is limited to LAN, Servers and IoT
- Limited Trusted-media access to Home Assistant host `192.168.20.11` and a five-device Apple TV alias; no general Servers-to-Trusted exception was created
- Added one host-scoped Servers-to-Trusted exception for the Tailscale subnet-router host `192.168.20.20`; the general Servers isolation rules remain in force
- Restricted Management VLAN access to the approved Mac mini, Mac laptop and iPhone alias, with an explicit block for other Trusted clients

## v1.5.0

### Added
- Functional `lab doctor` checks for both Pi-hole DNS endpoints, including public, local and blocked-domain resolution
- Stable Primary and Secondary Pi-hole service labels and Homepage tiles
- OPNsense aliases for the two Pi-hole servers and all routed client VLANs
- A single early floating firewall exception limited to TCP/UDP 53 from client VLANs to the Pi-hole pair

### Changed
- OPNsense Dnsmasq initially advertised `192.168.1.20` and `192.168.1.40` through DHCPv4 option 6 on every configured DHCP range; the current endpoints are `192.168.20.20` and `192.168.20.40`
- Renamed the Docker-hosted Pi-hole internal hostname to `pihole-primary`; the TrueNAS-managed secondary retains its generated container hostname
- Replaced the Mac-only DNS pilot with redundant network-wide DHCP advertisement

### Validated
- Both Pi-holes resolve public and `internal` names and block the test domain
- LAN, Servers VLAN 20, IoT VLAN 30 and Guest VLAN 40 can reach both resolvers
- The consolidated DNS exception precedes the existing RFC1918 isolation blocks in the compiled OPNsense ruleset
- Frigate remained healthy with zero container restarts, fresh NFS recording segments and no recording interruptions during the final 24-hour observation

### Security
- Preserved VLAN isolation by allowing only TCP/UDP 53 to the Pi-hole server alias
- Kept encrypted/private client DNS outside the DHCP rollout guarantee; no broad DoH/DoT interception was introduced
- Created checksum-recorded OPNsense backups before and after the DNS rollout

## v1.4.0

### Added
- Automated checksum-verified configuration pulls from the Mac to the Backup Synology
- Automated read-only Proxmox guest-archive mirroring to the Backup Synology
- Failure-only email alerts through the restricted Synology-to-Mac SSH path and Apple Mail
- Client-side-encrypted Hyper Backup protection in a private IDrive e2 S3-compatible bucket
- Bucket-scoped cloud credentials, 23-version rotation and weekly integrity checking
- Manual `lab backup synology-copy [--dry-run]` fallback
- Frigate SSH alias and toolkit inventory integration
- Deferred post-project evaluation of Tailscale Services

### Validated
- Initial and incremental Hyper Backup runs with two recoverable versions
- Off-site LXC 100 archive recovery with an exact SHA-256 match
- Homepage configuration restore and isolated temporary-container service validation
- Offline disposable Proxmox LXC restore with isolated networking
- Non-interactive OPNsense and Frigate public-key SSH
- `ssh frigate`, `lab ssh frigate` and the Homepage Frigate SSH launch path

### Security
- Restricted the Proxmox export identity to source-address-bound, read-only `rrsync`
- Kept S3 credentials, SSH private keys, Hyper Backup encryption material and raw archives outside Git
- Stored the Hyper Backup recovery key separately in encrypted, backed-up recovery storage
- Preserved tailnet-only scope for the future Tailscale Services evaluation, with no Funnel or public exposure

### Fixed
- Loaded the shared output library before the `lab` command renders backup help
- Removed the abandoned interactive Synology-copy pause from `lab backup all`
- Repaired OPNsense public-key authentication and configured macOS Keychain-backed SSH-agent loading

## v1.3.0

### Added
- Implemented routed infrastructure and baseline policy for VLANs 20, 50, 60 and 70
- Deployed Frigate in Proxmox VM 102 on Servers VLAN 20
- Isolated the Reolink Duo 2V PoE camera on Cameras VLAN 60
- Added narrowly scoped Frigate-to-camera HTTP, RTSP and ONVIF access
- Added TrueNAS NFS recording storage and reboot-safe systemd startup ordering
- Added Frigate web and SSH shortcuts to Homepage
- Added a private, checksum-verified Frigate configuration backup procedure

### Validated
- Frigate and its NFS storage recover automatically after a full VM reboot
- Main and substreams, ONVIF discovery, continuous recording and recent MP4 creation
- Camera TCP 9000 remains blocked from the Frigate VM

### Security
- Camera and Frigate credentials are excluded from repository documentation
- Cameras remain blocked from initiating access to internal RFC1918 networks

## v1.2.4

### Documented
- Recorded the verified second copy of the 2026-08-08 recovery set on the backup Synology
- Recorded successful SHA-256 verification of all six protected files from the Synology destination

### Clarified
- The Mac originals remain intact
- The Synology copy is on a separate host but remains same-site rather than off-site
- Automated replication and deletion remain deferred until retention and restore testing are established

## v1.2.3

### Designed
- Reserved VLAN 70 and `192.168.70.0/24` for isolated Proxmox experiments
- Defined the future Arista Et3 trunk, VLAN-aware Proxmox bridge and per-workload tagging model
- Defined default-deny internal policy, administrator access, implementation validation and rollback requirements

### Clarified
- Proxmox management and existing production containers remain on native VLAN 10 during the Lab rollout
- This release changes documentation only and does not deploy VLAN 70

## v1.2.2

### Added
- Documented the physical 15U rack elevation from U15 through U1
- Recorded shelf contents, patch-panel placement, core switch, OPNsense, PoE switching, UPS and reserved capacity

## v1.2.1

### Added
- Homepage SSH launch group for Proxmox, Docker LXC, OPNsense and TrueNAS
- Remote SSH validation through the private Tailscale subnet route
- Backup and restore guidance for Homepage, Pi-hole, Docker Compose and Tailscale policy
- Verified Proxmox guest archives and consolidated overlapping backup jobs into one retained daily schedule

### Clarified
- Remote SSH uses the hosts' existing OpenSSH services over Tailscale; native Tailscale SSH is not enabled
- No inbound WAN SSH rule or port-forward is required
- Raw backups, credentials, tokens and private configuration must not be committed to this repository

## v1.2.0

### Added
- Validated current-network baseline
- Homepage service dashboard at `home.internal`
- Tailscale subnet-router and split-DNS documentation
- Identity-restricted remote access to the trusted LAN
- Production IoT VLAN 30 and Guest VLAN 40 documentation
- TrueNAS active-backup LAN bond documentation
- Pi-hole 2026.05.0 container and Mac Mini DNS-filtering pilot
- Pi-hole quick link on the Homepage service dashboard

### Improved
- Documented the stable replacement WAN cable and X553 receive-ring tuning
- Updated service inventory and roadmap to match the deployed environment
- Clarified that remote administration uses Tailscale without inbound WAN ports
- Documented the Pi-hole-to-OPNsense DNS chain, validation commands and rollback procedure

## v1.1.0

### Added
- Modular backup framework
- Arista automated backups
- Proxmox host configuration backups
- Unified `lab backup all`
- Passwordless SSH for all infrastructure
- Improved help system
- Guided backup workflow

### Improved
- Shared output library
- Device configuration
- Health monitoring
- Repository organization

## v1.0.0

- Initial infrastructure baseline
- Completed the Phase 11 firewall and recovery-coverage review: removed the obsolete Beszel rule and empty legacy UniFi alias, reconciled all six guest archives and verified mirrors, and documented representative restore evidence plus accepted recovery boundaries.
