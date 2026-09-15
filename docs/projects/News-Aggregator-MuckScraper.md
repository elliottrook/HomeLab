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

- **Outbound egress is a real firewall/network-security decision, not a
  sandbox setting.** A deployed service on a lab VLAN making outbound HTTPS
  calls to many external news-outlet domains is a materially different
  thing from Claude Code's own `sandbox.network.allowedDomains`, which only
  governs what Claude Code itself can reach from the laptop — it says
  nothing about what a deployed lab service may reach. Whatever egress this
  project needs must be an explicit, narrowly-scoped OPNsense decision
  Jason approves before Milestone 2, per this repo's "changes that alter
  the network's security posture" rule.
- **Placement is undecided**: new LXC on Lab VLAN 70 (alongside other AI
  infra) vs. Servers VLAN 20 (alongside media/automation). Neither has been
  evaluated against capacity or trust-boundary considerations yet.
- **Clustering method is unspecified.** Whatever approach is chosen needs a
  concrete false-positive/false-negative expectation before it's trusted,
  not just "seems to work."
- **Bias-scoring methodology and its labeling are unresolved** — this is
  the most subjective piece of the whole project and needs Jason's explicit
  sign-off on both the method and how prominently the "automated estimate,
  not authoritative" caveat is shown before any output reaches a UI.
- **Feed list, refresh interval, and retention window** are all undecided
  and directly affect both storage sizing and how much this looks like
  general web scraping vs. bounded feed reading.
- No stream (M or A) has been selected. Implementation must not begin until
  Jason chooses one and the risks above are addressed.

## Milestones

### Milestone 1 — Discovery and design decisions

- [ ] Resolve placement (VLAN/host) and record the decision here.
- [ ] Resolve the outbound-egress/firewall question with Jason explicitly.
- [ ] Choose and document the clustering method and its expected accuracy
      trade-offs.
- [ ] Choose and document the bias-scoring methodology and UI labeling.
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

## References

- [Project Creation Standard](../Project-Creation-Standard.md)
- [Aster Operations](../Aster-Operations.md)
- [Local AI](completed%20projects/Local-AI.md)
- [Jellyfin Library Integrity Automation](Jellyfin-Library-Integrity-Automation.md) (credential-storage precedent)
