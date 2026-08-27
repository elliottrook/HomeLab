# Home Network Baseline

Baseline date: 2026-08-26
Status: This is the reconciled Phase 11 production baseline. VLANs 20, 30, 40,
50, 60 and 70 are routed and policy-enforced by OPNsense while VLAN 10 remains
the native Trusted network. Server, IoT, Guest, Management, Camera and Lab
migrations are complete. HomeLab Doctor reports 44 passes with no warnings or
failures, protected configuration shows no unaccepted drift, scheduled
failure-only reporting is active and operationally important TLS certificates
are monitored.

## Recovery checkpoint

Completed 2026-08-05:

- OPNsense configuration backup downloaded.
- UniFi Network backup downloaded from Settings > Control Plane > Backups.
- Arista running configuration backed up.
- TrueNAS configuration backup downloaded before the 2026-08-08 bond change.

Post-change recovery checkpoint completed 2026-08-08:

- Fresh OPNsense configuration backup downloaded after the IoT VLAN 30 rollout.
- Fresh UniFi Control Plane backup created/downloaded after the production IoT SSID migration.
- A dated 2026-08-08 backup set on the Mac contains checksum-recorded OPNsense, UniFi, TrueNAS, Homepage and Pi-hole exports plus a private Tailscale operational-state snapshot. All six files passed the saved SHA-256 manifest; the OPNsense XML, TrueNAS TAR, Homepage TGZ and Pi-hole Teleporter ZIP also passed structural or archive-integrity checks.
- The complete dated set and its checksum manifest were copied over SMB to `Backup/HomeLab-Backups/2026-08-08` on the backup Synology. Verification executed from the Synology destination reported `OK` for all six protected files. The Mac originals remain intact; this is a second-host, same-site copy rather than an off-site backup.
- Proxmox LXC 100 and LXC 101 `vzdump` archives on `/mnt/backups` passed complete Zstandard integrity tests. The backup disk is a separate 4 TB ext4 disk attached to the Proxmox host.
- Three overlapping Proxmox jobs were consolidated to one all-guests job at 02:30 using snapshot mode, Zstandard compression and 7-daily/4-weekly/6-monthly retention. The redundant jobs were disabled, not deleted, and a dry run marked only same-day duplicates for pruning.
- Arista VLAN and trunk changes saved to startup-config; an external copy of the current configuration was retained.

Backup-resilience checkpoint completed 2026-08-11:

- The Backup Synology independently pulls and checksum-verifies the Mac configuration recovery set and retained Proxmox guest archives.
- LXC 100, LXC 101 and QEMU 102 archives are retrieved through a dedicated source-restricted, read-only Proxmox export identity.
- Failure-only email notification was validated end to end; successful production runs do not send mail.
- Hyper Backup protects configuration and guest archives in a private IDrive e2 S3-compatible bucket using client-side encryption and 23-version rotation.
- Initial and incremental cloud versions completed successfully.
- A downloaded encrypted-cloud recovery of an LXC 100 archive matched the same-site source exactly by SHA-256.
- Frigate recordings and general media remain excluded from the off-site set.

Server-migration checkpoint completed 2026-08-15:

- A fresh, Zstandard-verified LXC 100 archive was created before the change.
- Docker LXC 100 moved intact from Trusted `192.168.1.20` to Servers VLAN 20 at `192.168.20.20`; Homepage, Portainer, primary Pi-hole, Tailscale and Beszel returned healthy.
- OPNsense DHCP option 6, `home.internal`, the Pi-hole resolver alias, local SSH configuration, Homepage links and active service configuration were updated to the new address.
- Tailscale now advertises both `192.168.1.0/24` and `192.168.20.0/24`, with both routes granted only to the administrator identity. Local and cellular/Tailscale access to the migrated services and representative Trusted/Servers targets passed.

Server-migration checkpoint completed 2026-08-16:

- Main Synology moved to `192.168.20.41` and Backup Synology to `192.168.20.42`; SMB, DSM, Synology Drive, Plex, Immich, Hyper Backup and the source-restricted backup pull paths passed as applicable.
- TrueNAS moved to `192.168.20.40` with both active-backup bond members on VLAN 20. Secondary Pi-hole, storage and application endpoints passed.
- Frigate's NFS source was updated to the new TrueNAS address and validated through a complete VM reboot, healthy container state and fresh recording flow.
- OPNsense DHCP/DNS aliases, Homepage, SSH aliases, inventories and operational scripts were updated. HomeLab Doctor completed with 39 passes, no functional warning and no failure.

Final-consolidation checkpoint completed 2026-08-20:

- Arista management is operational only on Management VLAN 50 at
  `192.168.50.2`; its former VLAN 10 address has been removed.
- Proxmox management is operational on `192.168.50.10` through tagged VLAN 50.
- The UniFi controller, PoE switch and both access points are operational on
  Management VLAN 50.
- Tailscale advertises Trusted, Servers and Management routes only to the
  approved administrator identity.
- HomeLab Doctor completed with 44 passes, no warnings and no failures.
- Configuration drift detection reports no unaccepted drift.
- Scheduled failure-only reporting and certificate monitoring are passing.
- All six Proxmox guests have local archives, checksum-verified Synology
  mirrors and representative isolated restore evidence.

AP/PoE switch replacement checkpoint completed 2026-08-26:

- The Binarui unit entered production under the documented name **AP Switch**.
- Both U7 Pro XG access points negotiated 2.5G full, the Arista uplink negotiated
  10G full and all three SSIDs became usable after the AP ports were configured
  as trunks.
- Arista Et33 is the AP Switch uplink trunk. Et34 is an access VLAN 60 handoff
  for the old TP-Link 8-port 1Gb PoE switch's future camera-only role.
- AP Switch management remains a documented anomaly: `192.168.50.26` is
  numbered in Management VLAN 50 but its Layer 2 management plane appears on
  VLAN 1/untagged. Direct recovery through port 5 is known good.
- Camera validation through Et34 and the TP-Link was deferred until the cameras
  are reconfigured. The retired UniFi PoE switch still needs to be forgotten in
  the UniFi Network application.

Store copies off the network appliances and treat them as sensitive configuration data.

## Current topology

```text
Internet / TELUS fibre
  |
  | 10 GbE WAN
  |
OPNsense — routing, DHCP and firewall policy
  |
  | Arista Et40 trunk
  |
Arista core — 192.168.50.2
  |
  +-- VLAN 10 Trusted — 192.168.1.0/24
  |     +-- Personal computers and phones
  |
  +-- VLAN 20 Servers — 192.168.20.0/24
  |     +-- Docker LXC 100 — 192.168.20.20
  |     +-- Frigate VM 102 — 192.168.20.10
  |     +-- Home Assistant VM 103 — 192.168.20.11
  |     +-- Forgejo LXC 108 — 192.168.20.30
  |     +-- TrueNAS — 192.168.20.40
  |     +-- Main Synology — 192.168.20.41
  |     +-- Backup Synology — 192.168.20.42
  |
  +-- VLAN 30 IoT — 192.168.30.0/24
  |     +-- Lutron, Hue, Aqara, TVs and consumer devices
  |
  +-- VLAN 40 Guest — 192.168.40.0/24
  |     +-- Internet-only guest clients
  |
  +-- VLAN 50 Management — 192.168.50.0/24
  |     +-- Arista — 192.168.50.2
  |     +-- Proxmox — 192.168.50.10
  |     +-- UniFi controller — 192.168.50.21
  |     +-- Authentik LXC 106 — 192.168.50.22
  |     +-- Reverse Proxy LXC 107 — 192.168.50.23
  |     +-- NUT server — 192.168.50.25
  |     +-- AP Switch — 192.168.50.26 (direct VLAN 1 recovery; see anomaly below)
  |     +-- Hall AP — 192.168.50.31
  |     +-- Office AP — 192.168.50.141
  |
  +-- VLAN 60 Cameras — 192.168.60.0/24
  |     +-- Reolink Duo 2V PoE — 192.168.60.10
  |
  +-- VLAN 70 Lab — 192.168.70.0/24
        +-- Hermes Agent LXC 104 — 192.168.70.10
        +-- Ollama VM 105 — 192.168.70.11

Tailscale remote administration
  |
homelab-gateway — 192.168.20.20
  +-- Trusted route     192.168.1.0/24
  +-- Servers route     192.168.20.0/24
  +-- Management route  192.168.50.0/24
```

## Device and address inventory

| Address | Device | MAC | Arista path |
|---|---|---|---|
| 192.168.1.1 | OPNsense LAN | e8:b5:d0:e1:8e:4f | Et40 |
| 192.168.50.2 | Arista management SVI | 44:4c:a8:1f:3e:c5 | Vlan50 |
| 192.168.50.10 | Proxmox | 6c:92:bf:27:89:a3 | Et4 |
| 192.168.20.20 | Docker LXC / Homepage / Pi-hole / Tailscale subnet router / Beszel | bc:24:11:43:71:67 | Et4 via Proxmox, tagged VLAN 20 |
| 192.168.50.21 | UniFi controller LXC 101 | bc:24:11:b6:de:53 | Et4 via Proxmox, tagged VLAN 50 |
| 192.168.50.25 | NUT server | 00:23:24:55:b1:1a | Et31, direct access port in management VLAN 50 |
| 192.168.50.26 | AP Switch | Not yet recorded | Et33; IP is not reachable normally on VLAN 50 because management appears on VLAN 1/untagged |
| 192.168.50.31 | UniFi Hall AP | 90:41:b2:ce:76:10 | AP Switch port 1, 2.5G full |
| 192.168.50.141 | UniFi Office AP | 84:78:48:ce:17:08 | AP Switch port 2, 2.5G full |
| 192.168.20.40 | TrueNAS `bond0` | 6c:92:bf:67:fb:bc | Et9 primary / Et17 failover, VLAN 20 |
| 192.168.20.41 | Synology DS920+ | 00:11:32:ca:e5:e5 | Et24, access VLAN 20 |
| 192.168.20.42 | Backup Synology | 00:11:32:c8:06:c5 | Et48, access VLAN 20 |
| 192.168.30.102 | Lutron | ec:24:b8:8e:d4:10 | Et45, access VLAN 30 |
| 192.168.30.155 | Downstairs Apple TV (wired) | d0:03:4b:29:99:23 | Et15, access VLAN 30 |
| 192.168.30.164 | Philips Hue | 00:17:88:22:42:e5 | Et46, access VLAN 30 |
| 192.168.30.166 | Aqara Hub M3 (wired) | 18:c2:3c:62:07:b0 | Et16, access VLAN 30 |
| 192.168.20.10 | Frigate VM 102 | bc:24:11:f5:09:a3 | Et4 via Proxmox, tagged VLAN 20 |
| 192.168.20.11 | Home Assistant OS VM 103 | bc:24:11:08:16:a3 | Et4 via Proxmox, tagged VLAN 20 |
| 192.168.50.22 | Authentik LXC 106 | bc:24:11:71:fe:a9 | Et4 via Proxmox, tagged VLAN 50 |
| 192.168.50.23 | Reverse Proxy LXC 107 | bc:24:11:f0:ef:fa | Et4 via Proxmox, tagged VLAN 50 |
| 192.168.20.30 | Forgejo LXC 108 | bc:24:11:2f:f5:08 | Et4 via Proxmox, tagged VLAN 20 |
| 192.168.70.10 | Hermes Agent LXC 104 | Not yet recorded | Et4 via Proxmox, tagged VLAN 70 |
| 192.168.70.11 | Ollama VM 105 | Not yet recorded | Et4 via Proxmox, tagged VLAN 70 |
| 192.168.60.10 | Reolink Duo 2V PoE | ec:71:db:80:49:6e | UniFi PoE port 3, VLAN 60 |
| 192.168.1.206 | Mac mini (in studio) | d0:11:e5:9e:c4:76 | Et8 |
| 192.168.30.197 | Downstream UniFi wireless client | d8:c8:0c:bb:52:a4 | Et33 via UniFi, VLAN 30 |
| 192.168.1.228 | Living-room Apple TV | c0:95:6d:81:11:5d | Et11 |

## Known-good health findings

- All connected Arista ports report zero FCS, alignment, symbol, receive, runt, giant, and transmit errors.
- Queue-drop counters remained unchanged between observations; existing totals are historical.
- Et33 (AP Switch uplink) and Et40 (OPNsense LAN) have zero queue drops at the retained baseline observation.
- Arista is the MSTP root for VLAN 10. All connected ports are forwarding; Et33 is the expected spanning-tree boundary/uplink.
- Switch temperatures and cooling are healthy. Highest observed PHY temperature was 51 C.
- PSU2 is online and supplies approximately 160 W. PSU1 is intentionally unpowered; redundancy is knowingly unavailable.
- OPNsense ix0 and ix1 are active at 10Gbps with correct LAN/WAN addressing and routing. The permanent ix1 WAN path completed its final stress test without a link flap, physical fault, CRC error, link interrupt, packet loss, or mbuf allocation failure.
- The temporary switch has been removed. Proxmox is directly connected on Arista Et4 as a trunk with native VLAN 10 and tagged VLANs 20, 50 and 70. Proxmox management uses `vmbr0.50` at `192.168.50.10`; the base bridge remains addressless. The Mac mini is directly connected on Et8 as an access port in VLAN 10.
- TrueNAS 25.10.5 uses `bond0` in active-backup mode at 192.168.20.40/24. Member `enp5s0f0` (MAC 6c:92:bf:67:fb:bc, Arista Et9) is the preferred primary and `enp5s0f1` (permanent MAC 6c:92:bf:67:fb:bd, Arista Et17) is the standby. Both links operate at 10 Gbps, MII monitoring runs every 100 ms, and `primary_reselect` is `always`. A controlled Et9 shutdown moved service to Et17 with one lost ping; restoring Et9 automatically returned service to the primary. Both switch ports remain independent access ports in VLAN 20 with PortFast; no port-channel or LACP is configured.
- Arista management is provided by Vlan50 at 192.168.50.2/24. Vlan10 remains addressless, Management1 is unassigned/down, and the management default route is `0.0.0.0/0` via `192.168.50.1`.
- UniFi Network Server version 10.5.67 runs in LXC 101 at `192.168.50.21` and uses third-party-gateway networks named Default, IoT (VLAN 30), Guest (VLAN 40) and Management (VLAN 50). The retired UniFi PoE switch has been physically replaced and remains to be forgotten in the UniFi Network application. Hall and Office U7 Pro XG APs use `.31` and `.141` and are connected to AP Switch ports 1 and 2 at 2.5G full. Local UniFi OS management is exposed at `https://192.168.50.21:11443` and is reachable only from approved administrator devices.
- OPNsense Guest interface `vlan0.40` is active on parent `ix0` at 192.168.40.1/24. Dnsmasq is the active DHCP service and serves 192.168.40.100-192.168.40.199 with 86,400-second leases. Kea was disabled after its logs confirmed it could not bind UDP port 67 because dnsmasq already owned the port.
- Arista Et40 is a trunk with native VLAN 10 and VLANs 10,20,30,40,50,60,70 allowed. Et33 is a trunk with native VLAN 10 and VLANs 10,30,40,50,60 allowed. Temporary test ports Et1 and Et2 are access ports in VLANs 40 and 30 respectively.
- AP Switch ports 1 through 4 are trunks with native VLAN 1 and VLANs
  1,10,20,30,40,50,60,70 permitted. Ports 1 and 2 serve the APs; ports 3 and 4
  are spare preconfigured AP/multigig PoE trunks. Port 5 is access VLAN 1 for
  emergency recovery. Port 6 is the 10G trunk to Arista Et33.
- The AP Switch/Et33 native-VLAN mismatch is deliberate and documented:
  untagged/native VLAN 1 traffic from the AP Switch is classified into native
  VLAN 10 by Arista Et33. Tagged SSID VLANs work, but AP Switch management IP
  `192.168.50.26` does not match its actual Layer 2 management path. OPNsense
  showed `.50.26` incomplete on `vlan0.50`. Direct recovery works by connecting
  a Mac configured as `192.168.50.27/24` to AP Switch port 5.
- Arista Et34 is described `Camera-PoE-TPLink` and configured as access VLAN 60.
  It is reserved for the old TP-Link 8-port 1Gb PoE switch as a flat camera-only
  switch. Validation with one reconfigured camera remains pending.
- No AP Switch firmware update was attempted. The interface requires a local
  image and no trustworthy published support/download source was identified;
  treat it as an as-is appliance during the burn-in trial.
- Arista `192.168.50.2` was reachable from OPNsense and Proxmox but not from
  Jason's Mac during the 2026-08-26 troubleshooting session. The Mac-specific
  path remains a later investigation.
- OPNsense IoT interface `vlan0.30` is active on parent `ix0` at 192.168.30.1/24. Dnsmasq serves 192.168.30.100-192.168.30.199 with 86,400-second leases and the `iot.internal` DHCP domain. The validated rule order allows IoT DNS and NTP to the interface address, blocks access to the firewall and RFC1918 networks, and permits remaining IPv4 Internet traffic.
- The OPNsense `os-mdns-repeater` plugin relays multicast DNS only among `ix0` (LAN), `vlan0.20` (Servers) and `vlan0.30` (IoT). Guest and WAN are excluded.
- Philips Hue on Et46 uses 192.168.30.164 and Lutron on Et45 uses 192.168.30.102. Both vendor apps and Apple Home remained functional after migration to VLAN 30.
- The Downstairs Apple TV is wired through Et15 and the Aqara Hub M3 through Et16. Both ports are labelled access ports in VLAN 30, negotiate at 100 Mbps, learn only their expected MAC addresses and received IoT DHCP leases after a controlled link cycle.
- The existing UniFi IoT SSID is assigned to the third-party-gateway IoT network using tagged VLAN 30. A temporary test SSID first validated wireless DHCP, DNS, Internet access and firewall isolation, then was removed. Final dnsmasq and ARP checks showed 23 leased IoT clients active on `vlan0.30`; Hue, Lutron, AirPlay/Cast discovery and vendor-app control all passed.
- Proxmox LXC 100 (`docker`) is an unprivileged Debian container at `192.168.20.20/24` on Servers VLAN 20. It runs Homepage, Portainer, the primary Pi-hole, Tailscale, Beszel and the Beszel agent. Homepage is published internally on TCP 3000 and is available as `http://home.internal:3000`.
- OPNsense dnsmasq owns the `home.internal` host record and listens for DNS on port 53053. Unbound remains the client-facing resolver on port 53 and conditionally forwards the `internal` domain to dnsmasq at 127.0.0.1:53053. Both local-LAN and remote Tailscale resolution were validated.
- The secondary Pi-hole at `192.168.20.40` uses the Servers gateway `192.168.20.1` for upstream DNS and conditional forwarding of `internal`; the former Trusted-gateway destination `192.168.1.1` is no longer reachable from VLAN 20 by design.
- Tailscale runs directly in Docker LXC 100 as the `homelab-gateway` subnet router. It advertises Trusted `192.168.1.0/24`, Servers `192.168.20.0/24` and Management `192.168.50.0/24`; IoT, Guest, Cameras and Lab are not advertised. IPv4 forwarding is enabled and the LXC has access to `/dev/net/tun`.
- Tailscale split DNS sends only the `internal` namespace to OPNsense at `192.168.1.1`. The broad default tailnet allow rule was replaced with an identity-specific grant permitting the administrator account to reach the Trusted, Servers and Management routes on all protocols. A host-scoped OPNsense rule permits the subnet router at `192.168.20.20` to reach Trusted because routed clients are source-NATed behind it. Remote Homepage, Home Assistant, Frigate and Proxmox access passed with the client off home Wi-Fi. SSH uses the existing host services through the subnet route; native Tailscale SSH is not enabled. No inbound WAN port-forward or public service exposure was added.
- Homepage includes Network, Smart Home, Security & Operations, AI & Automation, Virtualization, Storage, Media, Media Automation, Application Management, External Services, SSH Access and Security & Surveillance groups. The operations group contains Beszel, Code Server, Authentik, Dockge, Dozzle and the reverse proxy; Forgejo remains under Application Management. Hermes and Ollama are represented as isolated pilots without dead direct links. Primary and Secondary Pi-hole tiles, Home Assistant, Beszel and Frigate web/SSH tiles are operational. Beszel reports monitored-system health through a dedicated file-backed Homepage widget credential. The dashboard and its internal management targets remain intended for LAN or Tailscale access only.
- The NUT server is the independent management-VLAN host at `192.168.50.25`, MAC `00:23:24:55:b1:1a`, directly connected to Arista Et31. It is not downstream of the AP Switch; Et33 is the AP Switch uplink.
- Forgejo runs in unprivileged LXC 108 at `192.168.20.30`. Its complete repository, branches and release tag were synchronized with GitHub, SSH clone/push was validated, its archive is included in the nightly guest mirror, and an isolated LXC 978 restore verified the service, SQLite database and HomeLab repository before cleanup.
- Frigate VM 102 runs Debian 13.6 at `192.168.20.10` on VLAN 20. Its Reolink Duo 2V PoE camera uses `192.168.60.10` on VLAN 60. OPNsense permits only TCP 80, 554 and 8000 from Frigate to the camera; TCP 9000 remains blocked.
- Frigate VM 102 has the Coral Edge TPU passed through as a dedicated PCIe device. The guest loads the `gasket` and `apex` modules, exposes `/dev/apex_0` to the Frigate container and reports approximately 10 ms inference. CPU HEVC decoding remains separate from Coral object-detection inference.
- Frigate records to `192.168.20.40:/mnt/Media/Surveillance/Frigate` over NFSv4. A systemd-owned Compose service waits for the real NFS mount before starting, and a full reboot test confirmed a healthy container plus fresh recording segments after the TrueNAS migration.
- The primary Pi-hole 2026.05.0 runs in Docker LXC 100 at `192.168.20.20`; the secondary Pi-hole 2026.07.2 runs as a TrueNAS App at `192.168.20.40`. Both publish TCP/UDP 53, use OPNsense as their upstream path, resolve `home.internal` to `192.168.20.20` and return `0.0.0.0` for the blocked test domain.
- OPNsense Dnsmasq advertises both Pi-holes through an untagged DHCPv4 option 6 on every configured range. A source-network alias covering VLANs 20 through 70 and an early floating rule permit only TCP/UDP 53 to the resolver alias while preserving the existing private-network blocks. LAN, Servers, IoT and Guest paths were directly validated. Encrypted/private client DNS remains outside this DHCP-based guarantee.
- Home Assistant OS 18.2 runs as Proxmox VM 103 at reserved address `192.168.20.11` on VLAN 20 with 2 vCPU, 4 GB RAM and 32 GB storage. `http://home-assistant.home.internal` is operational on TCP 80 and encrypted native plus mirrored VM backups exist off-host. A host-specific rule permits only Home Assistant to initiate TCP/UDP access to IoT VLAN 30 before the general Servers RFC1918 block. Philips Hue, Lutron Caséta, Aqara Matter and Sonos are integrated. The Hue Hall motion-to-Lutron Laundry pilot is complete and now uses a scene, script and five-minute timer helper with a validated timer-finished light-off path. HACS is installed without an elective community repository; media and fringe-vendor integrations remain deliberately incremental.
- VLAN 70 was fully validated with disposable LXC 970: DHCP, Pi-hole DNS, blocked-domain response and Internet access passed, while non-DNS access to internal services remained blocked. The OPNsense VLAN parent was corrected from inactive `igb0` to trunk `ix0`; the test container was then purged.
- Hermes Agent now runs in unprivileged LXC 104 at `192.168.70.10`; Ollama runs in Ubuntu VM 105 at `192.168.70.11` and serves its OpenAI-compatible API on TCP 11434. Hermes successfully uses the local `qwen3-64k:8b` model profile with a 65,536-token context window. This remains a CPU-only pilot: 14 GB was the first stable tested Ollama allocation, response generation is slow, guest archives are mirrored and restore-tested within the encrypted `automated/proxmox-guests` off-site selection, and aggregate Proxmox memory allocation still requires review.

## Resolved incidents

### WAN dropouts

OPNsense ix1 previously recorded repeated carrier-loss events, normally recovering after about 29 seconds. Driver counters showed local faults, CRC errors, and link interrupts without watchdog resets or software drops. Replacing the temporary Cat6a WAN cable stopped the recurring events during the initial observation period.

The replacement cable remained stable for more than 48 hours after permanent installation. A final controlled test on 2026-08-07 local time (2026-08-08 UTC) transferred approximately 3.576 GB down and 1.707 GB up in 12.98 seconds. It measured 2.646 Gbps down, 1.311 Gbps up and high responsiveness. Concurrent 60-packet pings to OPNsense LAN and 1.1.1.1 both completed with 0% loss.

Final stress-test comparison:

| Counter | Before load | After load | Change |
|---|---:|---:|---:|
| ix1 link-down events | 93 | 93 | 0 |
| ix1 local faults | 95 | 95 | 0 |
| ix1 remote faults | 0 | 0 | 0 |
| ix1 CRC errors | 9 | 9 | 0 |
| ix1 link interrupts | 191 | 191 | 0 |
| ix1 RX missed packets | 88,257 | 272,591 | +184,334 |

Mbuf and jumbo-cluster denied/delayed counters remained zero. The RX-missed increase occurred only under the multi-gigabit stress load while every physical-link counter remained unchanged and both ping streams had zero loss. This identified receive-FIFO/queue pressure rather than a cable fault.

The X553 WAN interface had four reasonably balanced receive queues, full Ethernet flow control, no per-queue discards, no NetISR queue drops and no IDS/IPS process. Each queue initially had 2047 available credits, confirming a 2048-descriptor ring. The loader tunable `dev.ix.1.iflib.override_nrxds=4096` was applied, OPNsense was rebooted, and all four queues then reported 4095 available credits.

The repeated controlled test reached 2.835 Gbps down and 789 Mbps up with high responsiveness. It delivered 6,457,564 additional good packets while RX-missed increased by only 2,690, approximately 0.042%. That is a 98.5% reduction from the previous 184,334 missed packets despite higher download throughput. XOFF transmitted increased by 65, both 60-packet ping streams had 0% loss, all four queue-discard counters remained zero, and mbuf denied/delayed counters remained zero. Local faults stayed at the post-reboot baseline of 1 and CRC errors stayed at 0.

Keep the 4096-descriptor setting. RSS remains disabled because the receive queues are already balanced and the ring increase resolved the practical problem without a broader networking-stack change. Reconsider RSS only if missed-packet growth becomes material during normal operation or produces measurable application impact.

The pre-tuning physical baseline remains historical evidence: 93 link-down events, 95 local faults, 0 remote faults, 9 CRC errors and 191 link interrupts. The tuning reboot reset the live hardware counters, so future checks should compare post-reboot deltas rather than raw values from before the reboot. For cable health, link-down, local/remote-fault, CRC and link-interrupt changes remain decisive; interpret RX-missed deltas in relation to traffic volume.

### ASUS ARP interference

The old ASUS Wi-Fi/mesh system caused extensive ARP ownership changes. Locally administered MAC b6:fc:e7:34:d9:e4 claimed addresses belonging to numerous LAN clients. After the ASUS devices were removed, the MAC disappeared and affected clients returned to their legitimate addresses.

Do not reconnect the ASUS equipment without a factory reset and a deliberate configuration plan.

## Baseline commands

### OPNsense WAN

```sh
date
uptime
ifconfig ix1
netstat -I ix1 -bdn
sysctl dev.ix.1.iflib.override_nrxds
sysctl dev.ix.1.iflib | grep credits
dmesg | grep -c 'ix1: link state changed to DOWN'
sysctl dev.ix.1.mac_stats.local_faults
sysctl dev.ix.1.mac_stats.remote_faults
sysctl dev.ix.1.mac_stats.crc_errs
sysctl dev.ix.1.mac_stats.good_pkts_rcvd
sysctl dev.ix.1.mac_stats.rx_missed_packets
sysctl dev.ix.1.mac_stats.xoff_txd
sysctl dev.ix.1.link_irq
sysctl dev.ix.1 | grep rx_discarded
netstat -m | egrep 'requests for mbufs denied|requests for mbufs delayed|requests for jumbo clusters'
```

### Arista active links

```text
show interfaces status
show interfaces Ethernet3,8,9,11,17,24,33,40,45,46,48 counters errors
show interfaces Ethernet3,8,9,11,17,24,33,40,45,46,48 counters queue
show spanning-tree vlan 10
show environment all
```

### TrueNAS LAN bond

```sh
ip -br addr show bond0
ip -br link show master bond0
cat /proc/net/bonding/bond0
ip route show default
```

## VLAN plan and implementation status

This plan uses memorable VLAN IDs and distinct /24 networks. Existing VLAN 10 can remain the trusted LAN initially to reduce migration risk.

| VLAN | Name | Proposed subnet | Intended devices |
|---:|---|---|---|
| 10 | Trusted | 192.168.1.0/24 initially | Personal computers and phones |
| 20 | Servers | 192.168.20.0/24 | Frigate and future hosted services; implemented |
| 30 | IoT | 192.168.30.0/24 | Hue, Lutron, TVs and other smart devices |
| 40 | Guest | 192.168.40.0/24 | Guest Wi-Fi clients; Internet only |
| 50 | Management | 192.168.50.0/24 | Network-management infrastructure; routed baseline implemented |
| 60 | Cameras | 192.168.60.0/24 | Reolink camera; implemented |
| 70 | Lab | 192.168.70.0/24 | Isolated experimental Proxmox workloads; infrastructure implemented |

### Implemented: Guest VLAN 40

- OPNsense interface: `vlan0.40`, parent `ix0`, 192.168.40.1/24.
- DHCP: dnsmasq range 192.168.40.100-192.168.40.199; router and DNS supplied automatically as 192.168.40.1.
- Firewall order: allow Guest DNS to the Guest address; allow Guest NTP to the Guest address; block Guest to This Firewall; block Guest to the `RFC1918_Networks` alias; allow remaining Guest IPv4 traffic to the Internet.
- `RFC1918_Networks`: 10.0.0.0/8, 172.16.0.0/12 and 192.168.0.0/16.
- Arista: VLAN 40 named `Guest`; Et40 trunk native VLAN 10 with VLANs 10,20,30,40,50,60,70 allowed; Et1 temporary access test port.
- Wired validation client: `Jasons-Mac`, interface `en7`, leased 192.168.40.198 with gateway 192.168.40.1.
- Validation results: 1.1.1.1 reachable with 0% loss at approximately 6.1 ms; DNS resolution succeeded; 192.168.1.1 was blocked; HTTPS access to 192.168.40.1 timed out as intended.
- UniFi: third-party-gateway network `Guest` uses VLAN ID 40; tagged VLAN 40 is carried over Arista Et33 to the UniFi uplink; the Guest SSID uses the Guest network with wireless client isolation enabled.
- Wireless validation: DHCP, Internet and DNS succeeded; access to internal management addresses remained blocked as intended.
- Post-change OPNsense, UniFi and Arista recovery copies were completed. Peer-to-peer wireless client isolation can be explicitly verified later using two simultaneous Guest clients.

### Implemented infrastructure: IoT VLAN 30

- OPNsense interface: `vlan0.30`, parent `ix0`, 192.168.30.1/24.
- DHCP: dnsmasq range 192.168.30.100-192.168.30.199, 86,400-second leases, domain `iot.internal`; router and DNS supplied automatically as 192.168.30.1.
- Firewall order: allow IoT DNS to the IoT address; allow IoT NTP to the IoT address; block IoT to This Firewall; block IoT to `RFC1918_Networks`; allow remaining IoT IPv4 traffic to the Internet.
- Arista: VLAN 30 named `IoT`; Et40 is a trunk with native VLAN 10 and VLANs 10,20,30,40,50,60,70 allowed; Et33 is a trunk with native VLAN 10 and VLANs 10,30,40,50,60 allowed; Et2 is the temporary access test port. The validated running configuration was saved to startup-config.
- Wired validation succeeded: DHCP, default routing, DNS and Internet access worked; trusted-LAN and OPNsense-management access were blocked as intended.
- Production migration: Philips Hue on Et46 moved to 192.168.30.164 and Lutron on Et45 moved to 192.168.30.102. Both vendor apps and Apple Home passed post-migration testing. Selective mDNS repeating is enabled only between LAN and IoT.
- UniFi Wi-Fi migration: a third-party-gateway IoT network with VLAN ID 30 was added, Et33 was enabled for tagged VLAN 30, a temporary SSID passed validation, and the existing production IoT SSID was moved to that network without changing its credentials. Twenty-three DHCP leases were confirmed on VLAN 30, and Hue, Lutron, AirPlay/Cast discovery and representative vendor apps remained functional. The temporary SSID was then removed.

### Baseline policy

- Trusted may initiate connections to Servers and selected IoT services.
- Servers should receive only explicitly required inbound connections.
- IoT should be blocked from initiating connections to Trusted, Servers and Management.
- Guest should reach the Internet only and be isolated from all internal networks.
- Management should be reachable only from selected administrator devices.
- Cameras should reach the NVR and required time/DNS services only; Internet access should be denied unless necessary.
- mDNS reflection should be enabled only between the specific networks that require discovery, such as Trusted and selected IoT services.

## Migration guardrails

1. Treat the permanently installed WAN cabling as stable; reopen the physical-link investigation only if link-down, local/remote-fault, CRC or link-interrupt counters increase unexpectedly or dropout symptoms recur.
2. Download and verify backups before every change window.
3. Add VLANs without moving existing devices.
4. Test one non-critical wired client on each new VLAN.
5. Add firewall rules before migrating dependent devices.
6. Move one device category at a time, beginning with Guest or a test IoT client.
7. Keep local console access to OPNsense and Arista during management-network changes.
8. Record every port, VLAN, DHCP scope, reservation and firewall exception.

## Pending decisions

- Whether future TrueNAS redundancy should span a separate NIC/controller or switch. The current bond protects against a cable or individual port failure, but both members use the same dual-port adapter and Arista switch.
- Whether the existing 192.168.1.0/24 network will remain VLAN 10 during migration or be renumbered.
- The recommended initial approach is to retain 192.168.1.0/24 as native/untagged VLAN 10 so OPNsense and Arista management remain reachable while tagged networks are added.
- UniFi Port 9 requires no initial profile change: future tagged VLANs are already permitted. On the Arista, the same untagged traffic is locally classified as VLAN 10.
- Which trusted devices require cross-VLAN discovery or control of Hue, Lutron and Apple TV.
- Whether cameras need a dedicated network.
- Final management access devices and recovery procedure.

## Phase 11 Known-Good Checkpoint — 2026-08-20

- Proxmox currently exposes 31 GiB usable memory from two installed 16 GB SK hynix ECC RDIMMs in DIMM1 and DIMM3, configured at 1866 MT/s. The completed 24 GB two-pass `memtester` run reported no errors. The remaining RAM and E5-2698 v4 maintenance stage is pending.
- Production management endpoints are Arista `192.168.50.2`, Proxmox `192.168.50.10`, UniFi controller `192.168.50.21`, Hall AP `192.168.50.31` and Office AP `192.168.50.141`. The AP Switch is numbered `192.168.50.26` but requires the documented direct VLAN 1 recovery path because its management plane is not actually reachable on VLAN 50.
- Server endpoints include Frigate `192.168.20.10`, Home Assistant `192.168.20.11`, Docker and primary Pi-hole `192.168.20.20`, TrueNAS and secondary Pi-hole `192.168.20.40`, primary Synology `192.168.20.41` and Backup Synology `192.168.20.42`.
- Hermes LXC 104 at `192.168.70.10` and Ollama VM 105 at `192.168.70.11` remain isolated Lab VLAN 70 pilots. Both are included in Proxmox guest backups, mirrored to the Backup Synology, protected through the encrypted `automated/proxmox-guests` off-site selection and have passed isolated restore validation.
- Jellyfin, Immich, Plex, Seerr, Calibre, Audiobookshelf, Sonarr, Radarr, Lidarr and Prowlarr were directly reachable during reconciliation.
- No temporary VM/LXC guests remain. Former addresses and VM 903 references retained in the repository are explicitly historical migration or restore-test evidence.
- HomeLab Doctor completed with 44 passes, no warnings and no failures. Configuration drift was clear, six operational TLS certificates were healthy, Git was clean and the daily failure-only reporting LaunchAgent had a successful exit status.
