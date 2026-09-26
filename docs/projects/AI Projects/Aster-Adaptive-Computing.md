# Aster Adaptive Computing — Foundation and First Evidence Loop

**Status:** Active — Stream A; M0 complete; M1 Stage1 installed and verified;
Stage2 identity/assurance gates remain open; M2 offline foundation verified;
M3 controlled comparisons retained Aster/rules; M4 offline verifier and storage
review design prepared, independent custody/review gates still open.

**Owner:** Jason.

**Proposed:** 2026-09-25.

**Authorization stream:** Stream A — Autonomous, explicitly authorized by Jason on 2026-09-25: create the AI Projects folder, adopt these documents, mark superseded plans and archive them, and start this project. The authorization covers the bounded foundation milestones and their existing exclusions, not general administrator authority, later-release scope or automatic promotion authority. Repository/platform controls and per-push confirmation remain mandatory.

**Canonical project document:** `docs/projects/AI Projects/Aster-Adaptive-Computing.md`. Assessment and inventory are dated supporting evidence; this document governs implementation.

**Supporting assessment:** [architecture](ASSESSMENT.md), [inventory](INVENTORY.md), [harness comparison](HARNESS-ALTERNATIVES.md), [research log](research-log.md).

## 1. Purpose and desired outcome

Establish one coherent programme in which Aster's independently replaceable components improve through retained evidence, with deterministic authority and human governance. Deliver a finite foundation release that can compare routing and harness choices, explain outcomes, reject regressions and demonstrate one complete evidence-backed decision cycle.

Success does not require replacing the existing runtime or deploying a learned router. Keeping a simpler baseline after a reproducible comparison is a valid engineering result. It must still leave usable contracts, measurements, decision records and an operational improvement process—not merely another research report.

## 2. Current state and evidence

The assessment verified main `e50b670b906f397e1e70b6d51cf07e88235ac5c5` at Forgejo and its GitHub mirror. The checkout was behind; reverify the baseline before implementation. Existing user edits must be preserved.

Aster is the active bounded Python harness, with local llama.cpp inference, speech, source-local reports, Companion, Authentik, monitoring and an emerging AI-PAM integration. Hermes is not a required runtime dependency. Historical Hermes measurements demonstrate substantial prompt/tool overhead; current alternatives have not been benchmarked on this lab.

AI-PAM has implemented milestones and an initial read integration, but not full graduation. Isolated tests found missing originating-agent binding at consume and approvals surviving demotion to probation. Repair and verification are prerequisites to broadening broker use. No production exploit was attempted. Most components share one Proxmox host; host-loss availability is not promised by this project.

## 3. Scope and exclusions

**Foundation release includes:** state reconciliation; security-boundary regression gates; Decision, Harness Run, Capability, Outcome and Experiment contracts; a minimal authorized catalogue projection; current-runtime baseline; a bounded harness/routing comparison; local evidence storage; an opt-in read-only shadow pilot; and one evaluated reversible candidate with promotion or rejection and continuing observation.

**Excludes:** general shell/admin agents; automatic privilege changes; automatic security/evaluator-policy changes; new public ingress; production destructive tests; wholesale repository moves; new hardware; replacing Authentik/OpenBao; adopting Octelium; installing multiple orchestration/evaluation platforms; indiscriminate raw conversation retention; broad personal-data integration; an automatic production-remediation programme. Routine local implementation and synthetic evaluation are authorized within this foundation scope. New major dependencies, deployment targets, data collection and production boundary changes require the relevant milestone risk/compatibility gate; no such deployment is included in this initial baseline commit.

Full voice replacement, private/public live composition and guarded remediation remain later release gates in this same programme. Existing domain projects remain historical evidence and independently bounded implementation dependencies; their permissions do not transfer automatically.

## 4. Authority model

Jason owns authorization, risk acceptance and final promotion. Forgejo holds intended configuration and sanitized history; live observations establish actual state; NetBox owns adopted inventory facts; operational references own current procedures; wiki and Aster mirror remain derived consumers with provenance.

Decision engines and harnesses propose. Deterministic policy and AI-PAM authorize exact requests. Narrow adapters execute. Independent checks verify. The Learning Plane can create candidates and evidence, never grant permissions or rewrite its evaluator. Existing remote-write approval rules remain unchanged.

## 5. Architecture and data flows

Preserve the existing runtime and serving boundary. Add interfaces incrementally, initially in-process where possible:

`ingress → policy-constrained Decision function → bounded Harness Run → fixture/read adapter → independently labeled outcome → evidence store → experiment → human decision → versioned candidate/canary`

The household deterministic path bypasses the agent harness. Existing permitted capabilities remain reachable when experimental routing/learning is disabled. Neither CPU routing nor evidence collection requires the GPU. No new externally reachable port is required for the offline stages. Any pilot endpoint, identity, port or storage placement must be specified at its deployment gate after resource measurement.

The catalogue references AI-PAM permissions; it does not duplicate or override them. Model/skill/agent/experiment records are related data, not separate mandatory servers. Runtime data remains outside Git; sanitized manifests and decisions can enter Git after review. Harness-specific objects must not leak into stable APIs.

## 6. Privacy and security

Default to synthetic fixtures and no durable raw prompts. Define permitted features, retention, access and consent before real collection. Exclude credentials, personal calendar/email/document contents and approval secrets from initial datasets. Treat embeddings and pseudonyms as potentially sensitive. Disable unapproved external tracing and model-provider egress.

Experimental tools have no production credentials and cannot invoke effectful adapters. A policy DENY, revoked identity or expired approval must survive every harness substitution. Reauthorize after pause/restart; distinguish uncertain external outcomes from retryable failures. Bound model calls, fan-out, wall time and tokens. New agents begin with no implied scope.

Broker corrective work is tracked here as a prerequisite work package, with links to the existing AI-PAM evidence, rather than inventing a competing broker. It requires explicit bounded deployment approval and independent regression checks before any pilot relies on the changed path.

## 7. Pre-start risk assessment

| Risk | Likelihood / impact | Controls and residual risk |
|---|---|---|
| Framework swap reproduces prompt overhead | Plausible / poor responsiveness | Same-model comparison, prompt/call tracing, minimal tools, baseline retained; performance remains unknown until measured |
| Shadow collection leaks or retains private data | Plausible / high | Synthetic-first, source-local allowlist, approved retention, egress tests; derived features may remain identifying |
| Agent integration bypasses broker authority | Known code-path gaps / high | Block expansion until caller/demotion/revocation tests pass; no generic shell; production security audit remains broader than this project |
| Background experiments contend with speech/inference | Plausible / household disruption | Bounded concurrency and scheduled load, measure serving queues, immediate experiment stop; shared host remains a failure domain |
| Test leakage or weak labels creates false improvement | Plausible / misleading promotion | Family/time splits, locked holdout, human adjudication, explicit uncertainty; low-volume rare events cannot be certified statistically |
| New framework increases maintenance burden | Plausible / medium | Small shortlist, installation/dependency inventory, recorded tuning/review effort, stop rule |
| Rollback restores config but not target effects | High if actions generalized / high | Foundation is read-only; later effectful capabilities need separate compensation/reconciliation evidence |

The accepted foundation risk envelope is the table above under Stream A. Before each deployment, record exact target, resource/network changes, validation and rollback. Routine in-scope steps do not need repeated conversational approval; new material risks and repository/platform-mandated approvals remain gates. A new material risk or scope expansion pauses that mutation, not unrelated authorized analysis.

## 8. Persistence and resumability

Maintain one progress table in this project, not separate overlapping charters. Each work package records state, owner, exact baseline/candidate/evaluator/dataset digests, completed evidence, unresolved issue and next safe action. Store sanitized experiments under stable IDs. Use immutable release manifests and last-known-good pointers; preserve the current working deployment.

On resume: read this project's progress/evidence sections; verify Git status and authoritative refs without overwriting user work; check the recorded environment manifest; identify changed assumptions; resume the first incomplete gate. Never infer an interrupted side effect succeeded or retry it blindly. Local commit/push handling follows repository rules and records pending synchronization explicitly.

## 9. Milestones and gates

Checkboxes are milestone evidence claims. M0 is complete for baseline/start scope; later gates remain open until their full implementation, validation and documentation are complete.

| Gate | Work and dependency | Acceptance / measurement | Rollback and evidence before continuing |
|---|---|---|---|
| **M0 — baseline and scope** | Reverify source/live versions, owners, resource budget and authority boundaries | [x] Dated manifest; known/unknown list; current test baseline; approved local foundation/start scope — see evidence/M0-baseline.md | No runtime mutation. Continue only with pinned evidence and preserved user work |
| **M1 — authority regression boundary** | Design/fix caller binding and demotion revocation; review approver role, atomic consume and policy-change handling | [ ] Synthetic wrong-caller, demoted/revoked, expired, stale-policy, duplicate/concurrent-consume and restart tests; independent review; approved deployment if required | Retain restrictive disable/revoke path; do not roll back to unsafe broader grants. Offline experiments can proceed independently; integration cannot |
| **M2 — contracts and baseline adapters** | Decision/run/outcome/experiment schemas; minimal catalogue; current Aster adapter | [x] Offline synthetic contract fixtures; unknown-capability denial; no leaked secret fields; no production behavior/authority expansion; baseline overhead measured — see evidence/M2-integration-checkpoint.md | Remove adapter/config and retain current runtime; schema/version/evidence manifest |
| **M3 — harness and routing decisions** | M2; existing Aster vs minimal Pydantic AI; LangGraph on multi-step subset; rules vs one routing challenger | [ ] Separate controlled harness tests and local-model task tests; frozen corpus; quality, p50/p95, prompt tokens, calls, retries, resource and maintenance results; explicit choose/retain/reject ADR | No live migration required. Discard challengers; evidence must support the choice rather than framework preference |
| **M4 — minimal evidence loop** | M2; privacy-approved schema and storage design | [ ] Reproducible dataset manifests, label provenance, calibration where supported, paired evaluation, experiment record and proposal/review separation; storage restore test | Stop collector/runner; restore last-known-good manifests; no opaque data dependency |
| **M5 — read-only shadow pilot** | M1 for any connected broker path; M3/M4; explicit collection/deployment approval | [ ] Finite observation window, proposed 14 days plus sufficient labeled independent examples; no effectful calls; audited egress/retention; measured overhead and shared-service impact | Disable shadow switch, remove candidate traffic and disallowed data; extend window or declare inconclusive if sample inadequate |
| **M6 — one complete change decision** | M5 identifies a justified candidate or evidence to reject it | [ ] Preregistered benefit/guardrails; held-out result; human review; rejection recorded or approved reversible canary; proposed 14-day continued observation if promoted | Atomic versioned revert; invalidate incompatible pending plans; no evaluator/permission modifications |
| **M7 — operational graduation** | All prior gates and open risks reconciled | [ ] Operator explanation, monitoring/Doctor integration, restore and degradation tests, documentation, reproducible rerun and Jason acceptance; pending publication stated | Current stable path and documented uninstall/disable remain available; final manifest and evidence index |

The proposed windows and thresholds are finalized before data inspection. Calendar duration alone does not establish enough evidence. Harness replacement and learned routing are optional outcomes; a retained baseline still requires the evidence-loop and operational graduation gates.

## 10. Validation and evaluation

Use two independent comparisons: harness implementation with controlled model/tool fixtures, and routing strategy with frozen capability labels. Then measure the chosen candidates on pinned local serving configurations. Record warm/cold timing, model queue/prefill/decode, prompt/schema tokens, model calls, retries, RSS/CPU, task success, abstention, unauthorized-attempt blocks and development/maintenance effort.

The routing corpus covers timers, HA, media, factual questions, calendar, web, mixed questions, personal context, sysadmin and ambiguity, with private sources simulated. Label required/optional/prohibited capabilities and acceptable clarification. Calibrate only with disjoint supported data; unsupported confidence remains null. Separate synthetic, human gold, weak and outcome labels.

Fault tests cover invalid schemas, denial, expired/revoked approval, cancellation, crash around simulated action, stale context, router/model outage and unavailable telemetry. No production fault injection without a separate bounded plan. Hard safety constraints cannot be traded for average task success. Retain no-change outcomes and negative results.

## 11. Observability and maintenance

Reuse Prometheus/Grafana and Doctor. Low-cardinality metrics include decision latency, route/capability counts, abstention, actual versus predicted locality, tool/model failures, queue pressure, collector loss and experiment status. Detailed events remain in the approved local store; no prompt or principal IDs in metric labels.

Maintain exact dependency versions and a tested update process. New model/harness versions rerun conformance and relevant regression suites. Add maintenance/review hours and dependency count to experiment cost. Jason owns alerts and review cadence; automation may draft findings. Missing evidence freezes promotion rather than implying success.

## 12. Backup, restore and rollback

Protect non-secret configuration, catalogue manifests, experiment records and approved evidence state through existing backup mechanisms only after retention/privacy review. Private datasets need explicit encrypted backup/deletion policy; do not include them in Git or mirror them to GitHub. Existing PA backup exclusions remain intact.

Test isolated reconstruction of the evaluation environment and restoration of approved evidence state. Retain the previous production bundle until rollback and observation gates pass. Disable all experimental traffic independently of the user interface and baseline household path. Restore order: required storage/configuration, authority dependencies, stable runtime, optional collectors, optional experiments. Do not require Learning services to restore basic assistant operation.

## 13. Documentation and systems-of-record integration

| Integration | Foundation requirement |
|---|---|
| Doctor | Candidate/collector health and stale-evidence checks only where actionable; no duplicate host checks |
| Monitoring | Add bounded metrics and explicit loss/failure signals; Jason owns alerts |
| Backup/recovery | Approved evidence/config coverage and isolated restore, respecting privacy exclusions |
| NetBox | No new device/IP proposed; update only if actual service/deployment facts change |
| Human wiki | Current architecture, operator controls and recovery links after graduation |
| Aster mirror | Rebuild from adopted sanitized docs with provenance; no direct authority edits |
| Operational reference | Current runtime/harness version, enable/disable/recovery procedures |
| Repository portfolio | One programme/project entry with linked module work packages; preserve old project history |
| Diagrams/rack records | Logical dependency diagram; physical/rack updates not applicable without hardware changes |
| Homepage/discovery | No new dashboard necessary initially; add private link only if operator value established |
| Authentication/authorization | Distinct experiment identity, explicit approver roles and broker mapping where connected |
| DNS/certificates/firewall | None for offline work; any pilot change requires exact narrow deployment proposal |
| Schedules | Bounded experiments, concurrency, missed-run handling, last-success state |
| Security inventory | Credential-free fixtures; pinned artifacts; owner, patch/revocation and temporary-access cleanup |
| AI administration | No new general AI admin identity; any capability uses existing onboarding and approval standards |

## 14. Graduation criteria

The project graduates when Aster has stable replaceable contracts, an evidence-backed harness/routing decision, trustworthy outcome records, a reproducible benchmark, an independently governed change process, tested disable/restore paths and one completed improvement-or-rejection cycle. Jason must be able to answer what changed, why, with what evidence, under whose authority and how to revert it.

No unresolved authorization invariant can be marked as passed. Any accepted limitation is explicit. Full Alexa replacement, high availability and operational autonomy are not graduation claims for this foundation release.

## 15. Evidence log

| Date | Activity | Result / limits |
|---|---|---|
| 2026-09-25 | Repository/live architectural assessment | GO WITH RESTRUCTURING; baseline/provenance and security findings retained in assessment |
| 2026-09-25 | Current harness alternatives reviewed | Existing Aster baseline; Pydantic AI first challenger; LangGraph conditional; no installations or lab benchmark claims |
| 2026-09-25 | Single implementation project drafted | Review artifact only; no production/repository mutation, approval or milestone completion implied |
| 2026-09-25 | Jason authorized Stream A and consolidation | Canonical project adopted; five predecessors archived; M0 reverified; M1 started with 36 passing tests and two explicit expected-failure blockers; no production mutation |
| 2026-09-25 | M1 local authority candidate | Caller/demotion blockers fixed; 58 broker and 8 Companion tests pass; atomic concurrency/crash/restart and approver regressions retained; independent review and deployment still open |
| 2026-09-25 | M1 publication and M2 offline start | Forgejo/GitHub verified at 35175c8; 19 M2 conformance tests and four-case source-slice baseline retained; neither M1 deployment nor full M2 gate is complete |
| 2026-09-25 | M2 integration and M3 preregistration | 26 adaptive + 89 existing Aster tests pass; live hashes/packages reconciled; offline M2 gate complete; minimal challenger plan and 17-package dry-run resolution retained; no install/deployment |
| 2026-09-25 | M3 minimal preload experiment | Isolated 17-package/5.45 MB install; two process repeats per candidate; ~1 ms PydanticAI p95 and ~22 MiB incremental RSS; guardrails pass but no measured benefit, retain Aster; M3 overall open |
| 2026-09-25 | M3 tool-loop/routing smoke | Eight cases pass twice per harness; 30 adaptive tests pass; rules 10/10 held-out synthetic families vs TF-IDF 1/10, no test tuning; retain baseline, M3 model/representativeness gate open |
| 2026-09-25 | M4 storage, lineage and paired evaluation | Frozen manifests, outcome-bound totals and 164-event restore verified; four synthetic families pass controlled guardrail; 52 tests pass; no independent review or live-use approval |
| 2026-09-25 | M4 review preparation | Storage/retention/custody design proposed; offline export verifier reproduces 164 events and rejects forged summary; 56 tests pass; independent reviewer/custody still required |

| 2026-09-25 | Local M1 corrective candidate and independent review | 55 broker + 163 Aster tests pass; migration race identified by reviewer and fixed; production/identity/assurance gates remain open — see M1 evidence |

## 16. Later releases within the programme

After foundation graduation, propose bounded amendments under this document for: deterministic voice/household reliability; isolated live calendar/public-web composition; limited Class 1 optimization under explicit standing authorization; and one guarded operational remediation after AI-PAM/recovery graduation. Each amendment adds its own risk, acceptance, measurement and rollback gates. Unrelated storage, network and hardware projects remain independent dependencies.

## 17. Close-out and current resume point

**Active, not graduated.** M0 is complete. Jason approved M1 Stage1, and the
authenticated-caller, versioned-policy and atomic core/transport changes are
installed on LXC104. All 45 staged guest tests and legacy approval compatibility
passed. An initial socket-readiness race failed closed; a bounded same-code restart
recovered without a database restore. The subsequent 601-second observation passed
with stable services, zero restarts, unchanged request counts and no checked error
markers. See [deployment evidence](evidence/M1-stage1-deployment.md).

M1 remains open: explicit approver entitlement and verified passkey assurance
(Stage2) are local candidates requiring separate review, approval and live
validation. Do not expand tool authority or claim M1 graduation. The M6 Forgejo
read and safe-write transports were preserved through Stage1. Offline M2 work may
continue independently.

The reconciled local integration keeps `scripts/aster-adaptive` as the canonical
offline harness/evidence path and retains `services/aster-adaptive` only as a
namespaced selector conformance probe. The probe's31 vectors and29 tests do not
supersede the harness's52 tests or its M3/M4 findings. See [integration map and
current probe evidence](evidence/M2-reconciliation/README.md). Stage1 through
a08114b is represented in authoritative f25df18; this integration itself is local,
unpublished, and does not deploy Stage2 or alter the broker.

M2's offline foundation gate is complete: five contract families, a fixture-only
catalogue, 26 passing adaptive tests (including seven actual HTTP path tests),
89 passing existing Aster tests and the retained four-case baseline measurement.
Read-only live source/binary/package checks match the dated baseline; no production
mutation or model call occurred. See [M2 integration checkpoint](evidence/M2-integration-checkpoint.md).

M3's preregistered minimal preload comparison ran in a disposable, hash-pinned
PydanticAI slim environment (17 packages, 5.45 MB wheels; no provider extras).
Two independent process runs per candidate met the controlled overhead guardrails,
but established no correctness/maintenance advantage. **Retain Aster; do not
migrate.** Four candidate smoke/denial/cancellation checks pass. See
[M3 results, limitations and next steps](evidence/M3-preload-results.md).

The eight-case tool-loop comparison also passed for both implementations in two
fresh-process repeats. PydanticAI rejects malformed arguments earlier, but does not
remove the need for deterministic validation. A separate 300-variant/30-family
routing smoke test found rules exact on 10/10 held-out families versus TF-IDF 1/10;
these are biased-risk authored synthetic data, not production accuracy claims.
Thirty adaptive tests pass. See [M3 tool-loop/routing evidence](evidence/M3-tool-loop-results.md).

M3 remains open for representative reviewed routing labels and local-model
compatibility/quality/resource evidence; inference measurements need a bounded
current-load and consumer-overlap check. M1 Stage1 is deployed; the separate
Stage2 identity/assurance gates remain open.

M4 now has a synthetic SQLite evidence-store candidate: frozen experiment lineage,
evaluation-bound reviews, idempotent transactional appends and an externally pinned
hash-chain restore check. **40 adaptive tests pass**, and a disposable three-event
backup restored successfully. This is not authenticated review or production storage.
See [M4 storage checkpoint and limits](evidence/M4-storage-checkpoint.md).
The checkpoints through `c10bf84` were then pushed with Jason's explicit approval;
Forgejo and GitHub main were verified at `c10bf84b020860616cd26fe6b10be4a64aa63d35`.

The next local M4 step adds dataset manifests, registered runs and exact outcome
lineage. **45 adaptive tests pass**; four fresh fixture outcomes passed and their
ten-event ledger restored successfully. This is a lineage exercise, not a paired
performance result. See [M4 lineage evidence and resume point](evidence/M4-lineage-checkpoint.md).
Jason then authorized pushing `7ece818`; Forgejo and the GitHub mirror were verified
at `7ece81892982fee10a5999cd7844d7360a2d6e25`.

A newly preregistered paired synthetic experiment now binds aggregate evaluation
to exact outcomes and family denominators. All four authored families passed the
5 ms p95 overhead guardrail; the 164-event ledger restored successfully. **52 adaptive
tests pass.** See [M4 paired evaluation evidence](evidence/M4-paired-checkpoint.md).
The paired checkpoint was pushed with Jason's authorization; Forgejo and GitHub were
verified at `a86a4283fed99d70c3b41285c22fc4a021549527`.

The [storage and review design](M4-Storage-and-Review-Design.md) now records proposed
ownership, retention, checkpoint custody and recovery boundaries. A separate offline
verification command reconstructs 164 saved events and rejects a forged summary;
**56 adaptive tests pass**. See [review-preparation evidence](evidence/M4-review-checkpoint.md).
M4 remains open for actual independent review/custody and accepted operational design.
Next safe independent work is M1's review packet and read-only/local-test reconciliation
with the AI-PAM candidate; preserve that checkout's edits. M3 representative/model
gates remain open. No production changes or installs occurred. The newer review work
is local; a further push needs explicit authorization.

## Consolidated requirements and dependency ownership

The following standalone plans are superseded as execution queues, with history retained in `../archive/`:

- [Personal Assistant](../archive/Aster-Personal-Assistant.md): later-release email/calendar readers, morning check-in and nudges, isolated scheduled research, multi-person privacy, Photography Assistant/Immich/competition workflow. Preserve all retention, custody and source-isolation decisions. No email-send, calendar-write or live private/public composition is authorized by foundation work.
- [Home Assistant Voice Assistant](../archive/Home-Assistant-Voice-Assistant.md): later-release voice endpoints, local speech, timers/alarms/media/lights and household reliability. Replace mandatory LLM routing with a measured deterministic path.
- [Email Triage](../archive/Email-Triage-Digest.md), [Calendar Assistant](../archive/Calendar-Personal-Assistant.md), [Combined Morning Digest](../archive/Combined-Morning-Digest.md): preserve predecessor decisions through the Personal Assistant module; do not restart them independently.

AI-PAM, Lab Operations and the ARR execution follow-up remain active dependencies because they own unfinished authority, recovery and target-specific execution gates. Source/report contracts remain valid. Domain recommenders, subtitles, news, documents, access, backup and resilience projects remain separate modules/dependencies; a shared model endpoint does not make their deliverables redundant. Completed Aster projects remain historical graduation evidence in `../completed projects/`.

### Authorization and start evidence — 2026-09-25

Jason explicitly requested this project start as Stream A and the folder/archive consolidation. Read-only Forgejo verification matched e50b670; local main was fast-forwarded from 586457f without overwriting unrelated edits. Active service and broker hash checks matched the assessed baseline. Local synthetic test baseline and the two reproduced authorization gaps are recorded in M0 evidence. No new authority or production changes were introduced by project start.

### Historical M1 executable rollout preparation checkpoint

The prepared candidate now includes a read-only preflight, eight preflight regressions, a bounded two-file apply script and [exact operator commands](evidence/M1-stage1-commands.md). Broker suite65 and staged subset45 pass. No production execution or push has occurred. Expired pending rows were distinguished from usable approvals without mutation. The latest AI-PAM coordination has reopened its M6 workflow, so its earlier quiescent window is no longer valid. Resume by rechecking the live hashes/TTL summary, obtaining an immediately current coordination window and reviewing the exact Stage1 deployment with Jason. Do not infer approval from this checkpoint.


### Historical M1 resume gate — reviewed Stage1 candidate

Local checkpoint `7ef0b96` was completed. Both independent reviews have now
returned; the recovery-directory reporting finding is fixed and the rebuilt
release passes 45 staged tests. AI-PAM reports M6 rollback complete. Fresh
read-only verification found unchanged baseline source, healthy services and
zero usable approvals. The current next step is the exact Stage1 deployment
approval in [operator commands](evidence/M1-stage1-commands.md), followed by a
fresh immediate preflight. Previous notes about an active M6 cleanup window are
historical. Production is unchanged by this task; no push is authorized.


### Current checkpoint — Stage1 complete, Stage2 open

Jason's exact deployment approval was executed. Protected backup/restore,45 guest
tests, compatibility, live denial/health/permissions and the full ten-minute
observation passed. A Type=simple startup-readiness race caused a fail-closed stop;
a bounded same-candidate start recovered it without source changes or DB restore.
[Deployment evidence](evidence/M1-stage1-deployment.md) is authoritative for this
rollout. No Git push occurred. Continue with offline M2 contracts or the separately
reviewed Stage2 assurance design; do not claim full M1 graduation or widen tools.


### Historical local selector-probe continuation — M2 and Stage2 design

The next local-only candidate is in `services/aster-adaptive` and `schemas/aster`.
Strict contracts, an execution-disabled fixture catalogue and the extracted current
Aster tool selector pass28 tests and 12 fixture comparisons, with local timing and
pinned evidence in [M2 results](evidence/M2-offline-contracts.md). No framework
replacement, calibrated accuracy or live authority projection is claimed. M2's
connected acceptance gate remains open; M1 remains ungraduated.

[Stage2 design](evidence/M1-stage2-candidate.md) defines the smallest entitlement/
assurance candidate, negative cases, process-trust limitation and fail-closed
recovery. Existing 10 bridge + 10 approval-service tests pass. Actual signed
passkey-assurance provenance and a fresh user-session validation are unresolved;
no deployment approval is requested until that concrete candidate exists.

AI-PAM owns concurrent reconciliation of the alternate a5e8b22 all-at-once
implementation with exact deployed Stage1. Its old DB-approver tests must retain
a coverage/supersession map; they are not silently discarded. No shared broker
or approval source was edited in this M2 continuation, and its commits are outside
AI-PAM's pending remote publication unless separately reviewed. No push.


### Historical local selector-probe checkpoint

M2 corrective review passed at026e5e9 (supersedes30f79ea). An additional portable
conformance corpus passes31 vectors;29 adaptive tests pass in total. Evidence and
limits are linked from [M2 results](evidence/M2-offline-contracts.md). Stage1 remains
the only deployed change. Stage2 needs verified real-session assurance and an
explicit process-trust decision; the connected M2 gate remains open behind it.
No production/private data collection, authority expansion, new dependency or
Git push occurred. The AI-PAM task owns alternate-design reconciliation.


### Current integration resume point

Isolated branch `codex/aster-m2-reconcile-20260925`, based onf25df18, reconciles
local1a8fa68 without overwriting primary checkout edits. Seven earlier local
commits were already represented by AI-PAM; three M2 commits are retained as the
explicit selector-probe profile. Broker/approval/Aster and remote harness sources
are unchanged;52+29+76+163 tests pass. See the integration map for provenance,
semantic namespace resolution and rollback. No push or production change.
Recheck remote head and coordinate before any separately authorized publication.


### Current checkpoint — published integration and M4 review packet

Forgejo and its GitHub mirror were both verified at7133f3f after Jason's explicit
push instruction. Subsequent work is local-only. The pre-existingaf2cc4f M4 verifier
and design were reconciled onto that published baseline, preserving Stage1 and
all newer M2/M3/M4 evidence.56 harness/evidence +29 selector-probe tests pass; the
164-event paired export replays offline with unchanged historical hashes.
[Review packet](evidence/M4-review/REVIEW-PACKET.md) identifies the exact artifact,
verifier, checkpoint, decision and limitations. Independent human judgment and
checkpoint custody are not established. M4 is not graduated; no real collection,
new identity, Stage2 deployment or further push is authorized.
