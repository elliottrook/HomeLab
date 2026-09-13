# Aster Local Agent Operations

> Production since: 2026-08-31
> Scope: Lab VLAN 70 only; not a dependency for core HomeLab operation

## Service layout

| Component | Guest | Endpoint | Service |
|---|---|---|---|
| Aster API and browser UI | LXC 104 (`192.168.70.10`) | `http://192.168.70.10:9120` | `aster-agent.service` |
| llama.cpp Vulkan inference | LXC 110 (`192.168.70.12`) | `http://192.168.70.12:11435/v1` | `aster-llama.service` |
| Sanitized Forgejo producer | LXC 108 | Forgejo loopback API only | `aster-forgejo-report.service` |
| Sanitized NetBox producer | LXC 111 | NetBox loopback API only | `aster-netbox-report.service` |
| Source-report transport | Proxmox host | No network endpoint | `aster-source-reports.timer` |

The browser page asks for the Aster bearer key and stores it in that browser's
local storage. The API key is stored only in `/etc/aster/aster.env` in LXC 104.
The separate inference key is stored in that file and in
`/etc/aster-llama.env` in LXC 110. Both files are root-owned, group-readable by
only the corresponding service account, and excluded from Git.

The OpenAI-compatible chat endpoint supports both normal JSON responses and
authenticated server-sent-event streaming. Streaming was added for Hermes
Desktop compatibility; the same bounded function routing and knowledge scope
apply before the upstream stream begins.

## Hermes Desktop compatibility

Hermes Desktop v0.21.0 can use Aster as an OpenAI-compatible custom endpoint:

- endpoint URL: `http://192.168.70.10:9120/v1`;
- provider ID: `aster-local`;
- model: `aster-qwen3.8-27b`;
- declared context: 65,536, which satisfies Hermes' client-side 64K minimum;
- model discovery and use-for-new-chats enabled.

The declared context is compatibility metadata only. llama.cpp still has one
8,192-token slot, so the current roughly 4,900-token Hermes startup prompt fits,
but a sufficiently long session or larger tool prompt may exceed the real slot.
Hermes completed three end-to-end test turns, including streaming, but each
required roughly 65–69 seconds because its full agent prompt was reevaluated.
Use the direct Aster UI for normal conversation speed; keep Hermes for workflows
where its desktop harness is worth the additional latency.

## Runtime configuration

- llama.cpp b10507 (`95c409c13`)
- `unsloth/Qwen3.8-27B-GGUF:UD-IQ4_XS`
- Vulkan, all model layers offloaded
- One 8,192-token slot
- Four CPU threads, batch 256, microbatch 128
- Flash attention; Q8 key/value cache
- Model reasoning disabled by default
- Automatic real-generation warm-up during service start

Systemd does not report `aster-llama.service` fully started until the model is
loaded and warm-up completes. This normally takes roughly 1–2 minutes. The
first real user request then avoids the otherwise roughly 28-second cold path.
The unit allows up to five minutes for startup, while the health and generation
steps inside the warm-up script are independently bounded. This prevents
systemd's 90-second default start timeout from killing a healthy model during a
slow real-generation warm-up.

## Functions and knowledge

Aster 1.0 exposes eight allowlisted read-only functions:

- current time in an IANA timezone;
- Aster or inference health;
- the latest sanitized HomeLab health summary;
- keyword-ranked search of `/var/lib/aster/knowledge`;
- the fixed-path sanitized ARR report;
- the fixed-path sanitized Forgejo report;
- the fixed-path sanitized NetBox report; and
- a dry-run proposal for the one report-issued opaque ARR candidate.

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
Build it from the repository's explicit allowlist after material documentation
changes:

```sh
scripts/build-aster-knowledge-snapshot.sh /tmp/aster-knowledge.tar.gz
```

Copy the archive to Proxmox, replace `/var/lib/aster/knowledge` atomically in
LXC 104, and restore ownership to `aster:aster`. The builder includes
`docs/Aster-Operations.md` and does not copy Finder `._*` metadata. Never add
private backups, credentials or unreviewed external documents to the snapshot.

The graduated ARR curriculum is sourced from
`docs/ARR-Stack-Operational-Reference.md` and deployed as
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

The host path must end in `/xe`, and `vulkaninfo` must list Intel BMG G21 as a
discrete GPU. If VM 105 is confirmed stopped and `04:00.0` is unbound, stop
`aster-llama.service`, bind `0000:04:00.0` through
`/sys/bus/pci/drivers/xe/bind`, then start the service. Do not rebind the device
while VM 105 is running.

After a Proxmox or kernel update, run the read-only
`scripts/check-aster-b60.sh` command from the Proxmox host before treating
Aster as ready. It verifies the `xe` binding, stopped rollback VM, both Aster
services, and BMG G21 Vulkan visibility; it makes no changes.

## Restart and rollback

Restart the lightweight harness without reloading the model:

```sh
pct exec 104 -- systemctl restart aster-agent.service
```

Restarting inference reloads and warms the 27B model:

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

## Acceptance baseline

- First conversation after completed service warm-up: 4.75 seconds.
- Repeated simple conversation: approximately 3.6 seconds.
- Read-only time function after one-pass routing: approximately 10 seconds.
- Grounded current-hardware retrieval: approximately 24 seconds, with the
  answer correctly naming `docs/03-Hardware-Inventory.md`.
- Six earlier direct stability requests: HTTP 200 in 3.28–4.26 seconds.
- The 2026-09-01 multi-source acceptance prompt correctly identified both LXC
  roles, the exact Qwen3.8 model, llama.cpp/Vulkan, the VM 105 rollback path,
  the SYCL/BAR constraint, the first unfinished second-brain task and the stale
  Ollama wording in `docs/projects/Local-AI.md`.
- A focused checklist query returned the first three unchecked tasks in order
  from `docs/AI-Hermes-Second-Brain.md`, with no emitted tool-call markup.
- The focused checklist run processed 951 prompt tokens at 77.8 tokens/second
  and decoded at 4.9 tokens/second after B60-to-`xe` binding was restored.

These figures are single-user measurements. Inference intentionally has one
slot, so simultaneous requests queue instead of competing for the B60's memory.
