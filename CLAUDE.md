# HomeLab — Claude Code Project Context

This repo covers two active infrastructure projects. Read this file in full before
touching any device. Default posture: **ask before every meaningful action.**
Sandbox network access is restricted to the hosts listed in `.claude/settings.json`
— nothing else is reachable without an explicit settings change and my approval.

## Network topology
- Servers VLAN 20: Main Synology DS920+ at 192.168.20.41 (Drive server, primary family
  data), Backup Synology at 192.168.20.42 (Hyper Backup repository)
- Management VLAN 50: Lenovo NUT server at 192.168.50.25 (Debian 13/trixie, user `jason`,
  sudo available), gateway 192.168.50.1
- OPNsense is the gateway/DNS/firewall (Dell EMC SD-WAN Edge 610)
- Tailscale is the preferred private remote-access path — no broad DSM internet exposure
- OPNsense's `MGMT_ADMIN_HOSTS` alias (see `PROJECTS.md` Phase 9) already permits
  Jason's Mac mini (192.168.1.206), Mac laptop (192.168.1.241) and iPhone
  (192.168.1.112) to reach Management VLAN 50; all other Trusted clients are blocked.
  This is a network-layer fact independent of the sandbox list below — it governs
  what the laptop itself can reach, not what Claude Code's sandbox may originate to.

## Sandbox network access

`.claude/settings.json` → `sandbox.network.allowedDomains` is the enforced allow-list
for outbound connections Claude Code can make from this laptop. Keep this table and
that file in sync — update both in the same change.

| Host | Address | Why Claude needs it |
|---|---|---|
| OPNsense | 192.168.1.1 | Gateway/firewall/DNS; `lab doctor` WAN checks |
| Management-VLAN gateway | 192.168.50.1 | Management VLAN routing checks |
| Arista core switch | 192.168.50.2 | `lab doctor` link/health checks |
| Proxmox | 192.168.50.10 | Guest/host health, backups, `lab doctor` |
| Docker LXC 100 | 192.168.20.20 | Homepage/Portainer/Pi-hole primary, `lab doctor` |
| Frigate VM 102 | 192.168.20.10 | Surveillance health checks |
| Reverse Proxy LXC 107 | 192.168.50.23 | NPM/Authentik administration |
| AP Switch | 192.168.50.26 | Direct-management recovery path |
| Forgejo LXC 108 | 192.168.20.30 | Git remote (`git.elliottrook.com` also allowed, for HTTPS) |
| Observability LXC 109 | 192.168.20.31 | Prometheus/Grafana health checks |
| TrueNAS | 192.168.20.40 | Storage/NFS health, `lab doctor` |
| Synology DS920+ | 192.168.20.41 | Backup verification |
| Backup Synology | 192.168.20.42 | Backup verification |
| NUT server (Lenovo) | 192.168.50.25 | UPS health, `lab doctor` |
| Aster Agent LXC 104 | 192.168.70.10 | Local agent API/UI health |
| Aster llama.cpp GPU LXC 110 | 192.168.70.12 | Local inference health |
| git.elliottrook.com, github.com | — | Git remotes |
| deb.debian.org, security.debian.org | — | Package installs on Debian guests |

This list exists to let Claude run the same read-only `lab`/`doctor.sh` tooling from
this laptop that already runs from the Mac mini. It is not itself a grant of SSH
trust or firewall access — those are separate, host-by-host and OPNsense-side
changes, each still gated by the permission rule below.

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
- UPS #1 (APC Back-UPS Pro BN1500M2-CA) — originally intended to power
  TrueNAS + both Synology units; the final load distribution ended up
  different (see "Corrected 2026-08-29" below). Currently unplugged,
  waiting on new battery. Confirmed 2026-08-25 by
  physical inspection: **no NUT-compatible monitoring interface exists on
  this unit** (rear ports are all surge-protection passthrough; front
  USB-A/USB-C are charging-only). Will operate as a dumb battery only —
  no software visibility or coordinated shutdown possible via NUT.
  **Replaced 2026-08-28**: the second CyberPower CP1500PFCLCD arrived and
  is now connected to the Lenovo NUT server via USB, identified and
  configured as NUT device `nas-ups` (serial `CXXRP7016137`,
  `usbhid-ups` driver, pinned by serial since it shares the same
  USB vendor:product ID as UPS #3). Confirmed via `upsc`: `ups.status: OL
  CHRG`, battery 98%. While configuring this, also pinned the existing
  `proxmox-ups` entry to its serial (`CXXRO7009593`), since `port = auto`
  alone became ambiguous once two identical-VID:PID CyberPower units were
  on the same bus. Final disposition of the old APC BN1500M2-CA is still
  to be decided.
- UPS #2 (CyberPower OR500LCDRM1U) — NUT device `network-ups`. **Final
  load (2026-08-29, corrected from the original plan):** OPNsense, the
  Lenovo NUT server itself, the UniFi PoE switch, and the camera switch.
  Identified and configured 2026-08-29 after the Lenovo's permanent
  relocation, pinned by serial `GA4KS2000999`
  (a distinct format from the CP1500PFCLCD units' `CXXR...` serials).
  Confirmed via `upsc`: `device.model: OR500LCDRM1Ua`, `ups.status: OL`,
  battery 100%, `ups.load: 23`. Powering the NUT server itself makes this
  the most structurally critical unit — if it dies, monitoring and any
  future shutdown orchestration go dark along with the gateway.
- UPS #3 (CyberPower CP1500PFCLCD, pure sine wave) — NUT device
  `proxmox-ups`. **Final load (2026-08-29, corrected from the original
  plan):** Proxmox plus both Synology units.
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
  plugged into this unit's output, since load reads zero — confirmed
  2026-08-28: Proxmox is not currently plugged in). `nut-monitor`
  (upsmon) is not yet configured. Milestone 2 discovery in progress.
- 2026-08-28: Milestone 1 fully closed (hardware inventoried, hostname/
  DNS/time confirmed, SSH password auth disabled, reboot/network
  independence verified). Both desk-connected UPS units (`proxmox-ups`,
  `nas-ups`) have least-privilege `upsd`/`upsmon` monitoring configured.
  HomeLab Doctor extended with `check_nut` (live health) and
  `check_backup_age "NUT"` (config staleness). NUT config backed up into
  the existing `~/lab/private-backups` pipeline. Lenovo added to Beszel
  (host-level metrics only, not UPS-specific) — required a new OPNsense
  rule permitting Management VLAN 50 → Servers VLAN 20 port 8090, added
  by Jason since firewall changes are outside this project's scope.
  Full details in `docs/UPS-Power-Resilience-Claude-Handover.md`.
- 2026-08-29: Lenovo relocated to its permanent placement with all three
  UPS units now within USB reach. UPS #2 (`network-ups`) identified and
  configured as a NUT client (see above) and added to `upsmon`
  monitoring (same account, now three established `upsd` connection
  pairs). All three physical units are now accounted for: `proxmox-ups`,
  `nas-ups`, `network-ups` as NUT clients, and the APC BN1500M2-CA as a
  documented dumb battery.
- **Corrected 2026-08-29**: the final equipment distribution across the
  three active UPS units differs from the original plan — Jason
  redistributed load given physical/cabling constraints. Final mapping:
  `proxmox-ups` = Proxmox + both Synology units; `nas-ups` = TrueNAS +
  the Arista core switch; `network-ups` = OPNsense + the Lenovo NUT
  server + UniFi PoE switch + camera switch. This changes the dependency
  picture from what was first documented:
  - `network-ups` is now the most structurally critical unit (it powers
    the NUT server itself and OPNsense — losing it ends monitoring and
    the gateway simultaneously), not just "runs out of runtime first."
  - `nas-ups` carries the Arista core switch, so losing it breaks local
    network switching for everything, not just NAS storage.
  - Proxmox and both Synology units now share one UPS. Jason is about to
    triple Proxmox's RAM and add a substantial GPU — today's measured
    12%/~120W load on `proxmox-ups` should not be treated as a stable
    planning baseline; re-measure runtime once that hardware lands.
  - `nas-ups` still has the shortest measured runtime (~22.5 min at
    33%/~330W), but that figure was recorded under the corrected
    TrueNAS+Arista load, not the originally planned TrueNAS+Synology
    load — still valid as a real baseline, just re-attributed.
  Full power topology table in
  `docs/UPS-Power-Resilience-Claude-Handover.md` (Section 6) has been
  updated to match.
- 2026-08-29: **Milestone 2 fully closed.** Reboot test performed with
  all three UPS units connected: every NUT driver, `nut-server`,
  `nut-monitor`, and `beszel-agent` came back automatically with no
  manual intervention, and each driver rebound to its correct serial
  after USB re-enumeration. Lab Doctor's `check_nut` passed cleanly
  afterward. Next up: Milestone 3 (coordinated shutdown thresholds,
  `SHUTDOWNCMD`, and shutdown ordering) — not yet started.
- 2026-08-29: Milestone 3 in progress. Proxmox is now a NUT network
  client (`secondary`) of `proxmox-ups`, with a custom `SHUTDOWNCMD`
  script wired in that stops Frigate (its NFS dependency on TrueNAS)
  first, then remaining guests, then SSHes into both Synology units to
  shut them down, then powers off Proxmox itself. Not yet live-tested;
  warning/shutdown timing still uses NUT's hardware default rather than
  the discussed custom thresholds. Full details, including a
  self-caught-and-rotated credential exposure during setup, in
  `docs/UPS-Power-Resilience-Claude-Handover.md` (Milestone 3 tracker).
  TrueNAS is now also a NUT client (via its native `ups` middleware
  service, not a manual package install) monitoring `nas-ups`, with
  `shutdown: LOWBATT` and `powerdown: false`. A second credential
  exposure happened and was rotated during this step too (same root
  cause: an API call echoed the secret back). Both Proxmox and TrueNAS
  confirmed connected with the final rotated password. Not yet
  live-tested.
- 2026-08-29: Shutdown thresholds tightened via `override.battery.charge.low`
  in `ups.conf`, replacing each unit's ~10% hardware default:
  `nas-ups`=50%, `proxmox-ups`=80% (deliberately early despite having
  the most battery, because its shutdown script's SSH-to-Synology step
  depends on Arista/`nas-ups` still having power), `network-ups`=25%
  (powers the Lenovo itself, so it waits longest). Percentages are
  reasoned from topology/runtime, not field-validated as "correct" —
  but the trigger *mechanism* was validated same-day via a safe
  simulated test (briefly unplugging `proxmox-ups` with `SHUTDOWNCMD`
  temporarily swapped for a harmless command). That test caught a real
  gap: `override.battery.charge.low` alone only changes the displayed
  value per NUT's own docs — it doesn't make the driver actually compute
  `LB` from charge. Fixed by adding `ignorelb` to all three `ups.conf`
  sections, confirmed working (`proxmox-ups` correctly showed `LB` at
  78%, even while still `OL CHRG`). Since the fix is at the shared
  driver level, it covers TrueNAS's view of `nas-ups` too automatically.
  `SHUTDOWNCMD` reverted to the real script afterward. Full details in
  `docs/UPS-Power-Resilience-Claude-Handover.md` (Milestone 3 tracker).
- 2026-08-29: **Milestone 3 fully closed.** While documenting the final
  shutdown order, caught and fixed one more real bug: the Lenovo's local
  `upsmon` was still monitoring `proxmox-ups` and `nas-ups` as `primary`
  with the stock `SHUTDOWNCMD` (`/sbin/shutdown -h +0`) armed — meaning
  it could have shut *itself* down because one of those two units went
  critical, even though neither powers it. Fixed by removing those two
  `MONITOR` lines; the Lenovo now only monitors `network-ups` (its
  actual power source) for its own shutdown decision. Rotated the local
  `upsmon` account password twice in the process (first exposed via a
  diagnostic `grep`, then exposed again via the verification command for
  the first rotation) — fourth and fifth credential-exposure incidents
  this session, all same root cause (a command echoing a secret that
  wasn't suppressed). Final documented shutdown order: `nas-ups` (50%)
  → `proxmox-ups` (80%) → `network-ups`/Lenovo itself (25%). OPNsense/
  Arista/PoE/camera-switch have no automated shutdown (deliberate,
  recorded as a follow-up). Power-return note: since no UPS cuts its own
  output, shut-down hosts likely won't auto-restart on mains return even
  with BIOS "AC recovery" enabled — manual power-on is the current
  expectation. Next: Milestone 4 (monitoring/recovery) already
  substantially done from earlier work; remaining UPS-project work is
  physical topology follow-ups (UPS #1 disposition) and any Recommended
  Follow-ups logged along the way.

Hard rules:
- Milestone-based, same as above — confirm with me at each gate.
- Any command touching a live UPS, NUT config, or shutdown behavior needs explicit
  approval, even in a session where other commands are pre-approved.

## General working rules for every session
- Never run destructive commands (`rm -rf`, `mkfs`, `dd`, disk partitioning) without
  asking first, regardless of what's pre-approved.
- Never touch Hyper Backup selections, DSM shared-folder encryption, or existing
  Drive state without a recovery checkpoint.
- Read-only SSH/SCP work — status checks, reading configs or logs, `systemctl
  status`, `docker ps`, listing or viewing files, resource/health checks — may run
  without asking first once the host is in the sandbox network allowlist. Any
  SSH/SCP command that changes state on a remote host (file writes, service
  restarts, deletions), plus `sudo` and package installs, remain always-ask, every
  time, even mid-session.
- Changes that alter the network's security posture or structure — VLAN membership,
  firewall rules, DNS/routing, credentials, encryption, shared-folder ACLs, or
  inter-host trust (including adding a new device's SSH key to `authorized_keys`) —
  may be made, but only when all three hold:
  1. Jason has given explicit permission for that specific change.
  2. The change is required by the active project's stated goal, not general
     convenience or "while we're in there" scope creep.
  3. The change is the most minimal one that achieves that goal, preserving the
     existing security posture in every other respect (narrowest scope, narrowest
     source/destination, shortest-lived exception that still works).

  Pre-approval for other actions in a session never extends to this category —
  always ask per change, even mid-session, even for a project where SSH/SCP or
  other actions are otherwise pre-approved.

  If a proposed change would trade off against a safety/privacy standard stated
  elsewhere in this document, do not just make the call and note it afterward. Stop
  first, name the conflict explicitly, and lay out concretely: what capability is
  gained, what exposure/risk is added, whether a narrower version of the change
  would still meet the goal, and the rollback path — so Jason decides with the full
  trade-off in view, not just the recommendation.
- Scope changes to what the current project's active milestone actually requires.
  Don't fix, tidy or reconfigure adjacent systems in passing — flag it and ask, or
  note it as a follow-up, instead of doing it unprompted.
- If something looks irreversible or you're unsure of the blast radius, stop and ask
  instead of guessing.
- Commit documentation changes to git automatically at the end of each milestone
  or comparable unit of work — no need to ask first, and no need to announce
  intent to commit beforehand either. Just run it and report the resulting
  commit hash/summary afterward — an "I'm about to commit" preamble reads as
  seeking a green light even when a reply isn't actually being awaited. `git
  push` is the exception: never push without an explicit instruction to do so
  in that message, even though committing doesn't require one.
