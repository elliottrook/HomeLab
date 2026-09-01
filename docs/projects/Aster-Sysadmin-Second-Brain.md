# Aster Sysadmin Second-Brain Project

> Status: Active
>
> Project owner: Jason
>
> Started: 2026-09-01

## Purpose

Graduate Aster from a bounded HomeLab question-answering pilot into a
trustworthy local sysadmin assistant with a clean, recoverable, source-aware
operational knowledge system. Graduation requires demonstrated correctness,
conflict handling, security, recovery and acceptable performance; it does not
grant unbounded infrastructure autonomy.

The new `homelab-reference` repository is the candidate current-state
operational source. The existing `homelab` repository remains the project,
decision and evidence record.

## Authority model

Each kind of fact has exactly one declared authority:

1. **Live state** answers transient health and runtime questions. A mismatch
   with documentation is reported as drift; live state does not silently
   rewrite Git.
2. **Domain systems of record** own structured facts when explicitly adopted
   (for example, NetBox after its separate cutover gate passes).
3. **`homelab-reference`** owns reviewed current operational descriptions,
   dependency maps and approved runbooks.
4. **`homelab`** owns project scope, decisions, dated evidence, change history
   and future plans.
5. **Derived Aster memory/wiki entries** may summarize the layers above but
   are never authoritative and must preserve provenance and review dates.

Until NetBox's separate project reaches cutover, reviewed reference Markdown
remains authoritative for current network and inventory descriptions. Known
stale or physically unverified material must be excluded from Aster's
authoritative corpus or labelled uncertain.

## Knowledge boundaries

| Layer | Purpose | Mutability | Authority |
|---|---|---|---|
| Aster identity/system prompt | Behavior, honesty, safety and response style | Code-reviewed | Policy only |
| Conversation state | Current interaction context | Ephemeral | Never factual authority |
| Operational reference | Current topology, inventory, dependencies and runbooks | Human-reviewed Git | Current operations |
| Project/evidence repository | Decisions, experiments, milestones and history | Human-reviewed Git | Why/history/plans |
| Derived memory/wiki | Durable lessons and concise cross-source summaries | Generated then reviewed | Non-authoritative |
| Skills/tools | Bounded procedures and allowlisted actions | Code-reviewed and tested | Capability, not knowledge |

## Security and autonomy boundary

- Begin read-only. Retrieval, diagnosis, comparison, health checks and proposed
  commands do not imply permission to change infrastructure.
- No arbitrary shell, arbitrary filesystem path, arbitrary network target,
  credential retrieval or user-supplied command execution.
- Any future write function is one task-specific allowlisted operation with
  validation, audit output, timeout, rollback and a separate approval policy.
- Firewall, VLAN, credentials, encryption, ACL and inter-host trust changes
  continue to require explicit approval for the specific change, matching the
  operational reference's change discipline.
- Aster must surface uncertainty, stale sources and conflicts instead of
  selecting a convenient answer silently.

## Milestone 1 — Reference repository qualification

- [x] Resolve the repository's contradictory source-of-truth wording.
- [x] Separate current, uncertain and historical content so known-stale rack
  placement cannot be retrieved as current fact.
- [x] Add repository-wide provenance, review-date and authority conventions.
- [x] Add automated structure, link, secret-pattern, stale-marker and authority
  linting.
- [x] Reconcile Aster/local-AI operations with the deployed 2026-09-01 state.
- [x] Record the update workflow between `homelab`, `homelab-reference` and
  future NetBox exports.

Completion gate: the repository has an unambiguous authority contract, passes
its lint suite and contains no known-unlabelled stale current-state claim.

## Milestone 2 — Memory/wiki and ingestion

- [x] Define the initial wiki taxonomy and entry schema.
- [x] Create reviewed derived-memory entries for durable operational lessons.
- [x] Replace the hand-maintained snapshot allowlist with a manifest that
  records repository, authority, destination and sensitivity.
- [x] Build deterministic snapshots with checksums and a provenance index.
- [x] Reject secrets, unsafe file types, broken sources and unreviewed external
  content during build.
- [x] Teach Aster authority-aware retrieval across reference, project and
  derived-memory layers.

Completion gate: the same source commit deterministically produces the same
validated snapshot, and every retrieved result identifies its layer,
authority and source path. **Passed 2026-09-01** for the accepted clean source
commits recorded in the evidence log.

## Milestone 3 — Recovery and maintenance

- [ ] Include source repositories, manifest and deployed snapshot in verified
  local, off-host and encrypted off-site coverage.
- [ ] Rebuild the snapshot from clean Git checkouts.
- [ ] Perform an isolated restore and compare checksums and query behavior.
- [ ] Add a monthly knowledge-health review for drift, contradictions, broken
  provenance, oversized entries and taxonomy decay.
- [ ] Document rollback to the last accepted snapshot.

Completion gate: a clean environment can reproduce and restore the accepted
knowledge layer without copying untracked state or secrets.

## Milestone 4 — Teacher/pupil evaluation

- [x] Establish a versioned evaluation set covering topology, addressing,
  dependencies, incidents, backups, access control, uncertainty, conflicts and
  refusal boundaries.
- [x] Record expected sources and required/forbidden claims per question.
- [x] Test cold and warm latency, prompt tokens, decode rate and context headroom.
- [x] Test stale-source traps, prompt injection inside knowledge, missing facts,
  ambiguous changes and unsafe requests.
- [x] Iterate sources, retrieval and prompts until every critical test passes
  repeatedly without source or safety regressions.

Completion gate: all critical correctness/security tests and the documented
performance budget pass on repeated runs using the production model. **Passed
for the current read-only knowledge capability on 2026-09-01:** two independent
13-case runs passed on the same clean snapshot. Observed end-to-end latency was
21.6–52.8 seconds in the second run (the broader earlier range was 21.6–63.6
seconds); this is acceptable for deliberate single-user sysadmin consultation,
not interactive command execution.

## Milestone 5 — Bounded sysadmin capability

- [x] Inventory the minimum live read-only signal Aster needs beyond its own
  health: a sanitized HomeLab Doctor summary produced outside Aster.
- [x] Add only task-specific, source-restricted read-only tools: Aster reads a
  bounded JSON report under `/var/lib/aster/health`; it has no shell, network,
  credential or arbitrary-file capability.
- [ ] Re-run the full evaluation set with live-state tools enabled.
- [ ] Propose any write capability separately, with exact access, approval,
  validation and rollback boundaries; do not infer it from graduation.
- [ ] Record final ownership, accepted limitations and escalation rules.

Completion gate: Aster can safely diagnose and guide routine HomeLab operations
from authoritative knowledge and bounded live evidence. Any action authority is
explicitly enumerated rather than implied.

## Graduation criteria

Aster graduates only when:

- every milestone completion gate has passed with recorded evidence;
- the knowledge set survives a verified isolated restore;
- every critical evaluation passes repeatedly with correct provenance;
- performance remains inside the accepted production budget;
- secrets and private sources remain outside Git and model output;
- security boundaries and refusal behavior pass adversarial tests;
- production HomeLab operation remains independent of Aster; and
- Jason retains an explicit approval boundary for material changes.

## Evidence log

| Date | Milestone | Evidence | Result |
|---|---|---|---|
| 2026-09-01 | Discovery | Read all Aster/second-brain project literature and all 15 files in `homelab-reference`; compared authority, staleness, operations and safeguards | Reference repository is a strong foundation but requires authority, provenance, lint and staleness hardening before ingestion |
| 2026-09-01 | 1 | Added the operational reference contract, authority/review/source metadata to 13 pages, removed the unverified rack table, reconciled Aster operations and passed `lint_reference.py` | Reference qualification gate passed locally |
| 2026-09-01 | 2 | Added four derived-memory wiki pages, a 23-source manifest, deterministic archive builder, per-file SHA-256 provenance and authority-aware retrieval | Two dirty-development builds were byte-identical; clean-commit reproduction and deployed query validation remain |
| 2026-09-01 | 2 | Built the clean 23-source snapshot twice from detached clean checkouts and compared SHA-256; provenance records both repository commits with `dirty: false` | Deterministic snapshot gate passed |
| 2026-09-01 | 4 | Ran 13 in-container unit tests and two independent 13-case live exams against LXC 104; reviewed all answer text, then corrected source/retrieval guest-type ambiguities | 26/26 critical cases passed on the accepted LXC 104/LXC 110 production path |
| 2026-09-01 | 3 | Reviewed backup evidence for the source repositories, manifest and deployed snapshot | LXC 110 off-host mirror and isolated archive restore remain explicitly pending; graduation remains blocked until this is verified |
| 2026-09-01 | 5 | Added a root/operator-produced, schema-validated HomeLab Doctor summary tool; systemd grants Aster read-only access only to that report directory | Local implementation and unit tests complete; deployment and live evaluation remain pending |
