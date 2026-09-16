# Book Recommender Project

> Status: Proposed — not yet authorized
>
> Project owner: Jason
>
> Proposed: 2026-09-15
>
> Authorization stream: not yet selected — Stream M or Stream A to be chosen by
> Jason before implementation begins

## Purpose

Give Jason a periodic, private list of books/audiobooks to consider adding to
the household e-book and audiobook libraries, based on what's already owned —
originally pitched as a "Calibre/Kavita" recommender. As detailed below,
**Kavita is not actually deployed in this lab**, and the real "Calibre" tile
is not the API-having application Jason may have had in mind when naming the
idea. This charter treats that as the project's central open architectural
question rather than assuming a ready-made API surface exists.

## Current state and evidence

This section is written directly from
[`docs/04-Operations.md`](../04-Operations.md) ("Calibre and Audiobookshelf
(2026-09-05)") and a repository-wide check — read both before assuming
anything about this project's feasibility.

- **E-books**: the real library lives at `/mnt/Media/media/books` (851M) on
  TrueNAS, and is itself a valid Calibre library (it has its own
  `metadata.db`) — 723 real books, confirmed via `calibredb list
  --library-path=/mnt`. It is mounted into a TrueNAS SCALE-managed container
  (`ix-calibre-calibre-1`) running the **literal desktop Calibre
  application**, exposed only through a Selkies WebRTC remote-desktop UI.
- **Critical fact:** this Calibre deployment has **no REST API**. Per
  `docs/04-Operations.md`, it "can never get a widget" for exactly that
  reason — there is no programmatic surface to query title/author/genre/tag
  metadata, only the remote-desktop GUI a human drives interactively. Any
  automated reader must either bypass the app entirely (read `metadata.db`
  directly) or sit behind a different application altogether.
- **Kavita is not deployed anywhere in this lab.** A repository-wide,
  case-insensitive grep for "Kavita" returns zero hits outside of the
  original brainstormed project-idea list this charter originates from. It
  is not a TrueNAS app, not an LXC, not referenced in any operational
  document. Treating it as an existing data source would be a fabrication;
  it would have to be deployed from scratch.
- **Audiobooks are materially more tractable.** Audiobookshelf runs as a real
  TrueNAS SCALE container (`ix-audiobookshelf-audiobookshelf-1`), completed
  first-run setup on 2026-09-05, and has a working REST API. Its library
  ("Audiobooks", media type Books, folder `/mnt` pointing at
  `/mnt/Media/media/audiobooks`, 49GB, ~46 titles) was scanned successfully
  and its metadata (cover art, author, etc.) auto-matched. This means an
  audiobook-only version of this recommender has a real, already-working API
  to build against **today**, with no new service to deploy — a
  fundamentally different risk profile from the e-book side.
- Shared local inference (`aster-llama.service`, LXC 110,
  `192.168.70.12:11435/v1`, Qwen3.8 27B, Lab VLAN 70, bearer-authenticated)
  is available for narrative recommendation write-ups, noted as a resource
  contended by other AI projects (Aster, MuckScraper, and the proposed
  Auto-Collection-Descriptions and Music Recommender projects) — an open
  capacity question, not a settled one.

## Scope

- Read Audiobookshelf's library metadata (author, series, genre/tags,
  and — if exposed — listening progress/completion) via its REST API, using
  a dedicated least-privilege API key/token if Audiobookshelf supports
  scoped access, otherwise a dedicated account with the narrowest role it
  offers.
- Resolve the e-book data-source question (see Architecture and the single
  biggest open decision below) as an explicit early decision, not an
  assumption baked into the rest of the design.
- Compute recommendations (author/genre/series similarity, and completion-
  weighted signals if available) and produce a periodic, human-readable
  report, mirroring the Music Recommender project's report-only posture.
- Optionally use `aster-llama` for narrative "why this is recommended"
  write-ups, not for the core similarity computation.

## Out of scope

- Deploying Kavita or calibre-web as a decided outcome of this charter — that
  decision belongs to Jason, informed by the trade-offs below, not assumed
  by the project document.
- Any write access to the Calibre library, its `metadata.db`, or the
  Audiobookshelf library — this project is read-only against both, no
  matter which e-book data-source path is chosen.
- Acquiring or downloading any book/audiobook — like the Music Recommender,
  this project recommends only; acquisition remains a manual decision (there
  is no Radarr/Sonarr/Lidarr-equivalent "book request" pipeline in this lab
  today, and building one is not this project's job).
- Any third-party reading/listening-service integration (Goodreads,
  Audible, StoryGraph, etc.) as a recommendation input — this would send
  private reading interests to a third party, against the lab's
  maximum-practical-privacy principle, unless separately and explicitly
  approved later.
- A general Calibre/Audiobookshelf management UI or the unrelated
  Selkies/TLS access gap noted in `docs/04-Operations.md` — that is a
  standing infrastructure item independent of this project.

## Authority model

Audiobookshelf's live library state is the authority for audiobook facts.
For e-books, authority depends on the path chosen: Calibre's own
`metadata.db` remains authoritative regardless of which reading method is
used (a direct SQLite read does not change what owns the data, only how it's
read) — a newly-deployed Kavita/calibre-web instance would need to point at
the same underlying files rather than becoming a second, divergent copy of
the library. This project itself produces a derived, non-authoritative
report only.

## Architecture and design decisions

**The single biggest open decision governs everything else in this
project and must be resolved before Milestone 1's design work, not during
it:**

Since the real Calibre deployment has no REST API and Kavita does not exist
in this lab, an e-book recommender has exactly two real paths:

1. **Deploy a new service (Kavita or calibre-web) as a prerequisite.** This
   is a genuine new-platform decision, not a small addition — it means a new
   TrueNAS app or container, its own account/auth, its own attack surface,
   and ongoing maintenance, purely to get a metadata API this project needs.
   The lab ethos's caution against adding self-hosted services without clear
   justification applies directly here: the *only* justification would be
   this recommender project itself, so the cost/benefit has to be weighed
   explicitly, not treated as an obviously-worth-it default. Calibre-web is
   the lighter-weight option of the two (a web frontend over the same
   library, not a second library manager); Kavita is a heavier, more
   full-featured platform historically aimed at comics/manga/e-books beyond
   what's asked for here. Either would need its own project-level scoping
   (deployment, hosting VLAN, backup, credentials) before this recommender
   could depend on it.
2. **Read Calibre's `metadata.db` SQLite file directly, read-only, without
   going through the Calibre application at all.** This avoids deploying
   anything new: `metadata.db` is a well-documented, stable SQLite schema
   that many third-party tools already read this way. The trade-offs are
   real but bounded: (a) a read must be resilient to the file being open/
   locked by the Calibre desktop app at the same moment (mitigated by
   opening in read-only mode and tolerating a transient lock/retry, never
   writing); (b) this is coupling to Calibre's internal schema rather than a
   stable public API, so a future Calibre upgrade could change it (a real
   but historically slow-moving risk for this specific database); (c) it
   only ever reads facts Calibre already has (title, author, tags, series,
   ratings) — no reading-progress/completion signal exists on the e-book
   side at all, unlike Audiobookshelf.

This charter does not choose between these paths. Jason should decide based
on: whether a Kavita/calibre-web deployment has independent value beyond
this project (e.g. Jason actually wants a browsable e-book web UI, in which
case the recommender becomes a secondary beneficiary of a decision made on
its own merits), versus preferring the narrower, no-new-service
`metadata.db` read for this project alone.

**Because of this open question, propose starting with audiobooks only.**
Audiobookshelf's real, working, already-deployed API makes an
audiobook-only version of this recommender buildable immediately, with a
materially smaller and better-understood footprint than the e-book side.
This lets Jason evaluate whether the recommender concept delivers real value
before committing to either e-book path (new service vs. direct database
read). E-books become Milestone 3+, gated on the decision above, rather than
blocking the whole project on an unresolved architecture question.

**Reader/generator/report split**, matching the Music Recommender's pattern:
a source-local, least-privilege Audiobookshelf reader (and, later, whichever
e-book reader is chosen) feeds a plain, auditable similarity computation;
`aster-llama` is used only for optional narrative write-up, not core
ranking, for the same contention-management reason given in the Music
Recommender proposal.

**Hosting: recommend the TrueNAS script-style pattern for the same reasons
as the Music Recommender** — a periodic batch report with no persistent
service, matching the Jellyfin-Library-Integrity-Automation/Video-Library-
Archiving precedent, unless Jason wants this bundled with the Music
Recommender into one combined "household media recommender" service (a
reasonable option worth raising, not assuming).

## Privacy and security design

- All computation happens locally; no reading-history or library metadata
  is sent to any third party (Goodreads, Audible, etc. are explicitly out of
  scope as inputs, above).
- Audiobookshelf access uses the narrowest role/token the app supports,
  never a shared admin account — matching the existing `admin` account's own
  scope should not be widened for this project; a dedicated reader identity
  should be created if Audiobookshelf's permission model allows it.
- If the direct-`metadata.db`-read path is chosen: the read must be
  filesystem-level read-only (no write handle ever opened), and the account/
  process performing the read should have no broader filesystem access than
  that one file and its containing library directory.
- If a new Kavita/calibre-web deployment is chosen instead: it must follow
  the same VLAN, credential, and backup conventions as every other
  self-hosted service in this lab (least-privilege service account,
  Lab-VLAN-appropriate placement, no public exposure) — this would be
  scoped as its own sub-decision with its own risk assessment before
  deployment, per the standard's requirement that a materially different
  system/objective needs its own explicit approval.
- No new inbound exposure or firewall change is needed for the
  audiobooks-only phase.

## Pre-start risk assessment

- **Affected systems:** read-only against Audiobookshelf initially; e-book
  scope (Calibre `metadata.db` or a new Kavita/calibre-web instance) is
  explicitly deferred pending Jason's architecture decision.
- **Known consumers:** none — new report, no existing dependency.
- **Confidentiality/secret risk:** low for the audiobook phase (one
  least-privilege API credential). The new-service path (if chosen) adds a
  new credential/account surface that doesn't exist today — a real,
  though bounded, increase in attack surface that must be weighed against
  the no-new-service alternative.
- **Availability/integrity risk:** negligible for read-only Audiobookshelf
  calls. For the direct `metadata.db` read path: a naive implementation
  could corrupt or lock the database if it ever opens a write handle by
  mistake — mitigated by using a strictly read-only SQLite connection mode
  and never touching the file Calibre itself might be writing to.
- **Privacy risk:** audiobook listening/completion data (if read) is
  household behavioral data; keep it local to the report, same posture as
  the Music Recommender's play-history handling.
- **Irreversible operations:** none in the audiobooks-only phase. If a new
  service is deployed for e-books later, that deployment itself is the
  first irreversible-ish decision (removable, but a real change) and needs
  its own explicit sign-off separate from this document's general approval.
- **Recovery checkpoint:** not applicable to a read-only reporting tool.
- **Test strategy:** validate recommendations against the known real
  Audiobookshelf catalog (46 titles) — small enough to manually sanity-check
  every recommendation in an early run.
- **Likely interruption:** none expected; not a production dependency.
- **Unresolved decisions requiring Jason's acceptance before e-book work
  starts:** the Kavita/calibre-web-deployment vs. direct-`metadata.db`-read
  choice (the project's central open question); whether Audiobookshelf
  exposes a completion/progress signal worth using, to be confirmed in
  Milestone 1; recommendation cadence and hosting; and `aster-llama`
  contention acceptability for this project's expected call volume.

## Persistence plan

Each run's Audiobookshelf (and later, e-book) snapshot and output report are
written to a dated directory under the tool's own install path, matching the
Music Recommender's persistence approach — a read-only batch job with no
partial-state risk on interruption.

## Milestones

### Milestone 1 — Audiobook-only discovery and design confirmation

- [ ] Confirm Audiobookshelf's actual API surface for metadata, genre/author/
  series data, and any listening-progress/completion signal.
- [ ] Confirm the narrowest achievable credential scope for a dedicated
  reader identity.
- [ ] Decide recommendation cadence and hosting for the audiobook-only
  phase.
- [ ] Present the e-book architecture options (deploy Kavita/calibre-web vs.
  direct `metadata.db` read) to Jason as an explicit decision point before
  any e-book milestone begins — this document does not choose for him.

Completion gate: an accurate picture of Audiobookshelf's real API exists,
cadence/hosting are decided for the audiobook phase, and the e-book
architecture question is presented (not yet necessarily resolved).

### Milestone 2 — Audiobook recommender, dry run then recurring

- [ ] Build the read-only Audiobookshelf collector with a dedicated
  least-privilege credential.
- [ ] Implement similarity/weighting logic against the confirmed data
  source; generate a first report and manually review it against the known
  46-title catalog for sanity.
- [ ] Add the agreed schedule (if periodic) and a HomeLab Doctor staleness
  check.

Completion gate: a sample report is judged useful and accurate by Jason, and
(if scheduled) it runs reliably with detectable staleness/failure.

### Milestone 3 — E-book architecture decision and implementation

Blocked on Jason's decision from Milestone 1.

- [ ] If a new service (Kavita or calibre-web) is chosen: scope, deploy and
  secure it as its own bounded sub-effort (hosting, credentials, backup,
  VLAN placement) before this project consumes its API — this may warrant
  being tracked as a short separate project record given the standard's
  requirement that a materially different system gets its own explicit
  scoping, rather than being absorbed silently into this one.
- [ ] If direct `metadata.db` reading is chosen: implement a strictly
  read-only SQLite reader, tested against a copy of the real database first,
  then validated against the live file without ever opening a write handle.
- [ ] Extend the recommendation logic to include e-book data, using the same
  similarity approach as the audiobook phase.

Completion gate: e-book recommendations are produced from a real, verified
data source with no write exposure to the live Calibre library, and (if a
new service was deployed) it has passed its own scoped risk assessment and
backup verification.

### Milestone 4 — Combined report and hand-back

- [ ] Decide whether audiobook and e-book recommendations are delivered as
  one combined report or two separate ones.
- [ ] Run for a few cycles and confirm recommendation quality holds up.
- [ ] Document final architecture, credentials, schedule, and rollback path
  for both data sources.

Completion gate: normal operation does not depend on this session
continuing, and Jason has reviewed enough cycles to judge ongoing value for
both audiobooks and e-books.

## Validation plan

- Functional: recommendations are genre/author-plausible and never recommend
  a title already fully present in either library.
- Data-source correctness: manually cross-check a sample of Audiobookshelf-
  reported metadata (and, later, `metadata.db` or Kavita/calibre-web data)
  against the actual library contents.
- Failure-path: bad credential, unreachable Audiobookshelf/e-book source, and
  unreachable `aster-llama` (if used) all fail loudly with no silent partial
  report.
- Safety: for the direct-`metadata.db`-read path, explicitly test behavior
  while Calibre's desktop app has the file open, confirming no lock
  contention causes a corrupt read or, worse, a write attempt.
- Privacy: confirm no reading/listening data leaves the local report
  directory.

## Observability and maintenance

- HomeLab Doctor staleness check once Milestone 2 (audiobooks) introduces a
  schedule; extend to cover the e-book source once Milestone 3 lands.
- No new alerting thresholds beyond "did the last run succeed" — this is an
  advisory report, not a health-critical service.

## Backup, restore and rollback

- Read-only tool; no production state to protect beyond its own config/
  credentials (mode-600, outside Git) and report history.
- If a new e-book service is deployed (Milestone 3, Kavita/calibre-web
  path), it needs its own backup coverage matching this lab's standard
  pattern (config + any application database, verified restore) before it
  can be relied on — that is part of that sub-effort's own scoping, not an
  afterthought.
- Rollback for the recommender itself is disabling its schedule and/or
  revoking its credentials; rollback for a newly-deployed e-book service (if
  chosen) is removing that service entirely, which does not affect the
  underlying `/mnt/Media/media/books` library since it would only ever be
  mounted read-only for this purpose.

## Documentation and integration impact checklist

- [ ] **HomeLab Doctor** — not applicable until Milestone 2 introduces a
  schedule; then add a staleness/failure check, extended for e-books in
  Milestone 3.
- [ ] **Monitoring/alerting** — not applicable beyond Doctor coverage for an
  advisory report tool.
- [ ] **Backup and recovery** — required for config/credentials and report
  history; required and separately scoped for any new e-book service
  deployed under Milestone 3.
- [ ] **NetBox** — not applicable if hosted as a TrueNAS script; required
  (new LXC or container entry) if an LXC hosting path or a new Kavita/
  calibre-web container is chosen.
- [ ] **Human wiki** — optional operator note on report delivery and, if
  deployed, a new e-book service's basic operation.
- [ ] **Aster mirror/snapshot** — not applicable; this project's output is a
  personal taste report, not durable operational knowledge.
- [ ] **Operational reference and runbooks** — add a short entry once built;
  update `docs/04-Operations.md`'s Calibre/Audiobookshelf section if a new
  e-book service changes that section's facts.
- [ ] **Repository documentation** — add to `docs/projects/README.md`
  portfolio table (by others) and cross-link from `docs/04-Operations.md`.
- [ ] **Diagrams/rack records** — not applicable for the audiobook-only
  phase; required if a new e-book service/container is deployed.
- [ ] **Homepage/service discovery** — not applicable for a periodic report
  with no persistent UI; a new Kavita/calibre-web deployment (if chosen)
  would get its own Homepage card as part of that sub-effort.
- [ ] **Authentication/authorization** — new dedicated Audiobookshelf
  credential, least-privilege; new e-book service (if deployed) needs its
  own least-privilege account and, ideally, integration with the existing
  Authentik pattern rather than a standalone local account.
- [ ] **DNS, certificates and firewall** — not applicable for the
  audiobook-only phase; a new e-book service would need the same
  private-by-default placement as every other self-hosted service here.
- [ ] **Automation and schedules** — if Milestone 2/3 add schedules,
  document ownership, missed-run behavior and avoidance of conflicts with
  Jellyfin-Library-Integrity-Automation's and any other scheduled job's
  windows.
- [ ] **Security inventory** — new credentials recorded in the existing
  credential inventory location, outside Git.

## Graduation criteria

Not applicable at proposal stage. Expected to require: a working,
Jason-reviewed audiobook recommender with staleness detection; an explicit,
accepted decision on the e-book architecture question; and, if e-books are
built, a working recommender against a verified read-only data source with
no risk to the live Calibre library.

## Evidence log

No implementation work has occurred; this document is the initial proposal.

## Close-out

Not applicable — proposal stage only.

## References

- [Project Creation Standard](../Project-Creation-Standard.md)
- [`docs/04-Operations.md` — "Calibre and Audiobookshelf (2026-09-05)"](../04-Operations.md)
- [Music Recommender proposal](Music-Recommender.md)
- [Jellyfin library integrity automation](Jellyfin-Library-Integrity-Automation.md)
- [Aster Operations — shared `aster-llama` endpoint](../Aster-Operations.md)
- [Audiobookshelf API documentation](https://api.audiobookshelf.org/)
