# Infrastructure Resilience and Operations Hardening

> Status: Approved — Stream A (2026-09-24). Hardware (H1) postponed while
> Jason looks for deals; hardware-independent workstreams may start.
>
> Owner: Jason | Proposed: 2026-09-24 | Stream A — Autonomous (approved
> 2026-09-24)
>
> Origin: the recommendations from the 2026-09-23 lab health check
> ([Lab health remediation runbook](../runbooks/Lab-Health-Remediation-2026-09-23.md)).

## Purpose and desired outcome

Make the lab survive the routine events that exposed its weak points on
2026-09-23:

1. **Recovery that is faster, verified and complete.** Backups should be
   deduplicated, incremental and integrity-checked, with file-level restore,
   and should cover every guest, including those with bind mounts.
2. **No single maintenance action takes everything down.** Patching or
   rebooting the one Proxmox host should not stop DNS, reverse proxying and
   sign-in for the whole household at the same time.
3. **Scheduled operations do not depend on a laptop.** Doctor, the weekly
   configuration exports and the Aster lab worker should run on always-on
   infrastructure.
4. **Changes happen deliberately.** Container images are pinned, and new
   releases are announced rather than silently pulled.
5. **Drift and failures are noticed early:**
   - patch and reboot drift appear in Doctor;
   - failures reach Jason's phone;
   - script errors are caught before they reach the live lab.

This project hardens the existing lab; it does not re-platform it.

**Design chosen by Jason (2026-09-24): one small second node.** PBS, the
standby critical-path services and the ops runner all run on a single,
independent small-form-factor host. It shares no hardware with the primary
Proxmox host or TrueNAS. This collapses the original decisions D1–D3 into
one design.

## Current state and evidence (2026-09-23)

- **One Proxmox host** (E5-2698 v4, 80 GB RAM, pve-manager 9.2.20, kernel
  7.0.14-19) runs everything on the critical path:
  - LXC 100: primary Pi-hole, Homepage, Portainer;
  - LXC 106: Authentik;
  - LXC 107: NPM and cloudflared;
  - LXC 108: Forgejo;
  - LXC 104/110/116: Aster;
  - VM 103: Home Assistant;
  - VM 102: Frigate.

  The 2026-09-23 host reboot stopped all of them together. The secondary
  Pi-hole on TrueNAS kept DNS working; nothing else has a standby.
- **Backups:** nightly `vzdump` at 02:30 to the `backups` directory storage
  on the same host (3.8 TB, 18% used), then pulled to TrueNAS and pushed
  encrypted to IDrive via LXC 112. There is no deduplication, no
  incremental chain, no scheduled verification and no file-level restore.
  LXC 112 (bind mount) cannot be snapshotted. A one-off backup of LXC 104
  failed on 2026-09-23 (`tar` exit 2).
- **Scheduling on the Mac:**
  - `ca.yampy.homelab-report` (daily 08:15, Doctor and report);
  - `ca.yampy.homelab-weekly-backup` (Sunday 06:00, seven config
    exporters);
  - `com.jason.aster-lab-worker`;
  - `com.jason.homelab.aster-knowledge-review`.

  All four depend on the Mac being awake, with the repository at
  `$HOME/lab/homelab` and Jason's SSH aliases.
- **Unpinned images** on LXC 100: `homepage:latest`,
  `portainer-ce:latest`. On LXC 107: `nginx-proxy-manager:latest`,
  `cloudflared:latest`. Others (Pi-hole `2026.05.0`, Beszel `0.18.7`) are
  pinned.
- **Patching:** as of 2026-09-23, all 14 LXCs have security-only
  unattended-upgrades. Host, VM kernels, the GPU stack and OPNsense are
  deliberate and manual. Doctor has no view of pending host updates or
  reboot-required flags.
- **Alerting:** Doctor runs daily at 08:15, with Grafana's two UPS email
  alerts. Aster Companion already delivers Web Push and has a Doctor
  summary hook.
- **Host tuning:** swap 1.6 GiB used with ~46 GiB RAM available (default
  `vm.swappiness`).
- **CI:** Forgejo 16 is available; no Actions runner is configured.
  `doctor.sh` quoting bugs were caught only at run time on 2026-09-23.
- **Already done in the remediation:** thin-pool Doctor check and weekly
  LXC trim; apt proxy Doctor check; security-only auto-updates.
- **Related projects (not duplicated here):**
  - [TrueNAS DIY SAS expansion](TrueNAS-DIY-SAS-Expansion.md) owns storage
    capacity and drive choice. Note: three of six spare ST4000NM0023 drives
    failed long self-tests, a finding handed to that project.
  - [AI-PAM credential broker](homelab-credential-broker.md) owns credential
    custody.
  - [Authentik rollout](Authentik-Rollout.md) owns SSO policy.

## Scope and exclusions

### In scope (eight workstreams)

| WS | Workstream | Outcome |
|---|---|---|
| N | Second node build | A small standalone Proxmox VE host (not clustered) on its own UPS feed, hosting workstreams A, B and C. Rebuildable from Git and NetBox |
| A | Proxmox Backup Server (PBS) | PBS installed on the second node's host OS (supported alongside PVE). Deduplicated, incremental, verified guest backups with file-level restore, replacing `vzdump`-to-directory as the primary local backup. Existing TrueNAS and IDrive legs are re-pointed or retained |
| B | Critical-path resilience | Standby Pi-hole and NPM containers on the second node, plus a sign-in break-glass path, and a documented, **drilled** "primary Proxmox down" procedure |
| C | Always-on ops runner | An unprivileged container on the second node runs Doctor, the weekly exporters and the scheduled report, instead of the Mac. The Mac keeps interactive use |
| D | Image pinning and update notification | All long-running containers pinned to explicit versions. A notifier (Diun, D4) reports new releases; updates remain manual |
| E | Drift visibility | Doctor warns on pending reboots, host security updates older than 30 days, and held/blacklisted packages with updates available |
| F | Failure alerting | Doctor failures (not passes) pushed to Jason's phone through the existing Aster Companion Web Push path (D5) |
| G | Small hardening | Host `vm.swappiness=10`; Forgejo Actions runner running `bash -n`, `sh -n` and shellcheck on `scripts/` for every push |

### Explicit exclusions

- Storage capacity, drive selection and the Media pool (SAS expansion
  project).
- New household services (Vaultwarden, Uptime Kuma, ntfy); each would need
  its own charter.
- A Proxmox cluster with shared storage or live migration. The second node
  is standalone; clustering two nodes would also need a QDevice for quorum.
- Hosting NUT on the second node. The Lenovo M92p NUT server stays
  dedicated and independent, since it is the last host to shut down and
  orchestrates the others.
- Changes to Authentik policy, OPNsense firewall design or VLAN layout,
  except the minimal rules WS A–C strictly require, approved per change.
- Automatic updating of containers, hosts or firmware. Notification only.
- Removing any existing backup leg before its replacement has passed a
  restore test.

## Authority model

| Fact | Authority |
|---|---|
| Guest inventory, IPs, VLANs, new hosts | NetBox |
| Backup schedules, retention and verification | PBS (after WS A) and `docs/05-Backups.md` |
| Scheduled-job ownership and timing | Ops-runner systemd timers, mirrored in `configs/systemd/` |
| Pinned image versions | Compose files or `configs/` in this repository |
| Scope, decisions, evidence | This document |

## Architecture (target)

```text
 ┌──────── Primary Proxmox (existing) ────────┐        ┌──────── Second node (new, standalone PVE) ─────────┐
 │ all current guests                          │ backup │ host OS: Proxmox VE + Proxmox Backup Server        │
 │ nightly PBS backup job ─────────────────────┼───────►│   datastore on dedicated SSD (encrypted)           │
 └─────────────────────────────────────────────┘        │ LXC pihole-standby   (VLAN 20)                     │
                                                        │ LXC npm-standby      (VLAN 50, cold/warm per M5)   │
                                                        │ LXC ops-runner       (VLAN 50) ── Doctor 08:15,    │
                                                        │                        exporters Sun 06:00, report │
                                                        │                        ──► Companion push (failures)│
                                                        └──────────────┬─────────────────────────────────────┘
                                                                       │ PBS sync / pull
                                            TrueNAS copy ──► IDrive (via LXC 112, unchanged)
 Forgejo Actions runner (lint) · Diun (image notifications) — placement decided in M1/M2
```

### Second-node hardware

| | Recommended | Budget option |
|---|---|---|
| Model | Used Lenovo ThinkCentre **M720q / M920q** (8th/9th-gen Intel, Tiny) or equivalent | Lenovo **M92p Tiny**, the same model as the NUT server |
| CPU | 6-core i5/i7 (8th/9th gen), AES-NI | i5-3470T, 2c/4t, AES-NI. Verify jobs will be slow |
| RAM | 32 GB (up to 64 GB) | Must be upgraded to **16 GB** (its maximum). Tight |
| Storage | NVMe (OS and containers, ≥256 GB) **plus** 2.5" SATA SSD for the PBS datastore (**2 TB**) | One 2.5" bay: OS and datastore share one **2 TB** SSD (no separation) |
| Network | 1 GbE onboard, plus an optional PCIe NIC | 1 GbE only |
| Power | ~15–35 W | ~15–35 W |

- **Datastore sizing:** today's `vzdump` archives occupy ~663 GiB without
  deduplication. PBS deduplication should fit the existing 7 daily /
  4 weekly / 6 monthly retention within 2 TB with headroom. Confirmed in
  M0 from the actual archives.
- **Networking:** one port carries VLAN 20 (standby Pi-hole) and VLAN 50
  (host management, NPM standby, runner) as a tagged trunk. The switch port
  change is approved per change.
- **Power (pending H2):** recommended on **`network-ups`**, at ~75 W of
  300 W as of 2026-09-23. Adding ~25 W is estimated to cut its runtime from
  ~32 min to ~22 min. That keeps the node out of the primary Proxmox's
  power fate, but shares it with the gateway and NUT server. The
  alternative is `proxmox-ups` (ample headroom, but shared fate with what
  it protects).
- **Shutdown integration:** the node joins NUT as a `secondary` of its UPS,
  with thresholds set in M-N so it shuts down before the NUT server does.
- **Failure of the node itself:** loses local PBS history and the standby,
  but no primary data. TrueNAS and IDrive copies continue. The node is
  rebuildable from Git plus NetBox, and its PBS configuration is backed up
  to TrueNAS.



## Privacy and security design

- **PBS:**
  - datastore encryption with the key held offline, following the existing
    backup master-key custody (AI-PAM Black class; never in Git or chat);
  - a dedicated PBS API token scoped to backup/restore of named guests;
  - the Proxmox host holds only that token.
- **Ops runner:**
  - a dedicated service identity and SSH key, scoped per target like the
    existing `ai-lab-backup` pattern, with read-only where possible;
  - no copy of Jason's personal SSH credentials;
  - it gains the Mac's current reach, so every new SSH/firewall path is
    listed and approved individually.
- **Second node:** the same VLAN placement as the guests it backs up. No
  new inbound Internet path; standby services stay private.
- **Diun and the Actions runner:**
  - Diun needs only registry read access and Docker socket read (or compose
    files);
  - the runner is unprivileged and has no lab SSH access.
- **Notifications:** generic push text ("HomeLab Doctor: 2 failures") with
  detail only after Companion login, reusing the Companion privacy design.

## Pre-start risk assessment

| # | Risk | Likelihood / impact | Controls | Residual |
|---|---|---|---|---|
| R1 | Backup gap during the PBS cutover | Low / High | Run PBS in parallel with `vzdump` until two verified restores per guest class pass; retire old legs last | Low |
| R2 | PBS encryption key loss makes backups unrecoverable | Low / Very high | Offline key custody documented before the first encrypted backup; restore test uses the escrowed key | Low |
| R3 | The ops runner concentrates lab-wide SSH reach on one guest | Medium / High | Unprivileged LXC, per-target restricted keys, read-only by default, NetBox and Doctor coverage, no personal credentials | Medium, accepted with the second-node design |
| R4 | PBS, the standby and the runner share one small box (a new, smaller SPOF) | Low / Medium | Node loss affects no primary data; backups continue to TrueNAS and IDrive; Doctor alerts from the primary side when the node is down; rebuild from Git | Low |
| R9 | Budget M92p option: a single disk holds OS and datastore, 13-year-old hardware | Medium / Medium | Recommend M720q/M920q-class; if the M92p is chosen, SMART monitoring in Doctor and an accepted-risk note | Accepted only if H1 = budget |
| R10 | Adding the node to `network-ups` shortens gateway runtime (~32 → ~22 min) | Certain / Low–Medium | Measure after install; NUT secondary shutdown before the NUT server; alternatively `proxmox-ups` | Decided at H2 |
| R5 | Second-node standby services drift from primary | Medium / Medium | Config sync from Git; Doctor checks standby health and version parity | Low |
| R6 | Pinning images delays security fixes | Medium / Medium | Diun notifications plus a monthly maintenance window | Low |
| R7 | Push alerting becomes noisy | Medium / Low | Failures only, deduplicated, with a daily digest for warnings | Low |
| R8 | Hardware purchase delays the project | Medium / Low | WS D–G proceed without it; the runner can start as an interim LXC on the primary if needed | Low |

- **Irreversible operations:** none planned. Old backup legs are retired
  only after verified restores; every host change has a documented revert.
- **Service interruption:** PBS job changes, NPM/Pi-hole standby
  enablement and any second-node joining happen in announced windows.
- **Test strategy:**
  - restore proofs into isolated guests (disposable VMIDs, no network or
    an isolated bridge);
  - a planned "primary Proxmox off" drill for WS B;
  - synthetic Doctor failures for WS E/F.

### Decisions

**Recorded (Jason, 2026-09-24):**
- **D1–D3 → one second node.** A single standalone small-form-factor
  Proxmox VE node hosts PBS (on its host OS), the standby Pi-hole and NPM
  containers, and the ops-runner container.

- **H2 — UPS feed:** **`network-ups`** (R10 accepted; re-measure after
  install).
- **D4 — Update notifier:** **Diun**.
- **D5 — Failure alerts:** **Aster Companion Web Push**.
- **D6 — Stream:** **Stream A, the whole project.** The risk assessment
  above is the authorization envelope. Non-waivable stop conditions still
  require a fresh decision from Jason, including any materially broader
  firewall or trust rule than designed, retiring a backup leg without a
  verified restore, and credential exposure. Git pushes still follow the
  repository rule.

**Postponed:**
- **H1 — Hardware:** Jason is looking for deals. M720q/M920q-class
  (recommended) or a budget M92p at 16 GB (accepts R9). Workstreams D–G
  (M1, M2) do not depend on it. M-N, M3, M4 and M5 wait for the hardware.

## Persistence plan

- This document is the checkpoint: decisions, the current workstream, next
  safe action and evidence.
- Every host or guest change records its rollback before execution. Backup
  jobs keep the old leg until the new one's restore passes.
- No secrets in Git, including the PBS key, API tokens and runner keys.

## Milestones

### M0 — Discovery and decisions (read-only)
- [x] Record the second-node design (D1–D3), 2026-09-24.
- [x] Record H2, D4, D5 and D6 (2026-09-24). H1 is postponed while Jason
      looks for deals.
- [ ] Inventory every scheduled job on the Mac and its dependencies (SSH
      aliases, local paths, secrets).
- [ ] Inventory all container images and compose locations; list unpinned
      ones.
- [ ] Confirm the hardware shortlist and power draw for H1/H2 against the
      UPS headroom measured 2026-09-23.
- [ ] Size PBS storage from current `vzdump` archives and retention
      (7 daily / 4 weekly / 6 monthly).

Gate: decisions recorded, and Jason accepts the risk assessment and stream.

### M1 — Quick wins (WS E, F, G)
- [ ] Doctor drift checks: reboot-required (host, LXCs, VMs), host security
      updates older than 30 days, held or blacklisted packages with
      updates.
- [ ] Doctor failures sent via Companion Web Push (failures only, deduped).
- [ ] Host `vm.swappiness=10` (persistent sysctl; revert documented).
- [ ] Forgejo Actions runner plus a lint workflow for `scripts/`.

Gate: synthetic failures push to Jason's phone; the lint workflow blocks a
seeded syntax error.

### M2 — Image pinning and notifier (WS D)
- [ ] Pin every `:latest` image to its current digest or version; record in
      Git.
- [ ] Deploy Diun (D4) with notifications to the chosen channel.

Gate: no unpinned long-running image; a notifier test fires.

### M-N — Second node build (WS N; needs H1 hardware on site)
- [ ] Jason installs the hardware and cabling (physical step); VLAN trunk
      on the switch port (approved per change).
- [ ] Install Proxmox VE, then PBS on the host OS; NetBox records; Doctor
      reachability check.
- [ ] Join NUT as a `secondary` of the H2 UPS with a shutdown threshold
      ahead of the NUT server; re-measure UPS runtime.
- [ ] Host config backup added to `lab backup` / the ops runner.

Gate: node reachable, monitored, on UPS with a tested shutdown signal, and
recorded in NetBox.

### M3 — Ops runner (WS C)
- [ ] Unprivileged LXC on the second node; dedicated identity and
      restricted per-target keys.
- [ ] Port the four Mac LaunchAgents to systemd timers; run them in
      parallel for one week.
- [ ] Retire the Mac schedules after parity is shown. The Mac keeps the
      interactive `lab` CLI.

Gate: a week of parity, and one Mac-off week with no missed runs.

### M4 — Proxmox Backup Server (WS A)
- [ ] PBS on the second node's host OS, datastore on its dedicated SSD (or
      the shared SSD under the budget option); offline key custody
      documented and tested first.
- [ ] Parallel-run PBS jobs with `vzdump`; scheduled verify jobs.
- [ ] Restore proofs: one LXC, one VM, LXC 112 (bind mount) and a
      file-level restore.
- [ ] Re-point the TrueNAS/IDrive legs to PBS sync, or keep them, per the
      sizing; update `docs/05-Backups.md`.
- [ ] Retire the directory-storage `vzdump` job only after the above.

Gate: all restore proofs pass, and Doctor checks backup age plus verify
results.

### M5 — Critical-path resilience (WS B)
- [ ] Standby Pi-hole on the second node, added as a DNS server in DHCP
      (approved per change). Standby NPM with config synced from the
      primary. Sign-in break-glass path documented. "Primary down" runbook.
- [ ] Planned drill with the primary Proxmox powered off: DNS, proxied
      sites (or documented degraded mode) and admin access verified.

Gate: the drill passes and is documented with timings.

### M6 — Graduation
- [ ] Integration checklist complete; two independent Doctor passes.
- [ ] Close-out with the final architecture and accepted limitations.

## Validation and evaluation

- **Functional:** restores, drill, parity week, notifier and push tests.
- **Failure:** PBS unreachable, runner down, Mac off, push service
  unavailable; each must fail visibly.
- **Security:** key scopes, no personal credentials on the runner, no new
  inbound paths, secret scan of the repository.
- **Regression:** existing Doctor checks, backup legs, Aster lab worker and
  Companion notifications.

## Observability and maintenance

New Doctor checks cover:
- PBS job and verify status;
- runner timer freshness;
- standby-node health and version parity;
- drift (M1);
- a notifier heartbeat.

A monthly maintenance window covers host, VM-kernel, GPU-stack and OPNsense
updates.

## Backup, restore and rollback

- PBS configuration and datastore metadata are backed up to TrueNAS.
- The encryption key is escrowed offline.
- The runner and second node are rebuildable from Git plus NetBox.
- Every workstream's rollback restores the pre-change path (Mac schedules,
  `vzdump` job, single-node operation).

## Documentation and systems-of-record updates

- [ ] **HomeLab Doctor:** checks listed above.
- [ ] **Monitoring/alerting:** Companion push route; Grafana unchanged.
- [ ] **Backup and recovery:** `docs/05-Backups.md` rewritten for PBS;
      restore runbook.
- [ ] **NetBox:** PBS host, second node and runner; IPs and VLANs.
- [ ] **Human wiki:** "Proxmox is down" runbook; restore how-to.
- [ ] **Aster mirror:** operational docs only.
- [ ] **Operational reference:** backup, runner and standby operations.
- [ ] **Repository documentation:** architecture, IP addressing, hardware
      inventory, portfolio, changelog.
- [ ] **Diagrams/rack:** new hardware placement and UPS assignment (power
      budget checked).
- [ ] **Homepage:** PBS and notifier tiles, with no credentials.
- [ ] **Authentication/authorization:** PBS behind Authentik if supported;
      break-glass login documented.
- [ ] **DNS, certificates, firewall:** minimal per-change rules for PBS,
      the runner and the standby.
- [ ] **Automation and schedules:** runner timers, PBS jobs, trim, notifier.
- [ ] **Security inventory:** runner keys, PBS token and key custody.
- [ ] **AI administration integration:** PBS `ai-*` identity decision;
      runner identity recorded for AI-PAM onboarding.

## Graduation criteria

All milestone gates pass:
- restores are proven, including LXC 112 and file-level;
- the primary-off drill passes;
- no scheduled job depends on the Mac;
- no long-running image is unpinned;
- drift and failure alerts reach Jason's phone;
- documentation and NetBox agree.

## Evidence log

- **2026-09-24 — Decisions recorded.** H2 `network-ups`, D4 Diun, D5
  Companion Web Push, D6 Stream A for the whole project. H1 (hardware) is
  postponed while Jason looks for deals.

- **2026-09-24 — Second-node design chosen.** Jason asked whether PBS,
  the standby and the runner could share one machine, and whether NUT-class
  hardware could do it. Answer recorded above: yes on one node. The M92p is
  workable only with 16 GB RAM and a single 2 TB SSD; an M720q/M920q-class
  node is recommended. D1–D3 merged into the second-node design; H1, H2 and
  D4–D6 are pending.

- **2026-09-24 — Project proposed** from the 2026-09-23 health-check
  recommendations, at Jason's request. No system changed by this proposal.

## Close-out

Not started.
