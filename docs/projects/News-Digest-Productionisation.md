# News Digest — Productionisation Pilot

> **Status:** Active — Stream A baseline and promotion preparation
> **Project owner:** Jason
> **Authorization stream:** Stream A — approved continuation 2026-10-12
> **Service identity:** `news-aggregator`
> **Service release:** V1 baseline
> **Current environment:** VLAN 70, direct LAN access on the existing service
> **Target environment:** production application placement on VLAN 20, private
>   HTTPS ingress and authentication through VLAN 50

## Purpose and desired outcome

Use the News Digest as the first complete demonstration of the new lifecycle:
reproducible V1 artifact, lab/beta validation, production deployment, private
remote access, iPhone playback, monitoring, backup and rollback. The objective
is not to make the current lab service broadly reachable; it is to prove that a
stable daily service can be promoted without moving its mutable lab state.

## Current state and evidence

The service is a graduated V1 deployment on LXC 114, VLAN 70, with a local
reading UI and digest/audio pipeline. Kokoro `bm_daniel` is the canonical active
voice; Piper is a tested failsafe only. The current service has existing Doctor,
backup, DNS/firewall and mobile playback evidence. Existing direct LAN access
remains a historical/current-state fact until the pilot changes it.

## Scope and exclusions

In scope: release manifest, production guest or target, application state
separation, private DNS/HTTPS ingress, Authentik/NPM policy, Tailscale path via
already-authorised production routes, iPhone lock/playback acceptance, Doctor,
Beszel, backup/restore and rollback.

Out of scope: a new public WAN exposure, a broad VLAN 70 Tailscale route,
unrelated news-source changes, changing the canonical voice, or redesigning the
whole media acquisition/content desk.

## Architecture and authority

The application repository/build is the release source; the lifecycle document
owns environment and V1 semantics; the network baseline owns observed routes;
NetBox owns the production guest/IP record; NPM/Auth owns private ingress; and
the project owns promotion evidence. Production must run a known V1 artifact
with separate credentials and state, not the existing lab database by mount or
network dependency.

### Selected production placement — pending authorized creation

The selected target is a new unprivileged Proxmox LXC `news-aggregator-prod`
(VMID 126) on Servers VLAN 20 at `192.168.20.12/24`, gateway
`192.168.20.1`. The existing lab LXC 114 remains at `192.168.70.13/24` until
production acceptance. Read-only Servers-VLAN checks found no active ARP or
ICMP response for `.12`; the address is not considered allocated until NetBox,
OPNsense/DNS and the guest configuration are updated and rechecked in the same
change window. VMID 126 is currently unused in the live Proxmox inventory.

Creation, address allocation, firewall/DNS/NPM/Auth changes and any data or
credential migration remain separately authorized implementation steps.

## Pre-start risk assessment

| Risk | Control | Residual risk |
|---|---|---|
| News state or credentials are copied incorrectly | Fresh production state policy, explicit migration decision, backup and restore checkpoint | Historical digest continuity may be partial |
| Remote access exposes an application or admin path | Private DNS, NPM/Auth, source policy and no public port-forward | Proxy/auth misconfiguration can block the owner |
| Audio works on desktop but fails on locked iPhone | Real iPhone lock/background acceptance gate; native audio path retained | iOS behaviour can change with OS/browser updates |
| Production deployment diverges from lab | Same V1 artifact and manifest, no hand-edited production-only code | Configuration differences remain intentional |

## Milestones and gates

### 0. Pre-start discovery and release manifest

- [ ] Capture current V1 commit/build, configuration schema, dependencies,
  timers, data paths, ports, credentials, backup scope and rollback copy.
- [ ] Define what is copied, regenerated or intentionally omitted in production.
- [ ] Record the production DNS, NPM/Auth, firewall, Tailscale and NetBox plan
  before changing any live system.

**Gate:** risk assessment and recovery checkpoint are accepted before mutation.

### 1. Build a beta-quality promotion artifact

- [ ] Reproduce the service from the documented V1 artifact in an isolated
  beta target or disposable production-shaped guest.
- [ ] Run feed, digest, audio, stale-audio, renderer-failure and UI tests.
- [ ] Confirm canonical Kokoro output and documented Piper fallback behaviour.

**Gate:** beta is repeatable and does not use production secrets or state.

### 2. Deploy the production V1 instance

- [ ] Deploy the reviewed artifact to a separate production application target
  on VLAN 20 with its own production IP and service identity. This is a
  placement promotion, not an in-place relabel of LXC114's `192.168.70.13`.
- [ ] Keep the VLAN 70 lab instance reachable and independently stoppable until
  production acceptance, backup/restore evidence and rollback confidence are
  complete; only then perform the planned private DNS/ingress cutover.
- [ ] Configure separate credentials/state and record the release manifest.
- [ ] Add only the required production firewall, DNS, NPM/Auth and NetBox
  records; retain the lab instance until acceptance and rollback confidence.

**Gate:** production and lab identities are independently stoppable and
rollback does not require restoring the lab service.

### 3. Remote and user acceptance

- [ ] Validate the private HTTPS route on Wi-Fi and through Tailscale.
- [ ] Test digest generation, chapter metadata, audio start, pause and resume,
  screen lock, background audio and failure messaging on Jason's iPhone.
- [ ] Confirm no `.70` route was added merely to make the pilot work.

**Gate:** Jason accepts the daily workflow and the service remains private.

### 4. Documentation adequacy reflection — mandatory

- [ ] Re-read the lifecycle, project standard, architecture, network, IP,
  current baseline, service authorization, News project history, Aster voice,
  backup, monitoring, NetBox and user handover documents.
- [ ] Verify they identify V1, lab/beta/prod placement, active Kokoro voice,
  Piper-only fallback, endpoints, owner, rollback and remote-access path.
- [ ] Correct stale “Piper active” or “production on VLAN 70” statements and
  record any remaining gaps as follow-up work.

**Gate:** a future operator can operate and recover the digest without reverse
engineering this project.

### 5. Graduation

Graduation requires production acceptance, backup/restore evidence, monitoring
and inventory reconciliation, a tested rollback to the lab or prior production
artifact, documentation reflection completion and accepted residual risk.

## Integration checklist

- [ ] HomeLab Doctor and stale-audio/renderer checks
- [ ] Beszel for the final guest/service coverage
- [ ] Backup and isolated restore of application/configuration state
- [ ] NetBox, Homepage and operational-reference updates
- [ ] NPM/Auth, DNS, firewall and Tailscale review
- [ ] Human handover for the iPhone daily briefing workflow
- [ ] Aster mirror/wiki update with provenance

## Close-out record

This Stream A phase does not by itself authorise deployment, DNS/firewall
changes, remote access changes, credential changes or a Git push. Each remote
mutation still requires explicit user authorization at the operation boundary.

## Stream A promotion handoff — 2026-10-12

News is the first application promotion pilot. It follows the service registry
and the accepted Local AI Qwen3.5/SYCL contract rather than an arbitrary lab
endpoint. Stream A is limited to baseline reconciliation, reproducible beta
artifact preparation, evidence and promotion planning; no deployment, state
migration, DNS/firewall/authentication, credential or remote repository change
was performed. The separately approved morning digest timer change was applied
and verified in LXC114.

### Live baseline evidence

- LXC 114 `news-aggregator` is running at `192.168.70.13` on VLAN 70 with 8
  GiB memory and 8 vCPUs.
- The application health endpoint is `http://192.168.70.13:8080/healthz` and
  returned `{"status":"ok"}`. The service is bound to the guest address, not
  loopback port 8080.
- The hourly ingest timer and twice-daily digest timer are enabled and active.
  The approved morning timer change is live at 06:15/17:15 fixed-offset time;
  its randomized delay remains 120 seconds. Rollback checkpoint:
  `/root/news-digest-timer.before-20261012` in LXC114.
- Recent digest runs completed successfully: the 2026-10-12 morning run
  processed 21 clusters and generated 8.9 MB audio in about 35 minutes; the
  afternoon run processed 11 clusters and generated 4.2 MB audio in about 16
  minutes. These are observed runtime measurements, not a promise of a fixed
  completion time.
- Kokoro `bm_daniel` remains the active canonical voice and Piper remains the
  failsafe. The live application source still labels the LLM as `qwen3.8-27b`
  in `digest.py`, `summarize.py` and `language_notes.py`, while the accepted
  Local AI service contract is Qwen3.5/SYCL. This stale release label is a
  Stream A reconciliation gate; it must be corrected and tested before a new
  artifact is promoted, without changing the live service blindly.
- The guest is an unprivileged Debian LXC with 16 GiB rootfs, 8 vCPUs and 8
  GiB RAM. Its application state is local to `/opt/news-aggregator`; the
  database is about 29 MiB, static audio/UI state about 7 MiB and local Kokoro
  models about 292 MiB.
- The current Proxmox archive is present and passes the existing archive
  coverage pattern: the 2026-10-12 LXC114 archive is about 2.5 GB, with daily
  prior archives visible. The project still requires an isolated restore check
  before promotion.
- The digest service is a oneshot chain: text generation followed by Kokoro
  audio narration. The API service is separate and serves on guest port 8080;
  no production guest or private ingress has been created by this Stream A
  work.
- The local artifact's nine non-Kokoro unit tests pass. The Kokoro test remains
  blocked on the Mac-only missing `soundfile` dependency. The live guest also
  contains `summarize.py` and `language_notes.py`, so the local release source
  is incomplete until those helper paths are either imported into the artifact
  or explicitly retired from the production contract.

### Evidence captured

- The lifecycle, project standard, portfolio, architecture, network design,
  addressing, current baseline, backup, monitoring, Aster voice and News
  project history were reviewed.
- Read-only Proxmox inventory confirmed News LXC 114 (`news-aggregator`) is
  running at `192.168.70.13/24` on VLAN 70 with 8 GiB memory and 8 vCPUs.
- The service's read-only `/healthz` endpoint returned `{"status":"ok"}`.
- Existing documentation records the News V1 pipeline, Doctor coverage,
  private ingress intent, backup evidence and iPhone playback history. These
  are inputs to the promotion manifest, not proof that production placement
  has occurred.
- Local News unit-test discovery ran 9 tests successfully but could not import
  the Kokoro test because the available Python environment lacks `soundfile`.
  The live `/healthz` check passed; the dependency gap must be closed in the
  beta artifact environment before promotion.

### Readiness and dependency decisions

- The registry must first establish the authoritative V1 artifact, configuration
  revision, consumers, rollback copy and target placement record.
- The Local AI project must define the stable inference/speech contract and
  fallback before News is allowed to depend on `ai-prod`.
- Production must use separate state and credentials. The existing LXC 114
  database, mounts and VLAN 70 endpoint must be retained until acceptance and
  rollback confidence are complete.
- The pilot remains private: no public WAN exposure and no broad VLAN 70
  Tailscale route. Any remote path must use the already-authorized production
  ingress design and be validated on Wi-Fi and Tailscale.

### Evidence plan for the next authorized phase

Build a repeatable beta artifact using synthetic or disposable state; test
feeds, digest generation, canonical Kokoro output, stale-audio and renderer
failure behavior; then validate production DNS/NPM/Auth, firewall, NetBox,
Beszel, Doctor and backup/restore integration. Jason's iPhone acceptance must
cover lock/background playback, pause/resume and failure messaging. The final
milestone must include the mandatory documentation-adequacy reflection and a
fresh-operator handover for the daily briefing workflow.
