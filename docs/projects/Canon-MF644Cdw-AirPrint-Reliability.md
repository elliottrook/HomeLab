# Canon MF644Cdw AirPrint reliability

> Status: Complete — deployed and validated
>
> Owner: Jason
>
> Started: 2026-10-19
>
> Completed: 2026-10-19
>
> Authorization: Stream M — printer and network changes separately approved
>
> Speech impact: none

## Purpose and desired outcome

Keep the Canon MF644Cdw discoverable to Apple clients through Bonjour/AirPrint
while retaining the printer's normal energy-saving sleep behaviour. Printing
must continue to use IPP directly to the printer; the Mac mini publishes only
the discovery record and does not proxy print jobs. Keep both Canon printers
on stable addresses so saved print queues and recovery paths remain valid.

## Current state and evidence

- Printer: Canon MF644Cdw, Ethernet/Wi-Fi MAC `10:98:C3:DE:85:91`, IPv4
  `192.168.1.183`, original DHCP hostname `Canoncf5f20`.
- Printer AirPrint, IPP and IPv4 mDNS were initially enabled; Wireless LAN
  Power Save was off; Auto Sleep was one minute; main-controller firmware was
  `14.03`.
- The prior mDNS service name was corrupted by accumulated collision suffixes.
  It was changed, with approval, to `Canon MF644Cdw Office` and the printer was
  restarted.
- Immediately after restart the printer advertised and resolved normally.
  Once its Remote UI reported Sleep mode, fresh mDNS discovery stopped, while
  HTTP, SNMP and IPP at `192.168.1.183:631` remained reachable. A Canon MF210 on
  the same LAN continued to advertise, excluding a general LAN multicast fault.
- The evidence substantiates a printer firmware/sleep interaction: ordinary
  sleep suppresses this device's Bonjour responder even though the network and
  print service remain available. Wireless LAN Power Save is not the cause.
- A permanently active proxy beside native mDNS produced two discovery entries
  whenever the printer woke, because the printer collision-renamed its native
  instance to `Canon MF644Cdw Office (de:85:91)`. IPv4 mDNS is now disabled on
  the MF644 only; AirPrint and IPP remain enabled, making the Mac proxy the sole
  Bonjour authority while clients still print directly to the printer.
- The Canon MF210 `Hall` printer, MAC `28:C2:DD:F1:B2:E7`, answers fresh mDNS
  service, SRV, TXT and host queries directly at `192.168.1.205`; it does not
  reproduce the MF644 sleep-time failure. Its IPP port also remains reachable.

Official Canon references:

- [Using AirPrint](https://oip.manual.canon/USRMA-3547-zz-SSM-740-enUS/contents/devu-mobile-aap.html)
- [Wireless LAN power saving](https://oip.manual.canon/USRMA-3547-zz-SSM-740-enUS/contents/devu-setup-nw-wlesslan-wlessrouter.html)
- [Timer and energy settings](https://oip.manual.canon/USRMA-3582-zz-SSM-740-enUV/contents/devu-set_menu_list_1-pref-time_energy.html)
- [Network settings](https://oip.manual.canon/USRMA-3547-zz-SSM-740-enUS/contents/devu-set_menu_list_1-pref-nw.html)

## Scope and exclusions

In scope:

- preserve `192.168.1.183` for the printer in OPNsense Dnsmasq;
- preserve `192.168.1.205` for the MF210 `Hall` printer in OPNsense Dnsmasq;
- add one driverless macOS queue for the MF210 using direct IPP Everywhere;
- publish one static `_ipp._tcp,_universal` Bonjour record from the always-awake
  Mac mini;
- disable only the MF644's native IPv4 mDNS advertisement to prevent duplicate
  discovery entries while retaining AirPrint and IPP;
- retain the printer's existing AirPrint capabilities and one-minute sleep;
- document validation, recovery and rollback.

Excluded: firmware update, disabling sleep, firewall/VLAN changes, public
exposure, credential changes, scan-protocol changes, changing the existing
MF644 queue/default, NetBox device creation, and a Bonjour proxy or
printer-setting change for the MF210.

## Authority model

| Fact | Authority |
|---|---|
| Printer MAC, address and AirPrint capabilities | Live printer and OPNsense reservation |
| Reserved address | OPNsense Dnsmasq configuration |
| Synthetic Bonjour advertisement | This repository's LaunchAgent plist |
| Runtime state | macOS `launchd`, `dns-sd` and the agent logs |
| Diagnosis and recovery procedure | This project document |

## Architecture and data flow

```text
Apple client --mDNS query--> Mac mini (192.168.1.206)
Apple client <--Bonjour record-- Canon MF644Cdw Office
Apple client --IPP :631----------------> printer (192.168.1.183)
```

The service target is deliberately `canon-mf644-proxy.local`, not the
printer's `Canoncf5f20.local`. Both names resolve to the printer address, but a
distinct target prevents an mDNS hostname collision whenever the printer wakes
and republishes its native record.

## Privacy and security design

The workaround is LAN-only multicast discovery. It adds no Internet ingress,
credential, firewall permission, stored document, telemetry or third-party
dependency. The Mac mini publishes device capabilities and a private address;
print payloads go directly from client to printer.

## Pre-start risk assessment

| Risk | Control and residual risk |
|---|---|
| Address changes make the record stale | Exact MAC/IP DHCP reservation; DNS and port validation |
| Duplicate Bonjour host/service names | Separate proxy target hostname; live collision test |
| Mac mini unavailable or logged-out session absent | Mac mini has system sleep disabled; native printer discovery may still work while awake; direct-IP printing remains available |
| Incorrect TXT data affects client choices | Values copied from the printer's own working advertisement and resolved before installation |
| Dnsmasq restart briefly interrupts DHCP/DNS | Configuration checkpoint, bounded restart and immediate health/DNS validation |
| macOS cannot locate a vendor MF210 driver | Use the printer's verified IPP Everywhere/AirPrint capability; no downloaded driver or test page required |

No destructive or irreversible action is required. The OPNsense recovery
checkpoints are `/conf/backup/config-canon-airprint-20261019-1642.xml` for the
MF644 work and
`/conf/backup/config-canon-mf210-reservation-20261019-1655.xml` for the MF210
reservation. Abort on Dnsmasq failure, address mismatch, hostname collision or
loss of IPP reachability. No synthetic user data is needed.

## Persistence plan

The candidate plist is tracked at
`configs/launchagents/com.jason.homelab.canon-mf644-airprint.plist` and installed
at `~/Library/LaunchAgents/com.jason.homelab.canon-mf644-airprint.plist`.
`RunAtLoad` and `KeepAlive` make the publisher recover from login and process
failure. Logs live under `~/lab/monitoring-state/reports/`.

Resume by checking the OPNsense reservation, running `launchctl print
gui/$(id -u)/com.jason.homelab.canon-mf644-airprint`, and resolving the service
with `dns-sd -L 'Canon MF644Cdw Office' _ipp._tcp local.`.

## Milestones

- [x] Reproduce the failure and distinguish mDNS discovery from IPP reachability.
- [x] Repair the corrupt native AirPrint/mDNS service name.
- [x] Create and validate the OPNsense DHCP reservation and checkpoint.
- [x] Prove a collision-safe static Bonjour record using a distinct target host.
- [x] Install and load the persistent LaunchAgent.
- [x] Validate discovery and direct IPP reachability after the printer's
  one-minute sleep interval.
- [x] Verify the MF210's native Bonjour behaviour and reserve its current address.
- [x] Add and validate a driverless MF210 queue on the Mac mini.
- [x] Complete documentation and close-out review.

## Validation and evaluation

Required graduation evidence:

1. `plutil` accepts the tracked and installed property lists.
2. `launchctl` reports the job running.
3. `_ipp._tcp,_universal` browsing returns `Canon MF644Cdw Office`.
4. service resolution returns `canon-mf644-proxy.local:631` with the expected
   IPP/AirPrint TXT fields.
5. the proxy hostname resolves to `192.168.1.183`.
6. TCP 631 is reachable while the printer UI reports sleep.
7. publisher logs contain no `Name in use` collision.
8. discovery shows one MF644 instance after the retired native record expires.
9. `Canon_MF210_Hall` is idle/enabled, uses the reserved direct IPP URI and
   exposes the printer's media and quality options without a vendor driver.

## Observability and maintenance

The job's stdout and stderr logs are retained in the existing monitoring-state
report directory. A dedicated Doctor/Beszel alert would be disproportionate:
the job runs on an already monitored Mac, direct-IP printing is the safe
fallback, and discovery failure is immediately visible to the user. Recheck
the reservation and advertisement after printer replacement, address changes
or macOS upgrades.

## Backup, restore and rollback

The tracked plist and project record are the configuration backup. OPNsense has
the two pre-change XML checkpoints named above.

Rollback:

1. `launchctl bootout gui/$(id -u) ~/Library/LaunchAgents/com.jason.homelab.canon-mf644-airprint.plist`
2. remove the installed plist (retain the Git copy for evidence);
3. re-enable IPv4 mDNS on the MF644 only after the proxy has stopped; restore
   its desired native mDNS/AirPrint name if the printer retained a collision
   suffix;
4. remove only the affected `canon-mf644cdw` or `canon-mf210-hall` Dnsmasq
   reservation, or restore its named OPNsense checkpoint if broader Dnsmasq
   recovery is required;
5. restart Dnsmasq and verify its health;
6. clients fall back to native discovery while the printer is awake or direct
   IPP at `192.168.1.183`.
7. remove the Mac's Hall queue, if required, with
   `lpadmin -x Canon_MF210_Hall`; this does not alter the printer or reservation.

## Documentation and systems-of-record impact

- HomeLab Doctor: not changed; bounded user-facing discovery has a direct-IP fallback.
- Monitoring/Beszel: no new host or service endpoint; LaunchAgent logs are sufficient.
- Backup/recovery: Git-tracked plist plus two OPNsense checkpoints.
- NetBox: no topology, interface or VLAN change; reservation ownership remains OPNsense.
- Human wiki/Aster mirror: not required for this small local workaround.
- Operational reference: this document is the runbook and recovery record.
- Environment/release lifecycle: not a deployed application release; LAN utility only.
- Repository documentation: project portfolio and changelog updated.
- Diagrams/rack/Homepage/authentication/certificates/firewall: no impact.
- DNS: two private Dnsmasq reservations and generated
  `canon-mf644cdw.internal` / `canon-mf210-hall.internal` records.
- Automation: one user LaunchAgent, retained and observable.
- Security inventory/AI administration: no credential or AI capability exists or is added.

## Graduation criteria

The project is complete when the reservation is healthy, the persistent job
survives loading, sleeping-printer discovery and direct IPP pass, rollback is
documented, logs are collision-free, and this record contains the final evidence.

## Evidence log

| Date | Action and evidence | Result |
|---|---|---|
| 2026-10-19 | Compared two Canon printers and tested MF644 mDNS before/after sleep; HTTP/SNMP/IPP stayed reachable | Root cause isolated to the MF644 sleep-time Bonjour responder |
| 2026-10-19 | Renamed native service to `Canon MF644Cdw Office`, restarted and resolved its complete AirPrint record | Corrupt collision-suffixed name repaired |
| 2026-10-19 | Saved OPNsense checkpoint, added exact MAC/IP reservation, restarted Dnsmasq, and resolved `canon-mf644cdw.internal` to `192.168.1.183` | Reservation healthy |
| 2026-10-19 | Published with target `canon-mf644-proxy.local`; subtype browse, service resolve, A lookup and TCP 631 all passed | Collision-safe design proven before persistence |
| 2026-10-19 | Installed the tracked plist with mode `0600`; `launchctl` reports one running process and the installed file matches the tracked source | Persistent publisher active |
| 2026-10-19 | After the sleep interval, subtype browsing returned `Canon MF644Cdw Office`, service resolution returned `canon-mf644-proxy.local:631`, the hostname resolved to `192.168.1.183`, and TCP 631 connected | End-to-end discovery and direct print path passed |
| 2026-10-19 | Publisher output contains both successful registrations and no `Name in use` or conflict entry | Collision control passed |
| 2026-10-19 | Queried the MF210 directly on UDP 5353 after it had been idle; `_ipp._tcp.local` returned `Hall`, its full AirPrint TXT/SRV data and `Canon5fb19f.local` at `192.168.1.205`; TCP 631 also connected | MF210 does not reproduce the MF644 issue; no proxy warranted |
| 2026-10-19 | Confirmed the active lease maps `28:C2:DD:F1:B2:E7` to `192.168.1.205`, saved the second checkpoint, added `canon-mf210-hall.internal`, restarted Dnsmasq and validated both port 53 and direct port 53053 resolution | MF210 reservation healthy; Bonjour and IPP unchanged |
| 2026-10-19 | Duplicate screenshot and live browse showed the proxy's clean instance plus the printer's collision-suffixed native instance; the printer did not answer a direct mDNS query while asleep | Duplicate mechanism confirmed rather than inferred |
| 2026-10-19 | With approval, disabled only MF644 IPv4 mDNS. Remote UI still reports AirPrint On and IPP Printing On; direct UDP 5353 now times out, TCP 631 connects, the proxy resolves to `canon-mf644-proxy.local:631`, and after cache expiry browse shows one MF644 plus `Hall` | Duplicate eliminated without proxying print traffic |
| 2026-10-19 | Hall appeared in the AirPrint subtype, but macOS 26.6.2 had no Canon MF210 vendor PPD. A read-only IPP test passed and reported IPP 2.0, AirPrint 1.4/1.3, PDF/PWG Raster/URF and accepting-jobs state | Driver download is unnecessary; printer is valid for driverless IPP Everywhere |
| 2026-10-19 | With approval, added `Canon_MF210_Hall` at `ipp://192.168.1.205/ipp/print` with model `everywhere`; queue is idle/enabled and exposes Letter, A4, envelopes, media types, grayscale and quality controls | Hall is installed without a vendor driver; MF644 remains the default; no test page sent |

## User-facing handover

No new app or login is required. In macOS/iOS printer selection, choose
`Canon MF644Cdw Office`; the Mac mini supplies discovery and the client then
prints directly to the Canon. The printer may still show its normal sleep
state. If the printer disappears, first confirm the Mac mini user session is
running and check the LaunchAgent with `launchctl print
gui/$(id -u)/com.jason.homelab.canon-mf644-airprint`. Direct IPP at
`192.168.1.183:631` remains the recovery path. Do not remove the OPNsense
reservation unless the LaunchAgent is also disabled or retargeted.

For the monochrome printer, choose `Canon MF210 Hall` in the Mac print dialog.
It is a driverless IPP Everywhere queue and does not require Canon software.
The MF644 remains the system default.

## Close-out

The persistent publisher is active and the post-deployment intent/efficiency
review passed: one idle `dns-sd` process provides the sole MF644 discovery
record, introduces no print proxy or new trust path, and retains native sleep,
AirPrint capability and direct IPP. Stable Bonjour discovery depends on the Mac
mini user LaunchAgent; direct-IP printing is the independent recovery path.

## Documentation adequacy reflection

This record contains the architecture, authoritative configuration path,
validation commands, checkpoint and exact rollback. No additional service
registry, rack, firewall or credential handover is needed for the bounded LAN
discovery workaround.
