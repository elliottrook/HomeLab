# Fotosforfun hosting and incremental publishing

> Status: Active — Stream A authorized; M0 discovery and charter complete; A1 next
>
> Owners: Alisa (photography and publication approval), Jason Elliott (HomeLab administration and recovery)
>
> Proposed and started: 2026-10-10
>
> Authorization: Stream A for the bounded A1–A6 scope below

## Purpose and desired outcome

Host Alisa's approved `fotosforfun.ca` photography site from the HomeLab and
provide a pleasant private editor that lets her continually add, arrange,
describe, preview and publish photographs without access to Jason's other lab
applications. The public gallery grows over time; publishing never requires a
complete fortnightly replacement.

The editor is a separate Fotosforfun application, not a third pill in the
Photography Content Desk. It may reuse reviewed publishing modules and the
existing publisher/origin hosts, but has an independent process, Unix identity,
database, state tree, release namespace, Authentik application and authorization
policy. This is the first non-owner HomeLab application login and establishes a
least-privilege household-user pattern without creating general lab access.

The public site follows its own approved Fotosforfun design. The private editor
is an Aster-associated internal tool and follows the
[HomeLab UI style guide](../design/HomeLab-UI-Style-Guide.md) and
[app-icon guide](../design/App-Icon-Family.md). This project produces no speech,
so the Aster voice standard is not applicable.

## Current state and evidence

The approved frontend is preserved in the separate Sites repository at
`sites/fotosforfun`, commit `6a6c044ed3ce8197181e2ae68bbffa5a167a285e`.
It is a buildless static export with a private hosted preview and six visibly
credited Unsplash stand-ins. The gallery supports category filters, a keyboard
accessible viewer and previous/next navigation. It has no upload, catalogue,
approval, release or household-user backend.

Required corrections identified during inspection:

- contact mail is incorrectly `hello@fotosforfun.com`; the intended address is
  `hello@fotosforfun.ca`, subject to mailbox activation;
- gallery data are hard-coded in JavaScript and one renderer uses `innerHTML`;
  catalogue-controlled fields must instead be emitted safely;
- all six preview photographs, hero/about imagery and the preview disclosure
  must remain clearly non-production until Alisa supplies approved content.

Read-only live evidence on 2026-10-10:

| System | Evidence and intended role |
|---|---|
| Proxmox 9.2.20 | LXC 124 and 125 are running, unprivileged and on Servers VLAN 20 |
| LXC 124 `tcf-publisher` | 2 vCPU, 2 GiB RAM, 24 GiB disk with 21 GiB free; Python 3.13.5; existing desk and Beszel agent active/enabled |
| LXC 125 `tcf-origin` | 1 vCPU, 1 GiB RAM, 12 GiB disk with 11 GiB free; Nginx 1.26.3, cloudflared 2026.10.0 and Beszel active/enabled |
| Existing photography release roots | Separate `contrast` and `closet` roots are mode 0750; no Fotosforfun root exists |
| Existing public tunnel | `tcf-public-sites` is deliberately dormant with no ingress or DNS routes; it is not authorization to expose Fotosforfun |
| Authentik | Existing convention is owner-direct binding; household group design must be introduced explicitly and tested for denial of unrelated apps |

The current publisher has sufficient measured capacity for the initial service.
A dedicated guest would add recovery and maintenance overhead without a current
resource or isolation need. App-, state- and identity-level separation on LXC
124 is therefore preferred, with migration to a dedicated guest retained as a
future option if load or tenancy changes.

## Scope and exclusions

Stream A authorizes these expected change classes, limited to Fotosforfun:

- create a separate Fotosforfun editor service, database schema, service user,
  state directories, release pipeline, tests and documentation;
- reuse or extract only generic, tested image/release modules from the existing
  publishing code without changing Contrast/Closet behavior;
- create an append-oriented catalogue with explicit retirement/removal,
  ordering, categories, title, alt text, caption/credit, dates and focal point;
- bind the approved frontend to safely generated catalogue output while
  preserving its accepted design and conspicuous sample disclosure;
- create a dedicated Authentik application and `fotosforfun-editors` group,
  an Alisa user, passkey enrolment flow and Jason recovery-administrator binding;
- provide LAN-only HTTPS through the existing NPM/private-DNS pattern with an
  exact host/rule and no public editor route;
- add a separate origin root, forced deployment capability, immutable releases,
  rollback, backup, Doctor/monitoring, NetBox, Homepage and operator guidance;
- use synthetic or expressly approved non-identifying test images until Alisa
  supplies real photographs; and
- prepare `fotosforfun.ca` for a later public launch, without activating public
  DNS/tunnel ingress in the current authorization envelope.

Excluded: access to the existing Content Desk, Homepage dashboard, NAS, Immich,
NetBox, Beszel, SSH, Tailscale administration or other applications; shared
credentials; blanket photo-library access; face identification; public editor
or API; AI approval; automatic publication; sales, booking or tracking; deletion
of original photographs; public tunnel/DNS activation; and replacement/removal
of Apple mail records without a separate verified mail step.

Public exposure is a later non-waivable decision after real content, rights,
mail, edge behavior and rollback are accepted. The public static site may use
the existing dedicated photography tunnel only after that decision; the editor
will not.

## Authority model

- Alisa owns selection, titles, categories, descriptions, rights decisions,
  retirement choices and final publication approval for Fotosforfun.
- Jason owns infrastructure, security policy, recovery and break-glass access.
- The Fotosforfun catalogue database owns published-item state and ordering;
  immutable manifests own exact release content.
- Source photographs remain with their existing photo-library authority. The
  service stores only imports/derivatives and never edits originals.
- The approved Sites commit owns public presentation until a later accepted
  design revision.
- Forgejo owns deployable code/configuration. No photos, private notes, secrets
  or licensed private assets enter the GitHub protection mirror.
- Authentik owns human identity/application bindings; NPM/private DNS own the
  LAN browser route; NetBox owns deployed service/IP facts.
- The HomeLab repository and human wiki own design, operations and recovery
  records. Aster's mirror remains a derived, non-authoritative copy.

## Architecture and data flows

```text
Alisa on home LAN
      |
private HTTPS + Authentik passkey
      |
Fotosforfun Desk (separate process/user/database on LXC 124)
      |  upload -> validate -> orient -> strip EXIF -> derive
      |  draft -> preview -> Alisa approval -> immutable release
      v
restricted forced deployment capability
      |
Fotosforfun release root (static-only LXC 125)
      |
private review route initially
      |
later explicit public-launch gate -> fotosforfun.ca
```

The catalogue is append-oriented. A publish rebuilds the complete static export
from active records so the site remains portable, but prior photographs stay
active unless Alisa deliberately retires them. Removal is soft/reversible by
default. A permanently destructive purge is outside routine publication.

Each record includes an opaque ID, private import hash, sanitized derivative
hashes, title, category, alt text, optional caption/credit/date, focal point,
sort key, visibility/retirement state, version, approval actor/time/hash and
provenance/rights declaration. Hero/about selections and site copy are separate
versioned settings. Every change invalidates the prior approval.

Initial volume is small; publish-time static generation and browser lazy-loading
are sufficient. Add pagination or generated collection pages before a measured
gallery-size/performance threshold is exceeded rather than loading an unbounded
single page forever.

## Privacy and security design

- Alisa receives her own Authentik identity and enrols her own passkey. No
  password or credential is shared with Jason.
- `fotosforfun-editors` is bound only to the Fotosforfun application. A negative
  access matrix must prove Alisa cannot enter Jason's Content Desk or other
  owner-only applications.
- Jason receives a distinct recovery-administrator binding. Direct service
  recovery remains limited to the existing management path.
- The editor listens only on its private host/port and is reachable through an
  exact NPM host, split DNS and narrow NPM-to-service firewall rule. No public
  DNS name or Cloudflare ingress points to it.
- The service runs as a dedicated non-login Unix user with mode-0700 state and
  mode-0600 database/import files. It has no access to the TCF database or brand
  roots and only a Fotosforfun-scoped forced deployment capability.
- Uploads are size/pixel/type bounded; decoded content is validated; EXIF/GPS is
  removed from public derivatives; paths and filenames are never trusted as
  identifiers; scripts, unsafe SVG, links and traversal are rejected.
- Public rendering uses escaped text or DOM `textContent`, never catalogue data
  interpolated into `innerHTML`.
- Logs contain opaque IDs and outcomes, not image bytes, secrets, passkeys,
  personal filenames or raw private metadata.
- AI administration is not initially supported: the app intentionally has no
  general administrative API. Human recovery uses Jason's service/host path.
  A future bounded publishing API requires a dedicated `ai-fotosforfun` identity
  and broker design rather than Alisa's or Jason's identity.

## Pre-start risk assessment and accepted Stream A envelope

Jason selected home-only access and explicitly requested the usual project in
Stream A after accepting the separate-app architecture. This section records
the bounded authorization envelope.

| Risk | Control, rollback and residual decision |
|---|---|
| First non-owner can reach unrelated lab services — high | Dedicated user/group/application; exact binding and LAN route; deny tests against owner apps before handover. Abort on any unexpected access. |
| Shared LXC creates accidental cross-site state access — high | Separate Unix user, database, roots, process and deploy command; file-permission and cross-site negative tests. Roll back service/unit/account additions without touching TCF. |
| Upload exposes private/GPS data — high | Bounded curated imports, metadata stripping and public-derivative inspection; originals never modified. Remove unaccepted imports and rebuild from prior release. |
| Malicious text/file compromises editor or viewer — high | Strict decoders, content limits, safe DOM/static generation, adversarial tests and no executable uploads. Last accepted static release remains served. |
| Bad publication removes or misorders the growing collection — medium/high | Frozen manifest, full preview, explicit approval, atomic activation, immutable prior release and one-step rollback. Soft retirement by default. |
| Authentik/NPM outage blocks Alisa — medium | Static public/review origin remains independent; Jason retains direct private recovery. No weakening to bypass an outage. |
| Mail or DNS changes interrupt other services — high | Not changed in A1–A4; later exact record inventory/checkpoint and separate public/mail gate. |
| Public launch exposes placeholder or unauthorized content — high | No public route in this envelope; sample markers and rights/approval checks block release eligibility. |
| Host failure loses app state — high | Include code, config, DB and current release reconstruction in LXC/off-host backup; verify isolated restore before graduation. Source media retains its separate backup authority. |
| Service contention affects existing publishing — medium | Initial same-host deployment uses measured capacity, bounded jobs/locks and independent service health; monitor resource use and migrate if thresholds are exceeded. |

No destructive or irreversible operation is required. No existing public site,
database, identity binding, tunnel ingress or DNS/mail record will be overwritten.
Before every bounded live milestone, take a configuration/database checkpoint;
abort on failed recovery evidence, permissions broader than specified, unexpected
public reachability, cross-application access, source ambiguity or new material
risk. Platform approval prompts and per-push Forgejo confirmation remain
mandatory even under Stream A.

## Persistence plan

- This document is the durable project state and evidence log.
- All provisioning is idempotent and resolves existing objects before create.
- Schema migrations are versioned and operate on a checkpointed database.
- Candidate and accepted releases use atomic transitions and content hashes.
- Partial builds/staging are never served; the last accepted release survives a
  stopped job, reboot, dependency failure or expired session.
- Secrets and passkey material never enter Git, logs or this document.
- Resume by reading `AGENTS.md`, the project standard, this project, Git status,
  current live state and the last evidence entry before changing anything.

## Milestones

### M0 — charter and discovery

- [x] Inspect the approved frontend, current publishing architecture, project
  standard and live publisher/origin capacity.
- [x] Select a separate app on the existing hosts rather than a third desk pill
  or a new guest.
- [x] Record home-LAN-only editor access, authority boundaries, exclusions,
  risks, rollback and Stream A authorization.
- [x] Add the project to the portfolio and changelog.

Gate: scope is explicit, no live state has changed, and public exposure is not
authorized.

### A1 — preserve source and implement the isolated core

- [ ] Preserve and checksum the approved frontend; retain its private preview.
- [ ] Create the append-oriented schema, isolated store, renderer and tests.
- [ ] Replace unsafe/hard-coded catalogue rendering while preserving design.
- [ ] Implement import validation, derivative generation, draft/approval,
  retirement, ordering, preview, immutable release and rollback semantics.

Gate: local synthetic tests prove growing catalogue behavior, cross-site
separation, safe rendering and source reconstruction.

### A2 — private service and release root

- [ ] Checkpoint LXC 124/125 configuration and current application state.
- [ ] Add dedicated service/deploy identities, state/release roots and units.
- [ ] Deploy private editor and exact Fotosforfun static-origin vhost.
- [ ] Prove reboot, interrupted publication, wrong-site deployment and rollback.

Gate: private origin and editor operate without changing existing sites.

### A3 — Alisa identity and home-LAN access

- [ ] Create the Authentik user and `fotosforfun-editors` group/application.
- [ ] Add exact private NPM, DNS and firewall path; retain direct recovery.
- [ ] Have Alisa enrol a passkey in her browser; do not handle her credential.
- [ ] Prove allowed Fotosforfun access and denied access to owner-only apps.

Gate: Alisa can use only her editor from home and a clean session requires her
passkey.

### A4 — recovery, inventory and observability

- [ ] Add actionable Doctor checks and reconcile Beszel coverage/noise.
- [ ] Add/update NetBox service facts, Homepage tile visibility and runbooks.
- [ ] Protect code/config/database/reconstruction inputs/current release and
  verify an isolated restore plus rollback.
- [ ] Reconcile wiki, Aster mirror, operational references and security inventory.

Gate: failure is detectable and documented recovery is independently proven.

### A5 — private rehearsal and user handover

- [ ] Use only synthetic or expressly approved, non-identifying test photos.
- [ ] Rehearse add, edit, reorder, retire, preview, approve, publish and rollback.
- [ ] Validate desktop/mobile performance and growing-gallery thresholds.
- [ ] Deliver Alisa's plain-language guide and obtain workflow acceptance.

Gate: Alisa and Jason accept the private workflow; placeholders remain visibly
non-production and no public route exists.

### A6 — later public launch gate

- [ ] Replace every stand-in and disclosure only after Alisa approves real
  content, rights, titles, alt text, hero/about imagery and public wording.
- [ ] Activate/verify `hello@fotosforfun.ca` or another accepted contact.
- [ ] Inventory DNS/DNSSEC/mail, edge terms and exact tunnel/hostname changes.
- [ ] Present and obtain a new explicit public-exposure risk decision.
- [ ] Activate exact public static routes, validate external behavior and prove
  rollback without exposing the editor.

Gate: `fotosforfun.ca` serves only approved static derivatives and remains
independent of the private editor. This milestone is not authorized merely by
the current Stream A request.

## Validation and evaluation

Tests include schema migration, duplicate imports, corrupt/oversized/polyglot
files, traversal/symlinks, EXIF/GPS removal, malformed text, XSS, stale approval,
concurrent publish, interrupted activation, soft retirement/reinstatement,
ordering, full rebuild, wrong-site manifests, permission denial, reboot,
dependency loss, backup/restore and two independent normal-workflow passes.

Before graduation, measure generation latency, disk growth, derivative sizes,
browser payload/count, memory/CPU contention, permission surface and operational
friction. Set a measured pagination/collection-page threshold and verify the
service actually makes Alisa's normal photo additions simpler.

## Observability and maintenance

HomeLab Doctor will check the private editor, origin readiness, last successful
publication, backup age and manifest/release drift without inspecting content.
Beszel already monitors both retained guests; reconcile service impact and add
no duplicate host agent. Jason owns infrastructure alerts and upgrades. The
editor shows actionable publication/import failures to Alisa without exposing
system internals.

## Backup, restore and rollback

Protect the Fotosforfun application/configuration, database, sanitized imported
working copies needed for reconstruction, current accepted manifest and bounded
release set through existing LXC and TrueNAS-mirror coverage. Original media
remain under the photo library's separate backup policy. Prove database plus
release restoration into an isolated directory/service and verify checksums
before relying on it. Retain the last accepted release across every failed
deployment and never prune the only known-good copy.

## Integration impact checklist

- [ ] **HomeLab Doctor** — editor/origin/publication/backup/drift checks.
- [ ] **Monitoring/alerting** — Beszel reconciliation; no duplicate agent.
- [ ] **Backup and recovery** — configuration/state/reconstruction restore.
- [ ] **NetBox** — service facts on existing LXC 124/125; no new IP expected.
- [ ] **Human wiki** — Alisa operator guide and Jason recovery notes.
- [ ] **Aster mirror/snapshot** — derived architecture and recovery summary.
- [ ] **Operational references/runbooks** — identity, publishing and restore.
- [x] **Repository documentation** — project, portfolio and changelog created.
- [x] **Diagrams/rack records** — no physical/topology change; service-level
  diagram is contained here.
- [ ] **Homepage/service discovery** — separate tile/visibility policy; Alisa
  must not receive general Homepage access merely to find one application.
- [ ] **Authentication/authorization** — dedicated Authentik user/group/app,
  passkey, denial matrix and Jason recovery.
- [ ] **DNS, certificates and firewall** — exact private route first; public
  route deferred to A6.
- [ ] **Automation and schedules** — manual publish initially; locks/state;
  no recurring content schedule required.
- [ ] **Security inventory** — identity, permissions, patch owner and secrets
  custody/revocation.
- [x] **AI administration integration** — not currently supported; no safe or
  necessary admin API. Human break-glass is Jason's private host/service path.

## Graduation criteria

The project graduates only after A1–A5, recovery proof, integrations, denial
tests, two workflow passes, post-deployment efficiency review, documentation and
Alisa's acceptance are complete. A6 public launch may remain deliberately
deferred without weakening the private application, but the stock preview must
remain clearly marked and private. No unexplained temporary credentials,
bindings, files, rules or routes may remain.

## Evidence log

| Date | Evidence | Result / next action |
|---|---|---|
| 2026-10-10 | Inspected approved commit `6a6c044`, static structure, placeholder credits, `.com` contact mismatch and hard-coded/`innerHTML` gallery path | Accepted public design is preservable; dynamic binding and safe renderer are required |
| 2026-10-10 | Read project standard, current TCF publishing project, authorization guidance and live LXC 124/125 state | Separate app on existing hosts is the least-change architecture; both guests are healthy with substantial capacity |
| 2026-10-10 | Jason selected home-only access and requested project creation and continuation in Stream A | M0 authorization envelope recorded; proceed to A1 without public exposure |

## Close-out

Active. M0 is complete and A1 is next. No live service, identity, network, DNS,
mail or public route changed during project creation.
