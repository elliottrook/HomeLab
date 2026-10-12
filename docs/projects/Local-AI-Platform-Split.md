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

### Night schedule contract — proposed, not yet deployed

The morning digest is proposed to move to 06:15 local fixed-offset time. The
two hours immediately before it are reserved for the future local-AI email and calendar
analysis workload; no lab lease or backup activity may run in that interval:

| Window | Owner | Rule |
|---|---|---|
| 00:30 onward, bounded by completion | Proxmox guest backup | Move the all-guest backup earlier; declare success only after all archives pass their existing completion checks. |
| After backup-chain completion until 04:15 | `ai-lab` | Exclusive whole-host maintenance lease; ordinary sessions may be light, but no other workload may start and restarts/reboots are permitted. |
| 04:15–06:15 | Future local-AI analysis | Reserved for email/calendar analysis; no lab work, Proxmox backup, or LXC110 mirror. |
| 06:15 | News morning digest | Production reservation; lab remains excluded. |

The backup chain includes the Proxmox all-guest archive and its TrueNAS
follow-on pulls, including the dedicated LXC110 mirror. The proposed 00:30
start is intentionally conservative against the observed roughly 19-minute
Proxmox run and the roughly 6-minute LXC110 mirror; exact start offsets remain
subject to one measured end-to-end run and the TrueNAS task ordering. The
existing 04:00/04:20 TrueNAS tasks must not be left in place when the
04:15–06:15 analysis reservation is enabled. This schedule is a design
checkpoint only: no remote timer, Proxmox job, TrueNAS task, GPU lease, or
production service was changed by recording it.

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
