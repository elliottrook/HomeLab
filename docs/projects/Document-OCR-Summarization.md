# Document OCR + Summarization Project

> Status: Active — Stream A; Milestone 1 in progress
>
> Project owner: Jason
>
> Proposed: 2026-09-15
>
> Authorized: 2026-09-15 (Stream A, this project only)
>
> Authorization stream: Stream A — autonomous, scoped to this project's
> enumerated milestones below; see "Resolved decisions" for the three
> pre-start calls Jason made at authorization time

## Resolved decisions (2026-09-15, at Stream A authorization)

Jason resolved the three decisions this charter flagged as required before
work starts:

1. **One project or two:** kept as **one project**. Paperless-ngx deployment
   is this project's own Milestone 1; the summarization work follows as
   Milestones 2+. The Stream A authorization envelope therefore covers both
   the document-management infrastructure work and the AI-specific work.
2. **Write-back into Paperless:** **yes** — summaries will be written back
   into Paperless as a custom field/note once built, overriding this
   document's no-mutation-by-default recommendation. Per the charter's own
   treatment of this as a non-waivable-stop-condition-adjacent decision, the
   write path must still be a separately-scoped, narrowly-limited broker
   (custom-field write only — never delete, move, or retention-change),
   built and reviewed at Milestone 4, not a broad Paperless write credential
   handed to the summarization service generally.
3. **Sensitive-document exclusion policy:** **summarize everything by
   default** — no tag/type-based exclusion. Milestone 2's design does not
   need an exclusion mechanism; every ingested document's OCR text will be
   sent to `aster-llama` for summarization regardless of document type.

The fourth item (`aster-llama` shared-capacity contention across the news
aggregator, Aster, and this project) is not a decision with options — it
remains an accepted, monitored risk; watch for latency/contention once this
project is actively calling the endpoint.

## Purpose and desired outcome

Give Jason short, readable summaries of scanned/uploaded household documents
(mail, statements, forms, receipts, warranties, etc.) instead of having to
open and read each one. This was originally pitched paired with
Paperless-ngx, and this document keeps that pairing explicit rather than
assuming a document-management system already exists.

## Current state and evidence

- **Paperless-ngx is not deployed anywhere in this lab.** Checked
  `PROJECTS.md` directly rather than assuming: it appears exactly once,
  under "Future Services" (`# Future Services` section, alongside "Wiki"),
  as an unstarted idea with no design, no guest, no data. There is no
  existing document corpus, OCR pipeline, or document database to build
  on. This means **deploying Paperless-ngx (or an equivalent
  document-management target) is a genuine prerequisite**, not a detail —
  see Scope and Milestone 1 below.
- **OCR already exists inside Paperless-ngx itself**, via its own
  `ocrmypdf`-based ingestion pipeline (Paperless's standard, well-documented
  behavior: incoming documents are OCR'd, text-indexed, and tagged/dated
  automatically as part of its normal consume workflow). This project does
  not need to build or evaluate a separate OCR engine.
- **Local LLM inference already exists and is reusable:** `aster-llama` on
  LXC 110 (`192.168.70.12:11435`, OpenAI-compatible `/v1`, bearer-auth, Lab
  VLAN 70 only) already serves the news aggregator's summarization pipeline
  and the Aster sysadmin advisor.
- **Established integration pattern:** every prior AI-touching project in
  this lab that reads from a separate system of record does so through a
  source-local, least-privilege, read-only reader that publishes a
  sanitized report — the AI/consuming layer gets no mutation authority
  unless a separate, explicitly-approved broker exists
  (`docs/projects/completed projects/Aster-Sysadmin-Second-Brain.md`,
  `Aster-Forgejo-NetBox-Read-Only.md`, `Aster-Arr-Stack-Manager.md`'s
  execution-disabled broker). This project should follow the same shape
  against Paperless.

## Scope

- **In scope:**
  1. Standing up Paperless-ngx (or confirming and using an equivalent
     document-management target) as this project's own Milestone 1
     prerequisite, since none exists to build on — see the open decision
     below about whether this should instead be split into its own
     separately-authorized project.
  2. A read-only summarization layer that consumes Paperless's
     already-OCR'd text and metadata (title, correspondent, document type,
     tags, date) via Paperless's own API, and generates a short summary per
     document using `aster-llama`.
  3. Presenting those summaries somewhere Jason can read them (see
     Architecture — deliberately not assumed to be "inside Paperless" by
     default).
  4. Explicit handling of document sensitivity (tax forms, government IDs,
     medical records, financial statements) as a first-class design
     concern, not an afterthought.
- **Out of scope:**
  - Building a new OCR engine or pipeline. Paperless's own `ocrmypdf`
    pipeline already does this; duplicating it would be reinventing an
    already-solved problem and is explicitly rejected as this project's
    scope, per the brief's own framing.
  - Any write/mutation access to Paperless — no ability to alter document
    content, correspondent, tags, retention, or storage path, and no
    ability to delete a document, unless a separate, explicitly-approved
    write broker is proposed and authorized later (matching the ARR
    stack manager's execution-disabled-broker precedent).
  - General household document workflow redesign (physical scanning
    hardware, mail-sorting process, filing conventions) — this project
    consumes whatever Paperless already ingests; it does not change how
    documents get into Paperless.
  - Any cloud OCR or cloud LLM summarization — stays local, per the lab's
    local-first principle and this project's reuse of `aster-llama`.

## Out of scope

(See Scope above — consolidated there since the exclusions are numerous and
directly paired with their corresponding in-scope item.)

## Authority model

- **Paperless-ngx** (once deployed) is the authority for document content,
  OCR text, metadata, tags, correspondents, and retention/storage — this
  project never becomes a second copy of that authority.
- **This project's own summarization store** (a small database, scoped to
  this project's own guest) is the authority for generated summaries only —
  it is a derived artifact, not a system of record for the underlying
  documents, and must not be treated as replacing Paperless if Paperless is
  ever lost; a lost summary can always be regenerated from Paperless's own
  OCR text, but a lost original document cannot be regenerated from a
  summary.
- **Aster's mirror**, if this project is ever referenced there, would hold
  non-authoritative derived knowledge only, same as every other Aster
  integration in this lab.

## Architecture and data flows

### Prerequisite: Paperless-ngx deployment

Standard Lab-VLAN-70 placement pattern (new unprivileged LXC, matching the
Aster Agent/`aster-llama`/news-aggregator convention), OCR pipeline
configured per Paperless's own documented consume-folder or API-upload
workflow, storage sized against real document volume once known. This is
deliberately not designed in further detail here — it is its own
substantial piece of work (storage sizing, consume-folder vs. mobile
upload vs. scanner integration, backup of the document archive itself,
retention policy for originals) and arguably deserves scoping as **its own
project document** rather than being folded silently into an "AI
summarization" charter. See the open decision below.

### Summarization layer

- A new small service (co-located with Paperless's guest, or a separate
  Lab VLAN 70 guest — open decision, see below) that:
  1. Polls or receives a notification of newly-processed Paperless
     documents (Paperless supports webhooks/consumption-finished hooks in
     recent versions — to be confirmed against the deployed version during
     Milestone 2, not assumed here).
  2. Reads that document's OCR'd text and metadata via Paperless's REST
     API, using a **read-only, least-privilege API token** scoped as
     narrowly as Paperless's own permission model allows (Paperless
     supports per-user API tokens and Django-level object permissions;
     the exact achievable granularity needs to be confirmed live during
     Milestone 2 against the actually-deployed version — not assumed from
     general knowledge of the product).
  3. Sends the extracted text to `aster-llama` (`http://192.168.70.12:11435/v1`,
     bearer-authenticated with a new dedicated least-privilege key, matching
     the news aggregator's own dedicated-key pattern) for summarization.
  4. Stores the resulting summary, keyed to the source document's Paperless
     ID, in its own local database, and — per Jason's 2026-09-15 decision —
     also writes it back into Paperless as a custom field/note via the
     Milestone 4 scoped write broker once that exists (Milestones 1-3 write
     to the local store only; the broker isn't built yet).
- No component in this pipeline receives Paperless admin credentials, write
  scope, or the ability to alter/delete/misfile a document.

### Decided: one project (2026-09-15)

Resolved by Jason at Stream A authorization — see "Resolved decisions"
above. Kept as one project: Paperless deployment is this project's
Milestone 1, summarization is Milestones 2+.

### Decided: write-back into Paperless, via a scoped broker (2026-09-15)

Resolved by Jason at Stream A authorization — see "Resolved decisions"
above. Summaries will be written back into Paperless as a custom
field/note. The write path is a separately-scoped, narrowly-limited broker
(custom-field write only — never delete/move/retention-change), matching
the ARR stack manager's execution-disabled-broker precedent, designed and
reviewed at Milestone 4 rather than granted as a general credential now.

## Privacy and security design

- **Document sensitivity is the dominant risk in this project**, more so
  than any other AI-integration project in this lab to date — a
  document-management system commonly holds tax forms, government IDs,
  medical records, and financial statements, all of which would pass
  through this pipeline's `aster-llama` calls as plaintext (locally, not
  leaving the lab, but still processed by a shared service).
- **Read-only, least-privilege, source-local access only, until Milestone
  4's scoped write broker exists.** No admin credentials, no broad write
  scope; a dedicated API token scoped as narrowly as Paperless's permission
  model allows for the summarization reader, and a separate, narrower
  custom-field-only token for the Milestone 4 write-back broker once built.
- **Data minimization: decided 2026-09-15 — summarize everything by
  default.** No tag/type-based exclusion. Every ingested document's OCR
  text is sent to `aster-llama` regardless of document type. This raises
  the baseline exposure of sensitive document content (tax/ID/medical) to
  the summarization pipeline on every document, not just non-sensitive
  ones — accepted by Jason at authorization; revisit if real-world use
  surfaces a document class that should have been excluded.
- **No cloud dependency.** Both OCR (inside Paperless) and summarization
  (`aster-llama`) stay local, consistent with this lab's local-first,
  maximum-practical-privacy principles.
- **Standard placement/exposure:** Lab VLAN 70, bearer-authenticated API,
  Lab-VLAN-only exposure, unprivileged LXC — no public exposure proposed.
- **Shared `aster-llama` capacity is a real, open constraint**, not assumed
  away: this endpoint already serves the news aggregator and Aster: adding
  a third caller (this project) means genuine contention is possible under
  concurrent load, and no capacity ceiling has been measured for
  simultaneous multi-project use.

## Pre-start risk assessment

- **Objective and scope:** deploy the prerequisite document-management
  substrate (Paperless-ngx or equivalent — see open decision on whether
  this is one project or two) and a read-only summarization layer on top of
  it. Exclusions: no OCR reimplementation, no default Paperless write
  access, no cloud dependency, no new inbound Internet exposure.
- **Affected systems:** a new Paperless-ngx guest and its storage (new,
  substantial), the summarization service guest (new or co-located), and
  `aster-llama` on LXC 110 (existing, shared, contended).
- **Data at risk:** household documents of real sensitivity — tax records,
  IDs, medical, financial. This is qualitatively more sensitive than any
  data previously handled by an AI-touching project in this lab (the news
  aggregator handles public RSS content; Aster's existing curricula are
  infrastructure/operational data). Treat with the highest privacy
  standard applied so far in this repository.
- **Confidentiality/secret-handling risks:** the summarization API token
  and the `aster-llama` dedicated key are the only new credentials;
  neither should ever appear in logs or Git. A leaked summarization-service
  token would grant read access to potentially all documents in Paperless —
  the token's scope should be minimized as far as Paperless's permission
  model allows, and rotated if ever exposed, per this lab's established
  practice on prior credential-exposure incidents (see the NUT project's
  own handling in `CLAUDE.md`).
- **Availability/integrity/privacy/recovery risks:** a bug in the
  summarization service must not be able to corrupt, delete, or misfile a
  real document — enforced structurally by giving it no write scope, not
  merely by convention.
- **Irreversible/destructive operations:** none anticipated in the
  summarization layer itself. The Paperless deployment prerequisite may
  involve storage/dataset decisions (where documents live, retention of
  originals) that should get their own explicit recovery-checkpoint
  discussion when that milestone is reached — not assumed safe by default
  given the document sensitivity involved.
- **Expected auth/firewall/DNS/storage changes:** a new guest (or two) on
  Lab VLAN 70 with the standard narrow `MGMT_ADMIN_HOSTS`-style access
  rule, matching precedent; storage sizing for the Paperless document
  archive is unknown until real document volume is known.
- **Recovery checkpoint/rollback/abort:** the summarization layer alone is
  cheaply reversible (no mutation authority, derived data only). The
  Paperless deployment prerequisite needs its own backup/restore proof
  before being trusted with real household documents — treat "back up and
  test-restore the document archive" as a hard gate before any real
  (non-synthetic) document is ingested for summarization.
- **Test strategy:** use synthetic, clearly-labelled disposable test
  documents (not real tax/ID/medical documents) for pipeline development
  and validation, promoting to real documents only after the pipeline's
  read-only boundary and summarization quality are both proven.
- **Likely service interruption:** none to existing services; this is
  entirely new infrastructure.
- **Backup/Doctor/monitoring/NetBox/wiki impacts:** see the integration
  checklist below — all currently "not applicable, no implementation yet"
  except where a real gap is identifiable in advance.
- **Decisions resolved by Jason at Stream A authorization, 2026-09-15**
  (see "Resolved decisions" near the top of this document): one project
  (not split), write-back into Paperless via a Milestone 4 scoped broker,
  and summarize everything by default (no sensitive-document exclusion).
- **Remaining accepted, monitored risk:** `aster-llama` capacity contention
  across three concurrent projects (news aggregator, this project, Aster)
  once this project is active — not a decision with options, just a risk to
  watch.

## Persistence plan

Not applicable in detail at proposal stage — no implementation has started.
Once Milestone 1 begins, record current milestone, completed steps, exact
blockers, next safe action, and rollback location, per the Standard's
persistence requirements — with particular care given the document
sensitivity involved (no raw document content or secrets in the
project log or evidence entries).

## Milestones

All milestones are proposed and unchecked. None has been started.

### Milestone 1 — Document-management substrate (prerequisite)

- [x] Jason decided 2026-09-15: one project (not split) — Paperless
      deployment proceeds as this project's own Milestone 1.
- [x] Deployed Paperless-ngx 2026-09-15: new unprivileged LXC 115
      (`paperless-ngx`), Lab VLAN 70, `192.168.70.14`, matching the LXC
      113/114 convention (2 cores, 2048 MB memory, 512 MB swap, Debian 13,
      `keyctl=1,nesting=1` features). Docker CE 29.8.1 + Compose v5.5.1
      installed inside the LXC; Paperless-ngx deployed via its official
      `docker-compose.sqlite.yml` (broker: Valkey 9-alpine; webserver:
      `ghcr.io/paperless-ngx/paperless-ngx:latest`, SQLite backend) under
      `/opt/paperless-ngx`, matching this lab's `/opt/<name>` placement
      convention for Lab VLAN 70 services. A fresh `PAPERLESS_SECRET_KEY`
      was generated server-side; an initial echo of it into command output
      was caught and the key was silently rotated before proceeding (same
      root-cause pattern as prior credential-exposure incidents in this
      repo — see `CLAUDE.md`'s NUT project history). `PAPERLESS_TIME_ZONE`
      set to `America/Vancouver` to match the Proxmox host's own timezone
      (guest OS itself defaults to UTC, matching LXC 113/114). A superuser
      account (`jason`) was created with a random temporary password
      stored only at `/root/.paperless-temp-password` (mode 600) on LXC
      115 — never displayed in this session; retrieve it via `pct exec 115
      -- cat /root/.paperless-temp-password` and change it immediately on
      first login.
- [x] Storage: 32 GB `local-lvm` rootfs (10x+ headroom over a typical
      household OCR'd-PDF document archive; resizable later if needed).
      Paperless's `data`/`media`/`redisdata` are Docker named volumes,
      which live under the LXC's own rootfs, so they ride the existing
      **same-site nightly Proxmox backup** automatically — confirmed via
      `/etc/pve/jobs.cfg`'s active `vzdump` job, which backs up `all`
      guests (LXC 115 needed no separate job entry). **Off-site mirror
      coverage (Backup Synology / IDrive e2) has not yet been verified for
      this specific guest** and remains the hard gate before any real
      (non-synthetic) document is ingested, per this document's own
      Backup/restore/rollback section — do not ingest real documents until
      that is confirmed.
- [x] Confirmed live, not assumed: consume-folder ingestion and the OCR
      pipeline both work end-to-end — a synthetic image-based test
      document (`synthetic-ocr-test.png`, generated via ImageMagick,
      clearly labelled, not a real document) dropped into
      `/opt/paperless-ngx/consume/` was picked up, OCR'd via the
      container's bundled Tesseract, and its extracted text matched the
      source image (minor expected OCR noise: "HomeLab" read as
      "o9meLab"). Deleted immediately after confirming (`Document.objects
      .all().delete()`), consistent with this lab's synthetic-test-cleanup
      convention. Confirmed the DRF token-auth endpoint (`/api/token/`)
      exists and responds (HTTP 400 to an empty POST, i.e. present and
      correctly validating, not 404). **Real finding for Milestone 2's
      design:** Paperless-ngx's token auth is tied to a user account's own
      Django permissions (no separate fine-grained API scope concept) —
      the planned least-privilege reader needs its own dedicated
      non-superuser account with only `view_*` permissions granted, not a
      scoped token on the `jason` superuser account. Webhook/consumption-
      finished-hook support not yet confirmed against this specific
      deployed version — deferred to Milestone 2.

### Milestone 2 — Read-only integration design

- [ ] Create a dedicated, least-privilege Paperless API token; confirm its
      actual achievable scope (read-only, ideally document-content-only)
      against Milestone 1's findings.
- [ ] Confirm connectivity from the summarization service to Paperless's
      API and to `aster-llama`, using synthetic test documents only.
- [x] Sensitive-document exclusion policy decided 2026-09-15: summarize
      everything by default, no exclusion mechanism to build.

### Milestone 3 — Summarization pipeline

- [ ] Build the summarization service: polls/receives new-document
      notifications, pulls OCR text + metadata, calls `aster-llama` with a
      new dedicated key, stores the result locally keyed to the source
      document's Paperless ID.
- [ ] Verify against synthetic test documents first; only promote to real
      documents after the read-only boundary and output quality are both
      confirmed.

### Milestone 4 — Presentation

- [ ] Build the minimal summary view decided in Architecture (standalone
      page, or a Combined Morning Digest section if that project exists by
      then).
- [ ] Design and build the scoped write-back broker (custom-field write
      only, never delete/move/retention-change) per Jason's 2026-09-15
      decision to write summaries back into Paperless; review its scope
      explicitly before granting it any credential.

### Milestone 5 — Validation and graduation

- [ ] Confirm zero mutation capability against Paperless via a deliberate
      negative test (attempt a disallowed write with the service's own
      token; confirm it is rejected).
- [ ] Confirm summarization quality against a sample of real (already
      backed-up, already OCR'd) documents, sensitivity policy applied.
- [ ] Complete the required integration impact checklist for real.
- [ ] Evidence log complete; portfolio README updated (by others, per this
      task's instructions).

## Validation and evaluation

- **Functional:** a newly-ingested document (synthetic, then real) receives
  a correct, grounded summary within a reasonable time of Paperless
  finishing its own OCR/consume step.
- **Security/least-privilege:** the summarization service's Paperless token
  cannot write, delete, or move a document — proven with a deliberate
  denied-action test, not assumed from configuration alone.
- **Malformed/adversarial inputs:** a document with unreadable/garbled OCR
  text, a zero-byte document, or a document containing prompt-injection-like
  text embedded in its content should not cause the summarization service
  to take any action beyond producing a (possibly low-quality, clearly
  labelled) summary — no instruction embedded in document text should be
  able to make the service behave outside its read-only, single-purpose
  role.
- **Restart/failure behavior:** a `aster-llama` outage should fail this
  project's summarization run safely (retry/backoff, no data loss, no
  partial/corrupt summary presented as complete) without affecting the news
  aggregator's own use of the same endpoint, and vice versa.
- **Sensitive-data handling:** spot-check that no summary or log output
  contains full document numbers (SSN, account numbers) even when the
  source document does — a summarization prompt/output review step should
  specifically look for this before trusting the pipeline with real
  documents.
- **Two independent production-path passes**, per the Standard's baseline,
  before treating AI-mediated summarization output as reliable.

## Observability and maintenance

- HomeLab Doctor coverage for: Paperless-ngx availability, the
  summarization service's own availability, and a staleness check
  (documents ingested by Paperless with no corresponding summary after a
  reasonable threshold — matching the news aggregator's own
  freshness-check pattern for its audio pipeline).
- No new alerting surface beyond Doctor unless a specific gap is found
  during Milestone 5 testing.

## Backup, restore and rollback

- **Paperless's document archive** (originals, OCR text, database) needs
  its own backup coverage and a proven restore path before real documents
  are trusted to it — this is a hard prerequisite gate, not optional,
  given these are often irreplaceable originals (or the only digitized
  copy) of important documents.
- **This project's own summary store** is derived data — recoverable by
  re-running summarization against Paperless's OCR text — and does not need
  the same restore rigor as the originals, but should still be included in
  the guest's whole-guest backup for convenience.
- Rollback for the summarization layer alone is simple (stateless service,
  no mutation authority, can be redeployed or removed without touching
  Paperless). Rollback for the Paperless deployment prerequisite is a
  larger undertaking and should be designed as part of Milestone 1, not
  assumed.

## Documentation and systems-of-record updates (required integration impact checklist)

- [ ] **HomeLab Doctor** — to be added in Milestone 5; not applicable yet
      (no implementation exists).
- [ ] **Monitoring/alerting** — covered by the Doctor check above; no
      separate alerting surface planned.
- [ ] **Backup and recovery** — not applicable yet; the Paperless archive's
      backup design is a hard Milestone 1 gate once implementation starts
      (see above), and the summary store rides the guest's whole-guest
      backup.
- [ ] **NetBox** — not applicable yet; a new VirtualMachine/interface/IP
      entry required once the guest(s) exist, following the news-aggregator
      project's own NetBox onboarding steps.
- [ ] **Human wiki** — likely applicable, unlike the news aggregator's own
      "not applicable" call: Paperless is a household document-management
      tool other family members may eventually use, so operator/user
      guidance may belong in the wiki once built — to be confirmed at
      Milestone 4, not decided here.
- [ ] **Aster mirror/snapshot** — not applicable by default; this project's
      summarization path is direct to `aster-llama`, matching the news
      aggregator's own precedent of not routing through Aster itself. If
      Jason later wants Aster to be able to answer questions about
      document summaries, that would be a separate, explicitly-scoped
      Aster integration with its own privacy review, not assumed here.
- [ ] **Operational reference and runbooks** — to be added once the
      pipeline exists; not applicable at proposal stage.
- [ ] **Repository documentation** — this document, kept current through
      each milestone.
- [ ] **Diagrams/rack records** — required once the guest(s) exist; not
      applicable at proposal stage.
- [ ] **Homepage/service discovery** — a tile for Paperless-ngx itself
      (and, if separate, the summarization view) once deployed; not
      applicable at proposal stage.
- [ ] **Authentication/authorization** — Paperless has its own login system;
      given the document sensitivity here, individual accounts (no shared
      admin login) and MFA where supported should be the default, matching
      this lab's existing individual-account convention (see the Synology
      Drive project's own "individual DSM accounts only" rule) — to be
      confirmed and enforced at Milestone 1, not left to Paperless's
      installer defaults.
- [ ] **DNS, certificates and firewall** — a narrow `MGMT_ADMIN_HOSTS`-style
      rule and an internal DNS name, per precedent; not applicable at
      proposal stage.
- [ ] **Automation and schedules** — the summarization trigger (webhook vs.
      poll) is the primary automation surface; decided at Milestone 2.
- [ ] **Security inventory** — two new credentials anticipated: the
      Paperless API token and the dedicated `aster-llama` key for this
      project, both least-privilege and both to be documented (location,
      not value) once created.

## Graduation criteria

This project graduates when: the document-management substrate is deployed
with a proven backup/restore path, the summarization service is proven to
have zero mutation capability against it via a deliberate negative test,
summaries are demonstrably grounded in the real OCR'd text (spot-checked
against real documents, not just synthetic ones), the sensitive-document
exclusion policy (if any) is implemented and working, HomeLab Doctor covers
the new surface, and the required integration checklist is closed with real
evidence.

## Evidence log

| Date | Milestone | Evidence | Result | Operator |
|---|---|---|---|---|
| 2026-09-15 | 1 | Created LXC 115 (`paperless-ngx`) on Lab VLAN 70 at `192.168.70.14`, matching LXC 113/114 convention; installed Docker CE 29.8.1 + Compose v5.5.1; deployed Paperless-ngx via its official SQLite compose file under `/opt/paperless-ngx` | `docker compose ps` showed both `broker` and `webserver` containers `Up`/`healthy`; `curl http://localhost:8000/api/` returned HTTP 302 (expected unauthenticated redirect, confirms webserver responding) | Claude |
| 2026-09-15 | 1 | Generated `PAPERLESS_SECRET_KEY` server-side; caught it echoing into command output and rotated it before proceeding, without displaying the new value | New key confirmed present (108-char env line), never displayed in this session | Claude |
| 2026-09-15 | 1 | Created superuser account `jason` via non-interactive `createsuperuser`, with a random temporary password stored only at `/root/.paperless-temp-password` (mode 600) on LXC 115 | `User.objects.all()` confirmed `['AnonymousUser', 'jason']`; password never displayed in this session | Claude |
| 2026-09-15 | 1 | Confirmed same-site backup coverage: checked `/etc/pve/jobs.cfg`'s active `vzdump` job configuration directly rather than assuming | Active job has `all 1` (backs up every guest); LXC 115 needed no separate entry | Claude |
| 2026-09-15 | 1 | End-to-end OCR pipeline smoke test: generated a clearly-labelled synthetic image (`synthetic-ocr-test.png` via ImageMagick) with known text, dropped it into the consume folder, polled for ingestion | Ingested and OCR'd within one 10s poll interval; extracted text matched the source image (minor expected OCR noise on "HomeLab"); deleted immediately after confirming (0 documents remaining) | Claude |
| 2026-09-15 | 1 | Confirmed the DRF token-auth API surface exists (`POST /api/token/`) and investigated its permission model rather than assuming from general product knowledge | HTTP 400 on empty POST confirms the endpoint is live and validating; found token auth is tied to a user's own Django permissions, not a separate scope system — recorded as a real Milestone 2 design input (dedicated view-only user account needed, not a scoped token on `jason`) | Claude |

**Not yet done, explicitly flagged rather than silently skipped:** off-site
backup mirror verification for LXC 115 (hard gate before real documents),
NetBox entry, DNS name, Homepage tile, the narrow `MGMT_ADMIN_HOSTS`-style
firewall rule for admin access, webhook/consumption-hook support
confirmation, and individual-account/MFA enforcement beyond the single
`jason` superuser created so far.

## References

- [Aster Sysadmin Second-Brain](completed%20projects/Aster-Sysadmin-Second-Brain.md)
  (source-local reader / no-mutation-authority pattern referenced above)
- [Aster Forgejo and NetBox Read-Only Integration](completed%20projects/Aster-Forgejo-NetBox-Read-Only.md)
- [Aster ARR Stack Manager](completed%20projects/Aster-Arr-Stack-Manager.md)
  (execution-disabled broker precedent referenced above)
- [News Aggregator (MuckScraper) — Phase 1](completed%20projects/News-Aggregator-MuckScraper.md)
  (dedicated least-privilege `aster-llama` key precedent)
- [Project Creation Standard](../Project-Creation-Standard.md)
- `PROJECTS.md` — "Future Services" section, the only prior mention of
  Paperless-ngx in this repository
