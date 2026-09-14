# Aster Mirror Directory-First Retrieval and Scale Evaluation

> Status: Active — Stream A granted 2026-09-13. Milestone 1 baseline complete;
> found real cross-domain retrieval degradation, so the project proceeds to
> Milestone 2 rather than the hard-stop path.
>
> Owner: Jason
>
> Proposed: 2026-09-13
>
> Started: 2026-09-13
>
> Completed: —
>
> Authorization stream: **A — Autonomous**, granted by Jason 2026-09-13 in this
> project's own conversation, per the per-project authorization mechanism in
> `CLAUDE.md`. All changes remain staged, reversible, and pipeline-internal;
> platform/sandbox approval prompts remain mandatory regardless of this grant.

## Purpose and desired outcome

Determine whether flat per-claim retrieval in `aster-knowledge-mirror` has
degraded now that the corpus has scaled to 30 sources and 1,796 entries across
six unrelated domains, and — only if that is actually true — give Aster a way
to narrow to the right source before ranking individual claims, without
weakening the mirror's existing determinism, provenance, or non-authoritative
status. The user-visible outcome is that Aster's answers stay accurate and
correctly sourced as the corpus keeps growing; the directory layer is a means
to that end, not a goal in itself, and is not activated unless measurement
justifies it.

## Current state and evidence

- The graduated mirror is at pipeline `1.4.1`: 30 accepted sources, 1,796
  verified entries, content hash `11e0dee8a518502ef69b94e22331ed4ac9e63cb0e0420a3d2481284c7b35f2b5`.
- Storage is flat: `entries/<source-id>/<content-id>.md` plus five global
  indexes (`assets.json`, `services.json`, `symptoms.json`,
  `dependencies.json`, `provenance.json`). There is no directory- or
  source-level summary layer above individual entries.
- During the original Milestone 3 graduation, two ranking incidents occurred:
  unrelated high-authority results displaced the correct mirror entry from
  Aster's two-result context window, and later, front matter crowded the cited
  claim out of the excerpt. Both were fixed with prompt/ranking patches at the
  time, not with a structural change to retrieval.
- The only existing mirror-vs-complete-source context-reduction evaluation was
  run against a single synthetic fixture (755 vs. 774 characters). It has
  never been run at production scale or across more than one domain.
- Known consumer: Aster's existing snapshot-retrieval path on LXC 104 is the
  sole consumer of the mirror's ranking behavior. No other system reads it.

## Scope and exclusions

### Included

- A cross-domain retrieval evaluation at current production scale, run before
  any pipeline change.
- A deterministic one-line abstract plus bounded topic tags per `source_id`,
  generated only from already-accepted, already-verified entries.
- A new `indexes/directories.json` alongside the existing five indexes.
- A two-stage retrieval change in Aster's existing snapshot consumer
  (directory-first narrowing, then entry ranking within the narrowed set),
  gated behind a proven fallback to today's flat ranking.
- A direct before/after comparison against the Milestone 1 baseline before any
  production activation decision.

### Excluded

- Any change to the collector, intake portal, source manifest, licensing
  model, or accepted-corpus authority.
- Any new Aster tool, credential, or network path.
- Any self-rewriting or autonomously iterated memory — the abstract layer is
  generated deterministically by the existing pipeline discipline.
- Removing or weakening the existing per-claim source-locator verification.
- Public exposure, authentication changes, or firewall/DNS changes.

## Authority model

This project does not change the existing authority order:

1. validated live reports for transient state;
2. adopted systems of record, including NetBox where applicable;
3. reviewed `homelab-reference` current-state pages and runbooks;
4. reviewed operator-authored `homelab-wiki` pages;
5. version-matched vendor/upstream documentation;
6. community material and the generated Aster mirror.

The proposed directory abstract layer sits entirely inside tier 6. It is
generated exclusively from already-verified tier-6 content, carries no
independent fact, and must never be treated as evidence in itself — only as a
routing aid toward the entries that are the actual evidence. A conflict or
gap this layer surfaces (e.g., a query that fits no source well) is reported
and falls back to flat search, never silently resolved.

## Architecture and data flows

No new identity, network path, port, or trust boundary is introduced.

```text
existing flat mirror (LXC 113)         new directory layer (LXC 113)
entries/<source-id>/*.md    ---->     indexes/directories.json
                                        one abstract + topic tags per source_id,
                                        generated in-process during the existing
                                        mirror build step from that source's own
                                        already-verified entries
                                                 |
                                  streamed read-only to Aster (LXC 104),
                                  same path the mirror already uses today
                                                 |
                                   Aster retrieval (two-stage, in-process)
                                                 |
                         1. rank query against directory abstracts
                         2. narrow to top-scoring source(s)
                         3. rank entries within narrowed source(s)
                         4. if inconclusive at step 1 or 2, fall back to
                            today's flat entry-level ranking over all entries
```

Generation happens inside the existing mirror-build process on LXC 113;
consumption happens inside Aster's existing snapshot consumer on LXC 104. No
new service, listener, or outbound call is added anywhere in this flow.

## Privacy and security design

- **Least privilege:** abstract generation runs under the same restricted
  mirror-build identity already used for entry generation; no new identity is
  created.
- **Data minimization:** abstracts are derived only from content that has
  already passed the existing secret/injection lint and provenance
  verification. No new source class, upload path, or raw document is read.
- **Network policy:** unchanged. No new outbound or inbound path.
- **Logging:** the build log records per-source abstract generation and its
  hash, matching the existing mirror build log pattern; no new sensitive
  output is introduced.
- **Public exposure:** none. The wiki, mirror, and Aster remain private and
  internal throughout this project.

## Pre-start risk assessment

- **Objective, scope, exclusions, stream:** as stated above; Stream A
  requested because every change class is staged, reversible, and internal to
  the already-graduated pipeline.
- **Affected systems, users, data, network paths, systems of record:** Jason
  is the only user. Affected systems are limited to the mirror-build process
  on LXC 113 and Aster's retrieval path on LXC 104. No data outside the
  already-accepted corpus is touched. No network path changes. NetBox,
  `homelab-reference`, and the human wiki are not affected.
- **Current versions, dependencies, known consumers:** mirror pipeline
  `1.4.1`; Aster's existing snapshot consumer is the sole consumer of any
  ranking change.
- **Confidentiality and secret-handling risks:** none new — abstracts are
  generated from content that already passed secret/injection screening.
- **Availability, integrity, privacy, recovery risks:** the primary risk is
  that an incorrect or stale directory abstract could cause retrieval to skip
  the correct source entirely — a worse failure mode than today's flat search,
  which considers every entry. This is why Milestone 3 requires a proven
  fallback path before any activation. No new privacy risk, since no new
  source class is introduced.
- **Irreversible or destructive operations:** none. The directory layer is
  additive; flat search is retained as the explicit fallback and is never
  removed.
- **Authentication, firewall, DNS, storage, external-service changes:** none
  of these are touched by this project.
- **Recovery checkpoint, rollback path, abort conditions:** retain the current
  `1.4.1` mirror tree and its hashes, and the currently active Aster snapshot,
  before any change. Abort and do not proceed past Milestone 1 if the baseline
  shows no material degradation at production scale — in that case, record the
  finding and close the project without building the directory layer. Abort
  Milestone 3 if a reliable fallback to flat search cannot be demonstrated.
  Abort Milestone 4 activation if the before/after comparison does not show a
  clear improvement.
- **Test strategy:** synthetic fixtures are needed specifically for failure
  cases that would be unsafe to create in the production corpus — a missing,
  stale, or cross-domain-ambiguous abstract — to prove fallback behavior
  without risking a real retrieval regression.
- **Likely interruption and detection:** none expected beyond the existing
  bounded mirror-build restart pattern already covered by HomeLab Doctor and
  the daily/monthly timers.
- **Backup, Doctor, monitoring, NetBox, wiki/mirror, documentation impacts:**
  see the integration checklist below.
- **Unresolved decisions requiring acceptance before work starts:** whether to
  proceed with building the directory layer (Milestones 2-4) purely as a
  measured comparison even if Milestone 1 shows only marginal degradation, or
  to treat "no material degradation" as a hard stop. This document defaults to
  the hard stop; Jason should confirm or override this at authorization.

## Persistence plan

- **Current milestone:** Milestone 1 complete 2026-09-13; Milestone 2 not
  started.
- **Last verified state:** a 10-question cross-domain retrieval-precision
  baseline was run read-only against the live production mirror (1,796
  entries, tree unmodified) via `search_knowledge()`, Aster's actual ranking
  function. No mirror content, Aster configuration, or Aster snapshot was
  changed.
- **Next safe action:** review the Milestone 1 findings below, then begin
  Milestone 2 (directory abstract generator), which is additive and does not
  touch the deployed snapshot until a later, separately gated activation.
- **Rollback location:** the currently deployed `1.4.1` mirror tree and active
  Aster snapshot are the rollback target for every later milestone; their
  exact hashes are recorded in the Production Corpus Expansion evidence log
  and are not altered by this project until an explicit accepted milestone.
- Implementation will reuse the existing mirror pipeline's schema-versioned
  state and content-hash keying for idempotence — the directory-abstract
  generator is keyed by the same per-source content hash already used for
  entry generation, so a resumed or repeated run reuses unchanged abstracts
  rather than regenerating them.

## Milestones

### Milestone 1 — Baseline measurement at production scale — **complete 2026-09-13**

- [x] Design a cross-domain question set spanning ARR/media, Home Assistant,
      networking, storage, power and camera topics, including at least one
      question per domain with a plausible near-miss in another domain.
      **Result:** 10 questions grounded in the real accepted source list (read
      read-only from the live mirror's `entries/` and `indexes/` on LXC 113,
      no state changed), with near-miss pairs confirmed to genuinely share
      vocabulary in this corpus (certificate: NPM/Authentik vs SABnzbd;
      backup: OPNsense/Grafana vs SABnzbd; notification: Home Assistant vs
      Sonarr/Radarr/Lidarr/Prowlarr/Grafana/Prometheus; power: the existing
      synthetic-ups-manual vs real nut-docs pairing). Two questions
      (TrueNAS/Frigate) had no textual overlap found in this corpus and were
      kept as scale-only control cases rather than forced near-misses.
- [x] Run a retrieval-precision measurement against the live production
      mirror at current scale. **Scope note:** this ran Aster's actual
      `search_knowledge()` ranking function read-only against the real,
      unmodified 1,796-entry mirror (copied read-only for offline
      measurement; nothing on LXC 104/113 was changed), rather than the full
      `compare_mirror.py` LLM-answer comparison — the llama.cpp/Aster-agent
      hosts (192.168.70.10, .12) have no configured SSH path and no sandbox
      hostname entry, so end-to-end answer generation is deferred; the ranking
      layer is what determines precision and is what Milestones 2-4 would
      change, so it is the right layer to baseline first.
- [x] Record context size, precision, and misranking. **Result (10
      questions, 9 valid — one question had two legitimately correct
      candidate sources and was excluded as a bad test rather than a
      finding):** 7/9 correct at top rank. Two real problems found: (1) an
      OPNsense backup-schedule question was outranked by SABnzbd's own backup
      docs, with the correct source only reaching rank 3 of 5; (2) a
      Sonarr-notification question returned Grafana's notification docs at
      rank 1 with Sonarr absent from the top 5 entirely, despite "Sonarr"
      being named explicitly in the question. A third, structurally different
      issue was found: a Home-Assistant-phrased query triggered an existing
      hand-tuned regex shortcut in `search_knowledge()` (`focused_ha_reference`)
      that forces retrieval to a single non-mirror reference file and returned
      zero mirror results — in the live deployed snapshot this file exists, so
      the practical effect is that such queries never reach the 1,796-entry
      mirror at all, independent of corpus scale. Mean context size across the
      10 queries was ~4,125 characters at `max_results=5`.

Gate: **passed.** The baseline is dated, reproducible (harness and question
set retained in this evidence log), and shows real degradation at production
scale — a genuine cross-domain miss, a genuine misranking, and a
scale-independent retrieval-routing gap. The hard-stop-if-no-degradation
condition does not apply; Milestone 2 is authorized to proceed.

### Milestone 2 — Directory abstract generation

- [ ] Add a deterministic per-`source_id` abstract generator (one sentence
      plus bounded topic tags) reading only already-accepted, already-verified
      entries for that source.
- [ ] Add `indexes/directories.json` alongside the existing global indexes.
- [ ] Require build-twice identical hashes before publication, matching the
      existing mirror determinism guarantee.
- [ ] Add regressions for a sparse-entry source, a multi-domain source, and a
      source added after the index was built.

Gate: the directory index is deterministic, reproducible, and independently
verifiable against its source entries, with no new authority claim.

### Milestone 3 — Two-stage retrieval integration

- [ ] Add directory-first ranking ahead of entry-level ranking in Aster's
      existing snapshot consumer, gated behind an explicit fallback path.
- [ ] Prove with synthetic fixtures that a missing, stale, or wrong abstract
      falls back to today's flat entry-level search rather than returning
      nothing or the wrong source silently.
- [ ] Re-run the existing critical/adversarial evaluation suite (poisoned
      sources, conflicting authorities, secret refusal, missing evidence) to
      confirm the two-stage path does not change safety behavior.

Gate: two-stage retrieval activates only behind a proven fallback, and every
existing safety and adversarial case still passes.

### Milestone 4 — Comparative evaluation and regression

- [ ] Repeat the Milestone 1 question set against the two-stage path on the
      same snapshot generation, compared directly against the baseline.
- [ ] Re-run the general, ARR and Home Assistant regression suites.
- [ ] Document the outcome plainly, including a "no material improvement"
      finding if that is what the numbers show.

Gate: production activation, if any, is justified by a direct before/after
comparison rather than architectural preference alone.

### Milestone 5 — Recovery, observability and graduation

- [ ] Verify the retained `1.4.1` mirror and pre-change Aster snapshot remain
      recoverable and are exercised in an isolated restore test.
- [ ] Extend monthly corpus health to flag a directory abstract that has
      drifted from its source's current entries, only if the feature activates.
- [ ] Record final decision (activated / not activated), exact accepted
      hashes, and residual limitations in the evidence log.

Gate: the outcome is recoverable either way, monitored going forward if
activated, and documented with dated evidence.

## Validation and evaluation

- Functional: two-stage retrieval must match or improve precision against the
  Milestone 1 baseline on the same question set.
- Least-privilege / denied-action: the abstract generator must be proven
  unable to read unaccepted or unverified content — a direct regression.
- Malformed, missing, stale, adversarial inputs: covered by Milestone 3's
  synthetic fixtures.
- Restart/interrupted-run behavior: abstract generation must be idempotent and
  resumable, matching the existing pipeline's checkpoint discipline.
- Rollback to prior accepted state: exercised in Milestone 5.
- Backup integrity and isolated restore: proportional to the change — restore
  the retained `1.4.1` tree in isolation and confirm it serves correctly.
- Secret-pattern review: abstracts pass through the same existing
  secret/injection lint as every other mirror artifact; no new bypass.
- Performance/capacity: measure retrieval latency before and after in
  Milestone 4, not just context size.
- Doctor/monitoring behavior in success and failure: exercised once the
  feature activates.
- Regression of dependent Aster curricula: general, ARR, and Home Assistant
  suites re-run in Milestone 4.
- Two independent production-path passes: the Milestone 4 comparison is run
  twice against the identical snapshot, matching the existing evaluation
  discipline used throughout the corpus expansion project.

## Observability and maintenance

- No new Doctor check, alert, or schedule is added unless Milestone 4
  justifies activation.
- If activated: add a Doctor check for directory-index staleness relative to
  its source's current entries, and extend the existing monthly corpus-health
  job to flag drift, following the same pattern already used for stale
  sources and broken links.
- Alert ownership remains Jason, through the existing Doctor/monitoring
  channels; no new notification surface is introduced.

## Backup, restore and rollback

- **Protected components:** the current `1.4.1` mirror tree, its
  accepted-input and content hashes, and the currently active Aster snapshot,
  retained unchanged before any milestone begins.
- **Retention:** the pre-project `1.4.1` state is retained at minimum until
  Milestone 5's graduation decision is recorded, matching the existing
  last-good retention pattern used throughout the corpus expansion project.
- **Isolated restore proof:** Milestone 5 loads the retained `1.4.1` tree in
  an isolated environment and confirms it serves the existing evaluation
  fixtures correctly, independent of any directory-layer change.
- **Last-known-good path:** with the two-stage flag off, behavior is
  identical to today's flat retrieval — no corpus or snapshot change is
  required to roll back.

## Documentation and systems-of-record updates

- [ ] **HomeLab Doctor:** not applicable at proposal; add a directory-index
  freshness check only if Milestone 5 activates the feature.
- [ ] **Monitoring/alerting:** not applicable unless activated; reuses
  existing daily/monthly reporting with no new alert surface otherwise.
- [ ] **Backup and recovery:** the retained `1.4.1` tree and snapshot are
  already covered by existing backup jobs; no new backup target required.
- [ ] **NetBox:** not applicable — no new asset, VM, or service.
- [ ] **Human wiki:** not applicable — this project touches only the generated
  mirror and Aster's retrieval path, not the human-authored corpus.
- [ ] **Aster mirror/snapshot:** primary target of this project; update
  mirror architecture documentation once the graduation decision is recorded.
- [ ] **Operational reference/runbooks:** update the mirror architecture note
  in `homelab-reference` only if Milestone 5 activates the feature.
- [ ] **Repository documentation:** update the project portfolio and
  changelog on completion regardless of outcome.
- [ ] **Diagrams/rack records:** not applicable — no physical topology, rack,
  cable, or power change.
- [ ] **Homepage/service discovery:** not applicable — no new service surface;
  the existing authenticated portal link is unchanged.
- [ ] **Authentication/authorization:** not applicable — no new identity,
  role, or auth boundary is introduced.
- [ ] **DNS, certificates and firewall:** not applicable — no new network
  path; the entire change is internal to the existing LXC 113/104 pipeline.
- [ ] **Automation and schedules:** no new schedule; abstract generation runs
  inside the existing mirror build step. Extend the monthly health job only
  if the feature activates.
- [ ] **Security inventory:** no new secret, credential, or network path is
  introduced at any milestone.

## Graduation criteria

The project graduates only when:

- the Milestone 1 baseline is dated, reproducible, and independent of any
  pipeline change made afterward;
- if built, the directory index is as deterministic and independently
  verifiable as every other mirror artifact, with no new authority claim;
- the fallback to flat entry-level search is proven before any two-stage
  activation, including for missing, stale, and wrong-abstract cases;
- the Milestone 4 before/after comparison — run twice on the identical
  snapshot — directly justifies the final activation decision, whichever way
  it goes;
- every existing general, ARR, Home Assistant, and adversarial regression
  suite still passes;
- rollback to the retained `1.4.1` state is proven regardless of outcome;
- Doctor and monitoring coverage is extended only if the feature is activated,
  and is not left partially wired otherwise; and
- the final decision, exact hashes, and residual limitations are recorded in
  the evidence log and close-out.

## Evidence log

| Date | Milestone | Evidence | Result |
|---|---|---|---|
| 2026-09-13 | Proposal | Reviewed OpenViking's directory-first/tiered retrieval model against the graduated Aster mirror's flat structure and the two unresolved ranking incidents from its original graduation; identified that the mirror-vs-complete-source evaluation has never been run at production scale or across domains | Proposed a measure-first, activate-only-if-justified project; no source was enrolled and no system was modified |
| 2026-09-13 | Authorization | Jason granted Stream A for this project explicitly in-conversation, per `CLAUDE.md`'s per-project authorization mechanism | Milestone 1 begun the same day |
| 2026-09-13 | 1 baseline measurement | Confirmed no sandbox network path exists from this Claude Code session to the Aster agent, llama.cpp, or Aster Wiki hosts (no SSH alias, no sandbox hostname entry, IP-based HTTP(S) blocked by the sandbox proxy — consistent with the prior Authentik-project finding); per-command sandbox bypass was used only for read-only discovery and a read-only copy of the live mirror tree, both live-approved. Read-only SSH confirmed root access to Aster Wiki LXC 113; the deployed mirror (`/var/lib/aster-wiki/aster-knowledge-mirror`, 1,796 entries, 8.1 MB) was copied read-only to an isolated session scratch directory for offline measurement — nothing on LXC 104/113 was changed. No SSH path exists to the Aster agent host (LXC 104, `192.168.70.10`) at all (`Permission denied`), so the full LLM-answer `compare_mirror.py` comparison could not run; a 10-question cross-domain retrieval-precision harness was built instead, calling Aster's actual unmodified `search_knowledge()` function (extracted verbatim from `services/aster-agent/aster_agent.py` to avoid needing its unrelated `fastapi`/`httpx` runtime dependencies, which are not installable at the pinned versions from this Mac's network) against the real corpus | 7/9 valid questions correct at top rank (one question excluded as a flawed test — both candidate sources were legitimately correct). Two genuine retrieval problems found: OPNsense backup docs outranked by SABnzbd's own backup docs (correct source present at rank 3, not rank 1); a Sonarr-notification question returned Grafana notification docs at rank 1 with Sonarr entirely absent from the top 5. A third, scale-independent issue: a Home-Assistant-phrased query triggers an existing hardcoded `search_knowledge()` shortcut that bypasses the mirror entirely in favor of a single reference file. Milestone 1's gate passed — real degradation was found, so the hard-stop condition does not apply and Milestone 2 is authorized |

## Close-out

To be completed at graduation. Will record: whether the directory layer was
activated in production or the project closed at the Milestone 1 hard stop;
final architecture as deployed (or explicit confirmation that no architecture
change was made); ownership (Jason); recovery references (retained `1.4.1`
tree and snapshot location, or the final accepted tree if superseded); and any
deliberately deferred follow-on work, such as extending the directory layer to
sub-source topic clustering if a future corpus scale-up reopens the question.
