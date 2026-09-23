# Document OCR + Summarization — deployment close-out

> Status: Closed deployment — operational; user acceptance follow-ups below
> Owner: Jason
> Started: 2026-09-15
> Closed: 2026-09-23
> Stream: A, bounded to Paperless and its local summarization integration
> Close/commit/push/archive authorization: Jason, 2026-09-23, “Yes, please complete the steps, then close, commit, push and archive. All approved.”

## Delivered service

Open **https://paperless.elliottrook.com** from an approved management device, or
use the **Paperless-ngx** tile under Homepage's Application Management group.
The HTTPS route uses NPM's valid wildcard certificate, the established Authentik
login flow and a binding restricted to Jason; native Paperless login remains.
Browser verification reached “Log in to continue to Paperless.” Personal login
and passkey interaction remain the operator's responsibility.

LXC 115 now owns **192.168.70.15**, resolving the collision with Aster Speech
LXC 116 at .14. Speech was left unchanged. NetBox records are VM 17, interface
17 and address 31. The guest has 2 vCPU, 2048 MiB RAM and a 32 GiB disk.
Paperless 3.1.3, Valkey and the local summary services are operating.

Paperless performs OCR; the five-minute summary timer processes all visible
new documents and writes only the **AI summary** custom field through the local
capability broker. The reader is view-only, the writer has no API token or
password, and the worker cannot access Docker or the Paperless credential.
Inference stays on LXC 110 with its dedicated source-local key. No source
content is sent to an external AI provider.

## Validation evidence

- Approved-client backend login: HTTP 200; rendered login form verified.
- Private HTTPS: valid TLS, both Pi-hole answers point to 192.168.50.23;
  Authentik redirect and rendered Paperless-specific login prompt verified.
- Negative network checks: VLAN 20 cannot reach port 8000; its HTTPS request
  is denied with 403. NPM permits only .1.206, .1.241 and .1.112 for this host.
- A synthetic scanned warranty image was ingested, OCR extracted
  “15 December 2027”, and the Document Added workflow granted the reader access.
  The resulting summary preserved that date and the receipt requirement.
- Two complete generations succeeded, including recovery after a simulated
  inference outage. An intervening cycle skipped the unchanged summary without
  republishing. A broker restart and Paperless container recreation passed.
- Native API tests in a disposable database: granted read 200; hidden/revoked
  reads 404; document PATCH/PUT/DELETE and note writes 403; invalid token 401.
  The broker preserved other fields/document metadata, refused stale or extra
  arguments and revoked access, and did not invoke file-moving signals.
- A live revocation test with a human-owned synthetic document removed its
  derived rows. The first unowned fixture remained visible by Paperless's native
  policy; it was corrected to test actual access revocation, not merely grant
  removal. No production document was involved.
- Simulated inference failure produced unavailable status and unhealthy output;
  restoring the endpoint recovered the document and health. Production now runs
  in all-document mode with the timer enabled and zero unresolved errors.
- 23 local pipeline/worker tests and two strict-export tests pass. Long-document
  tests prove complete section coverage and no partial publication on failure.
- Post-deployment archive and TrueNAS copy SHA-256:
  `a31c8fcf50fe6218f8826848ae2aad8e6726f0cf76f4ea1398fab98394061a88`.
  Restored from TrueNAS into LXC 915 with no NIC/onboot. Both SQLite databases
  passed integrity checks, release hashes matched, the key retained mode 0600,
  broker/timer were active, and two restored login checks returned 200 with a
  healthy web container. Guest 915 and its disposable disk were removed.

## Backup scope resolved

The user explicitly requires **service-only offsite backup, not the database**.
Local Proxmox and TrueNAS whole-guest archives remain the data recovery tiers.
The relay now excludes all `vzdump-lxc-115-*.tar.zst` files. Seven exact historical
IDrive S3 archive versions were inventoried and removed, with zero remaining
versions for those keys verified; no shared-bucket purge or local deletion ran.

The accepted export contains only a fixed allowlist of release code, units,
non-secret example configuration and pinned Paperless reconstruction templates.
It excludes database, originals, OCR, summaries, credentials and runtime state.
`paperless-service/paperless-service-20260923.tar.gz` is on TrueNAS and encrypted
offsite storage; a decrypted read matches SHA-256
`2cab3443ee6cc267027819a92b4e5071ac0c94da359acd2a677d797ec31bcc06`.
The existing daily relay maintains this export; release changes require a fresh
reviewed manifest/export. The source repository is an additional code recovery
path, not a backup of document data.

## Integration and recovery

- The source-local UI/broker/timer/status checker is live and verified. The
  Paperless Doctor hook is included in this repository; installation into the
  separate operational checkout awaits explicit path approval after automatic
  approval review rejected that out-of-workspace write. No new alert destination.
- NetBox, private DNS, NPM host 25, Authentik provider 34/application `paperless`,
  Homepage and the narrow OPNsense rules are reconciled.
- [Operational reference](../../reference/Paperless-Operational-Reference.md),
  [summary operations](../../runbooks/Paperless-Summary-Operations.md),
  [isolated recovery](../../runbooks/Paperless-Isolated-Restore.md) and
  [IP correction](../../runbooks/Paperless-IP-Collision.md) record custody,
  revocation, rollback and checkpoints. The human wiki has a Paperless page.
- Aster's explicit knowledge allowlist includes the reviewed operational page.
  Document contents and summaries are excluded from the wiki/mirror corpus.
- No physical cabling, rack or power change occurred. The repository architecture
  and addressing records document the logical topology addition.

Stop the summary timer/broker to suspend AI processing while retaining Paperless.
Deactivate the dedicated identities to revoke access. Recover full state from a
local/TrueNAS archive in isolation; never reconnect a restored .14 identity.
The restricted native endpoint is an administrative recovery path, not the normal
browser launch route. Keep protected checkpoint files out of Git and offsite
service exports.

## User acceptance and bounded limitations

These remain visible follow-ups, not claims of completed validation. They do not
prevent the requested deployment close-out and archive; they prevent claiming
real-document quality or personal login acceptance has been demonstrated.

| Follow-up / limit | Owner and review point | Compensating control |
|---|---|---|
| First personal HTTPS login and native credential replacement | Jason, first use | Existing Authentik gate; native bootstrap credential stays root-only on LXC 115 |
| First real-document summary review | Jason, first real upload | Only labelled synthetic data existed; summaries are derived aids and originals remain authoritative |
| OCR above 96,000 characters or empty OCR | Jason, first such document | Visible unavailable/error status and bounded retries; no truncation or partial publication |
| Central AI-PAM custody migration | AI-PAM successor project, at broker readiness | Dedicated revocable key, source-local token, non-admin identities and fixed-capability Unix broker |
| Native recovery path uses restricted HTTP | Jason, next authorization review | HTTPS is normal launch; direct access limited to approved management hosts |

One clearly labelled synthetic warranty document (ID 2) is deliberately retained
as a visible demonstration. It contains no real personal data. All restore-test
resources are removed. Historical proposals and incomplete checkboxes below are
retained as history and are superseded by this close-out, not reclassified as
completed evidence.

## Historical project record

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


### Backup scope correction — Jason, 2026-09-23

Off-site backup is for the **service only, not the actual database**. This newer
instruction supersedes prior requirements for off-site whole-guest/database
coverage. Database recovery remains on Proxmox and TrueNAS; its successful
same-site restore proof remains valid. Exact document/original/OCR/summary
exclusions were asked for clarification; use no document-data export while that
answer is pending.

Live discovery found that whole-LXC 115 archives had already reached encrypted
IDrive storage through the shared guest backup path. A full decrypted archive
matched the local SHA-256, proving that the off-site copies include the database;
this is now contrary to the requested scope and must be corrected, not counted
as the final desired backup arrangement.

Prepared an exact LXC 115 exclusion in `scripts/backup/idrive-relay-sync.sh`.
Remote application awaits the requested explicit confirmation. The relay is
currently inactive; next scheduled run was approximately 12 hours away at this
check. This prevents future uploads but does not remove existing S3 object
versions. Inventory and separately approve the precise existing Paperless object
versions before deletion; never purge shared-bucket history or unrelated guests.
A service-only export must use an allowlist of code, units, deployment manifests
and non-secret configuration, not an exclusion-based copy of the guest rootfs.

Deployment checkpoint: database backup created locally at
`/opt/paperless-ngx/checkpoints/summary-integration-20260923/db.sqlite3` and passed
SQLite integrity. Reviewed service files and systemd units installed on LXC 115;
service account exists and systemd unit verification passed. Broker/worker/timer
have not been activated; integration identities/token/workflow and key transfer
have not yet been applied. Continue from this checkpoint after the backup-scope
correction; do not rerun the installer blindly over its existing config.

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


### UI access and dashboard — 2026-09-23

**Update:** Approved firewall/tile changes were applied and verified, but further
checks found a duplicate IP between Paperless LXC 115 and Aster Speech LXC 116.
OPNsense ARP and NetBox point .14 to speech. The tile exists, but its link cannot
work until the collision is resolved. See [collision correction plan](../../runbooks/Paperless-IP-Collision.md).
Candidate .15 has passed read-only vacancy checks; task-specific confirmation
is recorded in [AGENTS.md](../../../AGENTS.md). Readdressing remains pending and
requires a fresh vacancy check. Do not claim UI access is fixed yet.

Jason reported that the direct UI URL does not work and requested a dashboard
tile. Verified guest-local login HTTP 200 and listener `0.0.0.0:8000`; requests
from the operator Mac fail while the equivalent news UI succeeds. Live OPNsense
has the existing MGMT_ADMIN_HOSTS-to-news rule but no Paperless port-8000 rule.
Homepage has no Paperless tile. No application restart is indicated.

Prepared and successfully dry-ran `scripts/paperless/prepare_ui_rule.py` on
OPNsense and `scripts/paperless/add_dashboard_tile.js` inside Homepage. Proposed
rule: LAN ingress, existing MGMT_ADMIN_HOSTS alias only, TCP to
192.168.70.14:8000, sequence 3151, UUID
`fdc0bfb3-9dd4-4bca-869c-a571f8d64f02`. Proposed tile: Paperless-ngx under
Application Management, existing direct private URL, no credential-bearing
widget or server-side health probe. Both scripts preserve protected rollback
copies and abort on conflicting existing entries. Awaiting explicit confirmation
for applying the rule/reloading OPNsense and adding the tile/restarting only
Homepage. Validate from the Mac and retain a denied test from unapproved VLAN 20.
This does not provide public ingress, TLS, SSO or access for devices outside the
existing approved-host alias; those remain separate integration decisions.

- **2026-09-21 live state:** Paperless-ngx is deployed in LXC 115 at
  `192.168.70.14`. Its webserver container is healthy and the login endpoint
  returns HTTP 200. It runs Granian, with no dedicated nginx component.
  Milestone 1 remains open: local backups exist, but the current TrueNAS
  pull filter was corrected to include LXC 115 on September 21. No matching
  archive was present at discovery in the TrueNAS or off-site directory.
  The approved manual pull subsequently completed and the newest TrueNAS
  copy passed checksum/integrity verification and an isolated application
  restore drill. Off-site verification remains pending. See the resume
  checkpoint below. Historical proposal observations follow.
- **At proposal time, Paperless-ngx was not recorded as deployed.** Checked
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

### Resume checkpoint — 2026-09-21

Jason clarified that the request was to start the Paperless-ngx project,
not restart a service. Resume the existing combined project at Milestone 1.
No production changes or restarts were made during this discovery.

- Verified: LXC 115 running; `paperless-ngx-webserver-1` healthy;
  `paperless-ngx-broker-1` running; login HTTP 200.
- Local recovery evidence: six Proxmox archives dated September 16–21.
  The newest, `/mnt/backups/dump/vzdump-lxc-115-2026_09_21-02_44_54.tar.zst`,
  is 2,192,949,035 bytes, passes `zstd -q -t`, and has SHA-256
  `8d8ee04aee8fd1f6dbaa09cd9b3f55709af2a344438908c1e3ebbba1e55597b1`.
  Archive integrity is not yet an isolated application restore proof.
- Confirmed gap: TrueNAS rsync task 1 targets
  `/mnt/Media/backup/homelab-proxmox-guests`, runs daily at 04:00,
  has `delete=false`, and includes 100–109/111/113/114 before
  `--exclude=*`. It excludes 115. No LXC 115 archive was found there or
  via an exact-filter listing of `idrive-crypt:homelab-proxmox-guests`.
- Approved and applied on 2026-09-21 under `AGENTS.md`: preserve task 1's
  existing `extra` list, then insert only
  `--include=vzdump-lxc-115-*.tar.zst` immediately before `--exclude=*`.
  Preserve every other task field, including deletion, schedule, and
  existing guest coverage. No production service interruption expected.
  Six current archives add approximately 13.2 GB to the same-site copy;
  assess off-site capacity/version retention before relaying them.
- Validation after approval: re-read the task, confirm only that filter
  changed, run the approved pull, compare source/destination SHA-256 and
  archive integrity, then verify encrypted off-site coverage and perform
  an isolated restore before admitting real documents. Any manual remote
  job trigger remains subject to the repository confirmation rule.
- Rollback for the proposed filter change: restore the captured `extra`
  list only; preserve any copied backup archives. Never remove recovery
  copies as incidental cleanup.
- Applied: Jason approved the filter update; a fresh read after the update
  confirmed `extra` was the only changed configuration field. The initial
  request failed remote-path validation without applying the change. The
  successful retry used request-only `validate_rpath=false` because the
  restricted backup SSH account does not support the generic path probe;
  middleware source confirms this option is removed before persistence.
  Previous non-secret settings are saved at
  `/private/tmp/paperless-task1-before.json` on the operator Mac.
- Completed: approved manual TrueNAS task 1 run, job `52077`, returned
  SUCCESS. All six LXC 115 archive filenames and sizes matched Proxmox.
  The newest archive SHA-256 matched the source hash above and passed
  `zstd -q -t` independently on both hosts. Paperless remained healthy;
  login HTTP 200. Existing source backups were preserved.
- Pending: recurring schedule observation, off-site capacity/coverage,
  access/authentication and remaining
  Milestone 1 integrations. No real document contents were inspected.

### Next recovery checkpoint

Prepared [isolated restore drill](../../runbooks/Paperless-Isolated-Restore.md)
for temporary LXC 915 using the verified TrueNAS archive through the existing
read-only `/mnt/backup-relay` mount. ID 915 is unused; capacity is sufficient.
The drill disables autostart, removes networking before boot, inspects SQLite
read-only, verifies offline login/container health and removes only the
temporary guest. Jason confirmed the complete drill; it passed, including
SQLite quick_check, healthy webserver and two HTTP 200 login checks. Temporary
915 and its disk were removed, both source archives preserved, and production
115 remained healthy. The tested archive predates the reader account. A fresh
off-site exact-filter listing still returned no Paperless archives.

## Milestones

Milestone 1 is in progress; subsequent milestones remain incomplete.

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

#### Live design findings — 2026-09-21

- Deployed image labels report version `3.1.3`, revision
  `d48663e9ebaadc4b413a6ca3bc88cb5fbc4e468e`; Django `5.2.16`,
  Django REST Framework `3.17.2`. Inspected deployed source rather than
  assuming the proposal's permission model still describes this release.
- Aggregate-only query found zero documents and no `ai-paperless-reader`
  account. No document content was read. The environment-level AI enable
  setting is false; this does not establish the database override's state.
- Native `paperless_ai` includes classification and chat, with an
  OpenAI-compatible client. The inspected classifier suggests title/tags/
  correspondents; this is not evidence that it meets the project's
  restricted summary/custom-field contract. Do not enable it as a substitute
  without reviewing its complete mutation and credential boundaries.
- `PaperlessObjectPermissions` requires model-level view permission for
  GET and distinct add/change/delete permissions for mutations.
  `PermittedObjectsFilter` also restricts owned documents to ownership or
  explicit object grants. Model-level view alone does not authorize reading
  every owned document. Future ingestion must deliberately grant the reader
  view access without changing human ownership or existing permissions.
- Prepared `scripts/paperless/provision_reader.py`: defaults to dry-run;
  creates only an active, non-staff, non-superuser account with an unusable
  password and exactly `documents.view_document`. It issues no token,
  changes no document access and aborts on an incompatible existing account.
  Live dry-run through the deployed Django runtime returned `would_create`.
  Applying it requires the next explicit remote-change confirmation.
- Credential custody remains a separate design gate: keep any future token
  source-local behind a reader endpoint; do not issue or expose a token to
  the model or reuse Jason's credentials. Additional metadata permissions
  require demonstrated need. Test permitted reads and denied writes against
  synthetic fixtures before activating polling.
- Completed after Jason's explicit approval: applied the prepared account
  script in LXC 115. An independent Django query verified active=true,
  staff=false, superuser=false, unusable password, exactly
  `documents.view_document`, zero groups, zero API tokens and zero object
  grants. Paperless remained healthy and login HTTP returned 200.
  Recovery is to deactivate this dedicated account; no documents were
  touched. Credential custody, synthetic permission tests and ingestion
  access grants remain pending; account creation alone does not complete
  Milestone 2 or enable summarization.
- Backup check still found no LXC 115 archive on TrueNAS after the filter
  change; backup and restore gates remain open independently of this design.
- Read-only deployed-runtime verification using
  `scripts/paperless/verify_reader.py` passed: the document permission class
  allows GET/HEAD/OPTIONS and rejects POST/PUT/PATCH/DELETE; the note
  permission class rejects POST/DELETE. No mutation handler was invoked.
  This proves the model permission gates only, not full HTTP/token behavior
  or owned-document grants; synthetic integration tests remain pending.
- Reviewed the AI-PAM project and credential-broker README: central custody
  and the broker are still pending implementation in the recorded state;
  the historical SSH skeleton is explicitly not deployable. Do not assume
  a live token-custody integration or deploy that skeleton for Paperless.
- Backup operation approved and completed (job `52077`, SUCCESS): ran existing TrueNAS
  rsync task 1 once (`midclt call rsynctask.run 1`), preserving its configured
  scope and `delete=false`. This pulls all eligible missing/changed guest
  archives, including LXC 115, with no Paperless restart. Verify successful
  job completion, then checksum and integrity-test the copied LXC 115 archive.
  A failed copy leaves the Proxmox source intact; retain completed recovery
  copies. No manual off-site sync or restore was performed. All six files
  matched source names/sizes; the newest passed SHA-256 comparison and
  Zstandard verification. This does not yet prove application restore.

- [ ] Create a dedicated, least-privilege Paperless API token; confirm its
      actual achievable scope (read-only, ideally document-content-only)
      against Milestone 1's findings.
- [ ] Confirm connectivity from the summarization service to Paperless's
      API and to `aster-llama`, using synthetic test documents only.
- [x] Sensitive-document exclusion policy decided 2026-09-15: summarize
      everything by default, no exclusion mechanism to build.

### Milestone 3 — Summarization pipeline


#### Local prototype checkpoint — 2026-09-21


**Latest resume checkpoint — 2026-09-22:** prompt `summary-v3` allows one
sentence for short reminders and gives a factual-summary example that excludes
malicious meta-instructions. The first v2 refinement still described the
injection; v3 fixes that behavior on the tested example. After interruption,
confirmed no leftover evaluator process and reran the current code in memory
on LXC 110; no installed evaluation files or service settings were changed.
All four live synthetic cases completed in 68.53 seconds with zero failures.
Reviewed outputs retain receipt amount/date/warranty, library due date/no fine,
damaged-OCR uncertainty and only the bicycle appointment facts. Numeric account
identifiers and injection commentary are absent. Saved non-secret synthetic
results in `services/paperless-summary/evidence/2026-09-22-summary-v3.json`.
All 12 local regression tests pass; service health HTTP 200 during evaluation.
This is a small-sample quality check, not broad model robustness or load proof.

The installed evaluation files on LXC 110 still contain the earlier prompt;
use repository v3 for subsequent runs. Next integration gates remain actual
Paperless HTTP/token and owned-document permission tests using synthetic
fixtures, approved credential custody/transport, and deployment/reconciliation
work. No real documents, new credentials, production scheduler, write-back or
service restart was involved in this refinement. Off-site verification remains
deferred per Jason's direction.


Live evaluation completed after explicit approval. Added a dedicated key on
LXC 110 at `/etc/paperless-summary/llama-api-key` (root-owned 0600, parent 0700).
The original two-key file is retained at
`/etc/paperless-summary/aster-llama-api-keys.before-paperless`; its contents were
preserved exactly in the new three-key service file, with ollama ownership and
0600 mode retained. No secret value was emitted. Restarted only
`aster-llama.service`; it returned active/running with health HTTP 200.
Both prior keys and the new key returned HTTP 200 from the authenticated models
endpoint; missing and invalid keys returned 401 from chat completions.

Executed four serial synthetic requests using model
`/opt/models/qwen3.8-27b-iq4xs/Qwen3.8-27B-UD-IQ4_XS-00001-of-00002.gguf`.
All completed in 23.65 seconds, with zero failures. Review found receipt/date/
amount facts preserved, the numeric account identifier omitted, damaged OCR
uncertainty acknowledged, and the malicious instruction not followed. The last
summary unnecessarily described the injection attempt: refine the prompt to
omit meta-instructions and repeat evaluation before claiming production quality.
This small sample is not a general prompt-injection robustness proof.

Evaluation code is retained in `/etc/paperless-summary/evaluation` on LXC 110;
its temporary SQLite database was automatically deleted. No Paperless token,
document, deployment or scheduler was changed. The dedicated key remains local
to inference for testing; production credential custody/integration is pending.
Rollback copy is available; no rollback was required. Paperless login remained
HTTP 200. Off-site verification remains deliberately deferred.

Synthetic model evaluation is prepared in
`services/paperless-summary/evaluate_synthetic.py`. Four cases cover normal
facts/dates, numeric identifiers, damaged OCR and embedded malicious instructions.
It connects only to the inference host at its fixed private address, checks dedicated-key ownership and
0600 mode, performs serial requests and deletes its temporary summary database.
Model-output quality requires human/model review; success counts alone are not
a quality gate. Syntax validation passed; the approved live evaluation subsequently completed
all four cases (see results below).

Live inference discovery: LXC 110 `aster-llama.service` is active/running as
`ollama`, binary `/opt/llama.cpp-b11081/llama-server`; the API-key file is
`/etc/aster-llama-api-keys`, mode 0600, owned by ollama. No key values were read
into the session. Existing documented key enrollment requires a service restart.
The listener binds only `192.168.70.12:11435`, not loopback; its models endpoint
currently rejects unauthenticated requests (401), unlike the historical notes.

Operation explicitly approved and completed: preserved the current key file
in a protected rollback copy on LXC 110, generate a dedicated Paperless key
there, store it at `/etc/paperless-summary/llama-api-key` root-owned mode 0600
(directory 0700), append it atomically while preserving every existing key and
the service key-file ownership/mode, restart only `aster-llama.service`, verify
health and old/new-key acceptance source-locally without exposing credentials,
verify missing/invalid-key denial, then run the four synthetic evaluations.
The brief shared-service interruption affects Aster/news inference. No key
transfer to Paperless or activation of its pipeline is included. Recovery:
restore the saved key list and restart that same service if validation fails.
This source-local test-key custody is interim; central broker integration and
production summarizer custody remain pending. Existing credentials must not be
used for the new project's inference workload.

Jason asked to defer slow off-site verification and approved moving on with
synthetic pipeline development. Added `services/paperless-summary/` with a
GET-only reader, inference adapter, persisted SQLite retry state, duplicate/
changed-content detection and atomic summary publication. Twelve synthetic tests
passed, covering recovery/backoff, invalid OCR, numeric identifier redaction,
redirect/pagination boundaries and absence of a model-driven action path.

No production service, credential, document or schedule was changed. Inference
in tests is a deterministic double; actual local-model quality and full HTTP
permission tests remain unproven. The README records deployment gates, incomplete
PII handling, single-worker constraint, context-size handling and source/access
reconciliation limitations. Next: complete those local gaps and evaluate the real
local model with synthetic documents after a reviewed credential-custody path is
available. Off-site verification is deferred, not waived; real-document use stays
blocked until its gate passes. Milestone 3 is not complete.

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
| 2026-09-21 | 3 | Approved dedicated inference key enrollment and restart of LXC 110 aster-llama only. Existing keys preserved; protected rollback copy retained. Ran four synthetic cases against the deployed Qwen model. | Auth acceptance/denial checks passed; all four summaries completed in 23.65 seconds. Factual/identifier/OCR behavior acceptable for this sample; injection-summary verbosity needs refinement. Inference health and Paperless login HTTP 200. | Codex |
| 2026-09-21 | 1 | Jason confirmed the complete isolated restore drill. Restored the verified TrueNAS archive to LXC 915, removed networking before boot, checked SQLite read-only and started the application offline. | SQLite quick_check=ok; restored webserver healthy; two login HTTP 200 checks. Temporary guest/disk removed; source archives preserved; production 115 healthy. Off-site verification remains pending. | Codex |
| 2026-09-21 | 1 | Jason approved one manual run of TrueNAS task 1; job `52077` completed SUCCESS. Compared all six Paperless archive filenames/sizes and independently tested the newest archive on both hosts. | Newest SHA-256 `8d8ee04aee8fd1f6dbaa09cd9b3f55709af2a344438908c1e3ebbba1e55597b1` matched; both Zstandard checks passed. Paperless healthy, login HTTP 200. Same-site copy verified; off-site and isolated restore still pending. | Codex |
| 2026-09-21 | 2 | Jason explicitly approved creating `ai-paperless-reader`; applied `scripts/paperless/provision_reader.py` in LXC 115 and independently queried the resulting account. | Exact view-only model permission, active non-admin account, unusable password, zero groups/tokens/object grants. Webserver healthy and login HTTP 200. No document access or content changed. | Codex |
| 2026-09-21 | 1 | Jason approved adding only `--include=vzdump-lxc-115-*.tar.zst` to TrueNAS rsync task 1 before its terminal exclusion. Updated and re-read task configuration. | Only `extra` changed; enabled state, 04:00 schedule, `delete=false`, SSH credentials and existing guest coverage preserved. No manual job triggered; first copy, off-site validation and restore proof pending. | Codex |
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

- [Aster Sysadmin Second-Brain](Aster-Sysadmin-Second-Brain.md)
  (source-local reader / no-mutation-authority pattern referenced above)
- [Aster Forgejo and NetBox Read-Only Integration](Aster-Forgejo-NetBox-Read-Only.md)
- [Aster ARR Stack Manager](Aster-Arr-Stack-Manager.md)
  (execution-disabled broker precedent referenced above)
- [News Aggregator (MuckScraper) — Phase 1](News-Aggregator-MuckScraper.md)
  (dedicated least-privilege `aster-llama` key precedent)
- [Project Creation Standard](../../Project-Creation-Standard.md)
- `PROJECTS.md` — "Future Services" section, the only prior mention of
  Paperless-ngx in this repository

## iPhone access correction — 2026-09-23

Jason requested home Wi-Fi and Tailscale access. NPM host 25's original source
allowlist already included the registered administrator iPhone at 192.168.1.112,
but blocked the Tailscale subnet router's translated source, 192.168.20.20.
Added only that router address to the HTTPS allowlist. Authentik's Jason binding,
native Paperless login, backend firewall and public-source denial are unchanged.
No new VLAN route, WAN forwarding or public hostname exposure was added.

Checkpoint: /root/npm-before-paperless-iphone-20260923.sqlite on LXC 107,
SQLite integrity verified. NPM syntax passed; the router now receives the 302
sign-in redirect with verified TLS, the existing Mac still receives 302, and an
unapproved source receives 403. Physical iPhone acceptance remains with Jason.
The exact update script is scripts/paperless/enable_iphone_access.mjs.

The previously blocked operational Doctor installation and reference/wiki pushes
were subsequently approved and completed. The focused live Doctor check passed;
Forgejo reference/wiki refs are 76c2bea and c1aa96c. Neither sibling repository
has a configured GitHub push mirror. This access follow-up is recorded locally;
no additional Git push is implied by the iPhone access request.
