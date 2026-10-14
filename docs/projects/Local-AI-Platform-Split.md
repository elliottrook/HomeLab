# Local AI Platform — Lab/Production Split

> **Status:** Active — Stream A; V1 baseline and source contract reconciled; platform split remains open
> **Project owner:** Jason
> **Authorization stream:** Stream A approved 2026-10-12
> **Stream A approval:** Jason approved this project on 2026-10-12 within the
> documented platform-split scope. It covers contract definition, manifests,
> isolated validation, runtime/configuration/state separation and one
> controlled consumer; it does not authorize broader AI permissions, public
> exposure, arbitrary Tailscale routes or an unrecorded release change.
> **Service identity:** `local-ai-platform`
> **Service release:** V1 baseline; model/build versions remain separate
> **Current environment:** VLAN 70 transitional deployment
> **Target environment:** `ai-lab` plus `ai-prod`, with `ai-prod` on VLAN 20
>   or a separately approved AI/service VLAN

## Purpose and desired outcome

Turn Aster, speech and local inference from a successful but mixed lab
deployment into a shared internal platform. Lab consumers may experiment with
models and integrations; production consumers receive a stable API, canonical
Aster voice/visual identity, bounded behaviour, monitoring, fallback and a
documented release manifest.

The platform is infrastructure-like because multiple services depend on it, but
it is not foundational network infrastructure. It must therefore have a stable
service contract without becoming an undocumented single point of failure.

## Current state and evidence

- Aster Agent, Aster Speech and llama.cpp are V1 transitional deployments on
  VLAN 70.
- The active canonical spoken path is Kokoro `bm_daniel`, `en-gb`, speed `0.95`.
- Piper is retained as a tested failsafe only.
- Existing guests, addresses, model builds and recovery evidence remain the
  authorities until this project validates a replacement arrangement.

The live read-only baseline on 2026-10-12 found a material release discrepancy:
LXC 110's active unit is llama.cpp build `b11429`, using SYCL/Level Zero and
`Qwen3.5-9B-Q4_K_M.gguf`, bound to `192.168.70.12:11435`. The repository's
older operational references describe build `b10507`, Vulkan and Qwen3.8 27B.
Jason confirmed on 2026-10-12 that the current Qwen3.5/SYCL deployment is the
accepted V1 baseline. The older b10507/Qwen3.8 Vulkan references are therefore
stale documentation to reconcile; they are not a rollback target unless a
future project explicitly restores them.

## Scope and exclusions

In scope: platform boundaries, lab/prod runtime separation, API and voice
contracts, model/configuration manifests, credentials, state, monitoring,
backup/restore, fallback and one controlled production consumer.

Out of scope: a second physical Proxmox host, general autonomous administration,
new AI permissions, replacement of the existing Aster identity, and broad
Tailscale access to VLAN 70.

## Authority and architecture

The lifecycle model is authoritative for environment and release identity; the
network baseline is authoritative for observed addresses; NetBox is authoritative
for inventory; service references own runtime procedures; and this project owns
the platform contract and promotion evidence.

`ai-lab` and `ai-prod` share the Aster identity contract but do not share
mutable state, production credentials, unreviewed models or arbitrary lab
endpoints. Production consumers must have a documented fallback or graceful
degradation path when the platform is unavailable.

### Single-GPU operating model — accepted 2026-10-12

The lab has one usable inference GPU and it is already needed by Aster, News
and the daily speech workflow. The platform therefore uses one mutually
exclusive physical runtime rather than attempting to run separate GPU-backed
`ai-lab` and `ai-prod` guests concurrently:

- `ai-prod` is the stable V1 contract backed by the accepted Qwen3.5/SYCL
  runtime on LXC 110. Until a second GPU or an approved production placement
  exists, its VLAN 70 location is a documented transitional exception.
- `ai-lab` is an exclusive scheduled host-maintenance mode on the same GPU. It
  uses separate lab state, credentials and artifacts, acquires a whole-host
  maintenance lease, and cannot start while production or backup work owns the
  host. The lease is intentionally exclusive even when a particular experiment
  only needs the GPU: most sessions may leave services untouched, but every
  session is allowed to stop guests, restart components, or reboot the host.
- The daytime path remains Aster/News/Speech production service. News digest
  timers at approximately 06:15 and 17:15 local fixed-offset time are the
  production reservations; lab work must not overlap them.
- Entering lab mode must stop or quiesce production inference cleanly, record
  a checkpoint, run the bounded lab workload, and restore the accepted V1
  production service before the window closes. Failure to restore leaves the
  platform in an explicit degraded state and alerts the operator.

This is a capacity boundary, not high availability. A future VLAN 20
`ai-prod` placement remains a separate network/guest milestone and must not
create a second concurrent GPU consumer.

### Night schedule contract — backup sequence implemented 2026-10-12

The morning digest is proposed to move to 06:15 local fixed-offset time. The
two hours immediately before it are reserved for the future local-AI email and calendar
analysis workload; no lab lease or backup activity may run in that interval:

| Window | Owner | Rule |
|---|---|---|
| 00:30 onward, bounded by completion | Proxmox guest backup | All-guest snapshot job; declare success only after all archives pass their existing completion checks. |
| 01:00 | TrueNAS guest pull | Pulls the normal guest archive set after the Proxmox chain. |
| 02:00 | TrueNAS LXC 110 mirror | Dedicated same-site inference-guest mirror; remains excluded from the off-site relay. |
| 03:00 | TrueNAS Mac pull | Configuration pull completes before the analysis reservation. |
| After backup-chain completion until 04:15 | `ai-lab` | Exclusive whole-host maintenance lease; ordinary sessions may be light, but no other workload may start and restarts/reboots are permitted. |
| 04:15–06:15 | Future local-AI analysis | Reserved for email/calendar analysis; no lab work, Proxmox backup, or LXC110 mirror. |
| 06:15 | News morning digest | Production reservation; lab remains excluded. |

The backup chain includes the Proxmox all-guest archive and its TrueNAS
follow-on pulls, including the dedicated LXC 110 mirror. The bounded
measurement completed successfully on 2026-10-12 in 18m36s; the LXC 110 guest
archive took 5m23s and the historical roughly 6-minute mirror estimate remains
reasonable. The existing 02:30/04:00/04:20 schedule was replaced by the
00:30/01:00/02:00/03:00 sequence after that measurement. No GPU lease,
production service or analysis workload was enabled by this schedule change.

The whole-host lease does not mean that the Proxmox control plane, network
access, UPS protection, recovery console or the minimum monitoring path must be
stopped. It means no nonessential guest, scheduled job, inference consumer,
backup/sync task or automated remediation may run concurrently. The controller
must drain those workloads, acquire a host-level lock, record a pre-lab
checkpoint, and refuse new starts until the lease is released or expires.

## Pre-start risk assessment

| Risk | Control | Residual risk |
|---|---|---|
| A model or voice change affects several consumers | Pinned release manifest, synthetic evaluation and explicit promotion | Shared platform change still has broad impact |
| Production data or credentials enter lab | Separate identities, secrets and test data; deny-by-default network policy | Misconfiguration during migration |
| One Proxmox host remains a shared failure domain | Existing backups, restore evidence and tested fallback | No high availability |
| GPU/CPU contention degrades daily services | Resource envelope, concurrency limit and measured load gate | Capacity remains finite |
| Lab restart leaves production unavailable | Whole-host maintenance lease, pre-lab checkpoint, bounded lease expiry and post-lab restoration/health gate | A failed reboot can extend the degraded window |
| Fallback is documented but not usable | Real failover and recovery test before graduation | Manual intervention may remain necessary |

## Persistence, observability and recovery

Every milestone records a checkpoint, exact build/configuration references and a
resume point. Beszel, HomeLab Doctor, service-native health and existing
Prometheus/Grafana ownership must be reconciled rather than duplicated. Guest
archives, model artifacts, configuration and recovery identities require
protected coverage; restore into an isolated guest before production use.

## Milestones and gates

### 0. Reconcile the platform baseline

- [x] Inventory the live Aster, speech and inference guests, consumers,
  credentials, models, ports, timers, monitoring and recovery references.
- [x] Record the V1 service manifest without relabelling upstream or experiment
  versions. The accepted inference baseline is llama.cpp `b11429`,
  SYCL/Level Zero, Qwen3.5 9B Q4_K_M, one 8,192-token slot, and the existing
  authenticated endpoint on LXC 110.
- [x] Confirm the current Kokoro path and Piper-only fallback status from the
  accepted service documentation; live speech health remains passing.

**Gate:** no unknown production consumer or undocumented dependency remains.

### 1. Define and test the platform contract

- [ ] Define stable API, STT/TTS, health, authentication, identity, quotas,
  timeout and fallback contracts.
- [ ] Define model, voice-asset, build and configuration identifiers separately
  from service release V1.
- [ ] Define which consumers may use lab, beta and production endpoints.

**Gate:** a consumer can target the contract without knowing guest-specific
addresses or internal model details.

### 2. Establish `ai-lab` and `ai-prod`

- [ ] Create separate runtime/configuration/state boundaries on the existing
  host; use a whole-host maintenance lease rather than concurrent workloads.
  The lease must drain nonessential guests and timers, block new starts, and
  explicitly permit component restarts and full host reboots. Keep only the
  minimum Proxmox/network/UPS/recovery control plane needed to operate safely.
- [ ] Exercise both a light lab session and a destructive-maintenance-shaped
  session under the same lease contract; the scheduler must not need a second
  authorization path when the latter is required.
- [ ] Apply distinct credentials, data policy, network policy and deployment
  identities.
- [ ] Deploy the accepted V1 artifact as the production mode and a separately
  identified lab artifact only inside the exclusive lease window, with explicit
  model/configuration differences recorded.

**Gate:** lab changes cannot alter production state, credentials or serving
configuration without an explicit promotion; the host can be drained, restarted
and restored with a recorded checkpoint and health evidence.

### 3. Promote one consumer and prove fallback

- [ ] Move one agreed production consumer to the stable platform endpoint.
- [ ] Validate latency, concurrency, voice identity, failure behaviour and
  resource headroom under representative load.
- [ ] Exercise Kokoro failure and the Piper recovery path without presenting
  Piper as the canonical identity.

**Gate:** the consumer remains safe and understandable through platform loss or
  rollback.

### 4. Documentation adequacy reflection — mandatory

- [ ] Re-read the lifecycle standard, Project Creation Standard, architecture,
  network, IP, baseline, service authorization, Aster operations, AI project,
  backup, monitoring, NetBox and handover records.
- [ ] Ask whether a new operator can identify the current V1 release, target
  environment, endpoint, owner, dependencies, fallback and rollback without
  relying on project history or the implementation agent.
- [ ] Correct stale guidance, add missing links/evidence and create follow-up
  work for gaps; do not silently broaden this project's scope.

**Gate:** documentation and systems of record describe the deployed result, not
just the intended architecture.

### 5. Graduation

Graduation requires all gates, isolated restore evidence, Beszel/Doctor/NetBox
reconciliation, consumer acceptance, a recorded rollback and Jason's accepted
residual-risk statement. The platform remains V1 unless a deliberate V2 release
line is approved.

## Integration checklist

- [ ] HomeLab Doctor and fallback health checks
- [ ] Beszel and Prometheus/Grafana coverage
- [ ] Backup, isolated restore and model/artifact recovery
- [ ] NetBox guests, services, IPs and environment labels
- [ ] Human wiki, Aster mirror and operational references
- [ ] DNS, NPM/Auth, firewall and Tailscale exposure review
- [ ] User-facing handover for affected voice/briefing workflows

## Close-out record

This document is a proposal only. No guest, firewall, DNS, credential, model or
remote repository change is authorised by its creation.

## Read-only Stream M setup handoff — 2026-10-12

This project is dependent on the registry's initial inventory and is the
shared-platform prerequisite for production consumers. No split, deployment,
credential, model, firewall, DNS or remote repository change was performed.

### Evidence captured

- The adopted lifecycle and project standard were reviewed together with the
  architecture, network design, addressing, current baseline, Aster
  operations, backup, monitoring, authorization and portfolio records.
- Read-only Proxmox checks confirmed LXC 104 (`192.168.70.10`, Aster Agent),
  LXC 110 (`192.168.70.12`, GPU-backed inference) and LXC 116
  (`192.168.70.14`, Aster Speech) are running on VLAN 70. VM 105 remains a
  stopped legacy Ollama rollback guest.
- Read-only health checks returned `{"status":"ok"}` for Aster Agent and
  Aster Speech; `aster-llama.service` in LXC 110 is active.
- The documented active voice remains Kokoro ONNX `bm_daniel`, `en-gb`, speed
  `0.95`; Piper remains a tested failsafe only. Existing backup and isolated
  restore evidence is documented for the relevant guests and model artifacts.
- The local Aster Speech unit-test discovery is not currently reproducible on
  this Mac because the available Python environment lacks `jwt`; this is a
  test-environment gap, not evidence of a live service failure. The live
  `/health` check passed.

### Readiness and dependency decisions

- Treat the existing guests as V1 transitional deployments, not as `ai-prod`.
  Do not infer that a healthy VLAN 70 endpoint is a production promotion.
- Before implementation, identify every current consumer and its fallback,
  including News, then define one controlled consumer for the promotion gate.
- Record the exact serving build, model artifact, voice asset, configuration
  revision, credentials custody identifier, resource envelope and rollback
  reference. Do not read or copy secret-bearing files into project evidence.
- Resolve the registry's service-identity versus runtime-hostname mapping for
  LXC 104 and 110 before deciding whether a rename is necessary. This is an
  inventory/documentation issue, not authorization to rename either guest.

### Evidence plan for the next authorized phase

Capture synthetic contract tests, representative latency/concurrency and
resource-headroom measurements, lab/prod state-separation checks, an isolated
restore, a real Kokoro failure/Piper recovery test, and one consumer rollback.
The final milestone must include the mandatory documentation-adequacy
reflection and a fresh-operator trace from consumer to endpoint, dependency,
fallback and recovery.

### Exclusive-window implementation prerequisite

Before installing or enabling a scheduler, choose the recurring local-time
window for exclusive lab work. The schedule must avoid the News 06:15/17:15
production reservations, and any other nightly workload that the live timer
inventory identifies. The target sequence is backup first, whole-host drain and
lab maintenance, analysis from 04:15–06:15, then the 06:15 News reservation.
Before enabling a scheduler, measure one complete backup chain, define the
control-plane survival set and restoration checklist, and obtain explicit
authorization for the bounded Proxmox/TrueNAS schedule change; until then,
test the lease/controller manually only.

## Stream A baseline stop condition — 2026-10-12

Resolved: Jason confirmed that the current b11429/Qwen3.5 SYCL service is the
intended V1 baseline. The remaining work is documentation reconciliation and
validation of the target `ai-prod` boundary; no old-model restoration is
required.

No guest, service, model, credential, DNS, firewall or route was changed while
this discrepancy was being investigated.

## Accepted V1 release manifest

| Field | Accepted value |
|---|---|
| Service identity/release | `local-ai-platform` / V1 |
| Inference guest/endpoint | LXC 110 / `192.168.70.12:11435` |
| Inference build | llama.cpp `b11429` |
| Backend | SYCL / Level Zero GPU path |
| Model | `Qwen3.5-9B-Q4_K_M.gguf` |
| Model artifact | Ollama blob `sha256-cd76ec205963b3b33350093e6904d9de16c4e666fd104e1f632d25c7f15f2a13` |
| Live unit hash | `a4c75169673a1a230682b73d362a05c1bdd30f7a5c41cfb9c77463204dfd4cb3` |
| Live binary hash | `0404f751814391544c86469fa71a893c0f3858e7c7aeb2cb0982909c1c0de6c5` |
| Serving envelope | 8,192-token context, one slot, authenticated API, existing warm-up/readiness gate |
| Speech path | Kokoro `bm_daniel`, `en-gb`, speed `0.95`; Piper retained as failsafe |
| Current environment | Lab/Beta, VLAN 70 |
| Target production environment | `ai-prod` on VLAN 20, subject to target placement validation |
| Rollback | Retain current accepted V1 artifact/configuration and documented guest/model archives; do not restore the obsolete b10507 path implicitly |

## Source-contract reconciliation — 2026-10-12

The first Stream A implementation checkpoint reconciled the deployable Aster
source contract with the accepted live V1 manifest without changing the running
guest. The tracked gateway now defaults to the stable `aster-qwen3.5-9b`
identity, its runtime-identity prompt names Qwen3.5 9B on the B60
SYCL/Level-Zero path, the browser client uses the same model identifier, and the
tracked inference unit/warm-up request points at the b11429 SYCL binary, the
Qwen3.5 9B Q4_K_M artifact and the file-based API-key contract used by the live
unit. Historical Qwen3.8/Vulkan evaluation records remain historical and were
not rewritten into false current results.

Read-only live verification on 2026-10-12 confirmed:

- `aster-llama.service` is active and enabled in LXC 110.
- `http://192.168.70.12:11435/health` returns `{"status":"ok"}`.
- The live unit SHA-256 is
  `a4c75169673a1a230682b73d362a05c1bdd30f7a5c41cfb9c77463204dfd4cb3`.
- The live b11429 SYCL server SHA-256 is
  `0404f751814391544c86469fa71a893c0f3858e7c7aeb2cb0982909c1c0de6c5`.
- The live command binds `192.168.70.12:11435`, uses one 8,192-token slot,
  disables reasoning, and loads `Qwen3.5-9B-Q4_K_M.gguf`.

Validation completed locally with Python bytecode compilation. The full Aster
unit suite could not run on this Mac because its system Python lacks the
repository's `jwt` dependency; no deployment or service restart was attempted.
The next safe action is the contract milestone: define and test the stable API,
health, authentication, quota, timeout and fallback contracts, then validate a
separate lab lease/controller manually before any scheduler is enabled.

## Contract definition checkpoint — 2026-10-12

The stable V1 consumer contract is drafted in
[`docs/reference/Local-AI-Platform-Contract.md`](../reference/Local-AI-Platform-Contract.md).
It defines the logical `ai-lab`/`ai-prod` endpoint boundary, the transitional
mapping, Aster text API and stable model label, Kokoro/Piper speech behavior,
environment-specific authentication, one-slot GPU quota, bounded timeout and
retry behavior, overload handling, observability limits and recovery order.
This is a definition checkpoint only: no consumer was moved, no credential was
created or rotated, no scheduler was enabled, and no fallback or production
traffic test was claimed.

The Forgejo push of the preceding source-contract checkpoint succeeded at
`f942f47`. Its automatic GitHub mirror remained at `6ce8f3e` on two read-only
checks after propagation delay; no direct GitHub push was attempted. This local
contract work is intentionally retained for the next authorized synchronization
window.

## Synthetic contract boundary validation — 2026-10-12

Read-only probes exercised the transitional endpoints without using a credential
or sending a real prompt:

| Probe | Result | Interpretation |
|---|---:|---|
| Aster `/health` without auth | HTTP 200 | Liveness remains intentionally public |
| Aster `/v1/models` without auth | HTTP 401 | Model catalogue is protected |
| Aster `/v1/chat/completions` without auth | HTTP 401 | Conversation surface fails closed |
| Aster `/v1/models` with an invalid bearer | HTTP 401 | Invalid identity fails closed |
| llama.cpp `/v1/models` without auth | HTTP 401 | Backend is not anonymously callable |
| Aster Speech `/health` without auth | HTTP 200 | Speech liveness probe is available |
| Aster Speech `/health` with an invalid bearer | HTTP 200 | Health remains a liveness endpoint, not a data/API grant |

This validates the initial health/auth boundary only. It does not validate a
successful authenticated model call, quota enforcement, timeout behavior,
Kokoro failure/Piper recovery, resource headroom or consumer degradation; those
remain explicit gates and require the appropriate bounded test setup.

## Stream A contract reconciliation — 2026-10-13

The lab-operations gateway response wrapper still advertised the historical
`aster-qwen3.8-27b` label even though the accepted V1 contract is
`aster-qwen3.5-9b`. The local wrapper now uses the contract model constant for
both streaming and non-streaming completion metadata, with a regression
assertion added to the gateway test. The live service was not restarted or
replaced; deployment remains behind the contract validation gate.

The pure lease contract tests pass 4/4, and the installed Proxmox controller
currently reports `ready` with no Local AI timer or systemd scheduler enabled.
The controller's prior bounded light-drain test remains the live evidence for
service stop/restore and control-plane survival. Full model-call, quota,
timeout, speech fallback and consumer-loss tests remain open.

## Authenticated text contract probe — 2026-10-13

Using the existing protected operator environment on Aster LXC 104, a bounded
synthetic prompt with no tools or effectful instructions validated the
transitional text gateway without exposing or copying its credential. The
protected model catalogue returned only `aster-qwen3.5-9b`; the non-streaming
completion returned HTTP 200 with one choice, usage metadata and a 0.333-second
latency; and the streaming completion returned HTTP 200 with four SSE frames,
the expected event-stream content type and a terminal `[DONE]` frame. An
unauthenticated model-catalogue request continued to fail closed with HTTP
401.

This closes the authenticated JSON/streaming shape and stable model-identity
evidence for the text surface. It does not close quota/timeout boundary
behavior, Kokoro failure with Piper recovery, or a controlled consumer's
platform-loss behavior; those remain required before promotion.

## Speech deployment reconciliation — 2026-10-13

The prior speech project already established the intended split: the legacy
`aster-speech.service` on TCP 9130 retains Piper/Whisper for rollback and
Companion STT, while `aster-voice-candidate.service` on TCP 9131 is the
canonical Kokoro service. The candidate uses the pinned Kokoro runtime, asset
digest verification, serialized scheduling and the renderer boundary; the
canonical model assets are not copied into the legacy 9130 service.

Read-only live validation confirmed the candidate is active and its 9131 health
response identifies `aster-voice-candidate`, `kokoro-v1.0`, `aster-bm-daniel`,
voice policy `1` and `aster-base-en` STT. The existing speech health and public
HTTPS/JWKS probes also pass. No speech service was restarted, no asset was
copied, and no renderer or credential was changed in this reconciliation.

The remaining Local AI speech gates are therefore candidate promotion evidence:
authenticated canonical synthesis, a defined consumer response to the
candidate's content-free renderer error/cancellation frame, and one consumer
rollback/degradation check. The candidate's current failure behavior does not
silently switch to Piper; Piper remains the separately operated 9130 rollback
path. The contract has now been aligned with this rollback-based lab protocol
rather than requiring automatic voice switching.

The candidate scheduler/protocol/HTTP tests from the deployed Stream A source
tree pass 18/18, including renderer failure producing a content-free error
frame and explicit cancellation producing a cancellation frame. The web and
native consumers handle those frames as speech errors/termination and do not
switch to Piper or another environment. This is source-level and isolated
candidate evidence; a live renderer-failure injection and operator rollback
exercise remain open.

## Live renderer failure and recovery — 2026-10-13

With explicit continuation authorization, the isolated A380 renderer container
`deployment-renderer-1` was stopped briefly. The canonical LXC 116 9131 TTS
endpoint returned HTTP 502 while the renderer was unavailable; no Piper audio
was returned and no environment switch occurred. The renderer was restarted,
returned healthy after its normal model-load window, and the same canonical
9131 synthesis path returned HTTP 200. This validates the explicit failure
boundary and service recovery without changing routes, credentials or assets.

The operator-facing rollback procedure is now recorded in the platform
contract. It explicitly requires a validated legacy-v1 consumer bundle: the
AVS1/v2 client must never be pointed directly at the raw-WAV 9130 service.
Rollback remains an approved, labelled degraded operation and does not change
the canonical Kokoro identity.

On 2026-10-13 Jason confirmed that the Mac consumer plays canonical speech
correctly. The typed-turn silence behavior is intentional; microphone-originated
turns use the AVS1/v2 stream and play successfully. This closes the consumer
acceptance check without changing the client or speech deployment.

## Schedule implementation record — 2026-10-12

The approved end-to-end measurement completed successfully from 15:50:48 to
16:09:24 local, with all guest archives created and the existing completion
checks passing. The live schedules now read:

| System | Identifier | Schedule |
|---|---|---|
| Proxmox | `backup-49999802-1365` | `00:30` |
| TrueNAS guest pull | task 1 | `01:00` |
| TrueNAS LXC 110 mirror | task 3 | `02:00` |
| TrueNAS Mac pull | task 2 | `03:00` |

The control plane, network, UPS protection and minimum monitoring path remain
outside the lab lease. A manual, disabled-by-default controller is now
installed at `/usr/local/sbin/local-ai-lease` on the Proxmox host; no timer or
systemd service was enabled. Its bounded `--light` mode drains only the three
Local AI production services, records a root-private checkpoint, holds an
explicit lease lock and refuses release until the services and control plane
are healthy. Full guest draining and host restart remain explicit future
operations, not part of this first live test.

## Lease-controller candidate — local only — 2026-10-12

Added a pure planning contract at
[`scripts/local-ai/lease_contract.py`](../../scripts/local-ai/lease_contract.py)
with four local tests. It rejects an unverified/incomplete backup, active
production or conflicting jobs, a closed window and an unavailable host lock;
its release plan refuses to release the lock until restoration and health are
verified. The candidate emits only an ordered action plan and has no Proxmox,
systemd, SSH, network or scheduler side effects. It is now installed as the
manual host adapter but remains unscheduled and disabled.

## Live lease-controller test — 2026-10-12

The approved bounded live test completed successfully at 16:16–16:17 local.
The controller acquired a light service-drain lease after the measured
all-guest backup had completed and no `vzdump`, `rsync` or PBS client process
was active. It recorded a root-private checkpoint, stopped
`aster-agent.service` in LXC 104, `aster-llama.service` in LXC 110 and
`aster-speech.service` in LXC 116, and confirmed all seven Proxmox survival
units remained active: `pve-cluster`, `pvedaemon`, `pvestatd`, `pveproxy`,
`ssh`, `networking` and `nut-monitor`.

Release restored all three services and passed the health gate: Aster
`/health`, llama `/health` and the full LXC 116 speech health check all
returned healthy. The lease state and lock were removed after validation.
The test explicitly permitted neither reboot nor scheduler activation.

## Fixed-source lease observer and restore re-entry — 2026-10-13

The offline lease candidate now binds post-restore verification to a fixed
trusted-host observer rather than accepting a caller-supplied observation
callback. The observer owns the bounded Proxmox/LXC, TrueNAS and News probes,
the fresh owner-heartbeat check, exact runtime identity checks and authenticated
generation probe. Restore re-entry is therefore fail-closed if the observer is
missing, a prior stop/restore/start intent is unpaired, the lease identity
drifts, or the fresh observation does not meet the production gate. Before any
start effect, the observer also checks the individual fixed production unit;
already-active units are skipped and an ambiguous unit state retains the lease
for operator reconciliation rather than risking a blind replay.

The focused local suite passes 31/31 tests, including schedule parsing,
authenticated generation validation, secure manifest custody, fixed-source
probe selection, incomplete restoration, per-unit active-state recovery and
uncertain-effect recovery. The
controller remains advisory-only by default; no live timer or systemd unit was
enabled, and no guest, host or production service was changed. The next gate
is a separately reviewed test-only effect harness and recovery-controller
design before any live deployment or restart-shaped exercise.

## Staging effect boundary and fault injection — 2026-10-13

The candidate now includes a separate shell-free effect runner. It accepts only
the exact allowlisted `pct exec` service start/stop commands, applies a bounded
timeout, and converts timeout, operating-system and nonzero exit failures into
fail-closed effect errors. The watchdog systemd unit and timer remain disabled
candidates with manual start refusal and the required root-owned manifest.

Fault-injection tests cover shell/unknown-command rejection, timeout and
nonzero effect failure, disabled timer/unit properties, per-unit active-state
skipping, and unmatched journal intents. The full focused suite passes 35/35.
A staging manifest records the exact reviewed hashes, fixed probes, `04:15`
recovery deadline, rollback path and the limits of one future attended light
service-drain drill. No candidate file was installed, no timer was enabled and
no live effect was run.

The host-local recovery executor is now the disabled candidate unit's explicit
`ExecStart`: without `--effect-authorized` it emits only a content-free
decision; with the gate it invokes the fixed observer, journaled controller and
effect runner as one bounded restore path. The unit and timer remain refused or
disabled. The exact GGUF file digest is confirmed, but the direct
Proxmox-owner TrueNAS transport check currently fails host-key verification;
that transport setup remains a staging blocker before any live review.

The approved remediation is a bounded host-key enrollment, not relaxed SSH:
after the existing fingerprint comparison, Proxmox may receive a root-owned
mode-0600 `/etc/local-ai-lab/truenas_known_hosts` containing only the verified
TrueNAS key, plus a narrow batch-mode identity if required. The fixed observer
now names that file and requires `StrictHostKeyChecking=yes`; until enrollment
and an owner-context probe succeed, schedule observation remains fail-closed.
The recovery design does not create a new root-to-root grant merely to turn
that check green: local production restoration may proceed, but an unavailable
TrueNAS receipt leaves the lease locked in degraded/unknown state until a
separate least-privilege receipt or operator verification clears it.

## Proxmox TrueNAS host-key enrollment — 2026-10-13

With Jason's bounded authorization, Proxmox received only the verified TrueNAS
ED25519 host key at `/etc/local-ai-lab/truenas_known_hosts`. The directory and
file were read-only verified as root-owned mode `0700` and `0600`, and the
fingerprint matched `SHA256:QBtPEVZCzn5suuM98WY2bGSSvdgOLZ5xpLd17Xu0Xbo`.
The fixed strict-host-key probe reached TrueNAS but returned
`Permission denied (publickey)`. The existing Proxmox `/root/.ssh/id_rsa` was
tested explicitly and was also rejected. No credential was created, copied,
read, rotated or modified. The TrueNAS schedule receipt therefore remains
unknown and the admission gate remains closed.

The accepted dereferenced GGUF was measured read-only at
`cd76ec205963b3b33350093e6904d9de16c4e666fd104e1f632d25c7f15f2a13`; its
5.6 GB hash took approximately 18 seconds including transport. The trusted
observer therefore gives only this model-hash probe a dedicated 30-second
finite budget; all other probes remain bounded at five seconds.

The future live validation is intentionally two-stage: an attended light
service-drain test proves the controller/effect boundary without timer
activation; only after that passes may a separately approved, one-window timer
independence drill temporarily enable the candidate timer, induce one bounded
owner-loss/lease-expiry condition, verify recovery, and disable the timer again.
Neither stage is authorized by the staging work.

Light watchdog ticks now report only heartbeat/control-plane facts; all exact
runtime, GPU, schedule, model, unit and authentication fields remain explicit
unknowns until the bounded restoration observation runs. This prevents a
content-free lease status from being mistaken for exact production admission.

Restore journal reconciliation is also attempt-aware and order-aware. A prior
start observation no longer suppresses the fresh per-unit active probe, and a
second unmatched intent cannot be satisfied by an older observation. Re-entry
therefore remains fail-closed across repeated or interrupted starts.

The current effect controller is not a full shared-lease admission authority:
it cannot independently establish backup completion, News quiescence or
consumer isolation. A candidate evidence shape guard records the required
Proxmox/TrueNAS source, receipt, quiesced News schedule, four production
consumer identities and source marker, but does not authenticate any of them.
The benchmark gate therefore still refuses every Aster benchmark until actual
source adapters produce and verify same-night evidence bound to the lease.
Any light-drain test is preliminary controller/effect validation only.

The offline candidate now defines separate receipt shapes for the fixed backup
chain and Proxmox-owner quiescence observer. Composition requires verified
integrity, same-night timestamps, exact consumer coverage, News quiescence and
an explicit no-new-start observation. These are adapter contracts and tests,
not live provenance; the benchmark gate remains blocked until authenticated
read-only implementations produce them.
