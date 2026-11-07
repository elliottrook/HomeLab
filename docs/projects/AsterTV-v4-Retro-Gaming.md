# AsterTV v4 retro gaming

> Status: Active — Stream A; M4 server infrastructure graduated, M5 design-only
> candidate in review, and all implementation/integration held at the v3 gate
>
> Owner: Jason
>
> Proposed: 2026-11-06
>
> Started: 2026-11-06
>
> Completed: —
>
> Template: the repository's historical `PROJECT.md` structure, tightened by
> `docs/Project-Creation-Standard.md`

## Purpose and desired outcome

Add a controller-first retro game library to AsterTV v4 without turning an
AsterTV appliance into a game-library administrator. A household user should
eventually be able to browse an attractive, curated library, request an absent
game, install an available game to the current appliance, launch it through
Kodi RetroPlayer, and retain saves. Administration, acquisition, verification,
and recovery stay server-side.

The project is deliberately infrastructure-first. The library, acquisition,
broker, storage, security, monitoring, and recovery layers will be designed and
built before any AsterTV v4 page, Kodi add-on, skin mapping, fleet overlay, or
appliance deployment is created.

## Current state and evidence

- AsterTV fleet authority, design authority, v3 source, and current device
  compositions are present under `services/kodi/`.
- The fleet compiler reports Bedroom, Family, and Jen as complete bundle
  candidates; Guest remains an intentional non-deployed candidate. Eligibility
  is not deployment or household acceptance.
- No repository evidence currently satisfies all three release-gate facts:
  AsterTV v3 deployed, owner accepted, and v4 client work explicitly allowed.
  `services/aster-games/config/release-gate.json` therefore fails closed.
- The existing ARR stack provides Prowlarr and SABnzbd. This candidate consumes
  their private APIs but does not change them.
- There is no deployed retro catalogue, canonical ROM storage authority,
  device-sync identity, Aster Games broker, DNS record, firewall rule, backup
  job, NetBox record, or monitoring target yet.
- Upstream evidence reviewed on 2026-11-06 identifies ROMarr 1.8.0 as the
  acquisition/DAT-verification service and RomM 5.4.0 as the catalogue and
  device-sync authority. Their container manifests are digest-pinned in the
  candidate.

## Scope and exclusions

### In scope now — infrastructure phase

- A reproducible, inactive Compose candidate for ROMarr, RomM, MariaDB,
  Valkey, and a narrow Aster Games broker.
- Storage, authority, trust-boundary, identity, backup, restore, observability,
  and deployment contracts.
- A content-minimizing catalogue adapter and idempotent proposal ledger.
- Static validation and synthetic unit tests.
- Planning for an isolated server placement, private ingress, Authentik,
  NetBox, Doctor, Beszel, backups, and operational documentation.

### Authorized Stream A infrastructure work

- Allocate the guest/container and storage datasets.
- Create identities, secret files, private DNS, proxy/Authentik integration,
  firewall rules, NetBox objects, monitoring, backup jobs, and restore fixtures.
- Deploy the server stack and validate a synthetic/public-domain test library.
- Connect ROMarr to the existing Prowlarr and SABnzbd services with scoped
  credentials and a dedicated download category.

### Explicitly excluded until the AsterTV v3 gate passes

- Any `services/kodi/astertv-v4` source.
- Kodi add-on, RetroPlayer core selection, controller mapping, skin XML,
  runtime Games page/dialog/focus implementation, or deployable artwork.
- A retro-gaming fleet overlay, device manifest, bundle, or release plan.
- Any mutation, installation, or test on Jen, Bedroom, Family, or Guest.
- Enabling RomM remote installation or broker proposal execution.
- Changing the AsterTV design authority or declaring a v4 release.

Design-only Games specifications, synthetic fixtures, and focus contracts under
`services/kodi/astertv-design` are authorized before the gate. They remain
candidates and create no runtime or integration authority.

### General exclusions

- Public Internet ingress.
- Downloading content without the required rights; the operator remains
  responsible for lawful sources and platform-specific firmware/BIOS files.
- Committing ROMs, BIOS files, DAT redistribution payloads, account data,
  credentials, API keys, game titles, or save data to Git.
- Modifying existing Radarr, Sonarr, Lidarr, Readarr, Bazarr, Prowlarr, or
  SABnzbd behavior outside dedicated, approved ROMarr integration settings.
- B60 inference, Lab Hours, LLM inference, speech, TTS, or voice output.
- Game streaming through Sunshine/Moonlight in this release. It is a possible
  later project for systems RetroPlayer cannot serve acceptably.

## Authority model

| Fact | Authority | Notes |
|---|---|---|
| Project scope/status/evidence | This document | Milestone evidence is appended; unchecked work is not implied complete |
| AsterTV accepted design | `services/kodi/astertv-design` | Must not be changed in the infrastructure phase |
| Appliance composition | `services/kodi/astertv-fleet` | No retro overlay before the v3 gate |
| v3 deployment/acceptance | Existing AsterTV release evidence + owner acceptance | The gate file is only a derived enforcement record |
| Game catalogue and user metadata | RomM database | ROMarr and AsterTV consume it; neither silently owns it |
| Canonical ROM bytes | Dedicated storage dataset | ROMarr is sole application writer; RomM mounts it read-only |
| Acquisition and DAT decisions | ROMarr state/history | Unverified or ambiguous files do not become trusted silently |
| Saves and play history | RomM assets/database | Future devices use device-bound tokens and sync protocol |
| Requests/install proposals | Aster Games broker SQLite ledger | Proposal-only until a later reviewed execution capability exists |
| Network/IP inventory | NetBox | Created during approved deployment, reconciled against live state |
| Runtime truth | Service/container host | Doctor reports drift; Git does not pretend runtime state |
| Human operations | HomeLab wiki | Updated before operational graduation |
| Aster knowledge | Derived knowledge mirror | Sanitized, non-authoritative, no titles or credentials |

## Architecture and data flows

```text
Household admin browser
  -> private proxy + Authentik
     -> RomM UI (catalogue, accounts, saves)
     -> ROMarr UI (acquisition, verification, quarantine)

Prowlarr --scoped API--> ROMarr --dedicated category--> SABnzbd
                                      |
                                      v
                           untrusted download staging
                                      |
                              DAT verify/quarantine
                                      |
                                      v
                         canonical ROM library dataset
                             |                  |
                        ROMarr rw           RomM ro

Future AsterTV v4 client --device bearer token--> Aster Games Broker
                               |                      |
                        sanitized catalogue       pending proposal
                               |                      |
                               +------ RomM API ------+

No execution arrow exists in the infrastructure release.
```

### Service contract

| Component | Version/pin | Internal port | Role |
|---|---|---:|---|
| ROMarr | 1.8.0 + OCI digest | 6868 | Search, score, acquire, DAT verify, quarantine, import |
| RomM | 5.4.0 + OCI digest | 8080 | Catalogue, users, metadata, saves, device protocol |
| MariaDB | 11.8.5 + OCI digest | 3306 | RomM relational authority |
| Valkey | 8.1.4-alpine + OCI digest | 6379 | RomM cache/background coordination |
| Aster Games Broker | local 0.1.0; digest required at promotion | 8099 | Sanitized reads and pending proposals only |

Candidate UI and broker ports bind to `127.0.0.1` only. State and service
networks are internal. RomM and ROMarr alone join an outbound bridge for
approved metadata and private ARR dependencies; destination restrictions are a
live firewall requirement. Live private ingress will terminate at the
established proxy and will not directly publish container ports.

### Why this software

- ROMarr matches the existing ARR operating model and supports Prowlarr,
  SABnzbd, RomM, DAT verification, duplicate quarantine, and a documented API.
- RomM supplies the missing household library layer: metadata, cover art,
  accounts, saves, play history, client tokens, and a documented device-sync
  protocol. ROMarr remains acquisition rather than presentation authority.
- Kodi RetroPlayer/libretro is the later native AsterTV play route. It preserves
  controller-first operation and avoids a browser-first interface on the TV.
- A custom broker is retained because neither upstream admin API is a suitable
  least-privilege interface for a shared-room appliance.

Rejected for the primary path: ROMarr folder-only mode (no durable household
catalogue or save/device contract), exposing RomM directly to AsterTV (excess
authority and unstable UI coupling), and installing a general-purpose ROM
frontend beside Kodi (duplicates the AsterTV shell and focus model).

## Privacy and security design

- No public ingress. Admin interfaces use private DNS, TLS, proxy policy, and
  Authentik; service-to-service traffic remains on private networks.
- AsterTV never receives ROMarr, Prowlarr, SABnzbd, MariaDB, or RomM admin
  credentials. A future device token is unique, revocable, device-bound, and
  limited to catalog/read/sync operations required by that appliance.
- The broker returns only `id`, display name, platform slug, and cover URL. It
  strips filesystem paths, upstream download URLs, API keys, and arbitrary
  upstream fields.
- Proposal creation is authenticated, idempotent, bounded to two typed actions,
  and cannot execute. Request bodies and game titles are excluded from normal
  operational logs.
- ROMarr is the only application writer to the canonical library. Downloads
  land in a separate untrusted staging tree. RomM mounts canonical ROMs
  read-only.
- The candidate uses digest-pinned upstream images, drops broker capabilities,
  enables `no-new-privileges`, uses a read-only broker root filesystem, and
  requires secrets outside Git.
- BIOS/firmware, ROM provenance, and account data are treated as private. Only
  synthetic fixtures may appear in automated evidence.
- Aster/AI administration posture: a future `ai-aster-games` capability may
  read content-silent health and create a typed pending proposal. It may not
  browse titles, access raw service credentials, approve, execute, acquire,
  delete, quarantine, or deploy. No capability is active in this milestone.
- This project produces no speech and therefore introduces no Aster voice path.

## Pre-start risk assessment

Authorization stream is **Stream A**. On 2026-11-06 Jason directed: “Continue
stream a. Don’t stop until you need my approval. Push at the end of a milestone
and then continue.” This accepts the recorded infrastructure scope, risks,
exclusions, six bounded deployment changes, validation, and rollback envelope.
It also authorizes the required milestone pushes to Forgejo `origin`, followed
by read-only verification of the GitHub protection mirror. It does not waive
non-waivable stop conditions, authorize public exposure, authorize direct
GitHub pushes, or open the AsterTV v3/v4 gate.

| Risk | Likelihood / impact | Control | Residual decision |
|---|---|---|---|
| Unlicensed or unsafe acquisition | Medium / high | Lawful-source policy, dedicated category, interactive first import, DAT verification, quarantine, no credentials/content in Git | Operator must approve real source policy before connection |
| Wrong file written into canonical library | Medium / high | Separate staging, ROMarr sole writer, DAT checks, no overwrite, snapshots and sampled checksums | Synthetic import/rollback proof required |
| AsterTV v4 work destabilizes unfinished v3 | Medium / high | Machine-readable closed gate, validator rejects v4 paths/overlay, no appliance work | Gate opens only on recorded deployment + acceptance |
| Admin API or secret reaches shared-room client | Low / high | Broker mediation, device token, sanitized schema, private network, log minimization | Security test required before client milestone |
| Database or save loss | Low / high | Protected state set, consistent DB dump, snapshots, isolated restore | Deployment blocked until restore passes |
| ARR contention or path mismatch | Medium / medium | Dedicated download category, identical container path contract, staging capacity alert, first import manual | Validate against synthetic fixture before automation |
| Unsupported game/core or controller | Medium / medium | Later platform matrix and physical pilot, no promise from catalogue presence alone | AsterTV milestone owns compatibility |
| External metadata privacy | Medium / low | Minimum providers, document outbound domains, no private save/content upload | Provider choice needs approval |
| Service compromise | Low / high | Digest pins, private ingress, least privilege, read-only mounts, Authentik, update review | CVE/update process required before deployment |
| Capacity exhaustion | Medium / high | Quotas/alerts, staging cleanup, collection limits, separate datasets | Exact sizing from live discovery pending |
| B60 contention | None / high | No inference, schedule, B60 call, or dependency | Lab Hours not applicable unless scope changes |

There are no planned irreversible operations in the current phase. Future
deployment creates new state only. A failed checkpoint, unexpected public
route, missing storage ownership, secret exposure, ambiguous existing ROM
library, or material AsterTV authority drift is an abort condition.

## Persistence and resume plan

- All infrastructure source and tests live under `services/aster-games/`.
- The release gate is explicit and closed; session memory is never sufficient
  to open it.
- Exact upstream manifest digests, policy, API schema, backup contract, and
  milestone evidence are stored in Git without credentials.
- Live state will use durable host storage; container writable layers are never
  authorities.
- Every state-changing milestone starts with a recovery checkpoint and ends
  with evidence, documentation, validation, and a focused local commit.
- Resume by reading this document, checking the worktree, running:

  ```sh
  python3 services/aster-games/validate_stack.py
  python3 -m unittest discover services/aster-games/broker/tests -v
  ```

  Then continue only the first unchecked milestone whose prerequisites pass.

## Milestones

### M0 — Authority, requirements, and software decision

- [x] Recover and apply the repository `PROJECT.md` structure.
- [x] Apply the current Project Creation Standard and select Stream M.
- [x] Recover AsterTV fleet/design authority and validate the current candidate
  compositions without deploying them.
- [x] Select ROMarr + RomM + broker and record rejected alternatives.
- [x] Define the v3 deployment/owner-acceptance gate and infrastructure-first
  boundary.

Gate: design and safety boundaries are explicit enough to build an inactive
candidate without making live or AsterTV changes.

### M1 — Reproducible infrastructure candidate

- [x] Add digest-pinned Compose definitions with private networks, loopback
  diagnostics, read-only RomM library access, and disabled device installs.
- [x] Build the proposal-only Aster Games broker with sanitization,
  authentication, idempotency, and no execution route.
- [x] Add static validation, unit tests, Doctor probe, OpenAPI contract, and
  backup/restore contract.
- [x] Keep secrets, real paths, content, and credentials out of Git.

Gate: local validation and unit tests pass; the candidate contains no AsterTV
v4 implementation and cannot perform acquisition or install without external
deployment-local configuration.

### M2 — Live discovery and deployment design

- [x] Read-only inventory available compute, storage, proxy, Authentik, DNS,
  firewall, NetBox, Doctor, Beszel, backup, and existing ARR paths/identities.
- [x] Select exact guest/container placement, CPU/RAM/storage quotas, VLAN/IP,
  DNS names, UID/GID, datasets, snapshot policy, and recovery targets.
- [x] Define Prowlarr/SABnzbd scoped credentials and dedicated category without
  changing either service.
- [x] Produce the bounded deployment packet and rollback checkpoints.
- [x] Record Jason's Stream A authorization for the infrastructure deployment
  and milestone pushes.

Gate: the implementation packet has no guessed live facts and the recorded
Stream A authorization covers its bounded changes.

### M3 — Deploy protected server infrastructure

- [x] Create the approved guest/container and datasets.
- [x] Deploy pinned services with secrets in the approved source-local custody.
- [x] Add private TLS/Authentik ingress; prove no public or broad LAN exposure.
- [x] Register NetBox, Doctor, Beszel, backups, and operational ownership.
- [x] Build and pin the local broker image by digest.

Gate: all services are healthy and private; acquisition and device installation
remain disabled.

### M4 — Synthetic integration and recovery

- [x] Configure ROMarr with scoped Prowlarr/SABnzbd access and a dedicated
  category.
- [x] Import only a synthetic or distributable public-domain fixture through
  staging, verification, quarantine/restore, and RomM scan.
- [x] Verify sanitized broker catalogue output and pending proposal behavior.
- [x] Complete an isolated app-state restore and sampled media-integrity proof.
- [x] Validate capacity alerts, dependency failure, auth failure, restart,
  upgrade rollback, and no-secret/no-title observability.

Gate: passed 2026-11-07. The server-side platform is recoverable and
operationally accepted under the Stream A envelope. It still does not authorize
AsterTV work.

### G3 — AsterTV v3 prerequisite gate

- [ ] AsterTV v3 is deployed to the intended fleet under fleet authority.
- [ ] Fleet Doctor and exact composition evidence are clean.
- [ ] Jason records household/owner acceptance of v3.
- [ ] Evidence references are added and `v4_client_work_allowed` is explicitly
  approved before the release-gate candidate changes.

Gate: all four facts exist in durable evidence. Server-side infrastructure and
design-only M5 candidate work can finish before this point, but no Kodi,
client, fleet, device, broker-ingress, or integration work can start.

### M5 — AsterTV v4 experience design

- [x] Use the current accepted AsterTV design authority without changing its
  accepted tokens, asset provenance, or existing page contracts.
- [x] Design Games page, platform rails, detail/install dialogs, focus graph,
  controller status, empty/error/loading states, save conflict behavior, and
  accessibility.
- [ ] Define supported platform/core/controller matrix and performance budget.
  The measured Jen performance budget is recorded; the real support matrix is
  intentionally deferred to post-v3 integration testing.
- [ ] Obtain visual and interaction acceptance before fleet implementation.

Gate: the design candidate passes design-engineering acceptance and remains
separate from fleet deployment.

### M6 — Kodi client and fleet candidate

- [ ] Implement a least-privilege Kodi add-on against the broker and a separate
  device-bound RomM sync identity where required.
- [ ] Package reviewed RetroPlayer cores and controller mappings; keep BIOS
  material outside Git and out of bundles.
- [ ] Add an explicit v4 retro overlay to fleet authority, compile exact
  per-device compositions, and build immutable candidates.
- [ ] Prove failure isolation: library/broker outage cannot break normal AsterTV
  navigation or non-game media playback.

Gate: local/synthetic tests and fleet compilation pass; no appliance deploy yet.

### M7 — Physical pilot and fleet rollout

- [ ] Deploy first to the agreed pilot appliance under a bounded change packet.
- [ ] Validate controller-only browse/launch/exit, latency, scaling, audio,
  suspend/resume, save sync/conflict, rollback, and normal AsterTV regression.
- [ ] Obtain household acceptance before expanding one appliance at a time.
- [ ] Keep Guest candidate-only unless separately accepted.

Gate: every deployed appliance matches its accepted composition and Doctor is
clean.

### M8 — Operations, handover, and graduation

- [ ] Complete admin/user runbooks, wiki, mirror, update/rollback workflow,
  credential recovery, and supported-system matrix.
- [ ] Complete 30-day observation with no unresolved severity-high incident.
- [ ] Perform visual UI handover and owner acceptance.
- [ ] Close the project, archive evidence, and record remaining risks.

## Validation and evaluation

Infrastructure gates include:

- digest, network, mount, secret, release-gate, and policy static checks;
- proposal validation, idempotency, sanitization, authentication, unavailable
  dependency, oversized input, and execution-absence tests;
- Compose rendering with deployment-local values and container health checks;
- synthetic end-to-end acquisition/import/catalogue flow;
- authorization tests proving AsterTV cannot reach admin actions or paths;
- dependency interruption, database recovery, stale token, storage-full,
  restart, and rollback tests;
- isolated restore with counts/checksums and no real content in evidence;
- later controller-only physical UI tests and non-game AsterTV regressions;
- content-silent performance measures: catalogue p95, launch p95, CPU/RAM,
  staging throughput, and restore duration.

Graduation requires visual UI review on actual target hardware. API success and
screenshots alone do not establish focus, legibility, controller behavior, or
playback acceptance.

## Observability and operational model

- HomeLab Doctor will check RomM, ROMarr, broker, database dependency, storage
  headroom, backup freshness, restore age, certificate expiry, and release-gate
  consistency with content-silent output.
- Beszel will monitor the selected guest/container resources and disk usage.
- Service health logs may include service, status, duration, proposal UUID, and
  device pseudonym. They must exclude game titles, ROM filenames, save paths,
  API keys, download URLs, request bodies, and credentials.
- Acquisition history remains in ROMarr under admin authentication; it is not
  copied into Aster's general knowledge or monitoring.
- Alerts must distinguish dependency outage, auth failure, capacity pressure,
  backup/restore staleness, and application error.

## Backup, restore, rollback, and disaster recovery

The protected set is defined in
`services/aster-games/contracts/backup-restore.md`. It covers transaction-safe
MariaDB state, RomM config/resources/assets, ROMarr config, broker state, exact
versions, and secret recovery references. Valkey, download staging, and image
layers are reconstructible. Canonical ROM bytes use snapshots plus integrity
manifests appropriate to large media rather than the app-state job.

Rollback order is: stop proposal clients; disable acquisition; stop ROMarr and
broker; restore database and app state to a mutually compatible checkpoint;
restore the previous pinned images; start database/cache, RomM, ROMarr, then
broker; run Doctor and sampled checksums. AsterTV later retains a release-level
rollback to the last accepted non-gaming composition.

No backup task may be declared complete until an isolated restore is proven.

## Integration impact checklist

| Integration | Current decision / required evidence |
|---|---|
| Firewall/VLAN | NPM-only TCP 8080/6868 rules plus an LXC nftables pre-DNAT guard; broker remains internal-only |
| DNS/TLS | Both Pi-holes resolve the two private names to NPM; public resolvers return no record; wildcard TLS verifies |
| Authentik/proxy | Two owner-bound forward-auth applications and NPM hosts active; broker uses separate device auth later |
| DHCP/IPAM/NetBox | Static LXC 129 identity reconciled in NetBox as `192.168.20.38/24`, VLAN 20 |
| Storage/TrueNAS | `Media/Games` (2 TiB quota), dedicated staging, NFS squashing, and 30-day daily snapshots active |
| ARR services | Scoped Prowlarr/SAB credentials are source-local; the dedicated SAB `retro-games` category maps to its relative staging directory; ROMarr acquisition and auto-import remain disabled |
| Backups | All-guests job covers LXC 129; initial 2026-11-06 archive passed; the 2026-11-07 root-only app backup and no-egress isolated restore proof passed |
| Doctor/Beszel | Content-silent semantic Doctor check passes and Beszel reports `Aster Games` up |
| Homepage | Optional admin-only tile after private ingress acceptance |
| Wiki/mirror | Human wiki commit `57c475e` is deployed; accepted sanitized source hash `5418190c…`; mirror pipeline 1.5.0 verifies 1,832 entries with content hash `1efa0cd2…` and nine Aster Games entries |
| Aster/AI admin | No active capability; future read/propose only, source-local broker, execution disabled |
| AsterTV | Design-only candidate authorized and generated; no Kodi/client/fleet/device/integration work until G3 passes |
| B60/Lab Hours | No dependency or competition; not applicable unless scope changes |
| Speech | None |

## Documentation and handover checklist

- [x] Project record and portfolio entry.
- [x] Infrastructure README, example environment, policy, API, Doctor, and
  backup/restore contract.
- [x] Deployment and upgrade runbook.
- [x] Credential creation/rotation/recovery runbook.
- [ ] Supported platform/core/controller matrix.
- [ ] Household user guide and administrator guide.
- [x] NetBox, Doctor, Beszel, backup, wiki, and knowledge-mirror evidence.
- [ ] AsterTV visual handover and accepted screenshots/video on target hardware.

## Graduation and completion gate

Complete means the server platform is private, least-privilege, monitored,
recoverable, and accepted; AsterTV v3 was first deployed and accepted; the v4
Games experience was separately designed and approved; a physical pilot and
bounded rollout passed; normal AsterTV behavior regressed cleanly; and the
household can operate and recover it without this coding session.

Infrastructure completion alone is a milestone, not AsterTV v4 completion.

## Evidence log

### 2026-11-06 — M0 and M1 local candidate

- Recovered the historical Git `PROJECT.md` template and AsterTV fleet/design
  authority without changing live systems.
- Validated the recovered design suite (14 tests), fleet suite (51 tests), and
  current fleet compilation (four devices; three deployment-eligible, Guest
  candidate-only) before this project was created.
- Reviewed official ROMarr, RomM, and Kodi documentation; selected ROMarr 1.8.0
  and RomM 5.4.0 and recorded their distinct authority roles.
- Resolved and pinned multi-platform OCI manifests for ROMarr, RomM, MariaDB,
  Valkey, and the broker's Python base on 2026-11-06.
- Added the inactive Compose candidate, broker, policy/gate, OpenAPI, Doctor,
  backup/restore contract, validator, and synthetic tests.
- No live service, remote repository, AsterTV appliance, Kodi source, fleet
  manifest, DNS, firewall, account, or storage state was changed.

### 2026-11-06 — M2 read-only placement discovery

- Confirmed Proxmox 9.2.20 has about 52.4 GiB available RAM and 551 GiB
  available on `local-lvm`; VMID 129 is unused and the reviewed Debian 13
  template is present.
- Confirmed TrueNAS 25.10.5 has about 13.9 TiB available but only 2.6 GiB
  available RAM. Selected a dedicated unprivileged Proxmox LXC for application
  state and TrueNAS for the canonical ROM dataset/staging boundary.
- Confirmed the healthy live Prowlarr 2.6.5.5623 and SABnzbd 5.1.3 placement,
  ports, shared data root, and Docker network without reading credentials or
  title-level application state.
- Selected candidate VMID 129, VLAN 20 address `192.168.20.38/24`, 4 vCPU,
  6 GiB RAM, 96 GiB root, a 2 TiB quota-bounded `Media/Games` dataset, and
  UID/GID 568 NFS squashing. The address was absent from NetBox and did not
  answer ICMP, but must be rechecked immediately before allocation.
- Added an exact six-change Stream M deployment/validation/rollback packet.
  No dataset, directory, share, guest, address, account, credential, route,
  backup, or monitoring object was created.

### 2026-11-06 — Stream A authorization

- Jason accepted Stream A continuation for the recorded infrastructure scope
  and directed milestone pushes followed by continued execution.
- The AsterTV gate, public-ingress exclusion, credential controls, destructive
  stop conditions, and direct-GitHub-push prohibition remain unchanged.

### 2026-11-06 — M3 protected server infrastructure deployed

- Created TrueNAS dataset `Media/Games` with a 2 TiB quota, dedicated empty
  staging, UID/GID 568 NFS squashing, host-restricted exports, and a 30-day
  daily snapshot task. Proxmox NFSv4.2 mount units use hard mounts with
  `nosuid,nodev,noexec` and passed synthetic write/remove validation.
- Deployed unprivileged Debian 13 LXC 129 `aster-games` at
  `192.168.20.38/24`, MAC `BC:24:11:54:B1:E5`, with 4 vCPU, 6144 MiB RAM,
  96 GiB root, and the two exact bind mounts. NetBox's idempotent identity
  check now passes for the VM, interface, VLAN, address, and two UI services.
- Deployed digest-pinned RomM 5.4.0, ROMarr 1.8.0, MariaDB 11.8.5 and Valkey
  8.1.4 plus local broker image digest
  `sha256:011797a392d211d96626e54d67433d3fc41760e7047e53f9b0880afa99163929`.
  All five health checks pass. Credentials remain root-readable and
  source-local; the transfer of existing ARR keys used one-time RSA-OAEP
  encryption and left no transfer artifacts.
- Added owner-only Authentik forward auth and wildcard-TLS NPM hosts for
  `games.elliottrook.com` and `romarr.elliottrook.com`. Both private DNS
  servers resolve them to NPM, certificate verification succeeds, and
  unauthenticated requests receive the expected Authentik 302. Public DNS has
  no records. OPNsense and the LXC nftables guard allow only NPM to reach the
  direct UI ports; a non-NPM LAN probe was blocked while NPM received HTTP 200.
- Registered and verified the Beszel 0.18.7 agent, added the content-silent
  semantic probe to central Doctor, and completed an initial 1.08 GiB Proxmox
  snapshot archive. The enabled all-guests job provides ongoing coverage.
- ROMarr indexer/download-client enable flags and auto-import remain false;
  the broker has no host listener; device installation remains disabled; the
  release gate still reports `v4_client_work_allowed=false`. No game content
  was acquired, imported, enumerated, or exposed.

### 2026-11-07 — M4 synthetic integration and recovery graduated

- Created the dedicated SABnzbd `retro-games` category after a native SAB
  configuration backup. ROMarr's scoped RomM, Prowlarr, and SABnzbd connection
  tests pass; RomM alone is enabled while Prowlarr, SABnzbd, automatic import,
  scheduled acquisition, device installation, proposal execution, and the v4
  client gate remain disabled.
- Generated one original CC0 deterministic NES-format fixture and a matching
  one-entry Logiqx DAT. Its SHA-256 is
  `769238ade2162466bffdea87fe52fa0943d67a0299c49a0985191dabeb475637`.
  The fixture passed staging, unique DAT classification, canonical import,
  RomM scan, duplicate detection, quarantine, byte-identical restore, and a
  post-restore zero-duplicate audit. No commercial content was used.
- Verified the broker returned exactly the allowlisted catalogue fields,
  created one pending proposal, replayed the idempotency key without a second
  proposal, and exposed no execution capability. The closed release gate was
  independently confirmed.
- Created a root-only application backup with a transaction-consistent MariaDB
  dump, RomM/ROMarr/broker/DAT state, exact runtime/deployment identities,
  secret references only, aggregate counts, and a sampled-media checksum. Its
  complete manifest verifies.
- Restored that backup into a disposable internal Docker network with no
  egress. The 99-second proof matched aggregate state counts and the sampled
  checksum; refused an existing-file overwrite; detected capacity,
  dependency, and authentication failures; recovered after restart; restored
  exact pre-upgrade state; kept Doctor free of titles and credential terms;
  and destroyed every disposable container, network, and runtime path. The
  evidence manifest verifies and production Doctor is healthy afterward.
- Published the operator/credential/recovery runbook and service-registry
  record. The human wiki source commit `57c475e` is deployed and the reviewed
  Aster Games operational reference was accepted with SHA-256
  `5418190c8c1c2608e80687e89f3f6a1ad4fafd4485f6ec9060a164f2645a011d`.
  Mirror pipeline 1.5.0 double-built and verified 1,832 entries, 28 directory
  sources, and nine Aster Games entries at content hash
  `1efa0cd257afb3ab880860b2e2205a4b857174c122b3dbbce8dff3d2f8504a2c`.
- No AsterTV source, Kodi add-on, RetroPlayer/core/controller configuration,
  fleet overlay, appliance token, remote broker ingress, or device mutation
  was created. Work is now held at G3.

### 2026-11-07 — M5 design-only authorization and candidate

- Jason authorized AsterTV design work before v3 while directing that
  integration remain after v3. The durable release gate now records
  `v4_design_work_allowed=true` and keeps `v4_client_work_allowed=false`.
- Restored design-authority bytes matched the accepted `634c58eb` baseline
  before editing. The candidate changes no accepted colors, geometry, motion,
  asset provenance, or existing page contract and adds no Aster-owned raster.
- Added a design-only Games page specification, Games page catalogue mapping,
  eight closed remote focus graphs, and thirteen deterministic synthetic
  1920×1080 review fixtures covering rest, content focus, expanded side-rail
  focus plus its first/last edges, empty, offline, missing-art, long-title,
  detail, install, request, and save-conflict states.
- The candidate prioritizes Continue playing, Ready on this TV, Platforms,
  Library, and conditional Requests; distinguishes Resume, Play, Install, and
  Request; skips disabled actions; and returns focus to the exact prior item
  when it still exists.
- Owner review rejected the first artwork-focus treatment because it appeared
  as a title pill plus a separate three-sided border. The corrected fixture
  uses one continuous jade surface behind the unchanged artwork geometry,
  flowing directly into the deeper title treatment.
- Owner review also identified placeholder side-rail dots and missing compass
  marks in the top filters. The placeholder rail was replaced by the official
  72-pixel Aster rail and exact approved native-size limestone-backed exports.
  Games occupies a new standard slot directly below Music and temporarily uses
  the generic Aster rail icon pending a dedicated accepted Games icon. Every
  Games top-filter pill embeds the exact approved 32×32 plain-compass export.
  The expanded-rail fixture and focus graph now cover all eight destinations,
  Games focus, edge clamping, Back-to-collapse, and exact return focus.
- Jen's measured ceiling constrains the design to 1536 MiB total UI memory,
  256 MiB art cache, two prefetched rows, seven visible box-art tiles, no
  animated background, one simultaneous fade, and 1920-pixel maximum art.
- Design tests pass 22/22, generated outputs reproduce byte-for-byte, all focus
  graphs are closed, and the Aster Games infrastructure validator plus broker
  tests remain green. The visual and interaction candidate still requires
  owner acceptance. Platform/core/controller claims remain deferred until
  real post-v3 integration testing.

## Closeout summary

Server infrastructure graduated at M4 and the M5 design-only candidate is ready
for owner review. The project remains open and implementation-held at G3: no
Kodi, client, fleet, device, broker-ingress, or integration work is authorized
until v3 deployment, clean fleet evidence, Jason's v3 owner acceptance, and
explicit permission to open the v4 client gate are recorded.

