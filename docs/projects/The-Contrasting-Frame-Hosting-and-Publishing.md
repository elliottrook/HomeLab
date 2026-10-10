# The Contrasting Frame and The Closet Fatman publishing

> Status: Active — M0 accepted; dual-site revision incorporated; Stream A authorized; A3 in progress
>
> Owner: Jason Elliott
>
> Proposed: 2026-10-09
>
> Current authorization: Stream A for accepted A1–A6 scope
>
> M0 accepted: 2026-10-09

## Purpose and desired outcome

Host two related but visually distinct photography publications on Jason's own
network: The Contrasting Frame at `https://thecontrastingframe.com` and the more
whimsical The Closet Fatman at `https://theclosetfatman.com`. Provide one
private, AI-assisted Content Desk for both. They share page geometry, image and
story capacity, approval, scheduling and recovery, but never brand packages or
release state. Inference, the editor or a failed job must not take down either
site's last accepted gallery.

Jason requested autonomous completion, but explicitly made the initial milestone
monitored. M0 must discuss and flesh out the design with him, record decisions
and his acceptance of the concrete risks and scope, then transition the project's
single active stream to A. Do not run M and A simultaneously or treat this
planning request as approval of an unspecified Internet exposure.

Applicable visual standards are deliberately split by surface:

- The Contrasting Frame public site and its rendered preview use the
  [The Contrasting Frame style guide](../design/The-Contrasting-Frame-Style-Guide.md);
- The Closet Fatman uses the same page geometry and content slots, with its
  approved logo collection under `/Users/jasonelliott/Documents/The Closet
  Fatman`, a more whimsical website treatment and a different font. Its website
  style/template will be supplied separately and must not be guessed;
- the private Content Desk uses the
  [Aster internal UI style guide](../design/HomeLab-UI-Style-Guide.md) and
  [HomeLab app icon family](../design/App-Icon-Family.md).

An embedded gallery preview uses the selected public brand inside the
Aster-styled operator tool. This project produces no speech; no new voice/TTS
implementation is planned.

## Current state and evidence

The accepted static website is in the separate Sites source repository at:

`/Users/jasonelliott/Documents/ChatGPT/Aster Hardware Development/sites/the-closet-fatman`

Its latest accepted commit is `5b23ccb9d8d746196948246f936427495220ed28`.
The approximately 12 MB `dist/` contains five HTML pages, CSS/JS, full-colour
SVG logos, the dearJoe 4 Regular PRO webfont and demonstration photographs.
Production preview remains owner-private at
https://the-closet-fatman-photography.neat-pixie-1264.chatgpt.site/.
Despite its historical slug, that artifact is the accepted Contrasting Frame
baseline; it is not the new Closet brand package. Do not modify/delete this
recovery/reference site or its audience as part of the migration.

Jason reports ownership of `thecontrastingframe.com` and
`theclosetfatman.com`. Registrar, active DNS zone, nameservers, DNSSEC and mail
records for each must be verified before public launch.
`hello@thecontrastingframe.com` is the intended enquiry address, not a verified
working mailbox. Launch requires either a working mailbox or an accepted interim
contact address; a mail-server deployment is outside scope.

Read-only LAN evidence collected 2026-10-09:

| System | Verified or documented role |
|---|---|
| Proxmox `192.168.50.10` | Live version 9.2.20; local-lvm about 622 GiB available; dedicated guests feasible subject to memory/capacity check |
| TrueNAS `192.168.20.40` | Live `Media` pool about 10.8 TiB available |
| Existing photography | Live `Media/Photos`, `Archive`, `archive_main`; 47.3 GiB collectively; canonical source and rights not yet identified |
| Recovery | Live `Recovery/photos`: 96 KiB used, 1.20 TiB quota; this is not evidence that photos are backed up |
| Forgejo `192.168.20.30` | Live `jason/homelab` main `2f929145953445b1be3695f02ee5c969bc1e9c1a`; standards read directly through SSH |
| Reverse proxy `192.168.50.23` | Existing NPM/Cloudflare pattern documented in LXC 107; runtime connector/route settings still need sanitized verification |
| Local AI `192.168.70.12` | Documented llama.cpp inference in LXC 110; authenticated/broker path to be verified, not a new model deployment |
| Private access | Documented Authentik and Tailscale, with default-deny VLAN boundaries |

The two standard/style-guide blobs in this working checkout match Forgejo main
exactly before these changes. The checkout itself has additional local history:
base `5d260ba6bf14ff786579b353d5d44c314000e3e7`.
Its origin is a local clone/mirror chain, not the live Forgejo URL. Do not push
that entire history or mistake a local push for Forgejo synchronization.

## Scope and exclusions

After M0, the proposed A authorization covers: dedicated scoped datasets/ACLs;
two small unprivileged guests; static-server and private editor deployment;
a restricted importer/image renderer, local AI draft suggestions, review queue,
scheduled publisher, reversible release storage; narrow approved DNS/TLS/tunnel
or edge rules; backup, monitoring, NetBox, runbooks and operator training.
One backend serves both publications. Every content record, asset root,
approval, schedule, build and release carries an immutable site key:
`contrast` or `closet`. Mixed-site manifests are invalid.
Exact guest IDs, addresses, ports, accounts and public route must be approved
in M0 and uniqueness checked immediately before allocation.

Excluded: store/cart/payments, client booking, self-hosted email, moving/deleting
master libraries, blanket NAS scanning, facial
recognition, autonomous publication of unreviewed writing, cloud AI uploads,
new WAN port forwards, broad VLAN permits, unrelated service repair, changing
existing sharing/SSO/tunnel routes, public administration, and automatic
retirement of the Sites preview. Paid service purchases require Jason's decision.

## Authority and ownership

- Jason owns photograph selection, rights/consent, factual claims, narrative,
  approval, scheduling and final design decisions.
- Existing photo repository owns original files; the TCF publishing repository
  owns curated copies, story versions and explicit approved manifests.
- Forgejo owns source/templates/configuration. Keep private licensed assets
  outside a public mirror; check the existing GitHub mirror's audience first.
- NetBox owns allocated guest/IP/service facts; live deployed state verifies them.
- DNS provider owns public records; OPNsense and local resolvers own LAN policy.
- OpenBao/broker owns machine-secret custody; no values in Git or prompts.
- This project and the operational reference record accepted decisions and proof.
  Wiki/Aster snapshots are derived knowledge, not approval or runtime authority.

## Recommended storage

Create dedicated datasets only after M0, provisionally:

| Location | Content and access |
|---|---|
| `Media/TheContrastingFrame/library` | Curated master/export copies from the selected source, checksums and provenance; editor/importer read-only |
| `Media/TheContrastingFrame/brand` | Site-scoped logo masters/variants, licensed fonts, EULAs and receipts; private, selective per-domain webfont deployment |
| `Media/TheContrastingFrame/content` | Versioned Markdown stories, metadata, approved snapshots and scheduled collection manifests |
| `Media/TheContrastingFrame/workflow` | Private review DB/state and draft suggestions; editor-only writes, bounded retention |
| `Media/TheContrastingFrame/releases` | Complete immutable site exports and checksum manifests; publisher writes, backup reads |
| `Recovery/contrasting-frame` | Independent protected copy of scoped state, source reconstruction and approved assets; quota/retention set in M0 |

Paths above are proposals, not currently existing datasets. Prefer these to the
Mac Downloads/Documents folder or a general media/Immich application directory.
Do not rename or consolidate `Media/Photos/Archive` and `archive_main`.
Identify the actual source before importing; add selected copies without
overwriting masters. Source photos may remain in the existing repository.
Expose only a curated folder to automation, never the whole NAS.

Use SMB for Jason's optional Finder editing workflow; service NFS/SMB mounts
must be source-address restricted with tested UID/ACL mapping. Do not rely
on an unprivileged LXC's assumed root identity for NAS permissions.
The public host gets a local release copy, no NAS mount or source credentials.
Keep source code and manifests in a dedicated private TCF Forgejo repository
if agreed; infrastructure planning remains in homelab. Do not mirror proprietary
font packs, originals, private notes or approvals to public GitHub.

## Proposed architecture and data flow

Use two isolated unprivileged Proxmox guests on Servers VLAN 20, each with
guest firewall default-deny and exact inter-VLAN exceptions. Reassess a separate
DMZ only if M0 finds the current isolation insufficient; no new VLAN is assumed.

1. **TCF publisher/private Content Desk:** initial sizing 2 vCPU, 1–2 GiB RAM,
   16–32 GiB local disk, plus narrowly mounted private TCF datasets.
   It scans only the approved source folder, prepares candidates, renders
   previews and schedules approved releases.
2. **TCF public static origin:** initial sizing 1 vCPU, 512 MiB–1 GiB RAM,
   8–16 GiB local disk plus quota-controlled release storage.
   Static Nginx or Caddy, no editor, model, database, NAS mount or Docker socket.
   Serve only the selected accepted release read-only.

```text
Chosen private photo folder + Jason's Markdown stories
                      |
              Content Desk / publisher
           local AI suggestions -> human review
                      |
       site-bound approved version + scheduled publish_at
                      |
      validate complete site-specific static release
                      |
       scoped deploy -> shared static origin vhosts
                      |
        approved public HTTPS edge per domain
             /                         \
thecontrastingframe.com        theclosetfatman.com
```

The desk exposes a prominent `Contrast` / `Closet` pill and keeps that choice
visible through import, editing, preview, approval and scheduling. Switching
the pill changes the preview theme and destination; it never silently moves a
record between sites. Release roots and manifests remain separate per site.

The publisher may contact the local inference capability through the existing
authenticated service/broker pattern, with a dedicated `ai-tcf-editor` identity.
Do not invent a currently available vision capability: default to text based on
Jason's notes and manually supplied image descriptions. Optional local visual
analysis needs an explicitly verified model and its own evaluation.

Deployment uses an exact-target forced-command SSH account or narrowly scoped
authenticated deployment endpoint. It may stage/switch TCF releases, not run
arbitrary shell/root commands or administer DNS/firewalls. The inference identity
has no deployment capability. The public origin must not initiate connections to
private storage, Forgejo, Aster, OpenBao, editor or network administration.

Private editor: the LAN/Tailscale-only HTTPS name
`tcf.elliottrook.com` through NPM and Authentik owner-only access, plus a
documented break-glass path. No Cloudflare public route to it.

## Public domain and delivery decision

Preferred candidate: a dedicated TCF Cloudflare Tunnel/connector co-located
with the static origin and routing to loopback. This avoids giving an existing
Management-VLAN connector new reach and needs no inbound WAN port forward.
Only the exact gallery hostname(s) are published; unmatched routes return 404.
The tunnel remains a third-party public edge: public images traverse that service.

Cloudflare's current documentation requires a domain on Cloudflare for the
normal published-application flow and outbound connector reach on port 7844.
Preserve DNSSEC, MX/TXT and unrelated records when changing nameservers.
Registrar ownership is not evidence that DNS is already hosted there.
Select apex canonical URL and `www` redirect, HTTPS, certificate renewal,
correct forwarding headers, Host allowlist, content security policy, asset
cache busting and low/stale-aware HTML caching. Never disable origin TLS
verification for a remote origin; local loopback HTTP is a different boundary.

**M0 delivery gate:** this is image-heavy. Do not promise free/unlimited CDN use.
Assess Cloudflare's current non-HTML/large-file terms and expected image traffic.
If unsuitable, compare (a) a small public VPS HTTPS edge with encrypted
point-to-point connection to the read-only internal origin, and (b) an approved
image-delivery service holding only public derivatives. A VPS is not permission
for public home-IP records or WAN port forwarding. Costs and any cloud copy
require acceptance; keep internal hosting as the origin and private authority.

Public release includes only licensed public derivatives and approved text.
Remove demonstration assets or retain only clearly attributed, permitted items
that Jason explicitly accepts; do not advertise stock as his own photography.
Verify dearJoe's EULA for the new domain, preview environments and traffic tier
before launch. Existing Google font requests should be replaced with authorised
local copies where practical. Contact mailbox readiness is a separate launch gate.

Official sources checked 2026-10-09:
[Cloudflare Tunnel setup](https://developers.cloudflare.com/tunnel/get-started/),
[hostname routing](https://developers.cloudflare.com/tunnel/concepts/routing/),
[application service terms](https://www.cloudflare.com/service-specific-terms-application-services/).
Recheck applicability during M0; this project does not establish legal clearance.

## Content Desk and scheduled workflow

Build a small Aster-styled internal editor, not a general file manager or new
CMS ecosystem unless M0 identifies a clear benefit. Its embedded gallery
preview remains TCF-styled. The minimal path supports:

1. Select an allowlisted image; show filename/thumbnail, source checksum,
   orientation and collection. Stable IDs, not model-generated paths.
2. Write/import a Markdown story. Preserve Jason's original and revision history.
3. Request optional local AI suggestions for tone, brevity, spelling, titles or
   alt text. Show a diff; no automatic overwrite. AI never invents documentary
   facts, consent or personal information.
4. Preview the real gallery layout and full-image/story viewer on mobile/desktop.
5. Approve a frozen image/story/metadata version and set a publication date.
6. A dedicated timer promotes only approved due content. Show result, current
   release and one-step rollback. Manual publication uses the same safe path.

Each content record contains ID, allowed relative asset path, image hash,
orientation, focal point/crop choice, collection, title, alt text, story,
story mode (fictional/factual), provenance/rights and consent status, version,
approval identity/time/hash, publish_at timezone, expiry/withdrawal state.
Unknown rights or incomplete alt text blocks approval; model output cannot
set approvals or consent. No face identities inferred from images.

Any change to image, text, alt text, crop or public metadata invalidates prior
approval. Publisher validates a content hash against the approved snapshot.
No filesystem wildcard import automatically makes an image public.
Markdown is escaped/sanitized; reject traversal, external file references,
symlinks escaping the allowlist, unsafe SVG/script and embedded private metadata.
Treat stories/filenames as untrusted data, never execution instructions.

Proposed schedule for M0: one hourly timer checks due approved items, in
`America/Vancouver`, with an optional weekly editorial cadence Jason chooses.
The hour is a polling cadence, not a requirement to change content hourly.
If nothing is due/changed, no build and no notification. Store UTC instants
plus the chosen timezone, test DST and missed runs; after downtime, produce one
coherent current release rather than replaying every missed job. Do not create
a Codex heartbeat as the production scheduler: scheduling belongs to the service.

Use a lock, bounded retries/timeouts, durable versioned job state and atomic
release promotion. Build in staging, validate all pages/assets, then switch the
accepted release. Interrupted or failed runs leave the last release intact.
Retain rollback versions with a quota; never delete the last known good release.
Serve responsive WebP/AVIF/JPEG as supported, no upscaling, preserve colour
appearance, strip EXIF/GPS and retain rights privately. Never edit originals.
Full-size download sales are out of scope.

### M0 decisions accepted to date

- Immich on the main Synology is the eventual source catalogue. A deliberately
  separated professional-photography collection will be exposed read-only to
  the workflow; no such content exists yet.
- The separate future competition-analysis assistant is outside A1–A6. The
  publishing path begins with Jason's GUI approval, may later add monitored AI
  operation, and may move toward autonomy only through a future accepted gate.
- Stories are canonical UTF-8 Markdown files on a scoped Synology repository,
  edited elsewhere and imported by paste, drag/drop or allowlisted network
  selection. The Content Desk preserves originals and approved snapshots.
- The accepted gallery samples contain 36–68 words per story. Gallery text
  targets 40–70 words, warns above 80 and has a hard 100-word limit. An optional
  full-viewer story may contain up to 160 words. All variants require desktop,
  portrait and 390 px mobile preview; no automatic truncation or rewrite.
- Current photographs/stories are conspicuously labelled sample content and
  are not publication-approved. Real launch content is a later launch gate.
- Jason alone controls approval initially. The policy may become configurable
  through a later explicit design decision; AI cannot approve in this scope.
- Editorial cadence begins fortnightly. A quiet due-item check may run more
  often, but it publishes only immutable approved versions and emits no routine
  no-change notification.
- Synology is the private content authority, not the public web server. The
  isolated Proxmox origin receives only complete static release copies and has
  no NAS, Immich, AI or private-editor access.
- Backup scope covers configuration, reconstruction inputs/current story files,
  approval state and the current accepted site plus bounded operational
  rollback. Immich/media has its own backup process; this project does not add
  historical media or release-archive protection.
- Cloudflare currently holds the parked Contrasting Frame domain, and Jason
  owns `theclosetfatman.com`; live provider state for the second domain remains
  an A5 verification gate. Public delivery is free-tier only; each apex is
  canonical with its own `www` redirect. No editor, API, originals,
  administration, downloads or sales are public.
- Apple-hosted custom-domain mail is intended for
  `hello@thecontrastingframe.com`; working mail or an accepted interim address
  remains a launch gate.
- Jason reports the dearJoe webfont licence permits one domain and 10,000
  monthly views. It is restricted to The Contrasting Frame and must never be
  emitted in a Closet release. The Closet Fatman will use a different font.
  Monitor usage and extend the licence before exceeding it; EULA verification
  remains an A5 gate.
- The private Content Desk follows the Aster internal UI and app-icon guides;
  each embedded public preview follows its selected brand guide. Its accepted
  private hostname is `tcf.elliottrook.com`.
- The Closet Fatman uses identical content places/space and the same backend,
  with the approved maroon, deep navy, burgundy and silver logo collection.
  Its forthcoming website/template and non-dearJoe typography remain an
  explicit acceptance gate before public preview or launch.

### M0 dual-site revision

- The public display name will be finalized as either “The Closet Fatman” or
  “The Closet Fatman Photography” with the forthcoming website; the backend
  uses the stable `closet` key and short `Closet` pill either way.
- The two sites are intended to carry different media. Jason or the AI may
  deliberately select the same photograph/story for both at different times;
  this requires two site-bound records, independent review and independent
  approval. Approval or scheduling never transfers automatically.
- The authoritative Closet asset source is
  `/Users/jasonelliott/Documents/The Closet Fatman`: 290 files including 46
  core masters, four website-use copies, favicons/icons, manifest and geometry/
  export QA. Do not copy its full production pack into public Git.
- The Closet website is still to be developed and shared. Until then the desk
  may identify the Closet channel and its accepted palette/logo source, but it
  must not invent the public layout treatment or final font.
- Unless changed, each site has an independent fortnightly queue and launch
  gate, and the Closet contact follows the same Apple custom-domain-mail plan
  at `hello@theclosetfatman.com`. Provider/DNS state is verified live.

## Privacy security and risk assessment

| Risk | Control and residual decision |
|---|---|
| Original/client/private story exposure, high impact | Curated allowlist, read-only masters, independent public host, approved content hashes, EXIF stripping and external denied-path tests; Jason accepts public selected copies in M0 |
| Public service compromise, high impact | Static-only guest, no private mounts, default-deny lateral movement, separate connector/account, patch ownership; home origin still depends on household power/ISP |
| Wrong or unreviewed AI words, medium/high | Draft-only AI, visible diffs, explicit version approval, fiction/fact flag; author review is still required |
| DNS/mail disruption, high | Read all current records, preserve zone/DNSSEC/mail, bounded cutover and rollback; human registrar actions may be needed |
| Font/image rights and edge cost, medium/high | EULA/rights checks, attribution, consent, CDN terms and spending decision before launch |
| Lost data or bad scheduled deployment, high | Additive imports, checksum versions, atomic release, independent backups and isolated restore |
| Contention with Aster/media/backup jobs, medium | Bounded jobs/concurrency, resource measurements, existing inference service only, timer window agreed in M0 |
| Credential leak or excessive privileges, high | OpenBao/broker custody, non-root identities, strict deploy capability; no configuration/token dumps |
| Local clone diverges from Forgejo, medium | Patch-only transfer onto current authoritative checkout, focused commits; never push unrelated local history |

No production interruption is required during preparation. DNS cutover introduces
a bounded cache/propagation window; the old preview stays available. M0 must
record recovery checkpoints, public hostnames, exact firewall rules, affected
accounts, accepted provider cost/privacy, and abort conditions. Stop for new
exposure, unverified backups, source ambiguity, unavailable rights, failed
isolation or scope change. Stream A never waives platform approvals or the
repository's per-push remote-write rule.

## Milestones

### M0 Design workshop and approval Stream M

- [ ] New agent reads AGENTS, current Forgejo standards, this project, style guide
  and latest accepted website; reconciles local/remote state without pushing.
- [ ] Discuss one real photograph/story example and the private Content Desk
  mockup with Jason. Ask about normal writing/upload habits, folders, fiction
  versus factual notes, review expectations, scheduling and launch content.
- [ ] Confirm canonical photo source, storage/backup scope, domain/DNS/mail
  ownership, font licence, edge provider/terms/budget and desired public privacy.
- [ ] Verify NetBox allocations, host memory, model/broker availability and
  existing proxy/tunnel consumers; propose exact guest IDs/IPs and narrow ports.
- [ ] Record the concrete architecture, risks, exclusions, recovery plan and
  approvals. Obtain Jason's explicit M0 design/risk acceptance and transition
  the project to Stream A for the agreed A1–A6 scope.

Gate: Jason has discussed and accepted the design, not merely seen a plan.
No dataset creation, deployment, timer, credential provisioning, DNS/public
route or firewall mutation before this gate. Local prototypes and read-only
discovery may proceed. Remote Git writes still need immediate permission.

### A1 Preserve source and prepare content model

- [x] Verify baseline source/asset checksums and protect a restorable export.
- [x] Prepare private source repository/mirror policy, content schema and tests.
- [x] Separate demonstration content from launch-approved content; preserve all
  user originals and author-written story versions.
- [x] Validate orientation layouts and brand guide on synthetic/approved samples.

Gate: source reconstructs the accepted site; no proprietary/private data leaks.

### A2 Provision internal hosting and storage

- [x] Create only approved guests, datasets, accounts/ACLs and narrow rules.
- [x] Deploy private editor/preview and static origin; deny lateral/public admin.
- [x] Add host/guest backups, Beszel/Doctor and NetBox records; verify restore.
- [x] Validate reboot, mount loss and editor/inference outage with origin intact.

Gate: accepted gallery operates privately and isolation/recovery tests pass.

### A3 Deliver the AI assisted editorial workflow

- [ ] Implement `Contrast` / `Closet` site selector, story editing, optional
  draft-only local AI, diffs,
  rights/alt-text checks, live preview, approval and version invalidation.
- [ ] Prove site-key isolation: reject cross-brand asset, approval, schedule,
  font and mixed-site release reuse.
- [ ] Add dedicated service identities/broker mappings with denied-action tests.
- [ ] Jason completes a real photograph/story review and approval walkthrough.
- [ ] Preserve original words; verify path/metadata/prompt-injection safeguards.

Gate: Jason can operate the complete private authoring flow without the agent.

### A4 Scheduled publication and rollback

- [ ] Implement agreed timer, due-content manifest, locking and durable status.
- [ ] Stage, validate and atomically deploy exact approved content versions.
- [ ] Test changed-after-approval, concurrent jobs, missing/corrupt images,
  inference failure, timer outage, DST, crash before switch and rollback.
- [ ] Two independent scheduled production-shaped passes plus a no-change run.

Gate: approved due content publishes; unapproved content never does.

### A5 Public domain launch

- [ ] Reconfirm M0 exposure/provider decision and each site's content, style,
  font, DNS and mail gates; either site may remain private while the other launches.
- [ ] Capture DNS/proxy/certificate/firewall recovery checkpoints.
- [ ] Configure only approved domain/edge routes; preserve existing services/mail.
- [ ] Test real external unauthenticated gallery access and LAN/Tailscale access;
  verify HTTPS/redirects, responsive assets, cache invalidation and renewal.
- [ ] Externally test blocked editor, dotfiles, source maps, private manifests,
  originals, backup files and forbidden methods; verify origin lateral denies.
- [ ] Record rollback and any unavoidable outage/provider limitations.

Gate: the domain reaches only the accepted public gallery; no admin/data exposure.

### A6 Operational review and graduation

- [ ] Measure image weight, load experience, CPU/RAM/disk, AI latency, timer
  overlap and retention against M0 budgets; correct avoidable friction.
- [ ] Complete an isolated restore and rollback from protected recovery copies.
- [ ] Reconcile Doctor, Beszel, NetBox, wiki/mirror, runbooks, diagrams,
  Homepage, authentication, certificates, firewall and backup records.
- [ ] Deliver and validate the operator manual: add photo, write/review story,
  approve, schedule, check failure, withdraw content and restore last release.
- [ ] Jason accepts the handover; update evidence, graduation and close-out.
  Synchronize focused commits to Forgejo with permission and verify its mirror.

Gate: recoverable, efficient and supportable without Codex or live AI.

## Observability maintenance and integration impacts

Assess each standard checklist item; evidence remains pending until implemented.

| Integration | Required outcome |
|---|---|
| Doctor | HTTP/accepted-release checksum, timer last successful check rather than unchanged-file mtime, backup age, certificate and quota; no private stories in alerts |
| Beszel / existing monitoring | Both new guests registered and reporting; exact exclusions/alternate coverage documented; no duplicate noisy alerts |
| Backup / recovery | Scoped assets, content, workflow DB, sources, guest config and secret recovery; independent checksum-tested restore |
| NetBox | Guest/interface/MAC/VLAN/IP/status and services, uniqueness and API readback; approved allocations only |
| Human wiki | Author workflow, URLs/access and recovery manual |
| Aster derived mirror | Sanitized service/workflow facts with provenance; no private photographs, draft stories or credentials |
| Operational reference | Current deployment, ports, schedules, custody identifiers and break-glass |
| Repository / diagrams | Source path, trust flow, addressing and final design; no imaginary deployed facts |
| Homepage | Private Content Desk link and public gallery link, no secrets in config |
| Authentication | Owner-only editor, least-privilege importer/AI/deployer, recoverable owner access |
| DNS / TLS / firewall | Exact domain rules, renewal and external/private denied-action tests |
| Automation | Host-owned timer, DST/missed-run/lock tests, quiet no-op and actionable failure status |
| Security inventory | Updates, root-only machine secrets, broker risk class, revocation/rotation procedure |
| AI administration | Dedicated identities/capabilities; explicit unsupported status where no safe API exists |

Proposed backup: daily configuration/content/state and selected asset snapshots,
an independent Recovery copy, and an explicitly approved encrypted off-site
subset within current capacity. Do not silently include all photography or
reuse `Recovery/photos` as proof of existing protection. Jason must decide
original-photo backup coverage. Set retention/quota in M0; test restore into an
isolated target, including authorship/approval records, before graduation.

Rollback: select the previous immutable release; disable only the new timer if
it misbehaves; restore only TCF configuration; revert the exact domain/route
changes using the checkpoint. Never stop the existing shared tunnel or undo
unrelated proxy/firewall rules. Withdrawal of a photograph includes CDN cache
purge when supported and verification; explain that third-party copies of
previously public material cannot be guaranteed erased.

## Persistence and exact next action

Current milestone: A3. M0 design/risk acceptance was given by Jason on
2026-10-09 after review of the corrected Aster-styled Content Desk concept,
Synology/Immich source boundaries, isolated public origin, story limits,
approval/cadence, backup scope, domain/mail/font constraints and free-tier
public exposure. No public-domain route exists. The private Content Desk is now
available through owner-only Authentik at `tcf.elliottrook.com`; direct backend
access remains denied. Bounded Markdown/image drag-and-drop import and visible
approval controls and a site-scoped placeholder library are deployed. Until real
content exists, both sites use only conspicuously blocked records based on the
accepted old sample. The two completed website baselines and their distinct
annotation treatments are now registered and privately staged. Passkey access and
the explicit placeholder-to-real promotion gate are proven. Next safe action:
Jason checks the live dual-brand preview, then the first real photograph/story
save, promotion and approval walkthrough can begin when content is available.
Store design decisions, last validated gate, candidate/accepted release ID,
rollback checkpoint, exact blocker and next safe action at each milestone.
Use a versioned durable job-state DB with atomic transitions, not process absence.

Resume by reading AGENTS, this project and current repository/Forgejo status;
verify completed evidence before rerunning anything. Do not create recurring Codex automation
unless Jason separately asks; the new implementation conversation owns execution.

## Evidence log

| Date | Evidence | Result |
|---|---|---|
| 2026-10-09 | Accepted website source `5b23ccb9`; source size about 12 MB | Preserved outside homelab; migration pending |
| 2026-10-09 | Live Forgejo main `2f929145`; standard/style blob IDs match checkout | Standards verified; other branch history differs |
| 2026-10-09 | Read-only Proxmox version/guest/storage and TrueNAS dataset/capacity queries | Hosting/storage proposals grounded in current resources; no allocation made |
| 2026-10-09 | Style routing, TCF guide and project/handoff prepared locally | Remote synchronization requires per-push approval and clean reconciliation |
| 2026-10-09 | Jason accepted the Synology/isolated-origin design, story limits, initial approval/cadence, backup scope and simple free-tier public surface; corrected Content Desk visual routing | M0 decisions recorded; live allocation/provider facts remain implementation-time verification gates |
| 2026-10-09 | Jason reviewed the corrected Aster-styled Content Desk concept and explicitly directed “please begin, stream A” | M0 accepted; project transitioned to Stream A for A1–A6 within the recorded scope |
| 2026-10-09 | Read-only live reconciliation: Forgejo main `2f92914`; Proxmox 9.2.20 with about 49 GB available RAM and VMIDs 124–125 free; NetBox 4.6.9 has no TCF records and `.35`/`.36` are unassigned; TrueNAS 25.10.5 Media pool has about 18.1 TB free and no TCF dataset; DSM 7.4.1 has about 10.0 TB available | Proposed allocations grounded in current state; no infrastructure changed during discovery |
| 2026-10-09 | Authoritative Forgejo main was streamed read-only as a complete Git bundle; only preparation commit `b5c81a4` was replayed as `0062f18`, then accepted M0 decisions committed locally as `5a8802d` | Divergent local history was not transferred; no remote write occurred |
| 2026-10-09 | A1 baseline manifest covers every accepted `dist/` file; private archive `accepted-dist-5b23ccb9.tar.gz` SHA-256 `2333421596d0bdf3579f48fc9300531e4e6b8b3a4f3bb950268960a7783413dc` restored in isolation and matched the manifest | Accepted site is reconstructable; archive remains private and must gain independent A2 backup coverage |
| 2026-10-09 | A2 provisioned unprivileged LXC 124 `tcf-publisher` at `192.168.20.35` and LXC 125 `tcf-origin` at `192.168.20.36`, plus quota-bounded `Media/TheContrastingFrame/{brand,workflow,releases}` and `Recovery/contrasting-frame` datasets; NetBox API readback matched VM, IP, MAC, VLAN and interface state | The private Aster-styled Content Desk and isolated TCF-styled static sample origin are deployed; no public route exists |
| 2026-10-09 | Both guests loaded default-deny nftables policy. Denied tests passed from origin to Synology admin, Content Desk and Proxmox, and from publisher to Synology admin; exact publisher-to-origin SSH, publisher-to-Synology HTTPS and both agent-to-Beszel paths passed | Public origin has no NAS/editor/AI path; the publisher has only declared dependencies and ordinary package egress |
| 2026-10-09 | Initial non-pruning guest backups and their TrueNAS mirror copies matched SHA-256 (`124` `02c200119dbe3c34eca1977f0f6d13da7966b3d9f38d6f1219fa4c184803f948`; `125` `933b77f23a10e85d145eeac8d4bd69ec6d37a7aabb117cc9670368ecbb2f5ac5`) and passed archive integrity; the TrueNAS copy of LXC 125 restored as networkless temporary LXC 126, served its local health endpoint and retained all five sample banners, then the test guest/staging files were removed | Independent guest recovery is proven without attaching the restored origin to any network |
| 2026-10-09 | Beszel 0.18.7 reports both guests `up`; HomeLab Doctor verifies private desk/origin services, the current release manifest and both primary/mirror backup ages. Full Doctor: 81 pass, 13 pre-existing warnings, 0 fail | Monitoring and failure-only checks cover the new runtime without adding a parallel stack |
| 2026-10-09 | Stopping the Content Desk left origin health intact; both guests then rebooted and recovered their service/firewall/agent units automatically. Neither runtime has a NAS mount, and the origin checksum remained valid | Editor, future inference and NAS availability are not origin runtime dependencies; A2 gate passed |
| 2026-10-09 | Versioned content schema, immutable public hash, sample hard-block, traversal/rights/consent/story-limit tests and conspicuous five-page sample build completed; 10 tests passed | A1 gate passed; commercial font and all media remain outside the public-mirrored repository |
| 2026-10-09 | Jason expanded the design to The Contrasting Frame plus the more whimsical The Closet Fatman, sharing identical page/content capacity and one backend; approved `tcf.elliottrook.com` for the private desk | A3 adds a site pill and hard site-key isolation. Closet logo/style/font and second-domain provider/mail facts remain design/A5 gates; no public route changed |
| 2026-10-09 | Read-only inspection found `/Users/jasonelliott/Documents/The Closet Fatman` with 290 assets, approved palette notes, manifest, geometry/export QA and four website SVGs; Jason confirmed the sites normally use different media but may deliberately reuse work | Closet logo assets are authoritative and remain outside Git/runtime for now; shared work requires separate site records and approval. Final public name suffix and forthcoming site treatment remain open |
| 2026-10-09 | Deployed the dual-site desk pill and durable SQLite version store in LXC 124. The sample seeded as `contrast` version 1; state directory is mode 0700, database 0600, and mutation endpoints require an explicit same-application intent header. Sixteen tests cover hash/site invalidation, mixed-site rejection, independent cross-publication and sample approval denial | A3 persistence foundation is live privately. Closet public rendering remains locked until its forthcoming site treatment is supplied |
| 2026-10-09 | Added checkpointed OPNsense rule `b60d512c-ae24-4acf-9322-317ecee35da1`, exact TCP `192.168.50.23` → `192.168.20.35:8080`. Initial sequence 3210 loaded after the private-network deny and matched zero packets; corrected to the working wiki-rule sequence class 2194, reloaded, and NPM LXC connection returned zero | Private proxy-to-desk network gate passed without broadening VLAN access; NPM, Authentik and split-DNS objects remain pending |
| 2026-10-09 | Forgejo `main` advanced through `ccdeb98`; both temporary API tokens used for the authenticated push were removed and the remote ref was verified at `ccdeb98a604f22077ad2c158f4446eb0e56e2f6e` | Accepted M0, dual-site A3 foundation and private-access provisioning are durably synchronized; unrelated local duplicate files remain untouched |
| 2026-10-09 | Created Authentik forward-auth application `photography-content-desk`, attached it to the embedded outpost and bound only Jason as owner. NPM host 36 routes `tcf.elliottrook.com` to `192.168.20.35:8080` using wildcard certificate 8; NPM's own renderer reported online and `nginx -t` passed | Private HTTPS access is protected by the existing identity boundary; unauthenticated client request returns the expected same-host Authentik 302 |
| 2026-10-09 | Added checkpointed split-DNS records to OPNsense Unbound and both Pi-hole v6 instances. All three resolvers independently return `192.168.50.23`; the Mac's normal resolver does too, while `1.1.1.1` returns no A record | `tcf.elliottrook.com` is internal only; no public DNS or tunnel route was created |
| 2026-10-09 | Full client-path test returned HTTPS 302 to `/outpost.goauthentik.io/start`; direct Mac access to `192.168.20.35:8080` timed out. Primary and secondary Pi-hole are healthy and NPM syntax remains valid | Private access path passes end to end, and the firewall still prevents bypassing NPM/Authentik |
| 2026-10-09 | Deployed site-scoped drag/drop import for UTF-8 Markdown up to 64 KiB and JPEG/PNG/WebP up to 20 MiB/60 MP. A synthetic live probe confirmed Markdown normalization, ImageMagick auto-orientation/metadata stripping, private mode 0600, content-addressed SHA-256 filenames and scoped JPEG preview; probe files were removed. NPM host 36 now permits the bounded encoded request at 29 MiB and still passes `nginx -t` | Imported bytes cannot overwrite an earlier version's image, never leave the private desk, and do not alter a content version until explicit draft save |
| 2026-10-09 | Added visible collection, story type, orientation, rights, consent, focal-point and credit controls. Unsaved edits keep approval disabled; server-side approval still revalidates the immutable latest version. Both site pills load independent sample records. Twenty-two unit tests and the embedded JavaScript syntax check passed; private HTTPS still returns the expected Authentik 302 | Human review fields and save-before-approval boundary are live; creation/selection of fresh non-sample records and Jason's real walkthrough remain A3 gates |
| 2026-10-09 | Added site-scoped latest-record lists and placeholder creation. Created one live `PLACEHOLDER — Untitled photograph` workspace for each site from the old accepted sample; both are `sample=true`, version 1, unapproved and independently keyed. Twenty-three tests and embedded JavaScript syntax passed; a direct approval attempt returned 409 with sample/rights/consent blockers and private HTTPS retained its Authentik 302 | The desk is usable before real content arrives without any placeholder being accidentally publishable; deliberate promotion and a real owner walkthrough remain |
| 2026-10-10 | Accepted current site sources `49f210c7` (Contrast) and `c77684d` (Closet) into separate private brand datasets; file counts and annotation-manifest SHA-256 values matched. Added shared bounded annotation text/X/Y fields to the immutable public payload and live desk. Contrast previews a formal title/gold underline; Closet previews a whimsical handwritten note/arrow. Both live sample records advanced independently to unapproved version 2, and 24 tests plus embedded JavaScript syntax passed | Both finished visual systems now use one site-scoped workflow without sharing brand assets, approvals or default media; annotations cannot change after approval without invalidating it |
| 2026-10-10 | Diagnosed the Authentik browser error as an empty proxy-provider redirect allowlist created through the ORM path. Provisioning now invokes Authentik's OAuth defaults and explicitly assigns `aster-companion-passwordless`; live readback shows the two expected `tcf.elliottrook.com` callback URLs, one owner binding and the embedded outpost attachment. Reloading the original browser URL reached “Sign in to Aster Companion” for Photography Content Desk instead of the redirect error | Private login is repaired and follows the current passkey-only flow; Jason's human passkey ceremony is the remaining browser handoff |
| 2026-10-10 | Jason proved a clean external-browser sign-in with the passkey flow; an existing browser session correctly reused Authentik SSO. Added a typed-confirmation placeholder promotion gate. Ordinary draft saves cannot clear `sample=true`; promotion requires an imported image, replaced placeholder title/story and complete approval metadata, and always creates an unapproved version. Twenty-six tests passed; live rejection probes returned 422 for direct sample-flag removal and 409 for promoting the retained sample image | Authentication is proven end to end and placeholder material cannot silently become production content; first real-content walkthrough remains intentionally deferred until media exists |
| 2026-10-10 | Added site-scoped fortnightly editions that snapshot all current website slots. Edition readiness requires every slot to have a changed, non-sample, currently approved candidate, or a deliberate typed-confirmation removal. Removal is reversible during drafting and preserves the slot record/history; adding a slot is separately labelled as a structural change. Twenty-nine tests and embedded JavaScript syntax passed; live readback shows inactive independent edition workspaces for both sites and healthy service | Routine updates now replace the complete site atomically rather than accumulating entries; no edition was started while only placeholder content exists |

## Close out

Not graduated. M0 discussion, accepted risks, implementation, public launch,
scheduled publishing, recovery proof and user handover remain outstanding.
Record final architecture, ownership, recurring costs, limitations and deferred
storefront work here only when the graduation gates are actually met.
