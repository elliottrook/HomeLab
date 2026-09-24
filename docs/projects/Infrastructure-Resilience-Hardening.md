# Infrastructure Resilience and Operations Hardening

> Status: Proposed — pre-start risk assessment awaiting Jason's decisions
> (D1–D6)
>
> Owner: Jason | Proposed: 2026-09-24 | Stream M — Monitored (recommended;
> see D6)
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

### In scope (seven workstreams)

| WS | Workstream | Outcome |
|---|---|---|
| A | Proxmox Backup Server (PBS) | Deduplicated, incremental, verified guest backups with file-level restore, replacing `vzdump`-to-directory as the primary local backup. Existing TrueNAS and IDrive legs are re-pointed or retained |
| B | Critical-path resilience | A documented and **tested** "Proxmox host down" path. Optionally a small second node carrying standby DNS, NPM and a sign-in break-glass path (D2) |
| C | Always-on ops runner | Doctor, the weekly exporters and the scheduled report run on lab infrastructure, not the Mac. The Mac keeps interactive use |
| D | Image pinning and update notification | All long-running containers pinned to explicit versions. A notifier (Diun, D4) reports new releases; updates remain manual |
| E | Drift visibility | Doctor warns on pending reboots, host security updates older than 30 days, and held/blacklisted packages with updates available |
| F | Failure alerting | Doctor failures (not passes) pushed to Jason's phone through the existing Aster Companion Web Push path (D5) |
| G | Small hardening | Host `vm.swappiness=10`; Forgejo Actions runner running `bash -n`, `sh -n` and shellcheck on `scripts/` for every push |

### Explicit exclusions

- Storage capacity, drive selection and the Media pool (SAS expansion
  project).
- New household services (Vaultwarden, Uptime Kuma, ntfy); each would need
  its own charter.
- A Proxmox cluster with shared storage or live migration. WS B is about a
  standby path, not HA clustering, unless Jason chooses otherwise in D2.
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
                 ┌──────────── Proxmox (primary) ────────────┐
                 │ guests … │ nightly backup job ──► PBS datastore
                 └──────────┬────────────────────────────────┘
                            │ (sync job)
   PBS (D1: TrueNAS VM or dedicated box) ──► TrueNAS copy ──► IDrive (via LXC 112, unchanged)
   Ops runner (D3) ── timers: Doctor 08:15, exporters Sun 06:00, report ──► Aster Companion push (failures)
   Second node (D2, optional) ── standby Pi-hole / NPM / break-glass sign-in
   Forgejo Actions runner ── lint scripts on push
   Diun ── watches pinned images ──► notification
```

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
| R3 | The ops runner concentrates lab-wide SSH reach on one guest | Medium / High | Per-target restricted keys, read-only by default, NetBox and Doctor coverage, no personal credentials | Medium, accepted at D3 |
| R4 | The ops runner placed on the same Proxmox host keeps a SPOF | Certain if on Proxmox / Medium | Prefer the second node or another always-on host (D3); Doctor alerts via push even when the Mac is off | Depends on D2/D3 |
| R5 | Second-node standby services drift from primary | Medium / Medium | Config sync from Git; Doctor checks standby health and version parity | Low |
| R6 | Pinning images delays security fixes | Medium / Medium | Diun notifications plus a monthly maintenance window | Low |
| R7 | Push alerting becomes noisy | Medium / Low | Failures only, deduplicated, with a daily digest for warnings | Low |
| R8 | Hardware purchase (D1/D2) delays the project | Medium / Low | Workstreams C–G proceed independently | Low |

- **Irreversible operations:** none planned. Old backup legs are retired
  only after verified restores; every host change has a documented revert.
- **Service interruption:** PBS job changes, NPM/Pi-hole standby
  enablement and any second-node joining happen in announced windows.
- **Test strategy:**
  - restore proofs into isolated guests (disposable VMIDs, no network or
    an isolated bridge);
  - a planned "primary Proxmox off" drill for WS B;
  - synthetic Doctor failures for WS E/F.

### Decisions needed from Jason

- **D1 — PBS placement:**
  - **(a)** a small dedicated box (recommended; independent of both
    Proxmox and TrueNAS);
  - **(b)** a VM on TrueNAS (no purchase, but it shares TrueNAS's failure
    domain and the 93% pool);
  - **(c)** a VM on Proxmox (not recommended: it is the machine being
    protected).
- **D2 — Critical-path resilience level:**
  - **(a)** runbook plus drill only;
  - **(b)** a small second node running standby Pi-hole, NPM and a
    sign-in break-glass path (recommended);
  - **(c)** a full two-node Proxmox cluster (more complexity; needs a
    QDevice).
- **D3 — Ops-runner host:** on the second node if D2(b) (recommended);
  otherwise a small LXC on Proxmox as an interim, accepting R4.
- **D4 — Update notifier:** Diun (recommended; lightweight, per-host) or
  What's Up Docker (has a web UI).
- **D5 — Failure alerts:** Aster Companion Web Push (recommended; exists),
  or a new ntfy service (out of scope unless chosen).
- **D6 — Stream:** Stream M (recommended for WS A–C because of backup and
  critical-path risk), with the option to run WS D–G as Stream A.

## Persistence plan

- This document is the checkpoint: decisions, the current workstream, next
  safe action and evidence.
- Every host or guest change records its rollback before execution. Backup
  jobs keep the old leg until the new one's restore passes.
- No secrets in Git, including the PBS key, API tokens and runner keys.

## Milestones

### M0 — Discovery and decisions (read-only)
- [ ] Record D1–D6.
- [ ] Inventory every scheduled job on the Mac and its dependencies (SSH
      aliases, local paths, secrets).
- [ ] Inventory all container images and compose locations; list unpinned
      ones.
- [ ] Hardware shortlist for D1/D2 (power draw against the `proxmox-ups`
      and `network-ups` headroom measured 2026-09-23).
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

### M3 — Ops runner (WS C)
- [ ] Provision per D3; dedicated identity and restricted per-target keys.
- [ ] Port the four Mac LaunchAgents to systemd timers; run them in
      parallel for one week.
- [ ] Retire the Mac schedules after parity is shown. The Mac keeps the
      interactive `lab` CLI.

Gate: a week of parity, and one Mac-off week with no missed runs.

### M4 — Proxmox Backup Server (WS A)
- [ ] Deploy per D1; offline key custody documented and tested first.
- [ ] Parallel-run PBS jobs with `vzdump`; scheduled verify jobs.
- [ ] Restore proofs: one LXC, one VM, LXC 112 (bind mount) and a
      file-level restore.
- [ ] Re-point the TrueNAS/IDrive legs to PBS sync, or keep them, per the
      sizing; update `docs/05-Backups.md`.
- [ ] Retire the directory-storage `vzdump` job only after the above.

Gate: all restore proofs pass, and Doctor checks backup age plus verify
results.

### M5 — Critical-path resilience (WS B)
- [ ] Per D2: runbook and/or second node with standby Pi-hole, NPM and a
      sign-in break-glass path.
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

- **2026-09-24 — Project proposed** from the 2026-09-23 health-check
  recommendations, at Jason's request. No system changed by this proposal.

## Close-out

Not started.
