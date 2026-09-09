# Aster Sysadmin Second-Brain Project

> Status: Graduated — read-only advisor
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

- [x] Include source repositories, manifest and deployed snapshot in verified
  local, off-host and encrypted off-site coverage.
- [x] Rebuild the snapshot from clean Git checkouts.
- [x] Perform an isolated restore and compare checksums and query behavior.
- [x] Add a monthly knowledge-health review for drift, contradictions, broken
  provenance, oversized entries and taxonomy decay.
- [x] Document rollback to the last accepted snapshot.

Completion gate: a clean environment can reproduce and restore the accepted
knowledge layer without copying untracked state or secrets. **Passed
2026-09-08:** archive carriers, source provenance and the independently
recoverable encrypted-relay configuration have all been verified.

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
- [x] Re-run the full evaluation set with live-state tools enabled.
- [x] Propose any write capability separately, with exact access, approval,
  validation and rollback boundaries; do not infer it from graduation.
- [x] Record final ownership, accepted limitations and escalation rules.

Completion gate: Aster can safely diagnose and guide routine HomeLab operations
from authoritative knowledge and bounded live evidence. Any action authority is
explicitly enumerated rather than implied.

### Capability decision and ownership

No write capability is proposed for graduation. Aster remains a read-only
advisor: it may retrieve reviewed knowledge and the operator-produced health
summary, identify drift, and propose a bounded change for Jason to review. It
cannot execute commands, read secrets, write files, alter network policy, or
contact arbitrary endpoints. A future write feature requires its own project
record naming the exact target, least-privilege identity, validation, audit
record, timeout, rollback and approval moment.

Jason owns source review, material-change approval, credentials, backup
destinations and recovery decisions. `homelab-reference` owners maintain
current operational facts; the `homelab` project record maintains evidence and
decisions. The monthly review detects drift but does not edit anything. Aster
must escalate missing, stale, contradictory or insufficient evidence instead
of guessing.

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
| 2026-09-01 | 3 | Verified the LXC 110 archive integrity, restored it into isolated stopped LXC 980 with its network link down, inspected the service layout, then destroyed the temporary guest | Restore mechanics pass, but the archive did not provide verified model-artifact coverage and service configuration differs from production; an off-host mirror plus a fresh isolated restore remain required |
| 2026-09-01 | 5 | Deployed the root-produced `/var/lib/aster/health/latest.json` report with `root:aster` ownership and `0640` mode; ran 15 in-container unit tests and the full 14-case live graduation suite | 15/15 unit tests and 14/14 live cases passed; report correctly surfaced current warnings/failures without giving Aster shell, credentials, arbitrary files or new network access |
| 2026-09-02 | Recovery | Copied the 2026-09-01 LXC 110 archive to an independent root-only TrueNAS stopgap, matched its SHA-256, then restored that copy as stopped, network-isolated LXC 980 | Both active model blobs matched their content-addressed SHA-256 values; recovered unit differs only by the later `TimeoutStartSec=5min` improvement. Guest remains stopped to avoid a second production-GPU mapping |
| 2026-09-07 | 3 | Ran the monthly knowledge review from clean `homelab` and `homelab-reference` commits, then built, SHA-256 matched, temporarily restored and queried the 23-source snapshot from LXC 104 | Provenance, authority-aware retrieval and deterministic rebuild passed; root-only TrueNAS stopgap holds the snapshot. Encrypted off-site coverage remains incomplete |
| 2026-09-07 | 3 | Verified current LXC 104 and Forgejo LXC 108 archives byte-for-byte between Proxmox and the off-host TrueNAS copy, confirmed the LXC 104 archive contains the deployed snapshot provenance for clean `homelab` commit `09cd8a3873bb5230336cc4416a8d165606da761c` and clean `homelab-reference` commit `3e0618f52fd5ee87ee80ba9d346cabd243ed1445`, and confirmed the LXC 108 archive contains both source repositories. Recovered both complete archives as decrypted streams from the new encrypted IDrive relay and matched SHA-256 (`fac9064f1b91e02c439c8dcfb6e7cf490b92e690e1f44bc42b1a9af9cbd7eb27` for LXC 104; `28ff5f94351639362ab4f95e9513287079d8517ffbcc1f3bc15ceee9cd054e06` for LXC 108) | Local, off-host and encrypted-upload byte integrity are proven for the exact Aster recovery carriers. Graduation remains blocked because the new relay's encryption configuration/recovery material does not yet have its independently protected recovery copy, so recovery currently still depends on the live relay |
| 2026-09-08 | 3 | Confirmed the relay's initial encrypted IDrive sync completed successfully at `2026-09-08 04:06:11 UTC` (111,289 objects; 706.315 GiB) and read-only-listed both required Aster archives in `idrive-crypt:` afterward | Full sync now covers the two verified Aster recovery carriers. The independent protected recovery copy for the crypt configuration/material remains the sole unclosed recovery-material condition, so the Milestone 3 checkbox stays open |
| 2026-09-08 | 4 | Expanded authority-language retrieval, then added and deployed an explicit secret-retrieval boundary after adversarial testing showed that a refusal still pointed toward a live config. Rotated the affected Aster credentials, confirmed matching agent/inference keys and authenticated health, and reran the targeted authority and credential-safety regressions | Both targeted regressions passed; the credential response now refers only to an approved recovery/administrative-access procedure and does not point to live configuration. This is targeted training evidence, not a replacement for the original repeated graduation-performance runs |
| 2026-09-08 | 3 | Created a checksum-verified, mode-restricted independent copy of LXC 112's `rclone.conf` and `idrive-crypt` recovery material in the existing protected Mac recovery source, `~/lab/private-backups/recovery/idrive-relay/2026-09-08/`; verified its existing Mac→TrueNAS pull, encrypted IDrive relay copy and a temporary recovery drill that used only the copied configuration to decrypt-list the off-site bundle | This removes dependence on the relay guest's disk for the crypt material and completes the Milestone 3 coverage gate |
| 2026-09-08 | Graduation | Ran two independent production-path 14-case graduation suites after the authority, credential-boundary and response-limit regressions. Every case passed in both runs; worst end-to-end latency was 44.4 s in run one and 47.5 s in run two, both within the 52.8 s production budget. | Aster has graduated as a bounded read-only sysadmin advisor. It retains no action authority; material infrastructure changes still require Jason's explicit approval. |
| 2026-09-08 | 2 | Added derived-memory lessons for recovery dependency order and credential/recovery boundaries, each with source links, review dates, explicit non-authority and no secret-bearing material. Added both to the knowledge manifest for the next reviewed snapshot build. | Memory taxonomy now captures the post-graduation recovery and security lessons without widening Aster's access or making memory authoritative. |
| 2026-09-08 | 2 | Ran a clean, deterministic 25-source snapshot review from `homelab` commit `5d54eb113929b34d5ab2468264dbe8a6b9b944fa` and `homelab-reference` commit `6548731be984293ed19c50084eed419d77281f92`; accepted and activated archive SHA-256 `48feab8a8494fd61d86326d779fab0bf3d44d7952a6433cb16f346b923081087` on LXC 104. | The prior deployed directory remains retained as a rollback. Aster-account retrieval confirmed both new derived lessons are discoverable, while broad recovery queries continue to favor the authoritative runbook. |
