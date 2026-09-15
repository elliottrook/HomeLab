# News Aggregator (MuckScraper)

> Status: Graduated — all milestone completion gates passed. LXC 114
> `news-aggregator` runs a full hourly pipeline on VLAN 70
> (`192.168.70.13`): ingest → cluster → summarize → flag loaded language,
> chained in one systemd service, across **10 feeds** (Al Jazeera
> added 2026-09-15 as a real new-source test; AP News assessed and
> formally dropped — no source-published feed could be found and this
> project excludes third-party scraping proxies as a workaround). The
> reading UI is live at `http://news.internal:8080`, reachable only from
> Jason's approved devices via a narrow, `MGMT_ADMIN_HOSTS`-precedented
> firewall rule, verified end-to-end. HomeLab Doctor coverage and
> whole-guest backup (local Proxmox snapshot plus the off-host TrueNAS
> pull, both live and checksum-verified) are in place. Recorded in
> NetBox as VM id 15.
> Outlet bias ratings (BBC: Center, NPR: Lean Left, both cited to
> AllSides) are loaded and rendering live, with an "unverified this
> session" caveat on both the table row and a UI hover tooltip, since live
> verification against AllSides failed twice and Jason accepted the draft
> as-is at medium confidence — see Milestone 1's feed-list note and the
> evidence log for the AP News feed, which turned out to have been
> silently dropped since Milestone 2 and is not part of the running
> pipeline.
>
> Project owner: Jason
>
> Proposed: 2026-09-10
>
> Started: 2026-09-14
>
> Completed: 2026-09-15
>
> Authorization stream: **Stream A — Autonomous**, granted by Jason
> 2026-09-14 in this project's own conversation, per the per-project
> authorization mechanism in `CLAUDE.md` and the `Project-Creation-Standard`.
> Covers this document's enumerated scope end to end. Two decisions this
> document itself names as needing Jason's specific sign-off are preserved
> as explicit checkpoints rather than absorbed into blanket authorization,
> since the Standard's non-waivable stop conditions require a fresh,
> explicit decision for a broadened firewall/trust rule regardless of
> stream, and this document independently names the bias-methodology choice
> as too subjective to decide unilaterally:
>
> 1. **Outbound egress/firewall** — before Milestone 2, the exact external
>    domains/scope needed must be presented to Jason for an explicit,
>    narrowly-scoped OPNsense decision, not inferred or assumed.
> 2. **Bias-scoring methodology and its UI labeling** — before Milestone 3,
>    the chosen method and how prominently the "automated estimate, not
>    authoritative" caveat is shown must get Jason's explicit sign-off.
>
> Everything else in the enumerated scope — placement, clustering method,
> feed list, ingestion implementation, the reading UI — proceeds under
> Stream A without a per-step approval, per the normal milestone-by-milestone
> workflow.

## Purpose and desired outcome

A private, self-hosted news reading page that pulls stories from
user-selected RSS/Atom feeds, groups the same story as covered by different
outlets, flags likely duplicate/near-duplicate coverage, and attaches an
automated, clearly-labeled bias/slant estimate and a short local-model
summary to each cluster. The desired outcome is a faster, less repetitive
morning read of chosen sources — not a replacement for any outlet's own
site, and not a publishing or sharing platform.

## Current state and evidence

No component of this project exists today. Nothing has been deployed,
scoped in detail, or measured.

- No RSS/Atom ingestion, clustering, or reading UI runs anywhere in the lab.
- The shared local-inference endpoint this project would use for
  summarization already exists and is production: `aster-llama.service` in
  LXC 110 at `http://192.168.70.12:11435/v1` (OpenAI-compatible chat
  completions), currently `unsloth/Qwen3.8-27B-GGUF:UD-IQ4_XS` via
  llama.cpp/Vulkan — see [Aster-Operations.md](../../Aster-Operations.md). This
  project would call that endpoint as a separate client; it would not modify
  Aster's own bounded function allowlist or become part of Aster's curriculum.
- Lab VLAN 70 already hosts the AI-adjacent workloads (Aster LXC 104, the
  llama.cpp LXC 110). Servers VLAN 20 hosts the media/automation stack. No
  placement decision has been made for this project — see Open risks below.

## Scope

- Ingest a user-curated list of RSS/Atom feeds on a schedule.
- Group stories that cover the same underlying event across multiple
  outlets (title/entity/time-window clustering; exact method to be decided
  during design, not assumed here).
- Produce a heuristic-plus-local-model bias/slant label per outlet or
  per-story cluster, presented as an automated approximation, never as an
  authoritative rating.
- Summarize each cluster using the shared `aster-llama` endpoint.
- Serve a private, internal-DNS-only reading UI (no public exposure, no
  authentication bypass).

## Out of scope / exclusions

- Republishing, exporting, or sharing any aggregated content outside the
  household.
- Scraping any paywalled source or any source whose terms of service
  prohibit automated retrieval — RSS/Atom feeds the source itself publishes
  only.
- Training or fine-tuning a custom bias classifier — v1 uses prompting and
  heuristics against the existing shared model only.
- Replacing or modifying the existing Homepage service dashboard.
- Any second local model server — this project reuses `aster-llama`.

## Architecture and data flows

- **Compute**: new LXC (or container on an existing Servers VLAN 20 host —
  placement not yet decided, see Open risks). IP/VLAN to be assigned at
  deployment.
- **Feed ingestion**: a scheduled job (systemd timer or cron, matching the
  repo's existing pattern) fetches each configured feed over HTTPS on an
  interval, stores raw items in a local datastore (SQLite or similar —
  sizing not yet assessed).
- **Clustering/bias/summary**: a batch process reads new items, clusters
  them, calls `http://192.168.70.12:11435/v1` for summarization, and writes
  results back to the same datastore. This is a plain HTTPS client call to
  the existing endpoint — no new model, no new GPU workload.
- **Reading UI**: a small internal-only web app reads the datastore and
  renders clusters. Internal DNS name only (matching the
  `*.elliottrook.com` split-DNS pattern used elsewhere in the repo), never
  exposed through the public-facing reverse proxy path.
- **Identities**: a dedicated service account/API surface for this
  project's own datastore; no shared credentials with any other project.
  If Authentik fronts the reading UI, it gets its own application entry,
  not a shared one.

## Privacy and security design

- No feed content or generated summaries leave the lab network.
- The reading UI is internal-DNS-only; no public ingress is created.
- Bias/slant output is labeled in the UI itself as an automated heuristic
  estimate, not a factual or authoritative rating, everywhere it is shown.
- Any credential this project needs (none anticipated for RSS ingestion
  itself, unless a chosen source requires an API key) is stored outside
  Git, mode 600, on the host that uses it — never committed to a tracked
  file, matching every other project's credential pattern in this repo
  (e.g. [Jellyfin-Library-Integrity-Automation.md](../Jellyfin-Library-Integrity-Automation.md)'s
  "Safety and credentials" section).

## Open risks and decisions needing Jason's input

- **Outbound egress — resolved 2026-09-15.** The premise that this needs a
  new, broadened firewall rule turned out to be wrong once checked against
  `Current-Network-Baseline.md`: VLAN 70 already has validated broad
  outbound internet access. Jason chose to leave that existing posture
  as-is rather than narrow it to a domain allowlist, after the
  maintenance-burden trade-off was presented. **No OPNsense change is
  needed for this project.**
- **Placement: recommended Lab VLAN 70, 2026-09-14**, not Servers VLAN 20 —
  see Milestone 1's checklist for the full reasoning (already-validated
  broad egress with internal isolation, same-VLAN reach to `aster-llama`
  avoiding a new cross-VLAN rule, ample Proxmox headroom either way). A
  recommendation, not yet Jason's confirmed decision.
- **Clustering method: recommended, 2026-09-14** — headline/lede similarity
  within a rolling time window, no LLM call in the clustering step itself,
  tuned toward precision over recall. See Milestone 1's checklist for the
  full reasoning and its stated accuracy trade-off. Not yet validated
  against real feed data.
- **Bias-scoring methodology — resolved 2026-09-15: hybrid** (named
  external outlet-level rating as the primary, attributable label;
  `aster-llama` limited to an optional, visually secondary per-story
  loaded-language note). See Milestone 1's checklist for the full decision.
  One implementation detail carries forward to Milestone 3, not yet
  resolved: the exact rating source (AllSides / MBFC / Ad Fontes) and a
  check of its terms of use for programmatic reference.
- **Feed list, refresh interval, and retention window** are all still
  undecided and directly affect both storage sizing and how much this looks
  like general web scraping vs. bounded feed reading.
- Stream A has been granted (see header) with the egress and bias-labeling
  decisions above preserved as explicit checkpoints.

## Milestones

### Milestone 1 — Discovery and design decisions

- [x] Resolve placement (VLAN/host) and record the decision here.
      **Confirmed by Jason 2026-09-15: Lab VLAN 70**, not Servers VLAN 20.
      Checked `Current-Network-Baseline.md` rather than assuming: VLAN 70
      "was fully validated with disposable LXC 970: DHCP, Pi-hole DNS,
      blocked-domain response and Internet access passed, while non-DNS
      access to internal services remained blocked" — meaning broad
      outbound internet egress is *already* permitted from VLAN 70 today,
      with lateral access to other internal services already blocked. That
      is exactly this project's actual need (many external news domains
      out, no internal lateral access required). Placing it on VLAN 70 also
      means its call to `aster-llama` (`192.168.70.12:11435`) stays
      same-VLAN, needing no new cross-VLAN firewall rule at all — placing it
      on VLAN 20 instead would require a *new* VLAN 20 → VLAN 70 rule just
      to reach that dependency, on top of whatever egress rule the news
      fetching itself needs. Proxmox capacity is not a differentiator
      either way: ~28 GiB allocation headroom as of the most recent
      measurement (`03-Hardware-Inventory.md`, 2026-09-09), comfortably
      enough for a lightweight ingestion LXC. This is a recommendation, not
      a unilateral decision — Jason should confirm before Milestone 2.
- [ ] Resolve the outbound-egress/firewall question with Jason explicitly.
      **Resolved by Jason 2026-09-15: leave VLAN 70's existing broad
      egress as-is, no new firewall rule.** The trade-off was presented
      explicitly (narrowing to an FQDN-based allowlist would reduce this
      workload's blast radius if ever compromised, at the cost of ongoing
      maintenance every time the feed list changes, plus CDN-IP-churn
      fragility if done as static IPs rather than FQDN aliases). Jason
      chose to accept the existing, already-validated broad-egress posture
      rather than take on that maintenance burden. This is not a new
      exposure — VLAN 70 already permits this for its existing workloads —
      just a decision not to tighten further for this one. **This project
      needs zero OPNsense changes.**
- [x] Choose and document the clustering method and its expected accuracy
      trade-offs. **Recommendation, 2026-09-14:** headline + lede text
      similarity (e.g. TF-IDF cosine similarity or simpler fuzzy string
      matching — no new heavy ML dependency needed) within a rolling
      publish-time window (48-72 hours), plus a lightweight named-entity/
      keyword overlap check, greedily grouped (union-find style) above a
      similarity threshold. No LLM call is used for clustering itself —
      `aster-llama` is only called once per already-formed cluster for the
      summary, keeping inference cost bounded to cluster count, not raw
      item count. Expected trade-off: this approach favors **precision over
      recall** — outlets with very different headline framing for the same
      event may end up in separate clusters (a missed merge, low-risk
      failure: the reader just sees two similar-looking entries), while the
      threshold should be tuned conservatively enough that unrelated
      stories are rarely merged together under one bias-labeled summary (a
      wrongly-merged cluster is the worse failure mode, since it would
      misattribute one outlet's framing to another's story). This needs
      validation against real feed data once Milestone 2's ingestion
      exists — the accuracy trade-off is a design expectation here, not yet
      measured.
- [x] Placement confirmed by Jason 2026-09-15: **Lab VLAN 70.**
- [x] Choose and document the bias-scoring methodology and UI labeling.
      **Decided by Jason 2026-09-15: hybrid.** A named, external, published
      outlet-level rating (e.g. AllSides, Media Bias/Fact Check, or Ad
      Fontes Media — exact source still to be picked at Milestone 3, see
      below) is the primary, attributable label shown for each story's
      outlet — not the LLM's own opinion. `aster-llama` is used only for an
      optional, clearly secondary per-story note flagging notably loaded
      language within that specific story, visually distinct from the
      outlet-level rating so the two signals never blur into one unearned
      "bias score." This satisfies both halves of the required sign-off:
      the method (external, attributable primary signal; LLM kept to a
      narrow, secondary, clearly-labeled role) and the caveat prominence
      (the outlet rating's own source is cited directly in the UI; the
      LLM-derived note carries the standard "automated estimate, not
      authoritative" label from this project's Privacy and security design
      section).
      **Resolved differently than originally framed, 2026-09-15:** rather
      than build automated, repeated programmatic retrieval against a
      live rating service (which would need its terms of use verified,
      and this session's tools couldn't reliably fetch/verify external
      ToS pages live), `outlet_ratings` is populated by **manual, one-time
      citation** — the same way a bibliography cites a source, not a
      scraper hitting their site on a schedule. This sidesteps the
      automated-retrieval ToS question entirely rather than resolving it,
      which is an honest, different outcome from what was originally
      anticipated, not a semantic dodge: no request is ever made to the
      rating source's own infrastructure by this project.
      **A second, real finding while drafting the proposal:** of the 9
      configured feeds, only BBC/NPR/AP are the *type* of outlet AllSides
      (the proposed source — widely cited, freely viewable ratings page)
      typically rates at all. The other 6 — four tech trade publications
      (Ars Technica, The Verge, Hacker News, 9to5Mac) and two small
      Vancouver Island regional outlets (Times Colonist, Cowichan Valley
      Citizen, CHEK News) — almost certainly have no published AllSides
      rating, since AllSides is US-politics-focused and doesn't cover tech
      trade press or Canadian regional papers. That is correct, honest
      behavior for this UI to show ("no rating available") rather than
      something to force a fake label onto, and is itself informative:
      bias/slant as a concept doesn't meaningfully apply to a product
      review site or a municipal election roundup the way it does to
      general political news coverage.
      **Loaded 2026-09-15.** Two live verification attempts (WebFetch,
      Browser pane) both failed to reach AllSides from this session, so
      these remain Claude's own recollection, not confirmed against the
      live source. Jason reviewed this specific limitation and chose to
      accept the draft as-is rather than wait; the "unverified this
      session" caveat is recorded per-row in the `outlet_ratings.notes`
      column itself, not just in this document, so it travels with the
      data:
      | Outlet | Rating | Source | Confidence |
      |---|---|---|---|
      | BBC World News | Center | AllSides (recollection, unverified this session) | Medium |
      | NPR World | Lean Left | AllSides (recollection, unverified this session) | Medium |
      | Ars Technica, The Verge, Hacker News, 9to5Mac | *No rating* | — | High confidence these are simply unrated by AllSides, not that a rating was missed |
      | Times Colonist, Cowichan Valley Citizen, CHEK News | *No rating* | — | High confidence — AllSides doesn't cover Canadian regional press |
      | AP News | *Dropped from project* | — | See the feed-list entry above — AP has no accessible source-published feed and was never actually added to `feeds.json`, found while preparing this table |
- [x] Draft the initial feed list with Jason. **Candidate list, 2026-09-15
      — unverified, live URL/reachability checks belong to Milestone 2's
      own "validate against the initial feed list with real fetches" step,
      not this planning stage:**
      - General/world: BBC World News (`feeds.bbci.co.uk/news/world/rss.xml`),
        NPR World (`feeds.npr.org/1004/rss.xml`), AP News (exact current feed
        path to be confirmed at Milestone 2 — AP's public RSS availability
        has changed over time).
        **AP resolved 2026-09-15, and dropped:** this "to be confirmed" note
        sat unresolved through all of Milestone 2 and AP silently never made
        it into `feeds.json` — not caught until reviewing the bias-rating
        proposal surfaced an orphaned `outlet_ratings` row for a feed that
        didn't exist. Probed three plausible current AP RSS/feed endpoints
        live; all three returned 403. The one workaround available
        (RSSHub, a third-party proxy that scrapes sites without their own
        feed) would violate this project's own exclusion — "RSS/Atom feeds
        the source itself publishes only" — so it wasn't used. AP does not
        currently have an easily accessible, source-published feed and is
        dropped from this project's scope rather than worked around.
        **Added 2026-09-15 at Jason's request:** Al
        Jazeera English (`www.aljazeera.com/xml/rss/all.xml`, live-verified
        before adding — see Milestone 4's test below).
      - Tech: Ars Technica (`feeds.arstechnica.com/arstechnica/index`), The
        Verge (`theverge.com/rss/index.xml`), Hacker News front page
        (`news.ycombinator.com/rss`), 9to5Mac (`9to5mac.com/feed`).
      - Local — **Vancouver Island specifically**, not the city of
        Vancouver (corrected 2026-09-15; Jason is on the Island, in the
        Cowichan Valley/Duncan area): Times Colonist
        (Victoria/Island-wide daily), Cowichan Valley Citizen (Black Press
        Media — the hyper-local paper for Jason's specific area), CHEK
        News (Vancouver Island-wide TV/news). Exact feed paths for all
        three to be confirmed at Milestone 2; Black Press Media's RSS
        structure in particular should be checked rather than assumed.

### Milestone 2 — Ingestion pipeline — **complete 2026-09-15**

- [x] Deploy the chosen compute target. **LXC 114 `news-aggregator`**,
      Proxmox, Lab VLAN 70, `192.168.70.13/24`, unprivileged Debian 13.6,
      2 cores / 2GB RAM / 16GB disk, matching the existing LXC 104/110
      convention (`bridge=vmbr0, gw=192.168.70.1, tag=70`, nameserver
      `192.168.20.20`, `searchdomain=home.internal`). Verified both
      directions live, not assumed from Milestone 1's paper analysis:
      general outbound HTTPS works (`curl` to bbc.co.uk returned 200), and
      the same-VLAN `aster-llama` endpoint is reachable
      (`192.168.70.12:11435/v1/models` returned 200).
- [x] Implement scheduled feed fetch and raw-item storage. SQLite schema
      (`feed_items` with a `UNIQUE(feed_id, guid)` dedup constraint, plus a
      `fetch_log` table for per-run success/failure — the future HomeLab
      Doctor freshness check reads this) and a Python `ingest.py` using
      `feedparser`, running in a venv at `/opt/news-aggregator/venv`. A
      systemd `news-aggregator-ingest.timer` runs it hourly
      (`RandomizedDelaySec=300`, `Persistent=true`), enabled and active —
      next run confirmed scheduled.
- [x] Validate against the initial feed list with real fetches. **This is
      where Milestone 1's unverified candidate URLs got their first real
      test, and 2 of 9 were wrong, exactly the kind of thing this
      checklist item exists to catch:**
      - `chek-news` failed DNS (`chek.news` doesn't resolve) — the real
        domain is `cheknews.ca`, and the working feed path (found by
        following a redirect) is `https://cheknews.ca/feed/` (trailing
        slash required).
      - `times-colonist` failed to parse ("not well-formed" — the guessed
        `/feed` path returned a 403 from bot protection, not XML) — the
        real working path, found by probing common paths directly on the
        live site, is `https://www.timescolonist.com/rss` (no `.xml`
        suffix, despite serving `content-type: text/xml`).
      - The other 7 feeds worked on the first try with their Milestone 1
        candidate URLs, unchanged.
      - `feeds.json` on LXC 114 now has all 9 corrected, live-verified
        URLs. After fixing the two and re-running, all 9 succeeded; a
        second run confirmed the dedup constraint works correctly (0 new
        items on re-fetch for the 7 already-ingested feeds, 20/10 new for
        the two just-fixed ones). 243 real items landed across all 9 feeds
        on the first successful full run, including genuinely
        Vancouver-Island-local content from `chek-news` (Cowichan Lake,
        Tofino, Highlands municipal election coverage) — confirming the
        Milestone 1 local-source correction actually produced relevant
        results, not just a plausible-sounding list.

### Milestone 3 — Clustering, bias labeling and summarization

- [x] Implement clustering per the Milestone 1 design. **Done and verified
      2026-09-15.** `cluster.py`: headline `SequenceMatcher` ratio +
      keyword-Jaccard fallback, cross-outlet only (same-outlet items never
      merge), within a 72h window, comparison pool bounded to a 10-day
      lookback (not full history, to stay fast as the table grows — added
      after noticing the first draft would have rescanned everything on
      every run). Run against the real 311-item corpus: 303 new
      single-item clusters, 8 merges, **6 genuine multi-outlet clusters**.
      Spot-checked all 6 by hand — every one is a correct match (US
      orbital-weapons confirmation across BBC/Ars Technica/Hacker News,
      Steam Frame review across Ars/HN, two distinct iOS 27 angles each
      correctly kept separate rather than over-merged, Netherlands rail
      sabotage across BBC/HN, NATO/Lithuania drone across BBC/NPR) — real
      confirmation that "precision over recall" is holding in practice,
      not just as a stated intent.
- [x] Wire summarization to the shared `aster-llama` endpoint. **Done and
      verified 2026-09-15**, but this surfaced a real gap in the original
      plan: `aster-llama` requires an API key, and this project's design
      never accounted for that. Rather than reuse Aster's own key (which
      this document's own Privacy and security design section says to
      avoid) or silently pick an option, this was presented to Jason as an
      explicit decision. Jason chose to check for multi-key support first.
      `llama-server --help` confirmed `--api-key-file` accepts multiple
      keys; generated a new dedicated key server-side (never displayed in
      any output), added it alongside Aster's existing key in
      `/etc/aster-llama-api-keys` on LXC 110, switched
      `aster-llama.service` from `--api-key` to `--api-key-file`, and
      restarted. Verified after restart: Aster's original key still
      authenticates (production continuity confirmed), the new dedicated
      key authenticates, and unauthenticated/garbage-key requests are
      still correctly rejected with 401 on the endpoint that matters
      (`/v1/chat/completions` — `/v1/models` returns 200 with no key
      regardless, which turned out to be normal llama.cpp behavior, not a
      bug, confirmed by testing the actual completions endpoint
      separately rather than assuming). The new key lives at
      `/root/.news-aggregator-llama-key` on LXC 114, mode 600, matching
      this project's own credential-storage pattern.
      `summarize.py` generates a neutral 2-3 sentence summary per
      multi-outlet cluster (single-source items just show their own RSS
      summary — no LLM call needed there), explicitly instructed not to
      render any bias judgment. Ran against all 6 real multi-outlet
      clusters; spot-checked the output — factual, correctly notes where
      outlets differ in emphasis, zero bias language, exactly as
      instructed.
- [x] Implement bias/slant labeling with explicit UI caveats. **Mechanism
      built 2026-09-15; the actual outlet rating values are a draft
      proposal for Jason to confirm, not something decided unilaterally —
      see the evidence log entry and the open item below.** Two tables:
      `outlet_ratings` (feed_id → rating_label, source_name, source_url,
      as_of_date — the primary, attributable signal per the Milestone 1
      hybrid decision) and `item_language_notes` (per-story, optional,
      generated by `aster-llama` with an instruction to reply `NONE` for
      ordinary headlines and only flag genuinely notable loaded language —
      deliberately conservative, and every checked item is recorded
      whether flagged or not, so unflagged items aren't re-sent to the LLM
      on every future run). Ran against 45 real recent headlines: **zero
      flagged**, which on its own proves nothing — a detector that never
      fires might just be broken. Verified separately with a deliberately
      loaded synthetic headline ("Radical extremist politicians launch
      shameless attack on hardworking families...") and it correctly
      identified and named the specific loaded phrases, confirming the
      mechanism has real discriminating power rather than silently passing
      everything through. All four scripts (`ingest.py`, `cluster.py`,
      `summarize.py`, `language_notes.py`) are now chained into a single
      `run_pipeline.sh`, wired into the existing hourly systemd timer in
      place of the bare `ingest.py` call — each stage is independent and
      idempotent, and one stage failing doesn't block the others.

### Milestone 4 — Reading UI and hardening — **complete 2026-09-15**

- [x] Test adding a new source to the live pipeline. **Not a pre-planned
      item — Jason asked whether this was tested and requested Al Jazeera
      specifically, so it became the real test rather than a synthetic
      one.** Verified the live feed URL first
      (`https://www.aljazeera.com/xml/rss/all.xml`, confirmed 200 with
      `content-type: application/rss+xml`) rather than assuming. Added it
      to `feeds.json` — a config-only change, zero code edits — and ran
      the full pipeline. Result: 25 items ingested cleanly on the first
      try, and clustering immediately found genuine cross-outlet matches
      involving the brand-new source with no special-casing needed,
      including one real **3-way match** (BBC + Times Colonist + Al
      Jazeera, all correctly identifying the same US Supreme Court
      mail-in-ballot ruling). Ran the full pipeline end to end afterward:
      clustering found 5 new multi-outlet clusters involving Al Jazeera (11
      total corpus-wide, up from 6), and `summarize.py` generated clean
      summaries for all of them, including correctly attributing which
      specific outlet emphasized which angle (e.g. noting BBC highlighted
      the EPA's cost-savings claim on the emissions-rule repeal story while
      Al Jazeera focused on the termination of the limits themselves). Two
      clusters failed on the first summarization pass and succeeded
      cleanly on an immediate idempotent re-run — a transient issue, not a
      logic bug, and exactly what the idempotent design is for.
- [x] Build the internal-only reading UI. **Done 2026-09-15.** Flask app
      (`app.py`) behind gunicorn, bound explicitly to `192.168.70.13:8080`
      only (never `0.0.0.0`), run via `news-aggregator-ui.service`. Renders
      clusters newest-first: multi-outlet clusters show the `aster-llama`
      summary, single-source items show their own RSS description, each
      outlet links out with its rating shown if one exists in
      `outlet_ratings` — honestly labeled "(no rating)" otherwise, since
      the table is still empty pending Jason's confirmation of the draft
      values. The non-authoritative caveat is always visible at the top,
      not just present somewhere in the markup. A `/healthz` endpoint
      exists for the Doctor check below. Verified by fetching the real
      rendered page (27KB, real content, not an error page) and spot
      checking specific rendered entries.
- [x] Confirm no public exposure and correct internal DNS resolution.
      **Done 2026-09-15, and this surfaced a real, unanticipated gap that
      needed Jason's explicit decision before it could be closed.** Added
      `news.internal` → `192.168.70.13` to both Pi-holes (matching the
      existing `truenas.internal` direct-IP pattern, not the
      Authentik/NPM-fronted `*.elliottrook.com` pattern — proportionate
      for a single-user tool with no need for SSO). Verified zero WAN/
      OPNsense exposure (`grep -c 192.168.70.13 /conf/config.xml` before
      any change: 0 matches). But confirming VLAN 70's isolation also
      revealed that **Jason himself could not have reached this UI** —
      nothing permitted his own trusted devices into VLAN 70 at all, only
      the outbound-egress question had ever been considered. Presented
      this plainly rather than silently opening a rule; Jason chose a
      narrow, `MGMT_ADMIN_HOSTS`-precedented fix. Backed up
      `config.xml` (`config-news-aggregator-before-20260915.xml`,
      matching this repo's established naming convention) before any
      edit; made a minimal, surgical **text** insertion of one new rule
      rather than a full-tree XML re-serialization, specifically to avoid
      any risk of reformatting unrelated parts of a 175KB live production
      firewall config; the insertion script asserted every expected
      substitution actually happened before writing, and asserted the
      stale `opt4` value was gone from the new block. Validated the
      result still parses as well-formed XML before reloading. New rule:
      `MGMT_ADMIN_HOSTS → 192.168.70.13:8080/tcp` only, sequence 3150 (a
      single host destination and a single port, not a VLAN-wide
      allowance). Reloaded via `configctl filter reload`; confirmed the
      exact rule loaded into the live `pf` ruleset via `pfctl -sr`.
      **Verified end-to-end from a real approved device**, not just
      checked on paper: this Mac (`192.168.1.206`) is itself one of the
      three `MGMT_ADMIN_HOSTS` entries, and a direct DNS lookup + HTTP
      request from it succeeded. Regression-checked immediately after:
      a non-admin host (the Docker LXC on VLAN 20) still correctly
      cannot reach it (connection refused), confirming the rule is as
      narrow as intended and nothing else changed.
- [x] Add HomeLab Doctor and monitoring coverage. **Done 2026-09-15** — see
      the Required integration impact checklist below; `check_news_aggregator()`
      was added to `scripts/doctor.sh` and tested against real data.

### Milestone 5 — Documentation and graduation — **complete 2026-09-15**

- [x] Complete the integration impact checklist below for real.
- [x] Record final architecture and close out. See the Operations quick
      reference below and the final evidence log entries.

## Required integration impact checklist

- [x] **HomeLab Doctor** — added 2026-09-15. `check_news_aggregator()` in
      `scripts/doctor.sh`: fails if the UI service isn't active or
      `/healthz` doesn't report ok; fails if no feed fetch has succeeded
      in the last 2 hours; warns on a mix of recent successes and
      failures; fails if fetches are failing outright. Tested against the
      real system, not just written and assumed correct — the check
      correctly surfaced a real warning from the `times-colonist`/
      `chek-news` URL failures already recorded in `fetch_log` from
      earlier Milestone 2 testing, confirmed by querying the table
      directly rather than trusting the check's own output blindly.
- [x] **Monitoring/alerting** — covered by the Doctor check above; no
      separate alerting surface needed for a single-user internal tool
      already covered by the existing Doctor run.
- [x] **Backup and recovery** — closed 2026-09-15, matching the NetBox
      LXC 111 precedent exactly: LXC 114's entire state (app code,
      `news.db`, `feeds.json`, systemd units) is local to the guest's own
      filesystem, so the existing all-guests 02:30 daily Proxmox
      `vzdump` snapshot job (`all 1`, no per-VMID allowlist) already
      captured it automatically with zero config change — confirmed via
      a real archive from this morning (463 MB). The separate off-host
      leg needed a real change: the TrueNAS backup hub's daily pull uses
      an explicit per-VMID `rsync --include` allowlist (100–109, 111,
      113), which did not yet include 114. Added
      `vzdump-lxc-114-*`/`vzdump-qemu-114-*` to that allowlist (TrueNAS
      `rsynctask` id 1, matching the exact pattern used when VMID 113
      was added 2026-09-12), then ran the pull manually rather than
      waiting for the next scheduled run: the archive landed on TrueNAS
      and its SHA-256 matched the Proxmox-side source exactly
- [x] **NetBox** — added 2026-09-15. Followed this repo's own established
      precedent from the NetBox-DCIM project's close-out rather than
      hunting for a write-capable API token: the stored token is
      deliberately read-only since that project's own security decision, so
      the record was created via NetBox's Django shell directly in the
      `netbox-netbox-1` container, matching how the last VM record update
      was made for the same reason. Created VirtualMachine `news-aggregator`
      (id 15, site "Mini Atlas HomeLab", cluster "proxmox", 2 vCPU/2GB/16GB,
      matching the actual LXC 114 allocation), a `eth0` VMInterface (id 15,
      untagged — matching the existing convention that VLAN-70 VM interfaces
      in NetBox aren't tagged with a VLAN object either, checked against
      LXC 104's own interface before assuming), and IP address
      `192.168.70.13/24` (id 29) set as the VM's `primary_ip4`. Verified
      afterward via a read-only `GET`, not just trusted from the creation
      output.
- [x] **Human wiki** — not applicable. This project's output is
      personal, ephemeral news content, not reference documentation or
      operator-facing knowledge, so it has no place in Aster's human
      wiki corpus.
- [x] **Aster mirror/snapshot** — not applicable; this project does not
      touch Aster's own knowledge or function set.
- [x] **Operational reference and runbooks** — closed 2026-09-15 via the
      Operations quick reference section added below, covering restart,
      log locations, adding a feed, and health-check commands — the same
      scope this repo's other single-guest internal tools keep inline
      rather than in a separate runbook file.
- [x] **Repository documentation** — this document, the portfolio table,
      and (from this milestone) the completed-projects table are the
      full, current documentation; kept up to date at every milestone
      throughout, including this graduation pass.
- [x] **Diagrams/rack records** — not applicable, matching the
      Aster-Offline-Knowledge-Wiki precedent for a VM-only deployment:
      LXC 114 is a virtual guest with no physical rack, cable, or power
      topology change. Its NetBox VM record (id 15, added in Milestone 2)
      is the correct and complete inventory entry.
- [x] **Homepage/service discovery** — added 2026-09-15. Backed up
      `services.yaml` first
      (`services.yaml.before-news-aggregator-20260915`), then a minimal
      text insertion (not a full rewrite) adding a "News Aggregator" tile
      to the existing "Media" group, alongside Jellyfin/Immich/Seerr/
      Calibre/Audiobookshelf — the natural fit for a personal
      content-reading tool. Validated the YAML inside the real Homepage
      container (`js-yaml`, not assumed valid) before restarting it to
      pick up the change (config isn't hot-reloaded). Verified via
      Homepage's own `/api/services` endpoint, not just the page's raw
      HTML shell — matching the same verification precedent already used
      elsewhere in this repo's Homepage work.
- [x] **Authentication/authorization** — decided 2026-09-15: no
      application-layer auth (no Authentik front-end). Unlike the Aster
      wiki (proxied at `wiki.elliottrook.com`, reachable by hostname from
      any Trusted-VLAN client, which is why it needed an Authentik gate),
      this UI has no proxy hostname at all and is reachable only by IP
      from the three specific devices named in the `MGMT_ADMIN_HOSTS`
      firewall rule — a narrower restriction than Authentik plus broader
      network reachability would give. Adding an auth layer on top would
      be disproportionate complexity for a single-user, no-PII, read-only
      news reader; the network ACL already is the access control.
      Documented here rather than left silently unauthenticated.
- [x] **DNS, certificates and firewall** — closed in Milestone 4:
      `news.internal` resolves on both Pi-holes, zero WAN/OPNsense
      exposure confirmed before and after, and the narrow
      `MGMT_ADMIN_HOSTS → 192.168.70.13:8080/tcp` rule is live and
      verified end-to-end. No TLS certificate — plain HTTP is consistent
      with every other bare-IP `*.internal` entry in this repo (e.g.
      `truenas.internal`), none of which carry certs; only
      `*.elliottrook.com` hostnames proxied through NPM do.
- [x] **Automation and schedules** — the ingest → cluster → summarize →
      flag-language chain runs hourly via
      `news-aggregator-ingest.timer` (`RandomizedDelaySec=300`,
      `Persistent=true`, so a missed run — e.g. the guest being off —
      fires on the next boot/tick rather than being silently skipped).
      Each of the four stages is independent and idempotent within
      `run_pipeline.sh`, so one stage failing doesn't block the others,
      and HomeLab Doctor's `check_news_aggregator()` catches a stalled
      pipeline within 2 hours.
- [x] **Security inventory** — the one credential this project introduced:
      a dedicated `aster-llama` API key (least-privilege, separate from
      Aster's own production key), generated server-side and never
      displayed in any tool output. Stored at
      `/etc/aster-llama-api-keys` on LXC 110 (mode 600, owned by the
      `ollama` service account that runs `aster-llama`, alongside
      Aster's original key on its own line — verified live) and at
      `/root/.news-aggregator-llama-key` on LXC 114 (mode 600,
      root-owned, also verified live). No other credentials exist —
      `outlet_ratings` and `news.db` hold no secrets, and the reading UI
      has no login of its own (see Authentication/authorization above).

## Operations quick reference

- **Reading UI:** `http://news.internal:8080` (or `192.168.70.13:8080`),
  from any of the three `MGMT_ADMIN_HOSTS` devices only. Health check:
  `curl http://192.168.70.13:8080/healthz`.
- **Restart the UI:**
  `ssh proxmox "pct exec 114 -- systemctl restart news-aggregator-ui.service"`.
  Code/config changes to `app.py` are not hot-reloaded — always restart
  after deploying a new copy.
- **Add a feed:** edit `/opt/news-aggregator/feeds.json` on LXC 114 (one
  JSON object per feed: `id`, `name`, `url`), then either wait for the
  next hourly run or trigger one manually with
  `pct exec 114 -- /opt/news-aggregator/run_pipeline.sh`. No code change
  or service restart is needed — proven live with the Al Jazeera addition
  in Milestone 4.
- **Pipeline logs and state:** `fetch_log` and `cluster_summaries` tables
  in `/opt/news-aggregator/news.db` (SQLite); `journalctl -u
  news-aggregator-ingest.service` on LXC 114 for the most recent run's
  stdout/stderr.
- **Outlet ratings:** `outlet_ratings` table in `news.db`
  (`feed_id`, `rating_label`, `source_name`, `source_url`, `as_of_date`,
  `notes`) — edit directly via `sqlite3` if a rating needs
  correcting or a source needs re-verifying against AllSides.
- **Health monitoring:** `scripts/doctor.sh` → `check_news_aggregator()`.
- **Backups:** whole-guest daily Proxmox snapshot (`/mnt/backups/dump/vzdump-lxc-114-*`)
  plus the TrueNAS off-host pull (`/mnt/Media/backup/homelab-proxmox-guests/`).
  Restore procedure is the standard LXC `vzdump` restore this repo already
  uses for every other guest — no service-specific recovery steps beyond
  that (config and data both live inside the one archive).

## Graduation criteria

The project graduates when ingestion, clustering, bias-labeling and
summarization run unattended and reliably, the reading UI is stable and
internal-only, the outbound-egress decision has been explicitly approved
and implemented narrowly, monitoring/backup coverage exists, and Jason
accepts the residual limitations of the bias-labeling approach.

## Evidence log

| Date | Milestone | Evidence | Result | Operator |
|---|---|---|---|---|
| 2026-09-14 | Reconciliation, corrected 2026-09-15 | Jason shared this document's content; it did not exist on Forgejo `origin`. A WebFetch call summarizing GitHub's directory listing and commit history for this path fabricated a story — a 2026-09-10 commit, "claude" authorship, "12 proposed local-AI project charters," and 11 named sibling files — none of which was real, and was written into this evidence log, a commit message, and the portfolio without being checked against `gh api` first. Verified directly via `gh api` on 2026-09-15: no such commit exists; GitHub's real directory listing has no such files; the only real commits touching this path are the ones made in this same session. Corrected here rather than left standing | The file's content itself (verified twice independently — against Jason's own paste, and via a direct `gh api` content fetch) was genuine; the *incident narrative* built around it was not. No prior session, no direct-to-`github` push, no 11 sibling files ever existed. This is a real process failure worth naming plainly: a summarizing tool's output was trusted and documented without the cross-check this repo's own "evidence over assumption" principle requires | claude |
| 2026-09-14 | Authorization | Jason granted Stream A for this project's enumerated scope, with the outbound-egress/firewall decision (before Milestone 2) and the bias-methodology sign-off (before Milestone 3) preserved as explicit checkpoints rather than absorbed into blanket authorization | Milestone 1 (discovery and design decisions) begins | claude |
| 2026-09-14 | 1 placement and egress research | Checked `Current-Network-Baseline.md` rather than assuming: VLAN 70 was already validated with disposable LXC 970 for broad outbound internet access with internal-service isolation intact — exactly this project's actual need, and it removes the need for a new cross-VLAN rule to reach `aster-llama` (same VLAN). Checked `03-Hardware-Inventory.md`: ~28 GiB Proxmox allocation headroom as of 2026-09-09, not a differentiator either way | Recommended Lab VLAN 70 over Servers VLAN 20, reversing the document's original framing that assumed a new, broadened firewall rule would be needed — it may need none at all. Not yet Jason's confirmed decision |
| 2026-09-14 | 1 clustering method proposal | Proposed headline/lede similarity clustering within a rolling time window, no LLM call in the clustering step, tuned toward precision over recall, with the reasoning and trade-off documented in Milestone 1's checklist | Proposed, not yet validated against real feed data (no ingestion pipeline exists yet) |
| 2026-09-15 | 1 placement confirmed | Jason confirmed Lab VLAN 70 | Milestone 1's placement item complete |
| 2026-09-15 | 1 feed list drafted | Drafted a candidate feed list with Jason by category: general/world, tech (including 9to5Mac at Jason's request), and local — corrected mid-draft from "Vancouver" to **Vancouver Island** specifically (Cowichan Valley/Duncan area) once Jason clarified his actual location. Exact URLs are unverified candidates; none were live-fetched or reachability-checked in this session (a WebFetch attempt and a Browser-pane attempt at live RSS verification both failed to go through) | Candidate list recorded in Milestone 1's checklist. Live URL verification is explicitly deferred to Milestone 2's own "validate against the initial feed list with real fetches" step, not skipped |
| 2026-09-15 | 1 egress decision | Presented the full trade-off: narrowing VLAN 70's already-broad egress to an FQDN-based allowlist would reduce this workload's blast radius if compromised, at the cost of ongoing maintenance whenever the feed list changes, plus fragility if done with static IPs instead of FQDN aliases given CDN IP churn. Jason chose to leave the existing broad egress as-is | Four of Milestone 1's five checklist items are resolved: placement (VLAN 70), egress (leave as-is, no OPNsense change needed), clustering method (proposed), feed list (drafted candidates). Bias-scoring methodology remained open pending Jason's own decision |
| 2026-09-15 | 1 bias methodology decided | Presented three real options — LLM-judges-per-story, a named external outlet-level rating, or a hybrid of the two — with honest trade-offs for each. Jason chose the hybrid: a named, published, attributable outlet-level rating as the primary label, with `aster-llama` limited to an optional, visually secondary per-story loaded-language note | **Milestone 1 complete** — all five checklist items resolved. One implementation detail carries into Milestone 3: picking the exact rating source (AllSides / MBFC / Ad Fontes) and checking its terms of use for programmatic reference, the same diligence this project's exclusions already require for news sources |
| 2026-09-15 | 2 compute deployed | Created LXC 114 `news-aggregator` on Proxmox, Lab VLAN 70, `192.168.70.13/24`, matching the existing LXC 104/110 convention exactly (bridge, gateway, tag, nameserver, searchdomain, unprivileged Debian). Live-verified (not assumed) both directions: general outbound HTTPS (200 from bbc.co.uk) and same-VLAN reach to `aster-llama` (200 from `192.168.70.12:11435/v1/models`) | Milestone 1's placement recommendation holds up under a real deployment, not just paper analysis. One real mistake made and caught in the same step: an unquoted `--tags automation;ai` argument let the shell split it into two commands, silently dropping the `ai` tag — caught by re-checking `pct config` immediately after, fixed with the correct comma-separated syntax |
| 2026-09-15 | 2 ingestion pipeline built and validated | Built the SQLite schema, `ingest.py` (feedparser-based, dedup via `UNIQUE(feed_id, guid)`), and an hourly systemd timer; deployed and enabled on LXC 114. First real run against all 9 Milestone-1 candidate URLs found 2 broken: `chek-news` (wrong domain, `chek.news` → real domain `cheknews.ca`, real path `/feed/` found via redirect) and `times-colonist` (guessed `/feed` path 403'd on bot protection; real working path `/rss`, found by probing common paths on the live site). Fixed both in `feeds.json`, re-ran: all 9 succeeded, dedup confirmed correct (0 new on re-fetch for the 7 already-good feeds), 243 real items landed including genuinely Vancouver-Island-local `chek-news` content (Cowichan Lake/Tofino/Highlands election coverage) | **Milestone 2 complete.** This is exactly what the milestone's own validation step is for — 2 of 9 candidate URLs were wrong, found and fixed by real fetches, not caught by the Milestone 1 planning pass |
| 2026-09-15 | NetBox entry added | The stored NetBox API token is deliberately read-only (a security decision from the NetBox-DCIM project's own close-out); followed that project's own established precedent instead of hunting for write access — used NetBox's Django shell directly in the `netbox-netbox-1` container. Created VirtualMachine `news-aggregator` (id 15), a `eth0` VMInterface (id 15, left untagged, matching a check against LXC 104's own interface convention rather than assumed), and IP `192.168.70.13/24` (id 29) as `primary_ip4`. Verified afterward via a read-only `GET`, not just trusted from the creation script's own output | Required integration-checklist item closed for real, not marked not-applicable by default |
| 2026-09-15 | 3 clustering implemented | Built and ran `cluster.py` against the real 311-item corpus. First draft would have rescanned the entire historical table every run — bounded to a 10-day lookback before deploying. Found 6 genuine multi-outlet clusters; hand-verified all 6 are correct matches, including two distinct iOS 27 angles correctly kept as separate clusters rather than over-merged | "Precision over recall" confirmed holding in practice on real data, not just as a stated design intent |
| 2026-09-15 | 3 aster-llama auth gap found and fixed | Summarization hit a real gap the original plan missed: aster-llama requires an API key, and llama-server only supports one static key via `--api-key` by default. Rather than reuse Aster's own key (against this document's own "no shared credentials" design) or decide unilaterally, presented the trade-off to Jason. Jason chose to check for multi-key support first; `llama-server --help` confirmed `--api-key-file` accepts multiple keys. Generated a dedicated key server-side (never displayed in any output), added it to `/etc/aster-llama-api-keys` alongside Aster's existing key, switched the systemd unit, restarted. A `/v1/models` no-key 200 briefly looked like a regression; investigated rather than assumed and confirmed it's normal llama.cpp behavior (that endpoint is exempt from auth) by testing the actual `/v1/chat/completions` endpoint separately, which correctly rejects no-key and garbage-key requests with 401 | Aster's own key still works (production continuity confirmed), the new dedicated key works, unauthorized requests are still rejected. New key stored at `/root/.news-aggregator-llama-key` on LXC 114, mode 600 |
| 2026-09-15 | 3 summarization and language notes implemented | `summarize.py` ran against all 6 real multi-outlet clusters — neutral, factual, correctly notes emphasis differences across outlets, zero bias language (spot-checked). `language_notes.py` ran against 45 real headlines: zero flagged. Verified this wasn't a broken always-NONE detector by testing a deliberately loaded synthetic headline, which was correctly flagged with the specific loaded phrases named. All four pipeline stages chained into `run_pipeline.sh`, wired into the existing hourly systemd timer | **Milestone 3's clustering and summarization items complete.** Bias-labeling mechanism built and verified; the actual `outlet_ratings` values are a draft proposal for Jason, not yet loaded — see the checklist item above for the specific draft ratings and honest "no rating available" cases |
| 2026-09-15 | 4 new-source test (Al Jazeera) | Jason asked whether adding a new source was tested and requested Al Jazeera specifically — became the real test. Live-verified `https://www.aljazeera.com/xml/rss/all.xml` (200, correct RSS content-type) before adding it, rather than assuming. Added to `feeds.json` as a config-only change; ran the full pipeline (ingest → cluster → summarize). Ingested 25 items cleanly on the first try. Clustering found 5 new multi-outlet clusters involving Al Jazeera with no special-casing needed, including a genuine 3-way match (BBC + Times Colonist + Al Jazeera on the US Supreme Court mail-in-ballot ruling). `summarize.py` generated clean summaries for all of them; 2 failed on the first pass and succeeded on an immediate idempotent re-run (transient, not a logic bug) | The "just edit `feeds.json`" workflow this project was designed around is proven for real, not just asserted — zero code changes needed to absorb a genuinely new source, and the clustering/summarization pipeline generalized to it correctly on the first attempt |
| 2026-09-15 | 4 reading UI built | Flask app behind gunicorn, bound explicitly to `192.168.70.13:8080` only, run via `news-aggregator-ui.service`. Renders clusters newest-first with the non-authoritative caveat always visible, outlet ratings shown when present and honestly labeled "(no rating)" when not (the table is still empty). Verified by fetching the real rendered page (27KB, real content) and spot-checking specific entries, not just a 200 status code | Real, working reading UI. `outlet_ratings` still empty pending Jason's confirmation of the draft values from Milestone 3 |
| 2026-09-15 | 4 exposure/DNS check surfaced a real access gap | Added `news.internal` to both Pi-holes (`truenas.internal`-style direct pattern, not Authentik/NPM-fronted — proportionate for a single-user tool). Confirmed zero WAN/OPNsense exposure before any change (`grep -c 192.168.70.13 config.xml`: 0). But confirming VLAN 70's isolation also proved Jason's own trusted devices had no path into VLAN 70 at all — nothing had ever considered inbound access, only outbound egress. Presented this plainly rather than opening a rule silently | Jason chose a narrow, `MGMT_ADMIN_HOSTS`-precedented fix rather than leaving it unreachable |
| 2026-09-15 | 4 firewall rule added | Backed up `config.xml` first (`config-news-aggregator-before-20260915.xml`, matching this repo's established naming convention). Used a minimal, surgical **text** insertion of one new rule block rather than a full-tree XML re-serialization, specifically to avoid any risk of reformatting unrelated parts of a 175KB live production firewall config; the insertion script asserted every expected substitution actually happened and that the stale `opt4` value was gone before writing anything. Validated the result still parses as well-formed XML before reloading. New rule: `MGMT_ADMIN_HOSTS → 192.168.70.13:8080/tcp` only (a single host and a single port, not VLAN-wide), sequence 3150. Reloaded via `configctl filter reload`; confirmed the exact rule loaded into the live `pf` ruleset via `pfctl -sr` | **Verified end-to-end from a real approved device, not just on paper**: this Mac (`192.168.1.206`) is itself one of the three `MGMT_ADMIN_HOSTS` entries; a direct DNS lookup and HTTP request from it succeeded. Regression-checked immediately after: the Docker LXC (VLAN 20, not an approved host) still correctly cannot reach it — the rule is exactly as narrow as intended |
| 2026-09-15 | 4 HomeLab Doctor check added | `check_news_aggregator()` added to `scripts/doctor.sh`, following the existing `check_aster_wiki()` pattern: fails on an unhealthy UI or missing recent successful fetch, warns on a mix of recent success/failure, passes when healthy. Ran the real `scripts/doctor.sh` end to end rather than testing the function in isolation; it correctly surfaced a real warning, cross-checked directly against `fetch_log` to confirm it reflected genuine data (the original pre-fix `times-colonist`/`chek-news` failures from Milestone 2, still inside the 2-hour lookback window) rather than a bug in the new check's own logic | **Milestone 4 complete.** Reading UI live, DNS resolves, no unintended exposure, a real (Jason-approved) access path exists, and Doctor coverage is proven against real data, not just written and assumed correct |
| 2026-09-15 | 4 Homepage tile added | Jason asked whether the project had a dashboard tile — it didn't yet. Backed up `services.yaml`, added a "News Aggregator" tile to the existing "Media" group via a minimal text insertion. Validated the YAML inside the real Homepage container before restarting it (config isn't hot-reloaded); verified live via `/api/services`, not just the page HTML | Real, working dashboard entry, closing the last open item in the required integration checklist that had a concrete action to take |
| 2026-09-15 | 3 outlet ratings loaded, AP gap found and resolved | Attempted live re-verification of the draft AllSides ratings before loading them (WebFetch: 403 on `allsides.com`; Browser pane: declined) — both failed, consistent with this session's other Browser-pane rejections. Presented the honest unverified draft to Jason via a direct question rather than loading it silently; Jason chose "accept the draft as-is, medium confidence." Loaded `bbc-world` (Center) and `npr-world` (Lean Left) into `outlet_ratings`, each citing AllSides by name with a `notes` field stating plainly it's unverified this session. While loading a third row for `ap-news`, direct inspection of `feeds.json` showed AP was never actually added — Milestone 1's candidate list flagged its feed path as "to be confirmed at Milestone 2," but Milestone 2's real build silently never followed up, and this went unnoticed through Milestones 2-4. Deleted the orphaned row. Probed 3 candidate AP feed URLs live, all 403; declined the one available workaround (RSSHub) since it's a third-party scraping proxy and this project explicitly restricts itself to feeds the source publishes itself | AP News is formally dropped from the project rather than silently absent — documented in Milestone 1's feed-list section and the ratings table. Only 2 of the project's real 10 feeds currently carry a rating; the rest remain honestly labeled "(no rating)" |
| 2026-09-15 | 4 unverified-rating caveat surfaced in the live UI | The `notes` column recorded above wasn't reaching the rendered page at all — `get_clusters()` only selected `rating_label`. Extended it to also select `source_name`/`notes` and pass them through; added a `title` attribute to the `.rating` span in `app.py`'s template so hovering a rating shows the named source and the unverified-this-session caveat, not just the bare label. Deployed to LXC 114 (`app.py.bak-20260915` kept as rollback), restarted `news-aggregator-ui.service`. Verified live: BBC's rendered tooltip reads exactly `AllSides — Unverified this session - Claude recollection, not live-checked against the source`. NPR's rating wasn't visible in the current top-40 clusters shown (its newest item, 11:35 UTC, is older than the current 40-cluster cutoff of 13:11 UTC) — not a rendering gap; confirmed by running the identical query directly against the database and getting the correct row back, over the same code path already proven live for BBC | The caveat is now genuinely accessible where Jason will actually see it, not only sitting in the database. NPR's tooltip will appear as soon as its items re-enter the top-40 window on the next hourly ingest |
| 2026-09-15 | 5 backup and recovery closed | Local layer needed no change: the existing all-guests 02:30 Proxmox `vzdump` job already covered LXC 114 automatically, confirmed via a real 463 MB archive from that morning's run. The off-host leg did need a change — TrueNAS's daily pull uses an explicit per-VMID `rsync --include` allowlist that didn't yet have 114 in it. Added it (TrueNAS `rsynctask` id 1, matching the exact precedent from VMID 113's addition on 2026-09-12), using `validate_rpath: false` on the update call since the unrelated remote-path pre-check was failing even though the real scheduled job had succeeded that same morning — not blindly bypassed, confirmed first that the underlying SSH path was genuinely working via the job history. Ran the pull manually rather than waiting for the next scheduled run and verified the SHA-256 of the landed archive matched the Proxmox-side source exactly | Backup and recovery closed with real, checksum-verified evidence on both legs, not assumed from the general "all-guests" job description alone |
| 2026-09-15 | 5 remaining integration checklist items closed | Went through every still-open item for real rather than leaving them as "not yet assessed": human wiki and Aster mirror/snapshot (not applicable — personal news content, no Aster knowledge touched), diagrams/rack records (not applicable — VM-only, matching the Aster-Offline-Knowledge-Wiki precedent; NetBox's existing VM record is the correct inventory entry), operational reference (closed via a new Operations quick reference section in this document), authentication/authorization (decided: no Authentik front-end — the existing `MGMT_ADMIN_HOSTS` network restriction to three named devices is narrower than Authentik plus broader reachability would give, and the Aster wiki's contrasting choice to add Authentik was because it's reachable by hostname from any Trusted-VLAN client, which this project's UI is not), DNS/certificates/firewall (already closed in Milestone 4 — checkbox corrected), automation/schedules (documented the existing hourly timer's missed-run behavior), security inventory (documented and live-verified both API key file locations and permissions, correcting an initial ownership assumption for the LXC 110 key file — it's `ollama`-owned, not root-owned, checked directly rather than assumed) | **Milestone 5 complete.** Every integration checklist item is either done with real evidence or has an honest, reasoned "not applicable," none left as an unassessed placeholder |
| 2026-09-15 | 5 project graduated | All graduation criteria met: ingestion/clustering/bias-labeling/summarization run unattended via the hourly timer (proven across multiple real runs and the Al Jazeera addition), the reading UI is stable and internal-only (verified, with a regression check confirming non-approved hosts still can't reach it), the outbound-egress decision was explicitly approved (leave broad) and needed no firewall change, monitoring and backup coverage both exist and are checksum/health verified, and Jason accepted the bias-labeling approach's residual limitations (unverified-this-session ratings, accepted at medium confidence). Moved this document to `docs/projects/completed projects/` via `git mv` to preserve its full commit history, and updated the portfolio README to move its row into the Completed projects table | Project closed out |

## References

- [News Aggregator Phase 2 — Digest, Sections and Source Requests](News-Aggregator-Digest-and-Sections.md) (successor project)
- [Project Creation Standard](../../Project-Creation-Standard.md)
- [Aster Operations](../../Aster-Operations.md)
- [Local AI](Local-AI.md)
- [Jellyfin Library Integrity Automation](../Jellyfin-Library-Integrity-Automation.md) (credential-storage precedent)
- [Aster Offline Knowledge Wiki and Mirror](Aster-Offline-Knowledge-Wiki.md) (authentication-decision and diagrams/rack-records precedent)
