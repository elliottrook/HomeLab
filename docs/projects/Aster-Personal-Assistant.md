# Aster Personal Assistant

> Status: Active — M0 discovery; risk assessment and decisions D1–D7 accepted 2026-09-23
>
> Owner: Jason | Proposed: 2026-09-23 | Stream M — Monitored (accepted
> 2026-09-23)
>
> Supersedes: [Email triage digest](Email-Triage-Digest.md),
> [Calendar personal assistant](Calendar-Personal-Assistant.md) and
> [Combined morning digest](Combined-Morning-Digest.md) (all proposed, never
> started). Also absorbs the "web access for research" direction deferred by
> [Aster Companion App](completed%20projects/Aster-Companion-App.md).

## Purpose and desired outcome

Pivot Aster, whose local B60-backed inference is now fast enough for daily
use, toward being Jason's personal assistant:

- **Email:** read and analyze Jason's iCloud mail — what needs action, what is
  time-sensitive, what can wait.
- **Calendar:** digest iCloud calendars into a daily agenda, conflicts, prep
  needed and follow-ups.
- **Guidance through the day:** a morning check-in plus a small number of
  timely, opt-in nudges delivered through the Companion App.
- **Scheduled web research:** Jason queues a question ("research the best X"),
  Aster researches it overnight and reports cited findings in the morning
  check-in.
- **Photography competitions:** for a competition Jason names, Aster turns
  its rules into a checklist, searches Jason's Immich library, analyzes
  candidate photographs, recommends entries with reasons, and prepares
  correctly sized files for Jason to approve. Jason submits them himself.

It is **additive**: Sysadmin, Media Automation and Home Assistant personas
and their existing tools stay as they are. Jason confirmed (2026-09-23) this
adds **three new personas**, **Personal Assistant**, **Researcher** and
**Photography Assistant** (added the same day, same project), plus a new set
of isolated workers.

Two design requirements from Jason (2026-09-23) shape everything below:

1. **Multi-person from day one.** Jason only at launch, but the data model,
   credentials, storage, delivery and consent are per-person so family members
   can be added later without redesign.
2. **Evolve under set restrictions.** Start with read and analyze only. The
   system must include a governed way to later earn narrow write abilities —
   eventually basic email sending and appointment creation — only through
   training, evidence and explicit promotion, never by default.

## Current state and evidence

- **Aster** (LXC 104, `192.168.70.10`, Lab VLAN 70) serves the Companion App
  (`aster.elliottrook.com/companion`, Authentik passkey-only login) with
  per-persona tool sets enforced server-side, including a regression that
  blocks unsolicited model tool calls ([Aster-Operations.md](../reference/Aster-Operations.md),
  Companion M4).
- **Inference:** `aster-llama` on LXC 110 (`192.168.70.12:11435`), shared by
  Aster, Your News and Companion speech. Per-consumer bearer keys are the
  established pattern.
- **Delivery:** Companion notifications are deployed as a pilot. They use
  generic Apple Web Push with generic lock-screen text by default, so Apple
  sees delivery metadata only (Companion M8).
- **News:** Your News (LXC 114) produces a twice-daily digest and Piper audio
  at 05:15/17:15 `Etc/GMT+7`. It becomes the news section of the morning
  check-in and is not rebuilt.
- **Speech:** LXC 116 already provides STT/TTS for spoken check-ins.
- **AI-PAM** defines Green/Yellow/Red/Black risk classes and a probation
  ladder, but central custody is not deployed yet (M1 pending). This project
  aligns with those classes and must not presume the broker exists.
- **No email, calendar or general web-egress integration exists** in the lab.
  Aster guests currently have no general Internet egress. The only added
  outbound path documented is Speech → NPM for Authentik JWKS (rule
  `bc811346-6714-44b4-bc65-46e7430f46a8`).
- **Provider confirmed by Jason, 2026-09-23:** iCloud for mail and calendar.

### Key discovered constraint: iCloud credentials are not scope-limited

iCloud offers third-party access only through **app-specific passwords**.
Based on Apple's documented model, to be re-verified in M0: an app-specific
password is not limited to one service or to read-only. The same password
authenticates to IMAP (read, move, delete), SMTP (send) and CalDAV/CardDAV
(read and write) for the whole Apple ID. It can be revoked individually but
cannot be narrowed.

So "read-only" cannot be enforced by the provider for mail. It must be
enforced by *where the credential lives* and *what code can use it*. Calendar
has a better option. See Architecture and Pre-start risk assessment R1. This
is an unanticipated trade-off against the lab's least-privilege standard, and
it needs Jason's explicit decision before any credential is created.

## Scope and exclusions

### In scope

- iCloud mail read and analysis for Jason (Inbox plus explicitly chosen
  folders): triage buckets, one-line summaries, time-sensitive flags and
  suggested next steps shown as text only.
- iCloud calendar read and analysis: agenda, conflicts, travel/prep time,
  follow-ups, and cross-referencing mail with calendar inside the private
  zone.
- Morning check-in: calendar, mail, overnight research and the existing news
  digest, delivered in the Companion App, optionally spoken.
- Daytime guidance: a small opt-in set of nudges, for example "leave in 20
  minutes" or "reply needed today", with generic lock-screen text.
- A research queue: topics created only by an authenticated person in the
  Companion App, researched overnight by an isolated worker with web egress,
  and reported with citations.
- Three Companion personas: **Personal Assistant** (mail, calendar,
  check-in), **Researcher** (research queue and reports; no personal data)
  and **Photography Assistant** (competition rules, Immich library analysis,
  entry recommendations and formatted entries).
- Photography: read-only Immich access through a vetted community Immich
  MCP server with a permission-limited API key. The Researcher fetches
  competition rules and turns them into a **rules card** that Jason confirms.
  Candidates are pre-filtered with Immich smart search, analyzed by a local
  vision model and formatted into entry files (resolution and file size, as
  the rules require) for Jason's approval. The nightly job runs 02:30–03:30.
- A multi-person model: principal identity, per-person credentials, storage,
  retention, delivery and consent.
- The **capability ladder** and policy mechanism (see below). It is built and
  tested in this project. Every capability graduates at **L1 (Observe)**
  except `photo.format`, which graduates at **L2 (Draft)**. Jason asked for
  prepared entry files, and those files never leave the lab without him.

### Explicit exclusions (for this project's graduation)

- Sending, replying, forwarding, moving, flagging, deleting or marking-read any
  mail. Creating, editing, accepting or declining any calendar event. Each is
  a later capability-ladder promotion with its own risk assessment.
- Onboarding any person other than Jason. The design supports it; doing it is
  a separate per-person decision.
- Contacts (CardDAV), iMessage, Reminders, Notes, iCloud Drive, Apple
  Photos, Health, finance or any other data source. Immich is the only photo
  source.
- **Luminar Neo integration.** Luminar has no public API, scripting interface
  or MCP server (M0 finding F5), and driving its GUI on the Mac is rejected.
  Jason's Luminar edits reach Aster only as files he has exported into Immich.
- Writing to Immich: uploading, editing, deleting, favouriting, tagging or
  creating albums. A "shortlist album" write is a later ladder promotion.
- Submitting competition entries, creating competition accounts or paying
  entry fees. Jason submits. An emailed entry could later use `mail.send`.
- Creative or generative image edits of any kind, including AI enhancement,
  sky or background replacement. Formatting is limited to deterministic
  resize, file-size/quality, colour-space conversion and metadata handling.
- Research topics derived automatically from mail or calendar content.
- Research that logs in, submits forms, buys anything, downloads executables
  or uses any credential.
- Attachment content extraction or OCR. Document OCR remains its own project.
- Any public ingress, new public DNS, or model fine-tuning. "Training" here
  means prompts, examples, reviewed preferences and evaluation sets, not
  weight updates.
- A workflow-automation platform (n8n, Node-RED). Plain services and systemd
  timers follow the lab's precedent.
- Changes to Sysadmin/Media/HA personas, ARR execution or Lab Doctor
  execution.

## Authority model

| Fact | Authority | This project's role |
|---|---|---|
| Messages, events, read/unread state | iCloud | Read-only derived views; never a system of record |
| Minimized records, summaries, briefings | Personal-data store on the PA guest | Derived, retention-bounded, rebuildable from iCloud |
| Research findings | Cited external sources | Report is an approximation; every claim links its source |
| Who may use what capability at what level | `config/assistant-policy.yaml` in this repository (reviewed, committed) | Runtime enforces it; the model cannot change it |
| Principals and their enrolment | Authentik users plus policy file | Enrolment requires the person's own consent |
| Photographs, albums, people, EXIF | Immich (main Synology) | Read-only derived analysis; never modifies the library |
| Competition rules | The competition's published rules | The rules card is derived; Jason's confirmation is required before use |
| Project scope, decisions, evidence | This document | — |

Model output is always labelled as automated interpretation, never as a
restatement of the source.

## Architecture and data flows

The central rule: **no model context and no process ever holds private
personal data and an open Internet path at the same time.**

```text
                 ┌───────────── Personal-data zone (no web) ─────────────┐
iCloud IMAP/  ◄──┤ PA readers (per principal)                            │
CalDAV (egress   │   mail-reader: EXAMINE + BODY.PEEK only               │
 allowlisted)    │   cal-reader:  PROPFIND/REPORT only                   │
                 │ → minimized store → analyzer (aster-llama, own key)   │
                 └───────────────┬───────────────────────────────────────┘
                                 │ sanitized per-principal summaries (read-only API)
                                 ▼
 Companion ◄──── Aster (LXC 104) — PA + Researcher personas / composer
  (Authentik)      no web tool, no send tool, no credentials
                                 ▲
                                 │ research reports (untrusted text, cited)
                 ┌───────────────┴──────── Research zone (no personal data) ┐
Jason-typed ────►│ research queue → research worker → SearXNG → web (GET)  │
 topics only     │   via egress proxy; aster-llama with its own key        │
                 └─────────────────────────────────────────────────────────┘
```

### Components (proposed, M0 to confirm placement and IPs)

1. **PA guest** (new unprivileged LXC on Lab VLAN 70, NetBox-assigned IP):
   - `mail-reader`: holds the per-principal iCloud app-specific password
     (mode 600, dedicated system user, never on Aster's guest). The code opens
     mailboxes with IMAP `EXAMINE`, which is read-only at the protocol level,
     and fetches with `BODY.PEEK` so nothing is marked read. The IMAP client
     wrapper allowlists commands, so `STORE`, `COPY`, `MOVE`, `EXPUNGE`,
     `APPEND` and SMTP are absent, not just unused. It extracts a minimized
     record: sender, date, subject, a plain-text excerpt of the newest part,
     and attachment names/count only.
   - `cal-reader`: see calendar-access decision D2. The preferred path uses a
     separate **assistant Apple ID** with **view-only** shares, so
     read-only is enforced by iCloud itself.
   - `analyzer`: turns minimized records into triage, summaries and flags via
     `aster-llama` with a dedicated key. It treats all message text as
     untrusted data inside a delimited prompt and has no tools.
   - Store: SQLite per principal, schema-versioned, with retention jobs.
     Exposes a narrow **read-only, per-principal** HTTP API to Aster only
     (bearer key plus source-IP firewall).
   - Egress: iCloud mail/CalDAV endpoints and `aster-llama` only, through a
     hostname-allowlisted forward proxy (iCloud uses Apple CDN addresses, so
     IP rules alone are impractical; M0 to decide between proxy and OPNsense
     FQDN alias).
   - `photo-worker` (Photography Assistant back end, same private zone, no
     web): runs the vetted **Immich MCP server** locally with a
     per-principal Immich API key (see Photography design). It pre-filters
     with Immich smart search and metadata, sends preview-size images to the
     local vision model, and writes the formatted entry files and
     recommendations to the per-principal store. Aster's persona reaches it
     only through the PA API, so Aster never holds the Immich key.
2. **Research guest** (new unprivileged LXC on Lab VLAN 70, separate from
   the PA guest):
   - SearXNG (self-hosted metasearch; no search-API account; queries leave
     from the lab's public IP without a personal identity).
   - `research-worker`: pulls topics from its queue, searches, fetches pages
     read-only (GET only, no cookies or credentials, size, time and type
     limits, HTML converted to text, no JavaScript execution), and writes a
     structured report with citations via `aster-llama` using its own key.
   - The only broad egress in the design: outbound 443 (and 80 if M0 shows
     it is needed) via a logging egress proxy. No inbound from the Internet.
     No route to the PA guest, Management VLAN 50 or other VLANs beyond
     `aster-llama` and the proxy.
   - Queue writes come from the Companion App on behalf of an authenticated
     person, never from model output.
3. **Aster** (existing LXC 104):
   - New **Personal Assistant** persona with read tools over the PA API (the
     current principal's data only) and read access to finished research
     reports (as untrusted, cited text).
   - New **Researcher** persona: add, reprioritize and cancel queue topics,
     check job status, and discuss finished reports. It has **no** PA tools
     and no personal data. It never fetches the web itself; the research
     worker does that on its schedule.
   - **Server-enforced mutual exclusion:** no persona or chat may enable a PA
     tool and any web/fetch tool together. Aster has no web tool at all in
     this design; live interactive web browsing is excluded.
   - The briefing composer runs on a timer and pushes a generic notification
     ("Your morning check-in is ready"). Content is visible only after
     Companion login.
4. **Companion App:** check-in view, research-queue entry, nudge
   preferences, per-capability "why am I seeing this" and feedback (useful /
   wrong / don't do this again) that feeds the training record.

### Photography design

- **Rules card:** the Researcher fetches a competition's published rules
  (web zone) and extracts a structured card. The card records:
  - category and entry limits;
  - deadline;
  - date-taken window;
  - resolution (long edge / pixel dimensions);
  - maximum file size, format and colour space;
  - metadata requirements;
  - editing rules and model-release requirements.
  Rules are untrusted text and the extraction may be wrong, so
  **Jason confirms each card before it can be used**. The card is stored
  with the source URL and retrieval date.
- **Jason's standing editing rules** (2026-09-23; competitions vary, and the
  stricter of these and the card applies):
  - **no AI** editing or generation;
  - **sky replacement allowed only when the replacement sky is Jason's own
    photograph**;
  - **no border** on entries.
  Aster cannot reliably detect AI or sky edits from pixels, so those are
  handled as **flags plus attestation**:
  - Aster flags editing-software metadata (for example Luminar in EXIF)
    and any card rule it cannot verify;
  - Jason attests "no AI; sky source mine if replaced" when approving each
    entry.
  Borders are checkable. The formatter never adds one, and Aster flags any
  source whose edges look like an added frame or matte (uniform edge band).
- **Selection:** Immich smart search and metadata narrow the library to a
  shortlist. The vision model scores the shortlist against the card and the
  category theme (composition, subject, technical quality, fit), and each
  recommendation carries its reasons and any rule risks.
- **Formatting ("use Immich to format", 2026-09-23):** the Immich original,
  or Jason's Luminar export already in Immich, is the only source. Luminar
  is not involved. A deterministic formatter (libvips/Pillow class, chosen
  in M1) only:
  - resizes to the card's resolution;
  - meets the maximum file size by adjusting encoder quality;
  - converts colour space;
  - strips GPS/location and other metadata unless the card requires it.
  It never crops, retouches, composites or adds a border. Outputs are drafts in Companion
  (L2) for Jason to download, approve and submit.
- **Schedule (D11):** nightly 02:30–03:30 `Etc/GMT+7`. The job starts
  **only after the 02:30 Proxmox backup job has finished** (it ran
  02:30–02:46 on 2026-09-23) and stops at 03:30, carrying unfinished work
  to the next night. Interactive requests during the day use the same
  worker at chat priority.
- **Immich key permissions (read-only):** `asset.read`, `asset.view`,
  `asset.download`, `album.read`, `person.read`, `tag.read`,
  `server.about`, confirmed against Immich 2.7.5's permission list in M1.
  No upload, update, delete, album-write or shared-link permissions. The key
  enforces read-only even if the MCP server exposes write tools; those tools
  are also disabled or allowlisted out.
- **Privacy:** the library holds family faces, children and locations.
  Location data is stripped from outputs by default. Photos with
  identifiable people are flagged for the competition's model-release rules,
  and children are always flagged. Each person's key sees only that
  person's library.

### Multi-person design

- **Principal** = an Authentik user. Every record, credential, key, job and
  notification is tagged with exactly one principal. Every API call is
  scoped by the authenticated principal, so no cross-principal read path
  exists. This is enforced and tested, not assumed.
- Each person uses **their own** Apple ID, their own app-specific password
  (or their own view-only calendar share), their own retention settings and
  their own capability levels.
- Shared calendars and family events appear only through each person's own
  view. The household view is a later explicit feature, not a side effect.
- Enrolment requires the person's own consent in the Companion App, recorded
  in the policy file. Removal revokes their credential, deletes their store
  and is verified.
- Minors: no one under 18 is enrolled without a documented guardian decision
  and a tighter default policy. This is decided per person at enrolment.
- Capacity: each principal adds analyzer load on the shared GPU. Enrolment
  includes a capacity check.

### Capability ladder (the evolution mechanism)

Each capability is set per principal, for example `mail.read`,
`calendar.read`, `mail.draft`, `mail.send`, `calendar.create`,
`photo.read`, `photo.format`, `photo.album.write`,
`research.run`.

| Level | Name | What it means | AI-PAM class |
|---|---|---|---|
| L0 | Off | Not available | — |
| L1 | Observe | Read, analyze, summarize, suggest in words | Green |
| L2 | Draft | Prepares an exact draft (email text, event) shown only in Companion; nothing leaves the lab | Green |
| L3 | Propose and confirm | A separate narrow executor performs one exact action after the person approves it with a passkey in Companion; shows recipient/time/body and an undo where possible | Yellow |
| L4 | Bounded autonomy | Acts without per-action approval inside a written policy (e.g. accept holds from own devices; templated reply to allowlisted recipients), rate-limited, logged, undo window, daily digest of actions taken | Yellow/Red per policy |
| — | Never | Submitting competition entries or paying fees, deleting or editing Immich assets, generative image edits, deleting mail, forwarding outside allowlist, account/security settings, payments, passwords, anything in AI-PAM Black | Black |

**Rules that make it safe to evolve:**

- Levels live in the committed policy file. Aster cannot modify it, and
  a change is a Git commit Jason approves. The runtime refuses any action
  above the recorded level.
- **Promotion needs evidence**, recorded in this document's evidence log:
  - a minimum observation period at the level below;
  - quality metrics (e.g. share of L2 drafts accepted unedited) and zero
    policy violations;
  - a passed prompt-injection red-team suite for that capability, using
    adversarial synthetic emails and events;
  - a per-capability risk assessment; and
  - Jason's explicit approval.
  Thresholds are set in the capability's own assessment. Promotion is one
  level at a time.
- **Demotion is automatic** on any violation, injection detection or
  anomaly (rate, new recipient, off-hours burst), with notification to the
  person. A per-person and global **kill switch** drops everything to L0/L1
  immediately.
- **Write executors are separate from readers.** Send/create credentials,
  once they exist, live in a distinct executor that accepts only structured,
  approved action records, never free-form model output. Sending from an
  assistant-owned address rather than the person's own is an option to
  evaluate when `mail.send` is proposed.
- The L3/L4 design for mail sending must specifically address exfiltration:
  recipient allowlists, no attachments, content diffing against the
  approved draft, and no action triggered by an inbound message's
  instructions.
- **Training** = curated per-person examples, feedback from Companion,
  reviewed preference notes (plain text, principal-scoped, never in Aster's
  shared corpus) and a growing evaluation set. All of it is versioned and
  reversible.

## Privacy and security design

- **Separation (the primary control):** personal-data zone and research zone
  run on different guests, keys and network paths. Aster sees only sanitized
  summaries plus untrusted research text, with no egress tool. Fetched web
  content cannot reach a process that holds mail. Mail content cannot reach a
  process that can make arbitrary outbound requests.
- **Prompt injection is expected, not hypothetical.** Anyone can email Jason,
  and any web page can carry instructions. Controls: untrusted text is
  delimited and labelled; analyzer and research worker have no tools; Aster's
  assistant persona has read-only tools only; suggestions are text, never
  actions; red-team fixtures are part of every gate.
- **Credential custody:** per-principal app-specific password only on the PA
  guest, dedicated service user, mode 600, never logged or echoed. Scripts
  must not print secrets; this repeats the NUT-project lesson. AI-PAM
  custody is adopted when it exists, and until then this project records the
  custody location and rotation procedure itself. Revocation is available at
  appleid.apple.com as a human break-glass path.
- **Data minimization:** newest message part only, plain text, truncated;
  no remote images or tracking; attachment names only. Calendar: title,
  time, location, a bounded notes excerpt; attendee names only where needed.
- **Retention (D5, accepted 2026-09-23):** raw extracted mail text
  **24 hours**; summaries and triage **15 days**; research reports
  **60 days**. Derived defaults that follow those choices: check-ins 15 days
  (they contain summaries); calendar extracts rolling window (−7 to +60
  days); research fetched page text 7 days (never longer than the report). Deletion is verified by test, not just
  configured.
- **Logs:** IDs, counts, timings and error classes only. No subjects, bodies,
  addresses, event titles or research page content.
- **Notifications:** generic lock-screen text by default. Push payloads carry
  no personal content, because Apple Web Push metadata already leaves the
  lab.
- **Search privacy:** SearXNG avoids an account-linked search API. Research
  topics are still visible to upstream engines, so the queue UI warns
  against putting personal details in topics.
- **Network:** no inbound Internet path. Research egress is the only broad
  outbound rule in the lab for an AI guest. It is a **non-waivable
  stop-condition change** and requires Jason's explicit approval at M4
  whatever the stream.

## Pre-start risk assessment

| # | Risk | Likelihood / impact | Controls | Residual |
|---|---|---|---|---|
| R1 | iCloud app-specific password grants full mail send/delete and calendar write | Certain (provider design) / High if PA guest compromised | Credential only on PA guest, command-allowlisted client, no SMTP code, egress allowlist, revocable per password; calendar via view-only share (D2) | A PA-guest root compromise could use full mailbox rights. **Accepted by Jason 2026-09-23 (D1).** |
| R2 | Prompt injection via email or web content steers Aster | High / Medium at L1 (misleading advice), High at L3+ | Zone separation, tool-less analyzers, read-only persona, delimited untrusted text, red-team gates, write levels deferred | Misleading summaries remain possible; always labelled as interpretation |
| R3 | Data exfiltration through research egress | Medium / High | Research zone holds no personal data; topics only from people; no path PA→research | Low |
| R4 | New broad egress from an AI guest | Certain / Medium | Separate guest, proxy with logging, no route to PA/Mgmt/other VLANs, M4 explicit approval | Accepted only at M4 |
| R5 | Cross-principal leak once family is added | Low / High | Principal scoping in every layer, deny tests, per-person stores | Low |
| R6 | Shared `aster-llama` contention (overnight research vs 02:30 Proxmox backup, news 05:15, interactive use) | Medium / Low–Medium | Scheduling window, queue priority for interactive chat, capacity test at M2/M4 | Measured, not assumed |
| R7 | Stale or wrong guidance presented as current | Medium / Medium | Freshness stamps, fail-visible stale state, Doctor freshness checks | Low |
| R8 | Sensitive personal data in backups | Certain / Medium | Store is derived and short-lived; excluded from backups (D6) | Low |
| R9 | Scope creep toward writes | Medium / High | Capability ladder, committed policy, graduation at L1 (L2 for `photo.format`) | Low |
| R10 | Read access to the family photo library on the primary Synology | Certain / High if PA guest compromised | Permission-limited read-only Immich key, key only on PA guest, narrow VLAN 70 → Immich firewall path, per-principal keys | Accepted with D8 |
| R11 | Third-party Immich MCP server (supply chain, extra write tools) | Medium / Medium | Pin a reviewed release, disable/allowlist tools, read-only key, no web egress from PA guest | Low |
| R12 | Vision model change affects shared `aster-llama` consumers | Medium / Medium | M0 evaluation of both options with measured VRAM/latency; rollback to current text model | Decided at D10 |
| R13 | Misread rules or an undetectable edit breach disqualifies an entry | Medium / Medium | Jason-confirmed rules card, conservative formatting, flags plus attestation, Jason submits | Low |

**Irreversible operations:** none in scope. Mail and calendar are read-only;
the local store is rebuildable.

**Rollback per milestone:** stop timers; revoke the app-specific password
at appleid.apple.com; remove calendar shares; disable the Personal Assistant and
Researcher persona flags; remove research egress rule; destroy or restore the new LXCs from the
pre-change snapshot. Existing Aster personas are unaffected throughout.

**Test strategy:** synthetic, labelled mail and calendar fixtures first,
including adversarial injection messages. Real mail comes only after the
reader is proven read-only. A disposable test Apple ID is used (D3).

### Decisions recorded (Jason, 2026-09-23)

| # | Decision | Outcome |
|---|---|---|
| D1 | Full-power iCloud app-specific password on an isolated reader, read-only enforced in code | **Accepted** (R1 residual risk accepted) |
| D2 | Calendar access | **Dedicated assistant Apple ID with view-only calendar shares.** Jason creates the account and owns its 2FA (human step) |
| D3 | Disposable test Apple ID for synthetic testing | **Approved.** Jason creates it (human step) |
| D4 | Stream | **Stream M.** Conversion of later bounded milestones to Stream A may be revisited after M1; M4 egress rule stays an explicit decision regardless |
| D5 | Retention | **Raw mail text 24 h / summaries 15 days / research reports 60 days** |
| D6 | Backups of the PA store | **Excluded** (store is derived and rebuildable from iCloud); policy, code and guest config still covered |
| D7 | Timing | **Research window 22:00–02:00 `Etc/GMT+7`**, ending 30 min before the 02:30 Proxmox backup; morning check-in 06:00 `Etc/GMT+7` (proposed, not objected to) |
| — | Personas | **Three new personas: Personal Assistant, Researcher and Photography Assistant**, added alongside existing ones, in this one project |
| D8 | Photography source and formatting | **Immich only; format from Immich originals/exports.** Luminar is not integrated (no API) |
| D9 | Immich connection | **Vetted community Immich MCP server** with a permission-limited read-only key, run on the PA guest |
| D10 | Vision model | **M0 evaluates both** options (vision projector on the current model vs a separate small vision model used only in the photo window) before Jason chooses |
| D11 | Photo schedule | **02:30–03:30**, starting after the Proxmox backup finishes |
| D12 | Editing rules | **No AI; sky replacement only with Jason's own sky image; no border.** ("No background" clarified by Jason 2026-09-23 as no border.) Competitions vary; the stricter of these and the rules card applies. Formatting is mostly resolution and file size |

## Persistence plan

- This document is the durable checkpoint: current milestone, decisions,
  evidence, next safe action, rollback location.
- Jobs are idempotent by message UID/UIDVALIDITY and event ETag. Research
  jobs have durable states (`queued/running/done/failed`) with bounded
  retries and locks. Partial check-ins are never shown as current.
- No credential, message content, event content or research text in Git,
  resume notes or model-visible logs.
- On resume: re-read the Project Creation Standard, this document, Git
  status and live state; verify prior evidence before continuing.

## Milestones

### M0 — Discovery and decisions (read-only)

- [x] Re-verify iCloud app-specific password scope against current Apple
      documentation. (2026-09-23, see M0 findings F1.) `EXAMINE`/`BODY.PEEK`
      are standard IMAP (RFC 3501/9051) read-only semantics; proven live
      against the test Apple ID in M1.
- [ ] Verify view-only calendar sharing to a second Apple ID behaves as
      read-only over CalDAV. Design accepted; live proof moved to M1 once
      the assistant Apple ID exists.
- [x] Measure `aster-llama` headroom across the proposed windows.
      (2026-09-23, F2.)
- [x] Choose guest placement and IPs. (2026-09-23, F3; NetBox
      reservation happens at M1 creation.)
- [ ] Egress mechanism: Jason to choose between the F4 options before M1's
      PA egress rule.
- [ ] Vision evaluation (D10): check whether the deployed Qwen3.8 family has
      a compatible vision projector for llama.cpp; measure VRAM headroom on
      the B60 and latency for both options; recommend one to Jason.
- [ ] Immich MCP vetting (D9): shortlist maintained servers, review code
      and tool list, confirm they honour a limited API key, and choose a
      pinned release.
- [ ] Confirm Immich 2.7.5's exact API-key permission names and the Immich
      endpoint/port the PA guest will reach.
- [ ] Jason creates the read-only Immich API key in Immich (human step;
      never pasted into chat, Git or this document).

#### M0 findings (2026-09-23, read-only)

- **F1 — iCloud credentials.** Apple's app-specific password article
  (support.apple.com/102654) grants access to "mail, contacts, and
  calendars" with no documented read-only or per-service scoping. Up to 25
  can be active and each is revocable individually. **Changing or resetting
  the Apple Account password revokes all of them**, so Doctor must report an
  auth failure distinctly ("credential revoked") rather than as generic
  staleness. Apple also documents a newer "authorize the app using your
  Apple Account" path for supported third-party apps (support.apple.com/121539,
  revocable under Sign-In and Security → Account Data Sharing). Its scopes,
  and whether a self-hosted client can use it, are undocumented, so it is
  not usable today. It is recorded as a follow-up: if it ever offers
  per-service or read-only scopes, it would narrow R1. Community iCloud
  integrations likewise report one app-specific password working across
  IMAP, SMTP, CalDAV and CardDAV. R1 stands as accepted.
- **F2 — `aster-llama` capacity.** Live on LXC 110: single slot (`-np 1`),
  **8,192-token context**, decode ≈ **5.4 tokens/s**; short-prompt prefill
  13–16 tokens/s (larger prompts prefill faster; documented 55–390 tokens/s
  depending on size). The last 7 days show a steady background of roughly
  190–330 requests/hour (mostly short news-aggregator calls) with peaks at
  the 05:15/17:15 local digests. Journal hours are UTC; the lab is
  `Etc/GMT+7`. The **22:00–02:00 local research window (05:00–09:00 UTC)
  is among the quietest hours observed.** Consequences for the design:
  - Everything user-facing is **precomputed**. The check-in is composed
    before 06:00 rather than generated on demand. Interactive answers read
    stored summaries.
  - Email analysis runs one message per request with short outputs
    (≈25 s/message estimated). The worker processes messages one at a time
    so a waiting interactive chat is delayed by at most one message.
  - The 8K context caps any single call. The research worker must
    summarize page chunks, then synthesize. Estimated ≈15 minutes per topic,
    so plan **3–5 topics per night** with a hard stop at 02:00 and the
    remainder carried over.
  - Budgets are measured again at M2/M4 against real load.
- **F3 — Placement.** Lab VLAN 70 in use: .10 (104 Aster), .12 (110
  inference), .13 (114 news), .14 (116 speech), **.15 (115 Paperless-ngx,
  newly present)**. Proposed: PA guest `192.168.70.16`, research guest
  `192.168.70.17`, next free LXC IDs at creation. Confirm free in NetBox
  before use.
- **F4 — Egress options (Jason to choose; firewall change under Stream M):**
  - **(a) Dedicated egress-proxy LXC** (recommended). OPNsense lets only the
    proxy reach WAN. The proxy allows the PA guest to reach iCloud hostnames
    only (`imap.mail.me.com:993`, `caldav.icloud.com` and its
    `*-caldav.icloud.com` partition redirects) and the research guest to
    reach general 443. It is one logged choke point, and a compromised PA
    or research guest cannot widen its own egress. Cost: one more small
    guest.
  - **(b) OPNsense FQDN aliases.** The PA guest gets direct egress to
    resolved iCloud hostnames and the research guest gets 443 via a
    per-guest rule. No new guest, but Apple's CDN addresses rotate (alias
    refresh lag, possible over-breadth) and there is no per-request logging
    for research.
  - **(c) Proxy on each guest.** Rejected: a compromised guest controls its
    own proxy, so it provides no enforcement.
- [x] Record D1–D7 answers. (2026-09-23, see Decisions recorded.)
- [ ] Jason creates the assistant Apple ID and the disposable test Apple ID
      (human step; no credentials enter chat, Git or this document).

Gate: every decision recorded; Jason accepts the risk assessment and stream.

- **F5 — Photography (2026-09-23, read-only).**
  - **Immich 2.7.5** runs on the main Synology (`photos.elliottrook.com`).
    Immich (1.138+) supports permission-scoped API keys, `asset.read`
    covers search including smart search, and community MCP servers exist,
    including ones with a read-only profile.
  - **Luminar Neo** has no public API, scripting or MCP server, official or
    community.
  - **Vision:** `aster-llama` runs the text-only
    `Qwen3.8-27B-UD-IQ4_XS` with no vision projector loaded, so image
    analysis needs a model change (D10).
  - **Backup overlap:** the nightly Proxmox backup ran 02:30–02:46 on
    2026-09-23 (one sample; Proxmox host time is PDT, matching
    `Etc/GMT+7`).

### M1 — Principal model and read-only readers (synthetic first)

- [ ] PA guest, principal model, per-principal store and schema.
- [ ] `mail-reader` with command allowlist; `cal-reader` per D2.
- [ ] Prove read-only: allowlist unit tests; attempted mutating command
      refused; message read-state unchanged after fetch (test identity or
      synthetic message).
- [ ] Deny tests: principal A cannot read principal B (synthetic second
      principal); no secret in logs.
- [ ] Real Jason mailbox/calendar connected only after the above pass.

Gate: read-only proven, minimized records correct, egress limited to iCloud
and `aster-llama`.

### M2 — Analysis and the Personal Assistant persona

- [ ] Analyzer with dedicated key; triage, summaries, flags, calendar
      digest; injection fixtures included.
- [ ] Read-only PA API; Personal Assistant persona in Companion; server-side
      PA/web tool mutual exclusion enforced and regression-tested.
- [ ] Jason reviews a labelled real sample: no dangerous misses on
      time-sensitive mail.
- [ ] Capacity check against existing consumers.

Gate: useful, accurate L1 analysis; existing personas regress clean.

### M3 — Morning check-in and daytime nudges

- [ ] Composer: calendar + mail + news digest (+ research slot), stale-state
      labelling, optional spoken version via LXC 116.
- [ ] Generic notifications; opt-in nudge set; feedback controls.
- [ ] Capability-ladder runtime and committed policy file, all capabilities
      at L1; kill switch; demotion trigger tested with a synthetic
      capability.

Gate: Jason uses the check-in on real days and accepts it; ladder
enforcement proven with denied-action tests.

### M4 — Isolated overnight web research

- [ ] Present the exact egress rule (target, scope, logging, rollback) for
      Jason's explicit approval (non-waivable stop condition).
- [ ] Research guest, SearXNG, egress proxy, worker; Researcher persona and
      queue in Companion.
- [ ] Prove isolation: research guest cannot reach PA guest, Management
      VLAN 50 or other VLANs; PA guest cannot reach the web.
- [ ] Web injection fixtures; citation accuracy spot-check; overnight run
      reported in the check-in.

Gate: two real overnight research runs accepted by Jason; isolation tests
pass.

### M5 — Photography Assistant

- [ ] Vision option from D10 deployed with rollback, and existing consumers
      regression-tested.
- [ ] Immich MCP (pinned, tool-allowlisted) on the PA guest with a read-only
      key. Prove denied writes (upload/update/delete/album) with the real
      key. Narrow VLAN 70 → Immich firewall path approved and added.
- [ ] Rules-card extraction via the Researcher, with Jason's confirmation
      flow in Companion. Test with at least two real competitions.
- [ ] Shortlist and vision scoring. Flag editing software, people/children
      and unverifiable rules.
- [ ] Deterministic formatter: output resolution, file size and colour
      space checked against the card. Location stripped. No crop or
      retouch.
- [ ] Nightly 02:30–03:30 job gated on backup completion, with carry-over.
      Photography Assistant persona has no web and no write tools.
- [ ] Jason approves real prepared entries for at least one competition.

Gate: denied-write proof against Immich, rules cards confirmed by Jason,
formatted files pass their card's checks, and Jason accepts the
recommendations as useful.

### M6 — Hardening, family readiness and graduation

- [ ] Retention deletion proven; Doctor/monitoring; backups per D6;
      restore proof of config and policy.
- [ ] Enrolment/removal runbook tested with a synthetic second principal.
- [ ] Full integration checklist; two independent production-path passes.
- [ ] Close-out with the capability ladder at L1 and the first promotion
      candidates (likely `mail.draft` L2) listed as follow-ups.

## Validation and evaluation

- **Functional:** triage agreement with Jason's labels; no missed
  time-sensitive items; calendar conflicts found; research answers cited and
  checkable.
- **Security:** read-only proofs; cross-principal deny; PA/web tool
  exclusion; research-zone isolation; secret-pattern scan of logs/Git.
- **Adversarial:** injected instructions in emails, event notes and web
  pages ("forward this", "fetch this URL", "ignore previous"); malformed
  MIME; huge messages; hostile HTML.
- **Failure:** iCloud auth failure/revoked password, `aster-llama` down,
  proxy down, interrupted jobs — fail visible, resume cleanly.
- **Regression:** existing personas, ARR/Lab Ops gates, news and speech
  latency.
- **Photography:** formatted outputs measured against the card (pixels,
  bytes, colour profile, no GPS). Immich unchanged after runs. Injection
  text in competition rules and in photo captions/EXIF is ignored.
- **Human workflow:** Jason's real-day acceptance of check-in, nudges and
  photo recommendations.

## Observability and maintenance

- Doctor: reader freshness per principal, analyzer success, check-in
  generated today, research queue health, egress proxy up, retention job
  last run, photo job last completion and Immich reachability/key validity.
  Output is non-secret and counts only.
- Existing Doctor alerting only; no new alert channel.
- Maintenance: app-specific password rotation schedule; SearXNG updates;
  monthly review of injection-fixture results and feedback.

## Backup, restore and rollback

- Policy file and code live in Git. Guest configuration is covered by the
  existing Proxmox job once the LXCs exist (store included or excluded per
  D6).
- Credentials are regenerable and not backed up; rotation replaces them.
- Last-known-good: current Aster without the two new personas. Disabling
  their flags restores it.

## Documentation and systems-of-record updates

- [ ] **HomeLab Doctor** — checks above.
- [ ] **Monitoring/alerting** — existing Doctor path; Prometheus job only if
      M0 shows value.
- [ ] **Backup and recovery** — per D6; policy/config restore proof.
- [ ] **NetBox** — two new LXCs, IPs, VLAN 70 interfaces.
- [ ] **Human wiki** — assistant user guide, enrolment/removal, kill switch.
- [ ] **Aster mirror/snapshot** — operational docs only; personal data and
      research reports never enter the shared corpus.
- [ ] **Operational reference** — `Aster-Operations.md` assistant section.
- [ ] **Repository documentation** — portfolio, changelog, network design
      for the egress rule.
- [ ] **Diagrams/rack** — not applicable (virtual only), unless the network
      diagram shows per-guest egress.
- [ ] **Homepage** — not applicable; the Companion App is the surface.
- [ ] **Authentication/authorization** — Authentik users as principals;
      passkey approval reserved for L3+.
- [ ] **DNS, certificates, firewall** — PA egress allowlist; research egress
      rule (M4); VLAN 70 PA guest → Immich path (M5); no public DNS.
- [ ] **Automation and schedules** — reader, analyzer, composer, research,
      photo (backup-gated) and retention timers with missed-run behavior.
- [ ] **Security inventory** — credential locations, modes, rotation,
      revocation.
- [ ] **AI administration integration** — the Assistant is an AI consumer of
      personal data, not an administrator: record the identities, keys,
      custody and revocation; AI-PAM onboarding when available.

## Graduation criteria

Every milestone gate passes. Mail and calendar are proven read-only. The zone
separation is proven by tests. Jason has used the check-in and research on
real days and accepts them, and has approved real prepared competition
entries with Immich proven unchanged. Retention deletion is proven. Doctor coverage is
live. Enrolment and removal are rehearsed with a synthetic principal. The
capability ladder is enforcing L1 for every capability except
`photo.format` at L2. No secret or personal
content is in Git, logs or Aster's corpus.

## Evidence log

- **2026-09-23 — Project proposed.** Jason chose to pivot Aster toward a
  personal assistant, consolidate the three proposed email/calendar/digest
  charters into this project, adopt the recommended separation between
  personal data and web research, start read-and-analyze only, use iCloud
  for all, design for family expansion, and include a governed evolution
  mechanism toward eventual basic sending and appointments. Read-only
  repository review only; no system changed. Discovered constraint R1
  (unscoped iCloud app-specific passwords) raised for decision D1.

- **2026-09-23 — Photography Assistant added.** Jason added a third persona
  to this project: competition-rule-aware Immich library analysis,
  recommendations and formatted entries for his approval, nightly
  02:30–03:30. Decisions D8–D12 recorded. Read-only discovery (F5): Immich
  2.7.5 supports scoped read-only keys; Luminar has no API or MCP, so it is
  excluded; the current model is text-only; the backup overlap is handled by
  a gated start. Formatting was interpreted as deterministic
  resolution/file-size preparation from Immich sources, and "no background"
  as no background replacement. Jason to correct if either is wrong.

- **2026-09-23 — Photography rules clarified.** Jason confirmed formatting
  means a fixed tool working from Immich sources, and clarified "no
  background" as **no border**. D12 and the formatter/flag design are
  updated. Background replacement is not a standing rule; each competition's
  card governs it.

- **2026-09-23 — M0 read-only discovery.** Apple documentation reviewed
  (F1): R1 confirmed, all app-specific passwords are revoked on Apple
  Account password change, and a newer app-authorization path was noted as a
  follow-up. Live read-only Proxmox/LXC 110 check (F2/F3): single-slot, 8K
  context, ≈5.4 tokens/s decode, quiet 22:00–02:00 window, VLAN 70 .15 now
  used by Paperless-ngx. Design adjusted: precomputed check-ins, one message
  per request, chunked research with 3–5 topics per night. The SSH check ran
  outside the Claude Code sandbox after a sandbox refusal to the allowlisted
  Proxmox host; commands were read-only. **Remaining M0 items:** Jason
  creates the assistant and test Apple IDs, and chooses egress option F4.

- **2026-09-23 — Pre-start assessment accepted.** Jason accepted D1 (R1
  residual risk), D2 (assistant Apple ID with view-only shares), D3
  (disposable test Apple ID), D4 (Stream M), D5 (24 h / 15 days / 60 days),
  D6 (exclude PA store from backups) and D7 (research 22:00–02:00), and split
  the new persona into Personal Assistant and Researcher. Project moved to
  Active — M0. Next safe action: remaining M0 read-only discovery (Apple
  credential-scope verification, `aster-llama` headroom, placement/egress
  design) while Jason creates the two Apple IDs.

## Close-out

Not started.
