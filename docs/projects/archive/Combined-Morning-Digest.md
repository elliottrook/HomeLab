# Combined Morning Digest Project

> Successor: [Aster Adaptive Computing](../AI%20Projects/Aster-Adaptive-Computing.md), authorized by Jason as Stream A on 2026-09-25. This archived plan is no longer an independent execution queue. Existing privacy, exclusion and safety decisions remain requirements; future release gates govern implementation.

> Status: Superseded — 2026-09-25; retained as historical requirements and evidence.
>
> Project owner: Jason
>
> Proposed: 2026-09-15
>
> Authorization stream: not yet selected — Stream M or Stream A to be chosen
> by Jason before implementation begins

## Purpose and desired outcome

A single daily briefing that pulls together the household's morning
information sources into one place, instead of Jason checking several
separate views. At proposal time the only real source is the existing news
digest; the stated end goal is to fold in email and calendar summaries once
those have their own projects, and possibly other sources later (e.g.
weather, UPS/Doctor health, surveillance overnight events), without
redesigning the digest each time a new source lands.

This is explicitly a **build-on, not duplicate** proposal. Jason already has
a working twice-daily news digest — "Your News" on LXC 114 — with a
`/digest` page and a Piper-narrated audio briefing
(`docs/projects/completed projects/News-Aggregator-Digest-and-Sections.md`,
`News-Aggregator-Audio-Digest.md`). This project should make that digest
**the news component** of the combined morning digest, not rebuild
equivalent news-summarization logic a second time.

## Current state and evidence

- **News component (exists, production):** "Your News" LXC 114
  (`192.168.70.13`, Lab VLAN 70), `news-aggregator-digest.timer` at
  05:15/17:15 `Etc/GMT+7`, `/digest` page with abridged multi-source
  summaries, deviation notes, and a Piper TTS MP3 briefing
  (`static/digest-audio/latest.mp3`) narrating the latest digest run.
  Summarization uses the shared `aster-llama` endpoint
  (`http://192.168.70.12:11435/v1`, LXC 110, bearer-authenticated, Lab VLAN
  70 only) via a dedicated least-privilege API key stored at
  `/root/.news-aggregator-llama-key` on LXC 114.
- **Email and calendar components: do not exist.** Checked the current
  portfolio (`docs/projects/README.md`) and the historical build record
  (`PROJECTS.md`) — there is no Email Triage, Calendar PA, or equivalent
  project anywhere in this repository, active or completed. "Once
  email/calendar/etc. exist" in the brief is a forward-looking statement
  about projects that have not been proposed yet, not something this
  project can integrate against today.
- **Shared inference capacity:** `aster-llama` on LXC 110 already serves the
  news aggregator's summarization/digest/deviation-notes pipeline and the
  Aster sysadmin advisor. Any additional caller (a combined-digest
  synthesis step, or a future email/calendar summarizer) adds load to the
  same single GPU-backed `llama-server` process. No capacity ceiling has
  been measured for concurrent multi-project use — this is a real, open
  question, not assumed away (see Pre-start risk assessment).
- **Doctor/Homepage/NetBox precedent:** established by the news aggregator
  project and directly reusable (see Architecture below).

## Scope

- Design (not yet build, pending Jason's stream choice) a combined morning
  briefing that presents the existing news digest as its first and, for
  now, only real content source.
- Design the integration point so a future source (email summary, calendar
  agenda, etc.) can be added as a self-contained section without
  redesigning the digest's assembly, scheduling, or presentation layer.
- Define graceful-degradation behavior for a source that is missing (not
  yet built) or temporarily down (service outage), since this will be true
  of every non-news source for the foreseeable future and of the news
  source itself during any outage.
- Decide (with Jason, as an open decision below) whether this becomes a new
  page/section on the existing news-aggregator LXC 114, or a separate
  aggregator service that pulls from multiple sources.

## Out of scope

- Building the Email Triage or Calendar PA source projects themselves —
  those are separate, not-yet-proposed projects with their own scope,
  credentials, and privacy design (email and calendar content is
  materially more sensitive than public RSS news and deserves its own
  charter, not a rider on this one).
- Any new inbound exposure, public endpoint, or notification/push channel
  beyond what already exists for the news digest (LAN/VLAN-70 web page,
  optionally Tailscale, matching the existing pattern) — a push-notification
  or mobile-alert delivery mechanism is a separate later decision, not
  assumed here.
- Building a second, competing news-summarization pipeline. If the
  combined digest needs a different presentation of news content than
  `/digest` already provides, the plan is to extend or read from the
  existing `digest_entries`/audio pipeline, not fork a parallel one.
- Deploying a new LLM/model server. This project reuses `aster-llama`, or
  explicitly renegotiates capacity with the other consumers of it — it does
  not stand up a second inference endpoint.

## Architecture and design decisions

### Open decision requiring Jason's input: where does the combined digest live?

Two real options, deliberately not resolved by this document:

1. **New page/section on the existing news-aggregator LXC 114.** Cheapest
   change: reuses the existing Flask app, database, and `aster-llama` key.
   Works well while news is the only real source. Gets awkward if/when
   email and calendar are added, since LXC 114 was scoped and firewalled
   (`MGMT_ADMIN_HOSTS → 192.168.70.13:8080/tcp`) as a single-purpose news
   reader, and mixing household email/calendar content into that same
   guest, database, and access-control boundary blurs a currently
   clean privacy boundary (public news vs. private household
   communications).
2. **Separate aggregator service** (new LXC on Lab VLAN 70, matching the
   Aster Agent/`aster-llama`/news-aggregator placement precedent) that
   pulls a summary/feed from each source project (news, and later
   email/calendar) over a narrow, source-local read API — mirroring the
   established Aster pattern of "a source-local, least-privilege reader
   publishes a sanitized report; the consuming layer gets no mutation
   authority" (`docs/projects/completed projects/Aster-Sysadmin-Second-Brain.md`,
   `Aster-Forgejo-NetBox-Read-Only.md`). Costs a new guest and a small
   amount of duplicated plumbing now, for a materially cleaner boundary
   once more sources exist.

This document does not pick one. Option 2 is more consistent with this
lab's established data-sensitivity segregation (news is public and low-risk;
email/calendar will not be), but is more expensive today for zero present
benefit, since there is nothing to aggregate from yet. Recommend Jason
decide this at Milestone 1 once the actual near-term plan for an
email/calendar project is clearer, rather than guessing now.

### Source abstraction (applies under either option above)

- Each source (news today; email/calendar/etc. later) publishes a small,
  versioned, sanitized "briefing section" — a short structured record
  (headline/title, short body, optional link, generated-at timestamp,
  source-health flag) rather than raw source data. The combined digest
  assembles whichever sections are currently available and skips any
  section whose source is missing, stale, or erroring, rather than failing
  the whole page.
- "Missing" (project not built yet) and "down" (built, but the health
  check/API call failed or the data is stale) must both degrade the same
  way from the digest's point of view: the section is omitted with a
  visible, honest note (not a broken layout, not a silent gap, not a stale
  cached section presented as current) — matching this lab's
  evidence-over-assumption principle.
- Scheduling should key off the existing news digest's already-tuned
  05:15/17:15 `Etc/GMT+7` timer where practical, rather than introducing a
  second, differently-timed schedule for the same "morning briefing"
  concept — to be revisited once a second real source exists and its own
  natural cadence (e.g. email arrives continuously; calendar is a snapshot)
  is known.

### Reuse, not duplication, of the news component

Whichever placement option is chosen, the combined digest's news section
should read from the existing `digest_entries` table (or a small read-only
view/API in front of it) and the existing `latest.mp3`/`latest.json` audio
artifact, not regenerate summaries independently. This keeps the "Your
News" project as the single owner of news-summarization logic per the lab
ethos's "one declared authority for each fact" principle.

## Privacy and security design

- News content is already public/low-sensitivity; nothing changes there.
- Any future email or calendar source is materially more sensitive
  (personal correspondence, appointments, contacts) and must not be
  designed into this project's architecture as an afterthought. Concretely:
  read-only, least-privilege, source-local credentials for any future
  source (matching the Aster pattern), no shared admin credentials, and no
  requirement for this project to ever hold an email or calendar account's
  own password/OAuth token directly — that belongs to the source project.
- If Option 2 (separate aggregator LXC) is chosen, it should follow the
  same placement convention as Aster Agent/news-aggregator: Lab VLAN 70,
  bearer-authenticated API, Lab-VLAN-only exposure, unprivileged LXC.
- `aster-llama` calls (if the combined digest does any synthesis beyond
  simple assembly, e.g. a one-paragraph "here's your morning" intro) stay
  on the existing same-VLAN, bearer-authenticated endpoint — no new cloud
  LLM dependency.
- No public exposure is proposed. LAN/Tailscale only, matching every other
  personal-dashboard-style service in this lab.

## Pre-start risk assessment

- **Objective and scope:** design and, once authorized, build a combined
  morning digest that starts as a thin wrapper around the existing news
  digest and is architected for future sources. Exclusions: no new source
  projects, no new LLM server, no public exposure, no push notifications.
- **Affected systems:** LXC 114 (if Option 1) or a new Lab VLAN 70 guest (if
  Option 2), and `aster-llama` on LXC 110 as a shared, contended dependency.
  No existing production system is put at risk by this project's own
  scope; the news aggregator's existing `/digest` and audio pipeline are
  read from, not modified, unless Jason picks Option 1 and accepts that
  trade-off explicitly.
- **Confidentiality/secret-handling:** none at proposal stage — no
  credentials exist yet for sources that don't exist yet. This section
  must be revisited in full when an email/calendar source project is
  actually scoped, since that is where real secret-handling risk appears.
- **Availability/integrity/privacy/recovery:** low at this stage, since the
  only real dependency (news digest) already has its own backup/recovery
  coverage. The main real risk this project introduces is **`aster-llama`
  contention** — if the combined digest adds synthesis calls to the same
  shared endpoint used by the news pipeline and Aster, a slow or saturated
  `aster-llama` could delay or fail more than one project's output at once.
  This has not been measured under concurrent load from multiple callers.
- **Irreversible/destructive operations:** none anticipated. No deletion,
  no credential rotation, no firewall broadening beyond what a
  Lab-VLAN-70-pattern new guest would already require (narrow, per
  precedent).
- **Expected auth/firewall/DNS/storage changes:** none if Option 1 and the
  news digest's existing exposure is reused as-is; a new
  `MGMT_ADMIN_HOSTS`-style narrow rule and a NetBox/DNS entry if Option 2 —
  both are the standard, already-precedented pattern, not a new exposure
  class.
- **Recovery checkpoint/rollback/abort:** trivial while this remains a thin
  wrapper — the underlying news digest is unaffected either way, and the
  combined-digest layer itself (a new page or a new guest) can be removed
  without touching the news aggregator or `aster-llama`.
- **Test strategy:** live verification against the real, already-populated
  `digest_entries` table; no synthetic data needed for the news-only
  version. Graceful-degradation behavior (missing/down source) should be
  tested with a deliberately-disabled or unreachable stand-in source once
  more than one source exists.
- **Likely service interruption:** none expected to existing services; a
  bug in a new synthesis call against `aster-llama` could add latency to
  that shared endpoint, detectable via the existing news-aggregator/Aster
  Doctor checks plus a new check for this project (see Milestones).
- **Backup/Doctor/monitoring/NetBox/wiki impacts:** covered per-option in
  the integration checklist below.
- **Unresolved decisions requiring Jason's acceptance before work starts:**
  1. **Placement** (Option 1 vs Option 2 above) — the single biggest open
     decision in this document.
  2. **Whether to build anything now at all**, given there is currently
     only one real source (news) and the combined digest's main value is
     realized once a second source exists. A reasonable alternative is to
     defer implementation entirely until an email or calendar project is
     actually proposed, and keep this document as a proposal-only design
     record until then.
  3. **`aster-llama` capacity planning** across concurrent projects — not
     blocking for a news-only wrapper, but should be revisited before this
     project adds its own synthesis calls on top of the news pipeline's
     existing ones.

## Persistence plan

Not applicable in detail at proposal stage — no implementation has started.
Once Milestone 1 begins, this section should record: current milestone,
completed steps, exact blockers, next safe action, and rollback location, per
the Standard's persistence requirements.

## Milestones

All milestones are proposed and unchecked. None has been started.

### Milestone 1 — Placement decision and requirements

- [ ] Jason decides Option 1 (new page on LXC 114) vs Option 2 (separate
      aggregator LXC), informed by the state of any email/calendar project
      planning at that time.
- [ ] Confirm authorization stream (M or A) for this project specifically.
- [ ] Define the "briefing section" data contract (fields, staleness
      threshold, health-flag semantics) that any future source must
      implement.
- [ ] Decide whether the combined digest gets its own schedule or rides the
      existing 05:15/17:15 news timer.

### Milestone 2 — Minimal viable digest (news-only)

- [ ] Build the chosen placement's minimal combined-digest page/service that
      surfaces the existing news digest content through the new
      "briefing section" contract, with zero duplication of
      summarization logic.
- [ ] Verify live against real `digest_entries` data, not a fixture.

### Milestone 3 — Graceful degradation

- [ ] Implement and test the missing-source and down-source display paths
      using a deliberately disabled/unreachable stand-in source, since a
      real second source does not yet exist.
- [ ] Confirm a source outage never breaks or blanks the whole page — only
      the affected section degrades.

### Milestone 4 — Observability and documentation

- [ ] Add a HomeLab Doctor check appropriate to the chosen placement
      (availability of the combined-digest service itself; a
      staleness/health check per section once more than one source exists).
- [ ] Complete the required integration impact checklist for real.
- [ ] Update Homepage/NetBox/DNS as required by the chosen placement.

### Milestone 5 — Validation and graduation

- [ ] Confirm the news section renders correctly and matches the source
      digest's actual content.
- [ ] Confirm degradation behavior under a real induced failure.
- [ ] Confirm `aster-llama` load from this project (if any synthesis is
      added) does not visibly degrade the news pipeline's own summarization
      timing.
- [ ] Evidence log complete; portfolio README updated (by others, per this
      task's instructions — not edited by this document's author).

## Validation and evaluation

- **Functional:** the news section on the combined digest matches
  `/digest`'s own content for the same run.
- **Failure/regression:** a disabled stand-in source degrades visibly and
  honestly rather than breaking the page; the existing news `/digest` page
  and its Doctor checks show no regression from this project's existence.
- **Performance/capacity:** if this project adds any `aster-llama` calls,
  measure their latency alongside a concurrent real news-digest run to
  surface contention before it becomes a production problem.
- **User workflow:** Jason can reach one page/view for the morning briefing
  instead of navigating to `/digest` directly, with no loss of the content
  he already gets there today.

## Observability and maintenance

- Doctor coverage as defined in Milestone 4, matching the news aggregator's
  own established pattern (enabled-state and freshness checks, not just
  reachability).
- No new alert-notification owner beyond the existing Doctor
  report/`check_news_aggregator()`-style pattern unless a new failure mode
  is identified that existing checks do not cover.

## Backup, restore and rollback

- If Option 1: no new backup surface — already covered by LXC 114's
  whole-guest backup, per the news aggregator project's own established
  and measured backup-impact analysis.
- If Option 2: a new guest needs the same whole-guest Proxmox
  snapshot/off-host backup pattern already used for LXC 104/110/114, sized
  and verified once the guest exists.

## Documentation and systems-of-record updates (required integration impact checklist)

- [ ] **HomeLab Doctor** — to be added in Milestone 4; not applicable yet
      (no implementation exists).
- [ ] **Monitoring/alerting** — covered by the Doctor check above; no
      separate alerting surface planned.
- [ ] **Backup and recovery** — not applicable yet; addressed per-option
      once placement is decided (see above).
- [ ] **NetBox** — not applicable if Option 1 (no new guest/interface); a
      new VirtualMachine/interface/IP entry required if Option 2, following
      the news-aggregator project's own NetBox onboarding steps.
- [ ] **Human wiki** — not applicable, same reasoning as the news
      aggregator project: personal household content, not
      operator/reference documentation.
- [ ] **Aster mirror/snapshot** — not applicable; this project does not
      touch Aster's own knowledge or function set, and any `aster-llama`
      calls it makes go through the same direct path the news aggregator
      already uses, not through Aster itself.
- [ ] **Operational reference and runbooks** — a short "Combined Morning
      Digest" operations note should be added once Milestone 2 exists;
      not applicable at proposal stage.
- [ ] **Repository documentation** — this document, kept current through
      each milestone.
- [ ] **Diagrams/rack records** — not applicable if Option 1; required if
      Option 2 introduces a new guest, matching the news-aggregator
      project's own diagram/topology update.
- [ ] **Homepage/service discovery** — a new or renamed tile once a real
      combined-digest page/service exists; not applicable at proposal
      stage.
- [ ] **Authentication/authorization** — expected to match the news
      aggregator's own decision (network ACL only, no Authentik
      front-end) unless a future sensitive source (email/calendar) changes
      that calculus — to be revisited explicitly when such a source is
      added, not assumed to stay unauthenticated forever.
- [ ] **DNS, certificates and firewall** — not applicable if Option 1 (same
      host/port as today); a narrow `MGMT_ADMIN_HOSTS`-style rule and a
      `news.internal`-style DNS entry required if Option 2, per precedent.
- [ ] **Automation and schedules** — the scheduling decision in Milestone 1
      is the primary automation surface; not applicable until that decision
      is made.
- [ ] **Security inventory** — no new credentials anticipated for the
      news-only version; any future source's credentials belong to that
      source's own project, not this one.

## Graduation criteria

This project graduates when: the placement decision is made and
implemented, the news section reliably mirrors the existing digest with no
duplicated summarization logic, missing/down-source degradation is proven
with a real induced failure (not merely designed on paper), HomeLab Doctor
covers the new surface, and the required integration checklist is closed
with real evidence — genuinely applicable items done, others marked not
applicable with reason.

## Evidence log

No implementation work has occurred; this document is the initial proposal.

## References

- [News Aggregator (MuckScraper) — Phase 1](../completed%20projects/News-Aggregator-MuckScraper.md)
- [News Aggregator Phase 2 — Digest, Sections and Source Requests](../completed%20projects/News-Aggregator-Digest-and-Sections.md)
- [News Aggregator Phase 3 — Audio Digest](../completed%20projects/News-Aggregator-Audio-Digest.md)
- [Aster Sysadmin Second-Brain](../completed%20projects/Aster-Sysadmin-Second-Brain.md) (source-local
  reader / no-mutation-authority pattern referenced above)
- [Aster Forgejo and NetBox Read-Only Integration](../completed%20projects/Aster-Forgejo-NetBox-Read-Only.md)
- [Project Creation Standard](../../Project-Creation-Standard.md)
- [docs/projects/README.md](../README.md) — confirms no Email Triage or
  Calendar PA project currently exists in the portfolio
