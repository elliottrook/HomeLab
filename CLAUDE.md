# HomeLab — Claude Code Project Context

This repo covers two active infrastructure projects. Read this file in full before
touching any device. Default posture: **ask before every meaningful action.**
Sandbox network access is restricted to the hosts listed in `.claude/settings.json`
— nothing else is reachable without an explicit settings change and my approval.

## Network topology
- Servers VLAN 20: Main Synology DS920+ at 192.168.20.41 (Drive server, primary family
  data), Backup Synology at 192.168.20.42 (Hyper Backup repository)
- Management VLAN 50: Lenovo NUT server at 192.168.50.25 (Debian 12, user `jason`,
  sudo available), gateway 192.168.50.1
- OPNsense is the gateway/DNS/firewall (Dell EMC SD-WAN Edge 610)
- Tailscale is the preferred private remote-access path — no broad DSM internet exposure

## Project 1: Synology Drive family cloud
Goal: reactivate Synology Drive on the existing NAS as a private family cloud
(file sync, Finder/iOS access, controlled friend sharing) rather than deploying a
new platform.

8-milestone plan with completion gates — **stop and get my confirmation at each
gate before moving to the next**:
1. Discovery / capacity (read-only)
2. Identity & folder design
3. Synology Drive Server setup
4. macOS Finder pilot (Mac mini first, then laptop)
5. iPhone/iPad pilot
6. Friend sharing & file requests
7. Backup and recovery validation (Hyper Backup)
8. Monitoring, documentation, hand-back

Hard rules:
- Begin with read-only discovery only.
- Do not uninstall packages, delete old Drive state, change shared-folder encryption,
  or alter Hyper Backup selections until impact is understood and a recovery
  checkpoint exists.
- Never ask me to paste credentials, encryption keys, or recovery keys into chat
  or into any tracked file. Encrypted-folder keys and recovery instructions stay in
  protected offline storage.
- Individual DSM accounts only — no shared admin account. MFA required for admin.
- Start with LAN/Tailscale access only.

## Project 2: UPS & Power Resilience (NUT server)
Goal: Lenovo Tiny PC as a bare-metal NUT server for three UPS units, with orderly
shutdown, monitoring, backup, and Lab Doctor integration.

Authoritative reference: github.com/elliottrook/HomeLab —
`docs/UPS-Power-Resilience-Claude-Handover.md` (5-milestone tracker + 26-item
Definition of Done checklist — check items off as work progresses).

Current state:
- NUT 2.8.1-5 installed on the Lenovo box (192.168.50.25, interface eno1)
- UPS #1 (APC Back-UPS Pro BN1500M2-CA) — powers TrueNAS + both Synology units;
  currently unplugged, waiting on new battery
- UPS #2 (CyberPower OR500LCDRM1U) — powers Arista switch, OPNsense, Ubiquiti PoE switch
- UPS #3 (CyberPower CP1500PFCLCD, pure sine wave) — dedicated to Proxmox.
  Re-confirmed 2026-08-25 via live NUT/`usbhid-ups` query (authoritative —
  read from the UPS's own HID Power Device data): `device.model` /
  `ups.model` = `CP1500PFCLCDa`, serial `CXXRO7009593`. This matches the
  originally recorded model; an earlier note in this file incorrectly
  "corrected" it to `PR1500LCDRT2U` based on the generic `lsusb` name for
  USB ID `0764:0601` — that name comes from the static `usb.ids` table
  keyed only on vendor:product ID (CyberPower reuses this ID across
  several models), not from this specific device, so it was wrong. The
  live NUT-reported model is the trustworthy source going forward.
- Resolved 2026-08-24: apt/DNS resolution failure on the Lenovo box was caused
  by the `resolvconf` package being missing, so the static `dns-nameservers
  192.168.50.1` setting in `/etc/network/interfaces` never reached
  `/etc/resolv.conf`. Installed `resolvconf`; confirmed via reboot that
  `/etc/resolv.conf` regenerates correctly and `apt-get update` succeeds.
  Details in `docs/UPS-Power-Resilience-Claude-Handover.md` (Milestone 1).
- 2026-08-25: UPS #3 (CyberPower CP1500PFCLCD) is now physically connected
  to the Lenovo NUT server via USB. A `usbhid-ups` driver (`proxmox-ups`) is
  configured in `ups.conf`, `nut.conf` is set to `MODE=standalone`, and the
  `nut-driver@proxmox-ups` and `nut-server` services are running. Live
  telemetry via `upsc`: `ups.status: OL CHRG`, battery 99%, runtime ~11400s,
  input/output 118V, `ups.load: 0` (worth confirming Proxmox is actually
  plugged into this unit's output, since load reads zero). `nut-monitor`
  (upsmon) is not yet configured. Milestone 2 discovery in progress.

Hard rules:
- Milestone-based, same as above — confirm with me at each gate.
- Any command touching a live UPS, NUT config, or shutdown behavior needs explicit
  approval, even in a session where other commands are pre-approved.

## General working rules for every session
- Never run destructive commands (`rm -rf`, `mkfs`, `dd`, disk partitioning) without
  asking first, regardless of what's pre-approved.
- Never touch Hyper Backup selections, DSM shared-folder encryption, or existing
  Drive state without a recovery checkpoint.
- Treat SSH/SCP to any host, `sudo`, and package installs as always-ask, not
  auto-approved, even if the tool's `ask` list would otherwise allow a repeat.
- If something looks irreversible or you're unsure of the blast radius, stop and ask
  instead of guessing.
