# Lab Health Check and Remediation — 2026-09-23

> Requested by Jason ("run a thorough system check … make suggestions", then
> "Do all"). A read-only sweep came first (HomeLab Doctor plus deeper
> host/guest/network checks). The approved fixes were then applied one at a
> time, each with a rollback point. TrueNAS storage was excluded at Jason's
> request because old-drive testing is in progress; the SMART and
> uncorrectable-error alerts on the spare ST4000NM0023 drives come from that
> testing, not from the Media pool.

## Findings (read-only sweep)

| Area | Finding | Disposition |
|---|---|---|
| Doctor: NetBox | "login page HTTP 302" | Not a fault. NetBox moved behind Authentik on 2026-09-23. The check has been updated |
| Doctor: TrueNAS Media 93% | Known | Excluded (SAS expansion project) |
| Doctor: Jellyfin integrity backup 196h | The exporter existed but nothing scheduled it | Fixed |
| Doctor: news feed failures | One dpreview timeout and one item-summary timeout | No action |
| Proxmox host | 110 pending packages, incl. 12 security, kernel 7.0.14-8 → -19 and pve-manager 9.2.10 → 9.2.20 | Patched and rebooted |
| LXCs | Most had 18–21 security updates pending; no automatic updates anywhere | Patched; security-only automatic updates enabled |
| LXC 112 backup relay | Cannot reach Debian mirrors; packages last refreshed 2026-07-14 | **Open:** needs a firewall/egress decision |
| Frigate VM 102 | 15 pending updates | Patched (kernel meta-packages deliberately held) |
| Aster wiki collector (LXC 113) | Exits as failed daily since at least 09-18; 7 sources quarantined for upstream commit mismatch; Doctor did not notice | Doctor now warns. **Open:** a reviewed re-pin of the seven sources |
| OPNsense 26.7.1 | `pkg audit` flags Unbound, OpenSSL, OpenSSH, OpenVPN, strongSwan and Python; 82 package updates including base and kernel | See OPNsense section |
| OPNsense gateways | WAN gateway monitoring is disabled (no delay or loss data) | **Open:** a one-click GUI change for Jason |
| Claude Code sandbox | SSH to allowlisted lab IPs fails inside the sandbox | Explained below. **Open:** Jason's decision |
| Docker LXC 100 | 2.27 GB of unused images | Pruned |
| Proxmox thin pool | Provisioned 1.03 TiB against a 930 GiB pool; 23% actually used | Watch. `prepatch-20260923` snapshots add to it; remove them once patching is accepted |
| No-nesting LXCs 108/109/112 | Boot-time `dev-mqueue.mount`/`run-lock.mount` failures | No action; harmless (same AppArmor cause as the earlier `tmp.mount` fix) |

## Changes applied

### Repository
- `scripts/doctor.sh`:
  - The NetBox check accepts a 302 to `https://netbox.elliottrook.com/…`
    and then requires `authentik-netbox-ingress` to be running.
  - The wiki check warns when the collector's latest run failed or
    quarantined any sources. It reads the persistent journal, because
    systemd's `Result` resets when the container reboots.
- `scripts/lab`: new `lab backup jellyfin-integrity` target, also part of
  `lab backup all`.
- `docs/05-Backups.md`: the weekly job now runs seven exporters.

### Mac
- `~/Library/LaunchAgents/ca.yampy.homelab-weekly-backup.plist`: appended
  `jellyfin-integrity.sh` (last, because the chain uses `&&`), then
  reloaded with `launchctl bootout`/`bootstrap`. The original is saved in
  the session scratchpad. The exporter was run once manually: success.

### Proxmox guests (`apt-get upgrade`, `--force-confold`, no removals)
- Each LXC was snapshotted as `prepatch-20260923` first; LXC 112's
  snapshot failed, and its nightly vzdump is the fallback.
- Health was compared before and after: failed units and Docker running
  or unhealthy counts.
- Upgraded (package counts): 113 (59), 114 (39), 116 (40), 109 (54),
  108 (62), 104 (68), 111 (67), 115 (49), 100 (73), 101 (66), 107 (59),
  106 (44), 110 (53). LXC 112: 0, because it has no mirror access.
- **LXC 110 GPU stack held** (`apt-mark hold`): libdrm*, libllvm19,
  libvulkan1, mesa-vulkan-drivers, vulkan-tools. `aster-llama` stayed
  active and `check-aster-b60.sh` passed. Update these deliberately, with
  the B60 check, and `apt-mark unhold` afterwards.
- Rollback: `pct rollback <id> prepatch-20260923`.
- Verified afterwards: UniFi (Java and 11443 up), Pi-hole resolving, and
  NPM ingress (`auth`/`netbox` 302 to Authentik, `aster` 200).

### Automatic security-only updates (13 LXCs; all except 112)
- `unattended-upgrades` 2.12, with `/etc/apt/apt.conf.d/20auto-upgrades`
  and `52homelab-security-only`.
- `#clear` resets the origin list; the only allowed origin is
  `origin=Debian,codename=${distro_codename}-security,label=Debian-Security`.
- No automatic reboot, and no automatic removal of dependencies.
- LXC 110 also has `53homelab-gpu-stack`, a package blacklist for the
  Mesa/Vulkan/libdrm/LLVM/Intel stack.
- Verified with `unattended-upgrade --dry-run -d` ("Allowed origins").
- Docker-CE and other third-party repositories are not auto-updated.
- Rollback: `apt-get purge unattended-upgrades` and remove the two or three
  config files.

### Frigate VM 102
- Snapshot `prepatch-20260923` taken. Patched through the QEMU guest agent,
  as Jason approved, because `sudo` on the VM requires a password.
- The first attempt was interrupted: upgrading `qemu-guest-agent` restarts
  the agent, which killed the agent-spawned apt. It was completed with
  `systemd-run` (`dpkg --configure -a`, then `apt-get -f install` and
  `upgrade`). `dpkg --audit` is clean.
- `linux-image-amd64`/`linux-headers-amd64` were held back by `upgrade`.
  The VM has PCI passthrough, so update its kernel deliberately.
- The Frigate container is healthy.

### Proxmox host
- Before: host config backup (`scripts/backup/proxmox.sh`) and the list of
  running guests.
- `apt-get dist-upgrade`: 110 upgraded, 2 new, 0 removed, exit 0.
  pve-manager is 9.2.20.
- Rebooted into **7.0.14-19-pve**. 7.0.14-8 and 7.0.2-6 remain installed
  as fallbacks (GRUB boot; pin with
  `proxmox-boot-tool kernel pin 7.0.14-8-pve` if needed).
- After: all 14 LXCs and VMs 102/103 running (the same set as before),
  the B60 bound to `xe`, and no failed host units.

### Docker LXC 100
- `docker image prune -a -f` reclaimed 2.27 GB. All 9 running containers
  are unaffected. The stopped `code-server-pre-authentik` rollback
  container and its image are kept until the Authentik rollout graduates.

## Follow-up changes (Jason's decisions, 2026-09-23)

### OPNsense firmware 26.7.1 → 26.7.4_1
- Config backup taken first (`opnsense-config-2026-09-23_20-41-30.xml`)
  plus ZFS boot environment **`pre-update-20260923`** (rollback: select it
  at the console or run `bectl activate pre-update-20260923`). The boot
  environment is kept.
- `configctl firmware update`: 82 packages including base and kernel
  (FreeBSD 15.1-RELEASE-p3), then an automatic reboot.
- `pkg audit` dropped from six flagged packages to one (python313).
- Doctor afterwards: internet, DNS and WAN all pass.

### WAN gateway monitoring enabled
- WAN_DHCP was an automatic gateway with monitoring disabled by default.
  A stored `gateway_item` was created through OPNsense's own
  `OPNsense\Routing\Gateways` model (validated as the GUI would):
  `gateway=dynamic`, `defaultgw=1`, `monitor_disable=0`,
  `monitor=1.1.1.1`. It was then applied with `rc.routing_configure`.
- Verified: dpinger is running, WAN_DHCP shows 5.3 ms and 0.0% loss, and
  the default route is unchanged. The added 1.1.1.1 host route goes via
  WAN.
- Rollback: delete the WAN_DHCP entry in System → Gateways →
  Configuration, or restore the 20:41 config backup.

### Apt proxy for LXC 112 (closes the "cannot reach Debian mirrors" item)
- `apt-cacher-ng` 3.7.5 on **LXC 100 (192.168.20.20:3142)**. LXC 112 is on
  the same VLAN 20, so **no OPNsense rule was needed**.
- Configured in `/etc/apt-cacher-ng/zz-homelab.conf`:
  - binds only 192.168.20.20 and 127.0.0.1;
  - `ForceManaged: 1`, so only known Debian repositories are served;
  - `PassThroughPattern: ^$`, so there are no HTTPS tunnels;
  - `UseWrap: 1` (libwrap linked), with `/etc/hosts.allow` set to
    `apt-cacher-ng: 192.168.20.33 127.0.0.1` and `/etc/hosts.deny` to
    `apt-cacher-ng: ALL`.
- Verified:
  - LXC 112 fetches Debian indexes through the proxy;
  - a non-Debian URL returns `403 Forbidden file type or location`;
  - NetBox LXC 111 and TrueNAS get connection resets.
- LXC 112: `/etc/apt/apt.conf.d/01homelab-proxy` points at the proxy.
  - Patched 49 packages; health unchanged; the IDrive relay timer is
    intact.
  - Security-only unattended-upgrades are enabled, so **all 14 LXCs**
    now have them.
  - Rollback: this morning's vzdump (`vzdump-lxc-112-2026_09_23-02_44_27`),
    since 112 cannot be snapshotted because of its bind mount.
- Rollback for the proxy: `apt-get purge apt-cacher-ng` on LXC 100, remove
  the hosts.allow/deny lines, and remove 112's `01homelab-proxy`.

### Claude Code sandbox: `sandbox.excludedCommands: ["ssh", "scp"]`
- Rationale: the sandbox's network proxy is HTTP(S)-only and `NO_PROXY`
  covers 192.168.0.0/16, so the macOS sandbox blocks every SSH connection
  to lab IPs even though they are on the allowlist. Every SSH call had to
  run through an extra unsandboxed-approval step, and a timed-out prompt
  of that kind silently dropped steps during this session.
- Excluding `ssh`/`scp` from the sandbox keeps the real control intact:
  the `permissions` rules still decide. Read-only `ssh <host> cat/ls/...`
  forms are allowed, and every other `ssh`/`scp` asks, via
  `"ask": ["Bash(ssh:*)", "Bash(scp:*)"]`.
- Trade-off: SSH egress is no longer restricted by `allowedDomains`. The
  destination is bounded by the approval prompt and the SSH keys and
  config instead.
- Rollback: remove the `excludedCommands` line.
- It takes effect from the next Claude Code session; it was not live in the
  session that added it.

### Snapshot cleanup
- Removed the `prepatch-20260923` snapshots from LXCs 100, 101, 104, 106,
  107, 108, 109, 110, 111, 113, 114, 115 and 116 and from VM 102. None
  remain, and pve/data is at 24% data. Rollback from here is the nightly
  vzdump backups.

### Aster wiki re-pin
- Jason chose to ignore it for now. Doctor keeps warning while sources are
  quarantined.

## Held-back items completed (Jason: "do the worth doing and deliberately held back stuff now")

### UPS runtime re-measured (read-only `upsc`, approved)
- `proxmox-ups` 14%/~51 min (unchanged from 09-02).
- `nas-ups` 40%/~17 min, attributed to the spare drives under test.
- `network-ups` 25%/~32 min.
- Details are in `CLAUDE.md`.

### Doctor: `check_apt_proxy`
- Fails if apt-cacher-ng on LXC 100 is down, or if LXC 112 cannot fetch
  Debian's `InRelease` through it. The fetch is a raw HTTP HEAD via
  `/dev/tcp`, because 112 has no curl.
- Warns if 112's package lists are older than 48h.
- Verified passing against live state.

### LXC 110 GPU stack (deliberate update)
- Snapshot `gpu-stack-20260923` taken, then holds released on libdrm*,
  libllvm19, libvulkan1, mesa-vulkan-drivers and vulkan-tools.
- The only pending update was **mesa-vulkan-drivers 26.1.2 → 26.1.6**
  (trixie-backports). It was installed and `aster-llama` restarted.
- `check-aster-b60.sh` passes: `xe` binding, Vulkan sees BMG G21.
- The first post-restart request was slow (1.0 tokens/s decode), consistent
  with the driver update invalidating the Vulkan pipeline/shader cache.
  Subsequent throughput is verified from real traffic.
- **Evidence (04:13–05:0x UTC 2026-09-24):** five real short requests after
  the update decoded at 6.23–6.46 tokens/s, against 6.29–6.42 before it,
  and prefilled at 22–69 tokens/s, against 29–37 before. There was no
  regression.
- The `gpu-stack-20260923` snapshot (LXC 110) and the `kernel-20260923`
  snapshot (VM 102) were then removed; the thin pool is at 24.16% data and
  1.04% metadata.
- The unattended-upgrades GPU blacklist (`53homelab-gpu-stack`) remains, so
  future GPU-stack updates stay deliberate. The apt holds were not
  re-applied.
- Rollback now: re-install `mesa-vulkan-drivers=26.1.2-1~bpo13+1` if it is still in the archive, or restore from vzdump. The snapshot was removed after verification.

### Frigate VM kernel 6.12.101 → 6.12.107
- Snapshot `kernel-20260923` taken. The new kernel and headers were
  installed via the guest agent plus `systemd-run`.
- The Coral Edge TPU (`1ac1:089a`) uses the `apex`/`gasket` DKMS module.
  **The DKMS rebuild for 6.12.107 was confirmed before rebooting**
  (`dkms status`; `apex` vermagic 6.12.107).
- Afterwards: running 6.12.107, `apex`/`gasket` loaded, `/dev/apex_0`
  present, Frigate container healthy, log shows "TPU found".
- Fallback kernels 6.12.101 and 6.12.94 remain in GRUB.
- Rollback now: boot 6.12.101 from GRUB. The snapshot was removed after the Coral and Frigate were verified.

### OPNsense python313
- A firmware check found no updates available. python313-3.13.15 stays
  flagged by `pkg audit` until OPNsense ships a fix.

## Open items needing Jason

1. ~~**LXC 112 package access:**~~ Resolved with the apt proxy above.
   Originally: **LXC 112 package access:** it cannot reach deb.debian.org or
   security.debian.org, so it has not been patched since 2026-07-14.
   Options:
   - a narrow OPNsense allow rule to the Debian mirrors;
   - an apt proxy on another guest;
   - periodic patching through a temporarily opened path.
2. ~~**OPNsense WAN gateway monitoring:**~~ Enabled above. Originally:
   **OPNsense WAN gateway monitoring:** in System → Gateways →
   Configuration → WAN_DHCP, untick "Disable Gateway Monitoring" and set
   a monitor IP (for example a public resolver). This gives outage and
   latency history and makes dpinger meaningful.
3. **Aster wiki re-pin review** (deferred; Jason: ignore for now): seven sources, all pinned to `master`,
   are quarantined because upstream moved. The design requires a reviewed
   re-pin that checks the new upstream content still matches the deployed
   versions (Proxmox 9.2, TrueNAS 25.10.5, Jellyfin 10.11, and so on).
   Partial review, 2026-09-23:
   - OPNsense docs: 2 commits, none within the source boundary.
   - TrueNAS docs: 8 commits, 1 boundary file (+10 lines,
     `ManagingDatasets.md`).
   - The rest were not assessed, because the sandbox proxy truncates large
     GitHub compare responses.
4. ~~**Claude Code sandbox and SSH:**~~ Applied above. Originally:
   **Claude Code sandbox and SSH:** the sandbox proxy carries HTTP(S) only,
   and `NO_PROXY` includes 192.168.0.0/16. So SSH to allowlisted lab IPs
   is blocked by Seatbelt, and every SSH call needs an unsandboxed approval
   prompt. The only effective setting is `sandbox.excludedCommands`
   (`ssh`, `scp`). That runs SSH outside the sandbox without the
   per-command prompt, but it also stops the domain allowlist applying to
   SSH. The trade-off is Jason's call; the settings file is protected from
   Claude's writes.
5. ~~**Cleanup after acceptance:**~~ Done above. Originally:
   **Cleanup after acceptance:** remove the `prepatch-20260923` snapshots
   (13 LXCs and VM 102) once the patched state is accepted
   (`pct delsnapshot <id> prepatch-20260923`,
   `qm delsnapshot 102 prepatch-20260923`).
