# Aster Local Agent Operations

> Production since: 2026-08-31
> Scope: Lab VLAN 70 only; not a dependency for core HomeLab operation

## Service layout

| Component | Guest | Endpoint | Service |
|---|---|---|---|
| Aster API and browser UI | LXC 104 (`192.168.70.10`) | `http://192.168.70.10:9120` | `aster-agent.service` |
| llama.cpp SYCL FP16 inference | LXC 110 (`192.168.70.12`) | `http://192.168.70.12:11435/v1` | `aster-llama.service` |
| Sanitized Forgejo producer | LXC 108 | Forgejo loopback API only | `aster-forgejo-report.service` |
| Sanitized NetBox producer | LXC 111 | NetBox loopback API only | `aster-netbox-report.service` |
| Source-report transport | Proxmox host | No network endpoint | `aster-source-reports.timer` |

The browser page asks for the Aster bearer key and stores it in that browser's
local storage. Aster's server-side credential configuration resides in
`/etc/aster/aster.env` in LXC 104. The active inference unit in LXC 110 uses
`--api-key-file /etc/aster-llama-api-keys` and still references
`/etc/aster-llama.env`. The key file's observed owner/mode is
`ollama:ollama`/`0600`; the environment files and key contents were not read in
the 2026-10-11 runtime check. Keep credential values outside Git.

The OpenAI-compatible chat endpoint supports both normal JSON responses and
authenticated server-sent-event streaming. Streaming was added for Hermes
Desktop compatibility; the same bounded function routing and knowledge scope
apply before the upstream stream begins.

## Hermes Desktop compatibility

Hermes Desktop v0.21.0 can use Aster as an OpenAI-compatible custom endpoint:

- endpoint URL: `http://192.168.70.10:9120/v1`;
- provider ID: `aster-local`;
- model: `aster-qwen3.5-9b`;
- declared context: 65,536, which satisfies Hermes' client-side 64K minimum;
- model discovery and use-for-new-chats enabled.

The declared context is compatibility metadata only. llama.cpp still has one
8,192-token slot, so the current roughly 4,900-token Hermes startup prompt fits,
but a sufficiently long session or larger tool prompt may exceed the real slot.
Under the former 27B runtime, Hermes completed three end-to-end test turns, including streaming, but each
required roughly 65–69 seconds because its full agent prompt was reevaluated.
Use the direct Aster UI for normal conversation speed; keep Hermes for workflows
where its desktop harness is worth the additional latency.

## Runtime configuration

The 2026-10-10 full-BAR profile is persistently deployed and repeat-boot
validated: 32 GiB physical BAR2 with stock `xe`. Retained small-BAR boot
entries are emergency console recovery, not the preferred production profile.
Full trial and recovery evidence are in
[B60 inference engineering](../projects/B60-Inference-Engineering.md).

- llama.cpp b11429 (`d81235049`)
- `lmstudio-community/Qwen3.5-9B-GGUF:Q4_K_M`, pinned SHA-256
  `cd76ec205963b3b33350093e6904d9de16c4e666fd104e1f632d25c7f15f2a13`
- Private SYCL FP16/fusion-1 build, all 33 transformer layers offloaded;
  CPU-mapped and host buffers still exist
- One 8,192-token slot
- Four CPU threads, batch 256, microbatch 128
- Flash attention; Q4 key/value cache
- Model reasoning disabled by default
- Health readiness bounded to 300 seconds (systemd limit 330 seconds);
  protected synthetic generation during deployment/recovery validation
- `Restart=no`: no automatic repeated GPU initialization after failure
- Persistent pinned private runtime under `/opt/aster-sycl-b11429`;
  private Level Zero loader 1.33.1 and oneAPI libraries, no system/global change
- LXC 110 root disk 72 GiB (approved growth from 64 GiB, not shrinkable in place)

Read-only reconciliation on 2026-10-11 found the B60 physical BAR2 at 32 GB
and `aster-llama.service` active on the self-contained b11429 SYCL FP16 build;
its health endpoint returned OK. The unit uses an `ollama`-owned, mode-0600
API-key file at `/etc/aster-llama-api-keys`, whose contents were not read.
The [Stream A runtime record](../projects/AI%20Projects/evidence/Stream-A-SYCL-runtime-reconciliation-2026-10-11.md)
separates these current facts from unmeasured performance and recovery claims.

Systemd does not report `aster-llama.service` fully started until its current
readiness helper completes. The former Vulkan setup took roughly 1–2 minutes
to load and warm; current SYCL startup time has not been measured here. The
unit allows 330 seconds for startup. Validate a real request before claiming
that readiness also proves generation and template compatibility.

Persistent SYCL activation and regression passed on 2026-10-11; final exercised
soak acceptance is recorded in the B60 project ledger. Accepted unit SHA-256
`a4c75169673a1a230682b73d362a05c1bdd30f7a5c41cfb9c77463204dfd4cb3`;
binary `0404f751814391544c86469fa71a893c0f3858e7c7aeb2cb0982909c1c0de6c5`.
Measured matched decode gain is about 21% for short grounded/8K outputs and
about 19% for sustained 128-token outputs (~57.8 versus ~48.6 tok/s).
Do not confuse token-rate improvement with request-latency reduction.
The repository retains exact SYCL and Vulkan unit templates.

Explicit runtime-identity questions are answered deterministically by the
Aster agent rather than delegated to model recall. The versioned response names
the interface in LXC 104, Qwen3.5-9B/llama.cpp SYCL inference in LXC 110
and VM 105 as the stopped Ollama rollback guest. Actual mapped-runtime evidence
is authoritative. No LXC 104
source/restart change is implied by the bounded LXC 110 deployment approval.
Ordinary analysis questions
continue through the normal model and tool routes.

Systemd reports the inference unit started only after health readiness passes.
The SYCL unit uses its private bounded readiness helper, not the former Vulkan
real-generation warm-up script. Deployment and recovery additionally exercise
authenticated generation before reporting success. A normal later restart can
leave first-generation kernel work for its first caller; readiness alone is not
proof of correct generation.

The exact immediately previous 9B Vulkan unit is retained at
`/etc/systemd/system/aster-llama.service.pre-sycl-20261011`, SHA-256
`6b09f4580ef49b1c61532d22f48cc5091ec95a0e823f73893db7a83f5c1a461e`.
The approved controller `scripts/b60-bar/production-sycl.py --rollback`
validates that checkpoint and the retained Vulkan binary, atomically restores
only this known unit, stops/quiesces/clean-starts inference, and validates hashes,
health, `xe`, BMG G21 and protected generation. Native OpenVINO trials instead
use `--restore-accepted-sycl`; they must not leave Vulkan as accepted production.
Both recovery paths are bounded, fail closed on unknown unit hashes, and do
not change BAR, boot, system packages or credentials.

The exact former 27B production unit is retained at
`/etc/systemd/system/aster-llama.service.pre-9b-20261010`; its b11081 runtime,
IQ4_XS model shards and earlier Q8 unit remain intact. Normal rollback installs
that unit over `aster-llama.service`, runs `systemctl daemon-reload`, stops the
current service, waits 30 seconds, starts it once non-blocking, and validates
the former unit/runtime/model hashes, endpoint health, `xe`, BMG G21 Vulkan and
an authenticated synthetic Aster response. Do not retry a GPU/device failure
automatically.

## Lab Doctor and backup execution

As of 2026-09-23, Sysadmin Aster has a bounded execution pilot for Jason's
verified Companion identity. “Run lab doctor”, “back up OPNsense”, “back up
Aster”, and “lab job status” use a durable job queue. A constrained planner can
also choose one diagnostic or backup checkpoint needed by the current task.
It never receives retrieved instructions or client system prompts. A job being
queued is not evidence of successful completion or a usable recovery checkpoint.

The operator Mac polls the existing private HTTPS endpoint and runs fixed
Doctor/config-export adapters. A dedicated Proxmox forced-command identity
backs up allowlisted running LXCs without shell access or pruning. Config
exports cover OPNsense, Arista, Proxmox **host configuration**, NUT,
Observability and Video Archiver. Guest targets are LXC 104, 109, 111, 113 and
116. LXC 110, VMs, restores, retention/schedule changes and arbitrary commands
remain outside this execution surface. Existing ARR approval is unchanged.

Only Sysadmin's enabled lab tools and Jason's signed-in session can request
execution; legacy API credentials and other personas cannot. Model output cannot
widen target policy. Jobs serialize globally, deduplicate requests, enforce
cooldowns and check current storage capacity. Unknown/interrupted jobs require
operator reconciliation. Doctor returns bounded findings; backups return verified
artifact coverage. Off-host/off-site transfer remains on its existing schedule
and is not implied by successful local creation.

Source and recovery procedures:
`homelab/services/aster-lab-operations/README.md` and
`homelab/docs/projects/Aster-Lab-Operations.md`. Human CLI operation remains
independent. Companion UI acceptance and corpus publication passed on 2026-09-26;
operator-seeded production worker validation is recorded separately.

## Functions and knowledge

Aster retains its allowlisted read-only advisory functions:

- current time in an IANA timezone;
- Aster or inference health;
- the latest sanitized HomeLab health summary;
- keyword-ranked search of `/var/lib/aster/knowledge`;
- the fixed-path sanitized ARR report;
- the fixed-path sanitized Forgejo report;
- the fixed-path sanitized NetBox report; and
- a dry-run proposal for the one report-issued opaque ARR candidate.

As of 2026-10-11, the existing HomeLab health reader opens its fixed report
once without following symlinks, rejects non-regular or writable files and
reports over 65,536 bytes, and treats timestamps older than 36 hours as
unavailable. It still supplies bounded human summaries from a fresh sanitized
report; it is not the unpromoted schema-2 Doctor projection or a connected
Codex tool. The deployed source checkpoint before this reader change is
`/opt/aster-agent/rollback-aster-agent-before-doctor-reader-20261011.py`.

These functions are selected from the current request and pre-executed before a
single model call. Knowledge retrieval normally returns up to four
source-diverse results. Focused checklist, monitoring and reviewed
ARR-reference questions may return multiple chunks from the same authoritative
source when a long table or section spans chunk boundaries.
Current hardware inventory receives a strong present-state ranking preference,
but relevant operational and design records are not excluded from multi-part
answers. The Qwen model's native OpenAI function-call behavior was validated
separately, but Aster's production path is deliberately one-pass: it must not
emit or request follow-up tool calls. If the preloaded context is insufficient,
it says what is missing. There is no arbitrary shell, filesystem write, or
user-supplied network target.

### Forgejo and NetBox read-only reports

Aster has no API token or direct network path to Forgejo or NetBox. A dedicated
source-local account reads each service through its loopback API, and a
source-local oneshot converts the response to a strict allowlisted schema.
Every five minutes the Proxmox timer starts each producer, pulls only the
sanitized JSON, validates it again, and atomically installs it as a root-owned,
mode-0640 report in `/var/lib/aster/source-reports` in LXC 104. The Aster unit
mounts that directory read-only.

The Forgejo identity is restricted, cannot create repositories or
organizations, has `read` collaborator access only to `jason/homelab`, and its
token contains only read scopes. Its report includes repository visibility,
archive/default-branch state, update time, bounded branch/tag/release/open
issue/open pull counts, an abbreviated latest commit identifier and latest
action status. Source, diffs, messages, authors, issue/PR text and action logs
are excluded.

The NetBox identity has an unusable password, is not a superuser, and receives
one object permission whose only action is `view`. Its API token has writes
disabled. The report includes bounded device, VM, VLAN and prefix inventory
plus site/rack aggregate counts. Config contexts, custom fields, descriptions,
contacts, journal/change data, secrets and mutation authority are excluded.

Both Aster readers reject symlinks, non-regular files, non-root ownership,
group/other write permissions, oversized reports, unknown fields, invalid
types and timestamps more than 15 minutes old. Failure leaves the source
unavailable; it never causes Aster to contact a source or widen access.

To suspend the integration, disable `aster-source-reports.timer` on Proxmox;
the reports will age out and fail closed. Aster source rollback is retained in
`/opt/aster-agent/rollback-source-reports-20260909` in LXC 104. Restoring it
also requires removing the source-report unit drop-in and restarting only
`aster-agent.service`. Revoking either source token is a separate source-local
administrative action; it is not available to Aster.

The deployed Aster source also contains a structured ARR execution endpoint.
It is not an LLM function and natural-language chat cannot select it. It can
only rebuild a request for the one opaque candidate in a fresh sanitized
report, and the separate TrueNAS broker must also be running, reachable,
explicitly execution-enabled and holding a fresh server-side approval. The
broker is normally stopped, boot-disabled and blocked at the inter-VLAN
firewall. See the production gate below.

The deployed knowledge directory is a curated snapshot, not a live Git mount.
Build a candidate from the repository's explicit allowlist after material
documentation changes. **The default command below is a base-only preflight,
not a deployable replacement for an accepted snapshot with a derived mirror**:

```sh
scripts/build-aster-knowledge-snapshot.sh /tmp/aster-knowledge.tar.gz
```

Before any production refresh, include the same accepted, validated mirror via
`--mirror-root`, verify its generation/provenance index, and compare member
counts and source hashes with the deployed `.aster-provenance.json`. A
2026-10-11 base-only build contained 29 sources while the deployed snapshot
contained 1,825 including `aster-knowledge-mirror`; promoting the base-only
archive would remove most curated knowledge. A private read-only copy of the
accepted LXC 113 mirror was used for a complete 1,825-source local preflight;
the build passed twice with identical SHA-256. After staged source-hash and
service-account retrieval checks, that complete candidate was deployed on
2026-10-11 with the prior directory retained at
`/var/lib/aster/knowledge.before-sycl-20261011`. The base-only archive was
never deployed.
See the [Stream A runtime record](../projects/AI%20Projects/evidence/Stream-A-SYCL-runtime-reconciliation-2026-10-11.md).

Copy the archive to Proxmox, replace `/var/lib/aster/knowledge` atomically in
LXC 104, and restore directory/file ownership to `root:aster` with read-only
modes. The builder includes
`docs/Aster-Operations.md` and does not copy Finder `._*` metadata. Never add
private backups, credentials or unreviewed external documents to the snapshot.

The graduated ARR curriculum is sourced from
`docs/reference/ARR-Stack-Operational-Reference.md` and deployed as
`reference/operations/arr-stack.md`. Its provenance entry must remain
`current-with-exclusions` with a review date. Focused tests cover installed
versions and ports, canonical roots and handoff semantics, scheduled mutation
workflows, Prowlarr synchronization coupling and the broker's lack of standing
authority. Current health still comes from the fresh sanitized ARR report,
not the reference's point-in-time example.

### Offline human wiki and derived mirror

The private human source portal is `https://wiki.elliottrook.com`, backed by
LXC 113 (`aster-wiki`, `192.168.20.34`) through Authentik and NPM. Direct
backend access remains blocked. Its daily collector retains exact originals,
publishes only validated human content and builds a deterministic
non-authoritative mirror. Aster consumes that mirror only through its validated
knowledge snapshot and must identify the complete human source and locator.

Production uses mirror pipeline `1.5.0` and `ASTER_DIRECTORY_FIRST=1`. Aster
first scores the validated per-source directory index, then ranks claims within
the selected sources; a missing, stale, malformed or inconclusive directory
index fails back to flat claim ranking. Directory abstracts remain derived
navigation hints, never an authority source. The accepted mirror content hash
is `7bd9e61fd4d522f38d80f7e82157cfd8dae8189a31c066c1fe70f793767e3a24` and
the accepted deterministic Aster archive SHA-256 is
`94f87e3879a4bf749e299e8676de758191e2e04743cefdb2bfae4b6f34e5ea37`.

LXC 113 runs `aster-wiki-collector.timer` daily and
`aster-wiki-corpus-health.timer` monthly. HomeLab Doctor checks the intake,
durable collector state, both schedules and the bounded monthly report. Source
enrollment, quarantine, correction, resume, restore and rollback procedures are
tracked in `services/aster-wiki/README.md` and the human wiki operations
runbook. Restore the human repository, protected originals and accepted lock
before rebuilding the derived mirror or Aster snapshot.

### Accepted-snapshot rollback

Treat a snapshot as accepted only after a clean review/build records its SHA-256
and provenance commits. Before replacing the deployed directory, extract the
candidate into a new, root-owned staging directory and inspect
`.aster-provenance.json`. Keep the current deployed directory intact until the
candidate has passed retrieval checks. If the candidate is wrong, restore the
last accepted archive into a new staging directory, atomically rename it into
place, restore `root:aster` ownership and read-only modes, restart only
`aster-agent.service`, then run the versioned graduation retrieval cases. This
is a knowledge rollback only: it does not alter inference, networking, model
files or credentials. Record the replaced and restored archive hashes in the
project evidence log.

## ARR first-repair production gate

The first repair is limited to dismissing one stale completed Radarr queue
record while preserving media and downloader data. The complete request,
approval, audit and non-reversibility decision is in
`docs/projects/Aster-ARR-First-Repair-Decision.md`.

The source is staged on Aster and TrueNAS, but the execution broker remains
stopped and boot-disabled. Its checked-in default runs as
`aster-arr-broker`, binds only to loopback, denies non-loopback IP traffic and
sets `ASTER_ARR_EXECUTION_ENABLED=false`. The production drop-in changes only
the bind address and allows only Aster's host at the service sandbox; OPNsense
still blocks that path unless an explicitly approved temporary rule is added.
A fresh explicit permission is required for every later live attempt.

After that permission, use this order and stop on any failed check:

1. Record hashes of the reviewed source and current Aster files. Stage the
   broker account, private state directory, service files and Aster endpoint
   update without enabling execution.
2. Start the broker with execution false. Confirm `/v1/execute` is absent,
   missing authorization is denied, the listener and firewall match the exact
   reviewed addresses, and Aster chat still has no execution tool.
3. Provision the broker's private Radarr credential without printing, copying
   or placing it in Aster, Git, logs, prompts or the sanitized report. Open only
   the exact Aster-to-broker and broker-to-Radarr paths required for this test.
4. Run the private candidate issuer once. Zero or multiple eligible records is
   a successful refusal and ends the test. For one candidate, independently
   confirm its stale/completed/non-importing preconditions and review the dry
   run before proceeding.
5. At the final approval moment, run the operator-only approval command with
   the displayed opaque candidate and explicit non-reversibility acceptance.
   Its approval expires after two minutes and stays entirely server-side.
6. Call only Aster's authenticated structured repair endpoint with that opaque
   candidate. Never request execution in chat. Confirm one bounded result and
   that a replay is denied without another Radarr call.
7. Confirm the audit contains only operation, opaque candidate, decision,
   report age, result and timestamp. Then set execution false, remove the
   temporary network allowance and retain the audit as acceptance evidence.

Do not automatically retry `inspection_failed`, `outcome_unknown`,
`postcondition_failed` or a changed precondition. The approval has already
been consumed. Investigate read-only evidence and require a new candidate,
review and permission for any later attempt.

Rollback before a confirmed live action is to stop/disable the execution
broker, restore the accepted Aster source and remove the narrow network
allowance. After a confirmed dismissal there is no queue-record rollback;
media and downloader data remain untouched, but the removed Radarr queue
record is not recreated.

### 2026-09-09 first production gate evidence

- Reviewed commit `6bd7d4e` was staged with rollback copies on TrueNAS,
  Proxmox and LXC 104. Source hashes matched before installation.
- The deployed broker passed 61/61 tests as its unprivileged service account.
  Aster passed 41/41 deployed unit tests, and a disposable dependency-complete
  layout in LXC 104 passed the full 42/42 suite including the authenticated
  Aster → broker → fake Radarr execution path.
- With execution false, Aster reached only the exact temporary
  `192.168.70.10` → `192.168.20.40:9421/TCP` path. Missing authorization was
  denied with `401` and `/v1/execute` was absent with `404`.
- The one permitted private Radarr queue scan returned `status=none`: zero
  records met the exact stale/completed/imported-or-ignored predicate. The
  issuer therefore stored zero candidates and the empty sanitized state was
  pushed to Aster.
- No approval was created, no execution request or Radarr DELETE was sent,
  and no audit attempt exists. Final state was independently checked as zero
  candidates, zero approvals and no audit file.
- Cleanup stopped and boot-disabled the broker, confirmed zero listeners,
  removed the exact temporary OPNsense rule and reconfirmed that Aster's
  broker connection times out. Aster itself remains active and healthy.

The zero-candidate result is a successful fail-closed live eligibility gate.
At Jason's direction, graduation then used the same disposable-fixture method
as the earlier proposal test rather than manufacturing a failure in live
Radarr:

- A locked-down TrueNAS-local disposable endpoint exposed one synthetic queue
  record and accepted only the fixed fixture API key. The deployed broker was
  pointed at that endpoint; its original environment and private state were
  backed up first.
- One synthetic opaque candidate was published through the normal sanitized
  report transport. Aster's authenticated dry-run returned the exact operation
  and four preconditions.
- The operator-only two-minute approval was created and exactly one request was
  sent to Aster's structured endpoint. It returned `completed` with bounded
  result `dismissed`.
- Excluding the fixture readiness probe, the disposable target saw exactly
  collection GET, one queue-record DELETE and verification GET. The DELETE had
  `removeFromClient=false`, `blocklist=false`, `skipRedownload=true` and
  `changeCategory=false`.
- Replay returned `409` and caused no additional disposable-target call. The
  bounded audit was retained at
  `/mnt/Media/data/tools/aster-arr-rollbacks/4125f17-execution-fixture-audit.jsonl`.
- Cleanup restored the original broker environment and state, stopped the
  disposable endpoint, removed the transient execution switch, republished
  zero candidates, stopped/boot-disabled the broker and removed the temporary
  OPNsense rule. Live Radarr was never the configured execution target and was
  not changed.

The single operation is therefore graduated against the production-shaped
broker and disposable mutation target required by the gate. This does not
create standing execution authority: every future live Radarr attempt still
requires one naturally eligible candidate, independent review and fresh
explicit permission.

## Health and logs

### Home Assistant read-only report

Proxmox runs `/usr/local/sbin/refresh-and-push-aster-ha-report` every five
minutes from `/etc/cron.d/aster-ha-report`. Its root-owned producer queries VM
103 only through `qm guest exec ... ha --raw-json` and writes a strict aggregate
report to `/var/lib/aster/ha-report/latest.json` in LXC 104 as `root:aster 0640`.
The report contains only Core/Supervisor versions and booleans, backup-mount
configured/active booleans, and aggregate Resolution counts. It excludes all
entity, device, user, location, automation-state, log, configuration and
credential data. Aster has no Home Assistant token or direct client.

Rollback copies from graduation are under
`/opt/aster-agent/rollback-home-assistant-20260910` in LXC 104. The immediately
prior knowledge tree is `/var/lib/aster/knowledge.failed-run1`; restore the
saved source/unit and prior knowledge tree, reload systemd and restart
`aster-agent.service`. Removing `/etc/cron.d/aster-ha-report` and the Proxmox
producer scripts disables report refresh without changing Home Assistant.

From the Proxmox host:

```sh
pct exec 104 -- systemctl status aster-agent.service
pct exec 104 -- curl -sf http://192.168.70.10:9120/health
pct exec 104 -- journalctl -u aster-agent.service -n 100 --no-pager

pct exec 110 -- systemctl status aster-llama.service
pct exec 110 -- journalctl -u aster-llama.service -n 100 --no-pager
```

`lab doctor` checks both systemd services and the Aster health endpoint.

The B60 must be bound to the host `xe` driver before inference starts. Stale
DRM nodes can remain visible inside LXC 110 even when the host device is
unbound, in which case Mesa silently exposes `llvmpipe` and inference becomes
extremely slow. Verify both layers from Proxmox:

```sh
readlink /sys/bus/pci/devices/0000:04:00.0/driver
pct exec 110 -- vulkaninfo --summary
```

The host path must end in `/xe`. `vulkaninfo` remains a useful independent GPU
visibility check, but does **not** prove that the active SYCL/Level Zero server
is healthy; check `aster-llama.service` and its `/health` endpoint as well.
The former recurring cause was the enabled all-guests `vzdump`
job at 02:30: stop-mode backup started stopped rollback VM 105, whose
persistent `hostpci0: 04:00.0,pcie=1,rombar=0` mapping bound the B60 to
`vfio-pci`, then stopped QEMU without returning it to `xe`. Logs show this
transition near 02:35 on three consecutive nights. The persistent mapping was
removed on 2026-09-15. A subsequent real stop-mode VM 105 backup completed
while all 88 one-second samples remained `xe`, followed by a successful
authenticated Aster generation. Proxmox `driver=keep` is not a fix: it skips
bind/reset preparation while QEMU still requests a `vfio-pci` device.

VM 105 is now a disk/config rollback whose B60 must be attached only for an
intentional rollback. Before starting it, stop host inference, confirm VM 105
is stopped, and attach the device:

```sh
pct exec 110 -- systemctl stop aster-llama.service
qm status 105
qm set 105 --hostpci0 04:00.0,pcie=1,rombar=0
qm start 105
```

When the rollback test/use is over, stop VM 105 and remove the mapping before
restoring host inference. Confirm the VM is stopped before touching drivers:

```sh
qm stop 105
qm status 105
qm set 105 --delete hostpci0
readlink /sys/bus/pci/devices/0000:04:00.0/driver
# If still vfio-pci:
echo 0000:04:00.0 > /sys/bus/pci/drivers/vfio-pci/unbind
echo 0000:04:00.0 > /sys/bus/pci/drivers/xe/bind
pct exec 110 -- systemctl start aster-llama.service
scripts/check-aster-b60.sh
```

If VM 105 is confirmed stopped and `04:00.0` is unexpectedly unbound or held
by `vfio-pci`, stop `aster-llama.service`, bind `0000:04:00.0` through
`/sys/bus/pci/drivers/xe/bind`, then start the service. Do not rebind the device
while VM 105 is running.

After a Proxmox or kernel update, or after any VM 105 use, run the read-only
`scripts/check-aster-b60.sh` command from the Proxmox host before treating
Aster as ready. It verifies the `xe` binding, stopped rollback VM, absence of a
persistent B60 mapping, both Aster services, BMG G21 Vulkan visibility and the
active inference endpoint's health response; it makes no changes. The Vulkan
probe is an independent device check, not a claim that SYCL generation was
tested. HomeLab Doctor enforces the host/service invariants; verify its current
backend-specific coverage separately before relying on it for SYCL health.

The accepted production server uses Q4_0 K/V cache (`-ctk q4_0 -ctv q4_0`).
Matched authenticated Aster workflows on 2026-10-10 measured 10.72–10.99
decode tokens/s after promotion, compared with 5.94–6.69 for Q8_0. The exact
pre-promotion Q8 unit is retained at
`/etc/systemd/system/aster-llama.service.pre-q4-20261010` with SHA-256
`7e3e2d9a4c7d861b18ad2c9c83dc294893ea81f295a25918f76fcf3e0f9c9013`.
If a correctness, stability or device-health regression is attributed to Q4
K/V, restore that unit atomically, run `systemctl daemon-reload`, use the
documented stop/30-second-quiesce/clean-start sequence, then run
`scripts/check-aster-b60.sh` and authenticated generation validation.

## Restart and rollback

The approved B60 full-BAR boot is now the default via
`/etc/default/grub.d/zz-b60-bar.cfg` and `/etc/grub.d/41_b60_bar`, pinned to
7.0.14-23 and its separately verified aligned initramfs. A repeated attended
boot on 2026-10-10 reproduced 32 GiB BAR2 and full CPU-accessible usable VRAM.
Normal 23 and retained 20 entries remain under GRUB Advanced options for
console recovery. Do not remove the pinned kernel or assume a kernel update
will carry the custom helper forward; rebuild and validate before migration.
See `scripts/b60-bar/README.md` for exact hashes and default rollback.

Restart the lightweight harness without reloading the model:

```sh
pct exec 104 -- systemctl restart aster-agent.service
```

Restarting inference reloads the accepted 9B model; validate authenticated
generation afterwards rather than assuming health readiness warmed it:

```sh
pct exec 110 -- systemctl restart aster-llama.service
```

To roll LXC 110 back to Ollama without removing Aster:

```sh
pct exec 110 -- systemctl disable --now aster-llama.service
pct exec 110 -- systemctl enable --now ollama.service
```

Hermes remains installed in LXC 104. Re-enabling it is a separate rollback
decision because its default provider expects Ollama on port 11434 and its full
prompt/tool configuration is substantially slower than Aster.

## Historical acceptance baseline

The following measurements predate the 2026-10-10 9B promotion and are not
current-model performance evidence. See the Stream A
[model-change impact review](../projects/AI%20Projects/evidence/Stream-A-9B-model-change-impact-2026-10-10.md)
for the bounded comparison and unresolved verification.

- First conversation after completed service warm-up: 4.75 seconds.
- Repeated simple conversation: approximately 3.6 seconds.
- Read-only time function after one-pass routing: approximately 10 seconds.
- Grounded current-hardware retrieval: approximately 24 seconds, with the
  answer correctly naming `docs/03-Hardware-Inventory.md`.
- Six earlier direct stability requests: HTTP 200 in 3.28–4.26 seconds.
- The 2026-09-01 multi-source acceptance prompt correctly identified both LXC
  roles, the exact Qwen3.8 model, llama.cpp/Vulkan, the VM 105 rollback path,
  the SYCL/BAR constraint, the first unfinished second-brain task and the stale
  Ollama wording in `docs/projects/completed projects/Local-AI.md`.
- A focused checklist query returned the first three unchecked tasks in order
  from `docs/reference/AI-Hermes-Second-Brain.md`, with no emitted tool-call markup.
- The focused checklist run processed 951 prompt tokens at 77.8 tokens/second
  and decoded at 4.9 tokens/second after B60-to-`xe` binding was restored.

These figures are single-user measurements. Inference intentionally has one
slot, so simultaneous requests queue instead of competing for the B60's memory.


## Canonical Aster speech operations (verified 2026-10-12)

Aster's web client is `https://aster.elliottrook.com/`. `/companion` remains a
compatibility alias for existing Authentik callbacks, installed shortcuts, and
bookmarks; it is no longer a separate interface.

NetBox records the internal TCP 9120 endpoint on the existing `hermesagent`
LXC 104 object as `Aster web and agent API`; the public name remains owned by
the reverse proxy and DNS configuration.
LXC 116 is the network-level Aster Voice Service. Its canonical Kokoro
`bm_daniel` API binds `192.168.70.14:9131`, Home Assistant uses Wyoming TCP
10300, Companion browser TTS uses authenticated AVS1 streaming through the
longer-prefix HTTPS `/voice/v2/` route to 9131, and authenticated 9130
Piper/STT remains for Companion STT and migration rollback and
current Companion transcription. Companion JWT and dedicated service-key
authentication require separate validation: one does not prove the other.

Speech must reach `https://auth.elliottrook.com/application/o/aster-companion/jwks/`
through NPM `192.168.50.23:443`. OPNsense permits that exact source/destination
on Lab VLAN 70, rule UUID `bc811346-6714-44b4-bc65-46e7430f46a8`. An inbound
NPM-to-speech permit alone is insufficient. If voice hangs before transcription,
check this dependency and authentication error classes before tuning Whisper.

`python3 /opt/aster-speech/health_check.py` on LXC 116 checks the legacy API,
canonical API, exact approved voice/model/policy/STT identity, Home Assistant
Wyoming listener, HTTPS ingress, Companion OIDC discovery and JWKS reachability.
It also submits the fixed phrase `Aster health check.` through the authenticated
canonical API with a five-second timeout, accepts only a bounded RIFF/WAVE result
and immediately discards its bytes. It emits sanitized statuses and exits nonzero
on failure. HomeLab Doctor invokes the same probe through Proxmox. After a
candidate restart, allow approximately 15 seconds for model warm-up before
treating an initial refusal as a fault. Speech data is temporary; normal logs
contain timing/size and error categories, not recordings or transcripts.

Prometheus on LXC 109 scrapes `http://192.168.70.14:9131/metrics` every 15
seconds. The application and OPNsense both restrict that path to Prometheus
(`192.168.20.31`); an unauthorized peer receives HTTP 403. Metrics use only
bounded `interactive`/`batch` and outcome labels and expose request/queue
histograms, queue depth, busy workers, cancellations and renderer-error counts.
Beszel remains the owner of LXC 116 CPU, memory, disk and guest availability;
do not duplicate those resource alerts in the application rules.
Prometheus evaluates the five debounced service conditions. Grafana rule
`homelab-aster-voice-service` bridges firing `AsterVoice*` conditions into the
existing HomeLab email policy while preserving alert name/severity labels.
Cancellation is observable but intentionally does not alert by itself.

Reload the phone page after a web deployment. Tap the orb to start/stop recording.
The web UI reports Transcribing, Thinking and Preparing speech; if automatic
playback is blocked, tap the displayed audio Play control. Stop speech ends the
remaining reply. Long replies are spoken in bounded chunks. Typed turns stay silent.
Jason confirmed physical iPhone voice works on 2026-09-23; generated WAV and
AAC/MP4 smoke tests also pass. See `docs/projects/completed projects/Aster-Companion-App.md` for evidence,
rollback checkpoints and pending integration publication.


### Companion close-out operations

See [the operator guide](../runbooks/Aster-Companion.md) for sign-in, personas,
voice, credential locations, revocation and isolated restore steps. The three
personas are `sysadmin`, `media` and `home_assistant`; `enabled_tools` is
intersected with the chosen persona, including any unsolicited model tool calls.

Jason deferred live ARR execution on 2026-09-23. Both production brokers remain
inactive; the retained UI is not an enabled repair capability. The follow-up
preserves human approval outside the chat/AI path.

Speech LXC 116 now has verified local and TrueNAS task-1 backup coverage, with
matching SHA-256 and an isolated restored canonical Kokoro/Whisper round trip.
The restored guest must have its NIC removed and on-boot disabled before start;
use a protected restore-only environment to bind to loopback and select local
ONNX rendering. Doctor checks legacy/canonical speech, approved identity,
synthesis, HA Wyoming, HTTPS ingress, OIDC, JWKS and both backup ages. Homepage has
an additive Aster Companion tile; the legacy Aster Agent tile is retained.
NetBox VM/interface/IP IDs are 16/16/30 and service records cover TCP 9130,
9131 and 10300. The voice guide is published at
`/wiki/services/aster-voice-service/`; the Companion guide remains at
`/wiki/services/aster-companion/`.

Capacity measurement: simultaneous synthetic Companion/news requests took
13.816s/8.905s; speech TTS 1.68s and STT WAV/MP4 0.78s/0.75s. One cold Media
persona prompt evaluation took 110.466s. This is a measured shared-inference
limit, not a latency guarantee; model/hardware/inference changes remain outside
this project. Scheduled news ingest's most recent execution remained successful.


## AI-PAM authority boundary — graduated through M9, 2026-09-26

The shared AI-PAM core and Unix transport on LXC104 bind consumption to the
kernel-authenticated caller, revalidate current policy and lifecycle, invalidate
stale/unbound approvals, and serialize authorization transitions/migration. This
is a corrective boundary change, not authorization to add tools or grants.
The Authentik-backed approval service derives actor, assurance and `auth_time`
server-side. Aster Companion 0.2.2 provides native approval, denial, lifecycle,
history/audit and global emergency controls; privileged actions use isolated
`max_age=0` authentication so a cached browser session cannot satisfy freshness.

The exact hashes and rollout validation are recorded in
[Stage1 evidence](../projects/AI%20Projects/evidence/M1-stage1-deployment.md).
The two services are `homelab-broker` and `homelab-broker-approval`; existing
read/write Forgejo gateways are separate and were not restarted. Stage1 initial
health, catalogue, socket permissions and unauthenticated HTTP denial passed;
the deployment record owns the final observation result.

Recovery checkpoint on104:
`/var/lib/homelab-broker/rollback/m1-stage1-20260926T011710Z`.
Keep it protected: it includes the broker database and old source, not merely
public test fixtures. Backup and isolated restore integrity/count checks passed.
Do not export its contents into Git, prompts or the knowledge mirror.

If authorization integrity is uncertain, stop both broker entrypoints and retain
human SSH access. Do not blindly restore an older DB: it could resurrect an
already consumed authorization. Do not restart old vulnerable code with active
grants. Diagnose and use a reviewed restrictive candidate. A `Type=simple` unit
reporting active does not prove readiness; wait for both sockets and assert a
registered-peer application health response with a bounded timeout.

The active catalogue has four enabled services: `synthetic`, `forgejo-mcp`,
`forgejo-mcp-safe-write` and `lab-operations`. Its eight exact capabilities are
the four synthetic risk-class fixtures, Green Forgejo repository read, Yellow
safe-branch create, Green Doctor latest and Yellow Doctor run. `agent-hermes`
is Operator; the M5 replacement remains Retired as lifecycle evidence.

The read-only `scripts/check-ai-pam.py` Doctor probe is the drift authority for
this deployed shape. It validates database integrity, global enablement, the
exact service/capability catalogue, agent lifecycle, expired active requests,
all five service units and Unix sockets, and OpenBao's CA-validated initialized/
unsealed health response. It never reads an AppRole credential or target secret.
Any intentional catalogue expansion must update its reviewed expected set in
the same change; an unreviewed extra capability is a failure, not auto-adopted.

NetBox owns the existing Aster LXC 104 and OpenBao LXC 117/IP records. AI-PAM's
local Unix sockets create no additional endpoint to register. Homepage's
existing Aster Companion tile is the supported human entry point; do not add a
direct OpenBao, broker or gateway tile. Recovery checkpoint and restrictive
rollback warnings above remain applicable.
