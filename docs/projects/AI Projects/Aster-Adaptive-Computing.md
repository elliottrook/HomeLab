# Aster Adaptive Computing — Foundation and Operational Sysadmin Capability

**Status:** Active — Stream A. Operational Sysadmin Capability (SA0–SA5) is the next delivery priority, approved by Jason on 2026-09-28. SA0 reconciliation is active; all SA gates remain open. M0 and the offline M2 foundation have evidence. M1 Stage1 is verified and the September 27 Stage2 incident repair/iPhone approval workflows were accepted, but M1 and broader programme acceptance gates are not declared complete.

**Owner:** Jason.

**Current coordination and priority — 2026-10-05:** Jason requested one Codex
window for delivery, supporting agents coordinated there, and plain-language
explanations of practical consequences. The immediate priority is repairing the
local-Qwen evaluation contract before a further model or hardware decision.
The [validity review](evidence/SA3-evaluation-validity-review-2026-10-05.md)
reproduces scorer limitations without accessing private answers. Qwen remains
unqualified for operational diagnosis; general local-model inability and B60
inadequacy are not established. Next safe work is a separate offline evaluator
candidate with synthetic development tests. Doctor recovery is a separate pending
integration task. No deployment, push or model run is authorized by this update.
This priority supersedes older next-action prose below. The [fair thinking comparison](evidence/SA3-fair-thinking-comparison-2026-10-05.md)
now specifies paired thinking-off/on evaluation with adequate answer budgets.
An offline scorer candidate and synthetic fixture tests exist; no connected model
comparison has run. Paired request construction is now tested offline; the
[installed-version source review](evidence/SA3-per-request-thinking-2026-10-05.md)
supports per-request overrides. Jason subsequently approved the two-request
[smoke pair](evidence/SA3-thinking-smoke-result-2026-10-05.md): switching worked
without restart; off took 24.431 seconds and on 158.706 seconds. Neither mode is
qualified for operational diagnosis by this example. The synthetic multi-step
simulator, development fixtures and explicit-execution runner are now implemented
and locally validated. The [four-investigation plan](evidence/SA3-simulated-investigation-plan-2026-10-05.md)
is ready for connected-run approval (up to 12 calls/20 minutes inference). Continue
Stream A local work without milestone-by-milestone confirmation, pause only at
required gates and resume when granted. Production defaults remain unchanged.

**Proposed:** 2026-09-25.

**Authorization stream:** Stream A — Autonomous, explicitly authorized by Jason on 2026-09-25: create the AI Projects folder, adopt these documents, mark superseded plans and archive them, and start this project. The authorization covers the bounded foundation milestones and their existing exclusions, not general administrator authority, later-release scope or automatic promotion authority. Repository/platform controls and per-push confirmation remain mandatory.

**2026-09-28 amendment authorization:** Jason approved adding Operational Sysadmin Capability to this existing programme and making it the next delivery priority. This adopts the SA0–SA5 scope, local-first decision process and acceptance criteria below. Routine read-only discovery, local implementation and fixture evaluation proceed under the existing Stream A envelope. Exact connected deployments, new capability/credential paths, cloud egress and supervised repair canaries retain their stated risk and authorization gates; this amendment is not a blanket grant of root access or production mutation. Remote Git publication remains separately gated.

**Canonical project document:** `docs/projects/AI Projects/Aster-Adaptive-Computing.md`. Assessment and inventory are dated supporting evidence; this document governs implementation.

**Supporting assessment:** [architecture](ASSESSMENT.md), [inventory](INVENTORY.md), [harness comparison](HARNESS-ALTERNATIVES.md), [research log](research-log.md).

## 1. Purpose and desired outcome

The next user-visible outcome is an Aster sysadmin that can investigate an unfamiliar lab incident, gather missing evidence, distinguish competing explanations, prepare a bounded correction, execute through an authorized adapter and independently verify the result. [Operational Sysadmin Capability](Operational-Sysadmin-Capability.md) defines the adopted technical requirements and evaluation protocol; milestone status is maintained only in this document. Routing, knowledge recall and refusal tests alone do not qualify Aster for this role.

Establish one coherent programme in which Aster's independently replaceable components improve through retained evidence, with deterministic authority and human governance. Deliver a finite foundation release that can compare routing and harness choices, explain outcomes, reject regressions and demonstrate one complete evidence-backed decision cycle.

Success does not require replacing the existing runtime or deploying a learned router. Keeping a simpler baseline after a reproducible comparison is a valid engineering result. It must still leave usable contracts, measurements, decision records and an operational improvement process—not merely another research report.

## 2. Current state and evidence

The [September 28 readiness assessment](evidence/2026-09-28-sysadmin-readiness.md) and [two illustrative live diagnostics](evidence/2026-09-28-sysadmin-diagnostics.json) establish the amendment baseline: reasoning disabled, one-pass evidence preparation, a live ordinary-answer cap of 500 tokens, limited diagnostic access, and inadequate incident answers. These are observations, not proof Qwen can never succeed. The adaptive branch at `8fd5f8d`, local main at `d2f771d` and observed Forgejo main at `ca22e78` differ. Later production repairs must be preserved; earlier status prose below is dated history where superseded by this amendment.

The assessment verified main `e50b670b906f397e1e70b6d51cf07e88235ac5c5` at Forgejo and its GitHub mirror. The checkout was behind; reverify the baseline before implementation. Existing user edits must be preserved.

Aster is the active bounded Python harness, with local llama.cpp inference, speech, source-local reports, Companion, Authentik, monitoring and an emerging AI-PAM integration. Hermes is not a required runtime dependency. Historical Hermes measurements demonstrate substantial prompt/tool overhead. An isolated PydanticAI comparison passed guardrails but established no correctness or maintenance benefit, so the foundation baseline retains Aster; other alternatives remain conditional and unbenchmarked.

AI-PAM has implemented milestones and an initial read integration, but not full graduation. Isolated tests found missing originating-agent binding at consume and approvals surviving demotion to probation. Repair and verification are prerequisites to broadening broker use. No production exploit was attempted. Most components share one Proxmox host; host-loss availability is not promised by this project.

## 3. Scope and exclusions

**Foundation release includes:** state reconciliation; security-boundary regression gates; Decision, Harness Run, Capability, Outcome and Experiment contracts; a minimal authorized catalogue projection; current-runtime baseline; a bounded harness/routing comparison; local evidence storage; an opt-in read-only shadow pilot; and one evaluated reversible candidate with promotion or rejection and continuing observation.

**Excludes:** general shell/admin agents; automatic privilege changes; automatic security/evaluator-policy changes; new public ingress; production destructive tests; wholesale repository moves; new hardware; replacing Authentik/OpenBao; adopting Octelium; installing multiple orchestration/evaluation platforms; indiscriminate raw conversation retention; broad personal-data integration; an automatic production-remediation programme. Routine local implementation and synthetic evaluation are authorized within this foundation scope. New major dependencies, deployment targets, data collection and production boundary changes require the relevant milestone risk/compatibility gate; no such deployment is included in this initial baseline commit.

The adopted SA workstream includes bounded investigative tools, a Qwen-first capability trial, a provider decision and one supervised repair class after its gates. It does not introduce a general shell/admin agent or automatic remediation. Full voice replacement and private/public live composition remain later release gates in this same programme. Existing domain projects remain historical evidence and independently bounded implementation dependencies; their permissions do not transfer automatically.

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

The SA amendment adds reasoning/queue contention, stale or incomplete observations, evidence leakage, tool-loop escape and ambiguous repair outcomes. Its controls, deployment prerequisites and rollback requirements are specified in [the workstream risk and integration section](Operational-Sysadmin-Capability.md#risk-integration-and-recovery). Existing authority invariants remain mandatory; no SA work may silently weaken them.

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

**Delivery order:** SA0, then read-only SA1/SA2 and SA3. Finish applicable M1 controls before any connected capability relies on them and before SA4 writes. Generic S1 routing collection, learned routing and broad adaptive-learning promotion are deferred as delivery priorities; preserve their records and custody requirements, but do not require further household-routing labels before useful sysadmin diagnosis. M2/M4 contracts and evidence infrastructure are reused where applicable. No deployed timer or collection service is changed by this documentation amendment.

Checkboxes are milestone evidence claims. M0 is complete for baseline/start scope; later gates remain open until their full implementation, validation and documentation are complete.

| Gate | Work and dependency | Acceptance / measurement | Rollback and evidence before continuing |
|---|---|---|---|
| **M0 — baseline and scope** | Reverify source/live versions, owners, resource budget and authority boundaries | [x] Dated manifest; known/unknown list; current test baseline; approved local foundation/start scope — see evidence/M0-baseline.md | No runtime mutation. Continue only with pinned evidence and preserved user work |
| **M1 — authority regression boundary** | Design/fix caller binding and demotion revocation; review approver role, atomic consume and policy-change handling | [ ] Synthetic wrong-caller, demoted/revoked, expired, stale-policy, duplicate/concurrent-consume and restart tests; independent review; approved deployment if required | Retain restrictive disable/revoke path; do not roll back to unsafe broader grants. Offline experiments can proceed independently; integration cannot |
| **M2 — contracts and baseline adapters** | Decision/run/outcome/experiment schemas; minimal catalogue; current Aster adapter | [x] Offline synthetic contract fixtures; unknown-capability denial; no leaked secret fields; no production behavior/authority expansion; baseline overhead measured — see evidence/M2-integration-checkpoint.md | Remove adapter/config and retain current runtime; schema/version/evidence manifest |
| **M3 — harness and routing decisions** | M2; existing Aster vs minimal Pydantic AI; LangGraph only on a demonstrated graph-shaped need; rules vs routing challengers | [ ] Harness subdecision complete: retain Aster, keep Hermes optional and PydanticAI probationary. Overall gate remains open for representative independently reviewed routing evidence; a live harness challenger is required only after a concrete benefit hypothesis. See evidence/M3-harness-decision.md | No live migration required. Discard challengers; evidence must support the choice rather than framework preference |
| **M4 — minimal evidence loop** | M2; privacy-approved schema and storage design | [ ] Reproducible dataset manifests, label provenance, calibration where supported, paired evaluation, experiment record and proposal/review separation; storage restore test | Stop collector/runner; restore last-known-good manifests; no opaque data dependency |
| **M5 — read-only shadow pilot** | M1 for any connected broker path; M3/M4; explicit collection/deployment approval | [ ] Finite observation window, proposed 14 days plus sufficient labeled independent examples; no effectful calls; audited egress/retention; measured overhead and shared-service impact | Disable shadow switch, remove candidate traffic and disallowed data; extend window or declare inconclusive if sample inadequate |
| **M6 — one complete change decision** | M5 identifies a justified candidate or evidence to reject it | [ ] Preregistered benefit/guardrails; held-out result; human review; rejection recorded or approved reversible canary; proposed 14-day continued observation if promoted | Atomic versioned revert; invalidate incompatible pending plans; no evaluator/permission modifications |
| **M7 — operational graduation** | Applicable foundation gates, SA0–SA5 and open risks reconciled | [ ] Operator explanation, monitoring/Doctor integration, restore and degradation tests, documentation, reproducible rerun and Jason acceptance of demonstrated sysadmin operation; pending publication stated | Current stable path and documented uninstall/disable remain available; final manifest and evidence index |
| **SA0 — reconcile production and source** | Next; preserve production repairs and useful adaptive-branch work | [ ] One reviewed release tree and runtime manifest; live/repository diffs explained; checkpoint and reproducible release inventory | No blind reset; retain every source history and known-good production bundle |
| **SA1 — iterative investigation** | SA0; separate sysadmin mode and shared streaming/non-streaming loop | [ ] Follow-up tool selection, hypothesis revision, bounded context/reasoning/output, durable incident state and reconnect behavior; no fabricated execution | Feature-disable returns to accepted advisor; no new effectful tools |
| **SA2 — diagnostic evidence access** | SA0; develop alongside SA1; applicable M1 boundary checks | [ ] Registered-target Git/log/status/network/backup/config observations with provenance, age, truncation and denied-action tests | Revoke/disable individual read adapters; credentials remain outside model |
| **SA3 — Qwen capability and provider decision** | SA1/SA2; pinned corpus and settings | [ ] Current baseline versus improved non-thinking/thinking configurations; held-out quality and latency gates; recorded Qwen-only, narrow local/hybrid or cloud-sysadmin decision | At most two improvement configurations; no automatic cloud enrollment or production promotion |
| **SA4 — supervised reversible repair** | Diagnostic acceptance and applicable M1/AI-PAM/recovery gates; exact canary authorization | [ ] One repair class with bound plan, preconditions, checkpoint, approval, execution, independent postchecks, rollback and uncertain-outcome handling | Disable adapter; restore only bounded affected state; reconcile before retry |
| **SA5 — operational role acceptance** | SA0–SA4; representative held-outs and finite live shadow/canary observation | [ ] Accepted rubric, useful normal workflow, two independent critical production-path passes, recovery/degradation proof and Jason acceptance | Retain human recovery and proven narrower role; document limits, do not claim universal autonomy |

The proposed windows and thresholds are finalized before data inspection. Calendar duration alone does not establish enough evidence. Harness replacement and learned routing are optional outcomes; a retained baseline still requires the evidence-loop and operational graduation gates.

## 10. Validation and evaluation

For the SA workstream, the incident rubric in [Operational Sysadmin Capability](Operational-Sysadmin-Capability.md#finite-useful-evaluation) is controlling: 12 development incidents, at least 20 independently reviewed held-out variants, at least 18/20 correct/actionable investigations on the initial fixed set, zero unauthorized effects or false completion claims, and correct escalation on deliberately insufficient evidence. Freeze the precise set, labels, latency protocol and configuration before running; do not tune against the holdout. The adopted latency targets and finite trial cap are planning/acceptance requirements, not measured current capability. Retain the tests below as supporting regressions.

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

**Mandatory operational gate:** the programme cannot graduate Aster as a sysadmin until SA0–SA5 pass. Foundation or advisor completion may be recorded separately, with that limited label. The approved grade must distinguish knowledge advisor, diagnostic investigator, supervised repair operator and narrowly authorized scheduled operator. A model/harness selection or routing pass cannot substitute for incident evidence, independent verification and Jason's operational acceptance.

The project graduates when Aster has stable replaceable contracts, an evidence-backed harness/routing decision, trustworthy outcome records, a reproducible benchmark, an independently governed change process, tested disable/restore paths and one completed improvement-or-rejection cycle. Jason must be able to answer what changed, why, with what evidence, under whose authority and how to revert it.

No unresolved authorization invariant can be marked as passed. Any accepted limitation is explicit. Full Alexa replacement, high availability and operational autonomy are not graduation claims for this foundation release.

## 15. Evidence log

| Date | Activity | Result / limits |
|---|---|---|
| 2026-09-28 | SA0 publication and source reconciliation | Forgejo and GitHub `main` were verified at `ccd0ead`; the merged history retains Forgejo, adaptive and `d2f771d` production work. The source gateway SHA-256 exactly matches live, as does the already-reconciled Lab Operations adapter. Reasoning remains disabled; no runtime change — see [SA0 evidence](evidence/SA0-reconciliation-2026-09-28.md) |
| 2026-09-28 | SA1/SA2 typed incident evidence candidate | Added an offline, no-I/O incident/evidence contract with registered read-only targets, provenance/age/truncation fields and bounded follow-up proposals. Five local contract tests pass. It is neither a deployed adapter nor a completed SA gate — see [candidate evidence](evidence/SA1-SA2-offline-candidate-2026-09-28.md) |
| 2026-09-28 | SA1/SA2 versioned producer and persistence candidate | Added an exact-field, versioned source-local producer envelope, credential-free fixture and SQLite incident/reconnect state. Nine local tests pass, including producer denials and reopened-state validation. It is not connected or deployed — see [producer/persistence evidence](evidence/SA1-SA2-producer-persistence-2026-09-28.md) |
| 2026-09-28 | SA1/SA2 producer-boundary and presentation candidate | Defined the review inputs for a single individually disableable source-local status producer and added fixture-only, concise reconnect SSE frames. Two presentation tests pass; no gateway route, source adapter or live target is connected — see [boundary/presentation evidence](evidence/SA1-SA2-boundary-presentation-2026-09-28.md) |
| 2026-09-28 | First connected-producer proposal | Read-only inspection selected the existing sanitized Doctor report as the first narrow candidate and recorded its actual schedule, publisher, fixed handoff, consumer sandbox and disabled-by-default bridge/rollback proposal. No adapter or configuration is installed — see [deployment proposal](evidence/SA1-SA2-health-producer-deployment-proposal-2026-09-28.md) |
| 2026-09-28 | SA1/SA2 Doctor adapter disabled-baseline deployment | Published source through `29d0498`; installed the default-disabled fixed-path adapter on LXC 104 after 14 local and 5 staged-runtime tests. Gateway hash matches source, service is active and the capability is confirmed disabled. No incident or pilot ran — see [deployment evidence](evidence/SA1-SA2-doctor-adapter-deployment-2026-09-28.md) |
| 2026-09-28 | SA1/SA2 one-run Doctor canary | Temporarily enabled the fixed-path adapter, read one existing sanitized Doctor report and confirmed concise presentation excluding facts/hypotheses. It observed aggregate `fail`, then disabled the adapter and removed the temporary incident state. No repair or real-user flow ran — see [canary evidence](evidence/SA1-SA2-doctor-canary-2026-09-28.md) |
| 2026-09-28 | SA1/SA2 incident retention deployment | Added and installed 24-hour expiry, eight-incident and 256 KiB bounded-state controls; 16 contract tests pass and the deployed digest matches source. The adapter remains disabled — see [retention evidence](evidence/SA1-SA2-incident-retention-candidate-2026-09-28.md) |
| 2026-09-28 | SA3 evaluation preregistration | Audited the existing 14-case advisor and 7-case paraphrase suites; froze a 12-case development regression slice and rejected both as the required incident holdout. No Qwen setting or provider decision changed — see [SA3 preregistration](evidence/SA3-evaluation-preregistration-2026-09-28.md) |
| 2026-10-03 | S1 close-out and SA3 corpus readiness | Closed the 45-case S1 collection as incomplete without evaluation: final strata and adverse-constraint quotas do not satisfy the frozen protocol. Preserved every accepted record, added the missing empty SA3 intake-contract fields for repair scope, postcheck and latency, and added an empty custody template that separates future development/holdout uses and answer keys. No model, provider, router, tool or production change — see [S1 close-out](experiments/s1-routing-holdout-v1/CLOSEOUT-2026-10-03.md), [SA3 discovery](evidence/SA3-corpus-readiness-discovery-2026-10-03.md) and [custody readiness](evidence/SA3-incident-corpus-custody-readiness-2026-10-03.md) |
| 2026-10-03 | Doctor observation, parser repair and bounded deployment | A user Doctor request reached the existing fixed-worker route but was safely retained as `unknown/interrupted`; it is not a health result. Read-only provenance found a separate summary-format incompatibility. A 21-test worker-only repair was installed with a private rollback copy and healthy post-restart observation. The uncertain job was deliberately not cleared, so a fresh Doctor result remains blocked pending reconciliation — see [observation](evidence/SA3-doctor-observation-2026-10-03.md) and [candidate/deployment record](evidence/SA3-doctor-parser-compatibility-candidate-2026-10-03.md). |
| 2026-10-03 | Gateway regression validation | The two FastAPI-dependent Lab Operations gateway suites previously unavailable on the workstation ran in the existing Aster LXC environment: 28/28 passed in 3.3 seconds. Temporary tests were removed; no service, policy, model, credential, or configuration changed. |
| 2026-10-03 | Offline evidence source-pin revision | Whole-file source pins failed closed after unrelated Aster changes. AST review found the harness and selector slices unchanged; explicit reviewed pin revisions were bound to the current live-matching source. In isolated LXC validation, 51/51 evidence-harness and 29/29 selector-probe tests passed. No runtime behavior changed — see [source-pin revision](evidence/SA3-offline-source-pin-revision-2026-10-03.md). |
| 2026-09-28 | Jason approved the sysadmin-readiness recommendation and directed incorporation into the existing unified project | Adopted SA0–SA5 as next delivery priority; Qwen-first trial and conditional hybrid decision; mandatory sysadmin graduation gate; supporting assessment/live diagnostics retained; implementation gates remain open; documentation only, no deployment or push |
| 2026-09-25 | Repository/live architectural assessment | GO WITH RESTRUCTURING; baseline/provenance and security findings retained in assessment |
| 2026-09-25 | Current harness alternatives reviewed | Existing Aster baseline; Pydantic AI first challenger; LangGraph conditional; no installations or lab benchmark claims |
| 2026-09-25 | Single implementation project drafted | Review artifact only; no production/repository mutation, approval or milestone completion implied |
| 2026-09-25 | Jason authorized Stream A and consolidation | Canonical project adopted; five predecessors archived; M0 reverified; M1 started with 36 passing tests and two explicit expected-failure blockers; no production mutation |
| 2026-09-25 | M1 local authority candidate | Caller/demotion blockers fixed; 58 broker and 8 Companion tests pass; atomic concurrency/crash/restart and approver regressions retained; independent review and deployment still open |
| 2026-09-25 | M1 publication and M2 offline start | Forgejo/GitHub verified at 35175c8; 19 M2 conformance tests and four-case source-slice baseline retained; neither M1 deployment nor full M2 gate is complete |
| 2026-09-25 | M2 integration and M3 preregistration | 26 adaptive + 89 existing Aster tests pass; live hashes/packages reconciled; offline M2 gate complete; minimal challenger plan and 17-package dry-run resolution retained; no install/deployment |
| 2026-09-25 | M3 minimal preload experiment | Isolated 17-package/5.45 MB install; two process repeats per candidate; ~1 ms PydanticAI p95 and ~22 MiB incremental RSS; guardrails pass but no measured benefit, retain Aster; M3 overall open |
| 2026-09-25 | M3 tool-loop/routing smoke | Eight cases pass twice per harness; 30 adaptive tests pass; rules 10/10 held-out synthetic families vs TF-IDF 1/10, no test tuning; retain baseline, M3 model/representativeness gate open |
| 2026-09-26 | M3 serving-harness decision | Retain bounded Aster; Hermes optional; PydanticAI guardrails pass but no migration benefit; LangGraph/Pi deferred; existing local-model graduations prove baseline utility but not challenger equivalence. Harness subdecision complete, representative routing gate open — see evidence/M3-harness-decision.md |
| 2026-09-25 | M4 storage, lineage and paired evaluation | Frozen manifests, outcome-bound totals and 164-event restore verified; four synthetic families pass controlled guardrail; 52 tests pass; no independent review or live-use approval |
| 2026-09-25 | M4 review preparation | Storage/retention/custody design proposed; offline export verifier reproduces 164 events and rejects forged summary; 56 tests pass; independent reviewer/custody still required |

| 2026-09-25 | Local M1 corrective candidate and independent review | 55 broker + 163 Aster tests pass; migration race identified by reviewer and fixed; production/identity/assurance gates remain open — see M1 evidence |

## 16. Later releases within the programme

After foundation graduation, propose bounded amendments under this document for: deterministic voice/household reliability; isolated live calendar/public-web composition; limited Class 1 optimization under explicit standing authorization; and additional remediation classes beyond the current SA4 scope after AI-PAM/recovery graduation. Each amendment adds its own risk, acceptance, measurement and rollback gates. Unrelated storage, network and hardware projects remain independent dependencies.

## 17. Close-out and current resume point

**Controlling resume instruction — 2026-09-28:** SA0 source reconciliation is published and verified at `ccd0ead`; its gateway hash exactly matches live. The offline SA1/SA2 incident contract, producer schema, credential-free fixture, local reconnect/persistence candidate and concise presentation frames are implemented and locally tested. The first fixed-path Doctor adapter is installed on LXC 104 and one bounded service-local read canary passed; it is confirmed disabled afterward, and no state was retained. A local 24-hour/eight-incident/256-KiB retention candidate is ready. Existing advisor suites are frozen only as a 12-case development regression slice; the required incident holdout is not yet created. Next, obtain separate authorization to deploy the retention version and run a finite real authenticated-Companion read-only pilot with freshness/dedup checks, an observation period and rollback, while independently preparing the incident corpus. Do not enable reasoning, add targets, deploy a model change or broaden tool authority. All SA checkboxes remain open. See [SA3 preregistration](evidence/SA3-evaluation-preregistration-2026-09-28.md).

The checkpoints below retain their original evidence and limits. They do not override the current resume instruction or establish current live state.

**Active, not graduated.** M0 is complete. Jason approved M1 Stage1, and the
authenticated-caller, versioned-policy and atomic core/transport changes are
installed on LXC104. All 45 staged guest tests and legacy approval compatibility
passed. An initial socket-readiness race failed closed; a bounded same-code restart
recovered without a database restore. The subsequent 601-second observation passed
with stable services, zero restarts, unchanged request counts and no checked error
markers. See [deployment evidence](evidence/M1-stage1-deployment.md).

M1 remains open: Jason authorized full repair on September 27 after a partial
Stage2 rollout broke approval views. The coordinated owner configuration, daemon
and session-specific passkey mapping are now deployed and machine checks pass;
Jason confirmed fresh iPhone sign-in and synthetic approve/deny/management actions;
broker read-back verified fresh passkey approval, denial and suspension revocation.
The test fixture is retired and disabled. See the controlling
[repair evidence and resume point](evidence/M1-stage2-repair-2026-09-27.md).
Do not expand tool authority or claim M1 graduation. Offline M2
contract work can proceed independently. Further authority expansion requires its
own reviewed gate.

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

The later [M3 harness ADR](evidence/M3-harness-decision.md) completes the harness
subdecision by retaining Aster and rejecting a migration without a demonstrated
benefit. M3 remains open for representative independently reviewed routing labels.
A new local-model challenger run is conditional on a concrete benefit hypothesis,
current-source reconciliation and a separately bounded load/credential plan. M1
Stage1 is deployed; the separate Stage2 identity/assurance gates remain open.

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
Read-only reconciliation now confirms AI-PAM's integrated Stage1/M6 baseline at
`f25df1812b7ef339acb9cb59339c704a4032ea26`. Live core/transport/approval hashes match
the deployment record. The merged checkout passes 76 broker, 10 approval-bridge and
56 adaptive tests. See [M1 current review packet](evidence/M1-current-review-packet.md).
The earlier all-at-once candidate is superseded, not awaiting deployment. Stage2
still requires actual assurance provenance and a process-trust decision. A separate
unpublished M2/Stage2 continuation was observed and left untouched. No production
mutation occurred in this reconciliation; this merge and review work remain local.
A further push needs explicit authorization.

### Current contract reconciliation — 2026-09-26

The two offline contract candidates have been compared using pinned snapshots:
56 harness tests, 29 selector tests and 31 portable vectors pass. Ten cross-profile
samples are rejected in both directions; four version strings name incompatible
formats. See [contract mapping and decision](evidence/M2-contract-reconciliation.md).
Retain both scoped tools; no automatic converter or connected adoption is approved.
Independent expected-source pinning is now implemented before payload/chat-loop
compilation. All 62 adaptive tests pass; four lineage cases and eight tool-loop
cases passed with restore/provenance checks. See the
[source-pin checkpoint](evidence/M2-source-pin-checkpoint.md). A read-only Forgejo check found newer `2c71d6b`; recheck/reconcile
before any later integration. Stage2 and M4 review gates remain open. No push or
production mutation occurred in this comparison.

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


### Current M3 checkpoint — human-label design, no collection

M4 acceptance and independent custody remain pending. Existing M3 fixture sets
were inventoried, not rerun or relabeled as human gold. A proposed S0-only
30-family pilot and later separately approved 300-family screening design now
have taxonomy, adjudication/privacy/retention rules, protected splits and frozen
statistical definitions. The current validator is a design-only metadata check,
not an executable human-label collector:17new tests / 73 harness tests pass and the
empty batch reports zero human labels and no collection/evaluation authority.
See [label-design evidence and approval gate](evidence/M3-label-design/README.md).
This historical checkpoint preceded the scoped protocol approval below. A separate
implementation/retention readiness gate remains required before collection.


### Current checkpoint — approved design and proposed pilot custody

Jason accepted the S0-only protocol design; the [approval record](labeling/approvals/2026-09-25-protocol-design.md)
pins the exact approved commit and SHA256. This does not authorize collection,
implementation of intake tooling, model evaluation or deployment. The
[implementation readiness proposal](labeling/IMPLEMENTATION-READINESS.md) specifies
records, transition authority, custody alternatives, retention, failure tests and
rollback. Technical review rejected paper-only as the default: sanitized S0 train/dev
records may use durable Git retention under the approved protocol. The proposal
now recommends local forms/validator, with human content review before retention.
Separate custody remains required for the later hidden test study.

Next gate: approve bounded local forms/validator implementation without collection;
then separately authorize the 30-family pilot and durable sanitized Git retention. M4 human acceptance and independent checkpoint custody remain
separate and unresolved. Documentation review checks are recorded in
[label readiness evidence](evidence/M3-label-readiness.md). Publication remains pending: automatic approval review rejected the coordination
message asserting fresh push authority. No remote write was attempted. This does
not change the separate data-collection boundary.


### Current checkpoint — implementation-only S0 fixture tooling

Published baseline `4702ee0` is verified on Forgejo and GitHub. Jason's separate
[implementation-only approval](labeling/approvals/2026-09-25-implementation-only.md)
covers empty local forms, stdlib validation and tests. The new fixture-only checker
checks reference/state/privacy/revision/split invariants and rejects real content
and human authority claims. 23 new tests and 96 complete adaptive tests pass.
[Evidence and limitations](evidence/M3-local-tooling/README.md) distinguish this
from a human collector. Technical review passed; the local milestone is ready
for a focused commit, with collection still disabled.
Next gate remains explicit authorization for collection and durable S0 retention;
no case/label/review was collected. No production change or further push.


### Current checkpoint — manual pilot approved, start pending

Jason [approved the bounded manual S0 pilot](labeling/approvals/2026-09-25-pilot-collection.md)
for **26 September–25 October 2026**, with durable sanitized Git retention and
individual case/label review. The current local date is still September 25; no
case or label was created. Time Machine includes `/private/tmp`; the existing
per-user temporary root is excluded and Spotlight is disabled. Recheck the actual
draft subdirectory at start. Third-party capture is not established by these checks.
Next safe action after the start date: prepare ten clearly AI-proposed synthetic
train/dev drafts outside Git for Jason's individual review. No model/router
evaluation, production change, scheduling or further push is authorized.


### Current checkpoint — batch 1 accepted, effort unknown

Jason directly approved all ten batch-1 revision-1 cases and proposed labels.
[Manual evidence](labeling/pilot-s0/batch-1/README.md) preserves exact reviewed
bytes and hash-bound separate acceptance. Six train/four dev, no hidden test data;
AI-proposed, human-approved, not independent correctness. Zero unresolved review
decisions; intentionally ambiguous case 10 is accepted as clarify. Labeling effort
was not reported: median UNKNOWN, effort gate not passed. Pause before batch 2
until effort is reported. No evaluation, execution, deployment or push.


### Batch 1 effort checkpoint

Jason reported approximately five minutes active review for ten cases.
[Effort evidence](labeling/pilot-s0/batch-1/effort.json) records the aggregate and
30-second derived average, without fabricating per-case timing or measured median.
The aggregate bounds median below the two-minute stop threshold; zero unresolved
review decisions. Proceed to batch 2 proposals outside Git, pending human review.
No router/model evaluation or push authorized.


### Current checkpoint — batch 2 accepted, effort pending

Jason directly accepted cases 11–20 and their proposed labels.
[Batch 2 evidence](labeling/pilot-s0/batch-2/README.md) preserves exact reviewed
bytes and separate hash-bound acceptance. Five train/five dev; pilot total20/30.
Zero unresolved review decisions. Batch2 effort remains UNKNOWN; do not reuse
batch1 timing. Pause before batch3 pending reported effort. No evaluation,
execution, deployment, permission change or push.


### Batch 2 effort checkpoint

Jason reported the same five active-review minutes as batch1.
[Batch2 effort](labeling/pilot-s0/batch-2/effort.json) records this approximate
aggregate, not individual timings. Effort/ambiguity stop thresholds are not
triggered. Prepare final batch3 outside Git; no case or label acceptance inferred.
The 30-family cap remains binding. No evaluation, execution or push authorized.


### Current checkpoint — 30-family manual pilot complete, no evaluation

Jason approved final cases21–30 and reported three minutes review. Total30/30,
20train/10dev, three cases per stratum; aggregate reported effort13minutes.
[Results and limitations](labeling/pilot-s0/RESULTS.md) distinguish proposal-review
from independent annotation and forbid router-accuracy/calibration claims.
All artifact/case hashes and counts verified. No unresolved review decisions;
no actual median or independent correctness evidence. Collection cap reached.
Next: separately reviewed offline descriptive experiment plan, not execution.
No evaluation, new cases, deployment or push authorized; M4 remains open.


### Current checkpoint — descriptive offline comparison plan

[Plan](experiments/s0-routing-descriptive-v1/PLAN.md) proposes always-abstain, existing
keyword rules and fixed-threshold TF-IDF nearest baselines on20train/10dev families.
Request-only and context-assisted inputs are reported separately; context can leak
route hints, so no generalization/calibration claims or production promotion.
Corpus/source pins verified without invoking routers. Adapter/evaluator and actual
isolation checks are not implemented; null implementation pins block execution.
Next gate: local implementation/fixture tests only, followed by separate approval
for the bounded run. No evaluation, models, production changes or push performed.


### Current checkpoint — evaluator implementation, accepted-corpus launch disabled

Jason approved local evaluator/adapter implementation and fixture tests only.
[Implementation evidence](experiments/s0-routing-descriptive-v1/IMPLEMENTATION.md)
records29 new /125 full tests passing, with no accepted pilot case evaluated.
Pinned-source adapter, scoring and fixture comparison exist. Accepted-corpus launch
remains unconditionally disabled. OS isolation, hard timeout/resource enforcement
and durable output launcher are not verified; plan execution pins remain null.
Next: technical review and bounded launcher readiness, then separate exact run
approval. No collection, model call, deployment or push.

Harmless OS-isolation readiness probe failed with sandbox_apply Operation not
permitted. Accepted-corpus launch remains disabled; no weaker isolation substituted.
Independent review passed for implementation-only scope; further launcher/environment
readiness must be proposed separately. No plan execution pins populated.


### Current checkpoint — launcher design, current environment no-go

[Launcher readiness](experiments/s0-routing-descriptive-v1/LAUNCHER-READINESS.md)
proposes a stdlib supervisor and isolated worker without installing dependencies.
Six harmless primitive tests pass (131 full); timeouts, file/output bounds and
exclusive/atomic path primitives observed. OS network/process/read confinement
remains blocked/unverified; hard memory and crash recovery remain unproven.
No accepted corpus accessed, no live launcher created, gate remains disabled.
Next: technical review and a concrete permitted execution-context proposal before
any actual run approval. No deployment, installation or push.


### Current checkpoint — fixed LXC100 proposal and local supervisor fixtures

[LXC100 probe plan](experiments/s0-routing-descriptive-v1/LXC100-FEASIBILITY-PLAN.md)
now has argument-safe canary commands and exact not-found preflight requirement.
[Supervisor evidence](experiments/s0-routing-descriptive-v1/LXC100-SUPERVISOR-EVIDENCE.md)
records13 focused/144 full tests. Only invented local child programs can execute;
remote execution unconditionally denied. Proposed stop fallback is not invoked.
Candidate awaits technical review before commit/run-approval request; no LXC
mutation, accepted-corpus access, model evaluation, installation or push.


### Current checkpoint — complete fake probe flow, real transport absent

Reviewed feasibility plan/supervisor saved locally at1e506bd.
[Dry-run evidence](experiments/s0-routing-descriptive-v1/LXC100-DRY-RUN-EVIDENCE.md)
records17 new/161 full tests for the complete fake-transport state machine, exact
preflight, health/DNS comparison and ownership-aware failure cleanup. Actual
observation collectors and remote transport remain absent/disabled. No LXC100 or
accepted-corpus access. Candidate awaits technical review before commit or exact
shared-host run approval. No installation, infrastructure change or push.


### Current checkpoint — bounded observation/session candidate

[Candidate evidence](experiments/s0-routing-descriptive-v1/LXC100-CANDIDATE-EVIDENCE.md)
records 15 new and 176 full passing local tests. Fixed metadata collectors,
bounded session and PID/invocation ownership checks are implemented as disabled
candidates. Complete lifecycle integration and unloaded-unit recovery remain
unresolved. Next: review this candidate, then complete those local gates before
any live probe. No SSH/LXC100 invocation, corpus evaluation or push in this step.


### Current checkpoint — integrated candidate awaiting final review

Collector checkpoint committed locally as `50500ff`. The
[integrated candidate](experiments/s0-routing-descriptive-v1/LXC100-INTEGRATED-CANDIDATE.md)
now combines fixed sessions/collectors, durable ownership journal, guarded
completed-run cleanup and conservative read-only interruption recovery.
184 full tests pass, including 8 new tests with failure/interruption subcases.
No SSH, live DNS, LXC100 mutation, accepted-corpus evaluation or push occurred.
Next: final technical review of source pins and remaining risks, particularly
manual recovery after uncertain termination and concurrent privileged changes.
Keep all live adapters disabled pending that review.


### Current checkpoint — fixed one-shot adapter awaiting final review

Integrated checkpoint saved locally as `28a9e49`. The
[fixed one-shot candidate](experiments/s0-routing-descriptive-v1/LXC100-LIVE-CANDIDATE.md)
adds a ten-second readiness window, shared eight-second inspection deadline,
manifest-bound direct SSH/fixed DNS adapter and exclusive one-shot journal.
8 focused and 192 full tests pass; public invocation remains unconditionally
disabled. No live SSH/DNS/LXC100 operation or push occurred. Next: final review of
the pinned candidate before any invocation-enabling change. Existing manual
recovery behavior and accepted-corpus exclusion remain in force.


### Current checkpoint — approval-gated candidate, last preflight review pending

Reviewed timing/adapter checkpoint committed locally as `d476158`. The candidate
now verifies files through bounded O_NOFOLLOW descriptors with regular-file,
owner/mode/link checks and before/after identity checks. The no-argument launcher
requires the fixed external approval record to match the final reviewed manifest,
exact fixture-only scope, passed technical review, confirmed operator window and
explicit one-shot release. Jason's conditional authorization is recorded as
conveyed by the coordinating task, not cryptographic identity proof.

200 full tests pass. `lxc100-approval-record.json` is outside the manifest artifact
set and remains pending in all release fields. No live invocation, production
change, accepted-corpus evaluation or push occurred. Next: last preflight review
of the ready manifest and pending approval record before any release or invocation.


### Current checkpoint — single probe released, invocation handed to coordinator

Pending-gate checkpoint saved as `eb1deef`. The coordinating task passed its last
preflight review and confirmed the exclusive operator window for this single
fixture probe under Jason's conditional authorization. The fixed external record
now marks technical review passed, operator window confirmed and one-shot release.
The final manifest is bound after the documentation/test changes, without a hash
cycle. All 200 tests pass; the real released record was exercised only with
`_prepared_one_shot` mocked. This preparation task has not invoked SSH, DNS, LXC100
or the one-shot launcher and has not pushed. Next: the coordinating task verifies
the final committed hashes/preflight and performs the authorized single attempt.
Existing scope, no automatic retries and manual-recovery rules remain unchanged.


### Current checkpoint — run 001 read-only abort; no retry authorized

The coordinating task invoked the released one-shot once. [Run 001 evidence](experiments/s0-routing-descriptive-v1/run-001/RESULT.md)
preserves the verified five-record journal: unit/paths passed; health child failed;
mutation_attempted=false. The original journal remains untouched. Coordinator
read-only diagnosis identifies a changed container inventory and guest-root
memory.max=`max`, invalidating collector assumptions. No confinement result exists.
Next: prepare/test a bounded second-attempt candidate using dynamic inventory and
host-side LXC resource accounting, then request new approval. No automatic retry.


### Current checkpoint — second-attempt candidate, no new approval

[Attempt 2 plan](experiments/s0-routing-descriptive-v1/LXC100-ATTEMPT-2.md) proposes
bounded dynamic Docker inventory, fixed host-side LXC memory/swap accounting and
unchanged guest pressure/unit isolation gates. 206 full tests pass. New attempt2
journal/manifest/approval identities preserve run001 and prevent implicit retry.
All release fields, including fresh human approval, are pending. The original
journal remains untouched; no preparation-stage SSH/DNS/LXC operation occurred.
Next: technical review, then the explicit new approval question in the plan.


### Current authorization checkpoint — fresh run002 approval, review still pending

The coordinating task reports Jason explicitly approved the corrected second
attempt. [Fresh run002 authorization](experiments/s0-routing-descriptive-v1/RUN-002-AUTHORIZATION.md)
records exactly one fixture-only probe once technical review passes, with unchanged
exclusions and no automatic retry. The machine-readable gate stays pending;
final manifest binding must occur only after review. Candidate code and the 206
passing-test result are unchanged. Return the disabled candidate for final review;
no live execution or push during preparation.


### Latest attempt2 review checkpoint — full captured host output supported

The coordinating task supplied the complete sanitized host status capture.
Its exact fixture now parses, including all six pressure fields, bounded name/tags,
required type=lxc and required vmid=100. Unknown fields and malformed/negative/
nonfinite values remain rejected. Eight focused attempt2 tests and 208 full tests
pass. Candidate hash: `87ec5b4c9a8ae28728112182db79008895ad3049908f54993943d30e317f64ab`.
Fresh conditional approval is recorded separately, but technical review and
machine release remain pending. No commit/release/run since this correction.


### Current run002 checkpoint — final release prepared, invocation reserved

Corrected candidate technical review passed independently (8 focused/208 full).
Fresh Jason approval provenance now states exactly one run002. Released-record
tests use only a mocked prepared lifecycle. Final manifest and external record
are regenerated/bound after pinned artifacts settle; record validation is read-only.
The preparation task performs no probe invocation, journal creation, SSH/DNS,
commit or push. Next: coordinating task verifies final hashes and directs the
single authorized execution; no retry or scope expansion is implied.


### Run002 result — inconclusive preflight, no mutation

The coordinating task verified and invoked reviewed manifest
`1713058f4f280e116933295ec633f5c59925f8a9cba1635dae9a371ea0e322b2`
once. Read-only unit, path, guest-health and host-accounting observations completed,
then the lifecycle failed in preflight before any create or run intent. The journal
proves `mutation_attempted=false`, `manual_recovery_required=false`, no remote stop
and no corpus evaluation. A post-run fixed DNS diagnostic succeeded but does not
prove the earlier cause, which remains UNKNOWN / REQUIRES VERIFICATION. Exact
evidence is preserved under `run-002/`; the approval is consumed and no retry is
authorized.


### Failure observability milestone — local only

[Bounded run-failure observability](experiments/s0-routing-descriptive-v1/RUN-FAILURE-OBSERVABILITY.md)
adds lifecycle-controlled boundary codes and a five-value failure-class allowlist.
Exception messages and tracebacks are not retained. Injected DNS-timeout and
journal-I/O tests prove the codes distinguish the unresolved run002 interval
without persisting a sentinel secret. All 210 adaptive tests pass. This does not
retroactively identify run002's cause or authorize run003.


### Run003 decision gate

[The go/no-go review](experiments/s0-routing-descriptive-v1/RUN-003-GO-NO-GO.md)
permits local candidate preparation but explicitly rejects live execution at the
current checkpoint. One separately reviewed run003 may be justified because the
new telemetry creates information gain and neither prior attempt mutated LXC100.
It must use a new journal and approval, pin both evidence sets and preserve all
resource limits. A third pre-mutation failure is a hard stop on further live
attempts until the method or target changes.


### Run003 candidate checkpoint — reviewed, execution pending

The distinct run003 candidate validates the immutable run001 and run002 evidence,
uses a fresh absent journal and retains the same fixed commands and resource
ceilings. Its only execution-path change is bounded failure telemetry. Twenty-one
focused and 213 full tests pass; manifest
`188fc6a6e6ed8dda082e71c46e232145a782ad21c1ad03f795135a933ffc0c29`
is bound to the pending external record. Technical review passed. Human approval,
exclusive-window confirmation and one-shot release remain pending. No live query,
journal or infrastructure change occurred during preparation.


### Run003 outcome — LXC100 execution context rejected

Run003 passed preflight and reached the transient-unit attempt, which failed before
payload readiness with systemd `226/NAMESPACE` at the bounded `run-readiness` /
`validation` boundary. Manual receipt-guarded recovery reset the exact failed unit,
removed the exact canary and restored systemd and the Docker baseline. No corpus
was evaluated. The approval is consumed and evidence is preserved in `run-003/`.

The hard stop now applies: no run004 on LXC100 and no weakening of namespace
controls to force a pass. Stream A must treat this as a negative architecture
result and evaluate a VM or different isolation boundary before any further live
fixture execution.


### Execution-boundary decision after run003

[The post-LXC100 decision](experiments/s0-routing-descriptive-v1/POST-LXC100-EXECUTION-DECISION.md)
retires the shared Docker LXC as the S0 execution target and keeps accepted-corpus
evaluation blocked. A dedicated disposable VM is the preferred future boundary,
but no existing guest is approved for reuse and no current capacity claim is made.
The next safe work is a read-only VM capacity/network design followed by a separate
creation approval. Local routing implementation and invented-fixture tests may
continue meanwhile.


### Disposable VM feasibility checkpoint

[The read-only VM design](experiments/s0-routing-descriptive-v1/DISPOSABLE-VM-DESIGN.md)
finds a credible 1-vCPU, 1-GiB, 8-GiB no-vNIC boundary. Current memory/storage
snapshots show room for planning but are not reservations. The existing Debian
13.6 ISO matches Debian's archived checksum. VM creation remains unauthorized;
offline installation contents, artifact/result channel, exact Proxmox config,
teardown and creation-window capacity still need proof.


### Disposable VM concrete build gate

[The concrete build plan](experiments/s0-routing-descriptive-v1/DISPOSABLE-VM-BUILD-PLAN.md)
selects a dated, SHA-512-pinned Debian 13 generic cloud image, immutable local
NoCloud seed and a framed serial result protocol. The proposed VM remains one
vCPU/1 GiB/8 GiB with no vNIC, guest agent, credentials, GPU, passthrough or shared
filesystem. Local parser/seed tests precede any mutation; creation is stopped-state
first, and bootstrap canary plus invented S0 fixtures must pass before a separate
boundary decision. Accepted-corpus execution remains blocked. No image was
downloaded, VMID reserved or Proxmox state changed at this checkpoint.

V0 local preparation now adds a deterministic bootstrap-canary seed candidate,
proposed stopped VM configuration and strict serial protocol. Twenty focused
synthetic tests pass: 12 protocol/parser cases and 8 seed/config/semantic cases;
the full adaptive suite passes 234 tests. The checked
candidate contains no accepted-corpus marker, credentials, package update, network
device or grant of authority. The ISO and live PTY capture remain unbuilt/unverified;
no Proxmox mutation or external download occurred.


### Disposable VM V1/V2 outcome — failed safely

After explicit V1/V2 approval, VM118 `aster-s0-fixture-v0` was created from the
dated checksum-matched Debian image. Its stopped configuration proved one core,
1 GiB fixed RAM, 8-GiB disk, serial/seed devices and no vNIC, agent, credential,
passthrough, shared filesystem or automatic start. The single bootstrap boot
reported only loopback and reached the reviewed canary unit. That unit failed before
emitting a protocol result; the wrapper powered the VM off and the strict parser
rejected the capture as incomplete. VM118 is retained stopped, existing guests are
unchanged and no accepted corpus ran. An approved read-only forensic inspection
then proved systemd status `209/STDOUT`: direct TTY output conflicted with the
unit's private-device namespace. [V2 evidence](experiments/s0-routing-descriptive-v1/run-v2-bootstrap/README.md)
retains the bounded journal and cleanup receipts.

The local [v1 correction candidate](experiments/s0-routing-descriptive-v1/vm-candidate-v1/OPERATIONS-PLAN.md)
keeps `PrivateDevices=yes`, writes the protocol into the unit's bounded output
directory and lets the outer lifecycle publish it to serial only after success.
Twenty-one focused and 235 full adaptive tests pass. A new seed, fresh VM and V2b
boot require a new approval; V3 and accepted-corpus execution remain blocked.


### Disposable VM V1b/V2b release preflight

Read-only preflight on 2026-09-26 found VMID119 and all release paths free, VM118
stopped, 48.98GB available memory, and `local-lvm`/`local` above their gates. The
pinned image checksum revalidated and existing service-guest states matched the
recorded baseline. The exact [release packet](experiments/s0-routing-descriptive-v1/vm-release-v1b/PREFLIGHT.md)
binds the seed, stopped VM validator, one-boot wrapper, limits and stop-and-retain
failure behavior. Twenty-five focused and 239 full adaptive tests pass. No seed,
VM119 or boot exists; V1b/V2b await one explicit bounded execution approval.


### Disposable VM V1b/V2b outcome — bootstrap gate passed

Jason approved the manifest-bound window. V1b created stopped VM119 and its
configuration/seed gates passed. The single V2b boot emitted one valid
`bootstrap-canary-002` envelope, reported only loopback, and powered off without a
host stop. The strict parser accepted 119 canonical result bytes and the expected
payload identity; VM119 and all existing guests are stopped/running as expected.
[V2b evidence](experiments/s0-routing-descriptive-v1/run-v2b-bootstrap/README.md)
retains the sanitized receipts. This proves bootstrap/capture only. V3 now requires
a new invented-fixture candidate and separate execution approval; no corpus ran.


### Disposable VM V3 release prepared — isolation fixture only

The local [V3 candidate](experiments/s0-routing-descriptive-v1/vm-isolation-candidate-v1/OPERATIONS-PLAN.md)
turns the remaining boundary question into ten explicit checks: environment
allowlisting and clearing, fixed locale, unprivileged execution, loopback-only
interfaces, denied IPv4 and Unix socket creation, denied fork, denied read of a
planted non-secret canary, and denied system write. The systemd profile adds a
private network namespace, syscall filter, strict filesystem protection, one-task,
64-MiB/no-swap, 10%-CPU, 8-KiB-file and 15-second bounds. Result validation is
fail-closed and binds the exact run and payload manifest.

The [V3 release](experiments/s0-routing-descriptive-v1/vm-release-v3/PREFLIGHT.md)
proposes a fresh source-image import and new VM120/instance identity; it does not
reuse VM119's booted disk. Read-only preflight found next VMID120 and VMs118/119
stopped. Fifteen focused and 254 full adaptive tests pass, both host scripts pass
shell parsing, the generated cloud-config parses, and all manifest file hashes
recompute. No V3 file was staged remotely, ISO or VM120 was created, boot occurred,
or accepted corpus was read. Exact V3 execution remains a separate gate.


### Disposable VM V3 outcome — boundary remains NO-GO

After Jason's exact approval, the frozen V3 files were staged and hash-verified.
Fresh VM120 passed its stopped no-vNIC/no-agent configuration gate and booted once.
The 105,156-byte capture completed within bounds, the guest showed only loopback,
and it powered off without a host stop. The isolation unit failed before publishing
an `ASTER_S0_V1` result, however, so strict parsing returned `incomplete protocol`
and none of the ten controls is proven. No retry or corpus access occurred; VMs118,
119 and120 remain stopped and existing guests are healthy.

The [V3 evidence](experiments/s0-routing-descriptive-v1/run-v3-isolation/README.md)
therefore records FAILED/INCONCLUSIVE and the V4 decision is **NO-GO for accepted
corpus execution**. At that checkpoint the exact cause was UNKNOWN pending a
separately approved read-only stopped-disk inspection. A clean VM shutdown is
correctly treated as transport success rather than isolation success.

Jason then approved the bounded stopped-disk inspection. A read-only loop and
`ro,noload,nosuid,nodev,noexec` mount proved the filesystem clean, all three
generated artifact hashes exact, and both result files absent. The journal records
`226/NAMESPACE`: `/var/tmp/aster-s0-isolation-fixture-001` was absent while systemd
constructed the unit namespace, so Python never ran. Cleanup detached the loop and
left VMs118–120 stopped. The high-confidence design inference is an interaction with
`PrivateTmp=yes`; the corrected design should preserve private temporary directories
and move the planted denial target elsewhere. This diagnosis does not change the
NO-GO or authorize another boot.


### Disposable VM V3b correction prepared

The local [V3b candidate](experiments/s0-routing-descriptive-v1/vm-isolation-candidate-v2/OPERATIONS-PLAN.md)
preserves `PrivateTmp=yes` and every other security/resource control while moving
only the planted read-denial target to `/srv/aster-s0-isolation-fixture-002`. It
uses new run/instance identities and proposes a fresh image import into VM121; no
prior fixture disk is reused. Nine focused and 263 full adaptive tests pass, the
generated cloud-config and shell scripts parse, and the manifest file hashes
recompute. Release SHA-256 is
`825d6d40cde3b1388484e37581473bb2c9c0d4e6e88d905406562536782fc4e1`.

Read-only preflight found next VMID121, the new paths absent, VM120 stopped and
capacity above the established gates. [V3b release](experiments/s0-routing-descriptive-v1/vm-release-v3b/PREFLIGHT.md)
was frozen for a separately approved execution window.


### Disposable VM V3b outcome — boundary preparation GO

Jason approved the exact frozen V3b window. Every remotely staged source matched
the release manifest. The generated 380,928-byte seed ISO has SHA-256
`c8ad6005bfc221f522c4832208c6a869c936e5eddb885df4eab1f60375b07aae`,
contains exactly `meta-data` and `user-data`, and extracted bytes match the reviewed
sources. Fresh VM121 passed the stopped no-vNIC/no-agent configuration gate.

The one permitted boot emitted one complete, digest-bound envelope and powered off
without host intervention. The strict parser accepted the exact run and manifest,
364 canonical result bytes and digest. The semantic validator accepted all ten
mandatory checks: the environment was cleared and allowlisted with a fixed locale;
the process was unprivileged and loopback-only; IPv4 and Unix sockets, fork, system
write and the planted unrelated read were denied. Receipt-index verification found
zero mismatches. VMs118–121 are stopped, no retry or corpus access occurred, and
the raw 104,695-byte serial capture remains uncommitted because it contains noisy
boot output and generated public SSH host-key material.

The [V3b evidence and V4 decision](experiments/s0-routing-descriptive-v1/run-v3b-isolation/README.md)
change the boundary gate to **GO for preparation of a separately immutable
accepted-corpus candidate**. Corpus execution remains unauthorized. The next
candidate requires a fresh disk and identity, pinned corpus/code/result contract,
reviewed resource and lifecycle bounds, and a new exact human approval.


### Disposable VM V5 accepted-corpus candidate prepared

The local [V5 candidate](experiments/s0-routing-descriptive-v1/vm-corpus-candidate-v1/OPERATIONS-PLAN.md)
pins the nine already accepted S0 artifacts, their 20-train/10-development split,
the existing adapter and standard-library routing source, and a new bounded worker.
It compares always-abstain, existing keyword rules and fixed-0.2 TF-IDF nearest
under request-only and verbatim-synthetic-context profiles. It makes no cloud,
model or tool call and cannot promote a route. Confidence, privacy quality, cloud
requirement and production local-resolution remain explicitly unmeasured.

The proposed fresh VM122 retains the proven no-vNIC/no-agent boundary, runs one
unprivileged task with private network/devices/tmp and read-only inputs, and adds
384-MiB memory, 75-second unit, 4-MiB output and 300-second outer capture bounds.
Nine focused and 272 full adaptive tests pass; the generated cloud-config and host
scripts parse. Read-only preflight found VMID122 free, VMs118–121 stopped, all new
paths absent, the retained image exact and capacity above gates.

The [V5 release](experiments/s0-routing-descriptive-v1/vm-release-v5/PREFLIGHT.md)
is local and unexecuted. Release-manifest SHA-256 is
`1ae0bdeda1e5043a98065b4de8515d4a75045d936271a79f6f77cd80059c8a8c`.
No accepted case was evaluated while building the packet. Remote staging, VM/ISO
creation, boot, evaluation, cleanup and push require separate authorization.


### Disposable VM V5 outcome — failed/inconclusive

Jason approved the exact V5 window. The 23 staged files reproduced both manifests;
fresh VM122 passed the stopped no-vNIC/no-agent validator. Its 483,328-byte ISO and
extracted seed sources matched. The one offline boot reached
`aster-s0-corpus.service`, which exited with an error before publishing a protocol
record. The guest powered off within bounds without a host stop and no retry
occurred. VMs118–122 are stopped.

The [V5 evidence](experiments/s0-routing-descriptive-v1/run-v5-corpus/README.md)
records a 104,662-byte capture with SHA-256
`d8dc426db310dfe2855007da0edebc96170abcb293b997d76bcf65ea4c944aa8`,
zero protocol records, strict parse `incomplete protocol`, and zero receipt-index
mismatches. No routing or performance metric is credited. Whether the worker read
or partially processed accepted rows before failing is **UNKNOWN / REQUIRES
VERIFICATION**; protocol absence cannot prove it did not.

VM122 is retained stopped. Jason approved the local
[read-only forensic plan](experiments/s0-routing-descriptive-v1/run-v5-corpus/OFFLINE-FORENSIC-PLAN.md).
The clean stopped filesystem contained all 15 exact generated artifacts and no
result or protocol file. Its bounded journal proves `s0_descriptive.py` could not
import the omitted `validate_label_batch` module. The entry point had verified all
nine corpus hashes but failed before JSON parsing, adaptation, engine construction
or routing; zero accepted rows were evaluated.

The same evidence showed `RuntimeMaxSec=` is ignored for a oneshot unit, although
`TimeoutStartSec=75` and the host's 300-second wrapper remained effective. A V5b
candidate must close the package dependency set, statically verify that closure,
remove the ineffective directive, preserve the effective bounds and use a fresh
run, instance and VM identity. The forensic approval granted no retry, correction
execution, cleanup, promotion or push.


### Disposable VM V5b correction prepared

The [V5b candidate](experiments/s0-routing-descriptive-v1/vm-corpus-candidate-v2/OPERATIONS-PLAN.md)
uses a fresh identity and proposed VM123. It packages the validator omitted from V5,
adds a static sibling-import closure check, and proves the generated source set
imports under the guest's isolated Python flags. It removes the ineffective
`RuntimeMaxSec=` declaration while retaining `LimitCPU=70`,
`TimeoutStartSec=75` and the 300-second outer deadline. Corpus artifacts, split,
engines, profiles, threshold, security controls and result contract are unchanged.

The [V5b release](experiments/s0-routing-descriptive-v1/vm-release-v5b/PREFLIGHT.md)
is frozen locally at manifest SHA-256
`721c377dccca4fef1a685427d85f791559f67686b8bbf533439589f88b3a5d0f`.
Read-only preflight found VM123 and all new paths absent, VMs118–122 stopped, the
pinned image exact and capacity above gates. No accepted row was evaluated while
preparing it. Staging, creation and its one offline boot require a separate exact
approval; cleanup, retry, promotion and Git push remain excluded.


### Disposable VM V5b outcome — S0 comparison complete

Jason approved the exact V5b window. Initial staging failed closed because the
macOS archive added 30 AppleDouble files. Under a second explicit approval, a
hash-bound script deleted only that enumerated metadata set and proved the exact
24-file stage before infrastructure creation.

Fresh VM123 passed its stopped no-vNIC/no-agent gate and booted once offline. The
[V5b result](experiments/s0-routing-descriptive-v1/run-v5b-corpus/README.md)
contains one valid 36,453-byte canonical result for `corpus-descriptive-002`.
Strict framing and semantic validation passed, receipt hashes match, no host stop or
retry was required, and VMs118–123 are stopped.

On ten exposed development families, complete counts for abstain, keyword and fixed
nearest were 0/4/6 with request only and 0/3/8 with synthetic context. Context gave
nearest two gains but keyword one loss; nearest also produced missing and extra
capability errors. The [decision](experiments/s0-routing-descriptive-v1/run-v5b-corpus/DECISION.md)
retains all three as benchmark baselines and makes no production selection,
threshold change, calibration or privacy claim.

The evaluator used about 0.118 seconds while the disposable VM lifecycle took about
135 seconds. The VM is therefore retained as an offline experiment boundary, not a
serving harness. This closes the S0 descriptive comparison only.

### M3 serving-harness decision

The [M3 harness ADR](evidence/M3-harness-decision.md) combines the controlled
preload/tool-loop comparisons, current read-only serving checks, historical Hermes
measurements and existing production local-model graduations. The evidence supports
retaining the bounded Aster Python runtime. Hermes remains an optional client or
workflow harness; PydanticAI remains a probationary specialist challenger;
LangGraph and Pi remain conditional research options. No live challenger run is
justified until a concrete benefit hypothesis exists.

The harness subdecision is complete without a migration. M3 overall remains open
for representative independently reviewed routing evidence. M4 and all production
or shadow gates remain open.

The proposed [S1 holdout plan](experiments/s1-routing-holdout-v1/PLAN.md) defines
that remaining evidence as 50 new human-authored, no-suggestion families across ten
request strata. It freezes the retained baselines and permits only a later, separately
approved offline evaluation. S0 records cannot be relabeled or resplit into S1.
The concrete [collection gate](experiments/s1-routing-holdout-v1/COLLECTION-GATE.md)
now binds a blank form/schema, syntax-only validator, registry, custody design and
58 passing focused tests. Jason approved the bounded collection window; the
[activation checkpoint](experiments/s1-routing-holdout-v1/ACTIVATION.md) records an
empty mode-`0700` scratch directory and byte-identical empty bundle. Collection
dates remain unset until the first human request. Evaluation remains a later
separate gate.
### Historical integrated checkpoint — 2026-09-26

Source-pin work through `69c2a7e` is reconciled with Forgejo `616a5af`. The incoming
retrieval-only Aster change was reviewed explicitly; all eight extracted definitions
are unchanged, and both offline source pins were revised with retained evidence.
102 adaptive + 29 selector + 82 broker + 170 Aster tests pass. The 164-event historical
M4 proof still verifies. See [integration evidence](evidence/2026-09-26-integration.md).
This supersedes earlier notes calling the selector continuation unpublished or
AI-PAM an unfinished M6 candidate. No production or collection change occurred here.
Jason requested publication; verify the accepted commit and automatic mirror.

Next gates are the separately authorized S0 collection/retention step, actual M4
human review/independent custody, and Stage2 real-session assurance/process trust.
Implementation-only labeling approval does not cover collection. Consult newer
approval records before proceeding; do not manufacture human evidence or repeat
synthetic benchmarks in place of these gates. This checkpoint is retained as
evidence only; the 2026-09-28 controlling resume instruction above supersedes it.
