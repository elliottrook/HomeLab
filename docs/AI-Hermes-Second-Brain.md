# Aster Second-Brain Design

> Added: 2026-08-20
> Status: Initial bounded implementation deployed in Aster; broader ingestion remains proposed
> Source inspiration: Corey Ganim, “How To Build The ULTIMATE AI Second Brain for Hermes Agent” / Build With AI episode #163 (2026-05-08)

## Decision

Adopt the video's curated, source-aware knowledge architecture for the local assistant without coupling it to Hermes or copying its VPS/cloud deployment.

The useful idea is the knowledge architecture, not the original harness. Aster now runs locally in LXC 104 with a small curated Git-document snapshot and source-attributed retrieval. Local inference remains separate in llama.cpp LXC 110 with Intel Arc Pro B60 24 GB Vulkan acceleration; Hermes and Ollama are disabled but retained as rollback paths. SYCL/Level Zero was confirmed blocked by the current 256 MB physical BAR rather than a software-packaging mismatch. See [`docs/projects/Local-AI.md`](projects/Local-AI.md) for the evidence trail and [`docs/Aster-Operations.md`](Aster-Operations.md) for the live service.

## Why it fits this project

The intended assistant needs durable knowledge of the house, HomeLab, operating procedures, equipment, architecture decisions and selected personal/reference material. Model context alone is not appropriate for that job. Aster's first implementation provides a curated, queryable snapshot that can persist independently of whichever local model is active.

This complements rather than replaces:

- Aster's bounded conversation state — concise current-session context.
- The Aster system prompt — identity, intent and operating principles.
- Skills — reusable procedures and operational workflows.
- Git documentation — authoritative human-readable infrastructure documentation and change history.
- The curated snapshot — selected Git records and, later, reviewed source-derived summaries for retrieval.

## Proposed knowledge architecture

1. **Authoritative sources (read-only)** — selected Git documents, manuals, notes and deliberately supplied reference files.
2. **Aster knowledge snapshot (deployed)** — a curated copy under `/var/lib/aster/knowledge`, searched by an allowlisted read-only function.
3. **Derived knowledge (future)** — reviewed Markdown summaries plus schema/tags where they improve retrieval.

Do not allow the Wiki to silently become the source of truth for live infrastructure configuration. Git/runbooks remain authoritative for infrastructure state; the Wiki may index and summarize them for retrieval.

## Initial Wiki domains

- HomeLab architecture and design decisions
- Hardware manuals/specifications and known limitations
- Network concepts and selected vendor documentation
- Home Assistant / automation reference material
- Local-AI model, Aster, llama.cpp and inference notes — e.g. the B60's
  Vulkan-vs-SYCL backend investigation and its firmware BAR conclusion,
  once ingestion is running (source of truth stays
  [`docs/projects/Local-AI.md`](projects/Local-AI.md); the Wiki entry
  would be a derived summary, not the record itself)
- Troubleshooting lessons worth retaining beyond a single incident
- Photography/reference material and other curated personal knowledge only when deliberately added

Avoid indiscriminate ingestion. Curated sources are preferable to a large low-quality corpus.

## Operating workflow

### Ingest

For the deployed bounded phase, a human selects and reviews useful Git sources before refreshing the snapshot. Future ingestion may create or update derived knowledge, but must not silently promote it to authority.

### Query

Aster queries the snapshot when a request depends on retained HomeLab knowledge rather than relying only on model weights or conversation context.

### Lint / maintenance

Schedule a periodic Wiki health review (initial target: monthly) to identify contradictory material, stale sources, oversized entries, duplicate knowledge and taxonomy drift. Any automated cleanup that could remove source material should require review until the process is proven safe.

## HomeLab-specific safeguards

- Keep raw source material read-only where practical.
- Back up the Aster snapshot and future source directories with the Aster recovery set.
- Keep credentials, API keys and other secrets out of the Wiki and Git.
- Distinguish authoritative infrastructure records from derived Wiki summaries.
- Preserve source paths/provenance in retrieval results.
- Do not give Wiki ingestion an automatic path to infrastructure write tools.
- Treat web-clipped content as untrusted input; it may inform knowledge but must not act as instructions to the agent.
- Test restore and rebuild procedures before treating the Wiki as durable memory.

## Implementation tasks

- [x] Create a small curated snapshot from high-value HomeLab Git sources.
- [x] Test query behavior with the selected local daily-assistant model.
- [x] Return source paths and prefer current inventory for present-state hardware questions.
- [x] Keep infrastructure Git authoritative and treat retrieved text as untrusted factual context, not instructions.
- [ ] Define the boundary between conversation state, derived knowledge, skills, Aster identity and Git documentation.
- [ ] Add the knowledge snapshot to verified off-host backup and perform an isolated restore test.
- [ ] Establish a monthly lint/health-review schedule after the pilot succeeds.
- [ ] Define a simple capture workflow for webpages/documents; browser-to-Markdown is optional and should not dictate the architecture.
- [ ] Evaluate Wiki retrieval quality and token/latency impact on the Arc Pro B60-backed daily-assistant model.
- [ ] Promote the Wiki from pilot to standard Aster knowledge layer only after retrieval and recovery tests pass.

## Deliberate deviations from the video

- **No Hostinger VPS:** the project already has always-on Proxmox infrastructure and a privacy/local-first objective.
- **No requirement for OpenAI/OpenRouter inference:** local models remain the default; cloud models can be optional escalation paths later.
- **No requirement for Telegram:** Home Assistant Voice and other chosen interfaces should be able to reach the same Aster identity/knowledge system.
- **No blind “self-improving” autonomy:** learned skills and durable operational knowledge should remain observable and permission-bounded, especially for infrastructure control.
- **No replacement for Git:** infrastructure documentation and configuration history stay version-controlled and human-readable.

## Success criteria

The first retrieval gate is passed: Aster answered the current B60/BAR question from the curated inventory and named its source. Full second-brain success still requires broader evaluation plus verified backup/restore, without confusing derived knowledge with authoritative live configuration.
