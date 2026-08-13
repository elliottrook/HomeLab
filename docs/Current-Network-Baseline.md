# Home Network Baseline

Baseline date: 2026-08-09
Status: The WAN path remains stable. Routed interfaces, DHCP scopes and baseline firewall policy are deployed for VLANs 20, 30, 40, 50, 60 and 70 while VLAN 10 remains the native Trusted network. IoT and Guest are in production. Frigate VM 102 is operational on Servers VLAN 20 and records the isolated Reolink camera on Cameras VLAN 60 to TrueNAS NFS. Homepage and identity-restricted Tailscale access remain operational without inbound WAN ports.

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

Store copies off the network appliances and treat them as sensitive configuration data.

## Current topology

```text
TELUS modem 10Gb RJ45
  |
  | Cat6a via 10Gtek RJ45 SFP+ transceiver
  |
OPNsense ix1 (WAN, 10Gb)
OPNsense ix0 (LAN, 10Gb)
  |
Arista Et40
  |
Arista DCS-7050TX-64-R
  +-- Et1  Guest-VLAN40-Test (access VLAN 40)
  +-- Et2  IoT-VLAN30-Test (access VLAN 30)
  +-- Et3  unused
  +-- Et4  Proxmox (trunk; native VLAN 10, tagged VLANs 20,70)
  +-- Et7  Suspect-Link-Test-Only (disconnected)
  +-- Et8  Mac-Studio
  +-- Et9  TrueNAS-Primary
  +-- Et11 LivingRoom-AppleTV
  +-- Et17 TrueNAS-Failover (bond standby)
  +-- Et23 Synology-NIC-A
  +-- Et33 UniFi-PoE-Uplink (native VLAN 10, tagged VLANs 30,40,50,60)
  +-- Et40 OPNsense-LAN (native VLAN 10, tagged VLANs 20,30,40,50,60,70)
  +-- Et43 Old-ASUS-Disconnected
  +-- Et45 Lutron-Hub
  +-- Et46 Philips-Hue
  +-- Et48 Synology-NIC-B
```

Et43, formerly connected to the old ASUS Wi-Fi/mesh system, is disconnected. Et7 remains unused after earlier Mac Studio physical-link instability. The temporary switch used during WAN-cable testing has been removed; Proxmox and the Mac Studio now connect directly to the Arista.

The Proxmox path was traced to Et4 and configured as a trunk retaining native
VLAN 10 while carrying VLANs 20 and 70. Stale Synology descriptions were
removed from Et20 and Et21.

## Device and address inventory

| Address | Device | MAC | Arista path |
|---|---|---|---|
| 192.168.1.1 | OPNsense LAN | e8:b5:d0:e1:8e:4f | Et40 |
| 192.168.1.2 | Arista management SVI | 44:4c:a8:1f:3e:c5 | Vlan10 |
| 192.168.1.10 | Proxmox | 6c:92:bf:27:89:a3 | Et4 |
| 192.168.1.20 | Docker LXC / Homepage / Pi-hole / Tailscale subnet router | bc:24:11:43:71:67 | Et4 via Proxmox |
| 192.168.1.21 | UniFi controller | bc:24:11:b6:de:53 | Et4 via Proxmox |
| 192.168.1.40 | TrueNAS `bond0` | 6c:92:bf:67:fb:bc | Et9 primary / Et17 failover |
| 192.168.1.41 | Synology | 00:11:32:ca:e5:e6 | Et23 |
| 192.168.1.42 | Synology | 00:11:32:c8:06:c5 | Et48 |
| 192.168.30.102 | Lutron | ec:24:b8:8e:d4:10 | Et45, access VLAN 30 |
| 192.168.30.164 | Philips Hue | 00:17:88:22:42:e5 | Et46, access VLAN 30 |
| 192.168.20.10 | Frigate VM 102 | bc:24:11:f5:09:a3 | Et4 via Proxmox, tagged VLAN 20 |
| 192.168.20.11 | Home Assistant OS VM 103 | bc:24:11:08:16:a3 | Et4 via Proxmox, tagged VLAN 20 |
| 192.168.60.10 | Reolink Duo 2V PoE | ec:71:db:80:49:6e | UniFi PoE port 3, VLAN 60 |
| 192.168.1.206 | Mac Studio | d0:11:e5:9e:c4:76 | Et8 |
| 192.168.1.211 | Downstream UniFi client | d8:c8:0c:bb:52:a4 | Et33 |
| 192.168.1.228 | Living-room Apple TV | c0:95:6d:81:11:5d | Et11 |

## Known-good health findings

- All connected Arista ports report zero FCS, alignment, symbol, receive, runt, giant, and transmit errors.
- Queue-drop counters remained unchanged between observations; existing totals are historical.
- Et33 (UniFi uplink) and Et40 (OPNsense LAN) have zero queue drops.
- Arista is the MSTP root for VLAN 10. All connected ports are forwarding; Et33 is the expected spanning-tree boundary/uplink.
- Switch temperatures and cooling are healthy. Highest observed PHY temperature was 51 C.
- PSU2 is online and supplies approximately 160 W. PSU1 is intentionally unpowered; redundancy is knowingly unavailable.
- OPNsense ix0 and ix1 are active at 10Gbps with correct LAN/WAN addressing and routing. The permanent ix1 WAN path completed its final stress test without a link flap, physical fault, CRC error, link interrupt, packet loss, or mbuf allocation failure.
- The temporary switch has been removed. Proxmox is directly connected on Arista Et4 as a trunk with native VLAN 10 and tagged VLANs 20 and 70. The Mac Studio is directly connected on Et8 as an access port in VLAN 10.
- TrueNAS 25.10.5 uses `bond0` in active-backup mode at 192.168.1.40/24. Member `enp5s0f0` (MAC 6c:92:bf:67:fb:bc, Arista Et9) is the preferred primary and `enp5s0f1` (permanent MAC 6c:92:bf:67:fb:bd, Arista Et17) is the standby. Both links operate at 10 Gbps, MII monitoring runs every 100 ms, and `primary_reselect` is `always`. A controlled Et9 shutdown moved service to Et17 with one lost ping; restoring Et9 automatically returned service to the primary. Both switch ports remain independent access ports in VLAN 10 with PortFast; no port-channel or LACP is configured.
- Arista management is provided by Vlan10 at 192.168.1.2/24. Management1 is unassigned/down, and no `ip route` is currently configured.
- UniFi Network Server version 10.5.67 uses third-party-gateway networks named Default, IoT (VLAN 30) and Guest (VLAN 40). UniFi switch Port 9 is the 10GbE uplink to Arista Et33; its native network is Default (UniFi VLAN 1/untagged), tagged VLAN management is Allow All, auto-negotiation is enabled, and STP is enabled. Local UniFi OS management for this installation is exposed at `https://192.168.1.21:11443`.
- OPNsense Guest interface `vlan0.40` is active on parent `ix0` at 192.168.40.1/24. Dnsmasq is the active DHCP service and serves 192.168.40.100-192.168.40.199 with 86,400-second leases. Kea was disabled after its logs confirmed it could not bind UDP port 67 because dnsmasq already owned the port.
- Arista Et40 is a trunk with native VLAN 10 and VLANs 10,20,30,40,50,60,70 allowed. Et33 is a trunk with native VLAN 10 and VLANs 10,30,40,50,60 allowed. Temporary test ports Et1 and Et2 are access ports in VLANs 40 and 30 respectively.
- OPNsense IoT interface `vlan0.30` is active on parent `ix0` at 192.168.30.1/24. Dnsmasq serves 192.168.30.100-192.168.30.199 with 86,400-second leases and the `iot.internal` DHCP domain. The validated rule order allows IoT DNS and NTP to the interface address, blocks access to the firewall and RFC1918 networks, and permits remaining IPv4 Internet traffic.
- The OPNsense `os-mdns-repeater` plugin relays multicast DNS only between `ix0` (LAN) and `vlan0.30` (IoT). The running process is `/usr/local/bin/mdns-repeater ... vlan0.30 ix0`; Guest and WAN are excluded.
- Philips Hue on Et46 uses 192.168.30.164 and Lutron on Et45 uses 192.168.30.102. Both vendor apps and Apple Home remained functional after migration to VLAN 30.
- The existing UniFi IoT SSID is assigned to the third-party-gateway IoT network using tagged VLAN 30. A temporary test SSID first validated wireless DHCP, DNS, Internet access and firewall isolation, then was removed. Final dnsmasq and ARP checks showed 23 leased IoT clients active on `vlan0.30`; Hue, Lutron, AirPlay/Cast discovery and vendor-app control all passed.
- Proxmox LXC 100 (`docker`) is an unprivileged Debian container at 192.168.1.20/24. It runs Portainer and Homepage. Homepage is published internally on TCP 3000 and is available as `http://home.internal:3000`.
- OPNsense dnsmasq owns the `home.internal` host record and listens for DNS on port 53053. Unbound remains the client-facing resolver on port 53 and conditionally forwards the `internal` domain to dnsmasq at 127.0.0.1:53053. Both local-LAN and remote Tailscale resolution were validated.
- Tailscale runs directly in Docker LXC 100 as the `homelab-gateway` subnet router. It advertises only the trusted 192.168.1.0/24 network; IoT 192.168.30.0/24 and Guest 192.168.40.0/24 are not advertised. IPv4 forwarding is enabled and the LXC has access to `/dev/net/tun`.
- Tailscale split DNS sends only the `internal` namespace to OPNsense at 192.168.1.1. The broad default tailnet allow rule was replaced with an identity-specific grant permitting the administrator account to reach 192.168.1.0/24 on all protocols. Remote Homepage, management-tile and OpenSSH access passed with the client off the home Wi-Fi network. SSH uses the existing host services through the subnet route; native Tailscale SSH is not enabled. No inbound WAN port-forward or public service exposure was added.
- Homepage includes network, smart-home, monitoring-and-maintenance, virtualization, storage, media, media-automation, application-management, external-service, SSH-access and surveillance groups. Primary and Secondary Pi-hole tiles, Home Assistant, Beszel and Frigate web/SSH tiles are operational. Beszel reports Docker, Proxmox and Frigate health through a dedicated file-backed Homepage widget credential. The dashboard and its internal management targets remain intended for LAN or Tailscale access only.
- Frigate VM 102 runs Debian 13.6 at `192.168.20.10` on VLAN 20. Its Reolink Duo 2V PoE camera uses `192.168.60.10` on VLAN 60. OPNsense permits only TCP 80, 554 and 8000 from Frigate to the camera; TCP 9000 remains blocked.
- Frigate records to `192.168.1.40:/mnt/Media/Surveillance/Frigate` over NFSv4. A systemd-owned Compose service waits for the real NFS mount before starting, and a full reboot test confirmed a healthy container plus fresh recording segments.
- The primary Pi-hole 2026.05.0 runs in Docker LXC 100 at `192.168.1.20`; the secondary Pi-hole 2026.07.2 runs as a TrueNAS App at `192.168.1.40`. Both publish TCP/UDP 53, use OPNsense as their upstream path, resolve `home.internal` to `192.168.1.20` and return `0.0.0.0` for the blocked test domain.
- OPNsense Dnsmasq advertises both Pi-holes through an untagged DHCPv4 option 6 on every configured range. A source-network alias covering VLANs 20 through 70 and an early floating rule permit only TCP/UDP 53 to the resolver alias while preserving the existing private-network blocks. LAN, Servers, IoT and Guest paths were directly validated. Encrypted/private client DNS remains outside this DHCP-based guarantee.
- Home Assistant OS 18.2 runs as Proxmox VM 103 at reserved address `192.168.20.11` on VLAN 20 with 2 vCPU, 4 GB RAM and 32 GB storage. `http://home-assistant.home.internal` is operational on TCP 80 and the initial full backup exists. A host-specific rule permits only Home Assistant to initiate TCP/UDP access to IoT VLAN 30 before the general Servers RFC1918 block. Philips Hue at reserved address `192.168.30.164` and Lutron Caséta at reserved address `192.168.30.102` are integrated; Lutron device control passed. The next pilot step is restoring an unreachable Hue motion sensor and using it to trigger the Lutron `Laundry Main lights`.
- VLAN 70 was fully validated with disposable LXC 970: DHCP, Pi-hole DNS, blocked-domain response and Internet access passed, while non-DNS access to internal services remained blocked. The OPNsense VLAN parent was corrected from inactive `igb0` to trunk `ix0`; the test container was then purged.

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
show interfaces Ethernet3,8,9,11,17,23,33,40,45,46,48 counters errors
show interfaces Ethernet3,8,9,11,17,23,33,40,45,46,48 counters queue
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
