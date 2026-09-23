# Aster lab operations

Status: deployed Stream A pilot; Jason confirmed Companion acceptance on 2026-09-23. Project authority and evidence:
[`Aster-Lab-Operations.md`](../../docs/projects/Aster-Lab-Operations.md).

## Operator behavior

Use Sysadmin Aster in Jason's authenticated Companion session. Enable the new
`run_lab_doctor`, `start_lab_backup` and `get_lab_job` tools. Examples:

- “Run lab doctor”
- “Diagnose my lab”
- “Back up OPNsense”
- “Back up Aster before the task”
- “Lab job status”

A constrained planning pass can choose one diagnostic or checkpoint operation
from a current task request. It sees only the latest user text, never retrieved
instructions, earlier assistant text or client system prompts. Policy and target
validation run outside the model. Ambiguous requests fall back to the ordinary
advisor; request one named target. Legacy API keys and other users cannot start
operations. The job response is generated from server state, not model prose.

Jobs run asynchronously. Ask for status after submission. Jobs and results
survive Aster restarts; a pending task is not a verified recovery checkpoint.
Automatic continuation into arbitrary repairs is not implemented or authorized.
The existing ARR repair approval path is unchanged.

## Initial target registry

| Target | Coverage | Executor |
|---|---|---|
| doctor | Full current Doctor, result counts and bounded findings | Mac |
| opnsense, arista, proxmox, nut, observability, video-archiver | Configuration export; **proxmox is host configuration only** | Mac |
| guest-104, guest-109, guest-111, guest-113, guest-116 | Aster Agent, Observability, NetBox, Wiki, Speech LXC archives | Proxmox restricted helper |

Only targets present in both the broker and worker configuration are enabled.
LXC 110, VMs, restore, manual exports, prune and “backup all” are excluded from
this initial executor. Native guest backup runs in snapshot mode with
`--remove 0 --prune-backups keep-all=1`, 50 MiB/s bandwidth and one zstd thread.
The scheduled backup/TrueNAS copy/off-site schedules are unchanged.

## Identity and custody

- Broker: authenticated Companion JWT, issuer/audience verified by the existing
  gateway; exact Jason owner = SHA256(issuer + NUL + subject). API-key login has
  no lab execution authority. No client-supplied owner is accepted.
- Worker: dedicated `ai-lab-worker` logical identity via a random >=32-character
  bearer credential; can only claim jobs and complete a matching private lease.
- Proxmox: dedicated `ai-lab-backup` Unix identity with locked password,
  root-owned authorized_keys and an SSH `restrict,command="sudo -n
  /usr/local/sbin/aster-lab-guest"` key. Validate sudoers before activation.
  The helper takes no arguments and cannot accept paths or command text.
- Custody identifiers: LXC 104 `/etc/aster/lab-operations.env`; Mac
  `~/Library/Application Support/AsterLab/worker.json` and `guest_ed25519`.
  These are protected secret files, never Git or model context.
- Interim custody exception: AI-PAM is not deployed. The Mac worker runs as
  Jason so existing configuration-export/Doctor SSH access stays on its original
  machine. Aster receives only a fixed-operation queue, no SSH credentials.
  This is not a dedicated Mac Unix account; review at AI-PAM integration or in
  30 days. Full separation of the operator's local credentials is deferred.
- Revoke: disable the broker target list and unload the worker, remove the
  dedicated Proxmox authorized key. Do not kill an in-flight backup blindly.
- Rotate: generate a replacement worker credential at its endpoints without
  printing it, restart gateway and worker; provision a replacement restricted
  Proxmox key, validate, then remove the old key. Rotation needs its own approval.
- Human recovery: existing operator CLI and Proxmox UI remain independent.

## Installation envelope (approved Stream A; platform controls still apply)

1. Check current Aster source hash and active notification work. Build the
   deployment candidate from **current live source**, adding only the lab hooks.
   Do not overwrite or deploy unrelated working-tree notification changes.
2. Keep a private rollback copy of Aster source/unit configuration; obtain and
   verify a current LXC 104 recovery checkpoint through the human backup path.
3. Place the new broker module and patched gateway in `/opt/aster-agent` on
   LXC 104. Configure owner hash, random worker key and initially `doctor` only
   in the root-owned mode-0600 environment file. Add the supplied systemd drop-in.
4. Install a pinned copy of `worker.py`, `scripts/doctor.sh`, six exporter
   scripts, `scripts/lib/output.sh` and required `configs` under the private Mac
   `~/Library/Application Support/AsterLab` directory. Worker `repository` points
   at the pinned toolkit root; Doctor's Git checks still inspect the actual repo.
   Write mode-0600 JSON with `url=https://aster.elliottrook.com`, `worker_key`,
   `repository`, `state`, `home=/Users/jelliott`, `targets`, `guest_key` (when
   guests enabled). Install the supplied LaunchAgent. No new Mac inbound port.
5. Prove doctor twice through authenticated job creation, claim, execution and
   result delivery. Then enable each exporter only after real integrity and
   recovery validation. Preserve operator logs locally, outside model context.
6. Install guest helper root:root mode 0755 at `/usr/local/sbin/aster-lab-guest`;
   create protected state `/var/lib/aster-lab-guest`; provision the restricted
   identity, dedicated key and exact no-argument sudoers entry. Validate actual
   binary paths and sudoers; test denied commands, forwarding and other targets.
7. Enable selected guest targets only after a representative archive/isolated
   restore and two independent full-path passes. No guest delete, live restore,
   retention or storage migration is included.
8. Update Doctor, reference/wiki/mirror and service inventory from verified live
   behavior. Record each target's enabled or disabled status explicitly.

The private HTTPS proxy path already serves `/v1/`; no new public ingress,
DNS, firewall rule or external service is requested. Source-local credentials
remain local. macOS file writes outside the workspace require platform approval.

## Capacity, concurrency and failure behavior

One active broker job globally, 24 jobs/day, one backup/target/hour, Doctor
cooldown one minute. Duplicate requests return the same job. Queued work expires
in five minutes; a running job unresolved after two hours becomes **unknown**
and blocks new work until operator reconciliation. Pending result delivery is
retried without executing again. A Mac crash after claim reports unknown.

Config exports require 20 GiB free locally. All backup requests require a live
TrueNAS check and 256 GiB shared-pool reserve. Guest archives additionally reserve
256 GiB each until the expected filename and size appear at the normal TrueNAS
mirror destination; size equality releases the capacity reservation only, not
an integrity claim. The Proxmox helper requires estimated archive footprint
<=128 GiB plus 512 GiB local reserve, a running allowlisted LXC, no lock, and
avoids 02:00–06:00. The Mac avoids the weekly Sunday 05:00–08:00 window and
active config exporters. Existing schedules retain their own controls.

Unknown guest executions retain their reservation until an operator checks both
native backup status and archive placement. Do not clear uncertainty just to
make the next request succeed. No automatic retention change or cleanup.

Doctor returns counts and deduplicated bounded status lines with sensitive-pattern
redaction; raw operator output stays in
private `last-operation.log`. Backup verification checks new nonempty files,
checksums, expected archive members and full archive decoding. Observability
also runs SQLite quick_check on an isolated copy. This proves artifact integrity,
not a complete application restore or off-site recovery. Those remain separate
activation/graduation gates.

## Recovery and rollback

Back up the broker SQLite job database using SQLite's online backup API, its
environment in existing protected config custody, the private worker directory,
and guest helper state. Never publish job leases. Worker state includes the
pending result and capacity reservations and must survive restarts.

To roll back, disable targets and unload the Mac worker after reconciling active
jobs, restore the exact saved Aster source/unit drop-in and restart Aster. Remove
restricted guest authorization if retiring the feature. Keep produced archives;
do not restore an old job database over potentially in-flight work.

## Local validation

`python -m unittest discover -s services/aster-agent -p 'test_*.py'`

`python -m unittest discover -s services/aster-lab-operations -p 'test_*.py'`

Tests use synthetic files and mock executors; they do not create real backups.
Validation on 2026-09-23: 147 gateway tests and 18 worker/adapter tests passed.
Real outbound-worker jobs completed Doctor twice, all six configuration targets
and all five permitted guests. Tests were operator-seeded and do not substitute
for Companion JWT/UI acceptance. Isolated queue, custody and guest-file recovery
passed; full guest boot/application recovery and verified off-host copying remain
separate checks.

Config exports run in private staging outside the TrueNAS pull tree and are
published by atomic rename only after artifact validation. Published bundles live
at `private-backups/<target>/aster-<job-id>/`; drift inspection supports these and
the existing scheduled layout. Failed exports never become the newest published
configuration. Native guest archives retain their standard Proxmox layout.

Repeated requests identify the existing run and its requested timestamp. A prior
successful backup inside the one-hour cooldown cannot satisfy a *new* task
checkpoint; Aster explicitly reports that no new checkpoint was created.

The Mac worker is availability-dependent on Jason’s Mac. Recovery custody is
snapshotted after completed jobs into the existing protected Mac backup tree;
its presence alone does not prove the scheduled TrueNAS pull has completed.
The forced guest helper depends on Debian sudo, installed with only its exact
no-argument command granted to the dedicated identity.
