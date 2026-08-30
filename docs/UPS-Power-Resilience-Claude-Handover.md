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

- [x] Identify both UPS models, USB/device paths, capabilities and protected loads.
  All three physical units are now identified: UPS #1 (APC BN1500M2-CA,
  dumb battery, no NUT interface), UPS #2 (`network-ups`, CyberPower
  OR500LCDRM1U) and UPS #3 (`proxmox-ups`, CyberPower CP1500PFCLCD) plus
  its replacement (`nas-ups`, second CP1500PFCLCD). See the per-unit
  entries below for USB paths, serials and protected loads. **Note:**
  the equipment assignments in these per-unit entries reflect the
  original plan at the time each was written — the actual final
  distribution differs and is corrected in the Section 6 power topology
  table below (`proxmox-ups` also carries both Synology units, `nas-ups`
  also carries the Arista switch, `network-ups` also carries the Lenovo
  NUT server itself). Trust that table over the assignments below.
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
    **Update 2026-08-28 - replacement complete:** the second CyberPower
    CP1500PFCLCD arrived and is now connected to the Lenovo NUT server
    via USB. Since it shares the same USB vendor:product ID (`0764:0601`)
    as UPS #3, `udevadm info` was used to pull each unit's unique
    `ATTR{serial}` and pin both `ups.conf` entries by serial so driver
    binding is deterministic across reboots (the earlier `proxmox-ups`
    entry only had `port = auto`, which became ambiguous once a second
    identical-VID:PID device appeared on the bus):
    - `proxmox-ups` (UPS #3): serial `CXXRO7009593`
    - `nas-ups` (UPS #1 replacement): serial `CXXRP7016137`, dedicated to
      TrueNAS + both Synology units

    Both `nut-driver@*` instances and `nut-server` are active; confirmed
    via `upsc nas-ups@localhost`: `device.model: CP1500PFCLCDa`,
    `ups.status: OL CHRG`, `battery.charge: 98`. Final disposition of the
    old APC BN1500M2-CA (retire, repurpose as a dumb-battery elsewhere,
    etc.) is still to be decided.
  - [x] UPS #2 (CyberPower OR500LCDRM1U) identified and configured
    2026-08-29, after the Lenovo's permanent relocation put all three
    units within USB reach. Pinned by serial (`GA4KS2000999`, a distinct
    format from the two CP1500PFCLCD units' `CXXR...` serials, confirming
    it's a different physical unit/model as expected) as NUT device
    `network-ups`. Confirmed via `upsc network-ups@localhost`:
    `device.model: OR500LCDRM1Ua`, `ups.status: OL`, `battery.charge: 100`,
    `ups.realpower.nominal: 300`. Unlike the other two (still `ups.load:
    0`, nothing plugged in), this one already shows **`ups.load: 23`** —
    real equipment (Arista switch, OPNsense, UniFi PoE switch) is already
    drawing from it, so this is now live production load, not a bench
    test. `upsmon.conf` extended with a `MONITOR` line for `network-ups`
    reusing the existing `upsmon` account; verified via `ss` showing three
    established loopback pairs to `upsd` (six connections). All three UPS
    units are now NUT clients: `proxmox-ups`, `nas-ups`, `network-ups`.
- [x] Document the physical power topology and safe runtime assumptions.
  Recorded 2026-08-29 in Section 6 below: all three NUT-monitored units
  are live, on-line, and carrying real load. `nas-ups` has the shortest
  runtime (~22.5 min) despite matching `proxmox-ups`'s nominal capacity,
  because it's serving three NAS-class devices at once — the key fact
  Milestone 3's shutdown-threshold work needs to account for.
- [x] Install NUT directly on the utility host and configure least-privilege users.
  NUT 2.8.1-5 installed. A dedicated `upsmon` account (`primary` role,
  randomly generated password) was added to `upsd.users` 2026-08-28 and
  granted only monitoring/shutdown-signal privileges — no admin/instcmd
  access. `upsmon.conf` has `MONITOR` entries for both `proxmox-ups` and
  `nas-ups` using that account. Verified via `ss`: two established
  loopback connections to `upsd` (port 3493), matching both monitored
  units, and the standard NUT privilege-separation process model (parent
  `upsmon` runs as `root`, child de-escalates to the `nut` user). The
  actual password is not recorded anywhere in this repository — it lives
  only in `/etc/nut/upsd.users` and `/etc/nut/upsmon.conf` on the NUT
  server (root:nut, mode 640). No `SHUTDOWNCMD` is configured yet —
  deliberately deferred to Milestone 3, since real shutdown triggers and
  ordering haven't been decided.
- [x] Prove both UPS devices are detected consistently after reboot.
  Reboot test performed 2026-08-29 with all three units connected: all
  three `nut-driver@*` instances, `nut-server`, `nut-monitor`, and
  `beszel-agent` came back **automatically** with no manual intervention.
  Confirmed each driver bound to its correct serial after re-enumeration
  (`proxmox-ups` → `CXXRO7009593`, `nas-ups` → `CXXRP7016137`,
  `network-ups` → `GA4KS2000999`) — proving the serial-pinning approach
  is robust to USB re-enumeration order changing across boots. `upsmon`
  re-established all six expected loopback connections to `upsd`, and
  Lab Doctor's `check_nut` passed cleanly afterward.

### Milestone 3 — Coordinated shutdown

- [x] Define warning and shutdown thresholds from measured runtime.
  Implemented 2026-08-29 via `override.battery.charge.low` in
  `ups.conf` — overrides each unit's hardware-reported low-battery
  signal (~10% default) with a per-unit value derived from measured
  runtime *and* cross-UPS dependencies, not just each unit's own
  battery budget:
  - `nas-ups` = **50%** (~11 min of its 22.5 min budget) — least
    runtime, and losing it breaks local switching (Arista), so it gets
    the earliest, most generous trigger.
  - `proxmox-ups` = **80%** (~12 min of its 61 min budget) — despite
    having the most runway, its threshold is **not** driven by its own
    battery. Its shutdown script SSHes to both Synology units, and
    that traffic transits Arista (on `nas-ups`). Since TrueNAS's
    `powerdown: false` means Arista keeps drawing from `nas-ups`'s
    battery independent of TrueNAS's own shutdown timing, Proxmox's
    trigger has to fire close to `nas-ups`'s own timing, not late into
    its own budget, or Arista could plausibly be dead before the
    script tries to reach Synology.
  - `network-ups` = **25%** (~29 min of its 36 min budget) — powers
    the orchestrator (the Lenovo) itself and has no downstream
    SSH-dependency problem, so it can wait the longest, keeping
    monitoring alive as long as reasonably possible.

  Applied via `sed` anchored on each unit's unique USB serial (not a
  range match, learning from the earlier range-boundary bug) — verified
  all three drivers report their correct overridden value via `upsc`,
  and all services (drivers, `nut-server`, `nut-monitor`, both remote
  clients) reconnected cleanly afterward. **The percentages themselves
  are reasoned from topology and measured runtime, not field-validated
  as "correct" — Jason's own words: "we won't know until it's field
  tested." Treat as a considered starting point, to be revisited after a
  real outage.** The *mechanism* (that these thresholds actually trigger
  `LB` at all) was validated the same day — see the simulated test under
  "Configure and validate Proxmox shutdown behaviour" below, which
  caught a real gap (`override.battery.charge.low` alone doesn't work
  without `ignorelb`) before it could fail silently during a real
  outage.
- [x] Configure and validate Proxmox shutdown behaviour.
  **Configured 2026-08-29, not yet live-tested.** The Lenovo's `nut.conf`
  switched to `MODE=netserver` with explicit `LISTEN 192.168.50.25 3493`
  in `upsd.conf` (the default with no `LISTEN` lines was loopback-only,
  regardless of `MODE`). A `netclient` secondary-role account was added
  to `upsd.users`. Proxmox now runs `nut-client`, configured as a network
  `secondary` monitoring `proxmox-ups@192.168.50.25`. New OPNsense rules
  were needed for: TrueNAS (Servers VLAN 20) → NUT server (Management
  VLAN 50) port 3493; and separately, Proxmox's host management IP
  (`192.168.50.10`, itself on Management VLAN 50) → both Synology units
  (Servers VLAN 20) port 22 — this second one was unexpected, since it's
  a same-VLAN-to-cross-VLAN path unrelated to the NUT traffic itself.

  A custom `SHUTDOWNCMD` script (`/usr/local/bin/nut-shutdown.sh` on
  Proxmox) is wired in, replacing the package's stock default
  (`/sbin/shutdown -h +0`) which a naive `grep -q` check nearly left in
  place unnoticed — worth remembering to always positively verify what a
  config-presence check actually matched, not just that something
  matched. The script: stops Frigate VM 102 first (its NFS mount depends
  on TrueNAS), stops all other guests in parallel, SSHes into both
  Synology units to shut them down, then powers off Proxmox itself.
  Logs to `/var/log/nut-shutdown.log`.

  Synology shutdown uses Proxmox's own existing root SSH keypair
  (already auto-generated by Proxmox for cluster use — no new key
  generated), added to the `Jason` account's `authorized_keys` on both
  `gowest` and `gowest-backup` (the same automation-purposed account and
  `/etc/ssh/authorized_keys/%u` path Project 1 already established).
  Since an unattended trigger has no one to type a sudo password, both
  Synology units also got a narrowly-scoped `NOPASSWD` sudoers entry
  (`Jason ALL=(root) NOPASSWD: /sbin/shutdown -h now`) via a safe
  `/etc/sudoers.d/nut-shutdown` drop-in — DSM has no `visudo`, so a
  drop-in was used instead of hand-editing `/etc/sudoers` directly (a
  drop-in fails safe on bad permissions/syntax; the main file does not).

  **Incident, self-caught and fixed:** a verification `grep` command
  during setup printed the `netclient` account's full `MONITOR` line,
  including its password, into this session's own context/transcript —
  exactly what the never-echo-secrets pattern used everywhere else in
  this project was meant to prevent. Treated as exposed and rotated
  immediately (new random password generated, updated in both
  `upsd.users` and Proxmox's `upsmon.conf`, both services restarted,
  reconnection confirmed). No secret value is recorded in this
  repository at any point — only in the config files themselves and,
  briefly, this session's conversation history.

  **Validated 2026-08-29** via a safe simulated test, per Section 20's
  staged-testing approach: `SHUTDOWNCMD` was temporarily swapped for a
  harmless logging command (a technique suggested directly in NUT's own
  `upsmon.conf` comments), then `proxmox-ups` was briefly unplugged from
  the wall for real. Confirmed live: `OB` detection worked immediately;
  `battery.charge` genuinely dropped in real time under real discharge.

  This surfaced an important gap: at 79% (below the 80%
  `override.battery.charge.low` threshold), `ups.status` still showed
  no `LB` flag. Per NUT's own documentation, `override.battery.charge.low`
  **only changes the displayed value** — it does not by itself make the
  driver compute `LB` from charge. The missing piece is `ignorelb`, which
  tells the driver to disregard the UPS's native hardware low-battery
  signal and instead compute `LB` itself from `battery.charge <
  battery.charge.low`. Added `ignorelb` to all three `ups.conf` sections
  (anchored on each unique `override.battery.charge.low = N` line, same
  safe-anchoring approach as the serial-based inserts). Confirmed
  immediately afterward — no further battery draining needed — that
  `proxmox-ups` correctly showed `LB` at 78% charge, including while
  still `OL CHRG` (on mains), proving the comparison is purely
  charge-based and independent of on-battery state. Since this fix lives
  at the driver/`ups.conf` level on the Lenovo, it applies automatically
  to TrueNAS's view of `nas-ups` too — no separate fix was needed there.

  Plugged `proxmox-ups` back in once `OB` and the charge drop were
  confirmed (didn't drain further chasing the `LB` diagnostic on live
  production hardware). `SHUTDOWNCMD` reverted to the real script
  afterward, confirmed active. Jason's call: the actual `upsmon`
  OB+LB→FSD→`SHUTDOWNCMD` invocation chain wasn't separately re-tested
  after the `ignorelb` fix — accepted as sufficiently validated given
  that specific behavior is extremely standard, well-established NUT
  functionality, not something specific to this setup. What *was*
  hardware/setup-specific (real `OB` detection, and `LB` actually
  computing from our chosen threshold) is now proven.
- [x] Configure and validate applicable NAS/storage shutdown behaviour.
  Validated by the same 2026-08-29 test above, since the `ignorelb` fix
  lives at the shared driver level (`nas-ups`'s `ups.conf` section on the
  Lenovo) and TrueNAS's native client just reads whatever `upsd` reports
  — no TrueNAS-specific re-test was needed for the threshold mechanism.
  TrueNAS's own native shutdown behavior itself (as opposed to the
  trigger mechanism) has not been separately live-tested.
  **Configured 2026-08-29, not yet live-tested.** TrueNAS SCALE has a
  native `ups` service built into its middleware (`midclt`), used
  directly instead of installing a separate `nut-client` package — it
  wraps NUT internally and manages its own config, so a manual install
  would risk conflicting with what TrueNAS already owns. Configured via
  `midclt call ups.update`: `mode: SLAVE` (TrueNAS's client-mode
  terminology, unchanged from older NUT naming even though NUT itself
  moved to primary/secondary), `identifier: nas-ups`,
  `remotehost: 192.168.50.25`, reusing the same `netclient` account as
  Proxmox. Deliberately set `shutdown: LOWBATT` (wait for the real
  low-battery signal, not just "on battery") and `powerdown: false`
  (TrueNAS shuts itself down, but never tells the UPS to cut its own
  outlet power — that would also kill the Arista switch sharing
  `nas-ups`). No custom shutdown command — TrueNAS's own native graceful
  shutdown (clean ZFS export, etc.) is used as-is. The `ups` service also
  had to be explicitly enabled (`service.update ups {"enable": true}`) —
  starting it alone doesn't persist across a TrueNAS reboot.

  **Second self-caught credential exposure:** `midclt call ups.update`
  returns the full updated config as its response, including `monpwd` in
  plaintext — this printed into the session the same way the earlier
  `netclient` exposure did, from the same underlying habit (not
  suppressing output on a command that could echo a secret, not just the
  final verification step). Rotated again immediately across all three
  places the credential lives (`upsd.users`, Proxmox's `upsmon.conf`,
  TrueNAS's `ups.update`), this time with every command's output
  redirected to `/dev/null` and verification limited to fields that can
  never contain the secret. Worth remembering going forward: any command
  that *sets* a secret via an API that echoes back the full object needs
  the same output suppression as commands that *read* one.
- [ ] Document final shutdown order, return-of-power behaviour and manual override.

### Milestone 4 — Monitoring and recovery

- [x] Add the utility host to Beszel and expose only required read-only UPS metrics.
  Beszel agent (official `henrygd/beszel` installer from `get.beszel.dev`,
  checksum-verified release binary, dedicated low-privilege `beszel`
  service user) installed on `nut-server` 2026-08-28 and registered with
  the hub at `192.168.20.20:8090`. Live host-level metrics (CPU, memory,
  disk, temperature, uptime) confirmed actively updating in the Beszel
  dashboard. This required a new OPNsense firewall rule permitting
  `192.168.50.25` (Management VLAN 50) → `192.168.20.20:8090` (Servers
  VLAN 20) — Jason added this himself, since OPNsense/firewall changes
  are outside this project's scope (Section 23). Beszel provides
  host-level monitoring only; it has no NUT/UPS-specific telemetry
  (battery charge, `ups.status`, etc.) — that remains covered by `upsc`
  and Lab Doctor's `check_nut`, consistent with this repo's existing
  Beszel-vs-deeper-metrics division of responsibility (Section 15).
- [x] Add actionable power/NUT checks and alerts to HomeLab Doctor/reporting.
  Added `check_nut()` to [scripts/doctor.sh](../scripts/doctor.sh) 2026-08-28,
  following the existing `check_*` conventions (SSH via the `nut` alias in
  `~/.ssh/config`, `pass`/`warn`/`fail` helpers, failures/warnings arrays).
  Checks: `nut-server` and `nut-monitor` services active, both `proxmox-ups`
  and `nas-ups` detected via `upsc -l`, each unit's `ups.status` contains
  `OL` (fails if not — e.g. on battery or communication lost), and warns if
  `battery.charge` drops below 50%. Tested against the live server: passes
  cleanly today (`NUT server, monitor and both UPS units healthy`).
  Note: this only covers the two desk-connected units; UPS #2 will need
  adding to `expected_ups` once it's identified/connected.
- [x] Protect NUT configuration and document bare-metal recovery.
  Documented in [05-Backups.md](../05-Backups.md) under "NUT / UPS Server
  (Lenovo)" 2026-08-28: a manual pull command lands `ups.conf`, `nut.conf`,
  `upsd.users` (contains the real `upsmon` password), `upsmon.conf`, the
  SSH hardening drop-in, and network/hostname info directly into
  `~/lab/private-backups/nut/<timestamp>/` on the Mac — already inside the
  existing daily Backup Synology pull and encrypted IDrive e2 off-site
  task, so no new automation was needed. A first verified baseline was
  pulled and spot-checked. `check_backup_age "NUT" ...` added to
  `scripts/doctor.sh` to flag staleness. Bare-metal recovery procedure
  (reinstall Debian, restore configs, re-enable services) is documented
  but not yet tested end-to-end.

  **Caught and fixed while pulling this backup:** an earlier `sed` command
  used to pin `proxmox-ups`'s serial (see the upsd/upsmon entry above) had
  a bug — its end-of-range pattern (`/^desc = /`) assumed no leading
  whitespace, but every directive in `ups.conf` is indented 4 spaces, so
  the range never closed and ran to end-of-file. This caused
  `proxmox-ups`'s serial to also get inserted into `nas-ups`'s section
  (harmlessly shadowed by `nas-ups`'s own correct serial line already
  present below it, since NUT's parser takes the last matching directive
  in a section — confirmed via `upsc nas-ups` reporting the correct serial
  throughout). Fixed with a context-anchored `sed` deletion targeting only
  the duplicate line, followed by a driver/server restart; both units
  re-verified via `upsc <name>@localhost ups.serial` reporting their own
  correct serial.
- [ ] Perform controlled failure, shutdown and recovery tests.
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

### Power topology (recorded 2026-08-29, post-relocation; equipment mapping corrected same day)

All three NUT-monitored units are `OL` (on line, mains present) with 100%
battery charge at the time of recording. Load and runtime figures are
live snapshots from `upsc`, not fixed specs — they'll shift as equipment
changes, but give a real baseline for Milestone 3's threshold planning.

**The equipment-to-UPS mapping below is the corrected, final distribution
— it differs from what was originally planned.** Jason redistributed
load across the three active units to work within physical/cabling
constraints; do not trust equipment assignments recorded earlier in this
document (e.g. in the Milestone 2 tracker entries above) over this table.

| UPS | NUT name | Protected equipment | Capacity | Current load | Runtime at current load |
|---|---|---|---|---:|---:|
| UPS #1 — APC Back-UPS Pro BN1500M2-CA | *(none — dumb battery, no NUT interface)* | Nothing currently — final disposition (retire/repurpose) still undecided | 1500VA | Not visible to NUT | Not visible to NUT |
| UPS #2 — CyberPower OR500LCDRM1U | `network-ups` | OPNsense, **the Lenovo NUT server itself**, UniFi PoE switch, camera switch | 500VA / 300W nominal | 23% (~69W) | ~2175s (~36 min) |
| UPS #3 — CyberPower CP1500PFCLCD | `proxmox-ups` | Proxmox (Dell Precision T5810) **and both Synology units** | 1500VA / 1000W nominal | 12% (~120W) | ~3675s (~61 min) |
| UPS #1 replacement — CyberPower CP1500PFCLCD | `nas-ups` | TrueNAS **and the Arista core switch** | 1500VA / 1000W nominal | 33% (~330W) | ~1350s (~22.5 min) |

This corrected mapping changes the dependency picture significantly from
the original plan:

- **`network-ups` is now the most structurally critical unit**, not just
  the one with the least headroom. It powers OPNsense *and the Lenovo
  running NUT itself* — if it dies, monitoring and any future automated
  shutdown orchestration end at the same moment as the gateway does.
  Section 11's "storage before hypervisor" ordering logic doesn't
  directly apply here; this unit needs to be treated as a hard
  precondition for the whole coordinated-shutdown system to function at
  all, not just another tier in the sequence.
- **`nas-ups` carries the Arista core switch**, so losing it breaks local
  network switching for everything on the LAN, not just TrueNAS storage
  availability. It also still has the shortest measured runtime (~22.5
  min) of the three, which makes it doubly time-constrained.
- **Proxmox and both Synology units now share one UPS** (`proxmox-ups`).
  Jason is about to triple Proxmox's RAM and add a substantial GPU —
  today's measured 12%/~120W load should **not** be treated as a stable
  planning baseline. Re-measure runtime on this unit once that hardware
  upgrade lands, before finalizing Milestone 3 thresholds around it.
- Frigate (Proxmox VM 102) still depends on TrueNAS via NFS for its
  recordings storage, even though the physical UPS pairing changed —
  that cross-UPS dependency (`proxmox-ups` compute → `nas-ups` storage)
  is unaffected by this correction and still needs to be accounted for
  in shutdown ordering.

The APC BN1500M2-CA's final disposition (retire vs. repurpose as a
dumb-battery elsewhere) is still undecided — it currently has no
protected equipment assigned to it and is not part of the live topology
above.

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
- [x] Both UPS units positively identified.
- [x] UPS-to-device power topology documented.
- [ ] UPS management connections attached to Lenovo.
- [x] Both UPS devices reliably detected after reboot.
- [ ] NUT installed on bare metal.
- [ ] NUT server securely configured.
- [ ] Appropriate NUT clients configured.
- [ ] Proxmox shutdown behaviour implemented and tested.
- [ ] Applicable NAS shutdown behaviour implemented and tested.
- [ ] Shutdown ordering documented.
- [ ] Power-return behaviour understood and documented.
- [x] Lenovo added to Beszel.
- [ ] UPS monitoring integrated into existing observability where practical.
- [ ] Appropriate alerts implemented or explicitly deferred.
- [x] Lab Doctor extended for UPS/NUT health.
- [x] Lenovo/NUT configuration included in backup strategy.
- [x] Restore procedure documented.
- [x] Secrets excluded from public Git.
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
