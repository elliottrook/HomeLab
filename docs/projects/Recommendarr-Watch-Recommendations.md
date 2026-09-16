# Recommendarr Watch Recommendations Project

> Status: Proposed — not yet authorized
>
> Project owner: Jason
>
> Proposed: 2026-09-15
>
> Authorization stream: not yet selected — Stream M or Stream A to be chosen
> by Jason before implementation begins

## Purpose and desired outcome

Generate household-relevant watch recommendations ("you might like X because
you finished Y") from the existing media library's own metadata and watch
state, using local LLM reasoning, surfaced through a small private view or
Homepage card. This is a read-only, advisory feature: it suggests, it does not
add anything to Sonarr/Radarr or change library state on its own.

## Current state and evidence — including one correction to the brief

The originating brainstorm described this as drawing from "Sonarr/Radarr/
Jellyfin/Plex." That is stale: per the completed
[Plex-to-Jellyfin Media Migration](<completed projects/Plex-to-Jellyfin-Media-Migration.md>)
(closed 2026-09-01), Plex's source media was deleted with Jason's explicit
approval and Plex is confirmed **stopped**. The current authoritative service
inventory, `docs/reference/ARR-Stack-Operational-Reference.md` (reviewed 2026-09-09),
lists only Sonarr, Radarr, Lidarr, Prowlarr, SABnzbd and Jellyfin as the
current Docker-hosted media stack on TrueNAS (`192.168.20.40`) — Plex is not
in it. This project therefore sources recommendations from **Jellyfin**
(library catalog and watch/played state) and **Sonarr/Radarr** (monitored/
available catalog, not download or queue internals), not Plex. Flagging this
here rather than silently rewriting the brainstorm elsewhere, per the
project standard's evidence-over-assumption and drift-reporting principles.

Other confirmed facts this proposal relies on:

- Sonarr `4.0.19.2979`, Radarr `6.3.0.10514`, Jellyfin `10.11.11` — versions
  per the ARR operational reference, all Docker containers on TrueNAS,
  host-published ports (Sonarr 8989, Radarr 7878, Jellyfin 8096).
- Aster already has a working precedent for exactly this class of source:
  a source-local, least-privilege reader on TrueNAS produces a sanitized,
  schema-validated aggregate report every five minutes (TrueNAS Cron Job 5)
  for Aster's ARR curriculum. That report **deliberately excludes media
  titles, artist/album/movie/show names** and all download/queue identifiers
  — it was scoped for health/queue advisory use, not recommendations.
  Recommendations are only useful with titles and genres, so this project
  cannot simply consume the existing ARR health report; it needs its own
  reader with a different, wider sanitization boundary (see Scope and
  Architecture below), reviewed on its own terms rather than assumed safe by
  association with the existing one.
- A shared local LLM inference endpoint already exists:
  `aster-llama.service` on LXC 110 (`192.168.70.12:11435`, OpenAI-compatible
  `/v1`, Qwen3.8 27B `UD-IQ4_XS`, bearer-authenticated, Lab VLAN 70 only). It
  already serves Aster Agent and MuckScraper's summarizer/digest narration on
  dedicated per-consumer keys.
- "Recommendarr" is also the name of an existing open-source self-hosted
  project (a web app that connects directly to Sonarr/Radarr/Jellyfin/Plex/
  Tautulli APIs and an OpenAI-compatible LLM to generate recommendations).
  Whether Jason intends to deploy that specific upstream project or wants a
  lab-pattern-conformant bespoke build under the same name is an **open
  decision** (see Architecture and Pre-start risk assessment) — this document
  does not assume either answer.

## Scope

- Read sanitized library catalog and watch-state facts from Jellyfin (titles,
  genres, watched/unwatched/in-progress, ratings if present) and Sonarr/Radarr
  (monitored/available titles, not queue or download internals).
- Generate natural-language recommendations via the existing `aster-llama`
  endpoint (or a documented alternative if capacity doesn't allow reuse — see
  risk assessment) using a dedicated least-privilege bearer key.
- Present recommendations through a small private web view and/or a Homepage
  card, Lab VLAN 70 only, matching the MuckScraper precedent for a new
  unprivileged consumer LXC.
- Decide and record, explicitly, whether the upstream open-source
  "Recommendarr" project is adopted as-is or whether a bespoke reader +
  consumer is built following the lab's sanitized-reader pattern (see
  Architecture).

## Out of scope

- Any Plex integration or dependency — Plex is retired as a media source.
- Automatically adding recommended titles to Sonarr/Radarr, changing
  monitoring state, or triggering any acquisition. A future "add to
  watchlist" action would need its own explicitly-approved broker, mirroring
  the Aster ARR execution-broker pattern (dry-run-only, credential-isolated,
  separately gated) — not part of this proposal.
- Deep per-user viewing-behavior profiling beyond what generating a
  recommendation actually requires (see Privacy and security design — this is
  an explicit open decision, not resolved here, since it touches other
  household members' data, not just Jason's).
- Any change to the existing Aster ARR curriculum, its sanitized health
  report, or its execution broker.
- Lidarr/music recommendations — the brief scopes this to watch
  recommendations (TV/movies); music is explicitly a different, already
  separately-projected space (see the Music Playlist Acquisition Bridge
  project) and is not folded in here.

## Authority model

- **Jellyfin** and **Sonarr/Radarr** remain the sole authority for library
  catalog and watch-state facts. This project reads a sanitized derived copy;
  it never treats its own report as more current than the source, and a
  report/source mismatch is reported as drift, not silently resolved.
- **The new sanitized library-metadata reader** (source-local, on TrueNAS,
  matching the ARR reader precedent) is the sole authority for what this
  project's consumer may see — it defines the sanitization boundary, not the
  consumer app.
- **`aster-llama`** is a shared inference utility only. It returns
  recommendation text; it has no direct access to Sonarr/Radarr/Jellyfin and
  cannot request additional fields beyond what the reader already published.
- **This project document** owns the recommendation-specific design, risk
  acceptance and milestone evidence, independent of the Aster ARR project's
  own document.

## Architecture and data flows (proposed)

```
[Jellyfin catalog + watch state]   [Sonarr/Radarr monitored/available catalog]
        |  read-only, least-privilege API key (new, scoped narrower than
        |  the ARR health reader's key — recommendation reader needs
        |  titles/genres, still no queue/download/credential fields)
        v
[Source-local sanitized reader, TrueNAS, new schema distinct from
 the existing ARR health/queue report]
        |  schema-validated JSON, no credentials, no per-user PII beyond
        |  what personalization scope (below) requires
        v
[Recommendation consumer, new unprivileged LXC, Lab VLAN 70]
        |  bearer-authed HTTPS, dedicated least-privilege key
        v
[aster-llama /v1, LXC 110]
        |  recommendation text
        v
[Private web view / Homepage card, Lab VLAN 70 only]
```

**Open architecture decision — adopt upstream "Recommendarr" vs. build
bespoke:** the existing open-source Recommendarr project would be faster to
stand up, but its documented design connects directly to Sonarr/Radarr/
Jellyfin using their real API keys and calls an LLM endpoint itself — i.e., a
third-party codebase holding direct credentialed access to production media
services, which conflicts with this lab's established least-privilege,
source-local-reader pattern (used for Aster's ARR, Home Assistant and
Forgejo/NetBox integrations). Options, neither pre-selected here:

1. **Adopt upstream Recommendarr**, reviewed for supply-chain/credential
   handling first, and configured with its own scoped read-only keys rather
   than admin keys — faster, but requires trusting and periodically updating
   third-party code with direct API reach into Sonarr/Radarr/Jellyfin.
2. **Build bespoke**, following the reader/consumer split above — matches
   every other AI-touching lab integration, keeps Sonarr/Radarr/Jellyfin
   credentials entirely out of the consumer/LLM path, but is more build work
   and starts from a smaller feature set than the mature upstream project.

This is recorded as an **open decision requiring Jason's input**, not resolved
by this document.

**Open decision — personalization scope:** does this recommend at the
household level (one shared list from aggregate watch state) or per Jellyfin
user? Per-user personalization requires reading and reasoning over individual
family members' viewing history, which is a real privacy question about other
people's data, not just Jason's — flagged for explicit acceptance before
Milestone 3, not assumed.

**Open decision — capacity:** does `aster-llama` have headroom for a fourth
consumer class (recommendations, alongside Aster chat, MuckScraper, and the
proposed Home Assistant voice project) without degrading latency for the
others? Not measured. If recommendations are generated in a low-frequency
batch (e.g. nightly, like MuckScraper's twice-daily digest) rather than
interactively, contention risk is much lower than an interactive voice
use — worth deciding the refresh cadence explicitly rather than defaulting to
on-demand generation.

## Privacy and security design

- The recommendation reader's Sonarr/Radarr/Jellyfin API keys are read-only,
  newly minted, and scoped as narrowly as each product's permission model
  allows; they are never given to the LLM-facing consumer or to `aster-llama`.
- The consumer's `aster-llama` access uses its own dedicated bearer key,
  distinct from Aster's and MuckScraper's, so a compromise of one consumer
  cannot reach another's key or conversation history.
- No credential, download history, queue identifier or raw API response
  leaves the sanitized reader's schema — titles/genres/watch-status are
  included because the feature requires them (a wider boundary than the ARR
  health report, and explicitly reviewed as such, not silently inherited).
- Default to household-level aggregate recommendations unless Jason
  explicitly accepts the per-user personalization tradeoff for the whole
  household, given it involves other people's viewing data.
- No public exposure; Lab VLAN 70 only, matching every other AI-touching lab
  service.
- If upstream Recommendarr is adopted, its outbound network configuration
  must be pinned to only `aster-llama`'s endpoint (no default cloud LLM
  provider left configured) before any real library data reaches it.

## Pre-start risk assessment

**Objective/scope/stream:** as defined above; stream not yet chosen.

**Affected systems:** Jellyfin, Sonarr, Radarr (TrueNAS, `192.168.20.40`);
`aster-llama` (LXC 110, Lab VLAN 70); a new consumer LXC (Lab VLAN 70,
address to be assigned by NetBox — tentatively the next available Lab VLAN 70
address after LXC 114, not yet reserved); household members' aggregate or
per-user watch history depending on the personalization decision.

**Current versions/dependencies:** Sonarr `4.0.19.2979`, Radarr `6.3.0.10514`,
Jellyfin `10.11.11` per the 2026-09-09 ARR operational reference — reconfirm
live before implementation, since this document performs no new discovery.

**Confidentiality/secret-handling risks:** three new credentials minted (a
read-only Sonarr/Radarr/Jellyfin key set for the reader, a bearer key for the
consumer-to-`aster-llama` path, and — if adopted — upstream Recommendarr's own
credential store). All must follow existing root-owned/group-readable,
never-in-Git handling. If upstream Recommendarr is adopted, review how it
stores its configured API keys at rest before trusting it with real ones.

**Availability/integrity/privacy/recovery risks:**
- Per-user personalization would let an LLM (even a local one) surface one
  family member's viewing habits in a shared household-visible
  recommendation view — a real intra-household privacy consideration, not
  just an external-exposure one. Open decision, not resolved here.
- A fourth concurrent `aster-llama` consumer could degrade latency for Aster,
  MuckScraper and (if built) the Home Assistant voice project. Mitigated if
  recommendations are generated on a batch cadence rather than interactively;
  not yet decided.
- If upstream Recommendarr is adopted, it is untrusted third-party code
  gaining direct API reach into production Sonarr/Radarr/Jellyfin — a
  materially different risk profile than the lab's usual sanitized-reader
  pattern, and worth a deliberate accept/reject decision rather than default
  adoption purely because the name matches the brainstormed project.

**Irreversible/destructive operations:** none anticipated. The reader is
read-only by design; the consumer has no write path to Sonarr/Radarr/Jellyfin.
Rollback is stopping the consumer/reader and revoking the minted keys.

**Expected authentication/firewall/DNS/storage/external-service changes:**
new read-only API keys on Sonarr/Radarr/Jellyfin; a new bearer key for
`aster-llama`; a new Lab-VLAN-70 LXC and its NetBox/DNS record; no new
inbound firewall path expected beyond what Lab VLAN 70 consumers already have
to reach TrueNAS and LXC 110 for read-only API calls.

**Recovery checkpoint/rollback/abort:** no source-system state changes to
checkpoint (read-only). Rollback is deleting the new LXC and revoking its
keys; Sonarr/Radarr/Jellyfin/`aster-llama` are unaffected either way.

**Test strategy:** synthetic/sample library metadata for early development
before pointing at the real sanitized reader, to avoid iterating against
production Jellyfin/Sonarr/Radarr during build-out.

**Likely service interruption:** none to Jellyfin/Sonarr/Radarr; a broken
reader or consumer simply produces stale/absent recommendations, which should
fail closed (no recommendation shown / clearly marked stale) rather than
serving fabricated suggestions.

**Backup/Doctor/monitoring/NetBox/wiki impacts:** see the integration
checklist below.

**Unresolved decisions requiring Jason's acceptance before work starts:**

1. Adopt upstream open-source Recommendarr, or build bespoke on the lab's
   sanitized-reader pattern?
2. Household-aggregate or per-user personalized recommendations?
3. Batch/scheduled generation (lower `aster-llama` contention) or on-demand
   interactive generation?
4. Confirm `aster-llama` capacity headroom before committing to reuse it, or
   accept the shared-capacity risk and measure after the fact?
5. New consumer LXC number/address — to be reserved in NetBox at
   implementation time, not pre-assigned by this document.

## Persistence plan

This document is the durable checkpoint. No implementation state exists yet.
On resume: re-read this document, the current ARR operational reference and
`docs/reference/Aster-Operations.md` for any drift since 2026-09-15, confirm no open
decision above has been silently assumed, and continue from the last checked
milestone box.

## Milestones

- [ ] **M1 — Discovery and requirements.** Confirm live Sonarr/Radarr/Jellyfin
  versions and available read-only API scopes; confirm Jellyfin's watch-state/
  "next up" data actually exposes what's needed at the chosen personalization
  granularity; measure `aster-llama` capacity headroom; evaluate upstream
  Recommendarr's actual credential-handling and LLM-endpoint configurability
  firsthand (read its documentation/source) before recommending adopt vs.
  build to Jason.
- [ ] **M2 — Architecture and risk acceptance.** Resolve the open decisions
  above with Jason; present the pre-start risk assessment; Jason accepts it
  and selects Stream M or Stream A.
- [ ] **M3 — Sanitized library-metadata reader.** Build and deploy the
  source-local, least-privilege, schema-validated reader (or, if adopting
  upstream Recommendarr, scope and mint its read-only keys and pin its
  outbound LLM configuration to `aster-llama` only).
- [ ] **M4 — Recommendation consumer.** Deploy the new Lab VLAN 70 LXC (or
  the reviewed upstream app), wire it to the reader's report and to
  `aster-llama` via its own dedicated key, and produce a first real
  recommendation list against sanitized production data.
- [ ] **M5 — UI and validation.** Private web view and/or Homepage card;
  functional, adversarial, regression (shared-`aster-llama`-consumer latency)
  and rollback testing.
- [ ] **M6 — Observability, backup, documentation and graduation.** Close the
  integration checklist below, record final architecture and accepted
  limitations, and move this document to `completed projects/` only once the
  graduation criteria pass.

## Validation and evaluation

- Functional: recommendations are plausible, reference titles that actually
  exist in the sanitized report, and clearly label staleness if the report
  ages out.
- Least-privilege: the reader's keys cannot write; the consumer cannot reach
  Sonarr/Radarr/Jellyfin directly at all, only the reader's published report.
- Adversarial: a crafted/unusual library metadata entry (e.g. an
  unusually-formatted title) does not cause prompt injection into
  recommendation output that leaks reader internals or fabricates false
  library claims.
- Regression: existing Aster ARR curriculum, MuckScraper and (if built) Home
  Assistant voice latency/correctness are re-tested after adding this
  consumer to `aster-llama`.
- Rollback: stopping the consumer/reader and revoking keys leaves Sonarr/
  Radarr/Jellyfin fully unaffected, with no residual credential.
- Two independent production-path passes for the AI-mediated recommendation
  output, per the standard's baseline for AI-mediated behavior.

## Observability and maintenance

- Add a HomeLab Doctor check for reader freshness/report age and consumer
  service health, following the `check_news_aggregator` pattern (audio/report
  staleness detection) rather than inventing a new alerting style.
- No secret-bearing output in any check.

## Backup, restore and rollback

- The new reader's configuration and the consumer LXC's application state
  join the standard Proxmox/TrueNAS archive plus off-site copy pattern
  (`docs/05-Backups.md`), sized and scheduled like the comparable MuckScraper
  LXC 114 rather than assumed to need the larger LXC 110 model-archive
  treatment.
- No database of consequence is anticipated beyond cached report/
  recommendation state, which is regenerable from source and does not need
  irreplaceable-data-grade protection — confirm this assumption once actual
  storage needs are known in M3/M4.
- Rollback path: stop the consumer and reader services; delete the LXC if
  fully rolled back; revoke all minted keys.

## Documentation and systems-of-record updates (required integration checklist)

- [ ] **HomeLab Doctor** — add reader freshness and consumer-service health
  checks; no change to existing ARR health-report checks.
- [ ] **Monitoring/alerting** — decide whether Doctor alone suffices (likely,
  given this is a low-stakes advisory feature) or whether it needs its own
  Prometheus/Grafana panel; avoid duplicating the existing ARR queue/health
  dashboards.
- [ ] **Backup and recovery** — cover the new reader configuration and
  consumer LXC per the pattern above; no new credential store beyond the
  minted keys, recorded by location/rotation owner only.
- [ ] **NetBox** — reserve and record the new consumer LXC's address, VLAN
  and service once a number is assigned; not applicable until implementation.
- [ ] **Human wiki** — add a short operator page: what the feature does, its
  read-only/no-auto-add boundary, and how to disable it.
- [ ] **Aster mirror/snapshot** — not applicable in the usual sense; this
  project does not add Aster capability. If Jason later wants Aster itself to
  be able to *discuss* recommendations conversationally, that is a separate,
  explicitly scoped extension, not assumed here.
- [ ] **Operational reference and runbooks** — extend
  `docs/reference/ARR-Stack-Operational-Reference.md` only if the new reader changes
  any current-state fact about Sonarr/Radarr/Jellyfin's read access; otherwise
  add a dedicated operations note for the new reader/consumer, keeping the ARR
  reference's own excluded-fields boundary (no titles) intact and unchanged.
- [ ] **Repository documentation** — update `docs/01-Architecture.md` and
  `docs/02-IP-Addressing.md` once the consumer LXC is provisioned; correct any
  other stale Plex-as-active-source reference encountered along the way,
  consistent with fixing stale docs on sight.
- [ ] **Diagrams/rack records** — not applicable; no new physical hardware,
  only a new LXC guest.
- [ ] **Homepage/service discovery** — add a private card linking to the
  recommendation view once it exists; no credentials embedded in the card
  configuration.
- [ ] **Authentication/authorization** — decide whether the private web view
  needs its own login or relies on Lab-VLAN-only network exposure, matching
  how MuckScraper's news view is currently exposed; do not default to a new
  Authentik application unless the exposure model requires one.
- [ ] **DNS, certificates and firewall** — narrow read-only API access rules
  for the new reader; no new inbound path from outside the Lab VLAN.
- [ ] **Automation and schedules** — if batch-cadence generation is chosen,
  document the schedule owner, missed-run behavior and concurrency guard,
  matching the existing TrueNAS Cron Job pattern rather than a bespoke
  scheduler.
- [ ] **Security inventory** — record the three new credentials' existence,
  storage location and rotation owner; confirm none of them can reach beyond
  their documented scope during M5 validation.

## Graduation criteria

All milestones complete with recorded evidence; the adopt-vs-build decision is
recorded with its accepted tradeoffs; the personalization-scope decision is
recorded as explicitly accepted by Jason; no Sonarr/Radarr/Jellyfin credential
reaches the LLM-facing consumer; regression on other `aster-llama` consumers
passes; backup and rollback are proven; the integration checklist above is
closed or marked not applicable with reason.

## Evidence log

No implementation work has occurred; this document is the initial proposal.

## Close-out

Not applicable yet — this project has not started.

## References

- `docs/Project-Creation-Standard.md` — lab ethos, authorization streams, risk
  assessment and template requirements this document follows.
- `docs/reference/ARR-Stack-Operational-Reference.md` — current authoritative media
  stack inventory, versions and the existing ARR sanitized-reader precedent
  this project extends rather than duplicates.
- `docs/projects/completed projects/Plex-to-Jellyfin-Media-Migration.md` —
  source for the Plex-retirement correction in this document's Current state
  section.
- `docs/projects/completed projects/Aster-Arr-Stack-Manager.md` — the
  source-local reader / sanitized-report / execution-broker pattern this
  project's architecture follows.
- `docs/reference/Aster-Operations.md` — `aster-llama.service` endpoint and key-handling
  reference.
- `docs/projects/completed projects/News-Aggregator-MuckScraper.md` — the
  most recent precedent for a new unprivileged Lab VLAN 70 consumer LXC using
  a dedicated `aster-llama` key.
