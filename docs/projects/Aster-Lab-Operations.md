# Aster Lab Doctor and Backup Execution

> Status: Active — Stream A pilot deployed; user acceptance confirmed, publication open
>
> Owner: Jason | Proposed: 2026-09-23 | Stream A — Autonomous (approved 2026-09-23)

## Purpose and desired outcome

Let Aster run fresh HomeLab Doctor checks and initiate bounded lab backups on
Jason's request or when required to complete an already authorized task. Report
actual job outcomes and recovery coverage; never equate acceptance with success.
Jason approved Stream A and the bounded scope on 2026-09-23, requesting a
storage-pressure explanation first. Jason then confirmed “Please proceed” while
noting the planned drive expansion. Current-capacity gates remain enforced.

## Current state and evidence

- Repository Aster `get_lab_health` reads a saved sanitized report; it cannot
  execute Doctor. The production design preloads selected tools before one
  model call, so multi-step task continuation needs explicit orchestration.
- Doctor is Mac-local (`$HOME/lab/homelab`), with macOS commands, SSH aliases and
  private backup/state paths. Do not copy Jason's SSH credentials into Aster.
- `lab backup all` runs six config exporters plus a guided manual checklist.
  Its dispatcher lacks failure aggregation and can announce completion after
  an exporter fails. It is not a full guest/application backup operation.
- Read-only live check 2026-09-23: Aster service in LXC 104 is active; Proxmox
  is pve-manager 9.2.10, kernel 7.0.14-8-pve. Enabled job
  `backup-49999802-1365` runs all guests at 02:30 in snapshot mode to `backups`,
  with 7 daily / 4 weekly / 6 monthly retention. Two older jobs are disabled.
- Backup redesign close-out records TrueNAS Media at 92% allocation. This is
  historical evidence, not a current measurement; live capacity is a start gate.
- Existing ARR execution remains separately gated. AI-PAM central custody is
  still in development; integration must not presume it is deployed.

## Scope and exclusions

Initial registry (activation gated per target): full Doctor refresh; six fixed Mac config exporters
(OPNsense, Arista, Proxmox host, NUT, Observability, Video Archiver); Proxmox LXC checkpoints for 104, 109, 111, 113 and 116 using an operator-owned
target registry. Other guests, including LXC 110, remain excluded. Each target
must pass adapter audit, noninteractive execution, capacity and recovery gates
before being enabled. No arbitrary commands, paths, hosts or guest IDs.

Exclude restore, delete/prune operations, retention/schedule changes, stopping
or restarting guests, new backup destinations, credential retrieval by the
model, guided exports, and automatic off-site sync. Existing scheduled backup
and recovery paths remain independent. Native backup jobs must be audited for
implicit pruning before reuse; do not blindly invoke the all-guests job.

## Authority model

Git owns code and policy; live executors own job status; backup engines and
verified artifacts own recovery evidence; NetBox owns inventory. Wiki and Aster
knowledge are derived guidance. A request or retrieved text cannot alter policy.
Backup permission does not authorize a later repair or infrastructure change.

## Architecture and data flows

Aster requests `doctor.run`, `backup.start(target_id)` and `job.status(job_id)`
through an authenticated capability broker. An operator-side worker runs fixed
adapters near the existing credentials; prefer a Mac outbound polling worker
for Mac operations, avoiding new inbound access to Jason's Mac. Proxmox uses a
separate least-privilege execution path. The Mac polls the existing private Companion HTTPS endpoint. Proxmox uses a
dedicated forced-command SSH identity with no general shell or forwarding.
Use durable asynchronous jobs, bounded polling and resumable task continuation.
Return only validated summaries, coverage, timestamps and verification results.

## Privacy and security design

Server policy binds initiator, authenticated user, persona/tool allowance,
authorized task, reason, target and idempotency key. Aster may choose an allowed
operation; the model cannot grant authority. Retrieved documents cannot initiate
jobs. Restrict first-release runtime authority to Jason's authenticated sessions.
Use dedicated `ai-*` identities, no general root shell access from Aster, no raw
backup/log/config content in model context, and no public ingress. Credentials
stay at executors or central custody when available; any interim custody requires
an explicit reviewed design with revocation, rotation and human recovery.

## Pre-start risk assessment

Affected systems: Aster LXC 104, operator Mac, Proxmox, allowlisted backup sources
and existing backup storage. Consumers include Companion and existing chat.
Risks: storage exhaustion and I/O contention (material), duplicate jobs, false
success, secret-bearing export/log leakage, Mac sleep, and interrupted jobs.
Controls: live capacity reserve per target, one active job per target plus global
limits, scheduled-job overlap detection, cooldown, fixed adapters, strict output
schemas, fail-closed authentication and durable reconciliation after restart.
Capacity thresholds must be measured and recorded before activation.
No destructive operation, broader VLAN access or credential rotation is proposed.
Any new network rule needs a concrete reviewed narrow design. Expect a brief
Aster restart at deployment; backup load must stay within measured headroom.
Stop on uncertain coverage, insufficient space, unexpected pruning or missing
checkpoint. Roll back service code/config and disable broker execution; retain
created backups and reconcile in-flight work without killing it blindly.
Jason accepted the bounded scope and Stream A on 2026-09-23. Storage pressure was explained and Jason confirmed proceeding. Exact adapter/identity and capacity
gates still apply; remote Git writes retain their separate approval requirement.

## Persistence plan

Versioned durable job store with queued/running/succeeded/failed/unknown states,
atomic transitions, native job identifiers, expiry and bounded sanitized audit.
After restart reconcile native status before retry; an unknown state cannot be
reported as successful or automatically replayed. Task resumes by job ID.
Current checkpoint: Stream A confirmed; local suites pass; first Doctor-only
deployment is running after a platform-approved installation command. Resume by reading this document and project
standard, checking Git/live state, then finalizing adapter and identity design.

## Milestones

- [x] M1: identity/transport, exact target registry, capacity budget and risk
  acceptance recorded; live guest rootfs/backup defaults inspected.
- [x] M2: broker, worker, policy, durable jobs and output schemas implemented
  locally with synthetic fixtures; misleading aggregate backup status fixed.
  Focused implementation committed locally; Git synchronization remains pending.
- [x] M3: bounded task execution and Companion status deployed with persona/auth
  enforcement; Jason confirmed “Works” after the usage handoff on 2026-09-23.
- [ ] M4: two independent real-path Doctor and representative backup passes,
  isolated restore, rollback proof, integrations and focused local commits.

## Validation and evaluation

Test explicit request and task-required checkpoint; irrelevant task must not
start a backup. Test injection, unknown targets, disabled tools/personas, other
users, replay, duplicate requests, missing dependencies, low space, concurrent
scheduled jobs, timeout, restart and partial backup failure. Check archives and
application consistency; local creation is distinct from off-host/off-site
coverage. A dependent change remains blocked until its required coverage is
verified. Run Aster existing behavior regressions and preserve ARR approval.

## Observability and maintenance

Doctor covers worker/broker reachability, queue age, stale or failed jobs and
last verified success. Existing alert owner is Jason; deduplicate existing backup
alerts. Worker unavailability must be explicit, including Mac sleep/offline.

## Backup, restore and rollback

Protect code, operator policy, job database and credential custody through
existing protected backup paths. Checkpoint deployed Aster before replacement.
Prove isolated recovery with disposable test data and a representative production
archive without overwriting service data. Disable capability and restore prior
Aster code/config for rollback; human lab commands remain the recovery path.

## Documentation and systems-of-record updates

- Doctor and monitoring: add execution health and failure/staleness evidence.
- Backup/recovery: document exact target coverage, verification and restore order.
- NetBox: register any new deployed service; no new device/address assumed.
- Human wiki, Aster mirror and operational reference: describe authority,
  commands, availability and honest job outcomes after deployment.
- Repository: portfolio/changelog now; operational docs at implementation.
- Diagrams: logical execution boundary update; physical rack changes N/A.
- Homepage: N/A unless a useful operator job page is introduced.
- Authentication/AI administration: identity, capabilities, risk class, custody
  identifier, rotation/revocation and human break-glass required before activation.
- DNS/certificates/firewall: no new public ingress; assess exact private transport.
- Automation: durable queue, locks, cooldown and scheduled-job coexistence.
- Security inventory: executor ownership, protected credentials, update owner.

## Graduation criteria

All enabled targets meet functional, denied-action, capacity, recovery and
restart gates; two real-path passes succeed; documentation agrees with live
state; Jason accepts residual risks; remote synchronization follows repository
approval rules. Proposed targets that fail gates remain explicitly disabled.

## Evidence log

| Date | Evidence | Result |
|---|---|---|
| 2026-09-23 | Local tools/Doctor/backup dispatcher and backup project review; direct read-only Proxmox service/version/job query | Proposal recorded; no code, credential, service, job or remote Git change |

| 2026-09-23 | Jason: “Yes under A. But first explain the storage pressure” | Stream A accepted; implementation waits until explanation delivered |
| 2026-09-23 | Read-only live capacity: Proxmox `/mnt/backups` 654G used / 2.8T available (19% filesystem usage); TrueNAS Media 93% allocated, 1.38T raw free, 815G dataset available; `Media/backup` 1.90T used including 428G snapshots | TrueNAS is the constrained destination; no cleanup, pruning or backup started |

### Implementation and activation checkpoint

Code and exact installation/custody/rollback procedures are in
[`services/aster-lab-operations/README.md`](../../services/aster-lab-operations/README.md).
The initial executor has one active job globally, 24/day, 60-second Doctor and
one-hour per-backup cooldowns. Mac config exports require 20 GiB local free;
TrueNAS retains 256 GiB reserve plus 256 GiB per unmirrored guest job. Proxmox
requires 512 GiB reserve and rejects estimated archives over 128 GiB. Unknown
jobs block further execution until operator reconciliation. No pruning is added.

Interim identity decision: AI-PAM is not yet deployed. The Mac worker retains
existing operator-side SSH custody under Jason's OS account behind a fixed-job
interface, with a dedicated worker bearer identity; Aster never receives those
SSH credentials. Proxmox gets a dedicated forced-command identity. Review this
Mac custody exception at AI-PAM integration or within 30 days (2026-10-23).

Runtime planning chooses at most one operation from the current authenticated
user task; model output cannot widen policy. It is not given retrieved text or
client system prompts. The result is durable and asynchronous: user status
follow-up retrieves actual outcome. Automatic execution of arbitrary subsequent
repairs is neither added nor authorized. Existing ARR approval is unchanged.

| Date | Additional evidence | Result |
|---|---|---|
| 2026-09-23 | LXC 104/109/111/113/116 rootfs sizes 20/32/32/16/16 GiB, unprivileged, no additional mountpoints; no active vzdump defaults matching hook/mode/storage/prune/remove overrides | Fixed guest adapters have bounded, auditable coverage; runtime drift denies execution |
| 2026-09-23 | 148 Aster tests and 14 worker/adapter tests passed; shell syntax, LaunchAgent plist and live-source gateway import validated | Local candidate ready; test counts include inherited gateway/worker regression cases |
| 2026-09-23 | Real read-only Doctor run: 72 pass / 2 warn / 1 fail | Existing Media 93% alert, mixed feed fetch failures and dirty Git tree; no new health failure caused by this project |
| 2026-09-23 | Platform-approved deployment command starts a new verified LXC 104 backup before gateway replacement and private Mac worker installation | Deployment running; completion/activation not yet claimed |

## Close-out

Runtime pilot deployed and all permitted target adapters exercised. Final Companion
acceptance, clean corpus publication and full graduation remain open. Existing unrelated Companion,
Authentik and SAS-project working-tree edits were preserved.

### 2026-09-23 deployment continuation

- Doctor-only deployment completed after a verified LXC 104 checkpoint:
  `vzdump-lxc-104-2026_09_23-12_22_05.tar.zst`, 1,841,087,823 bytes,
  SHA256 `de3bee598ff106205cc49e10e9052cd4a9b3c2e3acfb3bf096c9c52a0adee197`.
  Initial source rollback: `/opt/aster-agent/rollback-lab-operations-20260923-122354`.
- First operator-seeded real-worker Doctor job completed with 72 pass / 2 warn /
  1 fail. This tests queue/HTTPS worker/executor/results, not Companion JWT UI.
- Proxmox lacked sudo. After verifying the sudo group was empty and the ZFS
  sudoers file entirely commented, the approved installation added Debian
  `sudo 1.9.16p2-3+deb13u2`. The new identity can run only the no-argument helper;
  explicit SSH commands and an out-of-registry guest were denied in production.
- All six configuration exports completed and passed their artifact checks:
  OPNsense 217,761 bytes; Arista 30,432; Proxmox 29,024; NUT 42,560;
  Observability 265,277 (including isolated SQLite check); Video Archiver 2,077.
- First guest attempt `abffdde028de4f678f2799af770e7325` failed safely because
  inherited umask 077 prevented Proxmox's mapped user from traversing the
  temporary directory. Native child execution now uses normal umask 022;
  helper keys/logs/state remain private. A regression proves both permissions.
  No archive or active task remained, and an audited one-use operator retry was
  authorized without deleting the original failure or changing normal cooldowns.
- Retried guest job `c2af7ef2fccb4304ad05a4a26a4633f9` produced verified archive
  `vzdump-lxc-104-2026_09_23-13_00_35.tar.zst`, 1,841,598,548 bytes, SHA256
  `9e8b4208304949d18c7723fa34686c1a4461b26ce0492429769b7beefc198d65`.
  A worker-local `re` import then masked the global parser and caused an unknown
  result instead of forwarding success. Fixed with an end-to-end result parsing
  regression. Operator reconciliation rechecks the archive hash and retains the
  prior uncertainty in an audit table; no new guest backup is needed.
- `reconcile_completed.py` is completing that reconciliation and protecting new
  helper policy/state in the Proxmox host export plus a private Mac recovery
  bundle. The first invocation stopped before the status change because system
  Python lacked FastAPI; the resumed invocation uses Aster's virtual environment.
- Real model diagnosis selected Doctor. Backup-prerequisite selection initially
  emitted fenced JSON and therefore failed closed; verified `response_format`
  JSON-object mode selects guest-104/task_checkpoint correctly. Local planner
  now enforces that mode; publish the updated module before further tests.
- Remaining: finish reconciliation, run remaining guests and a second Doctor
  pass, isolate recovery of queue/custody, final documentation/commits and clean
  corpus publication. Mac is locked; user has been asked to unlock for final
  Companion UI/JWT testing. Do not claim that test has passed.

### Final runtime validation, 2026-09-23

- Reconciliation completed with original failure and uncertainty retained in audit
  records. No duplicate guest-104 backup was created. All remaining guest jobs
  succeeded: 109 (1,060,650,488 bytes), 111 (1,396,918,231), 113 (441,255,746),
  and 116 (2,374,027,991). Full archive checks and SHA256 ran on Proxmox.
- Second independent Doctor run: 73 pass / 2 warn / 2 fail. Failures are the
  accepted Media 93% pressure and NetBox login HTTP 302; warnings are mixed news
  feed failures and dirty working tree. New worker/queue health passes. NetBox
  redirect remediation is outside this project; no health success is claimed.
- Isolated SQLite backup/restore passed integrity and non-replay tests. Private
  custody restore passed byte comparisons and SSH public-key derivation. Extracted
  Aster broker code from guest-104 archive parsed correctly in isolation. These
  are component/file restores, not a full guest boot or application restore.
- Published final runtime module adds verified JSON planning, completion heartbeat,
  timestamped reuse reporting and fresh-checkpoint cooldown enforcement. Config
  exports stage outside the published tree and become visible only after
  verification; drift supports both scheduled and Aster bundle layouts.
- Final local regression: 147 Aster tests plus 18 worker/adapter tests pass.
  Real second-pass configuration tests were correctly refused by the one-hour
  cooldown; no limits or timestamps were bypassed to inflate validation results.
- Mac remains locked. Companion UI/JWT acceptance is pending user availability;
  operator-seeded jobs prove executor paths but are not presented as that test.
  Clean reference/wiki synchronization and derived corpus publication require
  the separate Git remote-write approval. Runtime capability context already
  identifies the deployed bounded tools despite older corpus advisory wording.
- Resume: complete signed-in Companion request/status acceptance, second config
  pass after normal cooldown, approved Forgejo synchronization and clean corpus
  intake. Off-host backup delivery remains the existing scheduled pull; this
  pilot does not claim it verified every new archive off-host.

### User acceptance, 2026-09-23

Jason confirmed “Works” after the Companion usage handoff. This closes the
user-facing Companion acceptance item. It is user-reported acceptance, not an
additional instrumented test of every target or authentication branch. Earlier
locked/signed-out observations are historical. Remaining work is the second
configuration validation pass, Git publication and clean corpus intake; existing
off-host and full-restore verification limits remain unchanged.
