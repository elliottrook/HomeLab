# Aster Offline Knowledge Wiki and Mirror

> Status: Active — Milestone 2 in progress
>
> Project owner: Jason
>
> Proposed: 2026-09-10
>
> Started: 2026-09-10
>
> Authorization: Stream A — Autonomous

## Pre-start risk assessment and authorization envelope

Jason's 2026-09-10 instruction to start the project and work autonomously is
the Stream A approval for the scope and change classes below. It does not waive
repository or platform approval for remote Git writes, public exposure,
credential changes, destructive retention decisions or another non-waivable
stop condition in the project creation standard.

- **Objective and scope:** create the two private repositories, human wiki,
  bounded intake/collector workflow, generated mirror, Aster integration,
  evaluation, observability and recovery described in this document. Allowed
  changes are new application code/configuration, private service deployment,
  source-local scheduled jobs, narrow internal service registration, synthetic
  tests, protected backups and reversible Aster snapshot-manifest changes.
- **Affected systems and users:** Jason is the initial and only interactive
  user. The intended deployment touches Forgejo LXC 108, a dedicated collector
  target selected during Milestone 2, the private wiki presentation path,
  Aster LXC 104 and its existing snapshot builder, plus Doctor, backup and
  monitoring integrations. Inference remains on LXC 110; NetBox LXC 111 is a
  read-only identity source, not a deployment target.
- **Current state and dependencies:** read-only discovery on 2026-09-10 found
  LXCs 104, 108, 110 and 111 running. Aster is an unprivileged 4 GiB guest on
  VLAN 70; Forgejo is an unprivileged 2 GiB guest on VLAN 20. The existing
  27-source Aster manifest, deterministic snapshot builder, authority-aware
  retrieval, private Forgejo, Authentik onboarding pattern, HomeLab Doctor and
  protected Proxmox backup path are the dependencies to preserve.
- **Authority and data:** live reports and adopted systems of record remain
  authoritative for transient and structured facts; `homelab-reference`
  remains authoritative for reviewed current operations; imported upstream
  content is versioned reference material; generated mirror output is always
  non-authoritative. Conflicts are reported, never silently resolved.
- **Confidentiality and privacy:** the corpus may contain private topology and
  operating guidance, so both repositories and the service remain private.
  Credentials stay source-local and outside Git. Fetch/extraction rejects
  secret patterns and records only a non-sensitive failure reason. Aster gains
  neither Internet access nor collector credentials.
- **Availability and integrity:** bad upstream data, partial runs and incorrect
  summaries could poison retrieval. Run-specific staging, immutable input
  hashes, quarantine, verification, deterministic packaging, atomic activation
  and retained last-good commits/snapshots prevent partial publication and
  provide rollback. Core HomeLab operation does not depend on this service.
- **Outbound/network changes:** the collector alone receives bounded outbound
  HTTPS for accepted hostnames. No inbound Internet path or broader trust rule
  is authorized. Any internal DNS, proxy or firewall change must be the narrow
  private path documented here and retain an administrative recovery path.
- **Licensing:** originals enter Git only when redistribution/storage terms
  permit it. Otherwise metadata enters Git and the local-use original remains
  in protected storage. Ambiguous licenses quarantine rather than publish.
- **Destructive/irreversible work:** none is required. Retirement is two-stage;
  source history and protected originals are retained. Repository deletion,
  history rewrite, last-copy removal and irreversible corpus cleanup are
  excluded.
- **Recovery checkpoint and rollback:** before deployment, retain verified
  current archives of every affected guest and the accepted Aster snapshot.
  Disable the timer/service, reactivate the prior static build and snapshot,
  and retain staging for diagnosis. Abort on an unverified prerequisite
  backup, unexplained authority conflict, secret exposure, scope expansion,
  public ingress, or failure to reproduce the accepted package.
- **Testing and interruption:** synthetic fixtures cover each source type,
  malformed/adversarial content, redirects, size/type limits, secrets,
  conflicts and interrupted stages without touching production data. Two
  independent production-path passes and an isolated restore are required.
  Expected interruption is limited to bounded service activation/restart and
  will be detected through direct health checks plus Doctor/monitoring.
- **Residual risk:** upstream formats and licenses can change; model summaries
  can omit nuance; private operational text remains sensitive even without
  credentials. Quarantine, exact provenance, human-source fallback and monthly
  corpus review reduce but do not eliminate these risks. Jason accepts these
  residual risks within the stated Stream A scope.

## Scope and exclusions

The scope is limited to the architecture, interfaces, repositories, source
classes, deployment and graduation gates in this document. Explicit non-goals
are public publishing, general web browsing, arbitrary repository access,
credential ingestion, Aster infrastructure mutation, replacing NetBox or
`homelab-reference`, automatically promoting generated text to authority, and
deleting historical source material.

## Persistence plan and current resume state

The project document is the durable orchestration record. Implementation uses
schema-versioned state, content-addressed work items, per-run staging, bounded
locks/retries and atomic candidate-to-accepted transitions. Each completed
milestone ends with tests, evidence and a focused local commit. Remote
synchronization is recorded as pending until separately authorized.

**Synchronization cadence:** intermediate implementation stages use local
checkpoint commits only. Do not request or perform a remote push for each
stage. At the completion gate of each milestone, present the milestone's
validated commit range and request the single repository-required confirmation
for that milestone synchronization. This cadence does not waive the governing
rule that confirmation must occur immediately before the actual push.

**Current milestone:** Milestone 2 — safe daily acquisition.

**Last verified state:** private Forgejo repositories `jason/homelab-wiki` and
`jason/aster-knowledge-mirror` contain seed commits `678786c` and `260cdb0`;
both remain private. Dedicated unprivileged Debian 13 LXC 113 `aster-wiki` is
running at NetBox-selected `192.168.20.34`; its application archive is
installed and `aster-wiki-intake.service` is enabled. The Python 3.13 multipart
compatibility fix from local commit `fb1f160` is deployed: the service is active,
listens only on `127.0.0.1:8787`, and `/healthz` returns the expected JSON. The
collector timer remains explicitly disabled and inactive. The collector now
persists and sends HTTP validators, treats `304 Not Modified` as an explicit
unchanged result only when the prior accepted content still matches its locked
hash, and fails closed on missing or tampered prior content. The complete local
suite passes 26/26 tests. Its deployed manual synthetic pass accepted and
verified one source; a subsequent secret-pattern fixture quarantined exactly
one source without changing the accepted corpus or lock hashes.

**Next safe action:** continue authenticated queue promotion, HTTP rate limits
and Doctor integration locally. Reconcile the two intentionally retained
interrupted-run records from deployment debugging through an explicit operator
resume/closure workflow. Do not enable the collector timer before those gates
and two scheduled-cycle observations pass.

**Rollback location:** current `main` commit, deployed
`/opt/aster-wiki/aster_wiki/app.py.before-fb1f160`, and Aster's retained
accepted snapshot. LXC 113 is a new isolated target and its daily timer remains
disabled, so it has not changed Aster's accepted snapshot. Recovery checkpoint
`backups:backup/vzdump-lxc-113-2026_09_10-14_13_06.tar.zst` passed zstd
integrity verification and contains the deployed collector, unit and accepted
lock.

## Integration impact assessment

- [ ] **HomeLab Doctor:** add bounded service, pipeline age/result, quarantine
  count and accepted-snapshot checks with synthetic failure tests.
- [ ] **Monitoring/alerting:** add non-duplicative availability/run-age metrics
  and owner-visible alerts after the service target is selected.
- [ ] **Backup and recovery:** protect both Git repositories, collector state,
  permitted originals and deployed snapshot; prove isolated restore.
- [ ] **NetBox:** use existing asset/service IDs read-only where applicable; add
  a service record only if NetBox's adopted authority requires one.
- [ ] **Human wiki:** this project creates it; operator guidance and recovery
  links are graduation requirements.
- [ ] **Aster mirror/snapshot:** create the separately recoverable derived
  mirror and extend the validated manifest/retrieval path without changing its
  authority.
- [ ] **Operational reference/runbooks:** link or version-import selected
  material; current-state authority stays in `homelab-reference`.
- [ ] **Repository documentation:** update architecture, addressing,
  operations, backups, portfolio and changelog where deployment affects them.
- [x] **Diagrams/rack records:** not applicable at project start; no physical
  topology, rack, cable or power change is planned.
- [ ] **Homepage/service discovery:** add a private operator link with a useful
  health check and no embedded credentials after deployment.
- [x] **Authentication/authorization:** use the existing private onboarding
  pattern, owner/admin only, with a documented direct recovery path.
- [x] **DNS, certificates and firewall:** assess after target selection; only
  narrow split-DNS/internal proxy and collector egress changes are permitted.
- [ ] **Automation and schedules:** add observable daily and monthly jobs with
  locking, missed-run behavior and retained last-success state.
- [ ] **Security inventory:** document source-local secrets, restrictive modes,
  update ownership and removal of temporary access before graduation.

## Purpose

Create a private, offline-first HomeLab knowledge repository for people and a
separate Aster-optimized mirror derived from it. The human repository retains
complete manuals, upstream documentation, local notes and readable operating
guidance. Aster analyses accepted material into concise, source-linked
operational knowledge so it can retrieve the important constraints, symptoms,
dependencies and recovery steps quickly.

Provide a simple internal intake interface so adding equipment or software does
not require editing Git or YAML. An operator can paste a documentation/wiki URL,
enter a Git repository, or upload a manual; the interface discovers candidate
metadata and scope, previews what will be collected, and enrolls the accepted
source into the same resumable daily workflow.

The mirror is a cache and analysis product, never a source of truth. Aster must
be able to trace every derived claim to the human repository and, through it,
to the original document version. Failure or corruption of the mirror must not
damage the human corpus or prevent operators from reading it.

## Decision

Use two Git repositories with a one-way generation boundary:

```text
allowlisted upstream sources          operator-authored pages
             |                                  |
       intake portal                           wiki UI
             |                                  |
             +----> homelab-wiki <--------------+
                    human corpus
                         |
               read-only analysis job
                         |
                         v
              aster-knowledge-mirror
            concise derived operational memory
                         |
               validated Aster snapshot
                         |
                         v
                       Aster
```

- **`homelab-wiki`** is the human-focused repository. It holds complete,
  readable material and provenance. Reviewed local pages may be authoritative
  within the existing authority contract; imported documents are reference
  material only.
- **`aster-knowledge-mirror`** contains generated summaries, facts, retrieval
  hints and cross-links. Every file is reproducible and explicitly
  non-authoritative. Humans may review it, but must correct the source rather
  than hand-edit generated output.
- **`homelab-reference`** continues to own reviewed current operational state
  and runbooks. The new wiki links to or imports a versioned copy of selected
  material; it does not silently replace that repository.
- **`homelab`** continues to own project decisions, implementation evidence and
  change history.

This extends the graduated second-brain architecture; it does not widen
Aster's infrastructure or Internet authority.

## Human interface and source onboarding

Host a small private intake application alongside the static wiki. It is an
operator interface to the source manifest and staging workflow, not a general
browser and not a direct editor of the accepted corpus.

The **Add source** flow supports:

1. **Web documentation/wiki** — paste one starting URL; select a discovered
   sitemap, named wiki pages or a bounded path prefix.
2. **Git repository** — paste an HTTPS repository URL; select a branch, tag or
   release policy and choose proposed documentation paths from a repository
   tree preview.
3. **Manual upload** — upload PDF, HTML, Markdown or plain text; associate it
   with an existing NetBox asset or enter manufacturer, model and version.
4. **Equipment or application** — choose an existing asset/service or create a
   pending wiki identity, then attach one or more of the source types above.

The system performs read-only discovery and presents a single review screen
showing:

- resolved publisher, hostname, repository owner and final URL;
- proposed title, source ID, equipment/service association and taxonomy;
- collection boundary: exact files, path prefix, sitemap or named pages;
- version/update policy, expected download size and daily schedule;
- detected license/redistribution information and credential requirement;
- sample extracted text and the mirror entry types Aster would generate; and
- validation warnings, redirects or conflicts with existing sources.

Selecting **Accept source** creates a narrowly scoped manifest change and queues
the initial collection. That is the one deliberate enrollment action; known
source updates thereafter run unattended. A rejection or abandoned preview
does not alter Git, the accepted lock or Aster's snapshot.

The interface also provides:

- source status, last successful update, current upstream version and next run;
- pause, resume, retry and remove-from-future-updates controls;
- quarantine review with a readable reason and safe extracted preview;
- history and diff views for accepted source and mirror changes;
- links from every source to its human wiki pages and Aster mirror entries; and
- a visible distinction between `pending`, `accepted`, `stale`, `quarantined`,
  `paused` and `retired` states.

Removing a source is two-stage and recoverable: first retire it from future
updates and Aster's next mirror, then retain its Git history and protected
original until the normal retention decision. The portal cannot delete Git
history, bypass validation, publish the wiki externally, expose secrets or
grant Aster new capabilities.

Authentication uses the existing private service-onboarding pattern. Start
with the owner/admin identity only; any later editor role is separately scoped.
The UI submits structured jobs to an unprivileged queue. The collector alone
performs outbound fetches, and it accepts only validated jobs rendered into the
source-manifest schema.

## Authority and conflict model

For current facts, retrieval must prefer sources in this order:

1. validated live reports for transient state;
2. adopted domain systems of record, including NetBox where applicable;
3. reviewed `homelab-reference` current-state pages and runbooks;
4. reviewed operator-authored `homelab-wiki` pages;
5. version-matched vendor or upstream documentation in `homelab-wiki`;
6. community material, issue discussions and generated mirror entries.

The mirror may compress or connect these layers but may not promote a lower
layer, resolve a conflict silently, or invent a missing fact. A conflict entry
must name both sources, their authority and review dates, and tell Aster to
report the discrepancy.

## Repository design

### Human repository: `homelab-wiki`

```text
README.md
WIKI-CONTRACT.md
mkdocs.yml
docs/
  architecture/
  equipment/<asset-id>/
  services/{aster,arr,home-assistant}/
  runbooks/
  concepts/
  incidents/
  projects/
  upstream/
  manuals/<vendor>/<model>/
sources/
  sources.yaml
  licenses.yaml
  accepted-lock.json
tools/
tests/
```

Each source record must declare a stable source ID, owner/vendor, canonical
URL or repository, allowed path or document, source class, expected media type,
version policy, refresh interval, size limit, redistribution/licensing status
and enabled state. Equipment pages use the existing NetBox asset identity where
one exists, so adding a device means adding one page and its source records
rather than creating another inventory namespace.

Imported material is stored separately from authored pages and records:

- canonical URL and final URL;
- retrieval time and fetch result;
- upstream version, release, commit, ETag or Last-Modified value;
- original-file and normalized-text SHA-256;
- media type, extraction method and page/section map;
- license/redistribution decision;
- review state and superseded source version.

Original manuals are retained when licensing permits. Otherwise the repository
stores metadata, a local-use extracted copy outside Git if required, and a
stable reference to the protected document store.

### Aster mirror: `aster-knowledge-mirror`

```text
README.md
MIRROR-CONTRACT.md
entries/<source-id>/<content-id>.md
indexes/
  assets.json
  services.json
  symptoms.json
  dependencies.json
  provenance.json
state/
  accepted-input.json
  generation.json
evals/
```

Each derived entry must be small enough for focused retrieval and contain:

```yaml
schema_version: 1
entry_id: vendor-model-topic
source_id: vendor-model-manual
source_path: docs/manuals/vendor/model/manual.md
source_sha256: "..."
source_version: "..."
source_locator: "page 42 / section 7.3"
generated_at: "..."
generator_model: "..."
generator_prompt_version: "..."
authority: derived-memory
review_state: generated
confidence: high
supersedes: null
```

The body uses a fixed operational form where relevant:

- what the component is and its HomeLab role;
- model/version applicability;
- critical limits and prerequisites;
- dependencies and failure blast radius;
- important symptoms and likely causes;
- safe observations and diagnostic order;
- recovery or rollback outline;
- warnings, destructive steps and approval boundaries;
- unresolved contradictions or missing local facts;
- exact source locators.

The analysis job may also create topic and asset cross-links. It must not copy
credentials, manufacture commands absent from the source, or convert a vendor
example into a statement about the live HomeLab.

## Daily autonomous pipeline

Run the pipeline on a dedicated collector with outbound access. Neither Aster
nor the wiki presentation service needs general Internet access.

1. Load the committed allowlist and the previous accepted lock file.
2. Fetch only due sources, using conditional requests and repository commit or
   release checks where possible.
3. Enforce TLS, redirect, hostname, content-type, byte, page, archive and time
   limits before accepting content.
4. Reject executables, active content, encrypted documents, nested archives,
   secret patterns and sources outside the declared boundary.
5. Normalize text deterministically while retaining page and section locators.
6. Stage changed human-corpus content on a generated candidate branch or
   worktree; never overwrite operator-authored pages.
7. Run structure, provenance, license, link, duplication and secret linting.
8. Analyse only changed accepted inputs into mirror candidates. Unchanged input
   hashes must reuse the existing derived entries.
9. Validate schema, citations, source entailment, coverage, contradiction and
   prompt-injection resistance. A second verification pass must reject claims
   that cannot be located in the cited source.
10. Build the mirror and Aster snapshot twice and require identical hashes for
    deterministic packaging.
11. Publish atomically only when every blocking gate passes; retain the prior
    human lock, mirror commit and deployed snapshot for rollback.
12. Write a concise daily report containing changed, accepted, quarantined,
    failed and unchanged source counts. Failure must leave the last accepted
    repositories and snapshot active.

The scheduler owns no infrastructure mutation capability. Automatic commits
may be made to dedicated generated branches after the test suite passes.
Promotion to an authoritative human page remains a reviewed change. Remote
push policy follows repository authorization and is not granted by this
project document alone.

New sources accepted through the portal enter this pipeline immediately for
their initial run, then follow their declared daily or slower schedule. A
failed initial import stays `pending` or `quarantined`; it never becomes visible
to Aster merely because the operator submitted it.

## Resumption and usage-limit handling

The pipeline must be safe to stop after any item and resume without repeating
successful analysis unnecessarily:

- use a run ID and durable state database or append-only journal;
- checkpoint after fetch, extraction, analysis, verification and packaging;
- key every work item by source ID, input hash and pipeline version;
- write candidates to a run-specific staging directory and rename atomically;
- treat model timeout, quota exhaustion and process interruption as retryable;
- apply bounded retries with backoff, then continue other independent items;
- never mark a run accepted while any required item is incomplete;
- discard or quarantine partial output rather than exposing it to Aster; and
- provide `status`, `resume`, `verify`, `accept` and `rollback` operator modes.

Synthetic fixtures may be created for tests, including malicious pages,
contradictory manuals, scanned PDFs, malformed metadata and interrupted model
responses. They must be unmistakably labelled synthetic and excluded from the
production corpus and search index.

## Security boundary

- Aster receives no web browser, arbitrary URL fetcher, Git credential or
  collector credential.
- GitHub private access, if later needed, belongs only to the collector and is
  limited to read-only contents on named repositories.
- Upstream content is untrusted data. Instructions inside it cannot modify the
  pipeline, call tools, retrieve secrets or alter authority rules.
- The wiki is private and internal. Publishing it through a public proxy is out
  of scope and requires a separate project.
- Rendering runs without executable plugins or unsafe Markdown extensions.
- The wiki and mirror contain no secrets. Secret-bearing source material is
  rejected and recorded only by source ID and failure reason.
- Analysis runs without infrastructure credentials or write tools. Generated
  commands are prohibited unless present in the source and retained as quoted,
  source-located reference material.
- Aster must label mirror-derived answers and provide a route to the complete
  human document.

## Milestone 1 — Contracts and corpus prototype

- [x] Create `homelab-wiki` and `aster-knowledge-mirror` as separate private
  Forgejo repositories with explicit contracts and ownership.
- [x] Adopt the taxonomy, metadata schema, source manifest and authority model.
- [x] Establish how `homelab-reference` pages are linked or version-imported
  without creating competing current-state authorities.
- [x] Add a small representative corpus: one equipment manual, one Home
  Assistant document, one ARR document, one runbook and one incident record.
- [x] Prototype the internal Add source form for URL, Git repository and manual
  upload, including dry-run discovery and an acceptance preview.
- [x] Render the human wiki locally and verify navigation, search, source links
  and readability from a normal Lab client.

Completion gate: a person can browse the representative corpus offline and add
each supported source type without editing repository files; every document has
provenance and authority boundaries are unambiguous.

## Milestone 2 — Safe daily acquisition

- [x] Build a manifest-driven collector for allowlisted HTTP documents, wiki
  pages and Git repositories.
- [x] Add conditional fetch, rate limiting, validation, normalization,
  quarantine and retained-original handling.
- [x] Ensure generated imports cannot overwrite authored content.
- [x] Add resumable state, atomic acceptance and last-good rollback.
- [x] Complete the authenticated intake portal, structured queue, source-state
  dashboard, history/diff view and recoverable retirement workflow.
- [x] Ensure discovery cannot broaden a submitted scope without displaying the
  expanded files/pages and requiring source acceptance.
- [ ] Schedule a daily no-change-safe run and publish a bounded health report
  for HomeLab Doctor and Aster's existing report mechanism.
- [x] Prove with synthetic fixtures that redirects, oversized input, unsafe
  types, secrets, prompt injection and interrupted downloads fail closed.

Completion gate: two daily cycles complete unattended, including one changed
source and one deliberate failure, without changing the last accepted corpus
on failure. URL, Git and uploaded-manual sources can each be enrolled through
the UI and reach the accepted human corpus without shell or manifest editing.

## Milestone 3 — Aster analysis mirror

- [ ] Implement changed-document analysis using the fixed mirror schema.
- [ ] Preserve page/section locators and source hashes for every salient claim.
- [ ] Add verification that each claim is supported by its cited source and
  that uncertainty, version scope and destructive warnings survive reduction.
- [ ] Create asset, service, dependency, symptom and recovery indexes.
- [ ] Prevent duplication and mark superseded entries without deleting their
  provenance history.
- [ ] Produce a deterministic validated snapshot consumable by Aster's current
  authority-aware retrieval path.

Completion gate: the same accepted inputs and pipeline version reproduce the
same packaged mirror, and every tested claim maps to an exact human-source
location.

## Milestone 4 — Teacher/pupil evaluation

- [ ] Create a versioned evaluation set for manuals, ARR, Home Assistant,
  topology, dependencies, troubleshooting, conflicts, stale versions and
  missing information.
- [ ] Compare complete-source retrieval with mirror-first retrieval for answer
  correctness, citations, context tokens and latency.
- [ ] Require Aster to fall back to the human source when the mirror is
  insufficient rather than extrapolating.
- [ ] Test poisoned documents, misleading summaries, conflicting authorities,
  secret requests and requests to execute document instructions.
- [ ] Run regression suites for Aster's graduated general, ARR and Home
  Assistant capabilities.
- [ ] Repeat the complete production-path evaluation twice on the same accepted
  snapshot.

Completion gate: all critical cases pass twice, mirror-first answers retain or
improve correctness and provenance, and the evidence demonstrates a useful
reduction in retrieval context or latency without losing safety-critical facts.

## Milestone 5 — Recovery, operations and graduation

- [ ] Add both repositories, collector state, accepted originals where legally
  permitted and the deployed mirror snapshot to verified local, off-host and
  encrypted off-site coverage.
- [ ] Rebuild both the human presentation and mirror from clean repositories
  plus protected originals in an isolated environment.
- [ ] Test rollback after a deliberately bad upstream update and a deliberately
  bad generated summary.
- [ ] Document adding equipment, adding a source, reviewing quarantine,
  correcting source material, resuming a run and restoring service.
- [ ] Add daily pipeline health and monthly corpus-health checks for staleness,
  provenance, broken links, version mismatch, duplicate entries and taxonomy
  decay.
- [ ] Record final limitations, ownership and the exact accepted versions and
  hashes in the evidence log.

Completion gate: the service survives isolated restore, daily operation is
unattended and observable, rollback is proven, and all evaluation and security
gates pass without widening Aster's existing authority.

## Graduation criteria

The project graduates only when:

- every milestone completion gate passes with dated evidence;
- operators can add a new equipment page and source through a documented,
  low-friction browser workflow without Git or YAML knowledge;
- the daily pipeline resumes safely after interruption or model usage limits;
- source and mirror repositories are independently recoverable;
- all derived claims preserve source hashes and exact locators;
- unsafe or unsupported analysis is quarantined rather than published;
- Aster demonstrably uses the mirror faster or with less context while retaining
  source-correct answers and explicit uncertainty;
- the full human source remains one action away from every mirror result;
- production operation remains independent of Aster and of Internet access;
  and
- Aster retains its existing read-only capability and approval boundaries.

## Rollback

Disable the daily timer, keep the last accepted `homelab-wiki` lock and mirror
commit, and atomically reactivate the previous Aster snapshot. The human wiki
continues serving its last accepted static build. Collector staging and
quarantine may be retained for diagnosis but are never included in retrieval.
If the analysis layer is untrustworthy, remove the mirror sources from the
snapshot manifest and return Aster to the currently graduated second-brain
snapshot; the complete human repository remains intact.

## Evidence log

| Date | Milestone | Evidence | Result |
|---|---|---|---|
| 2026-09-10 | Design | Compared the proposed human/mirror split with the graduated second-brain authority, deterministic snapshot, recovery and evaluation guidance | Project ready; derived analysis is viable provided it remains reproducible, non-authoritative and traceable to exact human-source locations |
| 2026-09-10 | Start | Jason directed autonomous execution; recorded Stream A scope, exclusions, live dependency baseline, risks, recovery/abort conditions, persistence and every integration impact before implementation | Project active within the documented envelope; remote mutations and non-waivable stops remain separately controlled |
| 2026-09-10 | 1 | Created private Forgejo repositories `jason/homelab-wiki` and `jason/aster-knowledge-mirror`; verified private flags and exact initial commits `678786c`/`260cdb0`. Added explicit human/mirror contracts, strict manifest validation, five representative synthetic/local pages, safe local rendering and an intake UI. Ten tests cover URL, Git and real manual-upload previews, scope, TLS rejection, upload limit, active-HTML escaping and atomic idempotent candidates | Milestone 1 gate passed. A person can browse the offline seed and stage every supported source type without Git/YAML editing; provenance and authority boundaries are explicit. Production deployment intentionally waits for Milestone 2's collector and security gates |
| 2026-09-10 | 2 checkpoint | Added schema-versioned SQLite run/item state, per-stage checkpoints, run-specific staging, atomic accepted-lock/corpus publication, last-good rollback, tamper verification, bounded reports, operator run/resume/status/verify/rollback modes, daily systemd candidates and recoverable pause/resume/retry/retire queue controls. Acquisition covers HTTPS, protected uploads and bounded Git documentation paths. Twenty-one synthetic tests pass, including failed-update preservation, interruption/resume, redirects, traversal, size/type/secret/injection rejection and rollback | Safe-acquisition core is locally proven but Milestone 2 remains open pending authenticated queue promotion, conditional-fetch/rate-limit state, production target/address selection, Doctor integration and two unattended live cycles |
| 2026-09-10 | 2 discovery | Proxmox reports VMID 113 next, cached Debian 13 and ample storage/memory. NetBox 4.6.9's sanitized authoritative report shows `192.168.20.33` belongs to `backup-relay`, correcting the tempting inference from stale human addressing documentation | Do not allocate `.33`; exact NetBox IPAM confirmation is required before choosing the collector address. No guest or network state changed |
| 2026-09-10 | 2 deployment checkpoint | Reconciled the interrupted deployment: unprivileged Debian 13 LXC 113 `aster-wiki` is running at `192.168.20.34` with the expected 2 cores, 2 GiB RAM, 16 GiB disk, VLAN 20 firewall flag and boot ordering. The intake service is installed/enabled but failed because deployed Python 3.13.5 no longer provides `cgi`; the collector timer is disabled/inactive. Replaced `cgi.FieldStorage` with a bounded standard-library `email` multipart parser, added malformed-boundary and encoding regressions, and passed 23/23 local tests | Failure is understood and fails closed with no listener or accepted publication. The tested fix is ready for redeployment, which is paused at the repository-required confirmation for modifying the remote guest. The daily timer must remain disabled until later Milestone 2 gates pass |
| 2026-09-10 | 2 intake recovery | After Jason's explicit remote-mutation confirmation, retained the deployed pre-fix module as `/opt/aster-wiki/aster_wiki/app.py.before-fb1f160`, deployed the exact tested `app.py`, and restarted the intake service. Separate checks found the service active, Python listening only on `127.0.0.1:8787`, and `/healthz` returning `{"status":"ok","mode":"prototype"}`. The first HTTP probe only established that `curl` is not installed; a standard-library Python probe passed without adding a package | Intake presentation recovered on Debian 13 without broadening network exposure or dependencies. Collector timer remains disabled/inactive and no corpus or Aster snapshot was published |
| 2026-09-10 | 2 conditional acquisition | Added durable per-source ETag/Last-Modified state and conditional request headers. A `304` reuses prior content only after checking its normalized hash against the accepted lock, copies the verified content and provenance into the new atomic candidate, and reports it as `unchanged`; absent or tampered accepted input quarantines the run. Complete local suite passes 25/25 tests | No-change cycles now avoid unnecessary downloads without allowing an upstream validator to bypass local integrity. Deployment and rate-limit work remain pending; timer stays disabled |
| 2026-09-10 | 2 deployed acquisition gate | Deployment revealed that systemd's separate writable bind mounts made cross-device atomic renames impossible. Moved run staging and last-good directories onto the wiki filesystem, constrained run IDs against traversal, expanded the systemd writable scope only to the wiki `docs` and `sources` directories plus collector state, and retained the prior service/module files for rollback. Local suite passes 26/26. A deployed manual cycle accepted and `verify` checked one synthetic source. A second cycle substituted the tracked `synthetic-secret.txt` negative fixture, produced a bounded report with `quarantined: 1`, then restored the safe upload. Before/after SHA-256 remained `5f0c7a6a159cee7e4daf1b30d222464686ce6e4e06581efbaa27403d4050c0df` for content and `65f7f13275033960b4893bdc8de25560e2f1a891a604841e8a21c597ea1cdd3b` for the accepted lock | Deployed changed-source acceptance and deliberate failure preservation passed. The timer remains disabled/inactive. Two pre-publication systemd-debug attempts remain explicitly visible as interrupted run IDs; they did not change accepted content and will be used to prove operator resume/closure rather than erased |
| 2026-09-10 | Recovery checkpoint | With Jason's explicit confirmation, created snapshot-mode archive `vzdump-lxc-113-2026_09_10-14_13_06.tar.zst` on Proxmox `backups` storage (192 MB compressed; 674,539,520 bytes expanded). `zstd --test` passed, and targeted archive listing confirmed the deployed collector, collector systemd unit and accepted lock are present | A verified local recovery carrier now exists before further production changes. Off-host/off-site propagation and isolated restore remain required for graduation |
| 2026-09-10 | Remote synchronization | Pushed current `main` through `7dc6b28` to Forgejo after explicit approval. After destination-specific confirmation, the GitHub protection push reported `Everything up-to-date`, consistent with existing mirroring | Current committed milestone history is synchronized; later commits still require their own repository-authorized push confirmation |
| 2026-09-10 | 2 queue, pacing and Doctor candidate | Added persistent per-host request timing with a two-second minimum interval that survives process restarts. Manual acceptance atomically stores bounded uploads for a dedicated intake-to-collector group handoff; the collector atomically promotes validated enrollment/control candidates into the manifest and moves processed queue records to an audit directory. Added a HomeLab Doctor check for intake health, durable collector state and timer enablement plus LXC 113 backup age. Exact live probe currently returns the intended warning because the intake is healthy while the timer remains deliberately disabled. Local suite passes 28/28 and `bash -n` validates Doctor | Core acquisition, atomicity, scope and fail-closed Milestone 2 checkboxes are now evidence-backed. Deployment, private Authentik/proxy enforcement, timer scheduling and two observed scheduled cycles remain open |
| 2026-09-10 | 2 deployed queue handoff | Deployed the queue, upload, pacing and state modules with `/opt/aster-wiki/aster_wiki.before-1f35a86` retained. The first retry candidate proved intake's original `0700/0600` queue was correctly inaccessible to the separate collector identity. Corrected the shared handoff to group-restricted `0770/0640` queue permissions while uploads remain `0750/0640`; rerun moved the candidate into collector-owned processed history, left the live queue empty and passed accepted-corpus verification. Intake remained healthy and the timer remained disabled | Least-privilege intake-to-collector handoff is now proven with distinct service users. No candidate bypassed validation and no scheduling was enabled |
| 2026-09-10 | Process clarification | Jason clarified that remote Git synchronization belongs at milestone completion rather than after intermediate stages. Added the milestone-only synchronization cadence to the durable charter while retaining the repository-required immediate confirmation before each actual push | Intermediate work now uses local commits without repeated push requests; the next synchronization request occurs only after the Milestone 2 completion gate passes |
| 2026-09-10 | 2 authentication staging | After explicit confirmation, changed the intake listener to `0.0.0.0:8787` and enabled a dedicated nftables policy that permits loopback and NPM `192.168.50.23` to that port while dropping every other source to that port; all unrelated input remains unchanged. The first enable did not reload the already-active nftables unit, which a direct-client test caught; an explicit restart loaded the intended rules. Localhost health then returned HTTP 200 and a direct client was denied. NPM remains unable to connect because Management VLAN 50 currently has no narrow route to `192.168.20.34:8787`. Authentik 2026.8.0 presents its password/passkey login and requires Jason's interactive sign-in before provider/application creation | Backend exposure is fail-closed: only localhost works until the OPNsense rule is added, and the collector timer remains disabled. Resume after Jason signs into the displayed Authentik admin tab; then create the dedicated provider/application, narrow OPNsense rule, NPM host and private DNS records and validate the full login path |
| 2026-09-10 | 2 Authentik gate | The remote host had no visible browser session, so the approved onboarding used an idempotent `ak shell` provisioning script instead of UI automation. It cloned the known-good NPM provider flows into a dedicated `forward_single` provider for `https://wiki.elliottrook.com`, created the `aster-knowledge-wiki` application, bound exactly the existing owner identity because the proposed admin group does not exist, and attached the provider to the embedded outpost. The first atomic attempt rejected an incorrect policy-binding field type and rolled back; the corrected rerun reported one enabled owner binding and an attached outpost | The identity-layer objects are complete without storing credentials or identity details in Git. Network, NPM and split-DNS remain fail-closed and must be completed before browser authentication can be exercised |
| 2026-09-10 | 2 private network gate | After explicit approval, saved `/conf/backup/config-aster-wiki-before.xml`, added one validated OPNsense MVC firewall rule, saved the configuration and reloaded the filter. The persistent rule permits only TCP from NPM `192.168.50.23` to the wiki backend `192.168.20.34:8787`, on Management VLAN 50, before the private-network block. The loaded `pf` rule matched that exact tuple; a request originating in the NPM guest returned HTTP 200 from `/healthz`, while a direct Mac client still timed out at the backend nftables boundary | The reverse proxy can now reach the service through a least-privilege path, while direct access remains denied. NPM host creation and split DNS remain pending |
| 2026-09-10 | 2 reverse-proxy gate | After explicit approval, used a bounded idempotent helper to make a consistent SQLite backup and protected prior-row export, then created only NPM proxy host 7 for `wiki.elliottrook.com` pointing to `192.168.20.34:8787`. It retains wildcard certificate 8, forced TLS and the known-good minimal Authentik forward-auth behavior from host 2. NPM's bundled regeneration utility rebuilt all enabled hosts, `nginx -t` passed and workers reloaded. A certificate-valid `curl --resolve` request returned HTTP/2 302 to the same public hostname's Authentik start path; the existing NPM host still returned 302, and generated host 7 contains the auth request/outpost locations with no `X-authentik-*` identity propagation | TLS termination, backend routing and unauthenticated forward-auth interception are operational without depending on DNS. Split-DNS publication and an interactive owner login remain pending |
| 2026-09-10 | 2 split-DNS checkpoint | After authorization, retained restrictive copies of each Pi-hole `pihole.toml` and added only `192.168.50.23 wiki.elliottrook.com` to the existing `dns.hosts` arrays. Both Pi-hole resolvers independently returned the intended address, and the normal Mac resolver path reached the certificate-valid HTTP/2 Authentik redirect. Restarting OPNsense dnsmasq cleared its cache but its independent resolver still returned no answer, demonstrating that its client-facing port 53 path does not consume that internal listener's data | Client split DNS is working through both redundant Pi-holes. The documented three-resolver gate remained open pending a matching OPNsense Unbound host override |
| 2026-09-10 | 2 split-DNS completion | The initial OPNsense override was valid on dnsmasq's internal port 53053 but not visible through client-facing Unbound on port 53. After a fresh configuration backup and explicit confirmation, atomically removed that redundant dnsmasq record, created the same `wiki.elliottrook.com` A record in the Unbound model, validated both models, saved once and restarted both resolvers. OPNsense, primary Pi-hole and secondary Pi-hole each independently returned `192.168.50.23`; the normal HTTPS request continued to return the expected Authentik 302 | The narrow private DNS, certificate, firewall and proxy path is complete and independently verified across every documented resolver |
| 2026-09-10 | 2 retained originals and portal state | Added protected content-addressed storage of exact fetched bytes outside Git, recorded the retained path and licence state in accepted provenance, and extended verification to fail on original tampering. Added a read-only source dashboard plus bounded per-source run history and input-hash change indicators without exposing original content. Deployment retained the prior modules. The first controlled run accepted and verified one source and created a mode-`0640` retained original. Its dashboard request exposed mode-`0600` atomic manifest/lock publication; corrected both writers to `0640`, added regression assertions, redeployed, and reran successfully. Live dashboard and history pages render the accepted source, both files remain collector-owned/group-readable, verification passes, and the timer remains disabled. The local suite passes 30/30 | Conditional fetch, rate limiting, validation, normalization, quarantine and retained-original handling are complete. Portal state/history and least-privilege cross-service reads are live; interactive owner authentication and scheduled-cycle evidence remain before Milestone 2 closure |
| 2026-09-10 | 2 interactive authentication | From a normal client, Jason opened `https://wiki.elliottrook.com`, completed the Authentik password/passkey flow and confirmed return to the “Add a private knowledge source” intake page. Earlier unauthenticated testing proved the HTTP/2 302 interception, while direct backend access remained denied | The owner-only authenticated portal gate is complete. Scheduled daily cycles are the remaining Milestone 2 completion evidence |
| 2026-09-10 | 2 portal and original candidate | Added read-only source-state summaries, bounded per-source run history and hash-based input-change visibility without exposing source content. Exact fetched bytes now enter a protected content-addressed state tree using restrictive directory/file modes; accepted locks record that path and verification fails closed if either normalized content or its retained original changes. Expanded local coverage passes 30/30 tests, including dashboard/history reads, original byte preservation/mode and tamper detection | The remaining Milestone 2 portal and retained-original implementation is locally complete. Deployment and a live accepted run are pending; the production timer remains disabled |
