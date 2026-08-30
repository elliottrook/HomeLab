# UPS & Power Resilience — Implementation Close-Out

**Prepared for:** Aster / ChatGPT (final architectural review)
**Implementation assistant:** Claude
**Project owner:** Jason
**Date:** 2026-08-29
**Detailed working record:** [UPS-Power-Resilience-Claude-Handover.md](UPS-Power-Resilience-Claude-Handover.md) — this close-out summarizes it; that document has the full evidence trail, exact commands, and reasoning for every decision below.

## 1. Executive Summary

Three physical UPS units (plus one retired dumb-battery unit) are now coordinated by a bare-metal NUT (Network UPS Tools) server on a Lenovo ThinkCentre M92p. Proxmox and TrueNAS are independent NUT network clients that each shut themselves down (and, for Proxmox, dependent Synology units) when their respective UPS crosses a deliberately-chosen low-battery threshold — not NUT's ~10% hardware default. The trigger *mechanism* was validated via a safe simulated test; the real shutdown scripts have not been live-tested against a genuine outage, by explicit deferral to after this hand-back.

Milestones 1–4 are complete except two intentionally-deferred test items (see Section 12/13). Milestone 5 (this document) is in progress.

## 2. Final Architecture

```text
CyberPower CP1500PFCLCD (proxmox-ups) -- Proxmox + both Synology units
CyberPower CP1500PFCLCD (nas-ups)     -- TrueNAS + Arista core switch
CyberPower OR500LCDRM1U (network-ups) -- OPNsense, nut-server itself,
                                          UniFi PoE switch, camera switch
APC Back-UPS Pro BN1500M2-CA          -- dumb battery, unassigned
        |
        | USB (all three NUT-managed units)
        v
Lenovo ThinkCentre M92p (nut-server, 192.168.50.25, Management VLAN 50)
  - upsd (netserver mode, LISTEN on 127.0.0.1 and 192.168.50.25)
  - one usbhid-ups driver per unit, pinned by USB serial (all three
    CyberPower units share USB vendor:product ID 0764:0601)
  - local upsmon (primary) monitors ONLY network-ups (its own power source)
        |
        | network (NUT protocol, port 3493, secondary/client role)
        +--> Proxmox (192.168.50.10) -- custom SHUTDOWNCMD script
        +--> TrueNAS (192.168.20.40) -- native "ups" middleware client
```

Each UPS's low-battery threshold is overridden via `ups.conf`
(`override.battery.charge.low` + `ignorelb`, since the override alone
doesn't affect the driver's actual `LB` computation for this hardware —
see Section 12): `nas-ups`=50%, `proxmox-ups`=80%, `network-ups`=25%.
`proxmox-ups`'s threshold is high (fires early) specifically because its
shutdown sequence depends on Arista (on `nas-ups`) still being powered,
not because of its own battery runway — full reasoning in the handover
doc's Milestone 3 tracker.

## 3. Final Hardware Inventory

| Unit | Model | Serial | Protected equipment |
|---|---|---|---|
| NUT server | Lenovo ThinkCentre M92p | — | Intel i5-3470T, 7.6 GB RAM, 119.2 GB disk (LVM), Debian 13 |
| `proxmox-ups` | CyberPower CP1500PFCLCD | `CXXRO7009593` | Proxmox (Dell Precision T5810) + both Synology units |
| `nas-ups` | CyberPower CP1500PFCLCD | `CXXRP7016137` | TrueNAS + Arista core switch |
| `network-ups` | CyberPower OR500LCDRM1U | `GA4KS2000999` | OPNsense, the Lenovo itself, UniFi PoE switch, camera switch |
| (unassigned) | APC Back-UPS Pro BN1500M2-CA | — | None — no NUT-compatible interface exists on this unit at all (confirmed by physical inspection: all rear ports are surge-protection passthrough, front USB is charging-only) |

The final equipment-to-UPS mapping differs from the project's original
plan — Jason redistributed load across the three active units to work
within physical/cabling constraints once everything reached its
permanent placement.

## 4. Final Network Configuration

- NUT server: `192.168.50.25`, Management VLAN 50, direct Arista Et31 connection, MAC `00:23:24:55:b1:1a`
- `upsd` listens on `127.0.0.1:3493` and `192.168.50.25:3493` (explicit `LISTEN` directives — the package default with none is loopback-only regardless of `MODE`)
- New OPNsense rules added (each narrowly source/destination scoped, not broad VLAN-to-VLAN):
  - Management VLAN 50 → Servers VLAN 20: Lenovo → Beszel hub (`192.168.20.20:8090`)
  - Servers VLAN 20 → Management VLAN 50: Proxmox (`192.168.50.10`) and TrueNAS (`192.168.20.40`) → NUT server (`192.168.50.25:3493`)
  - Management VLAN 50 → Servers VLAN 20: Proxmox's host IP → both Synology units (`192.168.20.41`/`.42`) on port 22 (needed for the shutdown script's SSH step)
- SSH password authentication disabled on the NUT server (key-only, `PermitRootLogin prohibit-password`)

## 5. Final Software Configuration

- NUT 2.8.1-5 on the Lenovo (bare metal, `MODE=netserver`)
- Three `usbhid-ups` driver instances, each pinned by USB serial (not `port = auto` alone, which is ambiguous once more than one identical-model UPS shares a bus)
- Least-privilege accounts in `upsd.users`: `upsmon` (local `primary`, monitors only `network-ups`), `netclient` (`secondary`, shared by Proxmox and TrueNAS's remote connections)
- Proxmox: `nut-client` package, `MODE=netclient`, custom `SHUTDOWNCMD` at `/usr/local/bin/nut-shutdown.sh`
- TrueNAS: native `ups` middleware service (not a separate package install — TrueNAS already owns NUT internally), `mode: SLAVE` (client), `shutdown: LOWBATT`, `powerdown: false`
- Beszel agent installed on the Lenovo (host-level metrics only, not UPS-specific)
- All credentials are randomly generated and live only in the relevant config files (`upsd.users`, `upsmon.conf`, TrueNAS's `ups.update`) — never committed to Git (see Section 12 for credential-exposure incidents during setup, all caught and rotated same-session)

## 6. Protected Systems

| System | UPS | Shutdown mechanism |
|---|---|---|
| Proxmox (host + all guests) | `proxmox-ups` | Custom script: Frigate VM 102 first (NFS dependency on TrueNAS) → remaining guests in parallel → SSH-triggered Synology shutdown → host itself |
| Both Synology units | `proxmox-ups` (via Proxmox's script) | SSH + a narrowly-scoped `NOPASSWD` sudoers drop-in for `/sbin/shutdown -h now` only |
| TrueNAS | `nas-ups` | Native middleware client, plain graceful shutdown |
| The Lenovo NUT server itself | `network-ups` | Local `upsmon`, stock `/sbin/shutdown -h +0` |
| OPNsense, Arista, UniFi PoE switch, camera switch | `network-ups` / `nas-ups` | **None** — deliberate scope decision, not a bug (see Section 14) |

## 7. Shutdown Sequence

Each tier triggers independently on its own UPS's `LB` condition — there
is no central sequencer; the order below falls out of the chosen
thresholds:

1. `nas-ups` critical (50%, ~11 min elapsed of 22.5 min budget) — TrueNAS shuts down; `nas-ups` itself keeps powering Arista on battery afterward (`powerdown: false`)
2. `proxmox-ups` critical (80%, ~12 min elapsed of 61 min budget — deliberately early) — Frigate → other guests → both Synology units (SSH) → Proxmox host
3. `network-ups` critical (25%, ~29 min elapsed of 36 min budget) — OPNsense, then the Lenovo itself last

**Return of power:** no UPS is configured to cut its own output power, so shut-down hosts stay powered by the UPS the whole time — they just performed a normal OS-issued soft shutdown. This means Proxmox, TrueNAS, and the Lenovo will likely **not** auto-restart when mains returns, even with a BIOS "AC Power Recovery" setting enabled (that responds to real DC power loss/return, not this scenario). Manual — or IPMI/remote — power-on is the current expectation; not tested against each host's actual BIOS behavior.

**Manual override:** no built-in "abort a shutdown in progress" exists. The only real intervention point is before a threshold fires (e.g., stopping a host's `nut-monitor` service to prevent it from acting). Once `nut-shutdown.sh` starts running on Proxmox, it runs to completion.

## 8. Monitoring

- **Beszel**: host-level metrics for the Lenovo (CPU, memory, disk, temperature) — not UPS-specific
- **Lab Doctor** (`scripts/doctor.sh`): `check_nut` (live health — services active, all three units detected, `ups.status` contains `OL`, battery charge warning below 50%) and `check_backup_age "NUT"` (config-backup staleness)
- No push-style alerting (NUT `NOTIFYCMD`, email, etc.) — explicitly deferred, see Section 13

## 9. Lab Doctor Changes

Added `check_nut()` to `scripts/doctor.sh`, following existing `check_*` conventions (SSH via the `nut` alias, `pass`/`warn`/`fail` helpers). Added `check_backup_age "NUT" "$BACKUP_ROOT/nut" 48` alongside the existing OPNsense/Arista/Proxmox entries.

## 10. Backup Changes

A manual pull (documented in `05-Backups.md` under "NUT / UPS Server (Lenovo)") lands `ups.conf`, `nut.conf`, `upsd.users`, `upsmon.conf`, the SSH hardening drop-in, and network/hostname info directly into `~/lab/private-backups/nut/<timestamp>/` on the Mac — already inside the existing Backup Synology pull and encrypted IDrive e2 off-site pipeline, so no new automation was needed. `upsd.users` contains real (rotated) credentials; this directory is git-ignored and outside the repository.

## 11. Repository Changes

All work is on `main`, pushed to both the Forgejo origin and its GitHub mirror. Key files touched: `CLAUDE.md`, `docs/UPS-Power-Resilience-Claude-Handover.md` (primary working record), `docs/01-Architecture.md`, `docs/04-Operations.md`, `docs/Current-Network-Baseline.md`, `docs/03-Hardware-Inventory.md`, `docs/05-Backups.md`, `scripts/doctor.sh`, `CHANGELOG.md`, and this document. See Section 15 for the final commit reference.

## 12. Testing Results

| Test | Result |
|---|---|
| Reboot with all three UPS units connected | **Pass** — every driver, `nut-server`, `nut-monitor`, and `beszel-agent` recovered automatically; each driver rebound to its correct serial after USB re-enumeration |
| Simulated shutdown-threshold test (`proxmox-ups` briefly unplugged, `SHUTDOWNCMD` swapped for a harmless command) | **Pass, with a caught defect** — real `OB` detection and real-time battery drain confirmed, but surfaced that `override.battery.charge.low` alone doesn't drive the `LB` flag; fixed with `ignorelb`, re-confirmed working without further draining |
| Full destructive shutdown scripts (Proxmox script, TrueNAS native shutdown) against a real or simulated outage | **Not performed — explicitly deferred to after handover** (Jason's decision) |
| Recovery/restart behavior after a real triggered shutdown | **Not performed — explicitly deferred to after handover** |

**Credential-exposure incidents (all self-caught, same session, all rotated immediately):**
1. `netclient` password printed via a verification `grep` on Proxmox's `upsmon.conf`
2. `netclient` password printed via TrueNAS's `midclt call ups.update` response (the API echoes the full updated config back, including the password field)
3. Local `upsmon` password printed via a diagnostic `grep` while investigating the self-shutdown bug (Section 14)
4. The *rotation* of that same password was itself exposed via the verification command for the first rotation attempt

No exposed credential is recorded anywhere in this repository — only in the relevant config files on the affected hosts, and briefly in this session's own conversation history.

## 13. Outstanding Issues

- **Controlled failure and recovery testing not performed** — deferred to after handover, per Jason's explicit decision. The trigger *mechanism* is validated; the real shutdown scripts' end-to-end behavior against a genuine outage is not.
- **Alerts explicitly deferred** — no push-style notification on UPS events; visibility is pull-based only (Lab Doctor, Beszel).
- **BIOS "AC Power Recovery" behavior unverified** on Proxmox, TrueNAS, and the Lenovo — see Section 7.
- **APC BN1500M2-CA's final disposition undecided** — retire it, or repurpose as a dumb battery elsewhere.

## 14. Recommended Follow-Ups (outside this project's scope)

- No firewall or `fail2ban` on the NUT server — mitigated substantially by key-only SSH, but not eliminated as a hardening gap.
- OPNsense, Arista, and the UniFi PoE/camera switches have no automated shutdown — a deliberate scope boundary for this milestone (Section 14 of the handover doc explicitly allows this), not a defect. Wiring OPNsense's shutdown specifically would be a reasonable next project.
- Synology DSM has its own native UPS-awareness feature (separate from NUT) that was considered as an alternative early in this project; it's now moot since SSH-triggered shutdown was implemented directly, but worth knowing it exists if the SSH-based approach ever needs revisiting.
- A mid-project self-shutdown bug was found and fixed on the Lenovo itself (local `upsmon` was treating any of the three UPS units going critical as grounds for its own shutdown, even units that don't power it) — worth a second pair of eyes reviewing the final `upsmon.conf`/`ups.conf` architecture given how easy this class of mistake was to introduce.

## 15. Information Aster Must Incorporate

- **Three new UPS units are now part of production infrastructure**, physically distributed differently than any prior planning documents may have assumed (see Section 3's mapping) — any future master-architecture document should adopt this mapping as authoritative, not re-derive one from the original per-service assumptions.
- **A new class of automated action now exists**: Proxmox and TrueNAS can shut themselves (and, transitively, both Synology units) down automatically on a UPS event. This should be reflected in any master runbook covering "what can take Proxmox/TrueNAS/Synology offline unexpectedly."
- **New OPNsense rules exist** (Section 4) that master network documentation should incorporate — all narrowly scoped, not broad VLAN merges.
- **Manual power-on is currently required** after any real triggered shutdown event (Section 7) — this should be reflected in any incident-response or outage runbook.
