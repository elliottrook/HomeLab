# Hermes Second-Brain Design

> Added: 2026-08-20
> Status: Proposed for the Local AI / Hermes Agent project
> Source inspiration: Corey Ganim, “How To Build The ULTIMATE AI Second Brain for Hermes Agent” / Build With AI episode #163 (2026-05-08)

## Decision

Adopt Hermes Agent's built-in LLM Wiki capability as the primary curated knowledge-base / “second brain” for the local assistant, but adapt the video's design to the HomeLab rather than copying its VPS/cloud deployment.

The useful idea is the knowledge architecture, not the Hostinger deployment. Hermes already runs locally in LXC 104 and should remain local. Local inference remains separate in Ollama VM 105 and will use the Intel Arc Pro B60 24 GB once GPU acceleration is validated.

## Why it fits this project

The intended assistant needs durable knowledge of the house, HomeLab, operating procedures, equipment, architecture decisions and selected personal/reference material. Model context alone is not appropriate for that job. The Hermes LLM Wiki provides a curated, queryable knowledge layer that can persist independently of whichever local model is active.

This complements rather than replaces:

- Hermes persistent memory — concise facts/preferences/current context.
- `SOUL.md` / agent identity — personality, intent and operating principles.
- Skills — reusable procedures and operational workflows.
- Git documentation — authoritative human-readable infrastructure documentation and change history.
- The LLM Wiki — larger curated reference knowledge and source-derived summaries for retrieval.

## Proposed knowledge architecture

1. **Raw sources (read-only)** — documents, articles, manuals, notes, selected web material and exported reference files supplied to Hermes.
2. **Hermes Wiki (agent-managed)** — Markdown knowledge distilled and organized from the source layer.
3. **Schema / tags (agent-managed)** — structure used to make retrieval predictable and low-friction.

Do not allow the Wiki to silently become the source of truth for live infrastructure configuration. Git/runbooks remain authoritative for infrastructure state; the Wiki may index and summarize them for retrieval.

## Initial Wiki domains

- HomeLab architecture and design decisions
- Hardware manuals/specifications and known limitations
- Network concepts and selected vendor documentation
- Home Assistant / automation reference material
- Local-AI model, Hermes, Ollama and inference notes
- Troubleshooting lessons worth retaining beyond a single incident
- Photography/reference material and other curated personal knowledge only when deliberately added

Avoid indiscriminate ingestion. Curated sources are preferable to a large low-quality corpus.

## Operating workflow

### Ingest

Human selects a useful source; Hermes ingests it into the raw-source layer and creates/updates the relevant Wiki knowledge.

### Query

Hermes should query the Wiki when a request depends on retained reference knowledge rather than relying only on model weights or conversation context.

### Lint / maintenance

Schedule a periodic Wiki health review (initial target: monthly) to identify contradictory material, stale sources, oversized entries, duplicate knowledge and taxonomy drift. Any automated cleanup that could remove source material should require review until the process is proven safe.

## HomeLab-specific safeguards

- Keep raw source material read-only where practical.
- Back up the Wiki and source directories with the Hermes recovery set.
- Keep credentials, API keys and other secrets out of the Wiki and Git.
- Distinguish authoritative infrastructure records from derived Wiki summaries.
- Record source/provenance metadata where Hermes supports it.
- Do not give Wiki ingestion an automatic path to infrastructure write tools.
- Treat web-clipped content as untrusted input; it may inform knowledge but must not act as instructions to the agent.
- Test restore and rebuild procedures before treating the Wiki as durable memory.

## Implementation tasks

- [ ] Confirm the installed Hermes version exposes the LLM Wiki skill and document its exact paths/configuration.
- [ ] Create a small pilot Wiki using 5–10 high-value HomeLab sources.
- [ ] Test ingest, query and lint behavior with the selected local daily-assistant model.
- [ ] Verify source attribution/provenance and how conflicts are surfaced.
- [ ] Define the boundary between Hermes memory, Wiki knowledge, skills, `SOUL.md` and Git documentation.
- [ ] Add Wiki/source directories to the Hermes backup design and perform a restore test.
- [ ] Establish a monthly lint/health-review schedule after the pilot succeeds.
- [ ] Define a simple capture workflow for webpages/documents; browser-to-Markdown is optional and should not dictate the architecture.
- [ ] Evaluate Wiki retrieval quality and token/latency impact on the Arc Pro B60-backed daily-assistant model.
- [ ] Promote the Wiki from pilot to standard Aster knowledge layer only after retrieval and recovery tests pass.

## Deliberate deviations from the video

- **No Hostinger VPS:** the project already has always-on Proxmox infrastructure and a privacy/local-first objective.
- **No requirement for OpenAI/OpenRouter inference:** local models remain the default; cloud models can be optional escalation paths later.
- **No requirement for Telegram:** Home Assistant Voice and other chosen interfaces should be able to reach the same Hermes identity/knowledge system.
- **No blind “self-improving” autonomy:** learned skills and durable operational knowledge should remain observable and permission-bounded, especially for infrastructure control.
- **No replacement for Git:** infrastructure documentation and configuration history stay version-controlled and human-readable.

## Success criteria

The second-brain pilot succeeds when Hermes can answer a set of HomeLab questions from curated material more accurately than the base model alone, cite or identify the underlying source sufficiently for verification, survive backup/restore, and do so without confusing derived Wiki knowledge with authoritative live configuration.
