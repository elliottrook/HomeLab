# News Aggregator (MuckScraper)

> Status: Active — Stream A. Milestone 1 (discovery and design decisions)
> starting.
>
> Project owner: Jason
>
> Proposed: 2026-09-10
>
> Started: 2026-09-14
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
  llama.cpp/Vulkan — see [Aster-Operations.md](../Aster-Operations.md). This
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
  (e.g. [Jellyfin-Library-Integrity-Automation.md](Jellyfin-Library-Integrity-Automation.md)'s
  "Safety and credentials" section).

## Open risks and decisions needing Jason's input

- **Outbound egress, revised 2026-09-14:** the premise that this needs a
  *new*, *broadened* firewall rule turned out to be wrong once checked
  against `Current-Network-Baseline.md` — see the placement recommendation
  below. If VLAN 70 is confirmed, general outbound internet is already
  validated and permitted there; the live question is whether to
  voluntarily *narrow* that existing access to a specific domain allowlist
  for this workload, not whether to open something new. Still Jason's
  decision either way, before Milestone 2.
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
- **Bias-scoring methodology and its labeling remain fully unresolved** —
  this is the most subjective piece of the whole project, is explicitly
  named as a required Stream A checkpoint in this document's header, and
  needs Jason's own decision, not a proposal from this session.
- **Feed list, refresh interval, and retention window** are all still
  undecided and directly affect both storage sizing and how much this looks
  like general web scraping vs. bounded feed reading.
- Stream A has been granted (see header) with the egress and bias-labeling
  decisions above preserved as explicit checkpoints.

## Milestones

### Milestone 1 — Discovery and design decisions

- [x] Resolve placement (VLAN/host) and record the decision here.
      **Recommendation, 2026-09-14: Lab VLAN 70**, not Servers VLAN 20.
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
      **Materially better than expected, 2026-09-14:** if VLAN 70 is
      confirmed as placement, this project may need **zero new firewall
      rules** — general outbound internet is already validated and
      permitted from VLAN 70. The actual open question is inverted from how
      this document originally framed it: not "what new broad egress do we
      open," but "should we *narrow* VLAN 70's already-broad egress down to
      a specific news-domain allowlist for this workload specifically, as
      defense-in-depth, even though it isn't required." That narrowing
      decision (and the exact feed-domain list it would need) is still
      Jason's to make — recorded here as the live open question, replacing
      the original framing.
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
- [ ] Choose and document the bias-scoring methodology and UI labeling.
      Deferred — this is the explicit Stream A checkpoint requiring Jason's
      own sign-off (see header), not something to propose unilaterally.
- [ ] Draft the initial feed list with Jason.

### Milestone 2 — Ingestion pipeline

- [ ] Deploy the chosen compute target.
- [ ] Implement scheduled feed fetch and raw-item storage.
- [ ] Validate against the initial feed list with real fetches.

### Milestone 3 — Clustering, bias labeling and summarization

- [ ] Implement clustering per the Milestone 1 design.
- [ ] Implement bias/slant labeling with explicit UI caveats.
- [ ] Wire summarization to the shared `aster-llama` endpoint.

### Milestone 4 — Reading UI and hardening

- [ ] Build the internal-only reading UI.
- [ ] Confirm no public exposure and correct internal DNS resolution.
- [ ] Add HomeLab Doctor and monitoring coverage.

### Milestone 5 — Documentation and graduation

- [ ] Complete the integration impact checklist below for real.
- [ ] Record final architecture and close out.

## Required integration impact checklist

- [ ] **HomeLab Doctor** — not yet assessed; expected to need a feed-fetch
      freshness/failure check once a schedule exists.
- [ ] **Monitoring/alerting** — not yet assessed.
- [ ] **Backup and recovery** — expected: datastore and config need
      inclusion in the existing backup pipeline; not yet designed.
- [ ] **NetBox** — new LXC/IP/VLAN assignment would need a NetBox entry once
      placement is decided.
- [ ] **Human wiki** — not yet assessed — proposal stage.
- [ ] **Aster mirror/snapshot** — not applicable; this project does not
      touch Aster's own knowledge or function set.
- [ ] **Operational reference and runbooks** — not yet assessed — proposal
      stage.
- [ ] **Repository documentation** — this document and the portfolio table
      are the current documentation; further updates expected at each
      milestone.
- [ ] **Diagrams/rack records** — expected once the new LXC is placed.
- [ ] **Homepage/service discovery** — a private link is expected once the
      reading UI exists.
- [ ] **Authentication/authorization** — not yet assessed; likely
      Authentik-fronted like other internal apps, decision deferred to
      Milestone 4.
- [ ] **DNS, certificates and firewall** — internal DNS record expected;
      outbound firewall rule is the open item above.
- [ ] **Automation and schedules** — the feed-fetch and clustering jobs are
      the core automation surface; ownership and missed-run behavior to be
      defined in Milestone 2.
- [ ] **Security inventory** — no credentials anticipated for v1 beyond
      possible per-source API keys; storage location to be recorded once
      known.

## Graduation criteria

The project graduates when ingestion, clustering, bias-labeling and
summarization run unattended and reliably, the reading UI is stable and
internal-only, the outbound-egress decision has been explicitly approved
and implemented narrowly, monitoring/backup coverage exists, and Jason
accepts the residual limitations of the bias-labeling approach.

## Evidence log

| Date | Milestone | Evidence | Result | Operator |
|---|---|---|---|---|
| 2026-09-10 | Proposal | Drafted this project document and 11 sibling proposals in one batch | Committed directly to the `github` remote's `main` branch, bypassing Forgejo `origin` — the repo's established authoritative push path. Not caught until 2026-09-14 | claude (session unknown) |
| 2026-09-14 | Reconciliation | Discovered via a user request to "get started" on this project that the file did not exist on Forgejo/`origin` at all; fetched and verified the exact content from GitHub's API before writing it into this repo; committed and pushed to Forgejo (`8ecb360`) | Forgejo restored as the authoritative copy. 11 sibling files from the same batch remain `github`-only and unreconciled | claude |
| 2026-09-14 | Authorization | Jason granted Stream A for this project's enumerated scope, with the outbound-egress/firewall decision (before Milestone 2) and the bias-methodology sign-off (before Milestone 3) preserved as explicit checkpoints rather than absorbed into blanket authorization | Milestone 1 (discovery and design decisions) begins | claude |
| 2026-09-14 | 1 placement and egress research | Checked `Current-Network-Baseline.md` rather than assuming: VLAN 70 was already validated with disposable LXC 970 for broad outbound internet access with internal-service isolation intact — exactly this project's actual need, and it removes the need for a new cross-VLAN rule to reach `aster-llama` (same VLAN). Checked `03-Hardware-Inventory.md`: ~28 GiB Proxmox allocation headroom as of 2026-09-09, not a differentiator either way | Recommended Lab VLAN 70 over Servers VLAN 20, reversing the document's original framing that assumed a new, broadened firewall rule would be needed — it may need none at all. Not yet Jason's confirmed decision |
| 2026-09-14 | 1 clustering method proposal | Proposed headline/lede similarity clustering within a rolling time window, no LLM call in the clustering step, tuned toward precision over recall, with the reasoning and trade-off documented in Milestone 1's checklist | Proposed, not yet validated against real feed data (no ingestion pipeline exists yet) |

## References

- [Project Creation Standard](../Project-Creation-Standard.md)
- [Aster Operations](../Aster-Operations.md)
- [Local AI](completed%20projects/Local-AI.md)
- [Jellyfin Library Integrity Automation](Jellyfin-Library-Integrity-Automation.md) (credential-storage precedent)
