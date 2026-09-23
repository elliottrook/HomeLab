# Auto-Written Plex/Jellyfin Collection Descriptions Project

> Status: Proposed — not yet authorized
>
> Project owner: Jason
>
> Proposed: 2026-09-15
>
> Authorization stream: not yet selected — Stream M or Stream A to be chosen by
> Jason before implementation begins

## Purpose

Generate short, readable descriptions for Jellyfin movie (and, if in scope,
TV) collections that currently have no description or a poor one, using the
shared local LLM rather than manual writing. The user-visible result is a
Jellyfin collection view that reads as curated — a one- or two-sentence
description under each collection tile — without Jason having to hand-write
165+ blurbs.

This is cosmetic metadata work only. It does not change library structure,
membership, artwork, or anything Lidarr/Radarr/Sonarr manage.

## Current state and evidence

- The Plex-to-Jellyfin migration
  ([completed projects/Plex-to-Jellyfin-Media-Migration.md](<completed projects/Plex-to-Jellyfin-Media-Migration.md>))
  migrated 165 movie box-set collections into Jellyfin (covering 167/168 Plex
  collections), using a mix of the TMDb Collections plugin (auto-generated,
  franchise-derived membership and description) and manual/curated
  recreation via the Jellyfin Collection API for collections TMDb didn't
  produce. That means an unknown fraction of the 165 already carry a
  TMDb-sourced description today, and the real gap this project would close
  (collections with no description, or a weak one) has **not yet been
  measured** — inventorying it is the first milestone, not an assumed
  starting count.
- Jellyfin's own `Clean up collections and playlists` scheduled task
  **destroyed movie collections outright on two separate server restarts**
  (73 then 71 collections) before its `StartupTrigger` was disabled. This is
  recorded in
  [Jellyfin-Library-Integrity-Automation.md](completed%20projects/Jellyfin-Library-Integrity-Automation.md),
  which also built the standing collection/playlist-count regression check
  and preserved the original Plex migration manifests
  (`plex-movie-collections.json`, `plex-to-jellyfin-movie-map.json`) as the
  only real recovery path for that incident. Collections in this specific
  Jellyfin instance are a proven fragile asset, not a theoretical concern.
- Shared local inference already exists: `aster-llama.service` on LXC 110
  (`192.168.70.12:11435`, OpenAI-compatible `/v1`, Qwen3.8 27B `UD-IQ4_XS` on
  the Arc Pro B60 via Vulkan), bearer-authenticated, Lab VLAN 70 only. Other
  projects (Aster itself, MuckScraper's summarization and digest narration)
  already call this same endpoint — it is a **shared, contended resource**,
  not dedicated capacity, which this project must plan around rather than
  assume is idle.
- No AI-generated Jellyfin metadata write path exists anywhere in this repo
  today. The closest precedent is Jellyfin-Library-Integrity-Automation's own
  read/write pattern against the Jellyfin API (dedicated least-privilege API
  key, dry-run-then-apply, before/after manifest written before any change).

## Scope

- Inventory current Jellyfin movie collections and classify each as: has a
  substantive description already (leave alone), has no description or a
  placeholder/empty one (candidate), or was TMDb-plugin-generated (its
  description is that plugin's own text, not hand-written — decide whether
  "candidate" includes overwriting these; see Architecture below).
- Generate a short (1–3 sentence) description per candidate collection using
  the shared `aster-llama` endpoint, grounded only in data already available
  from Jellyfin/TMDb metadata for that collection's members (title, year,
  genre, existing summaries) — not external web lookups.
- Write generated descriptions back to Jellyfin via its Collection API, using
  a dedicated least-privilege API key scoped to exactly the endpoints needed.
- Back up the full current collection list and description text before any
  write, and cross-reference (not duplicate) the existing collection-count
  regression check from Jellyfin-Library-Integrity-Automation rather than
  building a second detector for the same failure class.
- If TV box-set collections exist and are in scope for Jellyfin at all, treat
  them as a second, later phase — the 165-collection baseline is movies only.

## Out of scope

- Any change to collection *membership*, artwork, sort order, or the TMDb
  Collections plugin's own generation logic.
- Any change to Jellyfin's `Clean up collections and playlists` task
  configuration — that belongs to Jellyfin-Library-Integrity-Automation.
- Music or audiobook metadata — see the separate Music Recommender and Book
  Recommender proposals.
- Generating descriptions from anything other than metadata already present
  in Jellyfin/TMDb for that collection (no synopsis scraping from third-party
  sites, no per-movie plot spoilers beyond what TMDb already shows).
- Building a general content-editing UI — this is a bounded backend
  generate-and-apply tool with a reviewable diff, not an interactive editor.

## Authority model

Jellyfin's own database remains the live authority for collection membership
and current description text. The preserved Plex migration manifests remain
the disaster-recovery authority for *membership* (per
Jellyfin-Library-Integrity-Automation), not for description text — this
project's own before-write backup of description text is the only recovery
path for descriptions specifically, since Plex never had TMDb-plugin-style
descriptions for manually recreated collections. This project's own dated
apply-reports are the record of what was generated and applied, when.

## Architecture and design decisions

**Reader/generator/writer split**, matching the established Aster-adjacent
pattern (source-local least-privilege reader → sanitized data → generation →
reviewed write):

1. A read-only pass against the Jellyfin API (dedicated API key, Collections
   scope only) lists all movie collections, their current description field,
   and member titles/years/genres.
2. Candidates (no/weak description) are sent to `aster-llama` with a prompt
   grounded only in that collection's own member metadata, producing a draft
   description per collection.
3. Drafts are written to a dated report for review, matching
   Jellyfin-Library-Integrity-Automation's dry-run-then-apply pattern, before
   any write reaches Jellyfin.
4. An apply step (same dedicated API key, write scope only to the
   description field) pushes accepted drafts, after first writing a
   before/after backup of the affected collections' description text.

**Hosting: recommend the TrueNAS script-style pattern, not a new LXC.** This
is a small, low-frequency, non-interactive tool (likely a one-time backfill
plus occasional runs when new collections appear) — closer in shape to
Jellyfin-Library-Integrity-Automation and Video-Library-Archiving (both
self-contained installs under `/mnt/Media/data/tools/`) than to Aster's
always-on API/UI services that justify a dedicated Lab VLAN 70 LXC. The
Lab-VLAN-70-LXC pattern remains the right choice if this ever grows into a
recurring scheduled service with its own state beyond a report directory;
that is not the case at proposal time. Jason should confirm this reasoning
before Milestone 1, since it is a judgment call rather than an obvious
default.

**Automation posture for the write step: human-reviewed for at least the
first several runs, with automation as an explicit later decision, not an
assumption.** Collection descriptions are cosmetic and trivially reversible
(a bad description can be blanked or regenerated with no data loss), which
is the same reasoning Jellyfin-Library-Integrity-Automation used to run its
safe/reversible corrections unattended. But this project's writes sit on
exactly the metadata class (Jellyfin collections) that has already caused
two real data-loss incidents in this instance, and LLM-generated text carries
its own failure mode (a plausible-sounding but factually wrong description,
e.g. misattributing a franchise entry). Recommendation: run the generate step
freely (it never touches Jellyfin), but require Jason's review of each dated
draft report before the apply step runs, for at least the first full pass
across all candidate collections. Once that pass is clean, revisit whether an
unattended apply for *future new* collections only (a much smaller, easier-
to-spot-check blast radius than the full backfill) is warranted — record that
as a Milestone 5 decision, not a Milestone 1 assumption.

### Single biggest open decision

**Whether to overwrite TMDb-plugin-generated descriptions, and how many
collections are actually candidates at all.** The 165-collection count is a
membership figure, not a description-gap figure — an unknown number of these
already carry a real TMDb-sourced description that this project should
probably leave untouched (regenerating text that already exists adds risk
for no real benefit). This has to be measured (Milestone 1 inventory) before
the project's real scope and effort are known, and Jason should decide the
overwrite policy (TMDb-generated descriptions are always out of scope for
regeneration, vs. only truly empty descriptions are candidates, vs. some
quality bar in between) before any generation work starts.

## Privacy and security design

- All generation happens against the local `aster-llama` endpoint, Lab VLAN
  70 only — no collection or media metadata leaves the lab.
- A dedicated Jellyfin API key (e.g. `jellyfin-collection-desc`) is created
  for this project, scoped to only the Collections read/write endpoints it
  actually calls — never a shared or admin key. Stored mode-600, outside
  Git, matching the `jellyfin-integrity` precedent.
- No new inbound exposure, no new VLAN, no new firewall rule: the tool only
  needs to reach Jellyfin (already Servers-VLAN-local or wherever Jellyfin
  runs) and the existing `aster-llama` endpoint on Lab VLAN 70.
- Generated text is logged in dated, non-secret reports; no credentials or
  personal data are ever part of a collection description.

## Pre-start risk assessment

- **Affected systems:** Jellyfin's collection metadata only (movies to
  start). No effect on Radarr/Sonarr, media files, or other Jellyfin
  libraries.
- **Known consumers:** Jellyfin's own web/app clients render the description
  field; no other system currently reads it.
- **Confidentiality/secret risk:** low — a new least-privilege API key is the
  only credential involved, stored per existing convention.
- **Availability/integrity risk:** a botched write could blank or corrupt
  description text for existing collections; mitigated by the before-write
  backup and the human-reviewed apply step above. It cannot delete a
  collection or member (no membership-write scope is requested for the API
  key).
- **Privacy risk:** minimal — collection descriptions are not personal data,
  and no household viewing history is involved in this project (that's the
  Music/Book recommender proposals' concern, not this one).
- **Irreversible operations:** none identified — every write is a text-field
  update, reversible by writing back the pre-change backup or blanking the
  field.
- **Recovery checkpoint:** the pre-write description backup taken each apply
  run, plus Jellyfin-Library-Integrity-Automation's existing collection-count
  baseline (for membership, not description text).
- **Test strategy:** dry-run generation and a small manually-reviewed sample
  batch before any full-library apply; no synthetic data needed since reads
  are non-destructive and writes are trivially reversible.
- **Likely interruption:** none expected to Jellyfin availability; the tool
  is a client of the existing API, not a service restart.
- **Unresolved decisions requiring Jason's acceptance before work starts:**
  the overwrite-policy question above; the LXC-vs-TrueNAS-script hosting
  call; how long the human-reviewed apply step remains mandatory before any
  unattended apply is considered; and confirming `aster-llama` contention
  from other in-flight AI projects is acceptable for this project's expected
  (low, batch) call volume.

## Persistence plan

Each run's inventory, drafts, and apply results are written to a dated report
directory (mirroring `reports/` in Jellyfin-Library-Integrity-Automation),
so the tool can resume from "what has already been reviewed/applied" rather
than re-generating from scratch after an interruption. No long-running
process is involved; a stopped run is simply re-run from the last completed
report.

## Milestones

### Milestone 1 — Inventory and gap measurement

- [ ] Enumerate all Jellyfin movie collections, current description field,
  and whether each originated from the TMDb plugin or manual recreation
  (cross-reference the preserved Plex migration manifests).
- [ ] Report the real candidate count (no/weak description) versus the
  165-collection total.
- [ ] Present the overwrite-policy and hosting decisions above to Jason for
  a decision before any generation work begins.

Completion gate: an accurate, evidence-based candidate list exists and
Jason has decided the overwrite policy and hosting approach.

### Milestone 2 — Generation, dry run only

- [ ] Build the reader against a dedicated least-privilege Jellyfin API key.
- [ ] Generate draft descriptions for all candidates via `aster-llama`,
  writing nothing to Jellyfin.
- [ ] Human-review a representative sample for factual accuracy (no
  misattributed franchise entries, no fabricated plot details) before
  trusting the approach at scale.

Completion gate: sampled drafts are accurate and appropriately short; no
Jellyfin write has occurred yet.

### Milestone 3 — Supervised apply

- [ ] Back up current description text for all candidate collections.
- [ ] Apply reviewed drafts for a small batch first, verify via the Jellyfin
  API and UI, then proceed to the full candidate set.
- [ ] Confirm the existing collection-count regression check still reports
  clean (this project must not trip it).

Completion gate: all approved drafts applied and verified with no collection
count or membership regression.

### Milestone 4 — Recurring coverage for new collections

- [ ] Decide and document the trigger for handling collections created after
  the initial backfill (manual re-run vs. a schedule).
- [ ] If scheduled, add a HomeLab Doctor check for staleness/failure,
  matching the `check_jellyfin_integrity` pattern.

Completion gate: new collections predictably get a description without
re-running a full-library backfill each time.

### Milestone 5 — Automation posture review and hand-back

- [ ] Revisit whether the apply step for *new* collections only can move to
  unattended, based on Milestone 3's clean track record.
- [ ] Document final architecture, credentials, schedule (if any), and
  rollback path.

Completion gate: an explicit, justified decision is recorded on automation
posture, and normal operation does not depend on this session continuing.

## Validation plan

- Functional: generated descriptions read naturally, stay within a defined
  length budget, and do not fabricate details absent from the source
  metadata.
- Regression: Jellyfin-Library-Integrity-Automation's collection-count check
  reports clean before and after every apply run.
- Failure-path: bad API key, unreachable Jellyfin, and unreachable
  `aster-llama` all fail loudly with no partial/silent write.
- Rollback: restoring the pre-apply description backup for a sample
  collection is tested at least once.
- Contention: confirm `aster-llama` response times stay reasonable for a
  batch job run outside of other projects' interactive use, or document an
  observed conflict for Jason to weigh against the other AI projects sharing
  that endpoint.

## Observability and maintenance

- Add a HomeLab Doctor check (`check_collection_descriptions` or similar)
  only once Milestone 4 introduces a schedule — a one-time backfill with no
  recurring job does not need one beyond the existing collection-count check
  already covering the risk this project could introduce.
- Reuse, not duplicate, `check_jellyfin_integrity`'s existing collection/
  playlist-count regression signal.

## Backup, restore and rollback

- Every apply run's before-state (description text only) is written to the
  tool's own report directory before any write, following the
  Jellyfin-Library-Integrity-Automation manifest-before-move precedent.
- No change to Jellyfin's own application-database backup coverage is
  needed or proposed here — that remains a separate, already-known gap
  tracked elsewhere (see Plex-to-Jellyfin-Media-Migration's close-out note).
- Rollback is: write the backed-up description text back via the same API
  key, or blank the field — both are cheap, low-risk operations.

## Documentation and integration impact checklist

- [ ] **HomeLab Doctor** — not applicable until Milestone 4 introduces a
  schedule; then add a staleness/failure check.
- [ ] **Monitoring/alerting** — not applicable beyond Doctor coverage; no new
  metrics warranted for a low-frequency text-generation tool.
- [ ] **Backup and recovery** — required: pre-write description backups per
  run, per the plan above.
- [ ] **NetBox** — not applicable; no new device, VM, interface, or IP is
  created (uses existing Jellyfin and `aster-llama` endpoints).
- [ ] **Human wiki** — optional short operator note once implemented,
  describing how to trigger a re-run for new collections.
- [ ] **Aster mirror/snapshot** — not applicable; this project produces no
  durable operational knowledge Aster needs to answer sysadmin questions.
- [ ] **Operational reference and runbooks** — add a short entry once built,
  matching the `jellyfin-integrity` tool's own documentation pattern.
- [ ] **Repository documentation** — add to `docs/projects/README.md`
  portfolio table (by others, per this task's instructions) and cross-link
  from Jellyfin-Library-Integrity-Automation's References section.
- [ ] **Diagrams/rack records** — not applicable; no physical or topology
  change.
- [ ] **Homepage/service discovery** — not applicable; this is a batch tool
  with no persistent UI, not a dashboard-worthy service.
- [ ] **Authentication/authorization** — new dedicated Jellyfin API key,
  least-privilege, per the plan above; no change to Authentik/SSO.
- [ ] **DNS, certificates and firewall** — not applicable; no new network
  path beyond existing reachability to Jellyfin and `aster-llama`.
- [ ] **Automation and schedules** — only if Milestone 4 adds a recurring
  trigger; document ownership, missed-run behavior and concurrency control
  at that point.
- [ ] **Security inventory** — new API key recorded in the credential
  inventory location already used for `jellyfin-integrity` and similar keys;
  outside Git.

## Graduation criteria

Not applicable at proposal stage. To be defined when Jason authorizes a
stream; expected to require: an accurate inventory, a clean sample-review
pass, a full apply with no collection-count regression, and an explicit
automation-posture decision recorded per Milestone 5.

## Evidence log

No implementation work has occurred; this document is the initial proposal.

## Close-out

Not applicable — proposal stage only.

## References

- [Project Creation Standard](../Project-Creation-Standard.md)
- [Plex-to-Jellyfin media migration](<completed projects/Plex-to-Jellyfin-Media-Migration.md>)
- [Jellyfin library integrity automation](completed%20projects/Jellyfin-Library-Integrity-Automation.md)
- [Video library archiving](<completed projects/Video-Library-Archiving.md>)
- [Aster Operations — shared `aster-llama` endpoint](../reference/Aster-Operations.md)
- [Jellyfin API documentation](https://api.jellyfin.org/)
