# Calendar Personal Assistant Project

> Status: Proposed — not yet authorized
>
> Project owner: Jason
>
> Proposed: 2026-09-15
>
> Authorization stream: not yet selected — Stream M or Stream A to be chosen
> by Jason before implementation begins

## Purpose and desired outcome

An AI-assisted layer over a real household calendar: daily/upcoming
briefings, extraction of action items and follow-ups from calendar events
(and, if in scope, related email), and a weekly digest of what's coming up.
Originally floated in brainstorming as "n8n/Node-RED + local model" — this
charter treats the workflow-engine choice as an open decision requiring
justification, not a foregone conclusion (see Architecture and design
decisions below). The desired outcome is less manual calendar review and
fewer missed follow-ups, not a new calendar application and not a system
with any ability to create, modify or delete events without Jason's review.

This is a proposal-stage charter only. No component described below has been
built, and nothing here is authorized for implementation.

## Current state and evidence

- No calendar integration (CalDAV or otherwise) exists anywhere in this
  repository today. No workflow-automation platform (n8n, Node-RED, or
  similar) exists anywhere in this lab either — a repository-wide search for
  both categories of term returned zero matches outside this document and
  its sibling [Email-Triage-Digest.md](Email-Triage-Digest.md).
- The household's actual calendar provider (iCloud Calendar, Google
  Calendar, or something else) is **not confirmed anywhere in this
  repository** and is an open discovery item, same as the sibling email
  project's mail-provider question. The Mac session's identity
  (`w58ghtwr9v@privaterelay.appleid.com`, an Apple private-relay address)
  suggests iCloud is plausible but does not confirm it.
- Shared local LLM inference already exists and is production: `aster-llama`
  (`aster-llama.service` on LXC 110, `192.168.70.12:11435`, OpenAI-compatible
  `/v1/chat/completions`, currently `unsloth/Qwen3.8-27B-GGUF:UD-IQ4_XS` via
  llama.cpp/Vulkan on an Intel Arc Pro B60 GPU, bearer-key authenticated,
  Lab VLAN 70 only). See [Aster-Operations.md](../Aster-Operations.md). Any
  local-LLM step in this project (briefing text generation, action-item
  extraction) should reuse this endpoint via a dedicated API key, matching
  the News Aggregator precedent, rather than deploying a second model.
- `aster-llama` is a **shared resource** other production workloads already
  depend on (Aster, the news aggregator's digest/language-note calls, and
  potentially the sibling Email Triage project if both are ever built).
  Concurrent load across multiple recurring AI-adjacent projects calling the
  same GPU-backed inference server is a real open question this project must
  account for, not assume away.
- This lab has **no workflow-automation platform today**, and its
  established pattern for scheduled/automated work is a plain, purpose-built
  script triggered by a systemd timer or cron job — see
  [Video-Library-Archiving](completed%20projects/Video-Library-Archiving.md)
  (GPU-accelerated downconversion, unattended Mon–Sat schedule, plain
  Python) and
  [Jellyfin-Library-Integrity-Automation.md](Jellyfin-Library-Integrity-Automation.md)
  (scheduled Sunday 3am job, plain Python checks), neither of which reached
  for a workflow engine despite being genuinely multi-step, scheduled
  pipelines. `PROJECTS.md`'s "Other Deferred Work" list explicitly names
  "New self-hosted services not required by this roadmap" as something
  requiring real justification, not a rubber stamp — n8n/Node-RED is exactly
  that category of new self-hosted service. See Architecture and design
  decisions below for the explicit build-vs-platform decision this project
  must make before implementation.
- This lab's established pattern for AI-adjacent access to a sensitive
  external system is a **source-local, least-privilege reader** that
  publishes a **sanitized, schema-validated, non-secret report**, with the
  AI/summarization component only ever reading that report. See
  [Aster-Sysadmin-Second-Brain.md](completed%20projects/Aster-Sysadmin-Second-Brain.md)
  and
  [Aster-Home-Assistant.md](completed%20projects/Aster-Home-Assistant.md).
  Calendar data is sensitive in a specific way this project must account
  for: shared/family events, other people's names and contact details in
  invites, and event locations/descriptions can reveal a lot about a
  household's routine and relationships — this needs the same data
  minimization discipline as the email project, even though a calendar
  event is typically shorter and more structured than an email body.

## Scope

- Connect to one household calendar (exact account(s)/calendar(s) TBD — see
  Open decisions) as a **read-only** client for the briefing/digest/
  action-item functions.
- Generate a daily briefing of the day's/next few days' events.
- Extract action items and follow-ups implied by event titles/descriptions
  (e.g. "prep slides for Tuesday's review", a recurring "call plumber"
  reminder) using `aster-llama`.
- Generate a weekly digest of upcoming events and open follow-ups.
- If, and only if, Jason explicitly wants write capability (e.g. creating a
  follow-up event or reminder from an extracted action item), that is a
  **separate, later decision** requiring its own risk assessment — see
  Out of scope below and the non-waivable-stop-condition-adjacent reasoning
  in Privacy and security design. Nothing in this initial proposal assumes
  write access will ever be granted.

## Out of scope / exclusions

- Creating, modifying, deleting, or accepting/declining any calendar event
  or invite. This system reads the calendar; it does not write to it in
  this proposal's scope. A future write capability (e.g. "add this action
  item as an event") is explicitly deferred to a separate project decision,
  not assumed here — matching the Aster pattern of not inferring write
  capability from a successful read-only graduation.
- Any workflow-automation platform (n8n, Node-RED, or similar) unless the
  Milestone 1 build-vs-platform decision (see Architecture and design
  decisions) concludes one is genuinely justified and Jason explicitly
  approves standing up a new self-hosted service for it.
- Any account beyond what Jason explicitly approves in scope (household-wide
  calendar coverage, including other family members' calendars or shared
  invite data involving non-household people, is not assumed).
- Any outbound notification channel (push notification service, SMS,
  auto-generated email) unless separately scoped and approved — v1 default
  is a pull-based digest/briefing page, matching the news aggregator's
  precedent, not a push mechanism (see Open decisions).
- Training or fine-tuning any model; this reuses `aster-llama` via prompting
  only.
- A second local model server of any kind.
- Public/Internet-facing exposure of the briefing/digest surface.

## Authority model

- The calendar provider (iCloud Calendar, or whichever provider is
  confirmed) is the sole authority for event existence, timing, attendees
  and content. This project never becomes a system of record for calendar
  data; it derives a transient briefing/digest view and, if extraction is
  built, a derived list of action items that references but does not
  replace the source event.
- The sanitized intermediate report (event fields extracted for
  briefing/action-item generation) is a derived artifact, not authoritative,
  bounded by an explicit retention window.
- `aster-llama`'s output (briefing text, extracted action items) is an
  automated approximation, always labeled as such — never presented as an
  authoritative restatement of calendar content, and never silently written
  back to the calendar.
- This `homelab` repository remains the authority for project scope,
  decisions and evidence.

## Architecture and design decisions

### Open decision: purpose-built script vs. workflow-automation platform

The original brainstorm floated "n8n/Node-RED + local model." This charter
treats that as an **open decision requiring justification**, not a default,
for three reasons grounded in this lab's actual precedent:

1. **No workflow-automation platform exists in this lab today** — adopting
   one would be a new category of self-hosted service, which
   `PROJECTS.md`'s "Other Deferred Work" list explicitly flags as needing
   real justification, and the lab ethos's "least privilege and minimum
   change" principle favors the narrower option absent a concrete reason to
   need more.
2. **This lab's own precedent for comparable multi-step scheduled pipelines
   is plain Python**, not a workflow engine: Video-Library-Archiving
   (GPU-accelerated multi-stage transcoding, scheduled) and
   Jellyfin-Library-Integrity-Automation (multi-check scheduled job) both
   chose a script-plus-systemd-timer design over any general automation
   platform, despite being genuinely multi-step. The News Aggregator's own
   four-stage pipeline (ingest → cluster → summarize → flag-language) is
   the closest functional analog to what this project needs (fetch → extract
   → summarize → digest) and is also plain Python chained by a shell script
   under one systemd timer — not a workflow engine.
3. **A workflow platform adds real, ongoing attack surface and maintenance
   burden** (its own web UI, its own credential store for the calendar
   connection, its own update cadence) for functionality a bounded script
   can likely provide at this project's actual scale (one household
   calendar, a daily/weekly cadence, three defined outputs: briefing,
   action items, digest).

**Recommendation for Milestone 1 to validate or overturn, not a decision
made here:** default to a small, purpose-built Python script (or a
handful of them, chained like the news aggregator's pipeline) under a
systemd timer, matching this lab's established pattern, unless Milestone 1's
discovery surfaces a concrete requirement (e.g. genuinely complex
conditional branching across many event types, or an integration surface
too broad for a bounded script to reasonably cover) that a general
automation platform would meaningfully simplify. This must be evaluated
against real requirements, not decided by the original brainstorm's framing.

### Proposed architecture (assuming the script-based default holds)

- **Compute**: a new unprivileged LXC on Lab VLAN 70, following the existing
  Aster Agent / `aster-llama` / news-aggregator convention.
- **Calendar access**: a single, narrowly-scoped read-only CalDAV connection
  (or provider-appropriate read-only API) using a dedicated app-specific
  credential — never Jason's primary account password, never shared with
  any other project or with any device's own calendar client configuration.
  Exact mechanism depends on the confirmed provider.
- **Fetch/extract stage**: a scheduled job (systemd timer) connects
  read-only, pulls upcoming/recent events, and writes a minimized,
  schema-defined local record (event title, time, location if needed for
  the briefing, a bounded description excerpt) — not a raw calendar mirror,
  and not full attendee/contact detail beyond what a briefing genuinely
  needs.
- **Briefing/action-item/digest stage**: a separate process reads the
  minimized record, calls `aster-llama` with a dedicated API key for
  briefing text and action-item extraction, and writes results to the same
  local store.
- **Surface**: an internal-only page (daily briefing, weekly digest, running
  action-item list), matching the news aggregator's pull-based digest
  precedent as the default (see Open decisions on push vs. pull).
- **Identities**: a dedicated calendar credential, a dedicated `aster-llama`
  key, and (if needed) a dedicated Authentik application entry — no shared
  credentials with any other project, including the sibling Email Triage
  project even if both are eventually built.

## Privacy and security design

- **Least privilege on the calendar itself.** Read-only access only, scoped
  to the specific calendar(s) actually needed (e.g. Jason's personal
  calendar, not every shared/family calendar by default) using a dedicated
  app-specific/OAuth-scoped credential.
- **Data minimization.** Decide explicitly what fields are extracted per
  event (title, start/end time, and how much of the location/description
  field) versus what is never extracted (full attendee list with email
  addresses, full free-text notes beyond what's needed for action-item
  extraction, any attached files). Shared/family calendar entries routinely
  contain other people's names, phone numbers or addresses in the
  location/description fields — treat that as sensitive-by-default and
  extract the minimum needed for a useful briefing, not everything
  available.
- **Third-party data in shared invites.** An event created by someone
  outside the household (e.g. a colleague's meeting invite, a child's
  school event from a shared parent calendar) may contain that other
  person's contact information. This project must not forward that
  information into `aster-llama` prompts or stored digests beyond what's
  needed for the briefing text itself, and must not treat consent for
  Jason's own calendar data as covering third parties who appear in it.
- **Retention and deletion.** Define an exact retention window for raw
  extracted event data, generated briefings/digests, and the action-item
  list. As with the email project, prefer the shortest window that still
  supports the stated use case (e.g. retain a rolling window of upcoming
  events plus recently-passed ones needed for "did I follow up on this,"
  not an indefinite calendar mirror).
- **No mutation capability in this proposal.** No create/modify/delete
  capability against the calendar is included. A future write feature (e.g.
  "convert this extracted action item into a calendar reminder with one
  click") requires its own project charter, its own risk assessment, and
  Jason's explicit approval — matching the Aster pattern of never inferring
  write capability from a successful read-only build.
- **Credential storage.** The calendar credential and the dedicated
  `aster-llama` key are stored outside Git, mode 600, on the one host that
  uses each, never logged. Apply the same discipline that caught repeated
  credential-echo incidents during the NUT project (a command echoing a
  secret in its own verification step is a real, repeated failure mode in
  this lab's history — guard against it explicitly in this project's own
  scripts and diagnostics).
- **Network policy.** Lab VLAN 70 placement, bearer-auth on any internal API
  surface, no public ingress, briefing/digest reachable only from Jason's
  approved devices.
- **Logging.** No event titles/descriptions/attendee data beyond what's
  needed for operational debugging should appear in logs; prefer logging
  event counts/timing over content.
- **Household/workflow-platform risk stacking.** If Milestone 1 does
  conclude a workflow-automation platform is genuinely justified, its own
  credential store, web UI exposure and update responsibility become
  additional privacy/security surface on top of the calendar access itself
  — that combined risk must be presented to Jason explicitly before
  proceeding, not evaluated only as "add n8n" in isolation.

## Pre-start risk assessment

- **Objective, scope, exclusions, stream**: as stated above. Recommend
  **Stream M** for Milestone 1 (provider/platform discovery, credential
  setup) given the number of open decisions and the sensitivity of calendar
  data, with a possible move to Stream A for later bounded milestones once
  the design is concrete.
- **Affected systems, users, data, network paths, systems of record**: one
  household calendar (provider TBD), a new Lab VLAN 70 LXC, the shared
  `aster-llama` endpoint, no existing HomeLab system of record modified.
- **Current versions, dependencies, known consumers**: `aster-llama` is a
  known, versioned, shared dependency; no other dependency exists yet.
- **Confidentiality and secret-handling risks**: the calendar credential and
  any cached event content (including third-party names/contact details
  appearing in shared invites) are the primary sensitive assets. A
  compromise of the new LXC would expose read access to recent/upcoming
  calendar contents (bounded by retention window) and the calendar
  credential itself.
- **Availability/integrity/privacy/recovery risks**: privacy is the
  dominant risk category, primarily around third-party data in shared
  invites (see above). Availability risk is low (a stalled briefing is an
  inconvenience). Integrity risk is low in the read-only design (no write
  path exists to corrupt the calendar). Recovery: the calendar itself needs
  no HomeLab recovery coverage; the local minimized-record store needs
  ordinary low-cost backup coverage (rebuildable by re-fetching, modulo the
  retention window).
- **Irreversible/destructive operations**: none in scope — no
  create/modify/delete calendar operation exists in this design.
- **Expected authentication/firewall/DNS/storage/external-service changes**:
  a new app-specific calendar credential (provider-side, not a HomeLab
  change), a new `aster-llama` API key, a new internal DNS name and narrow
  firewall rule for the briefing/digest UI, a new LXC in NetBox, and
  (conditionally, only if the platform decision goes that way) a brand-new
  self-hosted n8n/Node-RED service with its own exposure/credential
  footprint — which would need its own dedicated risk analysis beyond what
  this document covers, since this document assumes the script-based
  default.
- **Recovery checkpoint, rollback, abort conditions**: before any live
  calendar connection is made, confirm the read-only credential's actual
  scope with the provider (not assumed). Abort/pause condition: if the
  provider's read-only scoping is weaker than expected (e.g. an
  app-specific credential that implicitly grants write access because the
  provider doesn't support finer scoping), stop and present that gap to
  Jason before proceeding.
- **Test strategy**: use a disposable test calendar or a small set of
  synthetic test events for early pipeline testing before running against
  Jason's real calendar, to avoid processing real shared-invite data (with
  its third-party information) before the pipeline and its data-minimization
  behavior are trusted.
- **Likely service interruption**: none to any existing service; net-new,
  isolated workload.
- **Backup/Doctor/monitoring/NetBox/wiki/documentation impacts**: see the
  Required integration impact checklist below.
- **Unresolved decisions requiring Jason's acceptance before work starts**:
  1. **Purpose-built script vs. workflow-automation platform** — see
     Architecture and design decisions above; this is the single biggest
     open decision in this charter.
  2. **Which calendar(s) are in scope** — Jason's personal calendar only,
     or shared/family calendars too? Each additional shared calendar likely
     increases third-party data exposure (other people's names/contact
     details in invites they created).
  3. **Actual calendar provider and protocol** — iCloud Calendar via CalDAV
     is plausible given the session's Apple private-relay identity but is
     not confirmed anywhere in this repository.
  4. **How the calendar credential is stored/scoped**, and whether the
     provider genuinely supports read-only access or only an app password
     with implicit write scope.
  5. **Push vs. pull output** for the briefing/digest — default assumption
     is pull (a page Jason visits), matching the news aggregator's
     precedent; a push mechanism (notification, auto-email) is a new
     outbound capability requiring its own review.
  6. **Whether action-item extraction should ever write anything back**
     (e.g. a follow-up event/reminder) — this proposal assumes no, ever,
     without a separate future project.
  7. **`aster-llama` concurrent-load impact**, especially if both this
     project and the sibling Email Triage project are eventually built and
     run on overlapping schedules.
  8. **Exact retention window** for cached event data, briefings and the
     action-item list.

## Persistence plan

- This document and its evidence log are the durable checkpoint. Before any
  live calendar connection is made, the confirmed provider, platform
  decision, credential scope and retention window must be recorded here.
- Any partial/in-progress fetch or extraction state must be resumable
  without re-processing already-handled events and without presenting a
  half-updated briefing as current.
- No calendar credential, raw event content, or `aster-llama` key is ever
  persisted in this repository or in any resume note.

## Milestones

### Milestone 1 — Discovery and design decisions

- [ ] Confirm the real calendar provider and protocol with Jason.
- [ ] Confirm calendar scope: personal only, or shared/family calendars too.
- [ ] Resolve the purpose-built-script-vs-workflow-platform decision with a
      concrete requirements-based justification, not the original
      brainstorm's framing alone.
- [ ] Confirm what credential/scoping mechanism the provider actually
      supports for read-only access; document its real limitations.
- [ ] Decide push vs. pull output for the briefing/digest.
- [ ] Decide whether any future write capability is even wanted in
      principle (does not authorize building it now).
- [ ] Decide the exact data-minimization policy for event fields,
      especially third-party data in shared invites.
- [ ] Decide the exact retention window for cached event data, briefings
      and action items.
- [ ] Assess `aster-llama` concurrent-load impact, accounting for the
      sibling Email Triage project if it exists at the same time.
- [ ] Choose placement (Lab VLAN 70 LXC, matching existing convention) and
      record IP/NetBox plan.

Completion gate: every open decision above has Jason's explicit answer
recorded in this document before any live calendar connection is attempted.

### Milestone 2 — Read-only fetch pipeline (test data first)

- [ ] Build the minimized-record schema for calendar events.
- [ ] Implement the read-only fetch stage against a disposable test
      calendar or synthetic test events before touching Jason's real
      calendar.
- [ ] Validate the credential is genuinely read-only where the provider's
      API allows testing this safely.
- [ ] Validate against the real calendar with real events once the
      pipeline is trusted, checking specifically for third-party data
      handling in any shared/multi-attendee events.

Completion gate: the fetch stage reliably produces a minimized record from
real calendar data with confirmed read-only behavior and no unminimized
third-party data retained beyond what the Milestone 1 policy allows.

### Milestone 3 — Briefing, action items and digest

- [ ] Wire the minimized record to `aster-llama` via a dedicated API key.
- [ ] Implement the daily briefing generator.
- [ ] Implement action-item/follow-up extraction.
- [ ] Implement the weekly digest.
- [ ] Validate output against a representative sample of real events and
      hand-check for accuracy and any unwanted third-party data surfacing
      in generated text.
- [ ] Re-verify `aster-llama` shared-load behavior under this project's
      real request pattern.

Completion gate: briefing/digest/action-item output is accurate and useful
on real calendar data, and the shared inference endpoint shows no measurable
degradation to Aster or the news aggregator during this project's runs.

### Milestone 4 — Surface and hardening

- [ ] Build the internal-only briefing/digest page (or push mechanism, per
      the Milestone 1 decision).
- [ ] Confirm no public exposure; confirm the narrow firewall/DNS path.
- [ ] Implement and verify the retention/deletion policy on schedule.
- [ ] Add HomeLab Doctor coverage.
- [ ] Add backup coverage for the minimized-record store and configuration.

Completion gate: the surface is reachable only from approved devices, the
retention policy is proven, and Doctor/backup coverage exist.

### Milestone 5 — Validation and graduation

- [ ] Complete the Required integration impact checklist below for real.
- [ ] Run a security/privacy review pass specifically checking for
      third-party data leakage into logs, Git, or `aster-llama` prompts
      beyond what was explicitly decided.
- [ ] Two independent production-path validation passes on real calendar
      data, reviewed by Jason for briefing/action-item quality and any
      privacy surprise.
- [ ] Record final architecture, accepted limitations and close out.

Completion gate: all prior gates pass, Jason has reviewed real output and
accepted its quality/privacy posture, and no unresolved secret or
scope-creep item remains (including no undocumented drift toward a write
capability).

## Validation and evaluation plan

- **Functional**: briefing and digest content checked against the real
  calendar for a representative period for completeness (no missed events)
  and accuracy (no hallucinated events or times); action-item extraction
  checked for reasonable precision (not flooding Jason with false
  positives) and recall (not silently missing an obvious action item).
- **Security**: confirm the calendar credential cannot mutate the calendar;
  confirm no event content (especially third-party attendee/contact data)
  appears in logs or Git; confirm the surface is unreachable outside the
  approved device set.
- **Failure/adversarial**: test a malformed/unusual event (all-day,
  recurring with exceptions, multi-timezone), an empty calendar, a
  provider auth failure, and an `aster-llama` outage — the pipeline must
  fail safe (no update, visible stale-state indicator) rather than crash or
  silently show incorrect stale data as current.
- **Regression**: verify Aster's and the news aggregator's own behavior are
  unaffected by this project's `aster-llama` calls under realistic
  concurrent load, including alongside the sibling Email Triage project if
  both exist.
- **Restart/interrupted-run behavior**: verify a killed mid-run fetch or
  extraction job resumes cleanly without duplicate action items or
  double-processed events.
- **Privacy**: verify the retention window is enforced by re-checking the
  data store after the window elapses in a test run; specifically verify
  third-party data from shared invites does not persist beyond the same
  window as the rest of the event record.

## Observability and maintenance

- HomeLab Doctor check: fetch-pipeline freshness, briefing/digest generation
  success, surface health — following the news aggregator's
  `check_news_aggregator()` pattern.
- No new alerting surface beyond the existing Doctor failure-only alerting
  convention.
- Maintenance: periodic review of action-item extraction quality; periodic
  confirmation the calendar credential has not been revoked/expired.
- If a workflow-automation platform is ever adopted per the Milestone 1
  decision, it inherits its own ongoing update/patch responsibility as a
  new self-hosted service — record that ownership explicitly rather than
  leaving it implicit.

## Backup, restore and rollback

- The minimized-record store and configuration are protected by the
  standard whole-guest Proxmox daily snapshot once deployed on its own LXC,
  matching the news aggregator's precedent.
- The calendar itself is not this project's data to back up; it remains
  under the provider's own retention/backup.
- Rollback path: disable the fetch timer and/or revoke the app-specific
  calendar credential at the provider to immediately stop all calendar
  access; the briefing/digest/action-item store can be deleted without
  affecting the calendar.

## Documentation and systems-of-record updates — Required integration impact checklist

- [ ] **HomeLab Doctor** — add a check for fetch-pipeline freshness and
      briefing/digest generation health, following the
      `check_news_aggregator()` pattern. Not yet implemented — nothing is
      built.
- [ ] **Monitoring/alerting** — covered by the Doctor check above; no
      separate alerting surface anticipated for a single-user internal
      tool.
- [ ] **Backup and recovery** — whole-guest Proxmox snapshot once deployed;
      no separate credential backup (calendar credential and `aster-llama`
      key are regenerable, not backed up).
- [ ] **NetBox** — add the new LXC as a VM record once deployed, following
      the news-aggregator LXC 114 precedent.
- [ ] **Human wiki** — likely **not applicable**: personal, ephemeral
      briefing/digest content, not reference documentation. Revisit if a
      genuinely reusable operational lesson emerges during implementation.
- [ ] **Aster mirror/snapshot** — **not applicable**; this project does not
      touch Aster's own knowledge base or function set, and calendar
      content must never enter Aster's corpus.
- [ ] **Operational reference and runbooks** — add an inline "Operations
      quick reference" section to this document at graduation, matching the
      news aggregator's pattern.
- [ ] **Repository documentation** — this document and the portfolio table
      (updated by others per this task's instructions) are the current
      documentation.
- [ ] **Diagrams/rack records** — **not applicable**; a VM-only deployment
      with no physical topology change.
- [ ] **Homepage/service discovery** — add a tile once the surface exists
      and is confirmed working; no credentials embedded in the tile config.
- [ ] **Authentication/authorization** — decide at implementation time
      whether the surface needs Authentik or a narrow network ACL is
      sufficient, following the news aggregator's own reasoning.
- [ ] **DNS, certificates and firewall** — add an internal-only DNS name and
      the narrowest possible firewall rule once built; no WAN/OPNsense
      exposure. If a workflow-automation platform is adopted, its own
      admin UI exposure needs the same narrow-scoping analysis, done
      separately and explicitly.
- [ ] **Automation and schedules** — a systemd timer for the fetch/
      briefing/digest pipeline (or the workflow platform's own scheduler, if
      that path is chosen), with documented missed-run behavior.
- [ ] **Security inventory** — record the calendar credential's storage
      location and scope, and the dedicated `aster-llama` key's storage
      location, once created; both outside Git, mode 600. If a workflow
      platform is adopted, its own credential store becomes part of this
      inventory too.

## Graduation criteria

The project graduates when: the confirmed provider/scope/platform/retention
decisions are implemented as designed; the fetch pipeline is proven
read-only; briefing/action-item/digest quality is validated by Jason against
real calendar data; the surface is internal-only and access-controlled;
Doctor/backup/NetBox coverage exist; the retention policy is proven; no
credential or third-party event content has leaked into Git, logs, or
Aster's knowledge base; and no undocumented drift toward a calendar-write
capability occurred.

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
- [News Aggregator (MuckScraper)](completed%20projects/News-Aggregator-MuckScraper.md) — `aster-llama` dedicated-key pattern, VLAN 70 placement, pipeline-under-one-timer precedent
- [News Aggregator Phase 2 — Digest, Sections and Rebrand](completed%20projects/News-Aggregator-Digest-and-Sections.md) — digest-page precedent
- [Video Library Archiving](completed%20projects/Video-Library-Archiving.md) — plain-script-over-workflow-platform precedent
- [Jellyfin Library Integrity Automation](Jellyfin-Library-Integrity-Automation.md) — plain-script-over-workflow-platform precedent
- [PROJECTS.md](../../PROJECTS.md) — "Other Deferred Work" (new self-hosted services require justification)
- [Email Triage/Summarization Digest](Email-Triage-Digest.md) — sibling proposal, same session
