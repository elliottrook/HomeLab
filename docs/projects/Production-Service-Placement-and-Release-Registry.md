# Production Service Placement and Release Registry

> **Status:** Active — Stream A; registry milestone complete, maintenance and
> service-specific migrations remain separate
> **Project owner:** Jason
> **Authorization stream:** Stream A approved 2026-10-12 by Jason
> **Approval boundary:** This approval covers the local registry, release-record
> design, documentation reconciliation and read-only evidence work. It does
> not authorize service migrations, production cutovers, credential changes,
> DNS/firewall changes, remote workflow changes or additional remote Git pushes.
> **Service scope:** Existing HomeLab services currently treated as release V1
> **Target:** Stable application services on VLAN 20; management/ingress on
>   VLAN 50; lab and beta on VLAN 70

## Purpose and desired outcome

Create the repeatable control plane for promoting mature services out of the
development lab. The project will inventory current V1 services, classify their
real environment, define a target and exception for each, and establish a
release/deployment record that separates service version from build, model and
configuration revision.

This is a coordination project, not permission to move every service. Each
actual migration remains a bounded milestone with its own risk and rollback.

## Scope and exclusions

In scope: service inventory, V1 baseline assignment, environment/target matrix,
release manifest, ownership, dependencies, DNS/firewall/ingress policy,
backup/restore expectations, migration order and documentation reconciliation.

Out of scope: immediate mass migration, new hardware, public exposure, changing
service behaviour, or replacing the Local AI and News project documents. Those
projects are dependencies and pilots.

## Initial classification

| Service | Current V1 state | Target/disposition |
|---|---|---|
| Local AI platform | Transitional VLAN 70 | Split `ai-lab`/`ai-prod`; handled by its own project |
| News Digest | VLAN 70 direct LAN | First productionisation pilot; handled by its own project |
| Paperless | VLAN 70 backend through VLAN 50 ingress | Controlled application migration after pilot |
| Other mature applications | Confirm from current baseline and project records | VLAN 20 unless a documented exception is safer |

## Authority model and release record

The environment/lifecycle document owns definitions; the network baseline and
NetBox own observed placement; project documents own change scope and evidence;
service references own safe operation; Forgejo owns source history and accepted
release artifacts. No document may infer current live state from a proposed
target.

Each service record must contain:

`service_id`, `service_release` (`V1` for every current service), current
environment, target environment, build/commit or image digest, configuration
revision, owner, dependencies, ingress path, backup/restore reference,
monitoring owner, deployed date and rollback reference.

## Pre-start risk assessment

| Risk | Control | Residual risk |
|---|---|---|
| Inventory claims are mistaken for live state | Dated read-only reconciliation and source authority labels | State can drift after review |
| Moving a guest breaks hidden consumers | Dependency map, staged promotion and lab retention | Undiscovered consumer remains possible |
| Production and lab share secrets/state | Separate identities and explicit data migration | Temporary migration handling is sensitive |
| Registry becomes bureaucracy without evidence | Require each field to support operation, promotion or recovery | Some low-value services may need a lightweight record |

## Milestones and gates

### 0. Inventory and authority reconciliation

- [x] Enumerate the tracked promotion-relevant service/project records and
  current guests/services.
- [x] Assign every currently running service release line V1 without rewriting
  historical iteration or upstream version identifiers.
- [x] Record environment, network, owner, consumers, dependencies and unknowns
  in the [durable release registry](../service-release-registry.md).

**Gate:** every promotion-relevant service has a named owner, source of truth
and confidence level; unresolved artifact/configuration fields are explicit.

### 1. Target placement and migration order

- [x] Classify each service as lab, beta, production application, management /
  ingress, shared platform or explicit exception.
- [x] Choose migration order based on user impact, data durability,
  dependency centrality and rollback ease.
- [x] Define which services remain on VLAN 70 and why, with review dates.

**Gate:** migration proposals do not assume that `.70` is production or `.50`
is a general application network.

### 2. Release registry and promotion procedure

- [x] Add a durable tabular release record for each promotion-relevant service.
- [x] Define build promotion, configuration separation, deployment checkpoint,
  rollback, backup and post-deployment intent/efficiency review.
- [x] Add project-template prompts so new services enter the registry at V1.

**Gate:** an operator can answer “what is running, where, from which artifact,
and how do I roll it back?” without inspecting an arbitrary guest.

### 3. Execute individually approved migrations

- [ ] Produce a project brief for each service selected for movement.
- [ ] Promote the same reviewed release into the target environment; do not
  mutate or casually rename the lab instance.
- [ ] Reconcile DNS, NPM/Auth, firewall, Tailscale, NetBox, Beszel, Doctor,
  backups and handover per service.

**Gate:** each service independently passes its own graduation criteria.

### 4. Documentation adequacy reflection — mandatory

- [ ] Review every changed canonical document and representative operational,
  project, runbook, inventory and historical record.
- [ ] Test whether the documentation distinguishes current fact, transitional
  exception, target design, V1 service release, build revision and historical
  experiment version.
- [ ] Ask a fresh operator to trace one service from user entry point through
  ingress, backend, dependency, monitoring, backup and rollback.
- [ ] Fix stale guidance and create explicit follow-up projects for unresolved
  gaps before declaring the registry complete.

**Gate:** the documentation supports independent operation and future service
creation rather than merely describing this programme.

### 5. Graduation and maintenance

Publish the registry, review dates and exception owners. Graduation requires
sampled live reconciliation, a successful rollback/restore drill, project and
systems-of-record agreement, and Jason's acceptance of remaining single-host
risk. The registry itself does not grant permission for remote changes.

## Integration checklist

- [x] Architecture, Network Design, IP Addressing and Current Baseline —
  lifecycle and transitional placement reconciled; these remain authorities
  for observed state.
- [x] Project Creation Standard and portfolio — registry requirement and
  project sequencing recorded locally; portfolio status remains active until
  final graduation gates are accepted.
- [x] NetBox and service inventory — current records and the live Proxmox
  inventory were compared; unresolved service-artifact fields remain explicit.
- [x] DNS, NPM/Auth, firewall and Tailscale policy — mapped as service-specific
  promotion inputs; no rules, routes or records were changed.
- [x] HomeLab Doctor, Beszel and Prometheus/Grafana — ownership and coverage
  were reconciled from the operational records; no duplicate checks added.
- [x] Backup/restore and operational references — current coverage and known
  restore gaps are recorded per service; no backup data was changed.
- [x] Human wiki and Aster mirror provenance — identified as downstream
  handoff surfaces; no derived mirror was treated as authoritative.
- [x] Service-specific user handovers — correctly deferred to each promotion
  project because the registry changes no user workflow.

## Dependencies and sequencing

Start with this project's read-only inventory and registry design. Run the Local
AI split design in parallel once its baseline is known. Use News as the first
promotion pilot. Migrate Paperless and other mature services only after the
pilot exposes operational gaps. A second Proxmox host remains a later resilience
project, not a prerequisite for this logical separation.

## Close-out record

The registry coordination milestone is complete under the bounded Stream A
approval above. Service-specific migrations and production cutovers remain
separate projects and require their own authorization.

## Read-only Stream M setup handoff — 2026-10-12

This project is the portfolio prerequisite for the two service-specific
promotion projects below. The repository and live Proxmox inventory were
reviewed without changing systems. The current lifecycle interpretation is
unchanged: VLAN 70 is Lab/Beta, VLAN 20 is the production application target,
and VLAN 50 is management/ingress. Every current service remains V1; build,
model and experiment identifiers remain separate fields.

### Evidence captured

- `docs/Environment-and-Release-Lifecycle.md`, `docs/Project-Creation-Standard.md`,
  the portfolio, architecture, network design, addressing, current baseline,
  backup, monitoring and service-reference records were reviewed.
- Read-only Proxmox inventory on `192.168.50.10` confirmed running guests
  including LXC 104, 110, 114, 115 and 116, with VM 105 stopped. LXC 104,
  110, 114 and 116 remain on VLAN 70 at the documented addresses.
- Read-only health checks returned OK for Aster Agent LXC 104, News LXC 114
  and Aster Speech LXC 116. `aster-llama.service` in LXC 110 reported
  `active`.
- Proxmox runtime hostnames are `hermesagent` (104), `ollama-gpu-pilot`
  (110), `news-aggregator` (114) and `aster-speech` (116). The first two are
  historical runtime names and must be reconciled against service identity,
  NetBox and Beszel before any migration or rename decision; no rename was
  performed.

### Ordered dependency handoff

1. Complete the registry's read-only inventory and authority reconciliation,
   including NetBox/Beszel/service identity mapping and confidence labels.
2. Use that baseline to accept the Local AI platform contract and its
   `ai-lab`/`ai-prod` boundaries.
3. Use the registry and AI contract as inputs to the News promotion pilot.
4. Keep each deployment, DNS/firewall change, credential change, cutover and
   remote Git operation separately gated under Stream M; this handoff grants
   none of them.

### Remaining Stream M setup work

- Enumerate all current V1 services and their actual consumers, owners,
  endpoints, configuration revisions, release artifacts and rollback records.
- Reconcile each affected guest/service against NetBox and Beszel, explicitly
  recording deliberate exclusions and historical names.
- Add a machine-readable or tabular registry only after the source authority
  for each field is identified.
- Preserve the mandatory documentation-adequacy reflection as the final
  milestone and require a fresh-operator trace before graduation.

The remaining work is maintenance and service-specific execution, not a reason
to broaden this project into mass migration. A service may leave the registry's
`Pending` fields only through its own approved promotion project.

## Evidence log

| Date | Evidence | Result |
|---|---|---|
| 2026-10-12 | Read-only repository review and Proxmox inventory on `192.168.50.10` | Confirmed the documented VLAN 70/VLAN 20/VLAN 50 lifecycle, running guests, stopped VM 105, and historical runtime names that require identity reconciliation. |
| 2026-10-12 | Read-only health checks for Aster Agent, llama.cpp, Aster Speech and News | Aster Agent, Aster Speech and News returned healthy; `aster-llama.service` was active; News UI and both timers were active. |
| 2026-10-12 | Local synthetic test discovery | News ran 9 tests before the Kokoro test import was blocked by missing `soundfile`; Aster Speech discovery was blocked by missing `jwt`. Gaps are recorded for the appropriate downstream projects. |
| 2026-10-12 | Local commit `6a46bc7` and first approved push | Focused registry files were committed and pushed to Forgejo branch `codex/release-registry-stream-a`; GitHub read-only ref verification reported the same commit. |

## Graduation and current handoff

The durable registry and promotion procedure are complete as a coordination
milestone. Full project graduation remains gated on a sampled rollback/restore
drill, systems-of-record agreement and Jason's explicit acceptance of the
remaining single-host risk. No service migration is implied. The next approved
work should select one service-specific project, starting with the Local AI
platform contract and then News as the first application pilot.

## Read-only baseline registry — 2026-10-12

This is the initial evidence-backed registry slice. `Known` means supported by
the current documented baseline and/or the read-only Proxmox check; `Pending`
means the owning project must capture the exact release/configuration value
before promotion. No target placement below authorises a move.

| Service identity | Release | Current environment / placement | Target or disposition | Artifact/configuration | Dependencies and rollback | Confidence |
|---|---|---|---|---|---|---|
| `local-ai-platform` | V1 | Lab/Beta, VLAN 70: Aster 104 `.10`, llama.cpp 110 `.12`, Speech 116 `.14` | `ai-lab` plus `ai-prod`; production target VLAN 20 or separately approved AI VLAN | Build/model/voice manifest pending; active voice is Kokoro `bm_daniel` / `en-gb` / `0.95` | Consumers and fallback contract owned by Local AI project; LXC/VM archives and model restore evidence documented | High for placement; medium for release manifest |
| `news-aggregator` | V1 | Lab/Beta, LXC 114 `.13`, VLAN 70, direct LAN service | First production application promotion to VLAN 20 with VLAN 50 private ingress | Current source/build and configuration manifest pending | Local AI contract, Authentik/NPM, Doctor, Beszel, backup/restore; retain LXC 114 as rollback | High for placement and health; medium for artifact |
| `paperless` | V1 | Transitional backend, LXC 115 `.15`, VLAN 70, VLAN 50 ingress | Controlled application migration after News pilot | Existing operational reference and reconstruction export; exact release record pending | Authentik/NPM, storage, OCR/summarization and backup boundaries; retain current backend | High for placement; medium for promotion readiness |
| `authentik` / `reverse-proxy` | V1 | Management/ingress, LXC 106 `.22` and LXC 107 `.23`, VLAN 50 | Remain management/ingress; not application targets | Existing service references; exact build record pending | Required by private promotion paths; existing recovery references | High |
| `monitoring` | V1 | Production observability, LXC 109 `.31`, VLAN 20 | Remain production observability | Prometheus/Grafana baseline documented; exact deployed config revision pending | Beszel/Doctor/service-native checks; existing backup/recovery references | High |
| `netbox` | V1 | Production inventory, LXC 111 `.32`, VLAN 20 | Remain production inventory authority | Existing NetBox deployment; snapshot reconciliation date documented | Registry writes, if later approved, must be validated through NetBox API | High |

Infrastructure appliances, storage and the stopped/test Proxmox guests remain
systems of record or recovery dependencies rather than service-promotion
targets in this registry. Their placement is documented in the current network
baseline and must not be relabelled as application V1 merely to fill a table.
