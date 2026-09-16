# Music Recommender Project

> Status: Proposed — not yet authorized
>
> Project owner: Jason
>
> Proposed: 2026-09-15
>
> Authorization stream: not yet selected — Stream M or Stream A to be chosen by
> Jason before implementation begins

## Purpose

Give Jason a periodic, private list of new artists/albums to consider adding
to the household Jellyfin music library, based on what's actually already in
that library (and, if available, what's actually been listened to) — rather
than relying on a third-party streaming service's recommendation engine and
its associated data collection. The user-visible result is a report (not a
live UI) of recommended additions Jason can review and decide whether to
request via Lidarr.

This project does not acquire or add music itself — it recommends. Turning a
recommendation into an actual library addition remains a manual Lidarr
request, or a candidate future integration explicitly scoped later.

## Current state and evidence

- Jellyfin's Music library (`/mnt/Media/data/media/music`) is managed by
  Lidarr (255 artists) and was the subject of an extensive, recent, real
  cleanup — 271 orphaned tracks, a library-wide featured-artist folder-scatter
  bug, missing album art, and duplicate/gap-fill albums, all found and fixed
  by hand, then formalized into the standing
  [Jellyfin-Library-Integrity-Automation](Jellyfin-Library-Integrity-Automation.md)
  project. That project is the authority for library *hygiene*; this project
  is a new, separate concern (what to add, not what's wrong with what's
  already there) and must not duplicate or compete with its Wednesday 3am
  window for the same media files.
- Whether Jellyfin exposes real per-user listening/play-history data via its
  API (e.g. play counts, last-played timestamps, a Playback Reporting-style
  endpoint) is **unconfirmed** — a repository-wide search found no existing
  project or reference that queries such an endpoint. This must be verified
  directly against the deployed Jellyfin instance in Milestone 1, not
  assumed either way.
- Lidarr's own catalog metadata (artist list, monitored/unmonitored status,
  genre/tag data it holds) is a confirmed, already-used read surface — the
  existing Jellyfin-Library-Integrity-Automation project already reuses
  Lidarr's API key read-only for its scatter/duplicate detection, and
  [ARR-Stack-Operational-Reference.md](../ARR-Stack-Operational-Reference.md)
  documents the established pattern for scoping ARR-adjacent access
  read-only rather than touching its database directly.
- The Music Playlist Acquisition Bridge project
  ([Music-Playlist-Acquisition-Bridge.md](Music-Playlist-Acquisition-Bridge.md))
  is a related but distinct concern: it translates *externally supplied*
  playlist exports (Spotify/Apple Music) into Lidarr album requests. It does
  not analyze the existing library or generate original recommendations from
  listening behavior — there is no overlap in what each project actually
  computes, only in the fact that both can produce Lidarr-request-shaped
  output.
- Shared local inference (`aster-llama.service`, LXC 110,
  `192.168.70.12:11435/v1`, Qwen3.8 27B, Lab VLAN 70, bearer-authenticated)
  is available and is the established reuse target for any generative or
  reasoning step — noted here as a resource contended by other projects
  (Aster itself, MuckScraper, and the proposed Auto-Collection-Descriptions
  project), an open capacity question rather than a settled one.

## Scope

- Read Jellyfin's library metadata (artists, albums, genres/tags) via a
  source-local, least-privilege API key.
- Read Jellyfin's real listening/play-history data via its API, *if* Milestone
  1 confirms such an endpoint exists and is populated for this household's
  actual usage pattern (see Architecture below for the fallback if not).
- Read Lidarr's catalog metadata (monitored artists, genre/tag data) via its
  existing read-only access pattern.
- Compute artist/album-level recommendations using genre/tag similarity
  and/or listening-history weighting, optionally assisted by `aster-llama`
  for narrative write-ups ("why this is recommended") rather than for the
  core similarity computation itself.
- Produce a periodic, human-readable report of recommended additions, each
  with a stated reason grounded in real library/listening data.

## Out of scope

- Automatically creating Lidarr requests or adding any music — this project
  recommends only; a human decides what to actually request, at least for
  this proposal's scope. Auto-request could be proposed later as its own
  explicitly-scoped decision, matching how Jellyfin-Library-Integrity-
  Automation separates safe-automatic actions from human-approved ones.
  This is different in kind: adding a *new* artist/album is an acquisition
  decision (cost of storage, taste judgment), not a reversible metadata fix.
- Any change to Jellyfin or Lidarr library structure, tagging, or metadata —
  this project is read-only against both.
- Streaming-service integration (Spotify/Last.fm/etc. API calls) for
  recommendation input — this would send private listening interests to a
  third party, against the lab's local-first/maximum-practical-privacy
  ethos, unless a future, separately-scoped decision explicitly accepts that
  trade-off for a stated benefit.
- Real-time or interactive recommendation UI — this is a periodic report,
  not a service with its own dashboard, at least for the initial scope.
- Anything already owned by Jellyfin-Library-Integrity-Automation (orphan/
  scatter/duplicate detection, artwork, collection-count checks).

## Authority model

Jellyfin's live library state and (if confirmed) play-history data are the
authority for "what exists and what's been played." Lidarr's live catalog is
the authority for "what's monitored." This project produces a derived,
non-authoritative report; it does not become a system of record for
anything and does not write back to either source.

## Architecture and design decisions

**Source-local least-privilege readers, not raw database access**, matching
the pattern already established for Aster's ARR-adjacent work
(`docs/ARR-Stack-Operational-Reference.md`) and Jellyfin-Library-Integrity-
Automation's own Jellyfin/Lidarr API usage: a dedicated Jellyfin API key
scoped to read-only Library/Items (and play-history endpoints, if they
exist) and reuse of Lidarr's existing read-only key. No direct SQLite/
database access to either application, and no new write scope on either.

**Recommendation basis depends on Milestone 1's confirmation of play-history
availability** — this is the central open architecture question:

- If Jellyfin does expose real per-user play counts/history, recommendations
  can be weighted toward what's actually been listened to repeatedly (a
  materially stronger signal than library composition alone).
- If it does not (or the data is too sparse — e.g. if most listening happens
  outside Jellyfin's own client), the recommender falls back to a
  library-composition-only model: genre/tag co-occurrence and artist
  similarity derived from Lidarr/Jellyfin metadata already in the library,
  which is a weaker but still real, private, locally-computed signal.

Both paths avoid sending listening data to any third party — the difference
is only how strong the local signal is, not whether privacy is preserved.

**`aster-llama` is proposed for narrative write-up only, not core ranking.**
The similarity/weighting computation itself should be plain, auditable code
(no need for an LLM to compute genre overlap), reserving the shared,
contended inference endpoint for turning a ranked list into a short
human-readable "why this is recommended" note — a much lighter, batch-able
call pattern than a MuckScraper-style summarization job.

**Hosting: propose both options, recommend based on schedule shape once
Milestone 1's frequency decision is made.** A single periodic batch report
(e.g. monthly) fits the TrueNAS script-style pattern
(`/mnt/Media/data/tools/`, matching Jellyfin-Library-Integrity-Automation and
Video-Library-Archiving) with no persistent service. If Jason wants an
on-demand or more interactive version (e.g. queryable from Aster, or a small
web view), that pushes toward a new unprivileged Lab VLAN 70 LXC matching the
Aster Agent/`aster-llama` precedent instead. Recommend starting with the
TrueNAS script/report pattern for the same reason given in the Auto-
Collection-Descriptions proposal — it is the narrower, lower-overhead choice
for a low-frequency batch job — and revisiting only if usage shows the
interactive form is actually wanted.

### Single biggest open decision

**Whether Jellyfin exposes usable real listening/play-history data at all,
and if so, whether it's populated enough (versus most listening happening
outside Jellyfin, e.g. via a phone app or in-car playback that never touches
the server) to be worth building around.** This determines whether the
recommender has a real personalization signal or is effectively a
library-similarity tool wearing a recommender's name. This must be verified
against the live instance before committing to an architecture, not assumed
in either direction.

## Privacy and security design

- All computation happens locally: Jellyfin/Lidarr reads, similarity
  computation, and `aster-llama` narrative generation never leave the lab
  network. No streaming-service account or third-party recommendation API is
  contacted, consistent with the lab's maximum-practical-privacy principle.
- Dedicated, least-privilege API keys for Jellyfin (new) and Lidarr (reused,
  read-only) — mode-600, outside Git, matching existing convention.
- Any play-history data read is treated as sensitive household behavioral
  data even though it never leaves the LAN: it is used only to compute
  recommendations and is not published anywhere beyond Jason's own report,
  and is not retained longer than needed to compute the current report cycle
  unless Jason wants a trend view (a later, explicitly-scoped decision).
- No new inbound exposure or firewall change — the tool only needs existing
  reachability to Jellyfin, Lidarr, and `aster-llama`.

## Pre-start risk assessment

- **Affected systems:** read-only against Jellyfin and Lidarr; no write
  capability requested on either.
- **Known consumers:** none — this is a new report with no existing
  downstream dependency.
- **Confidentiality/secret risk:** low; two least-privilege API keys, same
  handling as existing precedent.
- **Availability/integrity risk:** negligible — read-only calls against
  already-proven-reachable APIs; a failed run produces no report rather than
  a bad one.
- **Privacy risk:** the one genuine risk in this project — household
  listening-history data, if it exists and is read, must not be exposed
  beyond the report itself (no cloud sync, no third-party API, no broader
  household visibility than Jason already has access to as owner).
- **Irreversible operations:** none — no write capability on any system of
  record.
- **Recovery checkpoint:** not applicable to a read-only reporting tool
  beyond normal repo/config backup.
- **Test strategy:** validate the recommendation logic against the known,
  already-cleaned library state (post Jellyfin-Library-Integrity-Automation)
  so results reflect real data, not lingering scatter/duplicate artifacts;
  spot-check a sample of recommendations for obvious nonsense (e.g.
  recommending an artist already fully owned).
- **Likely interruption:** none expected; not a production dependency.
- **Unresolved decisions requiring Jason's acceptance:** whether play-history
  data exists and is worth using (Milestone 1); recommendation cadence
  (weekly/monthly/on-demand) and how that maps to the hosting choice; whether
  `aster-llama` narrative write-ups are wanted or a plain ranked list
  suffices; and confirming `aster-llama` contention from other AI projects
  is acceptable for this project's expected (low, periodic) call volume.

## Persistence plan

Each run's inputs (library/Lidarr snapshot, and play-history snapshot if
used) and output report are written to a dated directory under the tool's
own install path, so a re-run can be compared against the prior cycle and an
interrupted run simply re-executes from scratch (cheap, since it is a
read-only batch computation with no partial-state risk).

## Milestones

### Milestone 1 — Discovery and data-source confirmation

- [ ] Confirm whether Jellyfin's deployed version/config exposes real
  play-history/play-count data via API, and how populated it actually is for
  this household.
- [ ] Confirm the exact Lidarr/Jellyfin read scopes needed and that a
  least-privilege key can be scoped to only those.
- [ ] Decide recommendation cadence and, based on that, the hosting approach
  (TrueNAS script vs. new Lab VLAN 70 LXC).
- [ ] Present the play-history finding and its implication for
  recommendation strength to Jason before building the similarity logic.

Completion gate: the data-source question is answered with live evidence,
and Jason has decided cadence, hosting, and whether `aster-llama` narrative
write-ups are in scope.

### Milestone 2 — Recommendation logic, dry run only

- [ ] Build the read-only Jellyfin/Lidarr collectors with dedicated
  least-privilege keys.
- [ ] Implement the similarity/weighting logic against the confirmed data
  source(s) from Milestone 1.
- [ ] Generate a first report against the real (already-clean) library and
  manually review it for sanity (no recommending already-owned artists, no
  nonsensical genre matches).

Completion gate: a sample report is judged useful and accurate by Jason
before any recurring schedule is proposed.

### Milestone 3 — Recurring report and integration

- [ ] Add the chosen schedule (cron/systemd timer) if cadence is periodic
  rather than on-demand, avoiding conflict with
  Jellyfin-Library-Integrity-Automation's Wednesday 3am window and any other
  existing scheduled media-pipeline job.
- [ ] Add a HomeLab Doctor staleness check if scheduled.
- [ ] Decide and document where the report lands (e.g. delivered like the
  MuckScraper digest, or a plain file/report directory) — a UI is out of
  scope unless separately requested.

Completion gate: recommendations arrive on the agreed cadence with a
recorded failure/staleness detection path.

### Milestone 4 — Review and hand-back

- [ ] Run for a few cycles and confirm recommendation quality holds up over
  time (not just the first sample).
- [ ] Document final architecture, credentials, schedule, and rollback
  (disable schedule / remove keys).

Completion gate: normal operation does not depend on this session
continuing, and Jason has reviewed enough cycles to judge ongoing value.

## Validation plan

- Functional: recommendations are genre/taste-plausible and never recommend
  an artist/album already fully present in the library.
- Data-source correctness: if play-history is used, spot-check that reported
  play counts match what Jason recalls actually listening to, at least for a
  few known cases.
- Failure-path: bad API key, unreachable Jellyfin/Lidarr, and unreachable
  `aster-llama` (if used) all fail loudly with no silent partial report.
- Regression: confirm this project's reads do not trigger any
  Jellyfin-Library-Integrity-Automation alert and do not compete for I/O
  during its Wednesday 3am window.
- Privacy: confirm no listening-history or library data is written anywhere
  outside the local report directory.

## Observability and maintenance

- HomeLab Doctor staleness check only if Milestone 3 introduces a schedule.
- No new alerting thresholds needed beyond "did the last run succeed" —
  this is an advisory report, not a health-critical service.

## Backup, restore and rollback

- Read-only tool; no production state to protect beyond its own config/API
  keys (backed up like other tool configs, mode-600, outside Git) and its
  own report history (useful for trend comparison, not safety-critical).
- Rollback is simply disabling the schedule and/or revoking the dedicated
  API keys — no dependent system needs to be unwound.

## Documentation and integration impact checklist

- [ ] **HomeLab Doctor** — not applicable until Milestone 3 introduces a
  schedule; then add a staleness/failure check.
- [ ] **Monitoring/alerting** — not applicable beyond Doctor coverage for an
  advisory report tool.
- [ ] **Backup and recovery** — required for config/API keys and report
  history, following the existing tool-config backup pattern.
- [ ] **NetBox** — not applicable if hosted as a TrueNAS script; required
  (new LXC entry) if Milestone 1 selects the LXC hosting path instead.
- [ ] **Human wiki** — optional short operator note on how/where reports
  land and how to trigger an ad-hoc run.
- [ ] **Aster mirror/snapshot** — not applicable; this project's output is
  a personal taste report, not durable operational knowledge.
- [ ] **Operational reference and runbooks** — add a short entry once built.
- [ ] **Repository documentation** — add to `docs/projects/README.md`
  portfolio table (by others) and cross-link from Jellyfin-Library-
  Integrity-Automation and the Music Playlist Acquisition Bridge project.
- [ ] **Diagrams/rack records** — not applicable unless the LXC hosting path
  is chosen, in which case update topology records for the new guest.
- [ ] **Homepage/service discovery** — not applicable for a periodic report
  with no persistent UI; revisit if an interactive form is built later.
- [ ] **Authentication/authorization** — new dedicated Jellyfin API key,
  least-privilege; reused read-only Lidarr key; no SSO change.
- [ ] **DNS, certificates and firewall** — not applicable; uses existing
  reachability to Jellyfin, Lidarr and `aster-llama`.
- [ ] **Automation and schedules** — if Milestone 3 adds a schedule, document
  ownership, missed-run behavior and scheduling conflicts avoided (the
  Wednesday 3am integrity job, the daily backup pull).
- [ ] **Security inventory** — new API key recorded in the existing
  credential inventory location, outside Git.

## Graduation criteria

Not applicable at proposal stage. Expected to require: a confirmed data
source, a sample report Jason judges useful, a working recurring cadence
with staleness detection (if scheduled), and no measurable regression to
Jellyfin-Library-Integrity-Automation or other scheduled jobs.

## Evidence log

No implementation work has occurred; this document is the initial proposal.

## Close-out

Not applicable — proposal stage only.

## References

- [Project Creation Standard](../Project-Creation-Standard.md)
- [Jellyfin library integrity automation](Jellyfin-Library-Integrity-Automation.md)
- [ARR Stack Operational Reference](../ARR-Stack-Operational-Reference.md)
- [Music playlist acquisition bridge](Music-Playlist-Acquisition-Bridge.md)
- [Aster Operations — shared `aster-llama` endpoint](../Aster-Operations.md)
- [Jellyfin API documentation](https://api.jellyfin.org/)
- [Lidarr API documentation](https://lidarr.audio/docs/api/)
