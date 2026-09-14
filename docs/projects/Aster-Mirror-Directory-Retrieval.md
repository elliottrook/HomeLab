# Aster Mirror Directory-First Retrieval and Scale Evaluation

> Status: Active — Stream A granted 2026-09-13. Milestones 1 and 2 complete
> 2026-09-13. Milestone 3 (directory-first retrieval, opt-in, fallback
> proven) and Milestone 4's retrieval-ranking comparison (8/10 vs. 6/10 on
> the real corpus, zero regressions) are complete as of 2026-09-14, but both
> milestones share one unmet item each: the live adversarial suite (M3) and
> the general/ARR/Home-Assistant regression suites (M4) could not run from
> this session — no network path exists from this Claude Code session to
> the Aster/llama.cpp hosts. **Do not activate `directory_first` in
> production on the current evidence alone** — this is carried forward as
> the explicit next safe action, to run from a host with real access.
> `directory_first` defaults off; nothing is deployed or activated in
> production.
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

- **Current milestone:** Milestones 1-2 complete 2026-09-13. Milestone 3 and
  Milestone 4's first/third checklist items complete 2026-09-14; both
  milestones have exactly one unmet item, and it is the same underlying gap
  for both: no live evaluation suite could be run from this session.
- **Last verified state:** `search_knowledge()` in
  `services/aster-agent/aster_agent.py` has an opt-in `directory_first`
  parameter (default `False`, unused by the one live call site), proven
  byte-identical to prior behavior when off, proven to fall back correctly
  when on but inconclusive, and shown to score 8/10 vs. 6/10 on the real
  corpus's retrieval ranking (reproduced twice, identical both times). No
  mirror content, Aster configuration, or Aster snapshot was changed; nothing
  was deployed or activated.
- **Next safe action:** from a host with real network access to LXC 104/110
  (the Aster agent host itself is the obvious candidate, since these
  dependencies and that access already exist there in production), run: (1)
  the Milestone 3 adversarial suite and (2) the eight Milestone 4 regression
  suites listed in that milestone's section, both with `directory_first=True`
  against the real endpoint. Only after both pass should Milestone 4's gate
  be considered met and a production activation decision be made — this
  session's evidence, while genuinely promising, is not sufficient on its
  own for that decision.
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

### Milestone 2 — Directory abstract generation — **complete 2026-09-13**

- [x] Add a deterministic per-`source_id` abstract generator (one sentence
      plus bounded topic tags) reading only already-accepted, already-verified
      entries for that source. **Implementation:** `_directory_abstract()` in
      `services/aster-wiki/aster_wiki/mirror.py`, wired into `build_mirror()`'s
      existing single pass over accepted sources (reusing the same `body`
      values already computed for entry generation, in both the fresh and
      unchanged-entry-reuse code paths — no new source read, no new authority,
      no LLM or network call). It is a bounded token-frequency count over each
      source's own claim bodies: markdown links/images, bare URLs, raw HTML
      tags and HTML entities are stripped first (verified necessary against
      the real corpus — see below), a fixed English stopword list is applied,
      and the top `DIRECTORY_TOPIC_LIMIT` (6) terms by `(-count, term)` become
      the topic tags feeding a one-sentence templated abstract. A source with
      `mirror_policy: human-only` correctly gets no directory entry, matching
      the existing human-only entry-generation rule. `PIPELINE_VERSION` bumped
      `1.4.1` → `1.5.0`, matching this repo's existing convention of a minor
      bump for a new output artifact.
- [x] Add `indexes/directories.json` alongside the existing global indexes,
      same `{"schema_version": 1, "entries": {...}}` shape as the other five
      indexes, written via the same `canonical_json()` helper.
- [x] Require build-twice identical hashes before publication. **Result:**
      the existing `test_build_is_deterministic_and_claims_are_source_located`
      test was extended to assert `directories.json` is byte-identical across
      two independent `build_mirror()` calls (it is automatically covered by
      the existing whole-tree `package_hash()` equality check, since the file
      is written before that hash is taken). Independently re-verified by
      running the generator directly against the real, unmodified 1,796-entry
      production mirror (the same read-only copy used for Milestone 1) twice
      and comparing output — identical both times, across all 24 populated
      production source IDs.
- [x] Add regressions for a sparse-entry source, a multi-domain source, and a
      source added after the index was built. **Result:** three new tests in
      `services/aster-wiki/tests/test_mirror.py` —
      `test_sparse_entry_source_gets_a_bounded_non_degenerate_abstract` (a
      single-entry source still gets a valid, non-empty, bounded abstract),
      `test_multi_domain_source_directory_reflects_more_than_one_topic_cluster`
      (a synthetic source spanning networking/storage/power sections shows
      topics from at least two of the three domains, not just one), and
      `test_directories_index_includes_a_source_added_after_the_prior_build`
      (a second `build_mirror()` call against the same output tree, with a
      new source added to the lock between calls, correctly adds that
      source's abstract without disturbing the existing one). A fourth test,
      `test_human_only_source_has_no_directory_abstract`, was added alongside
      these. All 13 mirror tests and the full 52-test `aster-wiki` suite pass.

**Real-corpus validation beyond the required regressions:** running the exact
generator against the real production mirror (read-only copy, nothing
deployed) surfaced and fixed a genuine quality problem before it could ever
reach production — the first version's naive tokenizer picked up markdown
badge/link and raw-HTML markup as top "topics" for several real sources (e.g.
`sonarr-4-0-19` showed `opencollective, svg, https, com`; `nginx-proxy-
manager-docs` showed `screenshots, png, src, img, href`). Fixed by stripping
markdown link/image syntax (keeping link display text), bare URLs, HTML tags
and HTML entities before tokenizing; re-run confirmed clean, genuinely
topical abstracts across all 24 real sources (e.g. `nginx-proxy-manager-docs`
now reads `nginx, docker, data, port, custom, npm`; `authentik-docs` reads
`application, authentik, user, provider, outpost, applications`). A known,
accepted residual limitation: a few GitHub-README-sourced sources
(`sonarr`, `radarr`, `prowlarr`) still surface genuine but low-value repeated
terms like `sponsors`/`backers` from real funding-appeal sections — this is
accurate extraction of real frequent content, not a bug, and is left as-is
rather than special-cased, consistent with this project's stated goal of not
adding fragile per-query shortcuts (the exact pattern Milestone 1 found
already causing problems in `search_knowledge()`).

Gate: **passed.** The directory index is deterministic (build-twice identical,
both in the synthetic test suite and against the real 1,796-entry corpus),
reproducible, and independently verifiable against its source entries (a
pure, auditable frequency count with no invented content). It carries no new
authority — `authority` continues to come only from `indexes/provenance.json`
and each entry's own front matter; `directories.json` is never consulted for
authority, only for routing. No mirror content was deployed or changed on
LXC 104/113; this is a repo-side pipeline change, not yet built or activated
in production.

### Milestone 3 — Two-stage retrieval integration — **mostly complete 2026-09-14, one item not executable from this session**

- [x] Add directory-first ranking ahead of entry-level ranking in Aster's
      existing snapshot consumer, gated behind an explicit fallback path.
      **Implementation:** `services/aster-agent/aster_agent.py` gained
      `_narrow_by_directory()` and a new `directory_first: bool = False`
      parameter on `search_knowledge()` (default off). The existing function
      body was renamed to `_rank_knowledge()` and parameterized by an
      `allowed_sources` restriction that is a no-op when `None` — so
      `directory_first=False` (every existing call site, including the one
      live production call in the `search_knowledge` tool dispatch at line
      837, which passes neither flag) produces **byte-identical** results to
      before this change. This was verified two ways: (1) re-running all 10
      of Milestone 1's real-corpus questions with `directory_first=False`
      after this change reproduced the exact Milestone 1 rankings, and (2)
      replicating 4 representative existing `test_aster_agent.py` cases
      (scoped ranking, current-state preference, operational authority, the
      focused-checklist override) against the change showed no difference.
      Narrowing itself is scoped strictly to `mirror/entries/`; reference-tier
      content (e.g. `docs/03-Hardware-Inventory.md`) is never affected by it,
      proven by a dedicated new test.
- [x] Prove with synthetic fixtures that a missing, stale, or wrong abstract
      falls back to today's flat entry-level search. **Result:** four new
      tests in `services/aster-agent/test_aster_agent.py` — missing
      `directories.json`, a stale entry (recorded `entry_count` no longer
      matches the live file count), and a query with no topical overlap
      against any directory abstract all produce **byte-identical** output to
      `directory_first=False`, proving the fallback is a true no-op in those
      cases rather than a degraded partial result. A fifth test proves
      correct narrowing on a clean case. All 5 were verified passing via the
      same standalone-extraction technique used in Milestones 1-2 (this
      sandboxed dev environment still has no network path to install
      `fastapi`/`httpx`/`pydantic` at the pinned versions needed to import
      `aster_agent.py` directly or run its test file as a whole — see
      Milestone 1's evidence for the same constraint).
- [ ] Re-run the existing critical/adversarial evaluation suite (poisoned
      sources, conflicting authorities, secret refusal, missing evidence).
      **Not executed — could not be, from this session.** That suite is a
      live black-box test against the real llama.cpp endpoint
      (`services/aster-agent/evals/run_evals.py`), and there is still no
      network path from this Claude Code session to LXC 104 or 110 (same
      constraint as Milestone 1's `compare_mirror.py` gap). What *is* proven,
      by construction rather than by re-running the suite: `directory_first`
      defaults to `False`, and the single live call site that would reach the
      adversarial suite's model calls does not pass it — so the suite's
      outcome cannot have changed, because the code path it exercises is
      unmodified. This is not a substitute for an actual re-run and should
      not be treated as one; it only establishes that nothing changed for
      *today's* deployed behavior. **Before Milestone 4 activates
      `directory_first` on the live path, the real adversarial suite must be
      run somewhere with actual access** (the Aster agent host itself, where
      these dependencies are already installed in production) — this is
      recorded as the next safe action below, not skipped silently.

**A genuine mid-implementation regression, caught and fixed before this
milestone was called done:** the first version of `_narrow_by_directory`
scored the query against abstract text using substring containment (matching
the entry-level ranker's own style). Re-testing against the real Milestone 1
question set — not just synthetic fixtures — surfaced two serious problems
this introduced: (1) the common word "for" matched as a substring inside
"forgejo", making the canonical `TEST-42` UPS question (previously perfect
under flat search) wrongly narrow to Forgejo's docs and return nothing
useful; (2) "add" matched inside "address", contributing to Sonarr's
notification question wrongly narrowing to OPNsense. Both are exactly the
failure mode this project's own risk assessment named as the primary danger
of this whole feature ("an incorrect... directory abstract could cause
retrieval to skip the correct source entirely — a worse failure mode than
today's flat search"). Fixed by scoring whole-word matches only, against the
curated topic tags plus the source id's own alphabetic components, dropping
the free-text abstract sentence from scoring entirely (it only restated the
topics as prose and doubled their count). Re-verified against the same real
1,796-entry corpus: **8/10 questions now correct at top rank under
`directory_first=True`, versus 6/10 under flat search, with zero
regressions** — both of Milestone 1's original failures (the Sonarr
notification miss and the OPNsense backup misranking) are now fixed, and
every previously-correct question remains correct.

Gate: **partially passed.** Two-stage retrieval activates only behind a
proven fallback (demonstrated for missing/stale/inconclusive abstracts, all
verified byte-identical to flat search), and directory-first narrowing has
shown a real, substantial improvement with no regressions on the available
evidence. The one unmet condition — re-running the live adversarial suite —
could not be executed from this session for the same network-access reason
as Milestone 1, and is carried forward rather than waived. `directory_first`
remains off by default and is not wired into any live call path; nothing in
production was changed.

### Milestone 4 — Comparative evaluation and regression — **partially complete 2026-09-14, blocked on the same access gap as Milestone 3**

- [x] Repeat the Milestone 1 question set against the two-stage path on the
      same snapshot generation, compared directly against the baseline.
      **Result:** run twice independently, byte-identical both times (fully
      deterministic — no randomness anywhere in this ranking path). Against
      the real 1,796-entry production mirror, `directory_first=True` scores
      **8/10 correct at top rank vs. 6/10 for today's flat search, with zero
      regressions** — every question that was already correct under flat
      search remains correct, and both of Milestone 1's original failures
      (Sonarr's notification miss, OPNsense's backup misranking) are fixed.
      The one persistently-wrong case (`home-assistant-1`) fails identically
      under both — it is the pre-existing `focused_ha_reference` regex
      shortcut identified in Milestone 1, unrelated to and unaffected by
      directory-first narrowing, and out of this project's scope to fix.
      This is a retrieval-ranking comparison (which source/entry gets
      surfaced), not an LLM-answer comparison — the latter is the next
      checklist item and is where this milestone is blocked.
- [ ] Re-run the general, ARR and Home Assistant regression suites.
      **Not executed — could not be, from this session, for the same reason
      as Milestone 3's adversarial-suite gap.** These are live black-box
      suites against the real llama.cpp endpoint
      (`services/aster-agent/evals/sysadmin-graduation.json`,
      `sysadmin-generalization.json`, `arr-advisory-graduation.json`,
      `arr-school-graduation.json`, `arr-stack-advisory.json`,
      `arr-stale-config-regression.json`, `home-assistant-graduation.json`,
      `knowledge-mirror-graduation.json`, run via `run_evals.py`), and there
      is still no network path from this Claude Code session to LXC 104 or
      110. This is a real, unmet checklist item, not a formality — it must
      run on a host with actual access before this milestone can be
      considered complete.
- [x] Document the outcome plainly. **Done above** — the retrieval-level
      result is a genuine, real improvement (not "no material improvement"),
      but the evidence is incomplete: it does not yet include how that
      improvement (or any regression) shows up in actual generated answers,
      nor whether any of the 8 pre-existing graduation/regression suites
      still pass with `directory_first=True`. Both are needed before this
      milestone's gate can be called fully passed.

Gate: **not yet passed** — this project's own standard requires production
activation to be justified by a direct before/after comparison, not
architectural preference alone, and only half of that comparison (retrieval
ranking) exists from this session. The retrieval-level result is genuinely
promising and worth carrying forward, but it is not sufficient on its own:
**do not activate `directory_first` in production, and do not skip the
regression-suite re-run, on the strength of this evidence alone.** The next
safe action is running the eight suites listed above (plus the Milestone 3
adversarial suite) with `directory_first=True` from a host that can reach
the llama.cpp endpoint — most plausibly the Aster agent host itself, where
these dependencies and network access already exist in production.

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
| 2026-09-13 | 2 directory abstract generation | Implemented `_directory_abstract()` in `services/aster-wiki/aster_wiki/mirror.py`, wired into the existing `build_mirror()` pass with no new source read and no new authority; bumped `PIPELINE_VERSION` `1.4.1` → `1.5.0` per this repo's existing minor-bump-for-new-artifact convention. Added 4 regression tests (sparse source, multi-domain source, source added after a prior build, human-only exclusion) plus extended the existing determinism test; all 13 mirror tests and the full 52-test `aster-wiki` suite pass. Independently ran the generator twice against the real, unmodified 1,796-entry production mirror (same read-only copy from Milestone 1; nothing on LXC 104/113 changed) — byte-identical both times across all 24 populated sources. That real-corpus run caught a genuine defect the synthetic tests missed: the first version's tokenizer surfaced markdown badge/link and raw-HTML markup as top "topics" for several real sources; fixed by stripping markdown links (keeping display text), bare URLs, HTML tags and entities before tokenizing, then re-verified clean on the same real corpus | Milestone 2's gate passed: deterministic, reproducible, independently verifiable against source entries, no new authority claim. Nothing was deployed or built in production |
| 2026-09-14 | 3 two-stage retrieval integration | Added an opt-in `directory_first` parameter to `search_knowledge()` in `services/aster-agent/aster_agent.py` (default off; the one live call site does not pass it, so today's deployed behavior is provably unchanged). First implementation used substring scoring against directory abstract text and, when re-tested against the real Milestone 1 corpus rather than only synthetic fixtures, was caught introducing two real regressions before being called done: "for" ⊂ "forgejo" broke the previously-perfect UPS TEST-42 case, and "add" ⊂ "address" contributed to a wrong Sonarr narrowing. Fixed by switching to whole-word matching against curated topic tags plus the source id's own alphabetic components, dropping the noisy free-text abstract sentence from scoring. Re-verified on the real corpus: 8/10 correct at top rank under `directory_first=True` vs. 6/10 flat, zero regressions, both of Milestone 1's original failures fixed. Added 5 new tests proving byte-identical fallback for a missing index, a stale abstract, and an inconclusive query, plus correct narrowing and reference-tier non-interference; verified passing via the same standalone-extraction technique used in Milestones 1-2 (this session still has no network path to install the pinned `fastapi`/`httpx`/`pydantic` versions needed to import `aster_agent.py` directly). Could not re-run the live adversarial evaluation suite (`run_evals.py` against the real llama.cpp endpoint) — same network-access gap as Milestone 1's `compare_mirror.py` limitation; proven by construction instead (unused-by-default parameter, unmodified live call path) that today's deployed behavior cannot have changed, which is not a substitute for the real re-run | Milestone 3's gate partially passed: fallback proven, real improvement measured, but the live adversarial re-run is outstanding and carried forward as a precondition before Milestone 4 could ever activate this on the live path. Nothing deployed; `directory_first` stays off by default |
| 2026-09-14 | 4 retrieval-ranking comparison | Repeated the Milestone 1 cross-domain question set against `directory_first=True` on the identical real 1,796-entry production mirror, run twice independently with byte-identical output both times (this pipeline has no randomness). Could not re-run the general/ARR/Home-Assistant regression suites or generate comparative LLM answers — same no-network-path gap as Milestone 3's adversarial suite; these suites (`sysadmin-graduation.json`, `sysadmin-generalization.json`, `arr-advisory-graduation.json`, `arr-school-graduation.json`, `arr-stack-advisory.json`, `arr-stale-config-regression.json`, `home-assistant-graduation.json`, `knowledge-mirror-graduation.json`) require the live llama.cpp endpoint via `run_evals.py` | 8/10 correct at top rank vs. 6/10 flat, zero regressions — a real, reproducible retrieval-level improvement, not "no material improvement." Milestone 4's gate is explicitly **not** called passed: this is half the required comparison, and production activation must not be decided on it alone. Next safe action is running the listed suites from a host with real access before any activation decision |

## Starting the handoff session

This project is handed off 2026-09-14 to a fresh session specifically because
finishing it needs something this session structurally does not have: a
network path to the Aster agent (LXC 104, `192.168.70.10`) and llama.cpp
(LXC 110, `192.168.70.12`) hosts. This is a **sandbox/platform limitation,
not a permission or authorization gap** — Stream A is already granted for
this whole project, and Milestones 1-4's retrieval-level work is done and
committed. What's left (Milestone 3's adversarial suite, Milestone 4's eight
regression suites, and Milestone 5) all require actually calling the real
model, and Claude Code's Bash sandbox on this Mac blocks raw TCP/SSH and
IP-based HTTP(S) to those hosts regardless of allowlist entries or
authorization stream — proven repeatedly across this project and the earlier
Authentik project.

**What the new session needs to do, concretely:**

1. Read this document in full, especially Milestones 3-4's evidence log
   entries, before touching anything — they explain exactly what passed,
   what's proven, and what's still open.
2. Every command that reaches `192.168.70.10` or `192.168.70.12` will need
   `dangerouslyDisableSandbox: true`, which triggers a live approval prompt
   even though Stream A is granted (platform/sandbox controls are mandatory
   regardless of project authorization — see `CLAUDE.md`). This is
   read-only, cost-bearing (real inference calls) work, not state-changing,
   but it still needs to be watched and approved as it runs.
3. If you (Jason) won't be at the keyboard, start this session with
   `cd /Users/jelliott/lab/homelab && claude --remote-control "Aster Mirror Eval Run"`
   and connect from the Claude iPhone app's Code tab, the same pattern used
   for the Authentik project's handoff — each sandbox-bypass prompt will
   appear as a phone dialog to approve.
4. Run, with `directory_first=True` explicitly set wherever the harness
   supports it:
   - Milestone 3's adversarial/critical suite (poisoned sources, conflicting
     authorities, secret refusal, missing evidence) — check
     `services/aster-agent/evals/run_evals.py` for the exact invocation this
     repo already uses for graduation-style runs.
   - Milestone 4's eight regression suites, listed in that milestone's
     section and evidence log row.
5. Compare each suite's `directory_first=True` result against its existing
   passing baseline (the suite files themselves record expected outcomes).
   Record pass/fail plainly in Milestone 3/4's checklists and evidence log —
   including a "no material improvement" or regression finding if that's
   what happens. **Do not activate `directory_first` in production
   (i.e. change the live tool-dispatch call site at
   `services/aster-agent/aster_agent.py`'s `search_knowledge` tool handler)
   until every suite passes** — this is the explicit condition this
   project's own gates were written around.
6. If everything passes: Milestone 5 (recovery/observability/graduation) is
   the last step, and needs Jason's explicit sign-off on the production
   activation decision itself before it's made, not just on the evidence
   supporting it.
7. If something doesn't pass: that's a legitimate, useful outcome too — stop,
   record it plainly, and either close the project at that finding or scope
   a fix, per this project's own "no material improvement" language in
   Milestone 4.

## Close-out

To be completed at graduation. Will record: whether the directory layer was
activated in production or the project closed at the Milestone 1 hard stop;
final architecture as deployed (or explicit confirmation that no architecture
change was made); ownership (Jason); recovery references (retained `1.4.1`
tree and snapshot location, or the final accepted tree if superseded); and any
deliberately deferred follow-on work, such as extending the directory layer to
sub-source topic clustering if a future corpus scale-up reopens the question.
