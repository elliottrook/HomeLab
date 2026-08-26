# HomeLab UPS & Power Resilience Project
## Project Handover: Claude

**Project owner:** Jason  
**Implementation assistant:** Claude  
**Final integration/review:** Aster / ChatGPT  
**Environment:** Jason's HomeLab  
**Repository:** This public HomeLab repository. Treat it as the authoritative source for current infrastructure details.

**Project status:** Handover ready; NUT/UPS implementation not yet validated

**Last reconciled:** 2026-08-24

## Project milestone tracker

This tracker provides the stepwise project view. The numbered sections below
contain Claude's detailed requirements, and Section 26 remains the final
item-level Definition of Done.

### Milestone 1 — Utility host foundation

- [x] Record the NUT server's intended identity: `192.168.50.25`, MAC
  `00:23:24:55:b1:1a`, Management VLAN 50, directly connected to Arista Et31.
- [x] Inventory the Lenovo hardware and install/update the selected bare-metal OS.
  Confirmed 2026-08-25 via `hostnamectl`/`lscpu`/`lsblk`: Lenovo
  **ThinkCentre M92p**, Intel **Core i5-3470T** (3rd gen, not the ~5th gen
  originally estimated), 7.6 GB RAM, single 119.2 GB disk (LVM: `/boot`
  partition + root/swap logical volumes). OS is Debian GNU/Linux 13
  (trixie), kernel `6.12.101+deb13-amd64`, no pending package upgrades.
  Recorded in [03-Hardware-Inventory.md](03-Hardware-Inventory.md).
- [x] Configure stable hostname, address, DNS, time and restricted administration.
  - [x] DNS resolution fixed 2026-08-24: `/etc/network/interfaces` specified
    `dns-nameservers 192.168.50.1`, but the `resolvconf` package was not
    installed, so `/etc/resolv.conf` never received a `nameserver` line and
    all name resolution (including `apt`) failed. Installed `resolvconf`,
    confirmed `/etc/resolv.conf` is now regenerated correctly via
    `resolvconf(8)`, and verified `apt-get update` and `getent hosts`
    both succeed after a reboot.
  - [x] Hostname confirmed 2026-08-25: static hostname `nut-server` already
    set (`hostnamectl`).
  - [x] Time confirmed 2026-08-25: NTP active and synchronized, timezone
    `America/Vancouver` (`timedatectl`).
  - [x] Restricted administration: SSH password authentication disabled
    2026-08-25 via `/etc/ssh/sshd_config.d/hardening.conf`
    (`PasswordAuthentication no`, `KbdInteractiveAuthentication no`,
    `PermitRootLogin prohibit-password`), validated with `sshd -t` and
    applied with `systemctl reload ssh` (no dropped sessions). Key-based
    login (`jason`'s existing `authorized_keys`, aliased as `ssh nut` on
    Jason's Mac) confirmed still working after the reload. No firewall
    (`ufw`/iptables) or `fail2ban` is configured — recorded as an
    **Observation / Recommended Follow-up** (Section 23) rather than
    blocking this item, since SSH brute-force risk is now substantially
    reduced by key-only auth and the host is Management-VLAN-only with
    no WAN exposure.
- [x] Verify reboot, network reachability and independence from the UniFi PoE
  uplink on Et33. Confirmed 2026-08-25: the host survived a reboot
  (2026-08-24 23:40) and came back up on its static config with working
  DNS; live MAC/interface (`eno1`, single onboard NIC, no other interfaces)
  matches the recorded identity. Independence from the UniFi PoE switch was
  already documented in
  [Current-Network-Baseline.md](Current-Network-Baseline.md) — direct
  connection to Arista Et31, not downstream of the PoE switch (Et33).

### Milestone 2 — UPS discovery and NUT server

- [ ] Identify both UPS models, USB/device paths, capabilities and protected loads.
  - [x] UPS #3 (CyberPower CP1500PFCLCD, dedicated to Proxmox) confirmed
    2026-08-25: physically connected via USB to the Lenovo NUT server,
    visible as `Bus 003 Device 003`, USB ID `0764:0601`. Model identity
    verified authoritatively via live `usbhid-ups`/`upsc` query (HID
    Power Device data read from the unit itself): `device.model` /
    `ups.model` = `CP1500PFCLCDa`, serial `CXXRO7009593` — this matches
    the originally recorded model. (Note: `lsusb`'s plain-text name for
    this USB ID resolves to `PR1500LCDRT2U` via the static `usb.ids`
    table, which is keyed only on vendor:product ID and is not specific
    to this device — CyberPower reuses ID `0764:0601` across models, so
    that name is misleading and should not be used for identification.)
    Device node `/dev/bus/usb/003/003` is group-owned by `nut` via an
    existing udev rule.
  - [x] `usbhid-ups` driver (`proxmox-ups`) configured in `ups.conf`,
    `nut.conf` set to `MODE=standalone`, `nut-driver@proxmox-ups` and
    `nut-server` services running and confirmed via `upsc
    proxmox-ups@localhost`: `ups.status: OL CHRG`, `battery.charge: 99`,
    `battery.runtime: 11403`, `input.voltage`/`output.voltage: 118.0`,
    `ups.realpower.nominal: 1000`. `ups.load: 0` — worth confirming with
    Jason whether Proxmox is actually plugged into this unit's output.
    `nut-monitor`/`upsmon` not yet configured (Milestone 3 territory).
  - [x] UPS #1 (APC Back-UPS Pro BN1500M2-CA) inspected 2026-08-25 (still at
    Jason's desk, battery not yet installed): **no NUT-compatible
    monitoring interface exists on this unit.** The rear panel carries
    only surge-protection passthrough jacks — two "Gigabit In/Out" RJ45
    (Ethernet surge protection), a third RJ45 labeled "Data port" (phone/
    DSL-speed surge protection, not a UPS data interface), "Cable In/Out"
    coax (surge protection), and a TVSS ground terminal. None of these
    carry UPS telemetry. The only USB ports (Type-A + Type-C) are on the
    front and are device-charging outputs (UPS supplies power out), not a
    computer-facing monitoring port — confirmed by physical inspection,
    no other USB/serial socket exists anywhere on the unit. **Conclusion:
    UPS #1 cannot be a NUT client and will operate as a "dumb battery"
    only** — it can provide runtime for its protected loads (TrueNAS +
    both Synology units per Section 2) but NUT has no way to read its
    status or trigger a coordinated shutdown from it. Recorded as an
    **Observation / Recommended Follow-up** (Section 23): Synology DSM
    has its own native UPS integration (separate from NUT, via direct
    USB to the NAS) that could be worth evaluating independently for
    those two boxes, outside this project's central-NUT-server scope.
    **Update 2026-08-25:** Jason ordered a second CyberPower CP1500PFCLCD
    (same model as UPS #3) to replace this APC unit, since it's already
    confirmed NUT-compatible via `usbhid-ups`. Not yet arrived — once it
    is, repeat the same identify/configure steps used for UPS #3. Final
    disposition of the APC BN1500M2-CA (retire, repurpose as a
    dumb-battery elsewhere, etc.) is still to be decided.
  - [ ] UPS #2 (CyberPower OR500LCDRM1U) remains to be connected/identified
    (already rack-mounted; Lenovo is still at Jason's desk, so a USB run
    to the rack may not be physically possible until relocation).
- [ ] Document the physical power topology and safe runtime assumptions.
- [ ] Install NUT directly on the utility host and configure least-privilege users.
- [ ] Prove both UPS devices are detected consistently after reboot.

### Milestone 3 — Coordinated shutdown

- [ ] Define warning and shutdown thresholds from measured runtime.
- [ ] Configure and validate Proxmox shutdown behaviour.
- [ ] Configure and validate applicable NAS/storage shutdown behaviour.
- [ ] Document final shutdown order, return-of-power behaviour and manual override.

### Milestone 4 — Monitoring and recovery

- [ ] Add the utility host to Beszel and expose only required read-only UPS metrics.
- [ ] Add actionable power/NUT checks and alerts to HomeLab Doctor/reporting.
- [ ] Protect NUT configuration and document bare-metal recovery.
- [ ] Perform controlled failure, shutdown and recovery tests.
- [ ] Update repository inventory, architecture, operations, backups and evidence.

### Milestone 5 — Hand-back

- [ ] Complete every applicable Section 26 checkbox or explicitly defer it with a
  reason and risk.
- [ ] Produce the required close-out report, Git references and final known-good
  test state for Aster's architectural review.

## 1. Purpose

Claude is delegated ownership of the **UPS & Power Resilience mini-project**. This is an addition to the established HomeLab architecture, not an opportunity to redesign it.

Work with Jason interactively to:

1. Inspect this repository and understand the current architecture.
2. Build the old Lenovo Tiny PC into a dedicated infrastructure utility machine.
3. Connect the HomeLab UPS systems to this machine.
4. Install and configure **Network UPS Tools (NUT) directly on bare-metal Linux**.
5. Make the Lenovo/NUT system the authoritative power-state service for relevant HomeLab equipment.
6. Implement an orderly shutdown strategy for supported systems.
7. Integrate the utility machine and UPS monitoring into existing monitoring, including **Beszel** where appropriate.
8. Add the new machine/configuration to the HomeLab backup regime.
9. Extend **Lab Doctor** so UPS/NUT infrastructure is checked as part of HomeLab diagnostics.
10. Test failure and recovery behaviour safely.
11. Fully document the implementation.
12. Produce a clean hand-back package for Aster to review and reincorporate into the master HomeLab project.

The project is complete only when **power monitoring, controlled shutdown, monitoring, backup, diagnostics, testing, and documentation form one coherent system**.

## 2. Existing Context

Jason currently has **two UPS units** protecting parts of the HomeLab. Historically these have effectively operated as "dumb batteries": equipment receives battery-backed power, but the HomeLab lacks a coordinated software layer capable of responding intelligently to power failures.

Desired architecture:

```text
UPS hardware
    ↓
USB / supported management connection
    ↓
Lenovo utility machine
    ↓
NUT server
    ↓
HomeLab systems / monitoring / automation
```

The Lenovo should remain independent of the virtualized infrastructure, which is why NUT should run **directly on its bare-metal OS**, not in Docker or on Proxmox.

## 3. Lenovo Utility Machine

An older Lenovo Tiny-form-factor PC is available. Verified hardware
(2026-08-25, via `hostnamectl`/`lscpu`/`lsblk` on the installed OS):

- Lenovo ThinkCentre M92p
- Intel Core i5-3470T (3rd generation, 2 cores / 4 threads, 2.9 GHz base)
- 7.6 GB RAM
- Single 119.2 GB disk (LVM: `/boot` partition + root/swap logical volumes)
- Onboard NIC: Intel 82579LM Gigabit (single interface, `eno1`)

Its role is a small, reliable **HomeLab infrastructure utility node**. Priorities: reliability, low resource use, simple recovery, minimal dependencies, SSH administration, predictable network identity, backup, health monitoring, and documentation. Do not add unrelated applications simply because spare resources exist.

## 4. Operating System

Select a stable lightweight Linux installation suitable for a long-lived infrastructure appliance. A minimal Debian-family server installation is likely appropriate unless repository context provides a reason otherwise. No desktop environment is required.

Document OS/version, hostname, IP/VLAN, storage layout, relevant packages, update mechanism, SSH configuration, and backup method. Do not expose the machine directly to the public Internet.

## 5. Network Placement

Inspect the repository before configuration and determine the correct current management/infrastructure VLAN and addressing conventions. **Do not invent a new VLAN or addressing scheme.**

Record hostname, MAC address, switch/port, VLAN, IP, gateway, and DNS. Update appropriate inventory/network documentation.

Current reserved identity confirmed 2026-08-24:

| Hostname | Address | MAC | VLAN | Physical path |
|---|---|---|---:|---|
| `nut-server` | `192.168.50.25` | `00:23:24:55:b1:1a` | 50 Management | Directly connected to Arista Et31 |

Arista Et33 is separately reserved as the UniFi PoE-switch uplink. The NUT
server is not connected through the PoE switch.

## 6. UPS Hardware Discovery

Do not assume the two UPS units are identical. For each UPS identify:

- manufacturer and exact model;
- capacity;
- approximate age if known;
- USB/serial/network management capability;
- NUT-compatible driver;
- devices currently powered from it;
- critical equipment;
- estimated load if available;
- battery condition/status.

Verify repository information against the physical hardware with Jason. Create a simple **UPS → connected equipment** power topology because shutdown behaviour must reflect actual physical wiring.

## 7. Physical Connection

Where supported, connect each UPS management interface to the Lenovo. USB is expected but must be verified from actual models. Both UPS units should preferably be independently visible to NUT.

Verify stable identification across reboot. Avoid dependence solely on transient device numbering such as `/dev/ttyUSB0` when persistent identifiers are available. Record physical connection, serial/unique identifier, Linux device identification, and NUT driver assignment. Label cables if practical.

## 8. NUT Architecture

Install **Network UPS Tools (NUT)** directly on the Lenovo OS. The Lenovo is the central NUT server.

```text
UPS #1 ─┐
        ├── Lenovo Utility Node
UPS #2 ─┘        │
                 ├── NUT drivers
                 ├── upsd
                 ├── upsmon
                 └── Network NUT clients
                         ├── Proxmox
                         ├── applicable NAS systems
                         └── other appropriate critical hosts
```

Use current NUT configuration conventions and make the configuration understandable and maintainable.

## 9. Security

Restrict NUT to required interfaces/networks, apply firewall restrictions, use minimum necessary permissions, separate monitoring/control credentials where appropriate, and provide no public Internet exposure.

**This repository is public. Never commit real passwords, API keys, tokens, UPS credentials, SSH private keys, or other secrets.** Provide sanitized configuration templates and document where real secrets reside.

## 10. Shutdown Strategy

Do not configure "power failure = immediate shutdown." Distinguish between short disturbance, sustained outage, low battery, UPS communication failure, recovery, and return of mains power.

Develop trigger timings with Jason after identifying UPS runtime, load, physical topology, and dependency relationships. The objective is to tolerate brief interruptions while preserving enough battery for orderly shutdown during a sustained outage.

## 11. Shutdown Ordering

Determine exact ordering from the current architecture. General principle:

1. **Non-critical workloads** — stop expendable workloads if useful for extending runtime.
2. **Applications/services** — gracefully stop appropriate applications, containers and VMs.
3. **Storage-dependent systems** — consumers stop before storage where required.
4. **Proxmox hypervisor** — shut down after relevant guests.
5. **Storage systems** — gracefully shut down applicable NAS/storage systems.
6. **Lenovo/NUT server** — remain operational as long as practical because it coordinates shutdown.
7. **UPS output shutdown** — if supported and appropriate, only after protected systems have stopped safely.

Do not implement automatic UPS power cycling without understanding behaviour when mains returns.

## 12. Proxmox Integration

The Dell Precision 5810 Proxmox host is a major protected system. Determine the cleanest supported method for it to respond to the central NUT server.

Test UPS-state visibility, communication-loss behaviour, shutdown commands, orderly VM/container shutdown, and clean host shutdown. Do not perform destructive outage testing without Jason's explicit agreement.

## 13. NAS / Storage Integration

Inspect repository documentation for current Synology/TrueNAS-related infrastructure. Determine which storage systems are actually UPS-backed and which support NUT or compatible network UPS monitoring. Do not assume every NAS should be a NUT client.

For each protected storage system document UPS source, monitoring mechanism, shutdown trigger, dependencies, and restart behaviour. Ensure storage consumers stop before storage where necessary.

## 14. Network Infrastructure

Document which critical network devices are UPS-backed, including relevant OPNsense, Arista, UniFi/PoE switching, AP/network infrastructure, and ISP modem/ONT equipment where applicable. Not every device needs software shutdown. The Lenovo must retain network connectivity long enough to issue required commands.

## 15. Monitoring Integration

The established monitoring direction is:

- **Beszel** for lightweight everyday status/health visibility;
- **Prometheus + Grafana** for deeper metrics/history/alerting.

Add the Lenovo itself to Beszel. Where practical expose useful UPS data: mains status, battery charge, runtime estimate, UPS load, input/output voltage, battery voltage, UPS status, and communication state.

Do not force all metrics into Beszel. If richer UPS metrics belong in Prometheus/Grafana, follow the existing architecture rather than creating a parallel monitoring stack.

## 16. Alerts

Where supported by existing alerting, implement sensible notifications for events such as UPS on battery, mains restored, low battery, communication loss, battery replacement warning, high UPS load, and shutdown initiated. Avoid excessive alert noise.

## 17. Lab Doctor Integration

Inspect the existing **Lab Doctor** implementation before modifying it. Extend it using existing conventions so future diagnostics can answer: **"Is the power-management infrastructure healthy?"**

Useful checks may include:

```text
Lenovo reachable
NUT service running
UPS #1 detected
UPS #2 detected
UPS communication healthy
UPS status valid
Battery state available
NUT network endpoint reachable
```

Do not create a competing health-check framework.

## 18. Backup Integration

The Lenovo is infrastructure and its recoverable configuration must join the HomeLab backup strategy. Inspect `docs/05-Backups.md` and the current backup implementation before changing anything.

At minimum preserve what is needed to reconstruct OS configuration where appropriate, NUT configuration, monitoring integration, Lab Doctor components, scripts, service definitions, relevant firewall/network configuration, and package/rebuild information.

Secrets must remain separate from public Git. The HomeLab off-site strategy includes **iDrive e2 S3-compatible storage** for system backups; follow the repository's current backup architecture rather than creating an independent system.

Desired recovery outcome: if the Lenovo HDD dies, Jason can replace/reinstall it and restore UPS service without reverse-engineering the project.

## 19. Recovery Documentation

Produce a concise procedure from **dead Lenovo/replacement disk → working NUT server managing both UPS units**. Cover OS installation, packages, configuration restoration, secrets restoration, networking, NUT validation, client validation, and monitoring restoration.

## 20. Safe Testing

Testing must be staged. Do not begin by pulling mains power while the whole HomeLab is running.

1. **Detection:** both UPS devices visible with sensible telemetry.
2. **NUT server:** services survive Lenovo reboot.
3. **Network query:** an authorized second machine can query NUT.
4. **Client monitoring:** protected hosts correctly see UPS state.
5. **Simulated shutdown condition:** test logic without exhausting batteries where possible.
6. **Controlled client shutdown:** test individual systems first.
7. **Controlled power-loss test:** only after earlier tests pass and Jason explicitly approves.
8. **Recovery:** confirm behaviour when utility power returns.

Document expected result, actual result, pass/fail, and corrective action for each significant test.

## 21. Failure Modes

Explicitly consider: one UPS disconnected, both UPS connections unavailable, Lenovo reboot, NUT service crash, network outage, Proxmox unreachable, NAS unreachable, brief mains loss/recovery, sustained outage, low battery, battery exhaustion, UPS hardware failure, and Lenovo hardware failure. The goal is predictable behaviour, not elaborate automation for every theoretical failure.

## 22. Repository Discipline

Inspect repository structure and conventions before making changes. Do not duplicate documentation where existing documents should be extended. Maintain established formatting. Scripts/config templates need clear names, useful comments, no embedded secrets, installation locations, and dependencies.

Keep a record of every repository-relevant change.

## 23. Scope Control

Claude owns implementation of this project but should **not independently redesign** VLAN architecture, OPNsense, Arista switching, SSO, Home Assistant, AI/Hermes, general monitoring architecture, master backup architecture, or unrelated services.

If the work exposes a broader issue, record it as **Observation / Recommended Follow-up** rather than expanding scope. Ask Jason before any major architectural departure.

## 24. Required Final Documentation

Before hand-back, create a comprehensive close-out record covering:

- **Hardware:** Lenovo exact model/spec, both UPS models, physical connections, protected devices, switch port, VLAN/IP.
- **Software:** OS/version, NUT version/architecture, packages, services, firewall rules.
- **NUT:** UPS names/drivers, server/client configuration, monitoring rules, shutdown logic, sanitized examples.
- **Monitoring:** Beszel, Prometheus/Grafana if implemented, alerts, available metrics.
- **Lab Doctor:** checks added, expected output, failure behaviour.
- **Backup:** protected files/configs, mechanism, destination, restore process, secret handling.
- **Testing:** test, expected result, actual result, pass/fail, corrective action.

## 25. Claude's Final Hand-Back Report

At completion create a document titled **UPS & Power Resilience — Implementation Close-Out**, specifically intended for Aster/ChatGPT. It must include:

1. Executive Summary — what was implemented and operational state.
2. Final Architecture — concise UPS → Lenovo/NUT → clients → shutdown flow.
3. Final Hardware Inventory.
4. Final Network Configuration — hostname, IP, VLAN, relevant ports.
5. Final Software Configuration.
6. Protected Systems — UPS-backed systems and controlled-shutdown participants.
7. Shutdown Sequence — exact triggers and order.
8. Monitoring — Beszel, Prometheus/Grafana and alerts actually implemented.
9. Lab Doctor Changes — exact checks added.
10. Backup Changes — what was added and how it restores.
11. Repository Changes — every file created/modified, script/template, and Git commit/branch references.
12. Testing Results.
13. Outstanding Issues — incomplete, uncertain, unsupported or deferred items; do not hide failed tests.
14. Recommended Follow-Ups outside scope.
15. **Information Aster Must Incorporate** — facts that supersede assumptions in master documentation.

## 26. Definition of Done

- [x] Lenovo hardware inventoried.
- [x] Bare-metal Linux installed and updated.
- [x] Stable hostname/IP/network placement configured.
- [x] Lenovo documented in HomeLab inventory.
- [ ] Both UPS units positively identified.
- [ ] UPS-to-device power topology documented.
- [ ] UPS management connections attached to Lenovo.
- [ ] Both UPS devices reliably detected after reboot.
- [ ] NUT installed on bare metal.
- [ ] NUT server securely configured.
- [ ] Appropriate NUT clients configured.
- [ ] Proxmox shutdown behaviour implemented and tested.
- [ ] Applicable NAS shutdown behaviour implemented and tested.
- [ ] Shutdown ordering documented.
- [ ] Power-return behaviour understood and documented.
- [ ] Lenovo added to Beszel.
- [ ] UPS monitoring integrated into existing observability where practical.
- [ ] Appropriate alerts implemented or explicitly deferred.
- [ ] Lab Doctor extended for UPS/NUT health.
- [ ] Lenovo/NUT configuration included in backup strategy.
- [ ] Restore procedure documented.
- [ ] Secrets excluded from public Git.
- [ ] Controlled failure testing completed.
- [ ] Recovery testing completed.
- [ ] Repository documentation updated.
- [ ] Final implementation close-out report produced.
- [ ] Outstanding/deferred improvements explicitly listed.
- [ ] Final Git commit/branch state recorded.

## 27. Handover Boundary

Work with Jason until the Definition of Done is satisfied or remaining items are explicitly deferred. Then **stop expanding the project**.

Give Jason:

1. final Git branch/commit reference;
2. the **UPS & Power Resilience — Implementation Close-Out** report;
3. outstanding/deferred items;
4. confirmation of the last successful test state.

Jason will return the project to **Aster / ChatGPT**, who will perform final architectural review, reconcile the implementation against the wider HomeLab project, update master project state as necessary, and determine the next project.

## Guiding Principle

This project is not primarily about monitoring battery percentage. It is about turning two independent UPS batteries into a **managed HomeLab power-resilience system**.

When finished, the HomeLab should know **when power has failed, how serious the failure is, how much runtime remains, which systems need to stop, in what order they should stop, whether that process succeeded, and how the power-management infrastructure itself can be recovered.**
