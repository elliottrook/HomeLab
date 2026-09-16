# Email Triage/Summarization Digest Project

> Status: Proposed — not yet authorized
>
> Project owner: Jason
>
> Proposed: 2026-09-15
>
> Authorization stream: not yet selected — Stream M or Stream A to be chosen
> by Jason before implementation begins

## Purpose and desired outcome

An AI-generated triage/summary of incoming household email: a private digest
that groups messages by rough priority (e.g. needs action / informational /
low priority), summarizes each in one or two lines, and surfaces anything
that looks time-sensitive — so Jason can decide what to actually open instead
of reading every message in the inbox. The desired outcome is a faster,
lower-noise way to triage a real mailbox, not an email client replacement,
not an auto-responder, and not a system with any ability to send, delete or
file mail on Jason's behalf.

This is a proposal-stage charter only. No component described below has been
built, and nothing here is authorized for implementation.

## Current state and evidence

- No email integration of any kind exists anywhere in this repository today.
  A repository-wide search for IMAP, CalDAV and related mail-access terms
  returned zero matches outside this document and its sibling
  [Calendar-Personal-Assistant.md](Calendar-Personal-Assistant.md).
- The Mac session this document was drafted in is authenticated as
  `w58ghtwr9v@privaterelay.appleid.com` — an Apple private-relay address,
  which tells us the *user-facing* account uses Apple's mail relay
  infrastructure but tells us nothing definitive about the household's real
  mailbox provider or protocol. Whether the actual inbox to be triaged is
  iCloud Mail (IMAP with an app-specific password), Gmail/Google Workspace,
  or something else entirely is an **open discovery item**, not yet confirmed
  anywhere in this repository. Do not assume a provider before Jason confirms
  one.
- Shared local LLM inference already exists and is production: `aster-llama`
  (`aster-llama.service` on LXC 110, `192.168.70.12:11435`, OpenAI-compatible
  `/v1/chat/completions`, currently `unsloth/Qwen3.8-27B-GGUF:UD-IQ4_XS` via
  llama.cpp/Vulkan on an Intel Arc Pro B60 GPU, bearer-key authenticated,
  reachable only from Lab VLAN 70). See
  [Aster-Operations.md](../Aster-Operations.md). This project should reuse
  that endpoint for summarization rather than standing up a second model —
  the same pattern the News Aggregator (MuckScraper) and its Phase 2 digest
  already established with their own dedicated `aster-llama` API key. See
  [News-Aggregator-MuckScraper.md](completed%20projects/News-Aggregator-MuckScraper.md)
  and
  [News-Aggregator-Digest-and-Sections.md](completed%20projects/News-Aggregator-Digest-and-Sections.md).
- `aster-llama` is a **shared resource** other Aster/AI projects already
  depend on (Aster itself, the news aggregator's digest and per-story
  language-note calls). Adding a recurring email-triage workload is a real
  open question about concurrent load and queueing behavior on one shared
  GPU-backed inference server, not something to assume away — see Pre-start
  risk assessment below.
- This lab's established pattern for AI-adjacent access to a sensitive
  external system is a **source-local, least-privilege reader** that
  publishes a **sanitized, schema-validated, non-secret report**, with the
  AI/summarization component only ever reading that report — never holding
  the source credential or contacting the source system directly. See
  [Aster-Sysadmin-Second-Brain.md](completed%20projects/Aster-Sysadmin-Second-Brain.md)
  (Milestone 5, the `/var/lib/aster/health` report pattern) and
  [Aster-Home-Assistant.md](completed%20projects/Aster-Home-Assistant.md)
  (the strict, aggregate-only report schema). Email content is materially
  more sensitive than either system's health telemetry — personal
  correspondence, financial/medical references, other people's data in
  message bodies and attachments — so this project must apply that pattern
  more strictly, not more loosely.

## Scope

- Connect to one household mailbox (exact account(s) TBD — see Open
  decisions) as a **read-only** client.
- Fetch new/unread messages on a schedule, extract headers and body text
  needed for triage.
- Classify each message into a small fixed set of priority buckets and
  generate a short (one-to-two sentence) summary via `aster-llama`.
- Flag messages that look time-sensitive (e.g. contain a deadline, an
  explicit request, or urgency language) for prominent placement in the
  digest.
- Present the result as a private, internal-only digest (page and/or
  scheduled output — see Open decisions on push vs. pull).
- Retain only what is needed to render the current digest and a short
  rolling history; define and enforce an explicit deletion/retention window
  for any cached message content or summary.

## Out of scope / exclusions

- Sending, replying to, forwarding, deleting, archiving, moving, labeling or
  otherwise mutating any message or mailbox state. This system reads mail; it
  never writes to the mailbox.
- Any auto-response, auto-reply, or drafting of outgoing email.
- Any workflow-automation platform (n8n, Node-RED, or similar) — this
  project introduces exactly one new access category (mailbox read access)
  and should be scoped as a small, purpose-built reader/summarizer, not a
  general automation platform. See
  [PROJECTS.md](../../PROJECTS.md)'s "Other Deferred Work" list, which
  explicitly names "New self-hosted services not required by this roadmap"
  as requiring real justification.
- Attachments beyond what is strictly needed to note their presence (e.g. "1
  attachment: invoice.pdf") — no attachment content extraction, OCR, or
  storage in v1 unless a specific need is identified and separately scoped.
- Any account beyond what Jason explicitly approves in scope (see Open
  decisions — household-wide inbox coverage is not assumed).
- Training or fine-tuning any model; this reuses `aster-llama` via prompting
  only, matching the News Aggregator precedent.
- A second local model server of any kind.
- Public/Internet-facing exposure of the digest or the mail-reading
  component.

## Authority model

- The mailbox provider (iCloud Mail, or whichever provider is confirmed) is
  the sole authority for message existence, content and read/unread state.
  This project never becomes a system of record for email; it derives a
  transient triage view.
- The sanitized intermediate report (headers, extracted text, classification
  inputs) is a derived artifact, not authoritative, and is bounded by an
  explicit retention window (see Privacy and security design).
- `aster-llama`'s output (summary text, priority label) is an automated
  approximation, always labeled as such in the digest UI — never presented as
  a factual restatement of the message.
- This `homelab` repository remains the authority for project scope,
  decisions and evidence, per the Project Creation Standard's authority
  model.

## Architecture and data flows

Proposed, not yet built or confirmed:

- **Compute**: a new unprivileged LXC on Lab VLAN 70, following the existing
  Aster Agent / `aster-llama` / news-aggregator convention (own IP in the
  `192.168.70.x` range, bearer-authenticated where it exposes any API,
  `192.168.70.0/24`-only reachability by default).
- **Mail access**: a single, narrowly-scoped read-only IMAP connection (or
  provider-appropriate read-only API) using a dedicated app-specific
  credential — never the account's primary password, and never a credential
  shared with any other project or with Jason's own mail client
  configuration. Exact mechanism depends on the confirmed provider (see Open
  decisions).
- **Fetch/extract stage**: a scheduled job (systemd timer, matching this
  repo's existing pattern — see the news aggregator's hourly timer) connects
  read-only, pulls new message headers/bodies, and writes a local,
  minimized, schema-defined record — not a raw mailbox mirror. This stage
  is the "source-local, least-privilege reader" in the Aster pattern above.
- **Triage/summarize stage**: a separate process reads only the minimized
  record (never raw MIME/attachment blobs), calls `aster-llama` at
  `http://192.168.70.12:11435/v1` with a dedicated API key (matching the
  news aggregator's `--api-key-file` multi-key pattern — never Aster's own
  key, never a shared key), and writes the priority label and summary back
  to the same local store.
- **Digest surface**: an internal-only page/service on the same LXC (or
  folded into an existing internal tool, TBD) rendering the current digest.
  No public exposure; reachable only from Jason's approved devices, likely
  via the same `MGMT_ADMIN_HOSTS`-precedented narrow firewall rule the news
  aggregator used, or DNS-only internal reachability if broader household
  access is ever in scope (unlikely — see Open decisions on single-user vs.
  household scope).
- **Identities**: a dedicated mail credential, a dedicated `aster-llama` key,
  and (if the digest needs its own auth) a dedicated Authentik application
  entry — no shared credentials with any other project, matching every prior
  project's stated credential-isolation pattern in this repository.

## Privacy and security design

This is the most important section of this charter given the sensitivity of
the data involved. Email is unusually sensitive: it routinely contains other
people's personal data (senders, cc'd parties, forwarded content), financial
and account information, medical references, and household-private
correspondence that was never intended for automated processing.

- **Least privilege on the mailbox itself.** Read-only access only. Use the
  narrowest scope the provider allows (e.g. a single IMAP folder if
  triage only needs Inbox, not every folder) and a dedicated
  app-specific/OAuth-scoped credential rather than the account's primary
  password, matching the lab's existing credential-isolation convention (see
  [Jellyfin-Library-Integrity-Automation.md](Jellyfin-Library-Integrity-Automation.md)'s
  credential-storage pattern, cited as precedent by the news aggregator).
- **Data minimization before the model ever sees anything.** Decide,
  explicitly and before implementation, what is extracted from a message at
  all (likely: subject, sender, date, a truncated/plain-text body extract)
  versus what never leaves the fetch stage (attachment binary content, full
  HTML with tracking pixels/remote images, long quoted-reply chains beyond
  the newest message). The summarization prompt sent to `aster-llama` should
  receive the minimum text needed to produce a useful triage summary, not
  the raw message.
- **Redaction is an open design question, not an afterthought.** Whether
  any pattern-based redaction (e.g. obvious account/SSN-like number
  patterns) should run before text reaches `aster-llama` needs an explicit
  decision — `aster-llama` is a shared local resource with no external
  network exposure, which lowers but does not eliminate the risk of
  sensitive content passing through a shared inference process also used by
  other projects.
- **Retention and deletion are first-class, not implicit.** Define an exact
  retention window for: raw extracted message text, the generated
  summary/priority label, and any digest history. Shorter is more aligned
  with "maximum practical privacy" — e.g. retain only long enough to render
  the current and immediately prior digest, then delete the extracted body
  text while keeping the (much smaller, less sensitive) summary and
  priority label for a longer rolling history if a history view is wanted.
  This must be a specific, documented number, not "indefinitely" by default.
- **No mutation capability, ever, without a separate project.** This system
  never authenticates with write scope to the mailbox. If a future project
  wants to propose one-click archive/delete/label actions from the digest,
  that is new scope requiring its own charter, its own risk assessment, and
  Jason's explicit approval — it is not assumed here, matching the
  established Aster pattern of "no write capability is proposed for
  graduation" (see
  [Aster-Sysadmin-Second-Brain.md](completed%20projects/Aster-Sysadmin-Second-Brain.md)).
- **Credential storage.** The mail credential and the dedicated
  `aster-llama` key are stored outside Git, mode 600, on the one host that
  uses each, never logged, never echoed by any diagnostic command (this
  repository's own credential-rotation incidents during the NUT project are
  the cautionary precedent — see `CLAUDE.md`'s NUT section — a command
  echoing a secret is a real, repeated failure mode to guard against
  explicitly in this project's own scripts).
- **Network policy.** Lab VLAN 70 placement, bearer-auth on any internal API
  surface, no public ingress, digest reachable only from Jason's approved
  devices.
- **Logging.** Application logs must not contain message body text, subject
  lines beyond what's needed for operational debugging, or the mail
  credential. Prefer logging message IDs/counts/timing over content.
- **Household scope.** Whether this covers only Jason's mail or other family
  members' mailboxes is an explicit open decision (see below) — the default
  assumption for this proposal is Jason's mailbox only, since that is the
  minimum needed to validate the concept and each additional mailbox is a
  proportional increase in blast radius and consent complexity (other
  people's mail contains other people's correspondents' data too).

## Pre-start risk assessment

- **Objective, scope, exclusions, stream**: as stated above. Stream not yet
  selected — recommend **Stream M** for at least Milestone 1 (mail-provider
  discovery and credential setup) given the sensitivity and the number of
  still-open decisions, with a possible move to Stream A for later bounded
  milestones once the design is concrete and Jason has reviewed it.
- **Affected systems, users, data, network paths, systems of record**: one
  household mailbox (provider TBD), a new Lab VLAN 70 LXC, the shared
  `aster-llama` endpoint, no existing HomeLab system of record is modified.
- **Current versions, dependencies, known consumers**: `aster-llama` is a
  known, versioned, shared dependency (see Aster-Operations.md); no other
  dependency exists yet since nothing is built.
- **Confidentiality and secret-handling risks**: the mail credential and any
  cached message content are the primary sensitive assets. A compromise of
  the new LXC would expose read access to the mailbox's recent contents
  (bounded by the retention window) and the mail credential itself. This is
  a materially higher-value target than any other Lab VLAN 70 workload
  deployed so far (news aggregator, Aster) since none of those hold
  personal-correspondence-grade data.
- **Availability/integrity/privacy/recovery risks**: privacy is the
  dominant risk category here (see Privacy and security design above).
  Availability risk is low (a stalled digest is an inconvenience, not an
  outage of anything else). Integrity risk is low (read-only access cannot
  corrupt the mailbox). Recovery: the mailbox itself needs no HomeLab
  recovery coverage (it's not this lab's data); the local minimized
  record/digest store should have ordinary config-level backup coverage
  proportional to its low replacement cost (it can be rebuilt by re-fetching
  from the mailbox, modulo the retention window already having expired
  content).
- **Irreversible/destructive operations**: none are in scope. No delete,
  send, or mutating mail operation exists in this design.
- **Expected authentication/firewall/DNS/storage/external-service changes**:
  a new app-specific mail credential (created at the provider, not a HomeLab
  change), a new `aster-llama` API key (same mechanism as the news
  aggregator's), a new internal DNS name and a narrow firewall rule for the
  digest UI (same `MGMT_ADMIN_HOSTS` pattern as precedent), a new LXC in
  NetBox.
- **Recovery checkpoint, rollback, abort conditions**: before any live mail
  connection is made, confirm the read-only credential's actual scope with
  the provider (not just assumed from documentation) and test against a
  disposable/test approach if one is available. Abort/pause condition: if
  the provider's read-only scoping turns out to be weaker than expected
  (e.g. an app-specific password that provides implicit send/delete access
  because the provider doesn't support finer scoping), stop and present that
  gap to Jason before proceeding — do not accept broader-than-intended
  mailbox access silently.
- **Test strategy**: use a disposable test mailbox or a small set of
  synthetic/labelled test messages sent to the real mailbox for early
  pipeline testing where possible, to avoid triaging real sensitive mail
  before the pipeline is trusted. Real-mail validation should still happen
  before graduation, since synthetic messages won't fully exercise real
  formatting/encoding variety.
- **Likely service interruption**: none to any existing service; this is a
  net-new, isolated workload.
- **Backup/Doctor/monitoring/NetBox/wiki/documentation impacts**: see the
  Required integration impact checklist below.
- **Unresolved decisions requiring Jason's acceptance before work starts**:
  1. **Which mailbox(es) are in scope** — Jason's only, or the whole
     household? (Default assumption above: Jason's only, pending
     confirmation.)
  2. **Actual mail provider and protocol** — iCloud Mail via IMAP with an
     app-specific password is the most likely candidate given the
     `@privaterelay.appleid.com` session identity, but this is not
     confirmed anywhere in this repository and must be verified with Jason
     directly, not assumed.
  3. **How the mail credential is stored/scoped** — confirm the provider
     actually supports a read-only or narrowly-scoped credential; if it only
     offers a full-access app password, that materially changes the risk
     profile and needs an explicit accepted-risk decision, not a silent
     assumption of "read-only" that isn't actually enforced by the provider.
  4. **Push vs. pull output** — does Jason want the digest delivered (e.g.
     a push notification or a separate summary email) or does he pull it
     (visiting a dashboard/digest page, as the news aggregator's digest
     already works)? A push design that itself sends email or notifications
     adds a new outbound capability and its own review; pull-only (a page
     Jason visits) is the narrower default and mirrors the news aggregator's
     precedent.
  5. **Redaction policy** before content reaches `aster-llama` — decide
     whether any pattern-based scrubbing runs first, or whether the shared
     local-only nature of `aster-llama` is judged sufficient on its own.
  6. **Concurrent load on `aster-llama`** — this project would add a new
     recurring caller to a GPU-backed inference server other production
     workloads (Aster, the news aggregator) already depend on. A capacity/
     contention check (e.g. worst-case summarization batch size and timing)
     should happen before this is treated as a free add-on, not assumed
     away because the endpoint already exists.
  7. **Exact retention window** for cached message text vs. summaries.

## Persistence plan

- This document and its evidence log are the durable checkpoint. Before any
  live mail connection is made, the confirmed provider, credential scope,
  and retention window decisions must be recorded here.
- Any partial/in-progress state (e.g. a fetch job that has processed some
  messages but not others) must be resumable without re-processing already
  triaged messages and without leaving a half-written digest visible to
  Jason as if it were current.
- No mail credential, raw message content, or `aster-llama` key is ever
  persisted in this repository or in any resume note.

## Milestones

### Milestone 1 — Discovery and design decisions

- [ ] Confirm the real mail provider and protocol with Jason (do not assume
      iCloud Mail).
- [ ] Confirm mailbox scope: Jason only, or household-wide.
- [ ] Confirm what credential/scoping mechanism the provider actually
      supports for read-only access; document its real limitations.
- [ ] Decide push vs. pull digest delivery.
- [ ] Decide the exact data-minimization and redaction policy before
      `aster-llama` calls.
- [ ] Decide the exact retention window for raw extracted content vs.
      summaries.
- [ ] Assess `aster-llama` concurrent-load impact and record an accepted
      approach (e.g. off-peak scheduling, request batching, or an accepted
      "best effort, low priority" queuing behavior).
- [ ] Choose placement (Lab VLAN 70 LXC, matching existing convention) and
      record IP/NetBox plan.

Completion gate: every open decision above has Jason's explicit answer
recorded in this document before any live mailbox connection is attempted.

### Milestone 2 — Read-only fetch pipeline (test data first)

- [ ] Build the minimized-record schema (headers, extracted text fields,
      explicit non-inclusion of attachment content).
- [ ] Implement the read-only fetch stage against a disposable test mailbox
      or synthetic/labelled test messages before touching real mail.
- [ ] Validate the credential is genuinely read-only (attempt a mutating
      operation in a disposable context and confirm it is rejected, if the
      provider's API allows testing this safely).
- [ ] Validate against the real mailbox with real (but low-risk) messages
      once the pipeline is trusted.

Completion gate: the fetch stage reliably produces a minimized record from
real mail with no attachment content, no credential leakage in logs, and
confirmed read-only behavior.

### Milestone 3 — Triage and summarization

- [ ] Wire the minimized record to `aster-llama` via a dedicated API key
      (never Aster's own key, never the news aggregator's key).
- [ ] Implement priority classification and summary generation.
- [ ] Implement the time-sensitivity flag.
- [ ] Validate summaries against a range of real message types (short,
      long, multi-quote-chain, non-English if applicable, etc.) and
      hand-check output quality and factual accuracy.
- [ ] Re-verify `aster-llama` shared-load behavior under this project's
      real request pattern, not just the Milestone 1 estimate.

Completion gate: triage output is accurate and useful on a representative
sample of real mail, and the shared inference endpoint shows no measurable
degradation to Aster or the news aggregator during this project's batch
runs.

### Milestone 4 — Digest surface and hardening

- [ ] Build the internal-only digest page (or push mechanism, per the
      Milestone 1 decision).
- [ ] Confirm no public exposure; confirm the narrow firewall/DNS path
      matches the `MGMT_ADMIN_HOSTS` precedent or an equivalently narrow
      scope.
- [ ] Implement and verify the retention/deletion policy actually deletes
      what it says it deletes, on schedule.
- [ ] Add HomeLab Doctor coverage.
- [ ] Add backup coverage for the minimized-record store and any
      configuration.

Completion gate: the digest is reachable only from approved devices, the
retention policy is proven (not just documented), and Doctor/backup coverage
exist.

### Milestone 5 — Validation and graduation

- [ ] Complete the Required integration impact checklist below for real.
- [ ] Run a security/privacy review pass specifically checking for
      sensitive-data leakage into logs, Git, or `aster-llama` prompts beyond
      what was explicitly decided.
- [ ] Two independent production-path validation passes on real mail,
      reviewed by Jason for triage quality and any privacy surprise.
- [ ] Record final architecture, accepted limitations and close out.

Completion gate: all prior gates pass, Jason has reviewed real digest output
and accepted its quality/privacy posture, and no unresolved secret or
scope-creep item remains.

## Validation and evaluation plan

- **Functional**: triage priority and summaries are checked against a
  human-labeled sample of real messages for reasonable agreement — not
  perfect classification, but no dangerous misses (e.g. a genuinely
  time-sensitive message silently landing in "low priority").
- **Security**: confirm the mail credential cannot mutate the mailbox;
  confirm no message content appears in logs or Git; confirm the digest is
  unreachable from outside the approved device set.
- **Failure/adversarial**: test a malformed message (broken MIME, unusual
  encoding), an empty mailbox, a provider auth failure, and an
  `aster-llama` outage — the pipeline must fail safe (no digest update, a
  visible stale-state indicator) rather than crash or produce a
  misleading/empty summary presented as current.
- **Regression**: verify Aster's and the news aggregator's own latency/
  behavior are unaffected by this project's `aster-llama` calls under
  realistic concurrent load.
- **Restart/interrupted-run behavior**: verify a killed mid-run fetch or
  triage job resumes cleanly without re-processing or double-counting
  messages.
- **Privacy**: verify the retention window is enforced by re-checking the
  data store after the window elapses in a test run.

## Observability and maintenance

- HomeLab Doctor check: fetch-pipeline freshness (last successful fetch
  within an expected window), triage/summarization success rate, digest
  service health — following the news aggregator's `check_news_aggregator()`
  pattern.
- No new alerting surface beyond the existing Doctor failure-only alerting
  convention, consistent with other single-user internal tools in this
  repository.
- Maintenance: periodic review of classification quality; periodic
  confirmation the mail credential has not been revoked/expired by the
  provider.

## Backup, restore and rollback

- The minimized-record store and any configuration are protected by the
  standard whole-guest Proxmox daily snapshot once deployed on its own LXC,
  matching the news aggregator's precedent (no separate config-level backup
  needed if everything lives in the guest's own filesystem).
- The mailbox itself is not this project's data to back up — it remains
  under the provider's own retention/backup, and this project must not
  become a substitute for that.
- Rollback path: disable the fetch timer and/or revoke the app-specific mail
  credential at the provider to immediately stop all mailbox access; the
  digest and minimized-record store can be deleted without affecting the
  mailbox.

## Documentation and systems-of-record updates — Required integration impact checklist

- [ ] **HomeLab Doctor** — add a check for fetch-pipeline freshness and
      digest-service health, following the `check_news_aggregator()`
      pattern. Not yet implemented — nothing is built.
- [ ] **Monitoring/alerting** — covered by the Doctor check above; no
      separate alerting surface anticipated for a single-user internal tool.
- [ ] **Backup and recovery** — whole-guest Proxmox snapshot once deployed,
      per the news aggregator precedent; no separate credential backup (the
      mail credential and `aster-llama` key are regenerable, not backed up,
      matching this repo's convention of not backing up regenerable
      secrets).
- [ ] **NetBox** — add the new LXC as a VM record once deployed (id, VLAN 70
      interface, IP), following the news-aggregator LXC 114 precedent.
- [ ] **Human wiki** — likely **not applicable**: this project's output is
      personal, ephemeral triage content, not reference documentation or
      operator-facing knowledge, matching the news aggregator's own
      assessment. Revisit if a genuinely reusable operational lesson emerges
      during implementation.
- [ ] **Aster mirror/snapshot** — **not applicable**; this project does not
      touch Aster's own knowledge base or function set, and message content
      must never enter Aster's corpus.
- [ ] **Operational reference and runbooks** — add an inline "Operations
      quick reference" section to this document at graduation (restart,
      credential rotation, log locations), matching the news aggregator's
      pattern, rather than a separate runbook file.
- [ ] **Repository documentation** — this document and the portfolio table
      (updated by others per this task's instructions) are the current
      documentation.
- [ ] **Diagrams/rack records** — **not applicable**; a VM-only deployment
      with no physical topology change, matching the news aggregator and
      Aster wiki precedent.
- [ ] **Homepage/service discovery** — add a tile once the digest UI exists
      and is confirmed working, following the news aggregator's Homepage
      addition pattern; no credentials embedded in the tile config.
- [ ] **Authentication/authorization** — decide at implementation time
      whether the digest needs Authentik in front of it or whether a narrow
      `MGMT_ADMIN_HOSTS`-style network ACL is sufficient, following the news
      aggregator's own reasoning (Authentik only needed when reachable by
      hostname from a broader client set than the ACL already restricts to).
- [ ] **DNS, certificates and firewall** — add an internal-only DNS name and
      the narrowest possible firewall rule for the digest UI once built; no
      WAN/OPNsense exposure.
- [ ] **Automation and schedules** — a systemd timer for the fetch/triage
      pipeline, with documented missed-run behavior (e.g.
      `Persistent=true`), matching the news aggregator's timer convention.
- [ ] **Security inventory** — record the mail credential's storage location
      and scope, and the dedicated `aster-llama` key's storage location,
      once created; both outside Git, mode 600.

## Graduation criteria

The project graduates when: the confirmed provider/scope/retention decisions
are implemented as designed (not weakened along the way); the fetch pipeline
is proven read-only; triage/summarization quality is validated by Jason
against real mail; the digest is internal-only and access-controlled;
Doctor/backup/NetBox coverage exist; the retention policy is proven to
actually delete what it claims; and no credential or message content has
leaked into Git, logs, or Aster's knowledge base.

## Evidence log

No implementation work has occurred; this document is the initial proposal.

## Close-out

Not applicable — project has not started.

## References

- [Project Creation Standard](../Project-Creation-Standard.md)
- [Project portfolio](README.md)
- [Aster Operations](../Aster-Operations.md) — `aster-llama` endpoint detail
- [Aster Sysadmin Second-Brain](completed%20projects/Aster-Sysadmin-Second-Brain.md) — source-local reader / sanitized report pattern
- [Aster Home Assistant Advisor](completed%20projects/Aster-Home-Assistant.md) — strict report schema precedent
- [News Aggregator (MuckScraper)](completed%20projects/News-Aggregator-MuckScraper.md) — `aster-llama` dedicated-key pattern, VLAN 70 placement precedent
- [News Aggregator Phase 2 — Digest, Sections and Rebrand](completed%20projects/News-Aggregator-Digest-and-Sections.md) — digest-page precedent
- [PROJECTS.md](../../PROJECTS.md) — "Other Deferred Work" (new self-hosted services require justification)
- [Calendar Personal Assistant](Calendar-Personal-Assistant.md) — sibling proposal, same session
